"""Coverage and aggregate integrity at the terminal calibration boundary."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
pilot = importlib.import_module("run_phase4_pilots")
audit = importlib.import_module("verify_phase4_calibration")


def surface():
    cells = []
    for preset in ("source_procedure", "canonical_default"):
        cells.append({"configuration_id": f"code:{preset}:coarse:a", "code_id": "code",
                      "preset_key": preset, "candidate": {"id": "a"}, "relay": {"procedure": preset},
                      "calibration_shots": 2, "per_shot_work_cap": {"bp_calls": 1,
                      "check_to_variable_updates": 10}, "public_boundary_seconds": 30})
    plan = {"cells": cells}
    codes = {"code": {"presets": {}}}
    for cell in cells:
        attempts = [{"shot_id": i, "status": "completed", "termination": "completed",
                     "outcome": "logical_failure" if i else "exact", "sample_identity": f"sample-{i}",
                     "aggregate_event_digest": "a" * 64, "failure": None,
                     "work_vector": {"bp_calls": 1, "check_to_variable_updates": 4},
                     "public_boundary": {"elapsed_seconds": 1.0, "category_charge_seconds": 1.0,
                                         "verify": {"shot_id": i, "termination": "completed"}}}
                    for i in range(2)]
        codes["code"]["presets"][cell["preset_key"]] = {
            "configurations": [pilot._configuration_evidence(cell, attempts)]}
    result = {"status": "completed", "codes": codes,
              "evaluation_namespace_accessed": False,
              "allocation": {"retained_public_boundary_seconds": 4.0, "wall_seconds_max": 120}}
    return plan, result


def row(result):
    return result["codes"]["code"]["presets"]["source_procedure"]["configurations"][0]


def test_complete_surface_reconstructs_counts_and_preserves_input():
    plan, result = surface()
    before = deepcopy(result)
    report = audit.audit_surface(plan, result)
    assert report["planned_attempts"] == report["retained_attempts"] == 4
    assert report["eligible_configurations"] == 2
    assert report["scope"] == "surface_integrity_only"
    assert result == before


@pytest.mark.parametrize("change,match", [
    (lambda r: r["codes"]["code"]["presets"]["canonical_default"]["configurations"].clear(), "configuration coverage"),
    (lambda r: row(r)["attempts"].pop(), "shot coverage"),
    (lambda r: row(r)["attempts"].append(deepcopy(row(r)["attempts"][0])), "duplicate shot"),
    (lambda r: row(r)["logical_failure"].update(failures=0), "aggregate"),
    (lambda r: row(r)["work"].update(mean_c2v=0), "aggregate"),
    (lambda r: row(r)["attempts"][0]["work_vector"].update(check_to_variable_updates=11), "work cap"),
    (lambda r: row(r)["attempts"][0]["public_boundary"]["verify"].update(shot_id=1), "verification receipt"),
    (lambda r: row(r)["attempts"][0].update(sample_identity=None), "sample identity"),
    (lambda r: row(r)["attempts"][0].update(aggregate_event_digest=None), "event digest"),
    (lambda r: r["allocation"].update(retained_public_boundary_seconds=0), "wall charge"),
    (lambda r: r.update(evaluation_namespace_accessed=True), "evaluation"),
    (lambda r: r.update(status="running"), "terminal"),
])
def test_omissions_and_rehashed_claim_drift_reject(change, match):
    plan, result = surface()
    change(result)
    # A consistent self-hash cannot repair missing or contradictory evidence.
    result["result_digest"] = pilot._digest(result)
    with pytest.raises(ValueError, match=match):
        audit.audit_surface(plan, result)


def test_cap_placeholders_stay_in_denominator_and_ineligible():
    plan, result = surface()
    cell = plan["cells"][0]
    attempts = row(result)["attempts"]
    attempts[1] = {"shot_id": 1, "status": "cap_reached", "termination": None,
                   "failure": "cap", "public_boundary": {"elapsed_seconds": 0.0}}
    result["codes"]["code"]["presets"]["source_procedure"]["configurations"][0] = pilot._configuration_evidence(cell, attempts)
    result["allocation"]["retained_public_boundary_seconds"] = 3.0
    result["status"] = "cap_reached"
    report = audit.audit_surface(plan, result)
    assert report["retained_attempts"] == 4
    assert report["eligible_configurations"] == 1
    assert report["attempt_status_counts"]["cap_reached"] == 1


def test_matched_sample_transplant_rejects():
    plan, result = surface()
    row(result)["attempts"][0]["sample_identity"] = "other-sample"
    with pytest.raises(ValueError, match="matched sample"):
        audit.audit_surface(plan, result)
