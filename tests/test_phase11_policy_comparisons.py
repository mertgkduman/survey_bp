"""Bounded, receipt-first Phase 11 policy-comparison regressions."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_phase11_policy_comparisons.py"


def _api():
    import importlib.util

    spec = importlib.util.spec_from_file_location("phase11_policy_comparisons", SCRIPT)
    assert spec and spec.loader, "policy comparison runner must be importable"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tracer_mbp4_one_change_contract_and_replay(tmp_path: Path) -> None:
    """The first policy tracer changes only a qualified MBP4 recurrence."""
    module = _api()
    study = module.load_policy_study(ROOT)
    tracer = next(item for item in study["comparisons"] if item["comparison_id"] == "gb46-mbp4-alpha")
    assert tracer["anchors"] == ["independence"]
    assert tracer["declared_changed_field"] == "recurrence"
    assert tracer["baseline"]["schedule"] == tracer["variant"]["schedule"]
    assert tracer["baseline"]["initialization"] == tracer["variant"]["initialization"]
    assert tracer["baseline"]["stopping"] == tracer["variant"]["stopping"]
    assert tracer["variant"]["recurrence"] == "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18"
    result = module.run_policy_comparisons(ROOT, tmp_path)
    assert result["status"] == "verified"
    assert result["comparison_count"] == 1
    verification = module.verify_policy_comparisons(ROOT, tmp_path)
    assert verification["replayed_records"] == 1
    record = json.loads((tmp_path / "records" / "gb46-mbp4-alpha" / "independence.json").read_text())
    assert record["sample_identity"] == record["baseline"]["sample_identity"] == record["variant"]["sample_identity"]
    assert record["baseline"]["terminal"] and record["variant"]["terminal"]
    assert record["baseline"]["work"] and record["variant"]["work"]
    assert record["baseline"]["runtime_ns"] >= 0 and record["variant"]["runtime_ns"] >= 0


def test_unsupported_or_multi_change_policy_is_rejected_before_output(tmp_path: Path) -> None:
    module = _api()
    study = module.load_policy_study(ROOT)
    bad = json.loads(json.dumps(study))
    comparison = bad["comparisons"][0]
    comparison["variant"]["alpha"] = 0.0
    with pytest.raises(ValueError, match="alpha"):
        module.validate_policy_study(ROOT, bad)
    bad = json.loads(json.dumps(study))
    bad["comparisons"][0]["variant"]["schedule"] = "qbp_variable_serial"
    with pytest.raises(ValueError, match="exactly one"):
        module.validate_policy_study(ROOT, bad)
    assert not list(tmp_path.rglob("*.json"))


def test_independence_cli_runs_and_replays_bounded_tracer(tmp_path: Path) -> None:
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--output-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    replay = subprocess.run(
        [sys.executable, str(SCRIPT), "replay", "--output-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)["replayed_records"] == 1
