"""Bounded Yao B1 canonical adaptation, with source gaps kept explicit."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from bp_registry.campaigns.targets import TableTargetReceiptV1
from bp_registry.campaigns.contracts import FailureCountExecutableLimitReceiptV1
from bp_registry.literature import parse_literature_policy
from bp_registry.manifests import preflight
from bp_registry.runner import canonical_public_manifest_context, derive_canonical_executable_maxima


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "literature_policies/yao-2024-guided-decimation/bpgd-t001.toml"
SOURCE = ROOT / "literature_policies/yao-2024-guided-decimation/paper_reproduction/source-targets-v1.json"
GATE = ROOT / "data/results/phase9-css-profile-tracer-v1/profile-gate.json"
MANIFEST = ROOT / "data/manifests/phase9-yao-b1-t001-p010-v1.json"
STUDY = ROOT / "data/studies/phase9-yao-b1-t001-p010-v1.json"
STUDY_V2 = ROOT / "data/studies/phase9-yao-b1-t001-p010-v2.json"
STUDY_V4 = ROOT / "data/studies/phase9-yao-b1-t001-p010-v4.json"
TARGET = ROOT / "data/studies/phase9-yao-b1-t001-p010-source-target-v1.json"
FIRST_RESULTS = ROOT / "data/results/phase9-yao-b1-t001-p010-v1"
RESULTS = ROOT / "data/results/phase9-yao-b1-t001-p010-v4"


def test_b1_verified_executable_maximum_is_representable() -> None:
    derived = derive_canonical_executable_maxima(canonical_public_manifest_context(MANIFEST))
    assert derived.derived_evidence_bytes_per_unit > 64 * 1024 * 1024
    receipt = FailureCountExecutableLimitReceiptV1.model_validate(
        {"schema": "failure_count_executable_limit_receipt_v1", **derived.as_evidence()})
    assert receipt.derived_evidence_bytes_per_unit == derived.derived_evidence_bytes_per_unit


def test_explicit_large_event_ceiling_keeps_legacy_b1_manifest_identity() -> None:
    from bp_registry.manifests import manifest_digest

    legacy = preflight(MANIFEST).manifest
    legacy_digest = manifest_digest(legacy)
    assert legacy.guarded_event_ceiling_bytes is None
    assert legacy_digest == canonical_public_manifest_context(MANIFEST).manifest_sha256
    expanded_path = ROOT / "data/manifests/phase9-yao-b1-t001-p010-v3.json"
    expanded = preflight(expanded_path).manifest
    assert expanded.guarded_event_ceiling_bytes == 1_048_576
    assert expanded.artifact == legacy.artifact
    expanded_limits = derive_canonical_executable_maxima(canonical_public_manifest_context(expanded_path))
    assert expanded_limits.serializer_bytes_per_event == 1_048_576
    assert expanded_limits.derived_evidence_bytes_per_unit > 3_000_000_000


def test_observed_large_work_event_has_new_guarded_v4_identity() -> None:
    failed = ROOT / "data/results/phase9-yao-b1-t001-p010-v3/run/attempts/00000001-757a1d1bbe51da66/events.jsonl"
    assert failed.is_file()
    assert not any(json.loads(line)["kind"] == "termination" for line in failed.read_text().splitlines())
    manifest = ROOT / "data/manifests/phase9-yao-b1-t001-p010-v4.json"
    expanded = preflight(manifest).manifest
    assert expanded.guarded_event_ceiling_bytes == 4_194_304
    limits = derive_canonical_executable_maxima(canonical_public_manifest_context(manifest))
    assert limits.serializer_bytes_per_event == 4_194_304
    assert limits.derived_evidence_bytes_per_unit > 14_000_000_000


def test_profile_gate_preflight_and_label_bind_source_before_b1_launch() -> None:
    gate = json.loads(GATE.read_text())
    assert gate["replay"]["verified"] is True
    assert gate["publication_slurm_authorization"] == "deny"
    source = json.loads(SOURCE.read_text())
    authored = next(item for item in source["table_target_receipts"] if item["target_id"] == "yao-fig3-bpgd-t001-p010")
    target = TableTargetReceiptV1.model_validate_json(TARGET.read_bytes())
    assert target.model_dump(mode="json", by_alias=True, exclude_none=True) == authored
    assert target.reported.value == 0.855932
    manifest = json.loads(MANIFEST.read_text())
    study = json.loads(STUDY.read_text())
    assert study["label"] == "canonical_adaptation"
    assert study["source_identity_status"] == "unverified"
    assert study["target_receipt_sha256"] == sha256(TARGET.read_bytes()).hexdigest()
    assert study["profile_gate_sha256"] == sha256(GATE.read_bytes()).hexdigest()
    assert study["policy_sha256"] == sha256(POLICY.read_bytes()).hexdigest()
    assert study["manifest_sha256"] == sha256(MANIFEST.read_bytes()).hexdigest()
    assert manifest["intervention"]["round_limit"] == parse_literature_policy(POLICY).decoder_projection(code_block_length=882)["intervention"]["round_limit"]
    assert manifest["artifact"]["code_id"] == "b1-ghp-882"
    assert manifest["error_rate"] == 0.1
    assert manifest["evidence"]["relation"] == "pilot_adaptation"
    assert manifest["evidence"]["assessment_status"] == "not_assessed"
    preflight(MANIFEST)


def test_first_batch_replay_retains_bounded_adaptation_evidence() -> None:
    first_partial = next((FIRST_RESULTS / "run" / "attempts").glob("*/partial-attempt.json"))
    partial = json.loads(first_partial.read_text())
    assert partial["first_exhausted_cap"] == "wall"
    assert partial["completed_shot_credit"] == 0
    assert partial["failure_credit"] == 0
    assert partial["overshoot_ns"] > 0
    study = json.loads(STUDY_V2.read_text())
    assert study["calibration_partial_receipt_sha256"] == sha256(first_partial.read_bytes()).hexdigest()
    assert study["campaign_document"]["failure_count_work_spec"]["policy"]["target_failures"] == 100
    assert study["campaign_document"]["failure_count_work_spec"]["policy"]["batch_size"] >= 1
    assert study["publication_slurm_authorization"] == "deny"
    for version in ("v2", "v3"):
        failed_root = ROOT / f"data/results/phase9-yao-b1-t001-p010-{version}/run/attempts"
        failed_ledger = next(failed_root.glob("*/events.jsonl"))
        assert not any(json.loads(line)["kind"] == "termination" for line in failed_ledger.read_text().splitlines())
        assert not list(failed_root.glob("*/attempt.json"))
    plan = FIRST_RESULTS / "plan" / "failure-count-plan.json"
    merge = FIRST_RESULTS / "merge" / "failure-count-merge.json"
    checked = subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", "verify", "--plan", str(plan),
         "--merge", str(merge), "--receipt", str(first_partial),
         "--campaign-root", str(ROOT)], cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert checked.returncode == 0, checked.stdout
    assert json.loads(checked.stdout)["campaign_state"] == "progress"
    assert json.loads(STUDY_V4.read_text())["calibration_failed_ledger_sha256"] == sha256(
        next((ROOT / "data/results/phase9-yao-b1-t001-p010-v3/run/attempts").glob("*/events.jsonl")).read_bytes()
    ).hexdigest()


def test_cap_censor_final_report_retains_two_shots_without_inference() -> None:
    from bp_registry.campaigns.contracts import canonical_json_bytes

    plan = RESULTS / "plan/failure-count-plan.json"
    root = RESULTS / "retry-run"
    merge = RESULTS / "merge/failure-count-merge.json"
    report_path = RESULTS / "assessment/failure-count-assessment.json"
    report = json.loads(report_path.read_bytes())
    terminal = json.loads((root / "failure-count-cap-censor.json").read_bytes())
    attempts = sorted((root / "attempts").glob("*/attempt.json"))
    assert len(attempts) == 2
    assert terminal["terminal_receipt"]["first_exhausted_cap"] == "wall"
    assert report["assessment_status"] == "inconclusive_cap_censored"
    assert report["terminal_state"] == "cap_censored"
    assert report["total_completed_shots"] == 2
    assert report["cumulative_failures"] == 2
    assert report["terminal_failure_ordinal"] is None
    assert report["inverse_binomial_rate"] is None
    assert report["target_decision"]["verdict"] == "inconclusive"
    assert report["actual_resources"]["wall_ns"] > 1_800_000_000_000
    assert report_path.read_bytes() == canonical_json_bytes(report) + b"\n"
    for attempt_path in attempts:
        attempt = json.loads(attempt_path.read_bytes())
        assert attempt["terminal_fact"]["outcome"] == "timeout"
        assert attempt["terminal_fact"]["termination"] == "wall_clock_deadline"
        assert attempt["attempt"]["state"] == "sealed_terminal"
    checked = subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", "verify", "--plan", str(plan),
         "--merge", str(merge), "--report", str(report_path), "--campaign-root", str(ROOT)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert checked.returncode == 0, checked.stdout
    assert json.loads(checked.stdout)["campaign_state"] == "cap_censored"
    assert json.loads(checked.stdout)["verified"] is True
