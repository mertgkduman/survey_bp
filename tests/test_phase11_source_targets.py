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
    with pytest.raises(ValueError, match="digest|frozen"):
        QuaternarySourceTargetV1.model_validate(changed)


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
