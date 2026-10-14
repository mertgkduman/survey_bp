"""Public lifecycle regressions for the Phase 11 controlled GB46 calibration."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_installed_cli_exposes_phase11_controlled_lifecycle() -> None:
    """The public wrapper advertises every lifecycle operation before a run starts."""
    result = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "preflight" in result.stdout
    assert "run" in result.stdout
    assert "resume" in result.stdout
    assert "replay" in result.stdout
    assert "verify" in result.stdout
    assert "assess" in result.stdout


def test_bounded_public_lifecycle_evidence_integrity(tmp_path: Path) -> None:
    """The shipped wrapper seals complete matched pairs before assessment."""
    output = tmp_path / "phase11-controlled"
    run = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "run", "--output-root", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    assert '"complete_pairs": 6' in run.stdout

    for command in ("replay", "verify"):
        result = subprocess.run(
            [sys.executable, "scripts/run_phase11_controlled.py", command, "--output-root", str(output)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        assert '"publication_authorization": "deny"' in result.stdout

    pair = output / "pairs" / "lower_y" / "0.json"
    pair.write_text(pair.read_text(encoding="utf-8").replace('"joint"', '"tampered"', 1), encoding="utf-8")
    tampered = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "verify", "--output-root", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert tampered.returncode == 2
    assert "error" in tampered.stdout


def test_gb46_three_point_design_has_disjoint_calibration_ranges() -> None:
    """The public design preserves all three exact rows without a source lane."""
    from bp_registry.campaigns.controlled_execution import preflight_phase11_controlled_design

    receipt = preflight_phase11_controlled_design(
        root=ROOT, design_path=ROOT / "data/studies/phase11-gb46-joint-separate.json",
    )
    assert receipt["point_order"] == ["lower_y", "independence", "higher_y"]
    ranges = receipt["sample_ranges"]
    assert {item for lower, upper in ranges.values() for item in range(lower, upper + 1)} == set(range(6))
    assert receipt["publication_authorization"] == "deny"


def test_gb46_empty_shard_is_explicitly_incomplete(tmp_path: Path) -> None:
    """An empty valid shard cannot be silently turned into an assessment."""
    result = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "run", "--output-root", str(tmp_path / "empty"),
         "--shard", "lower_y:1:0"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"assessment_status": "incomplete_shard"' in result.stdout
