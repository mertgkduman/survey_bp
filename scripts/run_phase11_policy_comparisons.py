#!/usr/bin/env python3
"""Bounded, replayable D-13 policy mechanism comparisons.

This runner deliberately owns a narrow controlled lane.  It permits only a
qualified recurrence difference while materializing a shared physical Pauli
sample before either decoder receives its syndrome and priors.
"""

from __future__ import annotations

import argparse
import base64
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter_ns
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bp_registry.campaigns.contracts import canonical_json_bytes
from bp_registry.campaigns.controlled_execution import _phase11_load_code, _phase11_sample
from bp_registry.campaigns.statistics import load_fixed_marginal_design
from bp_registry.quaternary.execution import TracerPauliProblem, _evaluate
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.mbp4 import FixedAlphaMbp4Kernel, Mbp4Spec
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


STUDY_PATH = Path("data/studies/phase11-policy-comparisons.json")
_SHARED_FIELDS = frozenset({"alpha", "schedule", "initialization", "construction", "stopping", "postprocessing"})


def _digest(value: object) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _write_exact(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(payload) + b"\n"
    if path.exists():
        if path.is_symlink() or path.read_bytes() != encoded:
            raise ValueError("policy comparison output conflicts with sealed bytes")
        return
    path.write_bytes(encoded)


def load_policy_study(root: Path) -> dict[str, Any]:
    path = root / STUDY_PATH
    if path.is_symlink() or not path.is_file():
        raise ValueError("policy comparison study is unavailable")
    try:
        return json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise ValueError("policy comparison study is not JSON") from error


def validate_policy_study(root: Path, study: dict[str, Any]) -> None:
    required = {"schema", "study_id", "evidence_lane", "claim_scope", "fixed_marginal_design", "code", "bounded_limits", "comparisons"}
    if set(study) != required or study["schema"] != "phase11_policy_comparison_study_v1":
        raise ValueError("policy comparison study schema is invalid")
    if study["evidence_lane"] != "controlled_canonical_adaptation" or "not_reproduction" not in study["claim_scope"]:
        raise ValueError("policy comparison study must retain controlled adaptation scope")
    fixed = study["fixed_marginal_design"]
    if set(fixed) != {"path", "sha256"} or sha256((root / fixed["path"]).read_bytes()).hexdigest() != fixed["sha256"]:
        raise ValueError("fixed marginal design identity differs")
    if study["code"] != {"code_id": "GB46", "design_path": "data/studies/phase11-gb46-joint-separate.json", "run_fidelity": "canonical_adaptation"}:
        raise ValueError("policy comparison code identity differs")
    limits = study["bounded_limits"]
    if set(limits) != {"samples_per_anchor", "max_iterations", "max_output_bytes"} or any(type(value) is not int or value < 1 for value in limits.values()):
        raise ValueError("policy comparison limits must be positive bounded integers")
    if not isinstance(study["comparisons"], list) or not study["comparisons"]:
        raise ValueError("policy comparison study requires at least one comparison")
    for comparison in study["comparisons"]:
        _validate_comparison(root, comparison)


def _validate_comparison(root: Path, comparison: dict[str, Any]) -> None:
    if comparison.get("method") == "aSCED":
        _validate_asced_comparison(root, comparison)
        return
    required = {"comparison_id", "method", "qualification_path", "qualification_status", "declared_changed_field", "anchors", "baseline", "variant"}
    if set(comparison) != required or comparison["method"] != "MBP4":
        raise ValueError("policy comparison is not a qualified MBP4 comparison")
    qualification = root / comparison["qualification_path"]
    if not qualification.is_file() or comparison["qualification_status"] != "deterministic_mechanism_assessed":
        raise ValueError("MBP4 qualification is unavailable")
    try:
        status = json.loads(qualification.read_bytes()).get("status")
    except json.JSONDecodeError as error:
        raise ValueError("MBP4 qualification receipt is invalid") from error
    if status != comparison["qualification_status"]:
        raise ValueError("MBP4 qualification status differs")
    if comparison["declared_changed_field"] != "recurrence" or not isinstance(comparison["anchors"], list) or not comparison["anchors"]:
        raise ValueError("policy comparison must declare recurrence and anchors")
    baseline, variant = comparison["baseline"], comparison["variant"]
    if set(baseline) != _SHARED_FIELDS | {"recurrence"} or set(variant) != _SHARED_FIELDS | {"recurrence"}:
        raise ValueError("policy comparison fields are incomplete")
    if baseline["recurrence"] != "scalar_llr_bp4" or variant["recurrence"] != "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18":
        raise ValueError("policy recurrence is unsupported")
    Mbp4Spec(alpha=variant["alpha"], schedule=variant["schedule"], max_iterations=1)
    changed = {key for key in baseline if baseline[key] != variant[key]}
    if changed != {comparison["declared_changed_field"]}:
        raise ValueError("policy comparison must change exactly one declared field")
    _validate_anchor_order(comparison["anchors"])


def _validate_anchor_order(anchors: object) -> None:
    if anchors != ["lower_y", "independence", "higher_y"]:
        raise ValueError("policy comparison anchors must be exactly lower_y, independence, higher_y")


def _validate_asced_comparison(root: Path, comparison: dict[str, Any]) -> None:
    required = {"comparison_id", "method", "comparison_kind", "qualification_path", "construction", "settings", "anchors", "canonical_controlled_eligible", "canonical_fidelity", "native_match_status", "native_qualification_path"}
    if set(comparison) != required or comparison["comparison_kind"] not in {"ordinary", "overcomplete"}:
        raise ValueError("aSCED comparison schema is invalid")
    if not (root / comparison["qualification_path"]).is_file() or comparison["canonical_controlled_eligible"] is not True:
        raise ValueError("aSCED controlled qualification is unavailable")
    if comparison["canonical_fidelity"] != "canonical_adaptation":
        raise ValueError("aSCED controlled fidelity must remain canonical adaptation")
    native_path = root / comparison["native_qualification_path"]
    native = json.loads(native_path.read_bytes()) if native_path.is_file() else {}
    if native.get("terminal") != "declined_unavailable" or comparison["native_match_status"] != "unavailable":
        raise ValueError("aSCED native availability differs from preserve_unavailable")
    _validate_anchor_order(comparison["anchors"])


def _probabilities(root: Path, anchor: str) -> tuple[float, float, float, float]:
    design = load_fixed_marginal_design(root / "data/studies/phase11-fixed-marginal-design.json")
    rows = {row.point_id: row for row in design.rows}
    if anchor not in rows:
        raise ValueError("policy comparison anchor is not frozen")
    return tuple(float(value) for value in rows[anchor].probabilities)


def _decode_pair(root: Path, comparison: dict[str, Any], anchor: str, sample_id: int, max_iterations: int) -> dict[str, Any]:
    design_path = root / "data/studies/phase11-gb46-joint-separate.json"
    design = json.loads(design_path.read_bytes())
    code = _phase11_load_code(root=root, code=design["code"])[0]
    probabilities = _probabilities(root, anchor)
    study_sha256 = sha256((root / STUDY_PATH).read_bytes()).hexdigest()
    sample = _phase11_sample(code=code, design_sha256=study_sha256, point_id=anchor, sample_id=sample_id, probabilities=probabilities)
    hidden_x = np.frombuffer(base64.b64decode(sample.x_bytes_b64), dtype=np.uint8).copy()
    hidden_z = np.frombuffer(base64.b64decode(sample.z_bytes_b64), dtype=np.uint8).copy()
    syndrome = np.asarray(tuple(sample.observations["X"].values()) if False else (), dtype=np.uint8)
    # The sample persists X syndrome before Z syndrome. Reconstruct directly from immutable CSS rows.
    syndrome = np.concatenate(((code.hx.astype(np.int64) @ hidden_z) % 2, (code.hz.astype(np.int64) @ hidden_x) % 2)).astype(np.uint8)
    original = QuaternaryOriginalProblem(
        lineage_id=f"original-policy-{comparison['comparison_id']}-{anchor}-{sample_id}",
        code=compile_css_artifact(code, source_artifact_identity=study_sha256), syndrome=syndrome,
    )
    evaluation_problem = TracerPauliProblem(original.code.checks, original.syndrome)
    priors = np.tile(np.asarray(probabilities, dtype=np.float64), (code.n, 1))
    baseline_started = perf_counter_ns()
    baseline_result = ScalarLlrBp4Kernel().new_session(original, priors).run(max_iterations=max_iterations)
    baseline_runtime = perf_counter_ns() - baseline_started
    variant_started = perf_counter_ns()
    variant_result = FixedAlphaMbp4Kernel(Mbp4Spec(alpha=comparison["variant"]["alpha"], schedule="qbp_flooding", max_iterations=max_iterations)).new_session(original, priors).run()
    variant_runtime = perf_counter_ns() - variant_started
    def arm(name: str, result: Any, runtime: int) -> dict[str, Any]:
        candidate = np.asarray(result.candidate, dtype=np.uint8)
        outcome, logical = _evaluate(
            evaluation_problem,
            np.asarray([2 if x and z else 1 if x else 3 if z else 0 for x, z in zip(hidden_x, hidden_z, strict=True)], dtype=np.uint8), candidate,
        )
        terminal = result.termination if hasattr(result, "termination") else result.terminal
        return {"arm_id": name, "sample_identity": sample.physical_sample_identity, "terminal": terminal,
                "outcome": outcome, "logical_action_agrees": logical, "candidate": candidate.tolist(),
                "work": result.work.as_evidence(structural_event_version=4), "runtime_ns": runtime}
    unsigned = {"schema": "phase11_policy_comparison_record_v1", "comparison_id": comparison["comparison_id"],
                "anchor": anchor, "sample_identity": sample.physical_sample_identity,
                "materialized_sample_sha256": sample.materialized_sample_sha256, "baseline": arm("baseline", baseline_result, baseline_runtime),
                "variant": arm("variant", variant_result, variant_runtime), "fidelity": "canonical_adaptation"}
    return {**unsigned, "record_sha256": _digest(unsigned)}


def run_policy_comparisons(root: Path, output_root: Path) -> dict[str, Any]:
    study = load_policy_study(root)
    validate_policy_study(root, study)
    output_root.mkdir(parents=True, exist_ok=True)
    records = 0
    for comparison in study["comparisons"]:
        if comparison["method"] != "MBP4":
            continue
        for anchor in comparison["anchors"]:
            record = _decode_pair(root, comparison, anchor, 0, study["bounded_limits"]["max_iterations"])
            _write_exact(output_root / "records" / comparison["comparison_id"] / f"{anchor}.json", record)
            records += 1
    verification = verify_policy_comparisons(root, output_root)
    _write_exact(output_root / "verification.json", verification)
    return {"status": "verified", "comparison_count": len(study["comparisons"]), "records": records, **verification}


def verify_policy_comparisons(root: Path, output_root: Path) -> dict[str, Any]:
    study = load_policy_study(root)
    validate_policy_study(root, study)
    replayed = 0
    for comparison in study["comparisons"]:
        if comparison["method"] != "MBP4":
            continue
        for anchor in comparison["anchors"]:
            path = output_root / "records" / comparison["comparison_id"] / f"{anchor}.json"
            if path.is_symlink() or not path.is_file():
                raise ValueError("policy comparison record is missing")
            observed = json.loads(path.read_bytes())
            expected = _decode_pair(root, comparison, anchor, 0, study["bounded_limits"]["max_iterations"])
            # Timing is observational; replay verifies identities, terminals, outcomes and typed work.
            for arm in ("baseline", "variant"):
                observed[arm]["runtime_ns"] = expected[arm]["runtime_ns"]
            observed["record_sha256"] = _digest({key: value for key, value in observed.items() if key != "record_sha256"})
            expected["record_sha256"] = observed["record_sha256"]
            if observed != expected:
                raise ValueError("policy comparison replay differs from sealed record")
            replayed += 1
    return {"schema": "phase11_policy_comparison_verification_v1", "status": "verified", "replayed_records": replayed,
            "publication_authorization": "deny", "claim_scope": study["claim_scope"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "replay", "verify"))
    parser.add_argument("--output-root", type=Path, default=ROOT / "data/results/phase11-policy-comparisons")
    args = parser.parse_args()
    try:
        payload = run_policy_comparisons(ROOT, args.output_root) if args.command == "run" else verify_policy_comparisons(ROOT, args.output_root)
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
