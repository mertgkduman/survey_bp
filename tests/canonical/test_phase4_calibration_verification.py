"""Coverage and aggregate integrity at the terminal calibration boundary."""
from copy import deepcopy
from hashlib import sha256
import importlib
import json
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
                      "calibration_namespace": "fixture-calibration",
                      "calibration_shots": 2, "per_shot_work_cap": {"bp_calls": 1,
                      "check_to_variable_updates": 10}, "public_boundary_seconds": 30})
    plan = {"cells": cells}
    codes = {"code": {"presets": {}}}
    for cell in cells:
        attempts = [{"shot_id": i, "status": "completed", "termination": "completed",
                     "outcome": "logical_failure" if i else "exact", "sample_identity": sha256(
                         f"bp-registry-sample-v1\0fixture-calibration\0{i}".encode()).hexdigest(),
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


@pytest.mark.parametrize("namespace", ["fixture-evaluation", "fixture-calibration"])
def test_reused_or_evaluation_namespace_sample_cannot_enter_calibration(namespace):
    plan, result = surface()
    for preset in result["codes"]["code"]["presets"].values():
        for a in preset["configurations"][0]["attempts"]:
            a["sample_identity"] = sha256(f"bp-registry-sample-v1\0{namespace}\0{0}".encode()).hexdigest()
    with pytest.raises(ValueError, match="frozen namespace and shot"):
        audit.audit_surface(plan, result)


def test_surface_sample_identity_agrees_with_public_sampler(small_css_checks):
    from bp_registry.css import CssCode
    from bp_registry.sampling import sample_shot
    hx, hz = small_css_checks
    plan, result = surface()
    for preset in result["codes"]["code"]["presets"].values():
        for a in preset["configurations"][0]["attempts"]:
            sample = sample_shot(CssCode(hx=hx, hz=hz), shot_id=a["shot_id"], seed=1,
                                 x_error_rate=0.1, manifest_identity="fixture-calibration")
            assert sample.sample_identity == a["sample_identity"]
    assert audit.audit_surface(plan, result)["status"] == "passed"


def test_exact_byte_provenance_and_terminal_gate(tmp_path, monkeypatch):
    plan, result = surface()
    plan.update(calibration_input={"cells": plan["cells"]}, calibration_digest="c" * 64)
    caps = {"schema_version": 4, "design_amendment": {"sha256": "d" * 64},
            "allocation": {"categories": {"calibration": {"wall_seconds_max": 120}}}}
    caps["caps_digest"] = pilot._digest(caps)
    caps_path = tmp_path / "caps.json"
    caps_path.write_text(json.dumps(caps))
    result.update(caps_sha256=sha256(caps_path.read_bytes()).hexdigest(),
                  calibration_input=plan["calibration_input"], calibration_digest=plan["calibration_digest"],
                  amendment_sha256="d" * 64)
    result["result_digest"] = pilot._digest(result)
    path = tmp_path / "result.json"
    path.write_text(json.dumps(result))
    monkeypatch.setattr(pilot, "calibration_plan", lambda root, cap: plan)
    assert audit.audit_terminal(root=tmp_path, caps_path=caps_path, calibration_path=path)["status"] == "passed"
    caps_path.write_text(json.dumps(caps, indent=2))
    with pytest.raises(ValueError, match="provenance"):
        audit.audit_terminal(root=tmp_path, caps_path=caps_path, calibration_path=path)
    result["status"] = "running"
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="terminal"):
        audit.audit_terminal(root=tmp_path, caps_path=caps_path, calibration_path=path)


def test_recovery_replaces_old_charge_instead_of_double_counting(tmp_path, monkeypatch):
    plan, result = surface()
    cell = plan["cells"][0]
    plan = {"cells": [cell], "calibration_digest": "c" * 64, "calibration_input": {"selection_rule": "fixture"}}
    result["codes"]["code"]["presets"].pop("canonical_default")
    row(result)["attempts"][0].update(status="incomplete_public_boundary", termination=None,
                                        public_boundary={"elapsed_seconds": 3.0})
    result.update(status="running", calibration_digest=plan["calibration_digest"])
    caps = {"design_amendment": {"sha256": "d" * 64, "path": "fixture.json"},
            "allocation": {"categories": {"calibration": {"wall_seconds_max": 120}}}}
    caps_path = tmp_path / "caps.json"
    caps_path.write_text(json.dumps(caps))
    output = tmp_path / "calibration"
    output.mkdir()
    (output / "result.json").write_text(json.dumps(result))
    (tmp_path / "base.json").write_text("{}")
    monkeypatch.setattr(pilot, "calibration_plan", lambda root, cap: plan)
    monkeypatch.setattr(pilot, "_BENCHMARK_MANIFESTS", {"code": "base.json"})
    monkeypatch.setattr(pilot, "_calibration_manifest", lambda *a, **kw: {"fixture": True})
    monkeypatch.setattr(pilot, "_json_command", lambda *a, **kw: {"fixture": True})

    def reconcile(**kw):
        attempt = kw["attempt"]
        if attempt["status"] != "incomplete_public_boundary":
            return False
        attempt.update(status="completed", termination="completed",
                       public_boundary={"elapsed_seconds": None, "category_charge_seconds": 30.0})
        return True

    monkeypatch.setattr(pilot, "_reconcile_retained_attempt", reconcile)
    actual = pilot.run_calibration(repository_root=tmp_path, caps_path=caps_path, output_root=output)
    assert actual["allocation"]["retained_public_boundary_seconds"] == 31.0


def test_reentering_capped_calibration_preserves_status_and_audit(tmp_path, monkeypatch):
    plan, _ = surface()
    cell = plan["cells"][0]
    plan = {"cells": [cell], "calibration_digest": "c" * 64, "calibration_input": {"selection_rule": "fixture"}}
    caps = {"design_amendment": {"sha256": "d" * 64, "path": "fixture.json"},
            "allocation": {"categories": {"calibration": {"wall_seconds_max": 2}}}}
    caps_path = tmp_path / "caps.json"
    caps_path.write_text(json.dumps(caps))
    (tmp_path / "base.json").write_text("{}")
    monkeypatch.setattr(pilot, "calibration_plan", lambda root, cap: plan)
    monkeypatch.setattr(pilot, "_BENCHMARK_MANIFESTS", {"code": "base.json"})
    monkeypatch.setattr(pilot, "_calibration_manifest", lambda *a, **kw: {"fixture": True})

    def preflight_only(root, verb, *args, **kw):
        assert verb == "preflight", "no public sample can start after this cap"
        return {"fixture": True}

    monkeypatch.setattr(pilot, "_json_command", preflight_only)
    output = tmp_path / "calibration"
    first = pilot.run_calibration(repository_root=tmp_path, caps_path=caps_path, output_root=output)
    assert first["status"] == "cap_reached"
    assert audit.audit_surface(plan, first)["status"] == "passed"
    second = pilot.run_calibration(repository_root=tmp_path, caps_path=caps_path, output_root=output)
    assert second["status"] == "cap_reached"
    assert audit.audit_surface(plan, second)["status"] == "passed"
    assert first == second
    invalid = {**second, "result_digest": "0" * 64}
    result_path = output / "result.json"
    result_path.write_text(json.dumps(invalid))
    retained_bytes = result_path.read_bytes()
    with pytest.raises(ValueError, match="provenance or digest"):
        pilot.run_calibration(repository_root=tmp_path, caps_path=caps_path, output_root=output)
    assert result_path.read_bytes() == retained_bytes
