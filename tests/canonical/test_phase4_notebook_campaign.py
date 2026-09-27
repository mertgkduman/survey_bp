"""Adversarial tests for the read-only Phase 4 notebook campaign adapters."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("phase4_notebook_campaign", ROOT / "scripts" / "phase4_notebook_campaign.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _qualified_result(root: Path, campaign, *, stage="calibration"):
    source = root / "scripts/run_phase4_pilots.py"; source.parent.mkdir(parents=True, exist_ok=True); source.write_text("# producer\n")
    code = root / "data/artifacts/code.json"; _write(code, {"code": "fixture"})
    caps = {"schema_version": 4, "status": "frozen_pre_calibration"}; caps["caps_digest"] = campaign.canonical_digest(caps)
    _write(root / "data/manifests/phase4-pilot-caps.json", caps)
    value = {"schema_version": 1, "status": "completed", "caps_digest": caps["caps_digest"],
             "source_policy_bytes": {"scripts/run_phase4_pilots.py": campaign.byte_sha256(source)},
             "code_manifest_bytes": {"data/artifacts/code.json": campaign.byte_sha256(code)},
             "sample_identity": "fixture-matched-sample-v1", "codes": {"fixture-code": {"status": "completed"}}}
    if stage in campaign.POST_SELECTION:
        selection = {"schema_version": 1, "status": "frozen_from_calibration_only"}; _write(root / "data/results/phase4-memory-relay/selected-settings.json", selection)
        value["selected_settings_digest"] = campaign.canonical_digest(selection)
    value["result_digest"] = campaign.canonical_digest(value)
    return value


def test_missing_and_running_artifacts_remain_explicit_not_synthesized(tmp_path):
    campaign = _module()
    missing = campaign.artifact_snapshot(tmp_path, "evaluation", campaign.ARTIFACT_PATHS["evaluation"])
    assert missing["status"] == "missing"
    _write(tmp_path / campaign.ARTIFACT_PATHS["evaluation"], {"status": "running"})
    running = campaign.artifact_snapshot(tmp_path, "evaluation", campaign.ARTIFACT_PATHS["evaluation"])
    assert running["status"] == "running_or_incomplete"
    assert running["execution_qualified"] is False


def test_terminal_requires_digest_and_byte_bound_source_code_caps_and_samples(tmp_path):
    campaign = _module()
    result = _qualified_result(tmp_path, campaign)
    path = tmp_path / campaign.ARTIFACT_PATHS["calibration"]
    _write(path, result)
    snapshot = campaign.artifact_snapshot(tmp_path, "calibration", campaign.ARTIFACT_PATHS["calibration"])
    assert snapshot["execution_qualified"] is True
    assert snapshot["tables"][0]["code_id"] == "fixture-code"

    tampered = dict(result); tampered["sample_identity"] = "other"
    _write(path, tampered)
    rejected = campaign.artifact_snapshot(tmp_path, "calibration", campaign.ARTIFACT_PATHS["calibration"])
    assert rejected["execution_qualified"] is False
    assert "digest" in rejected["reason"]


def test_post_selection_stage_requires_retained_selection_and_development_fixture_is_not_claim(tmp_path):
    campaign = _module()
    result = _qualified_result(tmp_path, campaign, stage="evaluation")
    path = tmp_path / campaign.ARTIFACT_PATHS["evaluation"]
    _write(path, result)
    qualified = campaign.artifact_snapshot(tmp_path, "evaluation", campaign.ARTIFACT_PATHS["evaluation"])
    assert qualified["execution_qualified"] is True
    (tmp_path / "data/results/phase4-memory-relay/selected-settings.json").unlink()
    unavailable = campaign.artifact_snapshot(tmp_path, "evaluation", campaign.ARTIFACT_PATHS["evaluation"])
    assert unavailable["execution_qualified"] is False
    assert "selected-settings" in unavailable["reason"]
    fixture = campaign.artifact_snapshot(tmp_path, "evaluation", campaign.ARTIFACT_PATHS["evaluation"], development_fixture=True)
    assert fixture["status"] == "development_fixture_not_assessed"


def test_inventory_keeps_historical_agreement_separate_from_selected_campaign(tmp_path):
    campaign = _module()
    _write(tmp_path / "data/results/phase4-memory-relay/author-v022-agreement-v1/runtime-comparison.json", {"status": "completed_derived_diagnostic"})
    inventory = campaign.build_campaign_snapshots(tmp_path)
    historical = inventory["artifacts"]["historical_author_agreement"]
    assert historical["status"] == "historical_provenance_only"
    assert historical["execution_qualified"] is False
    assert inventory["assessment"] == "not_assessed"
    assert all({"stage", "name", "title", "columns", "rows"} <= set(table) for table in inventory["tables"])
