"""Numerical and source-equation contracts for the canonical scalar BP4 kernel."""

from __future__ import annotations

import importlib.util
import numpy as np
import pytest

from bp_registry.quaternary.algebra import anticommutes
from bp_registry.quaternary.numerics import (
    QBP4_F64_V1,
    QuaternaryNumericalFailure,
    check_message,
    commutation_llr,
    llrs_to_probabilities,
    ordered_boxplus,
    pauli_hard_decision,
    probabilities_to_llrs,
)


def test_scalar_llr_bp4_kernel_is_available() -> None:
    """QBP-01 needs a production-owned scalar LLR-BP4 session, not an adapter."""
    assert importlib.util.find_spec("bp_registry.quaternary.kernel") is not None, (
        "bp_registry.quaternary.kernel is absent"
    )


def test_numerics_profile_persists_complete_binding_contract() -> None:
    evidence = QBP4_F64_V1.as_evidence()
    assert evidence["profile_id"] == "quaternary-bp4-f64-v1"
    assert evidence["saturation"] == 25.0
    assert evidence["saturation_boundary"] == "symmetric_after_every_public_message_or_belief_primitive"
    assert evidence["oracle_gate"] == "vector_and_exact_tree_fixtures_required_before_public_manifest"


def test_commutation_llr_matches_direct_four_state_mass_ratio() -> None:
    probabilities = np.asarray((0.40, 0.10, 0.35, 0.15), dtype=np.float64)
    llrs = probabilities_to_llrs(probabilities)
    for label in (1, 2, 3):
        anticommute = np.asarray(anticommutes(np.full(4, label, dtype=np.uint8), np.arange(4, dtype=np.uint8)), dtype=bool)
        expected = np.log(probabilities[~anticommute].sum()) - np.log(probabilities[anticommute].sum())
        assert commutation_llr(llrs, label) == pytest.approx(expected)


def test_logsum_and_boxplus_are_ordered_finite_and_symmetrically_clipped() -> None:
    assert ordered_boxplus(np.asarray((), dtype=np.float64)) == 25.0
    assert check_message(np.asarray((100.0,), dtype=np.float64), syndrome=1) == -25.0
    assert -25.0 <= ordered_boxplus(np.asarray((4.0, -3.0, 2.0), dtype=np.float64)) <= 25.0
    with pytest.raises(QuaternaryNumericalFailure, match="nonfinite"):
        ordered_boxplus(np.asarray((np.nan,), dtype=np.float64))


def test_four_state_normalization_and_persisted_zero_tie_rule() -> None:
    posterior = llrs_to_probabilities(np.asarray((0.0, 0.0, 0.0), dtype=np.float64))
    assert np.allclose(posterior, 0.25)
    assert pauli_hard_decision(np.asarray((0.0, 0.0, 0.0), dtype=np.float64)).name == "X"
    assert pauli_hard_decision(np.asarray((0.3, 0.2, 0.1), dtype=np.float64)).name == "I"
    assert pauli_hard_decision(np.asarray((0.1, -0.4, -0.4), dtype=np.float64)).name == "Y"


def test_decoder_priors_require_explicit_positive_smoothing() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        probabilities_to_llrs(np.asarray((1.0, 0.0, 0.0, 0.0), dtype=np.float64))
