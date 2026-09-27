"""Focused tests for the Phase 4 factorial preparation contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("phase4_factorial", ROOT / "scripts" / "run_phase4_factorial.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _inputs():
    return (
        json.loads((ROOT / "data/evidence/phase4-pilot-design.json").read_text(encoding="utf-8")),
        json.loads((ROOT / "data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8")),
        json.loads((ROOT / "data/evidence/phase4-factorial-execution-supplement-v1.json").read_text(encoding="utf-8")),
    )


def test_factorial_plan_is_finite_matched_and_preserves_frozen_binding_arrays():
    runner = _module()
    design, caps, supplement = _inputs()

    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)

    assert len(plan["cells"]) == 14 * 3 * 3 * 7
    assert plan["status"] == "prepared_no_sampling"
    damping = next(cell for cell in plan["cells"] if cell["arm_id"] == "v2c-damping-plus-ewa")
    assert damping["original_binding_array"] == ["v2c_damping", "affine_prior"]
    assert damping["execution_order"] == ["affine_prior", "v2c_damping"]
    cohort = [cell for cell in plan["cells"] if cell["code_id"] == damping["code_id"] and cell["noise_region"] == damping["noise_region"] and cell["shot_id"] == damping["shot_id"]]
    assert len(cohort) == 14
    assert len({cell["physical_sample_identity"] for cell in cohort}) == 1
    assert all(cell["fidelity"]["assessment"] == "not_assessed" for cell in plan["cells"])
    assert plan["blocked_execution_arms"] == []
    assert plan["outcome_cells"] == [
        "valid_correct", "valid_wrong_logical", "invalid_correct",
        "invalid_wrong_logical", "no_proposal",
    ]


def test_factorial_requires_complete_fresh_evaluation_and_admitted_arms(tmp_path):
    runner = _module()
    design, caps, supplement = _inputs()
    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)
    evaluation = tmp_path / "evaluation.json"
    evaluation.write_text(json.dumps({"status": "inconclusive"}), encoding="utf-8")

    with pytest.raises(ValueError, match="fresh evaluation"):
        runner.assert_factorial_predecessor(evaluation_path=evaluation, plan=plan)

    fixture = runner.development_fixture_evaluation(plan)
    evaluation.write_text(json.dumps(fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="development fixture"):
        runner.assert_factorial_predecessor(evaluation_path=evaluation, plan=plan)
    gate = runner.assert_factorial_predecessor(evaluation_path=evaluation, plan=plan, allow_development_fixture=True)
    assert gate["development_fixture"] is True
    assert gate["assessment"] == "not_assessed"


def test_development_fixture_runner_retains_all_outcomes_and_terminal_measurements(tmp_path):
    runner = _module()
    design, caps, supplement = _inputs()
    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)
    evaluation = tmp_path / "evaluation.json"
    evaluation.write_text(json.dumps(runner.development_fixture_evaluation(plan)), encoding="utf-8")

    def executor(cell):
        outcome = ["valid_correct", "valid_wrong_logical", "invalid_correct", "invalid_wrong_logical", "no_proposal"][cell["shot_id"] % 5]
        return {
                "cell_id": cell["cell_id"], "sample_namespace": cell["factorial_namespace"], "sample_identity": cell["physical_sample_identity"],
            "execution_status": "completed", "terminal": True, "diagnostic_cell": outcome,
            "selected": outcome in {"valid_correct", "valid_wrong_logical"},
            "candidate_origin": "ordinary_memory" if cell["arm_kind"] != "common_baseline" else "baseline",
            "raw_work": {"per_leg": [{"variable_to_check_updates": 4}], "total": {"variable_to_check_updates": 4}},
            "runtime_seconds": float(cell["shot_id"] + 1),
            "resource": {"maxrss_kib": None, "missing_reason": "development fixture does not measure RSS"},
            "trace": {"ledger_id": f"fixture-{cell['cell_id']}", "status": "not_collected"},
        }

    report = runner.run_factorial(evaluation_path=evaluation, plan=plan, executor=executor, allow_development_fixture=True)

    assert report["status"] == "development_fixture_not_assessed"
    summaries = report["aggregate"]["by_cell"].values()
    assert sum(sum(summary["diagnostic_cells"].values()) for summary in summaries) == len(plan["cells"])
    summaries = list(report["aggregate"]["by_cell"].values())
    assert all(summary["runtime_seconds"]["p95"] is not None for summary in summaries)
    assert sum(summary["resource_maxrss_kib"]["missing"] for summary in summaries) == len(plan["cells"])
    assert all(record["terminal"] for record in report["terminals"])


def test_factorial_manifest_preflights_all_frozen_arms_and_keeps_factorial_namespace_separate(tmp_path):
    runner = _module()
    design, caps, supplement = _inputs()
    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)
    manifests = runner.materialize_public_manifests(repository_root=ROOT, plan=plan, code_id="gross-bb-144")

    assert len(manifests) == 14 * 3
    namespaces = {manifest["randomness"]["physical_sample_identity"] for manifest in manifests.values()}
    assert len(namespaces) == 3
    assert all("factorial" in namespace for namespace in namespaces)
    assert len({manifest["randomness"]["decoder_seed_identity"] for manifest in manifests.values()}) == 14 * 3
    assert all(manifest["schema_version"] == 4 for manifest in manifests.values())


def test_incomplete_execution_is_retained_outside_proposal_cells():
    runner = _module()
    design, caps, supplement = _inputs()
    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)
    first, second = plan["cells"][:2]
    aggregate = runner.aggregate_terminals([
        {"code_id": first["code_id"], "noise_region": first["noise_region"], "arm_id": first["arm_id"],
         "execution_status": "completed", "diagnostic_cell": "no_proposal", "selected": False,
         "raw_work": {}, "resource": {"maxrss_kib": None}},
        {"code_id": second["code_id"], "noise_region": second["noise_region"], "arm_id": second["arm_id"],
         "execution_status": "incomplete_public_boundary", "terminal": False, "raw_work": None,
         "resource": {"maxrss_kib": None}},
    ], plan)
    completed = next(value for key, value in aggregate["by_cell"].items() if key.endswith(first["arm_id"]))
    incomplete = next(value for key, value in aggregate["by_cell"].items() if key.endswith(second["arm_id"]))
    assert completed["diagnostic_cells"]["no_proposal"] == 1
    assert completed["all_shot_failure"]["failures"] == 1
    assert incomplete["completed"] == 0
    assert incomplete["execution_statuses"]["incomplete_public_boundary"] == 1
