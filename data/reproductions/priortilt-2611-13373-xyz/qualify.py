"""Separate-seed full-budget XYZ and real50-process qualification before freezing."""
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from dataclasses import replace
import importlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
import numpy as np
from scipy.sparse import csr_matrix
import stim
import run,parallel,source_contract
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.relay_list import CircuitRelayListDecoder,RelayListSpec
from bp_registry.canonical.prior_tilt import indexed_uniform


def native_checks():
    sys.path.insert(0,str(run.ROOT/'results/reference/relay'));import relay_bp
    probes=[]
    dem=stim.DetectorErrorModel('error(.1) D0\nerror(.15) D1\nerror(.2) D2\nerror(.04) D0 D1\nerror(.12) D1 D2\nerror(.08) D0 D2\nerror(.03) D0 D1 D2 L0')
    base=DemBinaryModel.from_dem(dem);probs=np.array([i.args_copy()[0] for i in dem if i.type=='error'])
    model=replace(base,prior_llrs=np.log((1-probs)/probs))
    h=csr_matrix((np.ones(len(base.variables),np.uint8),base.variables,base.row_ptr),shape=(3,7))
    spec=RelayListSpec(initial=3,per_leg=2,additional=12,results=5)
    for seed in range(3):
        for shot in range(8):
            syndrome=np.array([(shot>>i)&1 for i in range(3)],np.uint8)
            gammas=np.zeros((spec.additional+1,7))
            for leg in range(1,spec.additional+1):
                for v in range(7):gammas[leg,v]=spec.gamma_low+(spec.gamma_high-spec.gamma_low)*indexed_uniform(seed,shot,leg,v)
            native=relay_bp.RelayDecoderF64(check_matrix=h,error_priors=probs,alpha=1.,gamma0=spec.first_gamma,pre_iter=spec.initial,num_sets=spec.additional,set_max_iter=spec.per_leg,explicit_gammas=gammas,stop_nconv=5,logging=False)
            expected=native.decode_detailed(syndrome);actual=CircuitRelayListDecoder(model,spec,seed).decode(syndrome,shot=shot)
            np.testing.assert_array_equal(actual.candidate,np.asarray(expected.decoding,np.uint8))
            assert actual.converged==expected.success and actual.iterations==expected.iterations
            np.testing.assert_allclose(actual.posterior,expected.posterior_ratios,rtol=2e-10,atol=2e-9)
            probes.append({'seed':seed,'shot':shot,'iterations':actual.iterations,'converged_legs':int(actual.trace[:,5].sum()),'native_candidate_work_posterior_match':True})
    binary=next(Path(relay_bp.__file__).parent.glob('_relay_bp*.so'))
    return {'cases':probes,'binary_sha256':run.sha(binary),'source_commit':'14cb31a18f9b9d7d099791b793e35b8a2951f8f3','scope':'same explicit gamma fields; aligned native prior expression; duplicate counting, stable weighted winner, all-leg iterations and selected posterior'}


def science(root,job,basis):
    data=[parallel.arrays(p) for p in sorted((root/'results'/job['id']/basis).glob('chunk-*.npz'))]
    return {k:np.concatenate([d[k] for d in data]) for k in ('candidate','prediction','stats','trace')}


def main():
    root=run.ROOT;source=source_contract.check();native=native_checks();records=[]
    plan={**run.design(),'software':run.software()}
    plan['protocol'].update({'noise_seed':2026111891,'policy_seed':2026111892,'max_shots':32,'target_errors':20,'batch':1,'minimum_free_bytes':0})
    original_load=run.load
    for index,job in enumerate(plan['jobs']):
        local=deepcopy(plan);local['jobs']=[job];base=root/'results/qualification'/job['method'];base.mkdir(parents=True,exist_ok=True)
        (base/'circuits').symlink_to(root/'circuits',target_is_directory=True) if not (base/'circuits').exists() else None
        (base/'source.json').symlink_to(root/'source.json') if not (base/'source.json').exists() else None
        run.write_json(base/'plan.json',local);run.write_json(base/'resource-amendment.json',{'qualification_only':True,'workers':50})
        run.ROOT=base;run.load=lambda:local
        begin=time.monotonic();parallel.execute(0,50);parallel.execute(0,50,audit=True)
        folder=base/'results'/job['id'];receipt=json.loads((folder/'audit.json').read_text())
        original={b:science(base,job,b) for b in run.BASES}
        # Independent full sequential replay of every pilot shot (not just endpoints).
        for b in run.BASES:
            c,m=run.case_model(job,b);dec=run.prepared(local,job,b,m)
            replayed_traces=[]
            for i in range(32):
                _,_,raw=run.noise(local,job,b,i,c)
                syn=np.unpackbits(raw['detectors'][0],bitorder='little',count=m.table.check_count)
                result=dec.decode(syn,shot=i)
                np.testing.assert_array_equal(np.packbits(result.candidate,bitorder='little'),original[b]['candidate'][i])
                expected=np.array([result.iterations,result.directed_edge_updates,int(result.converged),result.random_draws,result.biased_node_updates,result.lineage],np.uint64)
                np.testing.assert_array_equal(expected,original[b]['stats'][i]);replayed_traces.append(result.trace)
            np.testing.assert_array_equal(np.concatenate(replayed_traces),original[b]['trace'])
            # Timing is a concurrent instrumented cohort, not a one-core benchmark.
        saved=(folder/'complete.json').read_bytes();parallel.execute(0,50);parallel.execute(0,50,audit=True)
        assert saved==(folder/'complete.json').read_bytes()
        pids={json.loads(p.read_text())['worker']['pid'] for p in (folder/'parallel-stages'/parallel.VERSION).glob('*.json')}
        initialized=list((folder/'processes').glob('*.json'))
        assert len(initialized)>=50 and os.environ.get('SLURM_CPUS_PER_TASK')=='50'
        work=json.loads((folder/'parallel-work.json').read_text())
        records.append({'method':job['method'],'events':64,'full_paper_budgets':True,'full_original_dem_audit':True,'all_pilot_shots_sequential_replay':True,
                        'resume_receipt_unchanged':True,'stage_decoder_pids':len(pids),'initialized_processes_including_audits':len(initialized),
                        'wall_seconds':time.monotonic()-begin,'bases':{b:{k:v for k,v in s.items() if k!='chunks'} for b,s in receipt['bases'].items()},
                        'computed_shots':work['computed']['shots'],'retained_shots':work['retained']['shots']})
        print('PASS full XYZ50-process pilot',job['method'],flush=True)
    run.ROOT=root;run.load=original_load
    result={'passed':True,'source':source,'native_relay5':native,'process_pilot':records,
            'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'cpus':50,'actual_affinity':sorted(os.sched_getaffinity(0)),
            'scope':'Separate qualification seeds and32 shots/basis/method; full paper budgets; complete original-DEM audits, all-shot sequential science replay and exact resume. Production64-shot batches separately exercise ordering/prefix in unit fixtures. Canonical arithmetic/RNG adaptation retained.'}
    run.write_json(root/'qualification.json',result)
    print('QUALIFICATION PASSED',flush=True)


if __name__=='__main__':main()
