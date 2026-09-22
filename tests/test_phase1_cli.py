"""Public Phase 1 inspection commands must expose the pinned pilot contract."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


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


def test_public_pilot_counts_reconciled_interruption(tmp_path):
    from bp_registry.cli import run_pilot, verify_run

    manifest = Path("data/manifests/selected-css-pilot_adaptation-not_assessed.json")
    source = Path("data/results/pilot_adaptation-not_assessed/events.jsonl")
    output = tmp_path / "pilot"
    output.mkdir()
    events = [json.loads(line) for line in source.read_text().splitlines()]
    # Simulate an owner dying after its durable begin, before its terminal.
    events = [event for event in events if not (
        event["shot_id"] == 0 and event["kind"] == "terminal"
    )]
    (output / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))

    assert run_pilot(manifest, output)["final_row_count"] == 32
    assert verify_run(output)["final_row_count"] == 32
    result = json.loads((output / "result.json").read_text())
    assert result["denominators"]["all_terminal_shots"] == 32
    assert result["denominators"]["interrupted"] == 1
    assert result["denominators"]["outcome_unavailable"] == 1

    ledger = output / "events.jsonl"
    original = [json.loads(line) for line in ledger.read_text().splitlines()]
    for field, value in (
        ("native_iterations", 8), ("native_edge_updates", 144),
        ("candidate", [0] * 144), ("syndrome", [0] * 72),
        ("hidden_x", [0] * 144), ("selection_status", "native_bp_candidate"),
    ):
        tampered = [dict(event) for event in original]
        terminal = next(event for event in tampered if event["shot_id"] == 0 and event["kind"] == "terminal")
        terminal[field] = value
        ledger.write_text("".join(json.dumps(event) + "\n" for event in tampered))
        with pytest.raises(ValueError, match="unavailable|reconciliation"):
            verify_run(output)
    ledger.write_text("".join(json.dumps(event) + "\n" for event in original))


def test_public_pilot_counts_recorded_native_exception(tmp_path, monkeypatch):
    from bp_registry import reference, runner
    from bp_registry.cli import run_pilot, verify_run

    manifest = Path("data/manifests/selected-css-pilot_adaptation-not_assessed.json")
    source = Path("data/results/pilot_adaptation-not_assessed/events.jsonl")
    output = tmp_path / "pilot"
    output.mkdir()
    events = [json.loads(line) for line in source.read_text().splitlines()]
    (output / "events.jsonl").write_text("".join(
        json.dumps(event) + "\n" for event in events if event["shot_id"] != 0
    ))

    def unavailable_decoder(*_args, **_kwargs):
        raise RuntimeError("native decoder unavailable")

    monkeypatch.setattr(reference, "decode", unavailable_decoder)
    with pytest.raises(RuntimeError, match="native decoder unavailable"):
        runner.run_one(manifest, shot_id=0, ledger_path=output / "events.jsonl")

    assert run_pilot(manifest, output)["final_row_count"] == 32
    assert verify_run(output)["final_row_count"] == 32
    result = json.loads((output / "result.json").read_text())
    assert result["denominators"]["all_terminal_shots"] == 32
    assert result["denominators"]["outcome_unavailable"] == 1
    assert result["terminations"]["exception"] == 1
