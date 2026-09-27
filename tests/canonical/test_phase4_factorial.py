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
    assert plan["blocked_execution_arms"] == ["disordered-affine-prior"]


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
        outcome = ["proposed_selected", "proposed_unselected", "no_proposal", "terminal_failure", "terminal_incomplete"][cell["shot_id"] % 5]
        return {
            "terminal": True, "outcome_cell": outcome, "candidate_origin": "ordinary_memory" if cell["arm_kind"] != "common_baseline" else "baseline",
            "raw_work": {"per_leg": [{"variable_to_check_updates": 4}], "total": {"variable_to_check_updates": 4}},
            "runtime_seconds": float(cell["shot_id"] + 1),
            "resource": {"maxrss_kib": None, "missing_reason": "development fixture does not measure RSS"},
            "trace": {"ledger_id": f"fixture-{cell['cell_id']}", "status": "not_collected"},
        }

    report = runner.run_factorial(evaluation_path=evaluation, plan=plan, executor=executor, allow_development_fixture=True)

    assert report["status"] == "development_fixture_not_assessed"
    assert sum(report["aggregate"]["outcome_cells"].values()) == len(plan["cells"])
    assert report["aggregate"]["runtime_seconds"]["p95"] is not None
    assert report["aggregate"]["resource"]["maxrss_kib"]["missing"] == len(plan["cells"])
    assert all(record["terminal"] for record in report["terminals"])


def test_production_runner_rejects_plan_with_unimplemented_disordered_ordinary_arm(tmp_path):
    runner = _module()
    design, caps, supplement = _inputs()
    plan = runner.build_factorial_plan(design=design, caps=caps, supplement=supplement)
    evaluation = runner.development_fixture_evaluation(plan)
    evaluation.update({"development_fixture": False, "assessment": "assessed"})
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(evaluation), encoding="utf-8")

    with pytest.raises(ValueError, match="without an executable"):
        runner.run_factorial(evaluation_path=path, plan=plan, executor=lambda _cell: {})
