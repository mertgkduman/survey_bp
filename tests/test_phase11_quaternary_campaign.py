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
