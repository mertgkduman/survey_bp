"""Bound-state admission, finite-state execution, CPU isolation and ledger checks."""
from dataclasses import replace
from pathlib import Path
import gzip,json,tempfile,warnings
import numpy as np
from numba import get_num_threads
from audit_support import Audit
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64,ResolutionPolicy
HERE=Path(__file__).parent


def prior_admission(a):
    graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,2),dtype=np.uint8),policy=STABLE_SPA_F64)
    bound=graph.bind_error_rate(.2);s=np.array([0],dtype=np.uint8);rows=[]
    for value in (float('nan'),float('inf'),float('-inf')):
        try:
            replaced=replace(bound,prior=value);actual=replaced.run(s,max_iterations=0)
            rows.append(dict(value=str(value),rejected=False,candidate=actual.candidate,converged=actual.converged,iterations=actual.iterations))
        except (ValueError,ArithmeticError) as exc:rows.append(dict(value=str(value),rejected=True,error=type(exc).__name__))
    a.record('C03_bound_prior_validated_before_initial_shortcut',all(row['rejected'] for row in rows),rows=rows,
        scope='dataclass replacement of a correctly bound graph; only nonfinite prior changed')
    q=CompiledBp4Graph.from_code(PauliCode(checks=np.ones((1,2),dtype=np.uint8)),np.tile([.7,.1,.1,.1],(2,1)),policy=STABLE_SPA_F64)
    wide=np.full((2,3),np.longdouble('1e400'))
    assert np.all(np.isfinite(wide)), 'platform has no wider finite longdouble range; probe requires adaptation'
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            replaced=replace(q,prior_llrs=wide);finite=bool(np.all(np.isfinite(replaced.prior_llrs)))
            actual=replaced.run(np.zeros(1,dtype=np.uint8),max_iterations=0)
            details=dict(rejected=False,finite_stored_priors=finite,converged=actual.converged,candidate=actual.candidate,iterations=actual.iterations)
        except (ValueError,ArithmeticError) as exc:details=dict(rejected=True,error=type(exc).__name__)
    a.record('C03_stored_float64_priors_validated_after_conversion',details['rejected'] or details['finite_stored_priors'],
        details=details,warnings=[str(w.message) for w in caught],input_dtype=str(wide.dtype),input_finite=True)


def overflow_execution(a):
    p=replace(STABLE_SPA_F64,damping=0.,zero_syndrome_shortcut=False,resolution=ResolutionPolicy('float64',scope='scalar_edges'))
    base=CompiledBp4Graph.from_code(PauliCode(checks=np.ones((3,2),dtype=np.uint8)),np.tile([.7,.1,.1,.1],(2,1)),policy=p)
    graph=replace(base,prior_llrs=np.full((2,3),1e308));s=np.ones(3,dtype=np.uint8);rows=[];before=get_num_threads()
    sweep=graph.sweep(graph.initial_v2c(),s);assert not np.all(np.isfinite(sweep.beliefs))
    for mode in ('single','batch'):
        try:
            result=graph.run(s,max_iterations=1) if mode=='single' else graph.run_batch(np.array([s,s]),max_iterations=1,workers=2)
            rows.append(dict(path=mode,rejected=False,candidate=result.candidate if mode=='single' else result.candidates,iterations=result.iterations,converged=result.converged))
        except (ValueError,ArithmeticError,SystemError) as exc:rows.append(dict(path=mode,rejected=True,error=type(exc).__name__))
    assert before==get_num_threads()
    a.record('C01_overflow_is_reported_in_full_decode_and_batch',all(row['rejected'] for row in rows),rows=rows,
        scope='same shared sweep as spike 027; finite direct LLR graph state; initial shortcut disabled')


def cpu_isolation():
    rows=[];before=get_num_threads();stored=[]
    for family in ('binary','pauli'):
        h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8)
        if family=='binary':graph=CompiledBinaryFlooding.from_check_matrix(h,policy=STABLE_SPA_F64);extra={'error_rate':.2}
        else:graph=CompiledBp4Graph.from_code(PauliCode(checks=h),np.tile([.7,.1,.1,.1],(3,1)),policy=STABLE_SPA_F64);extra={}
        raw=np.array([[1,9,0,9],[0,9,1,9],[1,9,1,9]],dtype=np.uint8);syndromes=raw[:,::2];original=raw.copy()
        previous=None
        for workers in (1,2):
            result=graph.run_batch(syndromes,max_iterations=5,workers=workers,**extra)
            np.testing.assert_array_equal(raw,original);assert get_num_threads()==before
            candidates=[graph.run(s,max_iterations=5,**extra) for s in syndromes]
            np.testing.assert_array_equal(result.candidates,[c.candidate for c in candidates])
            np.testing.assert_array_equal(result.iterations,[c.iterations for c in candidates])
            if previous is not None:np.testing.assert_array_equal(result.candidates,previous)
            previous=result.candidates.copy()
            with tempfile.TemporaryDirectory(prefix='freeze-ledger-') as directory:
                path=Path(directory)/'events.jsonl';result.write_ledger(path);events=[json.loads(l) for l in path.read_text().splitlines()]
            for event in events:
                c=np.array(event['candidate'],dtype=np.uint8);s=np.array(event['syndrome'])
                observed=(h@c)%2 if family=='binary' else np.sum((h!=0)&(c[None,:]!=0)&(h!=c[None,:]),axis=1)%2
                assert bool(np.array_equal(observed,s))==event['candidate_valid']
                assert event['work']['check_to_variable_updates']==4*event['iterations']
                stored.append(event)
            empty=graph.run_batch(np.empty((0,2),dtype=np.uint8),max_iterations=0,workers=workers,**extra)
            assert empty.candidates.shape==(0,3) and len(empty.iterations)==0 and before==get_num_threads()
            rows.append(dict(family=family,workers=workers,noncontiguous_inputs_unchanged=True,empty_batch_shape=empty.candidates.shape))
    (HERE/'events.jsonl.gz').write_bytes(gzip.compress((''.join(json.dumps(e,sort_keys=True)+'\n' for e in stored)).encode(),mtime=0))
    return dict(cases=rows,ledger_rows=len(stored),thread_mask_restored=True)


def unary_epsilon_scope():
    rows=[]
    for degree in (1,2,4):
        results=[]
        for epsilon in (1e-4,1e-10):
            graph=CompiledBinaryFlooding.from_check_matrix(np.ones((1,degree),dtype=np.uint8),policy=replace(STABLE_SPA_F64,product_epsilon=epsilon))
            result=graph.sweep(np.full(degree,40.),np.zeros(1,dtype=np.uint8),error_rate=.2)
            results.append(result.check_to_variable)
        if degree==1:assert not np.array_equal(*results)
        else:np.testing.assert_array_equal(*results)
        rows.append(dict(degree=degree,small_unary_bound=results[0],large_unary_bound=results[1]))
    return dict(rows=rows,interpretation='epsilon is active only for the explicitly finite unary rule in stable policy v3')

if __name__=='__main__':
    a=Audit(HERE);prior_admission(a);overflow_execution(a);a.probe('CPU_input_isolation_and_empty_batches',cpu_isolation)
    a.probe('stable_epsilon_scope',unary_epsilon_scope);a.finish()
