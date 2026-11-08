"""Policy metamorphisms and executable admission counterexamples."""
from dataclasses import replace
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import numpy as np
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3, MIN_SUM_CPU_F64
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.quaternary.numerics import QBP4_F64_V3, pauli_hard_decision
from bp_registry.quaternary.schedules import QbpFloodingSchedule, QbpVariableSerialSchedule, QuaternaryCheckTransform

HERE=Path(__file__).parent
spec=spec_from_file_location('old_policy_probe',HERE.parent/'010-policy-extensibility/probe.py')
old=module_from_spec(spec);spec.loader.exec_module(old)

def metamorphisms():
    cases=0
    for damping in (0.,.1,.6,.95):
        profile=replace(QBP4_F64_V3,v2c_damping=damping)
        plain=old.fixture(profile);identity=old.fixture(profile)
        a=QbpFloodingSchedule(plain)
        b=QbpFloodingSchedule(identity,transforms=[QuaternaryCheckTransform.normalization(1.)])
        for _ in range(4):
            x=a.sweep().result;y=b.sweep().result
            for field in ('c2v','beliefs','v2c','candidate'):
                np.testing.assert_allclose(getattr(x,field),getattr(y,field),rtol=0,atol=2e-12)
            cases+=1
    u=QbpVariableSerialSchedule(old.fixture(replace(QBP4_F64_V3,v2c_damping=0.))).sweep().result
    d=QbpVariableSerialSchedule(old.fixture(replace(QBP4_F64_V3,v2c_damping=.6))).sweep().result
    assert np.max(abs(u.v2c-d.v2c))>1e-12
    norm=QuaternaryCheckTransform.normalization(2.);offset=QuaternaryCheckTransform.offset(.75)
    assert norm.apply(offset.apply(-3.))!=offset.apply(norm.apply(-3.))
    one=old.fixture(QBP4_F64_V3);two=old.fixture(QBP4_F64_V3);before=two.state_digest
    one.replace_prior(0,np.array([.01,.97,.01,.01]));one.sweep()
    assert two.state_digest==before and not two.problem.code.checks.flags.writeable
    rejected=[]
    for kwargs in (dict(schedule='layered'),dict(transforms=['normalized_min_sum']),dict(intervention='ambp4')):
        try:old.resolve_quaternary_composition(old.composition(**kwargs))
        except ValueError:rejected.append(kwargs)
    assert len(rejected)==3
    return dict(identity_comparisons=cases,serial_damping_observable=True,transform_order_observable=True,state_isolation=True,incompatible_rejections=rejected)

def profile_admission(a):
    h=np.array([[1,1,1]],dtype=np.uint8);incoming=np.array([1.,2.])
    scalar=BinarySpaKernel(profile=MIN_SUM_CPU_F64)
    actual=scalar.check_message(incoming,0)
    expected=BinarySpaKernel(update_rule=MinSumUpdate()).check_message(incoming,0)
    try:CompiledBinaryFlooding.from_check_matrix(h,profile=MIN_SUM_CPU_F64);rejected=False
    except ValueError:rejected=True
    a.record('V3-A01_scalar_profile_admission_matches_declared_min_sum',abs(actual-expected)<1e-12,
        declared=scalar.profile.as_evidence(),actual=actual,expected_min_sum=expected,compiled_rejects_same_pairing=rejected,
        scope='low-level scalar constructor; default and public literal profiles unaffected')

def metadata(a):
    profile=replace(BINARY_SPA_F64_V3,dtype='float32',exact_zero_decision=1)
    kernel=BinarySpaKernel(profile=profile)
    beliefs=kernel.assemble_beliefs(1,(),np.array([]),0.)
    decision=int(kernel.candidate_from_beliefs(beliefs)[0])
    q=replace(QBP4_F64_V3,candidate_tie_break='ties_Z_then_Y_then_X_then_I')
    qdecision=int(pauli_hard_decision([0.,0.,0.],profile=q))
    a.record('V3-A02_accepted_profile_metadata_describes_execution',
        str(beliefs.dtype)==profile.dtype and decision==profile.exact_zero_decision and qdecision==3,
        binary_declared=profile.as_evidence(),actual_dtype=str(beliefs.dtype),actual_zero_decision=decision,
        quaternary_declared=q.as_evidence(),actual_all_tie_decision=qdecision,
        scope='custom dataclass profiles accepted by low-level APIs; public manifest fields are closed')

if __name__=='__main__':
    a=Audit(HERE)
    a.probe('v3_composition_metamorphisms',metamorphisms)
    profile_admission(a);metadata(a)
    a.finish()
