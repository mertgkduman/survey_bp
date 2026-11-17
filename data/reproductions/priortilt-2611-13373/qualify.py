"""Independent source checks and full-budget pilots, never pooled with production."""
from dataclasses import replace
from hashlib import sha256
import gzip
import importlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from scipy.sparse import csc_matrix
import stim
from bp_registry.canonical.prior_tilt import PriorTiltDecoder,PriorTiltSpec,indexed_uniform
from bp_registry.circuit.paper_decoders import CircuitPaperDecoder,PaperDecoderSpec
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.memory_benchmark import source_masks,audit_candidates,validate_trace

ROOT=Path(__file__).resolve().parent
SOURCE=json.loads((ROOT/'source.json').read_text())
SCHEDULES=json.loads((ROOT/'phase-schedules.json').read_text())


def matrix(model):
    h=np.zeros((model.table.check_count,model.table.variable_count),np.uint8)
    for c,v in model.table.edges:h[c,v]=1
    return csc_matrix(h)


def settings(case,method):
    if method=='priortilt':
        s=SCHEDULES[case['code']][str(case['p'])]
        return PriorTiltSpec(ends=tuple(s['ends']),phases=tuple(tuple(p) for p in s['phases']))
    if method=='beam':return PaperDecoderSpec(method='beam',initial=40,per_leg=30)
    g0,lo,hi=SOURCE['relay_gammas'][case['code']]
    return PaperDecoderSpec(method='relay',first_gamma=g0,gamma_low=lo,gamma_high=hi)


def prepare(model,case,method,seed):
    spec=settings(case,method)
    return PriorTiltDecoder(model.table,model.prior_llrs,spec,seed) if method=='priortilt' else CircuitPaperDecoder(model,spec,seed)


def prior_source_checks():
    sys.path.insert(0,os.environ.get('PRIORTILT_REFERENCE','/tmp/survey-bp-priortilt-native-261113373'))
    from priortilt_rs import PriorTiltDecoder as Native
    rows=[]
    for case in SOURCE['circuits']:
        if case['basis']!='z' or case['p']!=max(float(p) for p in SCHEDULES[case['code']]):continue
        circuit=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));model=DemBinaryModel.from_dem(circuit.detector_error_model())
        # Source initialization expression is aligned here; production retains
        # the unchanged canonical DEM prior expression and records that choice.
        probs=np.array([i.args_copy()[0] for i in circuit.detector_error_model().flattened() if i.type=='error'])
        prior=np.log((1-probs)/probs);h=matrix(model)
        dets=circuit.compile_detector_sampler(seed=2026111771).sample(12)
        for pi in (0.,1.):
            spec=PriorTiltSpec(initial=12,round_len=6,rounds=4,ends=(1,3),phases=((pi,.5,.25,2.),(pi,.25,.5,3.),(pi,.5,.5,2.)))
            native=Native(h,probs,initial_iters=12,round_len=6,max_rounds=4,seed=4)
            native.set_round_schedule(np.array(spec.ends,np.int64),np.array([pi]*3),np.array([.5,.25,.5]),np.array([.25,.5,.5]),np.array([2.,3.,2.]))
            canon=PriorTiltDecoder(model.table,prior,spec,seed=3)
            for shot,det in enumerate(dets):
                native.reset_offset_statistics();expected=np.asarray(native.decode(np.asarray(det,np.uint8)),np.uint8)
                actual=canon.decode(np.asarray(det,np.uint8),shot=shot)
                error=float(np.max(abs(actual.posterior-native.log_prob_ratios())))
                matches=bool(np.array_equal(actual.candidate,expected))
                same_stop=actual.iterations==native.iterations and actual.converged==native.converge
                stats=native.offset_statistics()
                same_stats=int(sum(actual.trace[:,3]))==stats[0] and len(actual.trace)==stats[2]
                rows.append({'code':case['code'],'pi':pi,'shot':shot,'iterations':actual.iterations,'rounds':len(actual.trace),'max_posterior_error':error,'candidate_matches':matches,'stopping_matches':same_stop,'eligibility_matches':same_stats})
    (ROOT/'prior-native-probe.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert all(r['candidate_matches'] and r['stopping_matches'] and r['eligibility_matches'] for r in rows), 'native policy decisions differ; inspect prior-native-probe.json'
    binary=Path(importlib.import_module('priortilt_rs').__file__)
    return {'cases':rows,'binary_sha256':sha256(binary.read_bytes()).hexdigest(),'source_commit':SOURCE['commit'],'maximum_posterior_difference':max(r['max_posterior_error'] for r in rows),'state_correspondence':'canonical reduction order retained; strict native state tolerance not claimed',
            'scope':'native full terminal state and eligible-node counts with deterministic pi=0/1 schedules; native float64 initialization aligned; independently checked canonical total-minus extrinsics retained'}


def baseline_source_checks():
    sys.path.insert(0,os.environ.get('BEAM_REFERENCE','/tmp/survey-bp-beam-native-261113373'))
    from beam_search_decoder._beam_search_decoder import BeamSearchDecoder as NativeBeam
    sys.path.insert(0,os.environ.get('RELAY_REFERENCE','/tmp/survey-bp-relay-v022-package'))
    import relay_bp
    rows=[]
    for case in SOURCE['circuits']:
        if case['basis']!='z' or case['p']!=max(float(p) for p in SCHEDULES[case['code']]):continue
        circuit=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));model=DemBinaryModel.from_dem(circuit.detector_error_model())
        probs=np.array([i.args_copy()[0] for i in circuit.detector_error_model().flattened() if i.type=='error'])
        model=replace(model,prior_llrs=np.log((1-probs)/probs));h=matrix(model)
        dets=circuit.compile_detector_sampler(seed=2026111772).sample(12)
        beam=CircuitPaperDecoder(model,PaperDecoderSpec(method='beam',initial=12,per_leg=6,width=4,rounds=3))
        native_b=NativeBeam(h,error_channel=probs.tolist(),beam_width=4,num_results=1,initial_iters=12,iters_per_round=6,max_rounds=3)
        g0,lo,hi=SOURCE['relay_gammas'][case['code']]
        spec=PaperDecoderSpec(method='relay',initial=12,per_leg=6,additional=3,first_gamma=g0,gamma_low=lo,gamma_high=hi)
        relay=CircuitPaperDecoder(model,spec,seed=8)
        for shot,det in enumerate(dets):
            expected=np.asarray(native_b.decode(np.asarray(det,np.uint8)),np.uint8)
            actual=beam.decode(np.asarray(det,np.uint8),shot=shot)
            np.testing.assert_array_equal(actual.candidate,expected)
            assert actual.converged==bool(native_b.converge)
            rows.append({'code':case['code'],'method':'beam','shot':shot,'iterations':actual.iterations,'converged':actual.converged})
            # The native adapter accepts an explicit per-leg gamma table, so
            # both implementations can consume the exact same random fields.
            gammas=np.zeros((4,len(probs)))
            for leg in range(1,4):
                for v in range(len(probs)):gammas[leg,v]=lo+(hi-lo)*indexed_uniform(8,shot,leg,v)
            native_r=relay_bp.RelayDecoderF64(check_matrix=h.tocsr(),error_priors=probs,alpha=1.,gamma0=g0,pre_iter=12,
                        num_sets=3,set_max_iter=6,explicit_gammas=gammas,stop_nconv=1,logging=False)
            expected=native_r.decode_detailed(np.asarray(det,np.uint8));actual=relay.decode(np.asarray(det,np.uint8),shot=shot)
            np.testing.assert_array_equal(actual.candidate,np.asarray(expected.decoding,np.uint8))
            assert actual.converged==expected.success and actual.iterations==expected.iterations
            np.testing.assert_allclose(actual.posterior,expected.posterior_ratios,atol=2e-9,rtol=2e-10)
            rows.append({'code':case['code'],'method':'relay','shot':shot,'iterations':actual.iterations,'converged':actual.converged})
    rb=next(Path(relay_bp.__file__).parent.glob('_relay_bp*.so'))
    beam_module=importlib.import_module('beam_search_decoder._beam_search_decoder')
    return {'cases':rows,'beam_commit':SOURCE['beam_commit'],'beam_binary_sha256':sha256(Path(beam_module.__file__).read_bytes()).hexdigest(),
            'relay_commit':'14cb31a18f9b9d7d099791b793e35b8a2951f8f3','relay_binary_sha256':sha256(rb.read_bytes()).hexdigest(),
            'scope':'native candidate/convergence for both baselines; Relay all-path iteration count, selected posterior and explicit same gamma fields; no native Beam all-path work counter claimed'}


def numerical_order_probe():
    from priortilt_rs import PriorTiltDecoder as Native
    rows=[]
    for case in SOURCE['circuits']:
        if case['basis']!='z' or case['p']!=max(float(p) for p in SCHEDULES[case['code']]):continue
        circuit=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));model=DemBinaryModel.from_dem(circuit.detector_error_model())
        probs=np.array([i.args_copy()[0] for i in circuit.detector_error_model().flattened() if i.type=='error'])
        prior=np.log((1-probs)/probs);h=matrix(model)
        dets=circuit.compile_detector_sampler(seed=2026111771).sample(12)
        for cap in (1,6,12,36):
            # Zero rounds isolates ordinary BP, with exactly aligned priors.
            native=Native(h,probs,initial_iters=cap,round_len=1,max_rounds=0,seed=4)
            canon=PriorTiltDecoder(model.table,prior,PriorTiltSpec(initial=cap,round_len=1,rounds=0),3)
            for shot,det in enumerate(dets):
                expected=np.asarray(native.decode(np.asarray(det,np.uint8)),np.uint8);actual=canon.decode(np.asarray(det,np.uint8),shot=shot)
                rows.append({'code':case['code'],'cap':cap,'shot':shot,'iterations':actual.iterations,
                    'max_posterior_error':float(np.max(abs(actual.posterior-native.log_prob_ratios()))),
                    'candidate_matches':bool(np.array_equal(actual.candidate,expected)),
                    'stopping_matches':actual.iterations==native.iterations and actual.converged==native.converge})
    return {'cases':rows,'scope':'ordinary min-sum only, aligned float64 priors, no offset or RNG; isolates canonical total-minus versus native prefix/suffix reduction'}


def full_budget_pilot():
    ledger=ROOT/'qualification-events.jsonl.gz';events=0;noninitial=0;max_seconds=0.
    with gzip.open(ledger,'wt') as stream:
        for case in SOURCE['circuits']:
            circuit=stim.Circuit.from_file(str(ROOT/'circuits'/case['file']));model=DemBinaryModel.from_dem(circuit.detector_error_model())
            dmasks,omasks=source_masks(circuit.detector_error_model())
            dets,obs=circuit.compile_detector_sampler(seed=2026111773).sample(8,separate_observables=True)
            for method in ('priortilt','relay','beam'):
                decoder=prepare(model,case,method,2026111774)
                for shot,det in enumerate(dets):
                    start=time.perf_counter_ns();result=decoder.decode(np.asarray(det,np.uint8),shot=shot);ns=time.perf_counter_ns()-start
                    prediction=model.observable_matrix@result.candidate%2 ^ model.observable_bias
                    valid=np.zeros(model.table.check_count,np.uint8)
                    for c,v in model.table.edges:valid[c]^=result.candidate[v]
                    assert np.array_equal(valid,np.asarray(det,np.uint8)^model.syndrome_bias)==bool(result.converged)
                    if result.converged:assert result.iterations>0
                    assert np.isfinite(result.posterior).all()
                    stat=np.asarray([result.iterations,result.directed_edge_updates,int(result.converged),result.random_draws,result.biased_node_updates,result.lineage],np.uint64)
                    validate_trace(method,result.trace,stat,model,settings(case,method))
                    audit_candidates(np.packbits(result.candidate,bitorder='little')[None,:],np.packbits(det,bitorder='little')[None,:],
                        np.packbits(obs[shot],bitorder='little')[None,:],np.packbits(prediction,bitorder='little')[None,:],stat[None,:],dmasks,omasks)
                    max_seconds=max(max_seconds,ns/1e9);events+=1;noninitial+=int(len(result.trace)>(0 if method=='priortilt' else 1))
                    stream.write(json.dumps({'case':case['file'],'method':method,'shot':shot,'detectors':np.packbits(det,bitorder='little').tobytes().hex(),
                        'observables':np.packbits(obs[shot],bitorder='little').tobytes().hex(),'candidate':np.packbits(result.candidate,bitorder='little').tobytes().hex(),
                        'prediction':np.packbits(prediction,bitorder='little').tobytes().hex(),'converged':bool(result.converged),'iterations':int(result.iterations),
                        'directed_edge_updates':int(result.directed_edge_updates),'random_draws':int(result.random_draws),'biased_node_updates':int(result.biased_node_updates),
                        'lineage':result.lineage,'trace':result.trace.tolist(),'decode_ns_including_first_JIT':ns},sort_keys=True)+'\n')
    return {'events':events,'noninitial_traces':noninitial,'ledger_sha256':sha256(ledger.read_bytes()).hexdigest(),
            'seed_noise':2026111773,'seed_policy':2026111774,'max_seconds_including_first_JIT':max_seconds,
            'scope':'every circuit/method at full paper budgets; qualification-only shots, never production evidence or a source LER agreement claim'}


if __name__=='__main__':
    result={'prior_native':prior_source_checks()};print('PriorTilt native comparison passed',flush=True)
    result['numerical_order']=numerical_order_probe();print('Ordinary-BP numerical-order probe completed',flush=True)
    result['baseline_native']=baseline_source_checks();print('Beam/Relay native comparisons passed',flush=True)
    result['full_budget_pilot']=full_budget_pilot();print('Full-budget circuit pilot passed',flush=True)
    (ROOT/'qualification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
