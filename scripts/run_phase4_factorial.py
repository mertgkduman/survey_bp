#!/usr/bin/env python3
"""Prepare and gate the finite Phase 4 ordinary-memory/Relay factorial.

This module deliberately has no decoder command path.  It expands only the
frozen design, caps, and outcome-independent execution supplement.  A caller
may inject an executor after ``assert_factorial_predecessor`` accepts retained
fresh evaluation evidence.  That separation prevents a preparatory command
from spending a production sample or treating a fixture as assessment.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Mapping


OUTCOME_CELLS = (
    "proposed_selected",
    "proposed_unselected",
    "no_proposal",
    "terminal_failure",
    "terminal_incomplete",
)
ASSESSMENT = {"status": "not_assessed", "scope": "CSS_pilot_adaptation"}


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _supplement_payload(supplement: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in supplement.items() if key != "supplement_digest"}


def _validate_supplement(*, design: Mapping[str, Any], caps: Mapping[str, Any], supplement: Mapping[str, Any]) -> None:
    if supplement.get("status") != "frozen_pre_sampling":
        raise ValueError("factorial supplement must be frozen_pre_sampling")
    if supplement.get("calibration_outcomes_inspected") is not False:
        raise ValueError("factorial supplement must remain outcome-independent")
    expected = supplement.get("supplement_digest")
    if not isinstance(expected, str) or expected != _digest(_supplement_payload(supplement)):
        raise ValueError("factorial supplement digest does not bind its declared content")
    design_digest = _digest(design)
    caps_digest = _digest(caps)
    binding = supplement.get("input_digests")
    if not isinstance(binding, Mapping) or binding.get("design_canonical_sha256") != design_digest or binding.get("caps_canonical_sha256") != caps_digest:
        raise ValueError("factorial supplement is not bound to the frozen design and caps")
    if caps.get("status") != "frozen_pre_calibration":
        raise ValueError("factorial caps are not the frozen active-V4 contract")


def _arm_order(arm: Mapping[str, Any], supplement: Mapping[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]], bool]:
    arm_id = str(arm["id"])
    original = [str(item) for item in arm.get("memory_bindings", [])]
    entries = supplement.get("ordinary_memory_arms", {})
    if arm_id not in entries:
        return original, original, [], True
    entry = entries[arm_id]
    if not isinstance(entry, Mapping):
        raise ValueError(f"ordinary arm {arm_id} has invalid supplement entry")
    if entry.get("frozen_binding_array") != original:
        raise ValueError(f"ordinary arm {arm_id} does not preserve its frozen binding array")
    effective = entry.get("effective_execution_order")
    coefficients = entry.get("coefficients")
    if not isinstance(effective, list) or not isinstance(coefficients, list):
        raise ValueError(f"ordinary arm {arm_id} has incomplete execution metadata")
    if sorted(effective) != sorted(original):
        raise ValueError(f"ordinary arm {arm_id} changes its binding membership")
    return original, [str(item) for item in effective], [dict(item) for item in coefficients], entry.get("execution_ready") is True


def build_factorial_plan(*, design: Mapping[str, Any], caps: Mapping[str, Any], supplement: Mapping[str, Any]) -> dict[str, Any]:
    """Build the 14 × 3 × 3 × 7 identified cells without invoking a decoder."""
    _validate_supplement(design=design, caps=caps, supplement=supplement)
    arms = design.get("factorial_arms")
    grid = design.get("noise_grid")
    codes = design.get("codes")
    factorial = caps.get("factorial")
    if not isinstance(arms, list) or not isinstance(grid, list) or not isinstance(codes, Mapping) or not isinstance(factorial, Mapping):
        raise ValueError("frozen design/caps omit factorial inputs")
    counts = factorial.get("shots_per_arm_rate_code_by_code")
    cap_arms = factorial.get("arms")
    if not isinstance(counts, Mapping) or list(cap_arms or []) != [str(arm["id"]) for arm in arms]:
        raise ValueError("frozen caps do not match the frozen factorial arm list")
    cells: list[dict[str, Any]] = []
    for code_id, code in sorted(codes.items()):
        if code_id not in counts or int(counts[code_id]) <= 0:
            raise ValueError(f"factorial cap omits a finite positive shot count for {code_id}")
        namespace = str(code["sample_namespace"])
        for region in grid:
            region_id = str(region["region"])
            rate = float(region["error_rates"][code_id])
            for shot_id in range(int(counts[code_id])):
                physical_identity = _digest({"namespace": namespace, "region": region_id, "rate": rate, "shot_id": shot_id})
                for arm in arms:
                    original, execution_order, coefficients, execution_ready = _arm_order(arm, supplement)
                    arm_id = str(arm["id"])
                    cell_id = _digest({"code_id": code_id, "region": region_id, "rate": rate, "shot_id": shot_id, "arm_id": arm_id, "supplement": supplement["supplement_digest"]})[:24]
                    cells.append({
                        "cell_id": cell_id, "code_id": code_id, "noise_region": region_id, "error_rate": rate,
                        "shot_id": shot_id, "arm_id": arm_id, "arm_kind": arm["kind"],
                        "physical_sample_identity": physical_identity, "physical_sample_namespace": namespace,
                        "original_binding_array": original, "execution_order": execution_order, "coefficients": coefficients,
                        "execution_ready": execution_ready,
                        "relay_control": arm.get("control"), "work_cap": dict(caps["codes"][code_id]["per_shot_work_cap"]),
                        "runtime_boundary_seconds": int(factorial["runtime_boundary_seconds"]),
                        "fidelity": {"status": "controlled_css_pilot_adaptation", "assessment": ASSESSMENT["status"]},
                    })
    plan = {
        "schema_version": 1, "status": "prepared_no_sampling", "assessment": dict(ASSESSMENT),
        "input_digests": {"design_canonical_sha256": _digest(design), "caps_canonical_sha256": _digest(caps), "supplement_digest": supplement["supplement_digest"]},
        "cells": cells, "cell_count": len(cells), "outcome_cells": list(OUTCOME_CELLS),
        "blocked_execution_arms": sorted({str(cell["arm_id"]) for cell in cells if not cell["execution_ready"]}),
        "execution_order_note": supplement["execution_order_resolution"],
        "trace_contract": supplement["trace_contract"],
        "no_sampling": "This plan construction does not invoke canonical/native decoder execution.",
    }
    plan["factorial_digest"] = _digest({key: value for key, value in plan.items() if key != "factorial_digest"})
    return plan


def development_fixture_evaluation(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Create an explicitly non-assessment predecessor fixture for focused tests only."""
    codes = sorted({str(cell["code_id"]) for cell in plan["cells"]})
    arms = sorted({str(cell["arm_id"]) for cell in plan["cells"]})
    return {"schema_version": 1, "status": "completed", "development_fixture": True, "assessment": "not_assessed",
            "factorial_input_digests": dict(plan["input_digests"]), "admitted_arms": arms,
            "codes": {code: {"status": "completed"} for code in codes}}


def assert_factorial_predecessor(*, evaluation_path: Path, plan: Mapping[str, Any], allow_development_fixture: bool = False) -> dict[str, Any]:
    """Require complete fresh evaluation evidence before any production cell executes."""
    evaluation = _read_object(evaluation_path)
    if evaluation.get("status") != "completed":
        raise ValueError("fresh evaluation is absent, incomplete, or inconclusive")
    fixture = evaluation.get("development_fixture") is True
    if fixture and (not allow_development_fixture or evaluation.get("assessment") != "not_assessed"):
        raise ValueError("development fixture cannot authorize production factorial sampling")
    if not fixture and evaluation.get("assessment") == "not_assessed":
        raise ValueError("fresh evaluation marked not_assessed cannot authorize production factorial sampling")
    if evaluation.get("factorial_input_digests") != plan.get("input_digests"):
        raise ValueError("fresh evaluation does not bind this factorial design/cap/supplement")
    planned_arms = {str(cell["arm_id"]) for cell in plan["cells"]}
    if set(evaluation.get("admitted_arms", [])) != planned_arms:
        raise ValueError("fresh evaluation does not admit every focused factorial arm")
    expected_codes = {str(cell["code_id"]) for cell in plan["cells"]}
    code_rows = evaluation.get("codes")
    if not isinstance(code_rows, Mapping) or any(not isinstance(code_rows.get(code), Mapping) or code_rows[code].get("status") != "completed" for code in expected_codes):
        raise ValueError("fresh evaluation is not complete for every factorial code")
    return {"path": str(evaluation_path), "sha256": _file_sha256(evaluation_path), "development_fixture": fixture,
            "assessment": evaluation.get("assessment", "assessed"), "admitted_arms": sorted(planned_arms)}


def aggregate_terminals(terminals: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Derive counts and tails only from retained terminal records, retaining missingness."""
    outcome_cells = {name: 0 for name in OUTCOME_CELLS}
    runtimes: list[float] = []
    rss: list[float] = []
    missing_rss = 0
    origins: dict[str, int] = {}
    for terminal in terminals:
        if terminal.get("terminal") is not True or terminal.get("outcome_cell") not in outcome_cells:
            raise ValueError("factorial aggregate requires a retained classified terminal")
        outcome_cells[str(terminal["outcome_cell"])] += 1
        origin = terminal.get("candidate_origin")
        if isinstance(origin, str):
            origins[origin] = origins.get(origin, 0) + 1
        runtime = terminal.get("runtime_seconds")
        if isinstance(runtime, (int, float)) and not isinstance(runtime, bool):
            runtimes.append(float(runtime))
        resource = terminal.get("resource")
        value = resource.get("maxrss_kib") if isinstance(resource, Mapping) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            rss.append(float(value))
        else:
            missing_rss += 1
    def tails(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"p50": None, "p95": None, "max": None}
        ordered = sorted(values)
        index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * .95 + .999999)))
        return {"p50": ordered[len(ordered) // 2], "p95": ordered[index], "max": ordered[-1]}
    return {"terminal_count": len(terminals), "outcome_cells": outcome_cells, "candidate_origins": origins,
            "runtime_seconds": tails(runtimes), "resource": {"maxrss_kib": {**tails(rss), "missing": missing_rss}},
            "raw_work": "retained per terminal; no heterogeneous scalar cost is formed"}


def trace_link_event(*, ledger_id: str, schedule: Any) -> dict[str, Any]:
    """Finalize the coordinated observer API and return a ledger-link event payload.

    ``MemoryFloodingSchedule`` owns observations; this runner only binds the
    completed sidecar to the retained factorial ledger identity.
    """
    result = schedule.trace_result()
    link = result.ledger_link()
    if link is None:
        raise ValueError("bounded trace collection produced no link")
    return {"kind": "trace_link", "ledger_id": ledger_id,
            "data": {"trace_kind": "ordinary_memory", "sidecar": link}}


def run_factorial(*, evaluation_path: Path, plan: Mapping[str, Any], executor: Callable[[Mapping[str, Any]], Mapping[str, Any]], allow_development_fixture: bool = False) -> dict[str, Any]:
    """Execute an injected bounded executor only after the evaluation gate passes."""
    gate = assert_factorial_predecessor(evaluation_path=evaluation_path, plan=plan, allow_development_fixture=allow_development_fixture)
    if not gate["development_fixture"] and plan.get("blocked_execution_arms"):
        raise ValueError("factorial has arms without an executable ordinary-memory assignment implementation")
    terminals: list[dict[str, Any]] = []
    for cell in plan["cells"]:
        terminal = dict(executor(cell))
        terminal["cell_id"] = cell["cell_id"]
        terminal["physical_sample_identity"] = cell["physical_sample_identity"]
        terminals.append(terminal)
    aggregate = aggregate_terminals(terminals)
    fixture = gate["development_fixture"]
    return {"schema_version": 1, "status": "development_fixture_not_assessed" if fixture else "completed_not_assessed",
            "assessment": "not_assessed", "predecessor": gate, "factorial_digest": plan["factorial_digest"],
            "terminals": terminals, "aggregate": aggregate,
            "interpretation_limit": "CSS pilot adaptation; no circuit reproduction or universal ranking claim."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=Path("data/evidence/phase4-pilot-design.json"))
    parser.add_argument("--caps", type=Path, default=Path("data/manifests/phase4-pilot-caps.json"))
    parser.add_argument("--supplement", type=Path, default=Path("data/evidence/phase4-factorial-execution-supplement-v1.json"))
    args = parser.parse_args()
    plan = build_factorial_plan(design=_read_object(args.design), caps=_read_object(args.caps), supplement=_read_object(args.supplement))
    print(json.dumps({key: value for key, value in plan.items() if key != "cells"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
