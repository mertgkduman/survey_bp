"""Regression coverage for Phase 11 source-assessment claim boundaries."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "scripts/run_phase11_source_studies.py"
ASCED_TARGET = ROOT / "data/source-targets/phase11-asced-figure2-gb46.json"
ASCED_MANIFEST = ROOT / "data/manifests/phase11-asced-figure2-gb46.json"
NATIVE_QUALIFICATION = ROOT / "data/native/phase11-asced-matched-input-qualification.json"
AUTHORIZATION = ROOT / "data/results/phase11-production-authorization.json"
QBPGD_TARGET = ROOT / "data/source-targets/phase11-qbpgd-figure7-a5.json"
QBPGD_MANIFEST = ROOT / "data/manifests/phase11-qbpgd-figure7-a5.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STUDY), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_asced_ordinary_and_overcomplete_denied_assessment_keeps_unavailable_native_fidelity_separate(tmp_path: Path) -> None:
    """A denied source lane cannot erase the independently unavailable native gap."""
    assessment_path = tmp_path / "assessment.json"
    result = _run(
        "preflight",
        "--target", str(ASCED_TARGET),
        "--manifest", str(ASCED_MANIFEST),
        "--native-qualification", str(NATIVE_QUALIFICATION),
        "--authorization", str(AUTHORIZATION),
        "--assessment", str(assessment_path),
    )
    assert result.returncode == 0, result.stderr

    assessment = _json(assessment_path)
    assert assessment["admitted_shots"] == 0
    assert assessment["run_fidelity"] == "canonical_adaptation"
    assert assessment["source_fidelity"] == "not_promoted"
    assert assessment["authorization"]["decision"] == "deny"
    assert assessment["authorization"]["dispatch_attempted"] is False

    members = {member["member_id"]: member for member in assessment["members"]}
    assert set(members) == {
        "asced-figure2-gb46-ordinary",
        "asced-figure2-gb46-overcomplete",
    }
    for member in members.values():
        canonical = member["canonical_adaptation"]
        native = member["matched_native"]
        assert canonical["eligibility"] == "blocked"
        assert canonical["dispatch_attempted"] is False
        assert "digitized_clicks_unavailable" in canonical["failed_gates"]
        assert native["eligibility"] == "unavailable"
        assert native["terminal"] == "declined_unavailable"
        assert native["source_fidelity_claim"] == "none"
        assert native["paired_values"] is None


def test_qbpgd_a5_denied_setting_gap_adaptation_stopping_assessment_keeps_discrepancy(tmp_path: Path) -> None:
    """Deny must suppress even the bounded probe while retaining source gaps."""
    assessment_path = tmp_path / "assessment.json"
    result = _run(
        "run",
        "--target", str(QBPGD_TARGET),
        "--manifest", str(QBPGD_MANIFEST),
        "--authorization", str(AUTHORIZATION),
        "--assessment", str(assessment_path),
    )
    assert result.returncode == 0, result.stderr

    assessment = _json(assessment_path)
    assert assessment["status"] == "inconclusive"
    assert assessment["admitted_shots"] == 0
    assert assessment["run_fidelity"] == "canonical_adaptation"
    assert assessment["source_fidelity"] == "not_promoted"
    assert assessment["authorization"]["decision"] == "deny"
    assert assessment["authorization"]["dispatch_attempted"] is False
    assert assessment["source_stopping"] == {
        "error_cases": 100,
        "denominator": "trials_until_100_error_cases",
    }
    assert "continued_message_lifecycle_unresolved" in assessment["qualification_blockers"]
    assert assessment["discrepancy"] == "not_assessed_due_to_unresolved_figure_coordinates_and_author_identity"
    assert "qualification" not in assessment
