"""Public Phase 1 inspection commands must expose the pinned pilot contract."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def _run_cli(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "bp_registry.cli", *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    return json.loads(completed.stdout)


def test_researcher_can_inspect_the_pinned_pilot_from_documented_cli_commands():
    manifest = Path("data/manifests/selected-css-pilot_adaptation-not_assessed.json")
    output = Path("data/results/pilot_adaptation-not_assessed")

    preflight = _run_cli("preflight", str(manifest))
    verified = _run_cli("verify-run", str(output))

    assert preflight["run_id"] == "gross-bb144-pilot"
    assert preflight["code_id"] == "gross-bb-144"
    assert preflight["relation"] == "pilot_adaptation"
    assert preflight["assessment_status"] == "not_assessed"
    assert preflight["assessment_reason"]
    assert preflight["shot_budget"] == 32
    assert verified["run_id"] == preflight["run_id"]
    assert verified["final_row_count"] == preflight["shot_budget"]
