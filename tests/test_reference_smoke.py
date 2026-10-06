"""Native BP is a reference; syndrome fit is independently checked."""

import pytest


@pytest.mark.parametrize(
    "name",
    ("NativeBpOsdReference", "NativeBpLsdReference"),
)
def test_native_composite_reference_adapters_are_explicit(name):
    """Pinned native composites must retain identities distinct from canonical BP."""
    from bp_registry import reference

    assert hasattr(reference, name), f"{name} must be an explicit native reference adapter"


def test_native_bp_fits_tiny_syndrome():
    import numpy as np
    from bp_registry.reference import decode

    h = np.eye(2, dtype=np.uint8)
    syndrome = np.array([1, 0], dtype=np.uint8)
    result = decode(h, syndrome, error_rate=0.1, max_iter=10)
    assert np.array_equal((h @ result.candidate) % 2, syndrome)
    assert result.converged is True
    assert result.iterations >= 1


def test_native_metric_facts_qualify_public_sdk_observability():
    import numpy as np

    from bp_registry.reference import decode

    result = decode(
        np.eye(2, dtype=np.uint8), np.array([1, 0], dtype=np.uint8),
        error_rate=0.1, max_iter=10,
    )
    assert hasattr(result, "metric_facts"), "native results must expose typed metric facts"
    facts = {fact.metric: fact for fact in result.metric_facts}

    iterations = facts["native_iterations"]
    assert iterations.missingness.value == "observed"
    assert iterations.value == result.iterations
    assert iterations.method == "ldpc.BpDecoder.iter"
    assert iterations.scope == "native_decoder_call"
    assert iterations.unit == "native_iterations"

    edge_updates = facts["native_edge_updates"]
    assert edge_updates.missingness.value == "unavailable"
    assert edge_updates.value is None
    assert edge_updates.unavailable_reason == (
        "ldpc.BpDecoder does not expose edge-update counts"
    )
    assert result.edge_updates is None


def test_native_opaque_edge_work_cannot_be_claimed_as_observed_zero():
    import numpy as np

    from bp_registry.canonical.metrics import MetricFact, unavailable_metric
    from bp_registry.reference import NativeResult

    iteration = MetricFact.observed(
        "native_iterations", 1, method="ldpc.BpDecoder.iter",
        scope="native_decoder_call", unit="native_iterations",
        qualification="public_sdk_counter",
    )
    fabricated_edge_work = MetricFact.observed(
        "native_edge_updates", 0, method="ldpc.BpDecoder",
        scope="native_decoder_call", unit="edge_messages",
        qualification="fabricated",
    )
    opaque_control_flow = unavailable_metric(
        "native_control_flow_events", method="ldpc.BpDecoder",
        scope="native_decoder_call", unit="events",
        qualification="opaque_native_internal", reason="SDK does not expose events",
    )
    with pytest.raises(ValueError, match="unavailable"):
        NativeResult(
            candidate=np.zeros(2, dtype=np.uint8), converged=True, iterations=1,
            metric_facts=(iteration, fabricated_edge_work, opaque_control_flow),
        )


def test_metric_facts_reject_nonfinite_or_negative_observations_and_reasonless_missingness():
    from bp_registry.canonical.metrics import MetricFact, unavailable_metric

    kwargs = {
        "method": "test", "scope": "test_scope", "unit": "count",
        "qualification": "test_only",
    }
    with pytest.raises(ValueError, match="nonnegative"):
        MetricFact.observed("count", -1, **kwargs)
    with pytest.raises(ValueError, match="finite"):
        MetricFact.observed("count", float("inf"), **kwargs)
    with pytest.raises(ValueError, match="reason"):
        unavailable_metric("count", reason="", **kwargs)


def test_native_adapter_rejects_fractional_inputs_before_uint8_coercion():
    import numpy as np
    from bp_registry.reference import decode

    with pytest.raises(ValueError, match="dtype"):
        decode(np.array([[1.5, 0.0]]), np.array([0.0]), error_rate=0.1, max_iter=10)
    with pytest.raises(ValueError, match="dtype"):
        decode(np.array([[1, 0]], dtype=np.uint8), np.array([0.5]), error_rate=0.1, max_iter=10)


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


def test_checked_in_three_qubit_fixture_is_a_current_executable_manifest(tmp_path):
    """The documented project fixture must not silently fall back to legacy mode."""
    import json
    from pathlib import Path

    from bp_registry.manifests import ManifestV1, parse_manifest
    from bp_registry.runner import run_one

    manifest_path = Path("data/manifests/project-three-qubit-fixture.json")
    manifest = parse_manifest(manifest_path)
    assert isinstance(manifest, ManifestV1)
    assert manifest.artifact.code_id == "project-three-qubit-css-fixture"
    assert manifest.paper.relation == "pilot_adaptation"
    assert manifest.expected_output.status == "not_assessed"

    ledger_path = tmp_path / "fixture-events.jsonl"
    result = run_one(manifest_path, shot_id=0, ledger_path=ledger_path)
    events = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert result.run_id == manifest.run_id
    assert [event["kind"] for event in events] == ["begin", "terminal"]
    assert events[1]["manifest_sha256"]
    assert events[1]["code_id"] == "project-three-qubit-css-fixture"
    facts = {fact["metric"]: fact for fact in events[1]["native_metric_facts"]}
    assert facts["native_iterations"]["value"] == result.iterations
    assert facts["native_edge_updates"]["value"] is None
    assert facts["native_edge_updates"]["unavailable_reason"]


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
    from bp_registry.cli import _result_from_final_rows
    from bp_registry.ledger import reconcile

    result_payload = _result_from_final_rows(manifest_path, tmp_path, reconcile(ledger_path), 0.0)
    assert result_payload["native_metric_availability"]["native_iterations"] == {
        "observed": 1, "unavailable": 0,
    }
    assert result_payload["native_metric_availability"]["native_edge_updates"] == {
        "observed": 0, "unavailable": 1,
    }


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
