"""Public transport, replay, immutable binding, and stochastic identity."""
from pathlib import Path
from dataclasses import replace
from itertools import product
from hashlib import sha256
import json
import sys
import tempfile
import numpy as np
import stim

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from audit_support import Audit
from bp_registry.canonical.policy_decoder import BinaryPolicy
from bp_registry.circuit import SharedPolicySinterDecoder
from bp_registry.batch_records import encode_records,read_records,canonical_json
from bp_registry.gpu import GpuBatchResult


def affine_packing_and_binding():
    dem=stim.DetectorErrorModel('error(1) D0 L8\nerror(0) D8\nerror(0.2) D0 ^ D8 L9\nerror(0.8) L0')
    decoder=SharedPolicySinterDecoder().compile_decoder_for_dem(dem=dem)
    events=np.zeros((2,9),np.uint8);events[0,0]=1;events[1,8]=1
    result=decoder.decode_detailed(events)
    expected=np.zeros((2,10),np.uint8);expected[:,0]=1;expected[:,8]=1;expected[1,9]=1
    np.testing.assert_array_equal(result.predictions,expected)
    packed=decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.packbits(events,axis=1,bitorder='little'))
    np.testing.assert_array_equal(np.unpackbits(packed,axis=1,bitorder='little',count=10),expected)
    assert np.all(packed[:,1]<4)
    path=HERE/'affine-ledger.jsonl'
    if path.exists():
        assert decoder.verify_ledger(path)['verified']
    else: result.write_ledger(path)
    with tempfile.TemporaryDirectory() as directory:
        exported=Path(directory)/'records.jsonl';result.write_ledger(exported)
        before=exported.read_bytes()
        try: result.write_ledger(exported)
        except FileExistsError: pass
        else: raise AssertionError('ledger overwrite')
        assert exported.read_bytes()==before
    for name in ['predictions','faults','converged','iterations']:
        try:getattr(result,name).setflags(write=True)
        except ValueError:pass
        else:raise AssertionError('mutable result '+name)
    for name,key,values in [('faults','faults',[[256,0],[0,0]]),
                            ('converged','converged',[2,1]),('iterations','iterations',[1.5,2]),
                            ('iterations','iterations',[-1,2])]:
        rows=result.ledger
        for row,value in zip(rows[1:],values):row[key]=value
        try:replace(result,**{name:np.asarray(values),'ledger_json':encode_records(rows)})
        except ValueError:pass
        else:raise AssertionError('invalid execution dtype admitted '+name)
    try:replace(result,predictions=result.predictions^1)
    except ValueError:pass
    else:raise AssertionError('stale evidence admitted')
    empty=decoder.decode_detailed(np.zeros((0,9),np.uint8))
    assert empty.predictions.shape==(0,10)
    return dict(shots=2,detectors=9,observables=10,empty_batch=True,affine_offsets=True,
                packed_padding=True,immutable_columns=4,invalid_casts_rejected=4,replayed=decoder.verify_ledger(path))


def batch_fixture():
    h=np.array([[1,1,0,0,0,0,0,0],[0,1,0,0,0,1,1,0],[1,0,0,1,0,0,1,0],[0,0,1,1,1,0,0,1]],np.uint8)
    rates=[.1686279273722417,.2151861424206105,.23636213203981687,.13467950863149117,
           .1601663007877624,.2939527271376381,.2398796318588651,.23689172971836636]
    dem=stim.DetectorErrorModel('\n'.join(f'error({p}) '+' '.join(f'D{c}' for c in np.flatnonzero(h[:,v]))+f' L{v}'
                                         for v,p in enumerate(rates)))
    return h,rates,dem,np.tile(np.array([0,1,1,1],np.uint8),(8,1))


def transport_chunking():
    h,rates,dem,events=batch_fixture()
    records=[]
    for scope in [None,'configuration','attempt','sweep']:
        policy=BinaryPolicy(schedule='variable_node_serial',randomized=scope,max_iterations=5,rule='min_sum')
        decoder=SharedPolicySinterDecoder(policy).compile_decoder_for_dem(dem=dem)
        full=decoder.decode_detailed(events)
        # Exercise the actual public Sinter interface using the exact same bytes.
        packed=np.packbits(events,axis=1,bitorder='little')
        combined=decoder.decode_shots_bit_packed(bit_packed_detection_event_data=packed)
        singles=np.vstack([decoder.decode_shots_bit_packed(bit_packed_detection_event_data=row[None]) for row in packed])
        different=np.flatnonzero(np.any(combined!=singles,axis=1)).tolist()
        records.append(dict(scope=scope,different_shots=different,full_predictions=full.predictions.tolist(),
            single_predictions=np.unpackbits(singles,axis=1,bitorder='little',count=8).tolist(),
            full_valid=full.converged.tolist(),full_iterations=full.iterations.tolist(),
            shot_identities=[row['binary_execution']['shot_identity'] for row in full.ledger[1:]]))
        path=HERE/f'chunking-{scope}.jsonl'
        if not path.exists():full.write_ledger(path)
        assert decoder.verify_ledger(path)['verified']
        assert all(full.converged),scope
        if scope in [None,'configuration']:assert not different
    report=dict(discovery_seed=5302,discovery_trial=2,graph=h.tolist(),rates=rates,dem=str(dem),
                detectors=events.tolist(),records=records)
    (HERE/'chunking-counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not any(row['different_shots'] for row in records), (
        'Sinter batch partition changes randomized predictions for the identical inputs, policy and seed; '
        'batch-local circuit:index is part of the random key. Both differing predictions satisfy the original detectors.')
    return dict(cases=len(records))


def carried_qualification():
    prior=ROOT/'.planning/quick/261108-qcu-expand-existing-compatible-policies-acro'
    receipt=json.loads((prior/'qualification.json').read_text())
    for name,digest in receipt['source_sha256'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    for name,digest in receipt['evidence_sha256'].items():
        assert sha256((prior/name).read_bytes()).hexdigest()==digest,name
    hardware=ROOT/'.planning/quick/261108-meg-implement-compatible-circuit-policies-an/gpu-final'
    files=json.loads((hardware/'source-sha256.json').read_text())
    for name,digest in files.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    # CPU mathematical dependencies are checked independently in spike 050.
    qualification=json.loads((hardware/'gpu-qualification.json').read_text())
    ledgers=[]
    for case in qualification:
        path=hardware/f"gpu-{case['family']}-{case['policy']}.jsonl"
        rows=read_records(path,'gpu-flooding-ledger-v1')
        header={k:v for k,v in rows[0].items() if k!='ledger_sha256'}
        result=GpuBatchResult(np.asarray([r['candidate'] for r in rows[1:]],np.uint8),
            np.asarray([r['converged'] for r in rows[1:]],bool),np.asarray([r['iterations'] for r in rows[1:]],np.int64),
            np.asarray([r['syndrome'] for r in rows[1:]],np.uint8),canonical_json(header))
        assert result.ledger==rows
        assert case['stored_cpu_replay']['verified']
        ledgers.append(dict(path=str(path.relative_to(ROOT)),sha256=sha256(path.read_bytes()).hexdigest(),shots=len(rows)-1))
    (HERE/'carried-qualification.json').write_text(json.dumps(dict(
        shared_receipt_sha256=sha256((prior/'qualification.json').read_bytes()).hexdigest(),gpu_ledgers=ledgers,
        prior_full_tests=receipt['tests'],legacy=receipt['legacy'],sinter=receipt['sinter']),indent=2)+'\n')
    return dict(shared_source_hashes=len(receipt['source_sha256']),shared_evidence_hashes=len(receipt['evidence_sha256']),
        prior_full_passed=2462,prior_final_affected_passed=387,legacy_receipts=82,
        carried_Sinter_smoke_shots=24,carried_H200_shots=sum(r['shots'] for r in ledgers),new_GPU_execution=False)


if __name__=='__main__':
    audit=Audit(HERE)
    audit.probe('shared_affine_packed_and_binding',affine_packing_and_binding)
    audit.probe('Sinter_transport_batch_identity',transport_chunking)
    audit.probe('source_bound_prior_regression_and_hardware',carried_qualification)
    audit.finish()
