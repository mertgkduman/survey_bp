"""Public contract for the Phase 10 joint-Pauli tracer."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from bp_registry.manifests import QuaternaryExperimentV1, parse_manifest, preflight
from bp_registry.quaternary.execution import PauliValue, TracerPauliProblem, run_quaternary_tracer, syndrome_for, verify_quaternary_tracer
from bp_registry.runner import preflight_quaternary, run_quaternary, verify_quaternary_run


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "data/manifests/quaternary-five-qubit-tracer.json"


def test_tracer_public_facade_exists():
    """The installed package must expose a dedicated joint-Pauli tracer."""
    root = Path(__file__).resolve().parents[3]
    assert (root / "src/bp_registry/quaternary/execution.py").is_file()


def manifest_value() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_tracer_non_css_installed_cli_path_preflights_runs_and_replays(tmp_path):
    report = preflight_quaternary(FIXTURE)
    assert report["pauli_encoding"] == "I=0,X=1,Y=2,Z=3"
    result = run_quaternary(FIXTURE, tmp_path)
    assert result["assessment_status"] == "not_assessed"
    assert "performance result" in result["statistical_claim"]
    assert verify_quaternary_run(tmp_path)["verified"] is True


def test_tracer_preserves_non_css_original_checks_and_joint_y_syndrome(tmp_path):
    manifest = parse_manifest(FIXTURE)
    assert isinstance(manifest, QuaternaryExperimentV1)
    problem = TracerPauliProblem(manifest.problem.checks, manifest.problem.syndrome)
    candidate = [PauliValue.I, PauliValue.I, PauliValue.I, PauliValue.Y, PauliValue.I]
    assert syndrome_for(problem, candidate).tolist() == [1, 1, 1, 1]
    before = problem.checks.tobytes(), problem.syndrome.tobytes()
    run_quaternary_tracer(manifest, tmp_path)
    assert (problem.checks.tobytes(), problem.syndrome.tobytes()) == before
    assert not problem.checks.flags.writeable and not problem.syndrome.flags.writeable


def test_tracer_kernel_is_truth_sealed_and_records_smoothing_separately(tmp_path):
    from bp_registry.quaternary import execution

    assert "hidden" not in inspect.signature(execution._decode).parameters
    run_quaternary_tracer(parse_manifest(FIXTURE), tmp_path)
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert events[1]["data"]["hidden_truth_sealed"] is True
    assert events[2]["data"]["decoder_smoothing"] == pytest.approx(1e-12)
    assert events[1]["data"]["sampling"] == "one_categorical_I_X_Y_Z_value_per_qubit"


@pytest.mark.parametrize("field,value", [
    ("problem", None),
    ("channel", None),
])
def test_tracer_rejects_null_public_inputs(field, value):
    data = manifest_value(); data[field] = value
    with pytest.raises(Exception):
        parse_manifest(data)


def test_tracer_rejects_empty_invalid_and_mismatched_public_inputs():
    data = manifest_value(); data["problem"]["checks"] = []
    with pytest.raises(Exception, match="at least|nonempty"):
        parse_manifest(data)
    data = manifest_value(); data["problem"]["checks"][0][0] = 4
    with pytest.raises(Exception, match="I=0"):
        parse_manifest(data)
    data = manifest_value(); data["problem"]["syndrome"] = [0]
    with pytest.raises(Exception, match="syndrome"):
        parse_manifest(data)


def test_tracer_admits_one_qubit_explicit_encoding(tmp_path):
    data = manifest_value()
    data.update(run_id="one-qubit-qbp", problem={"checks": [[int(PauliValue.Z)]], "syndrome": [0]}, channel={"probabilities": [[1.0, 0.0, 0.0, 0.0]], "decoder_smoothing": 1e-12})
    manifest = parse_manifest(data)
    assert isinstance(manifest, QuaternaryExperimentV1)
    result = run_quaternary_tracer(manifest, tmp_path)
    assert result.candidate.tolist() == [PauliValue.I]


def test_tracer_replay_rejects_semantic_tampering(tmp_path):
    manifest = parse_manifest(FIXTURE)
    run_quaternary_tracer(manifest, tmp_path)
    path = tmp_path / "events.jsonl"
    path.write_text(path.read_text().replace('"not_assessed"', '"assessed"', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        verify_quaternary_tracer(manifest, tmp_path)
