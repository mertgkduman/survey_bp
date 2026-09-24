"""Public, bounded evidence checks for the Phase 3 matched pilot matrix."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PILOT_SCRIPT = REPOSITORY_ROOT / "scripts" / "run_phase3_pilots.py"


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
