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


def test_one_bounded_public_lifecycle_pair_set_replays_and_rejects_tampering(tmp_path: Path) -> None:
    """The shipped wrapper seals complete matched pairs before assessment."""
    output = tmp_path / "phase11-controlled"
    run = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "run", "--output-root", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    assert '"complete_pairs": 6' in run.stdout

    for command in ("resume", "replay", "verify", "assess"):
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
