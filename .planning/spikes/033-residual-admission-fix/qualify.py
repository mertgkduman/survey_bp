"""Rerun independent retained oracles without changing historical evidence."""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from audit_support import Audit


def load(folder):
    spec = spec_from_file_location(folder.replace('-', '_'), HERE.parent / folder / 'probe.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    a = Audit(HERE)
    math = load('027-stable-spa-stress-audit')
    upstream = load('028-stable-upstream-audit')
    schedules = load('029-schedule-policy-closure')
    execution = load('030-freeze-execution-audit')
    execution.HERE = HERE  # CPU ledger belongs to this qualification, never spike 030.
    for name, function in (
        ('multi_check_tree_inference', math.tree_inference),
        ('mixed_magnitude_parity_and_permutations', math.mixed_envelope),
        ('Pauli_label_covariance', math.pauli_covariance),
        ('stable_SPA_aligned_native_ldpc', upstream.aligned_native),
        ('stable_SPA_high_confidence_oracle', upstream.high_confidence),
        ('source_phi_bound_classification', upstream.source_phi),
        ('native_NMS_controls', upstream.native.normalized_min_sum),
        ('native_Relay_inner_memory_controls', upstream.native.native.relay_crosscheck),
        ('native_aSCED_zero_classification', upstream.native.source_zero_checks),
        ('fixed_local_schedule_damping_controls', schedules.local_controls),
        ('residual_source_scope_and_budget_denial', schedules.residual_source_scope),
        ('public_stable_policy_boundary', schedules.public_scope),
        ('intervention_policy_admission', schedules.intervention_admission),
        ('CPU_input_isolation_and_empty_batches', execution.cpu_isolation),
        ('unary_epsilon_scope', execution.unary_epsilon_scope),
    ):
        a.probe(name, function)
    math.overflow(a)
    execution.prior_admission(a)
    result = a.finish()
    raise SystemExit(bool(result['failed']))
