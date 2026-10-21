from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

stim = pytest.importorskip("stim")
pytest.importorskip("sinter")
pytest.importorskip("numba")

from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import MIN_SUM_CPU_F64, REFERENCE_CPU_F64
from bp_registry.canonical.schedules import FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.circuit import CanonicalBpSinterDecoder, DemBinaryModel


def test_dem_error_targets_and_forced_faults_preserve_parity() -> None:
    dem = stim.DetectorErrorModel("""
        error(1) D0 L0
        error(0) D1 L1
        error(0.1) D0 ^ D1 L1
    """)
    model = DemBinaryModel.from_dem(dem)
    assert model.source_error_count == 3
    assert model.table.variable_count == 1
    assert model.table.edges == ((0, 0), (1, 0))
    np.testing.assert_array_equal(model.syndrome_bias, [1, 0])
    np.testing.assert_array_equal(model.observable_bias, [1, 0])
    decoder = CanonicalBpSinterDecoder(3).compile_decoder_for_dem(dem=dem)
    predictions, converged, _iterations = decoder.decode_detailed(np.array([[1, 0], [0, 1]], dtype=np.uint8))
    np.testing.assert_array_equal(predictions, [[1, 0], [1, 1]])
    assert converged.all()


def test_compiled_first_sweep_matches_reference_policy() -> None:
    dem = stim.DetectorErrorModel("""
        error(0.1) D0 L0
        error(0.2) D0 D1
        error(0.3) D1 L1
    """)
    model = DemBinaryModel.from_dem(dem)
    syndrome = np.array([1, 0], dtype=np.uint8)
    schedule = FloodingSchedule(model.table, kernel=BinarySpaKernel())
    old_v2c = model.prior_llrs[model.variables]
    expected = schedule.sweep(old_v2c, syndrome, error_rate=0.1, prior_llrs=model.prior_llrs)
    decoder = CanonicalBpSinterDecoder(1).compile_decoder_for_dem(dem=dem)
    _prediction, _converged, iterations = decoder.decode_detailed(syndrome[None, :])
    from bp_registry.circuit.compiled import _decode_one
    candidate, _, _ = _decode_one(model.row_ptr, model.variables, model.prior_llrs, syndrome, REFERENCE_CPU_F64.saturation, 1, 0, False)
    np.testing.assert_array_equal(candidate, expected.candidate)
    assert iterations[0] == 1


def test_compiled_min_sum_first_sweep_matches_reference_policy() -> None:
    dem = stim.DetectorErrorModel("""
        error(0.1) D0 L0
        error(0.2) D0 D1
        error(0.3) D0 D1 L1
    """)
    model = DemBinaryModel.from_dem(dem)
    syndrome = np.array([1, 0], dtype=np.uint8)
    kernel = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    expected = FloodingSchedule(model.table, kernel=kernel).sweep(
        model.prior_llrs[model.variables], syndrome, error_rate=0.1, prior_llrs=model.prior_llrs,
    )
    from bp_registry.circuit.compiled import _decode_one
    candidate, _, _ = _decode_one(
        model.row_ptr, model.variables, model.prior_llrs, syndrome, MIN_SUM_CPU_F64.saturation, 1, 1, False,
    )
    np.testing.assert_array_equal(candidate, expected.candidate)


def test_relay_circuit_sinter_batch_contract() -> None:
    path = Path(__file__).resolve().parents[2] / "data/circuits/relay-v0.2.2/bicycle_bivariate_18_4_3_memory_X.stim"
    circuit = stim.Circuit.from_file(path)
    dem = circuit.detector_error_model(decompose_errors=False)
    decoder = CanonicalBpSinterDecoder(2).compile_decoder_for_dem(dem=dem)
    detectors, _truth = circuit.compile_detector_sampler(seed=12).sample(shots=4, separate_observables=True)
    packed = np.packbits(detectors, axis=1, bitorder="little")
    output = decoder.decode_shots_bit_packed(bit_packed_detection_event_data=packed)
    expected, _converged, _iterations = decoder.decode_detailed(detectors)
    np.testing.assert_array_equal(output, np.packbits(expected, axis=1, bitorder="little"))
    assert output.shape == (4, (dem.num_observables + 7) // 8)


def test_bad_bit_packed_shape_rejected() -> None:
    dem = stim.DetectorErrorModel("error(0.1) D0 L0")
    decoder = CanonicalBpSinterDecoder().compile_decoder_for_dem(dem=dem)
    with pytest.raises(ValueError, match="packed detection data"):
        decoder.decode_shots_bit_packed(bit_packed_detection_event_data=np.zeros((2, 0), dtype=np.uint8))


def test_zero_belief_tie_is_an_explicit_policy() -> None:
    dem = stim.DetectorErrorModel("error(0.5) D0 L0")
    events = np.array([[0]], dtype=np.uint8)
    zero = CanonicalBpSinterDecoder(0, tie_break="zero").compile_decoder_for_dem(dem=dem)
    one = CanonicalBpSinterDecoder(0, tie_break="one").compile_decoder_for_dem(dem=dem)
    np.testing.assert_array_equal(zero.decode_detailed(events)[0], [[0]])
    np.testing.assert_array_equal(one.decode_detailed(events)[0], [[1]])
    with pytest.raises(ValueError, match="tie_break"):
        CanonicalBpSinterDecoder(tie_break="invalid")


def test_sinter_custom_decoder_api_predicts_observables() -> None:
    import sinter

    dem = stim.DetectorErrorModel("error(0.1) D0 L0")
    output = sinter.predict_observables(
        dem=dem, dets=np.array([[False], [True]], dtype=np.bool_),
        decoder="canonical_bp", custom_decoders={"canonical_bp": CanonicalBpSinterDecoder(2)},
    )
    np.testing.assert_array_equal(output, [[False], [True]])
