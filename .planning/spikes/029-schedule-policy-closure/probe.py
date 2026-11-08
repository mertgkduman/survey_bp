"""Sensitivity/admission audit across schedule families and policy versions."""
from dataclasses import replace
from pathlib import Path
import numpy as np
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3,REFERENCE_CPU_F64
from bp_registry.canonical.schedules import EdgeTable,FloodingSchedule,CheckNodeSerialSchedule,VariableNodeSerialSchedule,LayeredSchedule
from bp_registry.canonical.residual import SyndromeResidualSchedule
from bp_registry.canonical.budgets import BudgetTree
from bp_registry.canonical.execution import CanonicalLocalStepExecutor,ScheduleProgress
from bp_registry.resolution import STABLE_SPA_F64
from bp_registry.research.contracts import _policy

HERE=Path(__file__).parent
H=np.ones((2,2),dtype=np.uint8);TABLE=EdgeTable.from_check_matrix(H)
OLD=np.array([1.,2.,3.,4.]);S=np.zeros(2,dtype=np.uint8)


def residual(weight,profile=BINARY_SPA_F64_V3):
    p=replace(profile,v2c_damping=weight)
    schedule=SyndromeResidualSchedule(TABLE,kernel=BinarySpaKernel(profile=p));messages=OLD.copy();c2v=np.zeros(4)
    cache=schedule.initialize(messages,c2v,S,error_rate=.2)
    proposal=schedule.propose_local_step(messages,c2v,cache,S,error_rate=.2)
    result=schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()),scope='attempt'),proposal,
        v2c=messages,c2v=c2v,cache=cache,progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
    return messages,result


def residual_sensitivity(a):
    left,l=residual(0.);right,r=residual(.6)
    selected=l.selection.index;variable=l.selection.edge[1]
    changed=[i for i,(_,v) in enumerate(TABLE.edges) if v==variable and i!=selected]
    expected=left.copy();expected[changed]=.6*OLD[changed]+.4*left[changed]
    a.record('C02_residual_damping_is_applied_or_rejected',not np.array_equal(left,right),
        selected_edge=selected,changed_edges=changed,undamped=left,damping_point_six=right,declared_damped_expected=expected,
        interpretation='conventional sRBP may intentionally be undamped; then admitting a damped profile must be rejected, not silently ignored')


def local_controls():
    rows=[]
    for kind in (FloodingSchedule,CheckNodeSerialSchedule,VariableNodeSerialSchedule,LayeredSchedule):
        outputs=[]
        for damping in (0.,.6):
            kernel=BinarySpaKernel(profile=replace(BINARY_SPA_F64_V3,v2c_damping=damping))
            kwargs={'partitions':((0,),(1,)),'provenance':'explicit'} if kind is LayeredSchedule else {}
            schedule=kind(TABLE,kernel=kernel,**kwargs);messages=OLD.copy()
            if kind is FloodingSchedule:messages=schedule.sweep(messages,S,error_rate=.2).new_v2c
            else:schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()),scope='attempt'),messages,S,error_rate=.2,
                progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
            outputs.append(messages)
        np.testing.assert_allclose(outputs[1],.6*OLD+.4*outputs[0],atol=2e-12,rtol=0)
        assert not np.array_equal(*outputs)
        rows.append(dict(schedule=kind.__name__,undamped=outputs[0],damped=outputs[1]))
    return dict(rows=rows,tolerance=2e-12,scope='one full flooding sweep or one budgeted local unit; unaffected edges remain unchanged')


def residual_source_scope():
    schedule=SyndromeResidualSchedule(TABLE,kernel=BinarySpaKernel(profile=REFERENCE_CPU_F64))
    state=OLD.copy();c2v=np.zeros(4);cache=schedule.initialize(state,c2v,S,error_rate=.2)
    proposal=schedule.propose_local_step(state,c2v,cache,S,error_rate=.2)
    assert proposal.selection.index==2
    assert proposal.decode_work.variable_to_check_updates==1
    before=state.copy()
    # Budget denial must not mutate state or consume a proposal.
    from bp_registry.canonical.budgets import BudgetLimit
    executor=CanonicalLocalStepExecutor(BudgetTree(limits=(BudgetLimit('attempt','check_to_variable_updates',0),)),scope='attempt')
    result=schedule.execute_local_step(executor,proposal,v2c=state,c2v=c2v,cache=cache,
        progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
    assert not result.admitted;np.testing.assert_array_equal(state,before)
    return dict(source_profile='explicit v1',selected_edge=2,denied_proposal_preserves_state=True)


def public_scope():
    try:_policy(STABLE_SPA_F64.as_spec(),rule='sum_product')
    except ValueError as exc:reason=str(exc)
    else:raise AssertionError('legacy research contract unexpectedly admits new stable policy')
    return dict(rejected=True,reason=reason,classification='intentional version boundary; stable policy remains compiled API only',
        implication='HTML must expose capabilities explicitly rather than label every generic entry point as stable SPA')

def intervention_admission():
    from bp_registry.canonical.compiled import CompiledBinaryFlooding
    from bp_registry.quaternary.compiled import CompiledBp4Graph
    from bp_registry.quaternary.numerics import QBP4_F64_V2
    from bp_registry.quaternary.problems import PauliCode
    binary=CompiledBinaryFlooding.from_check_matrix(H,policy=STABLE_SPA_F64)
    pauli=CompiledBp4Graph.from_code(PauliCode(checks=H),np.tile([.7,.1,.1,.1],(2,1)),profile=QBP4_F64_V2,policy=STABLE_SPA_F64)
    reasons=[]
    for call in (lambda:binary.run_paper_bpgd(S,error_rate=.2,sweeps_per_round=1),lambda:pauli.run_qbpgd(S,iterations_per_round=1)):
        try:call()
        except ValueError as exc:reasons.append(str(exc))
        else:raise AssertionError('unqualified stable-policy intervention was admitted')
    return dict(rejected=2,reasons=reasons)

if __name__=='__main__':
    a=Audit(HERE);residual_sensitivity(a);a.probe('fixed_local_schedule_damping_controls',local_controls)
    a.probe('residual_source_scope_and_budget_denial',residual_source_scope);a.probe('public_stable_policy_boundary',public_scope);a.probe('intervention_policy_admission',intervention_admission);a.finish()
