"""Native BP is a reference; syndrome fit is independently checked."""


def test_native_bp_fits_tiny_syndrome():
    import numpy as np
    from bp_registry.reference import decode

    h = np.eye(2, dtype=np.uint8)
    syndrome = np.array([1, 0], dtype=np.uint8)
    result = decode(h, syndrome, error_rate=0.1, max_iter=10)
    assert np.array_equal((h @ result.candidate) % 2, syndrome)
    assert result.converged is True
    assert result.iterations >= 1


def test_fixture_shot_links_manifest_source_and_terminal(tmp_path):
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
    result = run_one(manifest_path, shot_id=3, ledger_path=ledger_path)
    events = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert len(events) == 2
    assert events[0]["kind"] == "begin"
    assert events[1]["kind"] == "terminal"
    assert events[1]["run_id"] == manifest["run_id"]
    assert events[1]["shot_id"] == 3
    assert events[1]["source_revision"] == "v2"
    assert events[1]["experiment_relation"] == "pilot_adaptation"
    assert events[1]["expected_output_status"] == "not_assessed"
    assert events[1]["outcome"] == result.outcome
    assert isinstance(events[1]["native_converged"], bool)
    assert isinstance(events[1]["native_iterations"], int)
    assert events[1]["native_edge_updates"] is None
    assert events[1]["native_edge_updates_missing_reason"]
    assert events[1]["postselection"] == "none"


def test_runner_uses_sampling_and_independent_evaluator(tmp_path, monkeypatch):
    import json
    import numpy as np
    from bp_registry import runner

    assert hasattr(runner, "sampling"), "runner must call the sampling module"
    assert hasattr(runner, "evaluator"), "runner must call the evaluator module"
    from bp_registry.sampling import DecoderObservation, HiddenTruth, ShotSample
    from bp_registry.evaluator import Evaluation

    manifest = {
        "schema_version": 1, "run_id": "sentinel-smoke",
        "source_uri": "https://arxiv.org/abs/2312.10950", "source_revision": "v2",
        "source_anchor": "Figure 2", "code_id": "project-three-qubit-css-fixture",
        "experiment_relation": "pilot_adaptation", "expected_output_status": "not_assessed",
        "x_error_rate": 0.0, "seed": 12, "max_iter": 10, "bp_method": "product_sum",
        "schedule": "parallel", "input_vector_type": "syndrome",
    }
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
    manifest_path, ledger_path = tmp_path / "fixture.json", tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(manifest))
    result = runner.run_one(manifest_path, shot_id=5, ledger_path=ledger_path)
    terminal = [json.loads(line) for line in ledger_path.read_text().splitlines()][1]
    assert result.outcome == "logical_failure"
    assert terminal["sample_identity"] == "sentinel-sample"
    assert terminal["outcome"] == "logical_failure"
