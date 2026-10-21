"""Independent numerical-profile oracles for the canonical binary SPA kernel."""

from __future__ import annotations

import math

import numpy as np
import pytest

import bp_registry.canonical.numerics as numerics


def _profile_api():
    assert hasattr(numerics, "REFERENCE_CPU_F64"), (
        "binary-spa-flooding-f64-v1 must expose its resolved numerical profile"
    )
    assert hasattr(numerics, "probability_to_llr")
    assert hasattr(numerics, "prior_llr")
    assert hasattr(numerics, "hard_decision")
    assert hasattr(numerics, "canonical_min_index")
    assert hasattr(numerics, "check_to_variable")
    return numerics.REFERENCE_CPU_F64


def test_reference_profile_materializes_encoding_clipping_and_ties():
    profile = _profile_api()
    evidence = profile.as_evidence()

    assert evidence == {
        "profile_id": "binary-spa-flooding-f64-v1",
        "backend": "cpu-numpy",
        "dtype": "float64",
        "llr_encoding": "natural_log_odds",
        "syndrome_convention": "one_negates_check_to_variable",
        "saturation": 25.0,
        "prior_initialization": "log((1-p)/p)",
        "normalization": "none",
        "degree_one_rule": "positive_saturation_before_syndrome_sign",
        "exact_zero_decision": 0,
        "tie_break": "ascending_canonical_id",
    }
    np.testing.assert_allclose(
        numerics.probability_to_llr(np.array([0.2, 0.5, 0.8])),
        np.log(np.array([4.0, 1.0, 0.25])),
    )
    assert numerics.prior_llr(0.2) == pytest.approx(math.log(4.0))
    np.testing.assert_array_equal(
        numerics.hard_decision(np.array([-1.0, 0.0, 1.0])),
        np.array([1, 0, 0], dtype=np.uint8),
    )
    assert numerics.canonical_min_index(np.array([3.0, 1.0, 1.0]), np.array([4, 9, 2])) == 2


def test_boxplus_matches_direct_safe_equation_and_extremes_stay_finite():
    _profile_api()
    left, right = 1.2, -0.7
    direct = 2.0 * math.atanh(math.tanh(left / 2.0) * math.tanh(right / 2.0))
    assert numerics.boxplus_pair(left, right) == pytest.approx(direct)
    assert numerics.boxplus(np.array([left, right])) == pytest.approx(direct)
    assert np.isfinite(numerics.boxplus_pair(25.0, -25.0))
    assert np.isfinite(numerics.boxplus(np.array([25.0, -25.0, 25.0])))


def test_scalar_boxplus_preserves_array_oracle_bits_and_failures() -> None:
    rng = np.random.default_rng(6201)
    pairs = np.vstack((rng.uniform(-40, 40, size=(4096, 2)), np.asarray([
        [-0.0, 0.0], [25.0, -25.0], [1e-300, -1e-300], [40.0, 40.0], [-40.0, -40.0],
    ])))
    for profile in (numerics.REFERENCE_CPU_F64, numerics.NumericalProfile(saturation=12.3), numerics.NumericalProfile(saturation=500.0)):
        expected = []
        for left, right in pairs:
            old_pair = numerics.finite_saturate(np.asarray([left, right]), boundary="boxplus_pair_input", profile=profile)
            magnitudes = np.abs(old_pair)
            smaller, larger = float(np.min(magnitudes)), float(np.max(magnitudes))
            sign = -1.0 if float(old_pair[0]) * float(old_pair[1]) < 0.0 else 1.0
            with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
                correction = np.log1p(np.exp(-(smaller + larger))) - np.log1p(np.exp(-(larger - smaller)))
            expected.append(float(numerics.finite_saturate(sign * (smaller + float(correction)), boundary="boxplus_pair_output", profile=profile)))
        actual = [numerics.boxplus_pair(float(left), float(right), profile=profile) for left, right in pairs]
        np.testing.assert_array_equal(np.asarray(actual).view(np.uint64), np.asarray(expected).view(np.uint64))
    with pytest.raises(numerics.NumericalFailure, match="boxplus_pair_input"):
        numerics.boxplus_pair(np.nan, 1.0)
    with pytest.raises(ValueError, match="boxplus_pair_input"):
        numerics.boxplus_pair("invalid", 1.0)


def test_degree_one_empty_and_invalid_boundaries_are_explicit():
    profile = _profile_api()
    assert numerics.check_to_variable(np.array([], dtype=np.float64)) == profile.saturation
    assert numerics.check_to_variable(np.array([], dtype=np.float64), syndrome=1) == -profile.saturation
    assert numerics.boxplus(np.array([], dtype=np.float64)) == profile.saturation
    assert numerics.probability_to_llr(np.array([], dtype=np.float64)).shape == (0,)

    with pytest.raises(ValueError, match="probability"):
        numerics.probability_to_llr(np.array([0.0]))
    with pytest.raises(ValueError, match="binary"):
        numerics.check_to_variable(np.array([1.0]), syndrome=2)
    with pytest.raises(numerics.NumericalFailure, match="boxplus_input"):
        numerics.boxplus(np.array([np.nan]))
    with pytest.raises(numerics.NumericalFailure, match="probability_to_llr_input"):
        numerics.probability_to_llr(np.array([np.inf]))
