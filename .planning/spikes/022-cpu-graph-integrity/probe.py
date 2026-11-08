"""CPU boundary matrix with independent stopping/work and algebraic validity."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import gzip,json,tempfile
import numpy as np
from numba import get_num_threads
from audit_support import Audit,serial
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V1
from bp_registry.quaternary.problems import PauliCode,QuaternaryOriginalProblem
from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy

HERE=Path(__file__).parent


def policy(rule='sum_product',format='float64',shortcut=False):
    return BpFloodingPolicy(check_rule=rule,resolution=ResolutionPolicy(format,8 if format=='int8' else None,'all_state'),
        damping=.2,alpha=.8 if rule=='min_sum' else 1.,beta=.15 if rule=='min_sum' else 0.,
        hard_decision='map_pauli',zero_syndrome_shortcut=shortcut,version='bp-flooding-policy-v2',
        check_stabilization='exact_unity',product_epsilon=1e-10)


def valid(h,candidate,syndrome,family):
    if family=='binary':measured=(h.astype(np.int64)@candidate.astype(np.int64))%2
    else:measured=np.sum((h!=0)&(candidate[None,:]!=0)&(h!=candidate[None,:]),axis=1)%2
    return bool(np.array_equal(measured,syndrome))


def reference(graph,h,syndrome,family,limit,stop):
    # Reuse one-sweep numerical primitive; independently express decode control flow.
    p=graph.policy;checks=0;n=h.shape[1]
    if family=='binary':
        prior=np.log1p(-.8)-np.log(.8)
        initial=p.resolution.quantize(prior) if p and p.resolution.scope=='all_state' else prior
        candidate=np.full(n,int(initial<0),dtype=np.uint8)
        old=np.full(len(graph.variables),p.resolution.quantize(prior) if p else prior)
    else:
        llrs=np.array(graph.prior_llrs,copy=True)
        if p and p.resolution.scope=='all_state':
            llrs=np.array([[p.resolution.quantize(x) for x in row] for row in llrs])
        candidate=np.argmin(np.column_stack((np.zeros(n),llrs)),axis=1).astype(np.uint8)
        old=graph.initial_v2c()
    def check():
        nonlocal checks
        checks+=1;return valid(h,candidate,syndrome,family)
    if family=='binary' and p is None and len(graph.variables)==0:
        return candidate,0,check(),checks
    if p and p.zero_syndrome_shortcut and stop and check():
        return candidate,0,True,checks
    for iteration in range(1,limit+1):
        result=graph.sweep(old,syndrome,**({'error_rate':.8} if family=='binary' else {}))
        candidate=result.candidate;old=result.new_v2c if family=='binary' else result.v2c
        if stop and check():return candidate,iteration,True,checks
    return candidate,limit,check(),checks


def batch_matrix():
    masks=[np.zeros((2,3),dtype=np.uint8),np.array([[1,0,0],[0,1,0]],dtype=np.uint8),np.array([[1,1,0],[0,1,1]],dtype=np.uint8)]
    policies=[None,policy(),policy(shortcut=True),policy('min_sum',shortcut=True),policy('min_sum','int8',True)]
    syndromes=np.array(list(product((0,1),repeat=2)),dtype=np.uint8)
    entries=[];batches=0;previous=get_num_threads()
    with tempfile.TemporaryDirectory(prefix='bp-boundary-ledger-') as temporary:
        ledger=Path(temporary)/'events.jsonl'
        for family,mask,p,limit in product(('binary','pauli'),masks,policies,(0,1,4)):
            if family=='pauli' and not np.any(mask):
                try:PauliCode(checks=mask)
                except ValueError:continue
                raise AssertionError('identity-only Pauli rows unexpectedly admitted')
            h=mask if family=='binary' else mask*np.array([1,3,2],dtype=np.uint8)
            if family=='binary':
                graph=CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum' if p and p.check_rule=='min_sum' else 'spa',policy=p)
            else:graph=CompiledBp4Graph.from_code(PauliCode(checks=h),np.tile([.1,.6,.2,.1],(3,1)),policy=p)
            arrays=[v for v in vars(graph).values() if isinstance(v,np.ndarray)]
            before=[v.tobytes() for v in arrays]
            for stop,workers in product((True,) if family=='binary' else (True,False),(1,2)):
                kwargs={'error_rate':.8} if family=='binary' else {'stop_on_convergence':stop}
                batch=graph.run_batch(syndromes,max_iterations=limit,workers=workers,**kwargs)
                assert get_num_threads()==previous and not batch.candidates.flags.writeable
                batch.write_ledger(ledger);rows=[json.loads(x) for x in ledger.read_text().splitlines()]
                for shot,(s,row) in enumerate(zip(syndromes,rows,strict=True)):
                    candidate,iterations,ok,checks=reference(graph,h,s,family,limit,stop)
                    np.testing.assert_array_equal(batch.candidates[shot],candidate)
                    assert batch.iterations[shot]==iterations and batch.converged[shot]==ok
                    assert row['candidate_valid']==valid(h,np.array(row['candidate']),s,family)
                    work=row['work'];edges=int(np.count_nonzero(h));n=h.shape[1]
                    assert work['bp_calls']==iterations
                    assert work['convergence_checks']==checks
                    assert work['candidate_constructions']==iterations+1
                    assert work['candidate_checks']==n*(iterations+1)
                    assert work['belief_assemblies']==n*iterations
                    assert work['check_to_variable_updates']==work['variable_to_check_updates']==edges*iterations
                    entries.append(dict(checks=h.tolist(),**row))
                assert all(not v.flags.writeable and v.tobytes()==old for v,old in zip(arrays,before,strict=True))
                batches+=1
    payload=''.join(json.dumps(row,sort_keys=True)+'\n' for row in entries).encode()
    (HERE/'events.jsonl.gz').write_bytes(gzip.compress(payload,mtime=0))
    return dict(batches=batches,ledger_rows=len(entries),independent_controls='initial decisions, algebraic syndrome validity, stopping and work counts',
                graphs=['binary_empty','unary_plus_isolated','degree_two_tree'],workers=[1,2],caps=[0,1,4],immutable_graph_buffers=True,
                excluded_graph='identity-only Pauli rows correctly rejected by PauliCode')


def legacy_cap(a):
    h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8);s=np.array([1,0],dtype=np.uint8)
    code=PauliCode(checks=h);priors=np.tile([.97,.01,.01,.01],(3,1));profile=replace(QBP4_F64_V1,saturation=1.)
    session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-cap-audit',code,s),priors)
    scalar=session.sweep(stop_on_convergence=False);graph=CompiledBp4Graph.from_code(code,priors,profile=profile)
    compiled=graph.sweep(graph.initial_v2c(),s)
    error=float(np.max(abs(scalar.beliefs-compiled.beliefs)))
    a.record('B03_compiled_BP4_honors_accepted_v1_saturation',error<2e-11,
        profile=profile.as_evidence(),checks=h,syndrome=s,priors=priors,scalar_beliefs=scalar.beliefs,
        compiled_beliefs=compiled.beliefs,max_difference=error,
        scope='accepted nondefault v1 parameter through normal factory; default v1/v3 not implicated')


def failure_propagation():
    p=replace(policy('min_sum'),alpha=1e308)
    graph=CompiledBinaryFlooding.from_check_matrix(np.array([[1]],dtype=np.uint8),rule='min_sum',policy=p)
    previous=get_num_threads();failures=[]
    for kind in ('single','batch'):
        try:
            if kind=='single':graph.run(np.array([1],dtype=np.uint8),error_rate=.2,max_iterations=1)
            else:graph.run_batch(np.array([[1],[1]],dtype=np.uint8),error_rate=.2,max_iterations=1,workers=2)
        except Exception as exc:failures.append(dict(path=kind,exception=type(exc).__name__))
        else:raise AssertionError('overflow was returned as a decoded batch')
        assert get_num_threads()==previous
    return dict(failures=failures,thread_mask_restored=True,
                limitation='batch overflow surfaces as Numba SystemError rather than normalized domain failure; no decoded outputs returned')


if __name__=='__main__':
    a=Audit(HERE);a.probe('CPU_boundary_matrix',batch_matrix);legacy_cap(a);a.probe('overflow_fails_and_restores_threads',failure_propagation);a.finish()
