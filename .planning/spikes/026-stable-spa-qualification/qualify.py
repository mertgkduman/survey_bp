"""Rerun prior independent controls into a new evidence destination."""
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from dataclasses import replace
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from audit_support import Audit

def load(name,directory):
    spec=spec_from_file_location(name,HERE.parent/directory/'probe.py')
    module=module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def main():
    a=Audit(HERE)
    mathematical=load('fixed_math','012-v3-mathematical-audit')
    upstream=load('fixed_upstream','013-v3-upstream-audit')
    execution=load('fixed_execution','015-v3-execution-audit')
    boundary=load('fixed_boundary','022-cpu-graph-integrity')
    boundary.HERE=HERE  # Never overwrite historical evidence.
    a.probe('historical_binary_probability_oracle',lambda:mathematical.recurrences(False))
    a.probe('historical_pauli_probability_oracle',lambda:mathematical.recurrences(True))
    a.probe('native_ldpc',upstream.ldpc_v3)
    a.probe('native_normalized_min_sum',upstream.normalized_min_sum)
    a.probe('native_Relay',upstream.native.relay_crosscheck)
    a.probe('native_aSCED_decision_classification',upstream.source_decisions)
    a.probe('native_aSCED_zero_classification',upstream.source_zero_checks)
    a.probe('historical_full_buffer_differentials',execution.old.buffer_differentials)
    execution.receipts(a)
    a.probe('historical_CPU_840_row_matrix',boundary.batch_matrix)
    boundary.legacy_cap(a)
    historical_policy=boundary.policy
    def compatible_policy(rule='sum_product',format='float64',shortcut=False):
        policy=historical_policy(rule,format,shortcut)
        return replace(policy,version='bp-flooding-policy-v3',check_stabilization='log_domain') if rule=='sum_product' else policy
    boundary.policy=compatible_policy
    boundary.HERE=HERE/'stable-controls'
    boundary.HERE.mkdir(exist_ok=True)
    a.probe('stable_CPU_control_matrix_with_v2_minsum_controls',boundary.batch_matrix)
    result=a.finish()
    raise SystemExit(bool(result['failed']))

if __name__=='__main__':main()
