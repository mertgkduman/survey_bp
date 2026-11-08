"""Public contract counterexamples from canonical audit E03/E01/E02."""
from dataclasses import replace

import numpy as np
import pytest
import stim

from bp_registry.batch_records import encode_records
from bp_registry.canonical.numerics import NumericalFailure
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder
from bp_registry.circuit.policies import CircuitBatchResult


def decoder(**kwargs):
    return PolicyBpSinterDecoder(CircuitPolicy(**kwargs)).compile_decoder_for_dem(
        dem=stim.DetectorErrorModel("error(0.1) D0 L0"))


@pytest.mark.parametrize("field,key,value", [
    ("faults", "faults", np.array([[256]])),
    ("predictions", "prediction", np.array([[-1]])),
    ("predictions", "prediction", np.array([[256]])),
    ("faults", "faults", np.array([[.5]])),
    ("converged", "converged", np.array([2])),
    ("iterations", "iterations", np.array([1.5])),
    ("iterations", "iterations", np.array([-1])),
    ("iterations", "iterations", np.array([2**63], dtype=np.uint64)),
    ("iterations", "iterations", np.array([True])),
    ("faults", "faults", np.array([0])),
    ("converged", "converged", np.array([[True]])),
    ("iterations", "iterations", np.array([[0]])),
])
@pytest.mark.parametrize("construct", ["direct", "replace"])
def test_result_rejects_invalid_execution_values_before_conversion(field, key, value, construct):
    result = decoder().decode_detailed(np.array([[0]], np.uint8))
    records = result.ledger
    records[1][key] = value.tolist()[0]
    changes = {field: value, "ledger_json": encode_records(records)}
    with pytest.raises(ValueError, match="circuit result"):
        if construct == "replace":
            replace(result, **changes)
        else:
            CircuitBatchResult(**{**vars(result), **changes})


def test_result_rejects_scalar_column_as_value_error():
    result = decoder().decode_detailed(np.array([[0]], np.uint8))
    with pytest.raises(ValueError, match="circuit result"):
        replace(result, iterations=np.array(0))


def test_result_lossless_normalization_owns_arrays_and_replays(tmp_path):
    compiled = decoder()
    result = compiled.decode_detailed(np.array([[0], [1]], np.uint8))
    faults = result.faults.astype(np.int16)
    predictions = result.predictions.astype(bool)
    normalized = replace(result, faults=faults, predictions=predictions,
                         iterations=result.iterations.astype(np.uint64))
    faults[:] = 1
    predictions[:] = 0
    assert normalized.ledger_json == result.ledger_json
    for field, dtype in (("faults", np.uint8), ("predictions", np.uint8),
                         ("converged", np.bool_), ("iterations", np.int64)):
        actual = getattr(normalized, field)
        assert actual.dtype == dtype
        np.testing.assert_array_equal(actual, getattr(result, field))
        with pytest.raises(ValueError):
            actual.setflags(write=True)
    path = tmp_path / "normalized.jsonl"
    normalized.write_ledger(path)
    assert compiled.verify_ledger(path)["verified"]


def test_result_empty_batch_keeps_declared_column_ranks():
    result = decoder().decode_detailed(np.zeros((0, 1), np.uint8))
    assert replace(result, faults=np.empty((0, 1), np.int16)).faults.shape == (0, 1)
    with pytest.raises(ValueError, match="circuit result"):
        replace(result, faults=np.empty(0, np.uint8))


@pytest.mark.parametrize("backend", ["scalar", "compiled", "auto"])
@pytest.mark.parametrize("dem", ["error(0.1) D0 L0", "error(0.1) D0 L0\nerror(0.2) D0"])
def test_nms_overflow_fails_before_saturation(backend, dem):
    compiled = PolicyBpSinterDecoder(CircuitPolicy(rule="normalized_min_sum", parameter=1e308,
        backend=backend, max_iterations=1)).compile_decoder_for_dem(dem=stim.DetectorErrorModel(dem))
    with pytest.raises(NumericalFailure, match="normalized_min_sum_output"):
        compiled.decode_detailed(np.array([[1]], np.uint8))


@pytest.mark.parametrize("backend", ["compiled", "auto"])
@pytest.mark.parametrize("parameter", [.8, 1e305])
def test_nms_finite_values_keep_scalar_behavior(backend, parameter):
    config = dict(rule="normalized_min_sum", parameter=parameter, max_iterations=2)
    scalar = decoder(backend="scalar", **config).decode_detailed(np.array([[1]], np.uint8))
    compiled = decoder(backend=backend, **config).decode_detailed(np.array([[1]], np.uint8))
    assert scalar.ledger[1:] == compiled.ledger[1:]


@pytest.mark.parametrize("backend", ["scalar", "compiled", "auto"])
@pytest.mark.parametrize("syndrome,limit", [(0, 1), (1, 0)])
def test_nms_unexecuted_overflow_preserves_initial_stopping(backend, syndrome, limit):
    result = decoder(rule="normalized_min_sum", parameter=1e308, backend=backend,
                     max_iterations=limit).decode_detailed(np.array([[syndrome]], np.uint8))
    assert result.iterations.tolist() == [0]
    assert result.faults.tolist() == [[0]]
    assert result.converged.tolist() == [syndrome == 0]


def test_packed_overflow_does_not_publish_success_ledger(tmp_path):
    compiled = PolicyBpSinterDecoder(CircuitPolicy(rule="normalized_min_sum", parameter=1e308),
        ledger_directory=str(tmp_path)).compile_decoder_for_dem(dem=stim.DetectorErrorModel("error(0.1) D0 L0"))
    with pytest.raises(NumericalFailure, match="normalized_min_sum_output"):
        compiled.decode_shots_bit_packed(bit_packed_detection_event_data=np.array([[1]], np.uint8))
    assert not list(tmp_path.glob("*.jsonl"))


@pytest.mark.parametrize("controller,field,value", [
    (controller, field, value)
    for controller in ("single", "guided", "beam")
    for field, value in (("solution_limit", 2), ("relay_alpha", .25))
] + [(controller, "bias", 2.) for controller in ("single", "relay")])
def test_inactive_nondefault_controller_controls_are_rejected(controller, field, value):
    with pytest.raises(ValueError, match=field):
        CircuitPolicy(controller=controller, **{field: value})
    # Public factories must also revalidate a model_copy bypass.
    bypass = CircuitPolicy(controller=controller).model_copy(update={field: value})
    with pytest.raises(ValueError, match=field):
        PolicyBpSinterDecoder(bypass)


@pytest.mark.parametrize("controller", ["single", "relay", "guided", "beam"])
def test_shared_default_controller_fields_keep_policy_identity(controller):
    implicit = CircuitPolicy(controller=controller)
    explicit = CircuitPolicy(controller=controller, solution_limit=1, relay_alpha=.5, bias=20.)
    assert implicit.model_dump_json() == explicit.model_dump_json()


@pytest.mark.parametrize("controller", ["guided", "beam"])
def test_active_search_bias_changes_attempt_priors(controller):
    dem = stim.DetectorErrorModel("error(0.1) D0 D1\nerror(0.2) D0 D1 L0")
    attempts = []
    for bias in (2., 4.):
        compiled = PolicyBpSinterDecoder(CircuitPolicy(controller=controller, bias=bias,
            max_attempts=3, max_iterations=2)).compile_decoder_for_dem(dem=dem)
        result = compiled.decode_detailed(np.array([[1, 0]], np.uint8))
        child = result.ledger[1]["attempts"][1]
        assert abs(child["prior"][child["fixed"][0]]) == bias
        attempts.append(child["prior"])
    assert attempts[0] != attempts[1]


def test_active_relay_controls_keep_their_operands():
    counts = []
    for limit in (1, 2):
        result = decoder(controller="relay", relay_alpha=.25, solution_limit=limit,
                         max_attempts=3).decode_detailed(np.array([[1]], np.uint8))
        counts.append(len(result.ledger[1]["attempts"]))
        assert result.ledger[1]["control"]["termination"] == "solution_limit"
    assert counts == [1, 2]
