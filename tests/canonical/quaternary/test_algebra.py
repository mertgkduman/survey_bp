"""Independent contract tests for the reusable Pauli algebra."""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
from bp_registry.quaternary.algebra import Pauli, anticommutes, multiply_mod_phase, pauli_weight, syndrome, to_symplectic
from bp_registry.quaternary.problems import PauliCandidate, PauliCode, QuaternaryOriginalProblem, QuaternaryWorkingProblem, compile_css_artifact
from bp_registry.canonical.lineage import LineageEdge, LineageId
from bp_registry.css import fixture_code


def test_public_pauli_algebra_module_is_available():
    """The reusable algebra is a public Phase 10 contract."""
    assert Pauli.Y == 2


def test_public_quaternary_problem_contract_module_is_available():
    """Immutable general-stabilizer problems are a public Phase 10 contract."""
    assert PauliCode.__name__ == "PauliCode"


def test_general_pauli_code_preserves_order_labels_and_optional_logical_absence():
    code = PauliCode(
        checks=np.asarray([[Pauli.Y, Pauli.X], [Pauli.X, Pauli.Y]], dtype=np.uint8),
        row_roles=("general", "general"),
        row_original_indices=(4, 9),
    )
    assert code.row_roles == ("general", "general")
    assert code.row_original_indices == (4, 9)
    assert code.logical_basis_available is False
    assert code.syndrome([Pauli.Y, Pauli.I]).tolist() == [0, 1]
    assert not code.checks.flags.writeable
    with pytest.raises(ValueError):
        code.checks[0, 0] = Pauli.I


def test_css_compiler_preserves_stored_x_then_z_order_and_joint_y_syndrome():
    css = fixture_code()
    compiled = compile_css_artifact(css, source_artifact_identity="fixture-css-v1")
    assert compiled.row_roles == ("x", "z")
    assert compiled.row_original_indices == (0, 0)
    assert compiled.source_artifact_identity == "fixture-css-v1"
    assert compiled.checks.tolist() == [[Pauli.X, Pauli.X, Pauli.I], [Pauli.I, Pauli.I, Pauli.Z]]
    y_error = np.asarray([Pauli.Y, Pauli.I, Pauli.Y], dtype=np.uint8)
    assert compiled.syndrome(y_error).tolist() == [1, 1]
    assert compiled.logical_basis_available is True
    assert compiled.logical_x.tolist() == [[Pauli.X, Pauli.I, Pauli.I]]
    assert compiled.logical_z.tolist() == [[Pauli.Z, Pauli.Z, Pauli.I]]


def test_semantic_identity_binds_order_roles_basis_and_source_identity():
    first = compile_css_artifact(fixture_code(), source_artifact_identity="source-a")
    second = compile_css_artifact(fixture_code(), source_artifact_identity="source-b")
    assert first.semantic_sha256 != second.semantic_sha256
    assert b'"row_roles":["x","z"]' in first.semantic_bytes()
    assert b'"logical_basis":' in first.semantic_bytes()


def test_original_working_and_candidate_require_certified_immutable_lineage():
    code = compile_css_artifact(fixture_code(), source_artifact_identity="fixture-css-v1")
    original = QuaternaryOriginalProblem("original-fixture", code, np.asarray([1, 0], dtype=np.uint8))
    edge = LineageEdge("identity", LineageId("original", "original-fixture"), LineageId("working", "working-fixture"))
    working = QuaternaryWorkingProblem("working-fixture", original, edge)
    candidate = PauliCandidate("candidate-fixture", working, np.asarray([Pauli.Y, Pauli.I, Pauli.Z], dtype=np.uint8), 0)
    assert working.syndrome.tolist() == [1, 0]
    assert candidate.candidate.tolist() == [Pauli.Y, Pauli.I, Pauli.Z]
    assert not candidate.candidate.flags.writeable
    with pytest.raises(ValueError, match="identity working problem"):
        QuaternaryWorkingProblem("working-altered", original, LineageEdge("identity", LineageId("original", "original-fixture"), LineageId("working", "working-altered")), syndrome=np.asarray([0, 0], dtype=np.uint8))
    with pytest.raises(ValueError, match="transform and lift"):
        QuaternaryWorkingProblem("working-transform", original, LineageEdge("transform", LineageId("original", "original-fixture"), LineageId("working", "working-transform")))


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
