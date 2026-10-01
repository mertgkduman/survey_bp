"""Public, bounded evidence checks for the Phase 3 matched pilot matrix."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tomllib

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PILOT_SCRIPT = REPOSITORY_ROOT / "scripts" / "run_phase3_pilots.py"
NOTEBOOK_EXECUTOR = REPOSITORY_ROOT / "scripts" / "execute_phase3_notebook.py"
REPORT_ROOT = REPOSITORY_ROOT / "reports" / "phase3-pilots"


def test_analysis_extra_and_notebook_executor_are_pinned_and_confined():
    """D-18 analysis uses exact, isolated dependencies and a project kernel."""
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    assert project.get("optional-dependencies", {}).get("analysis") == [
        "matplotlib==3.10.9",
        "nbformat==5.10.4",
        "nbclient==0.10.2",
        "ipykernel==6.29.5",
        "plotly==7.1.0",
    ]
    assert NOTEBOOK_EXECUTOR.is_file(), "D-18 needs a confined notebook executor"
    executor_source = NOTEBOOK_EXECUTOR.read_text(encoding="utf-8")
    assert 'repository_root / ".venv" / "bin" / "python"' in executor_source
    assert '"argv": [str(interpreter)' in executor_source
    assert 'cell.metadata.pop("execution", None)' in executor_source
    assert "run_phase3_pilots" not in executor_source


def test_retained_pilot_reports_are_qualified_evidence_without_rankings():
    """D-18 outputs retain scopes, work, traces, and D-19 claim limits."""
    outputs = {
        "outcomes": REPORT_ROOT / "outcomes.csv",
        "work": REPORT_ROOT / "work-by-policy.csv",
        "convergence": REPORT_ROOT / "convergence.png",
        "work_runtime": REPORT_ROOT / "work-and-runtime.png",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in outputs.values())

    with outputs["outcomes"].open(newline="", encoding="utf-8") as stream:
        outcome_rows = list(__import__("csv").DictReader(stream))
    with outputs["work"].open(newline="", encoding="utf-8") as stream:
        work_rows = list(__import__("csv").DictReader(stream))

    assert len(outcome_rows) == len(work_rows) == 19
    for row in [*outcome_rows, *work_rows]:
        assert row["relation"] == "pilot_adaptation"
        assert row["assessment_status"] == "not_assessed"
        assert row["equal_total_cost_claim"] == "False"
        assert len(row["evidence_sha256"]) == 64
        assert row["trace_evidence_link"].startswith("data/results/phase3-pilots/events.jsonl#")
    assert {row["outcome"] for row in outcome_rows} == {"missing"}
    assert {row["outcome_missing_reason"] for row in outcome_rows} == {"unavailable_due_to_stopping"}
    assert {row["denominator_shots"] for row in outcome_rows} == {"1"}
    assert {row["cohort_terminal_count"] for row in outcome_rows} == {"19"}
    assert all(row["setup_runtime_ns"] and row["decode_runtime_ns"] for row in outcome_rows)
    assert all(row["full_work_vector_json"] and row["qualified_iterations"] for row in work_rows)
    assert all("full_work_units" not in row for row in work_rows)
    notebook = json.loads((REPOSITORY_ROOT / "notebooks" / "phase3-pilot-analysis.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "full_work_units" not in source


def _pilot_module():
    spec = importlib.util.spec_from_file_location("phase3_pilots", PILOT_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bb144_tracer_runs_through_public_preflight_run_and_verify(tmp_path):
    """The first matched lane is durable public evidence, not an internal shortcut."""
    assert PILOT_SCRIPT.is_file(), "Phase 3 needs a public BB-144 pilot runner"
    module = _pilot_module()
    report = module.run_pilots(
        repository_root=REPOSITORY_ROOT,
        output_root=tmp_path / "phase3-pilots",
        manifest_names=("phase3-pilot-bb144.json",),
    )
    assert report["code_ids"] == ["gross-bb-144"]
    assert report["labels"] == {"relation": "pilot_adaptation", "assessment_status": "not_assessed"}
    assert report["matched_sample_identities"] is True
    assert report["verified_terminals"]
    assert all(item["setup_runtime"]["value"] is not None and item["decode_runtime"]["value"] is not None for item in report["verified_terminals"])
    assert (tmp_path / "phase3-pilots" / "events.jsonl").is_file()
    assert (tmp_path / "phase3-pilots" / "result.json").is_file()


def test_focused_b1_and_hgp_matrix_retains_schedules_parameters_and_rejection():
    """Inspect the retained, publicly verified large-code pilot matrix."""
    module = _pilot_module()
    output = REPOSITORY_ROOT / "data" / "results" / "phase3-pilots"
    report = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert report["code_ids"] == ["b1-ghp-882", "gross-bb-144", "hgp-gallager-3-4-seed-20260923"]
    terminals = [item for item in report["verified_terminals"] if item["code_id"] != "gross-bb-144"]
    assert len(terminals) == 15
    bindings = {item["policy_effects"]["schedule"]["binding_id"] for item in terminals}
    assert {f"schedule-{kind}-v1" for kind in ("layered", "check-node-serial", "variable-node-serial", "randomized", "residual")} <= bindings
    assert any(item["policy_effects"]["update"]["binding_id"] == "update-normalized-min-sum-v1" for item in terminals)
    assert any(
        item["run_id"] == "phase3-hgp-gallager-nms-seeded"
        and "parameter_assignment" in item["policy_effects"]["update"]
        and item["policy_effects"]["update"]["parameter_generation"]["refresh_scope"] == "configuration"
        for item in terminals
    )
    assert all(item["budget_views"]["common_c2v_cap"] > 0 and item["budget_views"]["qualified_iteration_limit"] == 1 for item in terminals)
    assert all(item["budget_views"]["equal_total_cost_claim"] is False for item in terminals)
    assert all(item["setup_runtime"]["value"] is not None and item["decode_runtime"]["value"] is not None for item in terminals)
    assert all(item["artifact_raw_sha256"] and item["artifact_semantic_sha256"] and item["composition_identity"] for item in terminals)
    assert all({"hx_raw_sha256", "hz_raw_sha256", "lx_raw_sha256", "lz_raw_sha256"} <= item["matrix_hashes"].keys() for item in terminals)
    assert report["matched_sample_identities"] is True
    assert report["rejected_undefined"] is True
    assert len(report["public_verify_reports"]) == len(report["verified_terminals"])
    assert all((REPOSITORY_ROOT / item["output"] / "result.json").is_file() for item in report["public_verify_reports"])
    undefined = output / "manifests" / "undefined-randomized-without-controls.json"
    with pytest.raises(RuntimeError):
        module._json_command(REPOSITORY_ROOT, "preflight", str(undefined))
