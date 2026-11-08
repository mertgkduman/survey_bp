"""Audit valid-shape alternate construction and policy composition seams."""
from dataclasses import replace
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
import numpy as np
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3, MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import EdgeTable,FloodingSchedule,CheckNodeSerialSchedule,VariableNodeSerialSchedule
from bp_registry.canonical.execution import CanonicalLocalStepExecutor,ScheduleProgress
from bp_registry.canonical.budgets import BudgetTree
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.quaternary.numerics import QBP4_F64_V3, commutation_llr,check_message

HERE=Path(__file__).parent
H=np.ones((1,3),dtype=np.uint8);S=np.array([0],dtype=np.uint8)


def rejects(function):
    try:function()
    except ValueError:return True
    return False


def constructors(a):
    binary=CompiledBinaryFlooding.from_check_matrix(H)
    replaced=replace(binary,numerical_profile=MIN_SUM_CPU_F64)
    actual=replaced.sweep(np.array([1.,2.,3.]),S,error_rate=.2).check_to_variable
    q=CompiledBp4Graph.from_code(PauliCode(checks=H),np.tile([.7,.1,.1,.1],(3,1)))
    boxplus=replace(QBP4_F64_V3,check_rule='boxplus')
    changed=replace(q,profile=boxplus)
    qactual=changed.sweep(np.full((3,3),50.),S).c2v
    incoming=commutation_llr([50.,50.,50.],1,profile=boxplus)
    expected=check_message([incoming,incoming],syndrome=0,profile=boxplus)
    rows=[dict(family='binary',factory_rejects=rejects(lambda:CompiledBinaryFlooding.from_check_matrix(H,profile=MIN_SUM_CPU_F64)),
               replacement_accepted=True,declared=replaced.profile.as_evidence(),actual=actual,expected_min_sum=[2.,1.,1.]),
          dict(family='pauli',factory_rejects=rejects(lambda:CompiledBp4Graph.from_code(PauliCode(checks=H),np.tile([.7,.1,.1,.1],(3,1)),profile=boxplus)),
               replacement_accepted=True,declared=changed.profile.as_evidence(),actual=qactual,expected_boxplus=[expected]*3)]
    a.record('B01_alternate_graph_construction_preserves_admission',False,counterexamples=rows,
             scope='valid-shape graphs only; no unsafe malformed CSR execution; no mutation of historical data')
    a.record('normal_factories_reject_unqualified_pairings',all(row['factory_rejects'] for row in rows))


def schedule_profile(a):
    table=EdgeTable.from_check_matrix(H);kernel=BinarySpaKernel()
    mixed=FloodingSchedule(table,kernel=kernel,profile=MIN_SUM_CPU_F64)
    actual=mixed.sweep(np.array([1.,2.,3.]),S,error_rate=.2)
    aligned=FloodingSchedule(table,kernel=kernel).sweep(np.array([1.,2.,3.]),S,error_rate=.2)
    a.record('B01_schedule_profile_agrees_with_kernel_profile',False,
        kernel_profile=kernel.profile.profile_id,schedule_profile=mixed.profile.profile_id,
        actual_v2c=actual.new_v2c,aligned_v2c=aligned.new_v2c,
        interpretation='explicit conflicting schedule profile is accepted and bypasses v3 damping; same admission-root issue')


def serial_damping(a):
    rows=[];table=EdgeTable.from_check_matrix(np.array([[1,1,0],[0,1,1]],dtype=np.uint8))
    old=np.array([.3,-.6,1.2,.9]);syndrome=np.array([1,0],dtype=np.uint8)
    for kind in (CheckNodeSerialSchedule,VariableNodeSerialSchedule):
        plain=kind(table,kernel=BinarySpaKernel(profile=replace(BINARY_SPA_F64_V3,v2c_damping=0.)))
        damped=kind(table,kernel=BinarySpaKernel(profile=replace(BINARY_SPA_F64_V3,v2c_damping=.6)))
        left=old.copy();right=old.copy()
        for schedule,messages in ((plain,left),(damped,right)):
            executor=CanonicalLocalStepExecutor(BudgetTree(limits=(),parents={}),scope='attempt')
            result=schedule.execute_local_step(executor,messages,syndrome,error_rate=.2,
                progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False)
            assert result.admitted
        rows.append(dict(schedule=kind.__name__,undamped=left,damped=right,different=bool(np.any(left!=right))))
    a.record('B02_low_level_serial_honors_or_rejects_v3_damping',all(row['different'] for row in rows),counterexamples=rows,
             scope='budgeted public schedule API, low-level composition; public v3 binary manifest admission is flooding-only')


if __name__=='__main__':
    a=Audit(HERE);constructors(a);schedule_profile(a);serial_damping(a)
    spec=spec_from_file_location('qualified_policy_controls',HERE.parent/'014-v3-policy-audit/probe.py')
    controls=module_from_spec(spec);spec.loader.exec_module(controls)
    a.probe('qualified_quaternary_policy_metamorphisms',controls.metamorphisms)
    a.finish()
