"""Post-fix qualification without overwriting the historical audit findings."""
from dataclasses import replace
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import json
import numpy as np
from audit_support import Audit
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3, MIN_SUM_CPU_F64
from bp_registry.quaternary.numerics import QBP4_F64_V3

HERE = Path(__file__).parent


def load(name, directory):
    spec = spec_from_file_location(name, HERE.parent / directory / 'probe.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejects(function):
    try:
        function()
    except ValueError:
        return True
    raise AssertionError('inconsistent configuration was admitted')


def admission():
    for profile in (MIN_SUM_CPU_F64, replace(MIN_SUM_CPU_F64, saturation=20.)):
        rejects(lambda: BinarySpaKernel(profile=profile))
        rejects(lambda: CompiledBinaryFlooding.from_check_matrix(np.array([[1, 1, 1]], dtype=np.uint8), profile=profile))
    return dict(rejected_constructors=4)


def metadata():
    rejects(lambda: replace(BINARY_SPA_F64_V3, dtype='float32'))
    rejects(lambda: replace(BINARY_SPA_F64_V3, exact_zero_decision=1))
    rejects(lambda: replace(QBP4_F64_V3, candidate_tie_break='ties_Z_then_Y_then_X_then_I'))
    return dict(rejected_misleading_profiles=3,exhaustive_fixed_fields='tests/canonical/test_kernel_contract_admission.py')


if __name__ == '__main__':
    a = Audit(HERE)
    math = load('math_audit', '012-v3-mathematical-audit')
    upstream = load('upstream_audit', '013-v3-upstream-audit')
    policy = load('policy_audit', '014-v3-policy-audit')
    execution = load('execution_audit', '015-v3-execution-audit')
    a.probe('V3-A01_fixed', admission)
    a.probe('V3-A02_fixed', metadata)
    a.probe('binary_probability_oracle', lambda: math.recurrences(False))
    a.probe('pauli_probability_oracle', lambda: math.recurrences(True))
    a.probe('MAP_equality_patterns', math.ties)
    a.probe('finite_priors', math.finite_priors)
    a.probe('float16_boundaries', math.float16_boundaries)
    a.probe('unchanged_exact_unity_approximation', math.safeguard_characterization)
    a.probe('native_ldpc', upstream.ldpc_v3)
    a.probe('native_normalized_min_sum', upstream.normalized_min_sum)
    a.probe('native_Relay', upstream.native.relay_crosscheck)
    a.probe('native_aSCED_decision_classification', upstream.source_decisions)
    a.probe('native_aSCED_zero_check_classification', upstream.source_zero_checks)
    a.probe('policy_metamorphisms', policy.metamorphisms)
    a.probe('full_buffer_differentials', execution.old.buffer_differentials)
    execution.receipts(a)
    result = a.finish()
    raise SystemExit(bool(result['failed']))
