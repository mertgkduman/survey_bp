"""Regression coverage for the frozen aSCED Figure 2 source lane."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/source-targets/phase11-asced-figure2-gb46.json"
MANIFEST = ROOT / "data/manifests/phase11-asced-figure2-gb46.json"
ASSESSMENT = ROOT / "data/results/phase11-asced-figure2/assessment.json"
SCRIPT = ROOT / "scripts/run_phase11_source_studies.py"
REVIEW_SCRIPT = ROOT / "scripts/review_phase11_asced_figure2.py"
REVIEW = ROOT / "data/source-targets/phase11-asced-figure2-review.json"


def _run_review(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REVIEW_SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_asced_figure2_review_candidate_covers_every_selected_curve_point_and_stays_non_authorizing():
    """The pending human review must see all 32 selected Figure 2 points."""
    completed = _run_review("prepare", "--review", str(REVIEW))
    assert completed.returncode == 0, completed.stderr

    payload = _json(REVIEW)
    assert _run_review("verify-candidate", "--review", str(REVIEW)).returncode == 0
    assert payload["schema"] == "phase11_asced_figure2_review_v1"
    assert payload["execution_authorized"] is False
    assert payload["review_state"] == "pending_human_review"
    assert payload["candidate_sha256"]

    members = {member["member_id"]: member for member in payload["members"]}
    assert set(members) == {
        "asced-figure2-gb46-ordinary",
        "asced-figure2-gb46-overcomplete",
    }
    assert {member["construction"] for member in members.values()} == {"ordinary", "overcomplete"}
    for member in members.values():
        assert len(member["curves"]) == 2
        assert all(len(curve["points"]) == 8 for curve in member["curves"])
        for curve in member["curves"]:
            assert [point["point_id"] for point in curve["points"]] == [
                "p003", "p004", "p005", "p006", "p007", "p008", "p009", "p010",
            ]
            for point in curve["points"]:
                assert set(point["evidence_fields"]) == {
                    "axis_calibration_anchors", "digitization_uncertainty", "extraction_tool_operator",
                    "raw_click_coordinates", "tolerance", "transformed_coordinate_interval",
                }
                assert all(field["status"] == "blocked" for field in point["evidence_fields"].values())

    assert payload["source_snapshot"]["sha256"] == "0eec129dde3026f8225ec7d5f2884dbefe37566c9f71d105cae0195e4e4abca5"
    assert payload["source_crop"]["sha256"]
    assert payload["native_route"]["terminal"] == "declined_unavailable"
    assert payload["resource_bound"]["source_shots_admitted"] == 0


def test_asced_figure2_review_candidate_rejects_tampered_blocker_or_authorization(tmp_path: Path):
    review = tmp_path / "review.json"
    prepared = _run_review("prepare", "--review", str(review))
    assert prepared.returncode == 0, prepared.stderr

    altered = _json(review)
    altered["members"][0]["curves"][0]["points"][0]["evidence_fields"]["tolerance"] = {
        "status": "resolved",
        "value": 0.01,
    }
    review.write_text(json.dumps(altered, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tampered = _run_review("verify-candidate", "--review", str(review))
    assert tampered.returncode != 0
    assert "candidate differs" in tampered.stderr

    prepared = _run_review("prepare", "--review", str(review))
    assert prepared.returncode == 0, prepared.stderr
    altered = _json(review)
    altered["execution_authorized"] = True
    review.write_text(json.dumps(altered, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    authorizing = _run_review("verify-candidate", "--review", str(review))
    assert authorizing.returncode != 0
    assert "candidate differs" in authorizing.stderr


def test_asced_tracer_ordinary_target_is_exactly_gb46_figure2_and_blocked_before_sampling():
    assert TARGET.is_file(), "the frozen Figure 2 GB46 target receipt must exist"
    payload = _json(TARGET)
    ordinary = next(member for member in payload["members"] if member["member_id"] == "asced-figure2-gb46-ordinary")

    assert payload["schema"] == "campaign_quaternary_source_target_v1"
    assert payload["source_panel"] == {"figure": "Figure 2", "code": "GB46"}
    assert ordinary["decoder"] == {
        "baseline": "BP4",
        "variant": "BP4-aSCED",
        "iterations": 25,
        "K": 16,
        "Delta": 2,
        "L": 4,
    }
    assert ordinary["channel"] == "depolarizing"
    assert ordinary["stopping"] == {"minimum_logical_errors": 400, "maximum_trials": 1_000_000}
    assert ordinary["eligibility"] == "blocked_metadata"
    assert ordinary["admitted_shots"] == 0
    assert "digitized_clicks_unavailable" in ordinary["blockers"]


def test_asced_source_target_model_rejects_demo_substitution_and_post_freeze_mutation():
    from bp_registry.campaigns.targets import QuaternarySourceTargetV1

    payload = _json(TARGET)
    parsed = QuaternarySourceTargetV1.model_validate(payload)
    assert parsed.digest() == payload["target_receipt_sha256"]

    demo = copy.deepcopy(payload)
    demo["members"][0]["evidence_kind"] = "demo_configuration"
    with pytest.raises(ValueError, match="demo"):
        QuaternarySourceTargetV1.model_validate(demo)

    changed = copy.deepcopy(payload)
    changed["members"][0]["decoder"]["K"] = 15
    with pytest.raises(ValueError, match="digest|freeze"):
        QuaternarySourceTargetV1.model_validate(changed)


def test_asced_overcomplete_member_is_separate_and_freezes_obp4_settings_and_manifest_binding():
    payload = _json(TARGET)
    members = {member["member_id"]: member for member in payload["members"]}
    ordinary = members["asced-figure2-gb46-ordinary"]
    assert "asced-figure2-gb46-overcomplete" in members
    overcomplete = members["asced-figure2-gb46-overcomplete"]

    assert set(members) == {"asced-figure2-gb46-ordinary", "asced-figure2-gb46-overcomplete"}
    assert ordinary["target_slot"] != overcomplete["target_slot"]
    assert overcomplete["decoder"] == {
        "baseline": "OBP4",
        "variant": "OBP4-aSCED",
        "iterations": 12,
        "p0": 0.3,
        "K": 16,
        "Delta": 2,
        "L": 4,
    }
    assert overcomplete["extraction"]["status"] == "blocked_metadata"
    assert overcomplete["eligibility"] == "blocked_metadata"
    assert overcomplete["admitted_shots"] == 0

    manifest = _json(MANIFEST)
    assert manifest["target_document_sha256"] == hashlib.sha256(TARGET.read_bytes()).hexdigest()
    assert manifest["target_receipt_sha256"] == payload["target_receipt_sha256"]
    assert manifest["source_only"] is True
    assert manifest["controlled_comparison"] is False


def test_asced_preflight_writes_only_deterministic_blocked_assessment_before_sampling():
    process = _run("preflight", "--target", str(TARGET), "--assessment", str(ASSESSMENT))
    assert process.returncode == 0, process.stderr

    target_bytes = TARGET.read_bytes()
    assessment = _json(ASSESSMENT)
    assert assessment["target_document_sha256"] == hashlib.sha256(target_bytes).hexdigest()
    assert assessment["status"] == "blocked_metadata"
    assert assessment["admitted_shots"] == 0
    assert assessment["target_receipt_sha256"] == _json(TARGET)["target_receipt_sha256"]
    assert assessment["run_fidelity"] == "canonical_adaptation"
    assert assessment["source_fidelity"] == "not_promoted"
    blocked_run = _run("run", "--target", str(TARGET), "--assessment", str(ASSESSMENT))
    assert blocked_run.returncode != 0
    assert "blocked_metadata" in blocked_run.stderr


def test_asced_assessment_detects_target_digest_drift_and_never_opens_sampling_for_blocked_receipt(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_bytes(TARGET.read_bytes())
    assessment = tmp_path / "assessment.json"

    assert _run("preflight", "--target", str(target), "--assessment", str(assessment)).returncode == 0
    altered = _json(target)
    altered["members"][0]["blockers"].append("tampered_after_preflight")
    target.write_text(json.dumps(altered, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    verify = _run("verify", "--target", str(target), "--assessment", str(assessment))
    assert verify.returncode != 0
    assert "digest" in verify.stderr.lower()
    run = _run("run", "--target", str(target), "--assessment", str(assessment))
    assert run.returncode != 0
    assert "digest" in run.stderr.lower()
