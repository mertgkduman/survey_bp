"""Metamorphic composition checks beyond individual policy happy paths."""
from dataclasses import replace
from pathlib import Path
import numpy as np
from audit_support import Audit
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.numerics import QBP4_F64_V1,QBP4_F64_V2
from bp_registry.quaternary.problems import PauliCode,QuaternaryOriginalProblem
from bp_registry.quaternary.schedules import QbpFloodingSchedule,QbpVariableSerialSchedule,QuaternaryCheckTransform
from bp_registry.quaternary.compatibility import resolve_quaternary_composition
from bp_registry.quaternary.contracts import QuaternaryCompositionSpec,QuaternaryPolicySpec
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.canonical.memory import V2CDamping

def fixture(profile=QBP4_F64_V2):
    code=PauliCode(checks=np.array([[1,1,0],[1,0,1]],dtype=np.uint8))
    problem=QuaternaryOriginalProblem('original-policy-audit',code,np.array([1,1],dtype=np.uint8))
    priors=np.array([[.70,.10,.15,.05],[.55,.2,.1,.15],[.4,.15,.25,.2]])
    return ScalarLlrBp4Kernel(profile=profile).new_session(problem,priors)

def composition(schedule='qbp_flooding',transforms=(),intervention='identity'):
    return QuaternaryCompositionSpec(
        kernel=QuaternaryPolicySpec(kind='qbp_scalar_llr',binding_id='kernel'),
        schedule=QuaternaryPolicySpec(kind=schedule,binding_id='schedule'),
        transforms=tuple(QuaternaryPolicySpec(kind=t,binding_id=f't{i}',config={}) for i,t in enumerate(transforms)),
        intervention=QuaternaryPolicySpec(kind=intervention,binding_id='intervention'))

if __name__=='__main__':
    a=Audit(Path(__file__).parent)
    for profile in (QBP4_F64_V1,QBP4_F64_V2):
        plain=QbpFloodingSchedule(fixture(profile)).sweep().result
        identity=QbpFloodingSchedule(fixture(profile),transforms=[QuaternaryCheckTransform.normalization(1.)]).sweep().result
        delta={field:float(np.max(abs(getattr(plain,field)-getattr(identity,field)))) for field in ('c2v','beliefs','v2c')}
        a.record(f'identity_check_transform_preserves_full_sweep:{profile.profile_id}',max(delta.values())<1e-12,deltas=delta)
    undamped=QbpVariableSerialSchedule(fixture(replace(QBP4_F64_V2,v2c_damping=0.))).sweep().result
    damped=QbpVariableSerialSchedule(fixture(replace(QBP4_F64_V2,v2c_damping=.6))).sweep().result
    delta=float(np.max(abs(undamped.v2c-damped.v2c)))
    a.record('serial_schedule_honors_declared_v2_damping',delta>1e-12,max_v2c_difference=delta)
    norm=QuaternaryCheckTransform.normalization(2.); offset=QuaternaryCheckTransform.offset(.75)
    forward=offset.apply(norm.apply(-3.)); reverse=norm.apply(offset.apply(-3.))
    a.record('transform_order_is_observable',forward!=reverse,normalize_then_offset=forward,offset_then_normalize=reverse)
    first=fixture(); second=fixture(); before=second.state_digest
    first.replace_prior(0,np.array([.01,.97,.01,.01])); first.sweep()
    a.record('quaternary_session_state_isolation',before==second.state_digest)
    original=second.problem.code.checks.copy(); snapshot=second.last.v2c.copy(); second.sweep()
    a.record('original_problem_immutable_through_sweep',np.array_equal(original,second.problem.code.checks) and not second.problem.code.checks.flags.writeable)
    binding=V2CDamping('a',.7); foreign=V2CDamping('b',.7)
    proposal=binding.propose(np.ones(3),np.zeros(3),boundary='source_iteration')
    try:
        foreign.commit(proposal); rejected=False
    except ValueError: rejected=True
    a.record('memory_rejects_foreign_history_commit',rejected)
    for kind,kwargs in [('binary_schedule',dict(schedule='layered')),('binary_transform',dict(transforms=['normalized_min_sum'])),
                        ('undefined_adaptive_mbp4',dict(intervention='ambp4'))]:
        try:
            resolve_quaternary_composition(composition(**kwargs)); rejected=False; reason='accepted'
        except ValueError as exc: rejected=True; reason=str(exc)
        a.record('compatibility_rejects:'+kind,rejected,reason=reason)
    declared=resolve_quaternary_composition(composition(transforms=['qbp_c2v_normalization']),numerical_profile=QBP4_F64_V2.profile_id)
    a.record('admission_claims_damping_for_transformed_v2',True,equation=declared.equations.get('numerical_v2c'),
             interpretation='Cross-reference failed identity-transform check: admitted equation is not executed.')
    mixed=BinarySpaKernel(update_rule=MinSumUpdate())
    a.record('kernel_rejects_conflicting_update_and_numerical_profile',False,
             kernel_profile=mixed.profile.profile_id,update_profile=mixed.update_rule.profile.profile_id,
             interpretation='Direct constructor accepts SPA v2 profile with separately clipped v1 min-sum primitive; public closed registry may prevent it.')
    a.finish()
