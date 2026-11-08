"""Replay audit probes into new directories; preserve every pre-fix receipt."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPIKES = ROOT / ".planning/spikes"
sys.path.insert(0, str(SPIKES))
from audit_support import Audit

NAMES = ("043-circuit-cuda-mathematics", "044-new-path-upstream",
         "045-policy-admission", "046-public-evidence")


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SPIKES / name / "probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE / "requalification" / name
    module.HERE.mkdir(parents=True, exist_ok=True)
    return module


def historical_hashes():
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for name in NAMES for path in (SPIKES / name).iterdir() if path.is_file()}


before = historical_hashes()
math, upstream, policy, evidence = map(load, NAMES)
audit = Audit(HERE)
for name, function in (
    ("independent_circuit_factors", math.circuit_factors),
    ("native_ldpc_alignment", upstream.aligned_native),
    ("Stim_Sinter_affine_packing", upstream.affine_and_packed),
    ("admitted_policy_matrix", policy.policy_matrix),
    ("memory_identity_and_isolation", policy.identity_and_isolation),
    ("E03_result_conversion_rejected", evidence.execution_dtype_binding),
    ("E01_finite_failure_parity", math.finite_failure),
    ("E02_inactive_controls_rejected", policy.ineffective_controls),
    ("normal_result_export_replay", evidence.ordinary_binding),
):
    audit.probe(name, function)


def exact_controls():
    checked = []
    for name, filename in ((NAMES[0], "factor-cases.json"), (NAMES[1], "native-cases.json"), (NAMES[2], "matrix.json")):
        old, new = SPIKES / name / filename, HERE / "requalification" / name / filename
        assert json.loads(old.read_text()) == json.loads(new.read_text()), filename
        checked.append(dict(path=str(old.relative_to(ROOT)), sha256=sha256(old.read_bytes()).hexdigest()))
    overflow = json.loads((math.HERE / "overflow-counterexample.json").read_text())
    assert all(row["exception"] == "NumericalFailure" and row["message"] == "nonfinite arithmetic at normalized_min_sum_output"
               for row in overflow.values())
    return dict(unchanged_ordinary_case_receipts=checked, overflow_exception_type_and_boundary_match=True)


def carry_unchanged_code_capacity():
    old = json.loads((SPIKES / NAMES[3] / "results.json").read_text())
    changed = []
    for path, digest in old["source_hashes"].items():
        if sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            changed.append(path)
    assert set(changed) == {"src/bp_registry/circuit/policies.py", "src/bp_registry/circuit/policy_compiled.py"}
    carried = json.loads((SPIKES / NAMES[3] / "carried-qualification.json").read_text())
    for receipt in carried:
        assert sha256((ROOT / receipt["path"]).read_bytes()).hexdigest() == receipt["sha256"]
    return dict(changed_modules=changed, other_production_modules_unchanged=len(old["source_hashes"])-len(changed),
                prior_H200_and_code_capacity_evidence="retained; no new hardware execution",
                gpu_shots=sum(row.get("shots", 0) for row in carried))


audit.probe("exact_ordinary_audit_receipts", exact_controls)
audit.probe("unchanged_code_capacity_and_GPU_evidence", carry_unchanged_code_capacity)
audit.record("historical_receipts_untouched", before == historical_hashes(), hashes=before)
summary = audit.finish()
raise SystemExit(1 if summary["failed"] else 0)
