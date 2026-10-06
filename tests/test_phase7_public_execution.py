"""Focused public contracts for the Phase 7 standalone-LSD tracer."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


def _original():
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.canonical.problems import OriginalProblem, WorkingProblem

    original = OriginalProblem(
        lineage_id="original-phase7",
        hx=np.asarray([[1, 1, 0, 1]], dtype=np.uint8),
        hz=np.asarray([[1, 1, 0, 1], [1, 0, 0, 0]], dtype=np.uint8),
        syndrome=np.asarray([1, 0], dtype=np.uint8),
    )
    working = WorkingProblem(
        lineage_id="working-phase7", original=original,
        parent_edge=LineageEdge("identity", LineageId("original", original.lineage_id),
                               LineageId("working", "working-phase7")),
    )
    return original, working


def _failed_snapshot(*, reliability=(1.0, -2.0, 3.0, -4.0)):
    from bp_registry.canonical.postprocessing import FailedAttemptSnapshot

    original, working = _original()
    return FailedAttemptSnapshot(
        attempt_lineage_id="attempt-1", working=working,
        candidate=np.zeros(4, dtype=np.uint8),
        posterior_llr=np.asarray(reliability, dtype=np.float64),
        original_residual_weight=1, original_channel_nll=2.0,
        declared_attempt_ordinal=0,
    )


def test_reliability_snapshot_is_frozen_and_rejects_unusable_values():
    from bp_registry.canonical.postprocessing import FailedAttemptSnapshot

    snapshot = _failed_snapshot()
    assert snapshot.posterior_llr.flags.writeable is False
    assert snapshot.reliability_convention == "natural_log_odds_log_p0_over_p1"
    for bad in ((1.0, np.nan, 3.0, 4.0), (1.0, 2.0), (1.0, np.inf, 3.0, 4.0)):
        with pytest.raises(ValueError):
            _failed_snapshot(reliability=bad)


def test_closed_controller_calls_lsd_once_only_after_whole_composition_failure():
    from bp_registry.canonical.postprocessing import LsdPostprocessor, PostprocessingController

    controller = PostprocessingController(LsdPostprocessor(method="LSD_0", order=0))
    skipped = controller.execute((), bp_succeeded=False)
    assert skipped.status == "not_triggered_no_failed_snapshot"
    assert skipped.native_calls == 0
    success = controller.execute((_failed_snapshot(),), bp_succeeded=True)
    assert success.status == "not_triggered_bp_success"
    assert success.native_calls == 0
    result = controller.execute((_failed_snapshot(),), bp_succeeded=False)
    assert result.native_calls == 1
    assert result.selected_attempt_lineage_id == "attempt-1"
    assert result.bp_only_candidate == (0, 0, 0, 0)
    assert result.status in {"success", "invalid_candidate", "native_failure"}


def test_released_interface_uses_magnitude_llr_and_original_validation(monkeypatch):
    from bp_registry.canonical.postprocessing import LsdPostprocessor

    seen = {}

    class FakeLsdDecoder:
        def __init__(self, matrix, **kwargs):
            seen["matrix"] = np.asarray(matrix).copy()
            seen["kwargs"] = kwargs

        def decode(self, syndrome, weights):
            seen["syndrome"] = np.asarray(syndrome).copy()
            seen["weights"] = np.asarray(weights).copy()
            return np.asarray([0, 1, 0, 0], dtype=np.uint8)

    monkeypatch.setattr("bp_registry.canonical.postprocessing._load_lsd_decoder", lambda: FakeLsdDecoder)
    outcome = LsdPostprocessor(method="LSD_0", order=0).run(_failed_snapshot())
    assert np.array_equal(seen["weights"], [1.0, 2.0, 3.0, 4.0])
    assert seen["kwargs"]["bits_per_step"] == 1
    assert outcome.original_valid is True
    assert outcome.candidate == (0, 1, 0, 0)


def test_phase7_preflight_admits_only_disabled_or_qualified_lsd_binding(tmp_path):
    from bp_registry.manifests import CanonicalExperimentV8, preflight

    root = Path(__file__).resolve().parents[1]
    value = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    value.update({"schema_version": 8, "run_id": "phase7-preflight"})
    value["postprocessing_config"] = {
        "enabled": True, "method": "LSD_0", "order": 0,
        "source_status": "controlled_adaptation",
        "reliability_convention": "natural_log_odds_log_p0_over_p1",
    }
    path = tmp_path / "phase7.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    resolved = preflight(path)
    assert isinstance(resolved.manifest, CanonicalExperimentV8)
    assert resolved.manifest.postprocessing_config.method == "LSD_0"
    value["postprocessing_config"]["method"] = "arbitrary_import"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        preflight(path)


def test_tracer_installed_cli_runs_lsd_route_and_independently_replays(tmp_path):
    root = Path(__file__).resolve().parents[1]
    value = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    value.update({"schema_version": 8, "run_id": "phase7-installed-cli", "error_rate": 0.49})
    value["budgets"]["max_shots"] = 1
    value["budgets"]["attempt"]["max_iterations"] = 1
    value["postprocessing_config"] = {"enabled": True, "method": "LSD_0", "order": 0,
                                        "source_status": "controlled_adaptation",
                                        "reliability_convention": "natural_log_odds_log_p0_over_p1"}
    manifest = tmp_path / "phase7.json"
    output = tmp_path / "output"
    manifest.write_text(json.dumps(value), encoding="utf-8")
    for command in (("preflight", str(manifest)), ("canonical", str(manifest), "--output", str(output)), ("verify-run", str(output))):
        subprocess.run([sys.executable, "-m", "bp_registry.cli", *command], cwd=root, check=True, text=True, capture_output=True)
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert [event["kind"] for event in events] == ["shot_begin", "attempt", "bp_only", "fallback", "final", "work", "termination"]
