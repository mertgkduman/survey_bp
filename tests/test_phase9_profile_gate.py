"""Measured-first Yao small-fixture gate before any Phase 9 B1 assessment."""

from __future__ import annotations

from argparse import Namespace
from hashlib import sha256
import json
from pathlib import Path

from bp_registry.campaigns import cli
from bp_registry.literature import parse_literature_policy
from bp_registry.manifests import preflight


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/phase9-yao-small-profile.json"
STUDY = ROOT / "data/studies/phase9-css-profile-tracer-v1.json"
POLICY = ROOT / "literature_policies/yao-2024-guided-decimation/bpgd-t001.toml"


def test_tracer_policy_compiles_to_small_algebraic_manifest() -> None:
    manifest = json.loads(MANIFEST.read_text())
    design = json.loads(STUDY.read_text())
    projection = parse_literature_policy(POLICY).decoder_projection(code_block_length=3)
    assert design["label"] == "development_fixture"
    assert design["assessment_status"] == "not_assessed"
    assert design["policy_sha256"] == sha256(POLICY.read_bytes()).hexdigest()
    assert design["manifest_sha256"] == sha256(MANIFEST.read_bytes()).hexdigest()
    assert manifest["schema_version"] == 5
    assert manifest["intervention"]["round_limit"] == projection["intervention"]["round_limit"] == 3
    assert manifest["intervention"]["finite_bias_magnitude"] == 25.0
    assert manifest["evidence"]["assessment_status"] == "not_assessed"
    preflight(MANIFEST)


def test_tracer_public_policy_ledger_seal_merge_and_verify(tmp_path: Path) -> None:
    design = json.loads(STUDY.read_text())
    campaign = tmp_path / "campaign.json"
    campaign.write_text(json.dumps(design["campaign_document"]), encoding="utf-8")
    planned = cli._plan(Namespace(campaign=str(campaign), campaign_root=str(ROOT), output_root=str(tmp_path / "plan")))
    assert planned["publication_slurm_authorization"] == "deny"
    plan_path = planned["artifact_path"]
    first = cli._run(Namespace(plan=plan_path, campaign_root=str(ROOT), output_root=str(tmp_path / "run")), route="local")
    assert first["campaign_state"] == "progress"
    assert first["completed_shots"] == 1
    second = cli._run(Namespace(plan=plan_path, campaign_root=str(ROOT), output_root=str(tmp_path / "run")), route="local")
    assert second["campaign_state"] == "cap_censored"
    assert second["completed_shots"] == 2
    merged = cli._merge(Namespace(plan=plan_path, receipt=[second["receipt_path"]], campaign_root=str(ROOT), output_root=str(tmp_path / "merge")))
    assessed = cli._assess(Namespace(plan=plan_path, merge=merged["artifact_path"], campaign_root=str(ROOT), output_root=str(tmp_path / "report")))
    verified = cli._verify(Namespace(plan=plan_path, merge=merged["artifact_path"], report=assessed["artifact_path"], receipt=None, campaign_root=str(ROOT)))
    assert verified["verified"] is True
    assert assessed["report"]["assessment_status"] == "inconclusive_cap_censored"
    assert assessed["report"]["inverse_binomial_rate"] is None
    assert len(list((tmp_path / "run" / "attempts").glob("*/events.jsonl"))) == 2


def test_measured_replay_receipt_denies_publication_and_retains_missing_site_facts() -> None:
    gate = json.loads((ROOT / "data/results/phase9-css-profile-tracer-v1/profile-gate.json").read_text())
    assert gate["schema"] == "phase9_css_profile_gate_v1"
    assert gate["label"] == "development_fixture"
    assert gate["assessment_status"] == "not_assessed"
    assert gate["publication_slurm_authorization"] == "deny"
    assert gate["replay"]["verified"] is True
    assert gate["measurements"]["execution_wall_ns"]["value"] > 0
    assert gate["measurements"]["replay_wall_ns"]["value"] > 0
    assert gate["site"]["wall_ceiling"]["status"] == "unavailable"
    assert gate["site"]["scheduler_accounting"]["status"] == "unavailable"
