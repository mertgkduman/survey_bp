"""Backend and lifecycle metamorphic checks, with all counterexamples retained."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import json
import tempfile
import numpy as np
from audit_support import Audit, ROOT
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import REFERENCE_CPU_F64, BINARY_SPA_F64_V2
from bp_registry.canonical.schedules import EdgeTable,FloodingSchedule
from bp_registry.canonical.budgets import BudgetLimit,BudgetTree
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.numerics import QBP4_F64_V1,QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCode,QuaternaryOriginalProblem
from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy

def buffer_differentials():
    rng=np.random.default_rng(110611); count=0; maximum=0.
    for _ in range(12):
        h=(rng.random((3,6))<.6).astype(np.uint8)
        # Exclude unary checks here; dedicated edge cases below.
        for row in h:
            if row.sum()<2: row[:2]=1
        s=rng.integers(0,2,3,dtype=np.uint8); p=float(rng.uniform(.05,.8))
        for profile in (REFERENCE_CPU_F64,BINARY_SPA_F64_V2):
            scalar=BinarySpaKernel(profile=profile); schedule=FloodingSchedule(EdgeTable.from_check_matrix(h),kernel=scalar,profile=profile)
            compiled=CompiledBinaryFlooding.from_check_matrix(h,profile=profile)
            old=schedule.initialize(p)
            for _ in range(4):
                left=schedule.sweep(old,s,error_rate=p); right=compiled.sweep(old,s,error_rate=p)
                for field in ('check_to_variable','beliefs','new_v2c'):
                    delta=float(np.max(abs(getattr(left,field)-getattr(right,field))))
                    maximum=max(maximum,delta); assert delta<2e-11
                old=left.new_v2c; count+=1
        # Each column has a consistent Pauli label, so all rows commute.
        labels=rng.integers(1,4,6,dtype=np.uint8)
        code=PauliCode(checks=h*labels[None,:]); priors=rng.dirichlet(np.ones(4)*2,size=6)
        for profile in (QBP4_F64_V1,QBP4_F64_V2):
            session=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-backend-audit',code,s),priors)
            compiled=CompiledBp4Graph.from_code(code,priors,profile=profile); old=compiled.initial_v2c()
            for _ in range(4):
                left=session.sweep(stop_on_convergence=False); right=compiled.sweep(old,s)
                for field in ('c2v','beliefs','v2c','marginals'):
                    delta=float(np.max(abs(getattr(left,field)-getattr(right,field))))
                    maximum=max(maximum,delta); assert delta<2e-11
                old=left.v2c; count+=1
    return dict(seed=110611,sweeps=count,max_absolute_error=maximum)

def result_dict(result):
    return dict(candidate=result.candidate.tolist(),converged=bool(result.converged),
                iterations=int(result.iteration if hasattr(result,'iteration') else result.iterations))

def boundaries(a):
    h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8)
    for profile in (REFERENCE_CPU_F64,BINARY_SPA_F64_V2):
        for cap,p in ((0,.8),(2,.8)):
            matrix=h if cap==0 else np.zeros((1,3),dtype=np.uint8)
            s=np.zeros(len(matrix),dtype=np.uint8)
            left=BinarySpaKernel(profile=profile).run(matrix,s,error_rate=p,max_iterations=cap)
            right=CompiledBinaryFlooding.from_check_matrix(matrix,profile=profile).run(s,error_rate=p,max_iterations=cap)
            a.record(f'binary_initial_candidate:{profile.profile_id}:cap={cap}',result_dict(left)==result_dict(right),
                     scalar=result_dict(left),compiled=result_dict(right),p=p,matrix=matrix)
    code=PauliCode(checks=np.array([[1,1]],dtype=np.uint8))
    priors=np.array([[.1,.6,.2,.1],[.1,.6,.2,.1]])
    s=np.array([0],dtype=np.uint8)
    for profile in (QBP4_F64_V1,QBP4_F64_V2):
        for cap in (0,2):
            left=ScalarLlrBp4Kernel(profile=profile).new_session(QuaternaryOriginalProblem('original-prior-audit',code,s),priors).run(max_iterations=cap)
            right=CompiledBp4Graph.from_code(code,priors,profile=profile).run(s,max_iterations=cap)
            a.record(f'pauli_initial_candidate:{profile.profile_id}:cap={cap}',result_dict(left)==result_dict(right),
                     scalar=result_dict(left),compiled=result_dict(right),priors=priors,checks=code.checks)

def budget_work(a):
    code=PauliCode(checks=np.array([[1,1,0],[1,0,1]],dtype=np.uint8))
    problem=QuaternaryOriginalProblem('original-budget-audit',code,np.array([1,1],dtype=np.uint8))
    priors=np.tile([.7,.1,.15,.05],(3,1))
    for profile in (QBP4_F64_V1,QBP4_F64_V2):
        budget=BudgetTree(limits=(BudgetLimit('attempt','bp_calls',1),),parents={})
        session=ScalarLlrBp4Kernel(profile=profile).new_session(problem,priors,budgets=budget)
        session.sweep(stop_on_convergence=False); digest=session.state_digest
        capped=session.sweep(stop_on_convergence=False)
        a.record(f'capped_snapshot_retains_committed_work:{profile.profile_id}',capped.work==budget.summary('attempt'),
                 snapshot=capped.work.as_evidence(structural_event_version=4),
                 committed=budget.summary('attempt').as_evidence(structural_event_version=4),terminal=capped.terminal)
        a.record(f'denied_sweep_preserves_messages:{profile.profile_id}',digest==session.state_digest)

def explicit_policy_equivalence(a):
    h=np.array([[1,1,0],[0,1,1]],dtype=np.uint8); s=np.array([0,1],dtype=np.uint8)
    profile=replace(BINARY_SPA_F64_V2,v2c_damping=.1)
    plain=CompiledBinaryFlooding.from_check_matrix(h,profile=profile)
    policy=BpFloodingPolicy(check_rule='sum_product',resolution=ResolutionPolicy('float64'),damping=.1,
                           hard_decision='strict_pauli',zero_syndrome_shortcut=False)
    explicit=CompiledBinaryFlooding.from_check_matrix(h,profile=profile,policy=policy)
    old=np.full(4,30.)
    left=plain.sweep(old,s,error_rate=.1); right=explicit.sweep(old,s,error_rate=.1)
    a.record('explicit_float64_spa_preserves_v2_check_rule',np.allclose(left.check_to_variable,right.check_to_variable,rtol=0,atol=2e-11),
             plain=left.check_to_variable,policy=right.check_to_variable,
             explanation='Plain v2 clamps only exact unity; compiled BpFloodingPolicy clamps every product beyond 1-epsilon.')

def public_evidence(a,schema):
    from bp_registry.runner import run_quaternary,verify_quaternary_run
    from bp_registry.quaternary.execution import _sample,_digest,TracerPauliProblem,syndrome_for
    base=json.loads((ROOT/'data/manifests/quaternary-five-qubit-tracer.json').read_text())
    base['schema_version']=schema
    base['composition']={
        'kernel':{'kind':'qbp_scalar_llr','binding_id':'kernel'},
        'schedule':{'kind':'qbp_flooding','binding_id':'schedule'},'transforms':[],
        'intervention':{'kind':'identity','binding_id':'intervention'}}
    base['max_iterations']=5; base['max_work']=1
    # Deterministic public observations are generated from the declared sample identity.
    # Search fixture IDs, retaining the first capped example, not performance selection.
    examples=[]
    for index in range(20):
        data=json.loads(json.dumps(base)); data['run_id']=f'audit-budget-{index}'
        channel=np.tile([.7,.1,.1,.1],(5,1)); data['channel']['probabilities']=channel.tolist()
        physical=_digest({'checks':data['problem']['checks'],'channel':channel.tolist(),'run_id':data['run_id']})
        hidden=_sample(channel,seed_identity=f'{physical}:shot:0')
        problem=TracerPauliProblem(np.array(data['problem']['checks'],dtype=np.uint8),np.zeros(4,dtype=np.uint8))
        data['problem']['syndrome']=syndrome_for(problem,hidden).tolist()
        with tempfile.TemporaryDirectory(prefix='bp-audit-public-') as tmp:
            result=run_quaternary(data,tmp)
            replay=verify_quaternary_run(tmp)
            events=[json.loads(row) for row in (Path(tmp)/'events.jsonl').read_text().splitlines()]
            if result['termination']!='work_budget_exhausted': continue
            work=next(e['data']['work'] for e in events if e['kind']=='scalar_schedule')
            a.record(f'public_capped_ledger_retains_executed_sweep_work:{schema}',work['bp_calls']==1,
                     manifest=data,result=result,ledger_work=work,replay=replay)
            # Store the complete small failing public evidence bundle for independent review.
            bundle=Path(__file__).parent/f'{schema}-budget-counterexample'; bundle.mkdir(exist_ok=True)
            (bundle/'input.json').write_text(json.dumps(data,indent=2)+'\n')
            for file in Path(tmp).iterdir():
                if file.is_file(): (bundle/file.name).write_bytes(file.read_bytes())
            # Preserve the original receipt, then relocate only filesystem metadata
            # so the retained bundle can be replayed after the temp directory closes.
            receipt_path=bundle/'result.json'
            (bundle/'original-result.json').write_bytes(receipt_path.read_bytes())
            receipt=json.loads(receipt_path.read_text())
            receipt['manifest_path']=str((bundle/'manifest.json').resolve())
            receipt['output']=str(bundle.resolve())
            receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
            a.events[-1]['retained_bundle_replay']=verify_quaternary_run(bundle)
            break
    else: raise AssertionError('no capped public fixture found')

if __name__=='__main__':
    a=Audit(Path(__file__).parent)
    a.probe('randomized_scalar_compiled_buffers',buffer_differentials)
    boundaries(a); budget_work(a); explicit_policy_equivalence(a)
    for schema in ('quaternary_experiment_v2','quaternary_experiment_v3'):
        a.probe(f'public_capped_replay_probe_executed:{schema}',lambda schema=schema:public_evidence(a,schema))
    a.finish()
