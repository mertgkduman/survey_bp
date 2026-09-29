"""Pure, pre-publication contract for Phase 4 shared-memory evaluation.

The active V4 cap is intentionally a three-arm record.  This module does not
rewrite it, reserve its remaining allocation, write a result, or launch a
decoder.  It projects a separately identified, finite supplemental view from
the already-frozen cap and a deterministic calibration selection.  A later,
explicit publication step must decide whether to fund the supplemental
allocation before any fresh sample can be run.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import run_phase4_pilots as pilot
import verify_phase4_calibration as calibration_audit


SCHEMA_VERSION = 1
CONTRACT_KIND = "phase4-shared-memory-evaluation-supplement"
PUBLICATION_STATUS = "prepared_not_published_no_sampling"
LEGACY_ARMS = ("baseline", "selected_source_procedure", "selected_canonical_procedure")
SHARED_ARMS = ("shared_source_procedure", "shared_canonical_procedure")
TERMINAL_CALIBRATION = frozenset({"completed", "completed_with_inconclusive", "cap_reached"})


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest(value: object) -> str:
    return pilot._digest(value)


def _byte_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _verified_inputs(*, root: Path, caps_path: Path, calibration_path: Path,
                     selection_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Verify the exact immutable inputs used to derive a shared view."""
    root, caps_path, calibration_path, selection_path = (
        path.resolve() for path in (root, caps_path, calibration_path, selection_path)
    )
    caps = _read(caps_path)
    if caps.get("schema_version") != 4 or caps.get("status") != "frozen_pre_calibration":
        raise ValueError("shared evaluation requires the frozen active V4 cap")
    if caps.get("caps_digest") != _digest({key: value for key, value in caps.items() if key != "caps_digest"}):
        raise ValueError("shared evaluation cap digest does not verify")
    if tuple(caps.get("evaluation", {}).get("arms_per_code", ())) != LEGACY_ARMS:
        raise ValueError("shared supplement may only extend the unchanged legacy three-arm cap")
    plan = pilot.calibration_plan(root, caps)
    calibration = _read(calibration_path)
    if calibration.get("status") not in TERMINAL_CALIBRATION:
        raise ValueError("shared evaluation is gated on terminal calibration evidence")
    if calibration.get("caps_sha256") != _byte_sha(caps_path) or calibration.get("calibration_digest") != plan["calibration_digest"]:
        raise ValueError("shared evaluation calibration is not bound to this cap and plan")
    if calibration.get("calibration_input") != plan["calibration_input"]:
        raise ValueError("shared evaluation calibration input drifted")
    if calibration.get("evaluation_namespace_accessed") is not False:
        raise ValueError("calibration accessed fresh evaluation samples")
    if calibration.get("result_digest") != _digest({key: value for key, value in calibration.items() if key != "result_digest"}):
        raise ValueError("shared evaluation calibration result digest does not verify")
    calibration_audit.audit_terminal(root=root, caps_path=caps_path, calibration_path=calibration_path)
    selection = _read(selection_path)
    expected_selection = pilot.select_calibration_settings(calibration)
    if selection != expected_selection:
        raise ValueError("shared evaluation selection differs from deterministic calibration selection")
    return caps, calibration, selection


def _shared_candidate(*, caps: Mapping[str, Any], selection: Mapping[str, Any],
                      code_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """Return one jointly eligible candidate, never a fallback preset setting."""
    shared = selection.get("codes", {}).get(code_id, {}).get("shared_memory_settings", {})
    if not isinstance(shared, Mapping) or shared.get("status") != "selected_finite_precision_limited":
        return None, "no jointly eligible source/canonical calibration candidate"
    candidate = shared.get("candidate")
    candidate_id = shared.get("candidate_id")
    source_id = shared.get("source_configuration_id")
    canonical_id = shared.get("canonical_configuration_id")
    code = caps.get("codes", {}).get(code_id)
    if not isinstance(code, Mapping) or not isinstance(candidate, Mapping) or not isinstance(candidate_id, str):
        raise ValueError(f"shared selection is malformed for {code_id}")
    frozen = list(code.get("coarse_candidates", ())) + list(code.get("refinement_candidates", ()))
    if not any(candidate == item and candidate.get("id") == candidate_id for item in frozen):
        raise ValueError(f"shared selection candidate is outside the frozen surface: {code_id}")
    if source_id not in {f"{code_id}:source_procedure:coarse:{candidate_id}", f"{code_id}:source_procedure:refinement:{candidate_id}"}:
        raise ValueError(f"shared source configuration identity drifted: {code_id}")
    if canonical_id not in {f"{code_id}:canonical_default:coarse:{candidate_id}", f"{code_id}:canonical_default:refinement:{candidate_id}"}:
        raise ValueError(f"shared canonical configuration identity drifted: {code_id}")
    return dict(candidate), None


def build_presampling_supplement(*, root: Path, caps_path: Path, calibration_path: Path,
                                 selection_path: Path, shared_shots_by_code: Mapping[str, int],
                                 wall_seconds_max: int) -> dict[str, Any]:
    """Build a finite shared-view contract without publishing or sampling it.

    ``wall_seconds_max`` is a new, explicit supplemental ceiling.  It is not
    borrowed from the live V4 evaluation category, whose accounting remains
    byte-for-byte untouched.  The returned contract deliberately states that
    it cannot authorize a production command.
    """
    caps, _, selection = _verified_inputs(
        root=root, caps_path=caps_path, calibration_path=calibration_path, selection_path=selection_path
    )
    if set(shared_shots_by_code) != set(caps["codes"]):
        raise ValueError("shared supplemental counts must cover exactly the qualified codes")
    if not isinstance(wall_seconds_max, int) or wall_seconds_max <= 0:
        raise ValueError("shared supplement needs a positive finite wall ceiling")
    cells: list[dict[str, Any]] = []
    unavailable: dict[str, str] = {}
    planned_wall = 0
    for code_id in sorted(caps["codes"]):
        shots = shared_shots_by_code[code_id]
        if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
            raise ValueError(f"shared supplemental count is not positive for {code_id}")
        code = caps["codes"][code_id]
        namespace = code.get("evaluation_namespace")
        forbidden = {code.get("calibration_namespace"), code.get("native_namespace"), code.get("benchmark_namespace")}
        if not isinstance(namespace, str) or not namespace or namespace in forbidden:
            raise ValueError(f"shared sample namespace is not disjoint for {code_id}")
        candidate, reason = _shared_candidate(caps=caps, selection=selection, code_id=code_id)
        if candidate is None:
            unavailable[code_id] = str(reason)
            continue
        boundary = code.get("canonical_public_boundary_seconds")
        work = code.get("per_shot_work_cap")
        if not isinstance(boundary, int) or boundary <= 0 or not isinstance(work, Mapping) or not work:
            raise ValueError(f"shared supplemental bounds are invalid for {code_id}")
        planned_wall += len(SHARED_ARMS) * shots * boundary
        for arm in SHARED_ARMS:
            cells.append({
                "code_id": code_id, "arm": arm, "status": "ready", "candidate": candidate,
                "sample_namespace": namespace, "shots": shots,
                "error_rate": float(code["central_error_rate"]), "public_boundary_seconds": boundary,
                "work_cap": dict(work), "kernel": "min_sum" if arm == "shared_source_procedure" else "spa",
                "preset": "source_procedure" if arm == "shared_source_procedure" else "canonical_default",
                "memory_tuning_identity": _digest(candidate),
            })
    status = "prepared" if not unavailable else "blocked_inconclusive_shared_selection"
    if planned_wall > wall_seconds_max:
        raise ValueError("shared supplemental category wall ceiling would be overcommitted")
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "contract_kind": CONTRACT_KIND,
        "publication_status": PUBLICATION_STATUS, "status": status,
        "no_production_side_effects": True,
        "source_cap": {"path": str(caps_path.resolve()), "byte_sha256": _byte_sha(caps_path), "caps_digest": caps["caps_digest"],
                       "legacy_arms_per_code": list(LEGACY_ARMS)},
        "selection": {"path": str(selection_path.resolve()), "byte_sha256": _byte_sha(selection_path),
                      "selection_digest": _digest(selection), "shared_selection_rule": selection.get("shared_selection_rule")},
        "sample_contract": {"namespace_policy": "reuse matched legacy evaluation namespace across existing and shared views",
                            "forbidden_namespaces": ["calibration", "native", "benchmark"]},
        "allocation": {"category": "evaluation_shared_supplement", "wall_seconds_max": wall_seconds_max,
                       "planned_max_wall_seconds": planned_wall, "counts_per_arm_by_code": dict(shared_shots_by_code),
                       "work_scope": "each shared arm retains the active-V4 per-shot work cap"},
        "cells": cells, "unavailable_codes": unavailable,
        "source_and_timing_qualification": {
            "status": "not_qualified_for_production",
            "reason": "exact-author native timing/agreement covers the selected source procedure, not this unpublished shared setting",
        },
        "claim_scope": "prepared finite CSS pilot supplement; no sampling, publication qualification, or decoder ranking claim",
    }
    contract["contract_digest"] = _digest(contract)
    return contract


def verify_presampling_supplement(contract: Mapping[str, Any]) -> None:
    """Reject mutable, overcommitted, or production-authorizing contracts."""
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("contract_kind") != CONTRACT_KIND:
        raise ValueError("unknown shared evaluation supplement")
    if contract.get("publication_status") != PUBLICATION_STATUS or contract.get("no_production_side_effects") is not True:
        raise ValueError("shared supplement must remain unpublished and non-production")
    if contract.get("contract_digest") != _digest({key: value for key, value in contract.items() if key != "contract_digest"}):
        raise ValueError("shared supplement digest does not verify")
    allocation = contract.get("allocation")
    cells = contract.get("cells")
    if not isinstance(allocation, Mapping) or not isinstance(cells, list):
        raise ValueError("shared supplement omits allocation or cells")
    counts = allocation.get("counts_per_arm_by_code")
    ceiling = allocation.get("wall_seconds_max")
    planned = allocation.get("planned_max_wall_seconds")
    if (not isinstance(counts, Mapping) or isinstance(ceiling, bool) or not isinstance(ceiling, int) or ceiling <= 0
            or isinstance(planned, bool) or not isinstance(planned, int) or planned < 0):
        raise ValueError("shared supplement allocation is not finite and positive")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in counts.values()):
        raise ValueError("shared supplement counts are not positive finite integers")
    if planned > ceiling:
        raise ValueError("shared supplement overcommits its category")
    if contract.get("status") != "prepared":
        raise ValueError("shared supplement has ineligible or inconclusive selections")
    if any(not isinstance(cell, Mapping) for cell in cells):
        raise ValueError("shared supplement cell is malformed")
    names = [(cell.get("code_id"), cell.get("arm")) for cell in cells]
    expected = {(code_id, arm) for code_id in counts for arm in SHARED_ARMS}
    if set(names) != expected or len(names) != len(expected) or any(cell.get("status") != "ready" for cell in cells):
        raise ValueError("shared supplement has undeclared or unavailable arms")
    recomputed_wall = 0
    by_code: dict[str, list[Mapping[str, Any]]] = {}
    for cell in cells:
        code_id, arm = cell.get("code_id"), cell.get("arm")
        if (arm not in SHARED_ARMS or cell.get("kernel") !=
                ("min_sum" if arm == "shared_source_procedure" else "spa")
                or cell.get("preset") != ("source_procedure" if arm == "shared_source_procedure" else "canonical_default")):
            raise ValueError("shared supplement arm or kernel is undeclared")
        shots, boundary = cell.get("shots"), cell.get("public_boundary_seconds")
        if (isinstance(shots, bool) or not isinstance(shots, int) or shots != counts.get(code_id)
                or isinstance(boundary, bool) or not isinstance(boundary, int) or boundary <= 0):
            raise ValueError("shared supplement cell count or boundary drifted")
        if cell.get("memory_tuning_identity") != _digest(cell.get("candidate")) or not isinstance(cell.get("work_cap"), Mapping):
            raise ValueError("shared source/canonical memory tuning differs")
        recomputed_wall += shots * boundary
        by_code.setdefault(str(code_id), []).append(cell)
    if recomputed_wall != planned:
        raise ValueError("shared supplement planned wall accounting drifted")
    for code_id, pair in by_code.items():
        if len(pair) != 2:
            raise ValueError(f"shared supplement pair count drifted for {code_id}")
        fields = ("sample_namespace", "memory_tuning_identity", "candidate", "work_cap", "error_rate", "public_boundary_seconds", "shots")
        if any(pair[0].get(field) != pair[1].get(field) for field in fields):
            raise ValueError(f"shared source/canonical pair differs for {code_id}")


def shared_cells(contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return validated shared cells for manifest-only preflight callers."""
    verify_presampling_supplement(contract)
    return [dict(cell) for cell in contract["cells"]]


def verify_bound_sources(*, contract: Mapping[str, Any], caps_path: Path,
                         selection_path: Path) -> None:
    """Ensure a prepared contract cannot be replayed against substituted inputs."""
    verify_presampling_supplement(contract)
    cap = contract["source_cap"]
    selection = contract["selection"]
    if _byte_sha(caps_path) != cap.get("byte_sha256"):
        raise ValueError("shared supplement cap byte identity drifted")
    value = _read(caps_path)
    if value.get("caps_digest") != cap.get("caps_digest"):
        raise ValueError("shared supplement cap semantic identity drifted")
    if _byte_sha(selection_path) != selection.get("byte_sha256"):
        raise ValueError("shared supplement selection byte identity drifted")
    if _digest(_read(selection_path)) != selection.get("selection_digest"):
        raise ValueError("shared supplement selection semantic identity drifted")
    selected = _read(selection_path)
    if tuple(value.get("evaluation", {}).get("arms_per_code", ())) != LEGACY_ARMS:
        raise ValueError("shared supplement must bind the unchanged legacy evaluation arms")
    for code_id in value.get("codes", {}):
        candidate, reason = _shared_candidate(caps=value, selection=selected, code_id=code_id)
        if candidate is None:
            raise ValueError(f"shared supplement selection is ineligible: {code_id}: {reason}")
        pair = [cell for cell in contract["cells"] if cell["code_id"] == code_id]
        code = value["codes"][code_id]
        if len(pair) != 2 or any(
                cell["candidate"] != candidate
                or cell["sample_namespace"] != code.get("evaluation_namespace")
                or cell["sample_namespace"] in {code.get("calibration_namespace"), code.get("native_namespace"), code.get("benchmark_namespace")}
                or cell["work_cap"] != code.get("per_shot_work_cap")
                or cell["public_boundary_seconds"] != code.get("canonical_public_boundary_seconds")
                or cell["error_rate"] != float(code.get("central_error_rate"))
                for cell in pair):
            raise ValueError(f"shared supplement cell no longer binds frozen source settings: {code_id}")
