#!/usr/bin/env python3
"""Read-only terminal calibration coverage audit; ledger replay is a separate gate.

No settings are selected or written. A surface-integrity verdict proves plan
coverage and internal aggregate consistency, not canonical ledger semantics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping

import run_phase4_pilots as pilot
from bp_registry.phase4_analysis import wilson_interval

TERMINAL = {"completed", "completed_with_inconclusive", "cap_reached"}
ATTEMPT_STATUSES = {"completed", "budget_exhausted", "incomplete_public_boundary", "cap_reached"}


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid nonnegative finite {name}")
    return float(value)


def _close(actual: object, expected: float, name: str) -> None:
    if not math.isclose(_number(actual, name), expected, rel_tol=1e-12, abs_tol=1e-8):
        raise ValueError(f"{name} does not reconstruct from retained attempts")


def _summary(cell: Mapping[str, Any], attempts: list[Mapping[str, Any]]) -> dict[str, Any]:
    complete = [a for a in attempts if a["status"] == "completed"]
    logical = [a for a in complete if a.get("outcome") in {"exact", "stabilizer_equivalent", "logical_failure"}]
    failures = sum(a["outcome"] == "logical_failure" for a in logical)
    work = [a["work_vector"] for a in complete]
    eligible = len(complete) == cell["calibration_shots"] and len(logical) == len(complete)
    return {
        "status": "completed" if eligible else "inconclusive",
        "logical_failure": {"failures": failures, "denominator": len(logical),
            "estimate": failures / len(logical) if logical else None,
            "wilson_95": wilson_interval(failures, len(logical)), "eligible": eligible,
            "precision_status": "finite_precision_limited_wilson_95_percent" if eligible else "insufficient_precision_or_nonterminal"},
        "work": {"mean_c2v": sum(w.get("check_to_variable_updates", 0) for w in work) / len(work) if work else None,
                 "mean_total": sum(sum(w.values()) for w in work) / len(work) if work else None},
        "termination_counts": dict(Counter(a["termination"] for a in attempts if a.get("termination") is not None)),
    }


def audit_surface(plan: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Reject missing planned rows, duplicated shots, and self-hashed claim drift."""
    if result.get("status") not in TERMINAL:
        raise ValueError("surface audit requires terminal calibration")
    if result.get("evaluation_namespace_accessed") is not False:
        raise ValueError("calibration accessed evaluation samples")
    expected = {c["configuration_id"]: c for c in plan["cells"]}
    if len(expected) != len(plan["cells"]) or not expected:
        raise ValueError("invalid frozen configuration plan")
    expected_presets = {(c["code_id"], c["preset_key"]) for c in expected.values()}
    found_presets = set()
    found = {}
    for code_id, code in result.get("codes", {}).items():
        for preset_key, preset in code.get("presets", {}).items():
            found_presets.add((code_id, preset_key))
            for configuration in preset.get("configurations", []):
                cid = configuration.get("configuration_id")
                if cid in found:
                    raise ValueError("duplicate configuration coverage")
                cell = expected.get(cid)
                if cell is None or (code_id, preset_key) != (cell["code_id"], cell["preset_key"]):
                    raise ValueError("configuration coverage outside frozen code/preset")
                found[cid] = configuration
    if set(found) != set(expected) or found_presets != expected_presets or set(result.get("codes", {})) != {c["code_id"] for c in expected.values()}:
        raise ValueError("configuration coverage differs from frozen plan")
    statuses: Counter[str] = Counter()
    samples: dict[tuple[str, int], str] = {}
    total_charge = 0.0
    eligible_count = 0
    for cid, cell in expected.items():
        config = found[cid]
        if config.get("candidate") != cell["candidate"] or config.get("relay") != cell["relay"]:
            raise ValueError("configuration controls differ from frozen plan")
        attempts = config.get("attempts")
        if not isinstance(attempts, list):
            raise ValueError("shot coverage is absent")
        ids = [a.get("shot_id") for a in attempts]
        if any(isinstance(i, bool) or not isinstance(i, int) for i in ids):
            raise ValueError("invalid shot coverage identifiers")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate shot coverage")
        if set(ids) != set(range(cell["calibration_shots"])):
            raise ValueError("shot coverage differs from frozen plan")
        for a in attempts:
            status = a.get("status")
            if status not in ATTEMPT_STATUSES:
                raise ValueError("unknown retained attempt status")
            statuses[status] += 1
            boundary = a.get("public_boundary", {})
            charge = boundary.get("category_charge_seconds")
            if charge is None:
                charge = boundary.get("elapsed_seconds")
            charge = _number(charge, "wall charge")
            total_charge += charge
            if status in {"completed", "budget_exhausted"}:
                termination = "completed" if status == "completed" else "budget_exhausted"
                if a.get("termination") != termination:
                    raise ValueError("attempt status contradicts termination")
                receipt = boundary.get("verify")
                if not isinstance(receipt, Mapping) or receipt.get("shot_id") != a["shot_id"] or receipt.get("termination") != termination:
                    raise ValueError("terminal verification receipt missing or contradictory")
                sample = a.get("sample_identity")
                if not isinstance(sample, str) or not sample:
                    raise ValueError("terminal sample identity missing")
                key = (cell["code_id"], a["shot_id"])
                if key in samples and samples[key] != sample:
                    raise ValueError("matched sample identity differs across calibration configurations")
                samples[key] = sample
                digest = a.get("aggregate_event_digest")
                if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                    raise ValueError("terminal aggregate event digest missing")
                work = a.get("work_vector")
                if not isinstance(work, Mapping) or not work:
                    raise ValueError("terminal work cap evidence missing")
                for name, count in work.items():
                    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                        raise ValueError("invalid integer work cap evidence")
                    if name not in cell["per_shot_work_cap"] or count > cell["per_shot_work_cap"][name]:
                        raise ValueError("retained attempt exceeds frozen work cap")
                if set(work) != set(cell["per_shot_work_cap"]):
                    raise ValueError("terminal work cap components missing")
            elif status == "cap_reached" and (charge != 0 or a.get("termination") is not None):
                raise ValueError("unstarted cap placeholder claims terminal work")
        summary = _summary(cell, attempts)
        for field, value in summary.items():
            if config.get(field) != value:
                raise ValueError(f"configuration aggregate {field} does not reconstruct")
        eligible_count += int(summary["logical_failure"]["eligible"])
    allocation = result.get("allocation", {})
    _close(allocation.get("retained_public_boundary_seconds"), total_charge, "wall charge")
    if total_charge > _number(allocation.get("wall_seconds_max"), "wall cap") + 1e-8:
        raise ValueError("calibration wall charge exceeds frozen category")
    expected_status = ("cap_reached" if statuses["cap_reached"] else "completed"
                       if eligible_count == len(expected) else "completed_with_inconclusive")
    if result["status"] != expected_status:
        raise ValueError("terminal aggregate status does not reconstruct")
    return {"status": "passed", "scope": "surface_integrity_only",
            "planned_configurations": len(expected), "eligible_configurations": eligible_count,
            "planned_attempts": sum(c["calibration_shots"] for c in expected.values()),
            "retained_attempts": sum(statuses.values()), "attempt_status_counts": dict(statuses),
            "ledger_semantics": "requires_separate_public_verification",
            "assessment_status": "not_assessed"}


def audit_terminal(*, root: Path, caps_path: Path, calibration_path: Path) -> dict[str, Any]:
    """Load exact bytes and bind the complete surface to its frozen cap/plan."""
    caps_bytes, result_bytes = caps_path.read_bytes(), calibration_path.read_bytes()
    caps, result = json.loads(caps_bytes), json.loads(result_bytes)
    if result.get("status") not in TERMINAL:
        raise ValueError("surface audit requires terminal calibration")
    if caps.get("schema_version") != 4 or caps.get("caps_digest") != pilot._digest({k: v for k, v in caps.items() if k != "caps_digest"}):
        raise ValueError("frozen cap digest does not verify")
    plan = pilot.calibration_plan(root, caps)
    if result.get("caps_sha256") != sha256(caps_bytes).hexdigest() or result.get("calibration_input") != plan["calibration_input"] or result.get("calibration_digest") != plan["calibration_digest"]:
        raise ValueError("calibration provenance differs from frozen plan")
    if result.get("amendment_sha256") != caps["design_amendment"]["sha256"]:
        raise ValueError("calibration amendment identity drifted")
    if result.get("result_digest") != pilot._digest({k: v for k, v in result.items() if k != "result_digest"}):
        raise ValueError("terminal result digest does not verify")
    if result.get("allocation", {}).get("wall_seconds_max") != caps["allocation"]["categories"]["calibration"]["wall_seconds_max"]:
        raise ValueError("calibration category wall cap drifted")
    report = audit_surface(plan, result)
    return {**report, "calibration_digest": plan["calibration_digest"], "result_byte_sha256": sha256(result_bytes).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--caps", type=Path, default=Path("data/manifests/phase4-pilot-caps.json"))
    parser.add_argument("--calibration", type=Path, default=Path("data/results/phase4-memory-relay/calibration/result.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    print(json.dumps(audit_terminal(root=root, caps_path=root / args.caps, calibration_path=root / args.calibration), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
