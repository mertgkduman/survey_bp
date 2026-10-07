"""Independent contract tests for the reusable Pauli algebra."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
from bp_registry.quaternary.algebra import Pauli, anticommutes, multiply_mod_phase, pauli_weight, syndrome, to_symplectic


def test_public_pauli_algebra_module_is_available():
    """The reusable algebra is a public Phase 10 contract."""
    assert Pauli.Y == 2


def test_public_quaternary_problem_contract_module_is_available():
    """Immutable general-stabilizer problems are a public Phase 10 contract."""
    assert importlib.util.find_spec("bp_registry.quaternary.problems") is not None


@pytest.mark.parametrize("label", range(4))
def test_explicit_encoding_and_symplectic_mapping(label, pauli_oracle):
    observed = to_symplectic(label)
    assert observed.tolist() == list(pauli_oracle["bits"][label])
    assert not observed.flags.writeable


@pytest.mark.parametrize("left", range(4))
@pytest.mark.parametrize("right", range(4))
def test_commutation_and_multiplication_match_hand_table(left, right, pauli_oracle):
    assert anticommutes(left, right) is (not pauli_oracle["commutes"][left][right])
    assert multiply_mod_phase(left, right) == pauli_oracle["products"][left][right]


def test_syndrome_and_weight_match_independent_hand_calculation(pauli_oracle):
    checks = np.asarray([[1, 2, 0], [3, 1, 2]], dtype=np.uint8)
    error = np.asarray([3, 2, 1], dtype=np.uint8)
    observed = syndrome(checks, error)
    assert observed.tolist() == pauli_oracle["syndrome"](checks, error).tolist()
    assert pauli_weight(error) == 3
    assert not observed.flags.writeable


@pytest.mark.parametrize("checks,error,diagnostic", [
    (None, [0], "must not be null"),
    ([[0.0]], [0], "integer Pauli"),
    ([[4]], [0], "I=0"),
    ([0, 1], [0, 0], "two-dimensional"),
    (np.empty((1, 0), dtype=np.uint8), [], "at least one row and one qubit"),
    ([[0, 0]], [0, 0], "identity-only"),
    ([[1]], np.empty(0, dtype=np.uint8), "matching the check qubits"),
])
def test_syndrome_rejects_invalid_dimensions_and_labels(checks, error, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        syndrome(checks, error)


def test_vector_boundaries_reject_noninteger_and_shape_mismatch():
    with pytest.raises(ValueError, match="integer Pauli"):
        to_symplectic([Pauli.I, 1.5])
    with pytest.raises(ValueError, match="same shape"):
        anticommutes([Pauli.I], [Pauli.I, Pauli.X])
    with pytest.raises(ValueError, match="same shape"):
        multiply_mod_phase([Pauli.I], [Pauli.I, Pauli.X])
