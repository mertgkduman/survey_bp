from pathlib import Path
from dataclasses import replace
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64
from bp_registry.canonical.updates import NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment
from bp_registry.canonical.schedules import EdgeTable,FloodingSchedule,LayeredSchedule,CheckNodeSerialSchedule,VariableNodeSerialSchedule
from bp_registry.canonical.execution import CanonicalLocalStepExecutor,ScheduleProgress
from bp_registry.canonical.budgets import BudgetTree
HERE=Path(__file__).parent
H=np.ones((2,2),dtype=np.uint8);S=np.array([0,1],dtype=np.uint8);TABLE=EdgeTable.from_check_matrix(H)

class RecordingRule:
    profile=MIN_SUM_CPU_F64
    def __init__(self,rule):self.rule=rule;self.calls=[]
    def __getattr__(self,name):return getattr(self.rule,name)
    def check_to_variable(self,incoming,**kwargs):
        self.calls.append(dict(kwargs));return self.rule.check_to_variable(incoming,**kwargs)


def indexed_updates(a):
    for kind in ('nms','oms'):
        assignment=ParameterAssignment(shape='source_iteration',values=(.2,.8,.4))
        make=lambda:NormalizedMinSumUpdate(alpha=assignment) if kind=='nms' else OffsetMinSumUpdate(beta=assignment)
        rule=RecordingRule(make());kernel=BinarySpaKernel(update_rule=rule)
        kernel.run(H,S,error_rate=.2,max_iterations=3)
        observed=sorted(set(r['source_iteration'] for r in rule.calls))
        a.record(f'D01_{kind}_standalone_iteration_context',observed==[0,1,2],observed=observed,expected=[0,1,2],calls=len(rule.calls),syndrome_inconsistent=True)
        # Explicit sweep is the positive control for the same update object.
        f=FloodingSchedule(TABLE,kernel=BinarySpaKernel(update_rule=make()))
        outputs=[f.sweep(np.array([1.,2.,3.,4.]),S,error_rate=.2,source_iteration=i).check_to_variable for i in (0,1)]
        a.record(f'{kind}_explicit_flooding_context',not np.array_equal(*outputs),outputs=outputs)
        from bp_registry.canonical.execution import AtomicFloodingExecutor
        control=RecordingRule(make());schedule=FloodingSchedule(TABLE,kernel=BinarySpaKernel(update_rule=control))
        AtomicFloodingExecutor(schedule,BudgetTree(limits=()),scope='attempt').run_attempt(np.ones(4),S,error_rate=.2,max_iterations=3)
        seen=sorted(set(row['source_iteration'] for row in control.calls))
        a.record(f'{kind}_atomic_flooding_iteration_control',seen==[0,1,2],observed=seen)
        for schedule_type in (LayeredSchedule,CheckNodeSerialSchedule,VariableNodeSerialSchedule):
            rule=RecordingRule(make());kernel=BinarySpaKernel(update_rule=rule)
            kwargs=dict(partitions=((0,),(1,)),provenance='explicit') if schedule_type is LayeredSchedule else {}
            schedule=schedule_type(TABLE,kernel=kernel,**kwargs)
            schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()),scope='attempt'),np.array([1.,2.,3.,4.]),S,error_rate=.2,
                progress=ScheduleProgress(iteration=1,local_steps=2,cursor=(0,)),is_converged=lambda _:False)
            observed=sorted(set(r['source_iteration'] for r in rule.calls))
            a.record(f'D01_{kind}_{schedule_type.__name__}_iteration_context',observed==[1],observed=observed,expected=[1])


def reported_posterior(a):
    for schedule_type in (CheckNodeSerialSchedule,VariableNodeSerialSchedule):
        kernel=BinarySpaKernel(profile=MIN_SUM_CPU_F64,update_rule=NormalizedMinSumUpdate(alpha=ParameterAssignment(shape='scalar',value=1.)))
        schedule=schedule_type(TABLE,kernel=kernel);messages=np.array([1.,2.,3.,4.]);seen=[]
        def transform(beliefs,c2v):
            out=beliefs+np.array([-8.,3.]);seen.append(out.copy());return out
        result=schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()),scope='attempt'),messages,np.array([0,0]),error_rate=.2,
            progress=ScheduleProgress(iteration=0,local_steps=0,cursor=(0,)),is_converged=lambda _:False,
            prior_llrs=np.array([-2.,4.]),transform_beliefs=transform)
        a.record(f'D02_{schedule_type.__name__}_reported_posterior',np.array_equal(result.posterior,seen[0]),actual=result.posterior,expected=seen[0],candidate=result.candidate)

if __name__=='__main__':
    a=Audit(HERE);indexed_updates(a);reported_posterior(a);a.finish()
