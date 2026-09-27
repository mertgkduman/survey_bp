"""Fresh Phase 4 evaluation gates and manifest contracts."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
evaluation = importlib.import_module("run_phase4_evaluation")
pilot = importlib.import_module("run_phase4_pilots")
calibration_audit = importlib.import_module("verify_phase4_calibration")


def _caps() -> dict:
    return json.loads((ROOT / "data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8"))


def _terminal_calibration(caps: dict) -> dict:
    plan = pilot.calibration_plan(ROOT, caps)
    codes = {code_id: {"presets": {"source_procedure": {"configurations": []},
                                          "canonical_default": {"configurations": []}}}
             for code_id in caps["codes"]}
    for cell in plan["cells"]:
        attempts = [{"shot_id": shot_id, "status": "cap_reached", "termination": None,
                     "failure": "fixture-only cap placeholder", "public_boundary": {"elapsed_seconds": 0.0}}
                    for shot_id in range(cell["calibration_shots"])]
        aggregate = calibration_audit._summary(cell, attempts)
        codes[cell["code_id"]]["presets"][cell["preset_key"]]["configurations"].append({
            "configuration_id": cell["configuration_id"], "candidate": cell["candidate"],
            "relay": cell["relay"], "attempts": attempts, **aggregate,
        })
    value = {"status": "cap_reached", "caps_sha256": evaluation._byte_sha(
        ROOT / "data/manifests/phase4-pilot-caps.json"),
        "calibration_digest": plan["calibration_digest"], "calibration_input": plan["calibration_input"],
        "amendment_sha256": caps["design_amendment"]["sha256"], "evaluation_namespace_accessed": False,
        "allocation": {"category": "calibration", "wall_seconds_max": caps["allocation"]["categories"]["calibration"]["wall_seconds_max"],
                       "retained_public_boundary_seconds": 0.0}, "codes": codes}
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


def _shared_terminal_calibration(caps: dict) -> dict:
    """Fixture-only completed calibration with one jointly eligible candidate."""
    calibration = _terminal_calibration(caps)
    plan = pilot.calibration_plan(ROOT, caps)
    for cell in plan["cells"]:
        if cell["tier"] != "coarse" or cell["candidate"] != caps["codes"][cell["code_id"]]["coarse_candidates"][0]:
            continue
        configurations = calibration["codes"][cell["code_id"]]["presets"][cell["preset_key"]]["configurations"]
        configuration = next(item for item in configurations if item["configuration_id"] == cell["configuration_id"])
        work = {name: 0 for name in cell["per_shot_work_cap"]}
        attempts = [{
            "shot_id": shot_id, "status": "completed", "termination": "completed", "outcome": "exact",
            "sample_identity": sha256(
                f"bp-registry-sample-v1\0{cell['calibration_namespace']}\0{shot_id}".encode("utf-8")
            ).hexdigest(), "work_vector": work,
            "aggregate_event_digest": "0" * 64,
            "public_boundary": {"elapsed_seconds": 0.0,
                                "verify": {"shot_id": shot_id, "termination": "completed"}},
        } for shot_id in range(cell["calibration_shots"])]
        configuration["attempts"] = attempts
        configuration.update(calibration_audit._summary(cell, attempts))
    calibration["status"] = "cap_reached"
    calibration["result_digest"] = evaluation._digest(
        {key: value for key, value in calibration.items() if key != "result_digest"}
    )
    return calibration


def _shared_supplement(tmp_path):
    caps = _caps()
    calibration = _shared_terminal_calibration(caps)
    calibration_path = tmp_path / "calibration.json"
    selection_path = tmp_path / "selected-settings.json"
    _write(calibration_path, calibration)
    _write(selection_path, pilot.select_calibration_settings(calibration))
    counts = {code_id: 1 for code_id in caps["codes"]}
    wall = sum(2 * int(code["canonical_public_boundary_seconds"]) for code in caps["codes"].values())
    supplement = evaluation.build_shared_evaluation_supplement(
        root=ROOT, caps_path=ROOT / "data/manifests/phase4-pilot-caps.json",
        calibration_path=calibration_path, selection_path=selection_path,
        shared_shots_by_code=counts, wall_seconds_max=wall,
    )
    return caps, calibration_path, selection_path, supplement, wall


def test_shared_evaluation_supplement_preserves_legacy_plan_and_matches_namespace(tmp_path):
    caps, _, _, supplement, _ = _shared_supplement(tmp_path)
    legacy_selection = pilot.select_calibration_settings(_shared_terminal_calibration(caps))
    before = evaluation.evaluation_plan(caps, legacy_selection)
    assert supplement["publication_status"] == "prepared_not_published_no_sampling"
    assert supplement["no_production_side_effects"] is True
    assert supplement["source_cap"]["legacy_arms_per_code"] == list(evaluation.ARMS)
    assert evaluation.evaluation_plan(caps, legacy_selection) == before
    assert {cell["arm"] for cell in supplement["cells"]} == {
        "shared_source_procedure", "shared_canonical_procedure"
    }
    for code_id in caps["codes"]:
        rows = [cell for cell in supplement["cells"] if cell["code_id"] == code_id]
        assert {row["sample_namespace"] for row in rows} == {caps["codes"][code_id]["evaluation_namespace"]}
        assert len({row["memory_tuning_identity"] for row in rows}) == 1
        assert {row["kernel"] for row in rows} == {"min_sum", "spa"}


def test_shared_evaluation_manifest_preflights_without_sampling(tmp_path):
    from bp_registry.manifests import preflight

    _, _, selection_path, supplement, _ = _shared_supplement(tmp_path)
    cell = next(item for item in supplement["cells"] if item["arm"] == "shared_source_procedure")
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[cell["code_id"]]).read_text(encoding="utf-8"))
    manifest = evaluation.build_shared_manifest(
        base=base, cell=cell, supplement=supplement,
        caps_path=ROOT / "data/manifests/phase4-pilot-caps.json", selection_path=selection_path,
    )
    assert manifest["randomness"]["physical_sample_identity"] == cell["sample_namespace"]
    assert manifest["policies"]["update"]["kind"] == "min_sum"
    assert "not authorized for sampling" in manifest["evidence"]["procedure"]
    manifest_path = tmp_path / "shared-manifest.json"
    _write(manifest_path, manifest)
    assert preflight(manifest_path).artifact is not None


def test_shared_evaluation_rejects_inconclusive_drift_and_overcommit(tmp_path):
    caps, calibration_path, selection_path, supplement, wall = _shared_supplement(tmp_path)
    with pytest.raises(ValueError, match="overcommitted"):
        evaluation.build_shared_evaluation_supplement(
            root=ROOT, caps_path=ROOT / "data/manifests/phase4-pilot-caps.json",
            calibration_path=calibration_path, selection_path=selection_path,
            shared_shots_by_code={code_id: 1 for code_id in caps["codes"]}, wall_seconds_max=wall - 1,
        )
    tampered = deepcopy(supplement)
    tampered["cells"][0]["arm"] = "factorial_arm_not_admitted"
    tampered["contract_digest"] = evaluation._digest(
        {key: value for key, value in tampered.items() if key != "contract_digest"}
    )
    with pytest.raises(ValueError, match="undeclared"):
        evaluation.shared_evaluation.verify_presampling_supplement(tampered)
    rehashed = deepcopy(supplement)
    rehashed["cells"][0]["shots"] = 2
    rehashed["contract_digest"] = evaluation._digest(
        {key: value for key, value in rehashed.items() if key != "contract_digest"}
    )
    with pytest.raises(ValueError, match="count or boundary drifted"):
        evaluation.shared_evaluation.verify_presampling_supplement(rehashed)
    swapped_kernel = deepcopy(supplement)
    swapped_kernel["cells"][0]["kernel"] = "spa"
    swapped_kernel["contract_digest"] = evaluation._digest(
        {key: value for key, value in swapped_kernel.items() if key != "contract_digest"}
    )
    with pytest.raises(ValueError, match="arm or kernel"):
        evaluation.shared_evaluation.verify_presampling_supplement(swapped_kernel)
    substituted_candidate = deepcopy(supplement)
    code_id = substituted_candidate["cells"][0]["code_id"]
    alternative = caps["codes"][code_id]["coarse_candidates"][1]
    for row in substituted_candidate["cells"]:
        if row["code_id"] == code_id:
            row["candidate"] = alternative
            row["memory_tuning_identity"] = evaluation._digest(alternative)
    substituted_candidate["contract_digest"] = evaluation._digest(
        {key: value for key, value in substituted_candidate.items() if key != "contract_digest"}
    )
    evaluation.shared_evaluation.verify_presampling_supplement(substituted_candidate)
    first = substituted_candidate["cells"][0]
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[first["code_id"]]).read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="frozen source settings"):
        evaluation.build_shared_manifest(
            base=base, cell=first, supplement=substituted_candidate,
            caps_path=ROOT / "data/manifests/phase4-pilot-caps.json", selection_path=selection_path,
        )
    byte_drifted_cap = tmp_path / "byte-drifted-cap.json"
    byte_drifted_cap.write_bytes((ROOT / "data/manifests/phase4-pilot-caps.json").read_bytes() + b"\n")
    first = supplement["cells"][0]
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[first["code_id"]]).read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="cap byte identity drifted"):
        evaluation.build_shared_manifest(
            base=base, cell=first, supplement=supplement,
            caps_path=byte_drifted_cap, selection_path=selection_path,
        )
    changed_selection = json.loads(selection_path.read_text(encoding="utf-8"))
    changed_selection["codes"][next(iter(changed_selection["codes"]))]["shared_memory_settings"]["candidate_id"] = "drift"
    _write(selection_path, changed_selection)
    cell = supplement["cells"][0]
    base = json.loads((ROOT / evaluation.active.CODE_MANIFESTS[cell["code_id"]]).read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="selection byte identity drifted"):
        evaluation.build_shared_manifest(
            base=base, cell=cell, supplement=supplement,
            caps_path=ROOT / "data/manifests/phase4-pilot-caps.json", selection_path=selection_path,
        )


def test_shared_evaluation_marks_fixture_inconclusive_selection_unavailable(tmp_path):
    caps = _caps()
    calibration = _terminal_calibration(caps)
    calibration_path = tmp_path / "calibration.json"
    selection_path = tmp_path / "selected-settings.json"
    _write(calibration_path, calibration)
    _write(selection_path, pilot.select_calibration_settings(calibration))
    wall = sum(2 * int(code["canonical_public_boundary_seconds"]) for code in caps["codes"].values())
    supplement = evaluation.build_shared_evaluation_supplement(
        root=ROOT, caps_path=ROOT / "data/manifests/phase4-pilot-caps.json",
        calibration_path=calibration_path, selection_path=selection_path,
        shared_shots_by_code={code_id: 1 for code_id in caps["codes"]}, wall_seconds_max=wall,
    )
    assert supplement["status"] == "blocked_inconclusive_shared_selection"
    assert supplement["cells"] == []
    with pytest.raises(ValueError, match="ineligible or inconclusive"):
        evaluation.shared_evaluation.verify_presampling_supplement(supplement)
