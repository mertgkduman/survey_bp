"""Independent outcome contracts for frozen general-Pauli candidates.

The expected outcomes use the hand Pauli tables from this test package.  They
must remain separate from the quaternary kernel algebra so the evaluator does
not validate an implementation with its own lookup table.
"""

from __future__ import annotations

from itertools import product
import importlib.util
import inspect

import numpy as np
import pytest

from bp_registry.canonical.lineage import LineageEdge, LineageId
from bp_registry.css import fixture_code
from bp_registry.quaternary.problems import (
    PauliCandidate,
    PauliCode,
    QuaternaryOriginalProblem,
    QuaternaryWorkingProblem,
    compile_css_artifact,
)

PAULI_BITS = ((0, 0), (1, 0), (1, 1), (0, 1))
PAULI_PRODUCTS = (
    (0, 1, 2, 3),
    (1, 0, 3, 2),
    (2, 3, 0, 1),
    (3, 2, 1, 0),
)


def hand_syndrome(checks: object, error: object) -> np.ndarray:
    """Independent symplectic syndrome from the local hand Pauli table."""
    rows = np.asarray(checks, dtype=np.uint8)
    candidate = np.asarray(error, dtype=np.uint8)
    answer = np.zeros(rows.shape[0], dtype=np.uint8)
    for row, check in enumerate(rows):
        parity = 0
        for left, right in zip(check, candidate, strict=True):
            x1, z1 = PAULI_BITS[int(left)]
            x2, z2 = PAULI_BITS[int(right)]
            parity ^= (x1 * z2 + z1 * x2) % 2
        answer[row] = parity
    return answer


def _candidate(code: PauliCode, truth: object, proposed: object) -> PauliCandidate:
    original = QuaternaryOriginalProblem(
        "original-evaluator-fixture", code, hand_syndrome(code.checks, truth)
    )
    edge = LineageEdge(
        "identity",
        LineageId("original", original.lineage_id),
        LineageId("working", "working-evaluator-fixture"),
    )
    working = QuaternaryWorkingProblem("working-evaluator-fixture", original, edge)
    return PauliCandidate(
        "candidate-evaluator-fixture", working, np.asarray(proposed, dtype=np.uint8), 0
    )


def _general_code(*, logical_basis: bool = True) -> PauliCode:
    arguments: dict[str, object] = {}
    if logical_basis:
        # XX is the stabilizer. XI and ZZ form one independently declared pair.
        arguments = {
            "logical_x": np.asarray([[1, 0]], dtype=np.uint8),
            "logical_z": np.asarray([[3, 3]], dtype=np.uint8),
        }
    return PauliCode(checks=np.asarray([[1, 1]], dtype=np.uint8), **arguments)


def _residual(truth: object, proposed: object) -> tuple[int, ...]:
    return tuple(
        PAULI_PRODUCTS[int(left)][int(right)]
        for left, right in zip(truth, proposed, strict=True)
    )


def _css_bits(labels: object) -> tuple[np.ndarray, np.ndarray]:
    pairs = [PAULI_BITS[int(label)] for label in labels]
    return (
        np.asarray([pair[0] for pair in pairs], dtype=np.uint8),
        np.asarray([pair[1] for pair in pairs], dtype=np.uint8),
    )


def test_evaluator_module_is_an_independent_public_boundary():
    assert importlib.util.find_spec("bp_registry.quaternary.evaluator") is not None, (
        "QBP-03 needs an evaluator outside decoder and policy visibility"
    )


def test_invalid_syndrome_precedes_every_other_outcome():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    result = evaluate_pauli_candidate(_candidate(_general_code(), [0, 0], [3, 0]))

    assert result.outcome == "invalid_syndrome"
    assert result.logical_action is None
    assert result.logical_action_unavailable_reason == "candidate syndrome differs from original observation"


def test_exact_and_degenerate_stabilizer_residuals_have_distinct_outcomes():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    code = _general_code()
    exact = evaluate_pauli_candidate(_candidate(code, [2, 3], [2, 3]))
    degenerate = evaluate_pauli_candidate(_candidate(code, [0, 0], [1, 1]))

    assert exact.outcome == "exact"
    assert exact.logical_action == ((0, 0),)
    assert degenerate.outcome == "stabilizer_equivalent"
    assert degenerate.logical_action == ((0, 0),)


def test_logical_failure_reports_specific_declared_logical_action():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    result = evaluate_pauli_candidate(_candidate(_general_code(), [0, 0], [1, 0]))

    assert result.outcome == "logical_failure"
    assert result.logical_action == ((1, 0),)
    assert result.logical_action_unavailable_reason is None


def test_missing_logical_basis_is_typed_unavailable_without_changing_span_outcome():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    code = _general_code(logical_basis=False)
    degenerate = evaluate_pauli_candidate(_candidate(code, [0, 0], [1, 1]))
    logical = evaluate_pauli_candidate(_candidate(code, [0, 0], [1, 0]))

    assert degenerate.outcome == "stabilizer_equivalent"
    assert logical.outcome == "logical_failure"
    for result in (degenerate, logical):
        assert result.logical_action is None
        assert result.logical_action_unavailable_reason == "original code has no declared logical basis"


def test_exhaustive_general_fixture_matches_hand_syndrome_and_span_enumeration():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    code = _general_code()
    for truth in product(range(4), repeat=2):
        for proposed in product(range(4), repeat=2):
            result = evaluate_pauli_candidate(_candidate(code, truth, proposed))
            if not np.array_equal(hand_syndrome(code.checks, proposed), hand_syndrome(code.checks, truth)):
                expected = "invalid_syndrome"
            elif _residual(truth, proposed) == (0, 0):
                expected = "exact"
            elif _residual(truth, proposed) == (1, 1):
                expected = "stabilizer_equivalent"
            else:
                expected = "logical_failure"
            assert result.outcome == expected


def test_css_compilation_agrees_with_existing_css_evaluator_for_all_tiny_pauli_pairs():
    from bp_registry.evaluator import evaluate_candidate
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    css = fixture_code()
    compiled = compile_css_artifact(css, source_artifact_identity="css-evaluator-agreement")
    for truth in product(range(4), repeat=compiled.n):
        truth_x, truth_z = _css_bits(truth)
        for proposed in product(range(4), repeat=compiled.n):
            proposed_x, proposed_z = _css_bits(proposed)
            expected = evaluate_candidate(
                css,
                true_x=truth_x,
                true_z=truth_z,
                candidate_x=proposed_x,
                candidate_z=proposed_z,
            )
            actual = evaluate_pauli_candidate(_candidate(compiled, truth, proposed))
            assert actual.outcome == expected.outcome


def test_evaluator_rejects_malformed_candidate_even_if_an_object_was_tampered_after_freeze():
    from bp_registry.quaternary.evaluator import evaluate_pauli_candidate

    candidate = _candidate(_general_code(), [0, 0], [0, 0])
    object.__setattr__(candidate, "candidate", np.asarray([0, 4], dtype=np.uint8))

    with pytest.raises(ValueError, match="candidate Pauli labels"):
        evaluate_pauli_candidate(candidate)


def test_evaluator_source_does_not_import_kernel_commutation_or_stopping_logic():
    import bp_registry.quaternary.evaluator as evaluator

    source = inspect.getsource(evaluator)
    assert "from .algebra import" not in source
    assert "stopping" not in source
