"""Native BP is a reference; syndrome fit is independently checked."""

import pytest


def test_native_bp_fits_tiny_syndrome():
    import numpy as np
    from bp_registry.reference import decode

    h = np.eye(2, dtype=np.uint8)
    syndrome = np.array([1, 0], dtype=np.uint8)
    result = decode(h, syndrome, error_rate=0.1, max_iter=10)
    assert np.array_equal((h @ result.candidate) % 2, syndrome)
    assert result.converged is True
    assert result.iterations >= 1


def test_legacy_fixture_cannot_create_execution_evidence(tmp_path):
    import json
    from bp_registry.runner import run_one

    manifest = {
        "schema_version": 1,
        "run_id": "fixture-smoke",
        "source_uri": "https://arxiv.org/abs/2312.10950",
        "source_revision": "v2",
        "source_anchor": "Figure 2",
        "code_id": "project-three-qubit-css-fixture",
        "experiment_relation": "pilot_adaptation",
        "expected_output_status": "not_assessed",
        "x_error_rate": 0.0,
        "seed": 12,
        "max_iter": 10,
        "bp_method": "product_sum",
        "schedule": "parallel",
        "input_vector_type": "syndrome",
    }
    manifest_path = tmp_path / "fixture.json"
    ledger_path = tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="read-only"):
        run_one(manifest_path, shot_id=3, ledger_path=ledger_path)
    assert not ledger_path.exists()


def test_runner_uses_sampling_and_independent_evaluator(tmp_path, monkeypatch):
    import json
    import numpy as np
    from pathlib import Path
    from bp_registry import runner

    assert hasattr(runner, "sampling"), "runner must call the sampling module"
    assert hasattr(runner, "evaluator"), "runner must call the evaluator module"
    from bp_registry.sampling import DecoderObservation, HiddenTruth, ShotSample
    from bp_registry.evaluator import Evaluation

    sentinel = ShotSample(
        shot_id=5, sample_identity="sentinel-sample", hidden=HiddenTruth(
            x=np.array([1, 0, 0], dtype=np.uint8), z=np.zeros(3, dtype=np.uint8)
        ), observation=DecoderObservation("Z", np.array([0], dtype=np.uint8)),
        observations={"Z": DecoderObservation("Z", np.array([0], dtype=np.uint8))},
    )
    monkeypatch.setattr(runner.sampling, "sample_shot", lambda *args, **kwargs: sentinel)
    monkeypatch.setattr(
        runner.evaluator, "evaluate_candidate",
        lambda *args, **kwargs: Evaluation("logical_failure", True),
    )
    monkeypatch.setattr(
        runner.reference, "decode",
        lambda *args, **kwargs: runner.reference.NativeResult(
            candidate=np.zeros(144, dtype=np.uint8), converged=True, iterations=1
        ),
    )
    manifest_path, ledger_path = (
        Path("data/manifests/selected-css-pilot_adaptation-not_assessed.json"),
        tmp_path / "events.jsonl",
    )
    result = runner.run_one(manifest_path, shot_id=5, ledger_path=ledger_path)
    terminal = [json.loads(line) for line in ledger_path.read_text().splitlines()][1]
    assert result.outcome == "logical_failure"
    assert terminal["sample_identity"] == "sentinel-sample"
    assert terminal["outcome"] == "logical_failure"


def test_selected_pilot_preflight_is_bound_and_transparent(tmp_path):
    """The public pilot path accepts only the Plan 08 selected artifact."""
    import json
    from pathlib import Path

    from bp_registry import runner

    manifest_path = Path("data/manifests/selected-css-pilot_adaptation-not_assessed.json")
    assert manifest_path.exists(), "the selected CSS pilot manifest must be checked in"

    report = runner.preflight_pilot(manifest_path)
    assert report["run_id"] == "gross-bb144-pilot"
    assert report["code_id"] == "gross-bb-144"
    assert report["relation"] == "pilot_adaptation"
    assert report["assessment_status"] == "not_assessed"
    assert report["assessment_reason"]
    assert report["paper_revision"] == "v1"
    assert report["implementation_revision"] == "fa77e3333d3ec44c79d8f914dd24c040d1da471b"
    assert report["paper_uri"].startswith("https://arxiv.org/")
    assert report["implementation_uri"].startswith("https://github.com/")
    assert "curve pass" not in json.dumps(report).lower()

    altered = json.loads(manifest_path.read_text())
    altered["implementation"]["revision"] = "not-the-pinned-source"
    invalid = tmp_path / "invalid-selected-pilot.json"
    invalid.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="selected artifact"):
        runner.preflight_pilot(invalid)
