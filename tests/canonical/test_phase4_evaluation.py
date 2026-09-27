"""Fresh Phase 4 evaluation gates and manifest contracts."""

from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
evaluation = importlib.import_module("run_phase4_evaluation")
pilot = importlib.import_module("run_phase4_pilots")


def _caps() -> dict:
    return json.loads((ROOT / "data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8"))


def _terminal_calibration(caps: dict) -> dict:
    plan = pilot.calibration_plan(ROOT, caps)
    codes = {code_id: {"presets": {
        "source_procedure": {"configurations": []},
        "canonical_default": {"configurations": []},
    }} for code_id in caps["codes"]}
    value = {"status": "completed_with_inconclusive", "caps_sha256": evaluation._byte_sha(
        ROOT / "data/manifests/phase4-pilot-caps.json"),
        "calibration_digest": plan["calibration_digest"], "calibration_input": plan["calibration_input"],
        "evaluation_namespace_accessed": False, "codes": codes}
    value["result_digest"] = pilot._digest(value)
    return value


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_fresh_evaluation_rejects_live_calibration_before_freezing(tmp_path):
    caps = _caps()
    calibration = _terminal_calibration(caps)
    calibration["status"] = "running"
    calibration["result_digest"] = pilot._digest({k: v for k, v in calibration.items() if k != "result_digest"})
    path = tmp_path / "calibration.json"
    _write(path, calibration)
    selection = tmp_path / "selected-settings.json"
    with pytest.raises(ValueError, match="terminal calibration"):
        evaluation.verified_inputs(root=ROOT, calibration_path=path, selection_path=selection,
                                   freeze_selection=True)
    assert not selection.exists()


def test_fresh_evaluation_freezes_exact_selection_and_rejects_drift(tmp_path):
    caps = _caps()
    calibration = _terminal_calibration(caps)
    path = tmp_path / "calibration.json"
    selection_path = tmp_path / "selected-settings.json"
    _write(path, calibration)
    _, _, selected = evaluation.verified_inputs(root=ROOT, calibration_path=path,
                                                 selection_path=selection_path, freeze_selection=True)
    assert selected == pilot.select_calibration_settings(calibration)
    selected["codes"]["gross-bb-144"]["presets"]["source_procedure"]["status"] = "selected_finite_precision_limited"
    _write(selection_path, selected)
    with pytest.raises(ValueError, match="differ from deterministic"):
        evaluation.verified_inputs(root=ROOT, calibration_path=path,
                                   selection_path=selection_path, freeze_selection=True)
    calibration["evaluation_namespace_accessed"] = True
    calibration["result_digest"] = pilot._digest({k: v for k, v in calibration.items() if k != "result_digest"})
    _write(path, calibration)
    with pytest.raises(ValueError, match="samples were already accessed"):
        evaluation.verified_inputs(root=ROOT, calibration_path=path,
                                   selection_path=selection_path, freeze_selection=True)


def test_fresh_evaluation_plan_caps_arms_and_b1_work():
    caps = _caps()
    selected = pilot.select_calibration_settings(_terminal_calibration(caps))
    code_id = "b1-ghp-882"
    candidate = caps["codes"][code_id]["coarse_candidates"][0]
    selected["codes"][code_id]["presets"]["source_procedure"] = {
        "status": "selected_finite_precision_limited", "candidate": candidate,
        "configuration_id": f"{code_id}:source_procedure:coarse:{candidate['id']}"}
    plan = evaluation.evaluation_plan(caps, selected)
    assert len(plan["cells"]) == 3 * len(caps["codes"])
    assert {cell["arm"] for cell in plan["cells"]} == set(evaluation.ARMS)
    assert all(cell["shots"] == 448 for cell in plan["cells"])
    assert all(cell["sample_namespace"] not in {caps["codes"][cell["code_id"]]["calibration_namespace"],
                                                 caps["codes"][cell["code_id"]]["native_namespace"]}
               for cell in plan["cells"])
    source = next(cell for cell in plan["cells"] if cell["code_id"] == code_id and cell["arm"] == "selected_source_procedure")
    assert source["status"] == "ready"
    assert source["work_cap"]["bp_calls"] == 3
    assert source["work_cap"]["relay_transfers"] == 2
    assert plan["shared_settings_view"]["status"] == "not_admitted_by_current_v4_evaluation_arm_cap"
    modified = deepcopy(caps)
    modified["evaluation"]["arms_per_code"].append("shared_source")
    with pytest.raises(ValueError, match="arm cap drifted"):
        evaluation.evaluation_plan(modified, selected)


def test_fresh_evaluation_manifest_preflights_and_matches_samples(tmp_path):
    from bp_registry.manifests import preflight

    caps = _caps()
    code_id = "gross-bb-144"
    selected = pilot.select_calibration_settings(_terminal_calibration(caps))
    candidate = caps["codes"][code_id]["coarse_candidates"][0]
    selected["codes"][code_id]["presets"]["source_procedure"] = {
        "status": "selected_finite_precision_limited", "candidate": candidate,
        "configuration_id": f"{code_id}:source_procedure:coarse:{candidate['id']}"}
    plan = evaluation.evaluation_plan(caps, selected)
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[code_id]).read_text(encoding="utf-8"))
    manifests = {}
    for arm in ("baseline", "selected_source_procedure"):
        cell = next(cell for cell in plan["cells"] if cell["code_id"] == code_id and cell["arm"] == arm)
        manifest = evaluation.build_manifest(base=base, cell=cell, plan=plan)
        path = tmp_path / f"{arm}.json"
        _write(path, manifest)
        assert preflight(path).artifact is not None
        manifests[arm] = manifest
    assert manifests["baseline"]["randomness"]["physical_sample_identity"] == manifests["selected_source_procedure"]["randomness"]["physical_sample_identity"]
    assert manifests["baseline"]["run_id"] != manifests["selected_source_procedure"]["run_id"]
    assert manifests["selected_source_procedure"]["policies"]["update"]["kind"] == "min_sum"
    assert manifests["selected_source_procedure"]["budgets"]["max_shots"] == 448


def test_fresh_evaluation_no_proposal_is_a_failure_and_incomplete_is_separate():
    rows = [
        {"shot_id": 0, "status": "completed", "diagnostic_cell": "no_proposal",
         "selected": False, "termination": "budget_exhausted", "work_vector": {}},
        {"shot_id": 1, "status": "completed", "diagnostic_cell": "valid_correct",
         "selected": True, "termination": "completed", "work_vector": {}},
        {"shot_id": 2, "status": "incomplete_public_boundary", "termination": None},
    ]
    summary = evaluation.summarize_rows(rows, planned=4)
    assert summary["diagnostic_cells"]["no_proposal"] == 1
    assert summary["all_shot_failure"]["failures"] == 1
    assert summary["all_shot_failure"]["denominator"] == 2
    assert summary["incomplete_or_unstarted"] == 2


def test_fresh_evaluation_category_cap_stops_before_shot(tmp_path):
    caps = _caps()
    selection = pilot.select_calibration_settings(_terminal_calibration(caps))
    plan = evaluation.evaluation_plan(caps, selection)
    cell = next(cell for cell in plan["cells"] if cell["code_id"] == "gross-bb-144" and cell["arm"] == "baseline")
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[cell["code_id"]]).read_text(encoding="utf-8"))
    manifest = evaluation.build_manifest(base=base, cell=cell, plan=plan)
    output = tmp_path / "baseline"
    output.mkdir()
    _write(output / "manifest.json", manifest)
    _write(output / "preflight.json", {"status": "passed"})
    result = evaluation.run_cell(root=ROOT, cell=cell, manifest=manifest, output=output,
                                 category_wall_seconds_max=900.0, category_wall_seconds_used=900.0)
    assert result["status"] == "category_cap_reached"
    assert result["summary"]["attempted"] == 0
    assert not (output / "attempts.json").exists()


def test_fresh_evaluation_matched_summary_rejects_sample_drift(tmp_path):
    code_id = "gross-bb-144"
    for arm, sample in (("baseline", "sample-a"), ("selected_source_procedure", "sample-b")):
        path = tmp_path / code_id / arm
        path.mkdir(parents=True)
        (path / "attempts.json").write_text(json.dumps([{
            "shot_id": 0, "status": "completed", "sample_identity": sample,
            "diagnostic_cell": "valid_correct", "selected": True,
        }]), encoding="utf-8")
    with pytest.raises(ValueError, match="sample mismatch"):
        evaluation.matched_summary(output=tmp_path, code_id=code_id,
                                   first="baseline", second="selected_source_procedure")


def test_fresh_native_pair_uses_frozen_disjoint_namespace_and_count():
    caps = _caps()
    selected = pilot.select_calibration_settings(_terminal_calibration(caps))
    code_id = "gross-bb-144"
    candidate = caps["codes"][code_id]["coarse_candidates"][0]
    selected["codes"][code_id]["presets"]["source_procedure"] = {
        "status": "selected_finite_precision_limited", "candidate": candidate,
        "configuration_id": f"{code_id}:source_procedure:coarse:{candidate['id']}"}
    plan = evaluation.evaluation_plan(caps, selected)
    native = evaluation.native_cell(caps, selected, code_id, plan)
    assert native["shots"] == 73
    assert native["sample_namespace"] == caps["codes"][code_id]["native_namespace"]
    assert native["sample_namespace"] != caps["codes"][code_id]["evaluation_namespace"]
    assert native["candidate"] == candidate
    modified = deepcopy(caps)
    modified["codes"][code_id]["native_shots_per_code"] += 1
    with pytest.raises(ValueError, match="native shot count drifted"):
        evaluation.native_cell(modified, selected, code_id, plan)


def test_fresh_native_gamma_translation_is_deterministic_and_decoder_visible():
    caps = _caps()
    selected = pilot.select_calibration_settings(_terminal_calibration(caps))
    code_id = "gross-bb-144"
    candidate = caps["codes"][code_id]["coarse_candidates"][0]
    selected["codes"][code_id]["presets"]["source_procedure"] = {
        "status": "selected_finite_precision_limited", "candidate": candidate,
        "configuration_id": f"{code_id}:source_procedure:coarse:{candidate['id']}"}
    plan = evaluation.evaluation_plan(caps, selected)
    cell = evaluation.native_cell(caps, selected, code_id, plan)
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[code_id]).read_text(encoding="utf-8"))
    manifest = evaluation.build_manifest(base=base, cell=cell, plan=plan)
    observation = {"check_matrix": [[1, 0, 1], [0, 1, 1]], "sample_identity": "public-sample-0"}
    first, digests = evaluation.explicit_native_gammas(manifest, observation, later_legs=2)
    second, repeated = evaluation.explicit_native_gammas(manifest, observation, later_legs=2)
    assert first.shape == (2, 3)
    assert first.tolist() == second.tolist()
    assert len(digests) == 2 and digests == repeated
    changed = {**observation, "sample_identity": "public-sample-1"}
    assert evaluation.explicit_native_gammas(manifest, changed, later_legs=2)[1] != digests


def test_fresh_native_started_attempt_charges_declared_boundary(tmp_path):
    pair = tmp_path / "gross-bb-144"
    (pair / "canonical").mkdir(parents=True)
    (pair / "canonical" / "attempts.json").write_text(json.dumps([{"shot_id": 0,
        "public_boundary": {"elapsed_seconds": 12.5}}]), encoding="utf-8")
    _write(pair / "native-attempts.json", {"attempts": [{"shot_id": 0,
        "status": "incomplete_interrupted"}]})
    assert evaluation.native_category_wall(tmp_path) == 912.5


def test_terminal_candidate_uses_completed_candidate_and_budget_diagnostic_candidate():
    terminal = {"candidate": [1, 0], "candidate_lineage_id": "candidate-lineage",
                "diagnostic_candidate": [0, 1], "diagnostic_candidate_origin": "last-sweep"}
    assert evaluation.terminal_candidate_for_diagnosis(terminal, termination="completed") == ([1, 0], "candidate-lineage")
    assert evaluation.terminal_candidate_for_diagnosis(terminal, termination="max_iterations") == ([0, 1], "last-sweep")
