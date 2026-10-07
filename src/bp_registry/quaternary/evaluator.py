"""Independent outcome classification for frozen general-Pauli candidates.

The evaluator deliberately owns its compact symplectic and GF(2) routines.
It must not import kernel algebra: a shared commutation defect must not let a
decoder validate its own output after the candidate has been frozen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .problems import PauliCandidate, PauliCode


Outcome = Literal["invalid_syndrome", "exact", "stabilizer_equivalent", "logical_failure"]
LogicalAction = tuple[tuple[int, int], ...]


_SYMPLECTIC = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)
_FROM_SYMPLECTIC = np.asarray(((0, 3), (1, 2)), dtype=np.uint8)


@dataclass(frozen=True, slots=True)
class QuaternaryEvaluation:
    """One total outcome with observed or explicitly unavailable logical action.

    Each logical-action pair is ``(x, z)``.  The first bit is residual
    commutation with the declared logical-Z row, and the second is commutation
    with the declared logical-X row.  This gives the logical Pauli coordinate
    of the residual while retaining immutable, JSON-friendly values.
    """

    outcome: Outcome
    logical_action: LogicalAction | None
    logical_action_unavailable_reason: str | None

    @property
    def logical_action_available(self) -> bool:
        """Whether this evaluation observed a declared logical action."""
        return self.logical_action is not None


def _labels(value: object, *, name: str, shape: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != shape or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be an integer Pauli array with shape {shape}")
    if np.any((array < 0) | (array > 3)):
        raise ValueError(f"{name} must use I=0, X=1, Y=2, Z=3 labels")
    return np.array(array, dtype=np.uint8, copy=True)


def _syndrome(checks: np.ndarray, error: np.ndarray) -> np.ndarray:
    """Compute a full commutation syndrome with evaluator-local symplectic data."""
    check_bits = _SYMPLECTIC[checks]
    error_bits = _SYMPLECTIC[error]
    parity = (
        check_bits[..., 0] * error_bits[np.newaxis, :, 1]
        + check_bits[..., 1] * error_bits[np.newaxis, :, 0]
    ).sum(axis=1) % 2
    return np.asarray(parity, dtype=np.uint8)


def _multiply_mod_phase(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return the phase-free Pauli residual using evaluator-local labels."""
    bits = _SYMPLECTIC[left] ^ _SYMPLECTIC[right]
    return _FROM_SYMPLECTIC[bits[:, 0], bits[:, 1]]


def _gf2_rank(matrix: np.ndarray) -> int:
    """Compute binary rank by local Gauss-Jordan elimination."""
    work = np.asarray(matrix, dtype=np.uint8).copy() % 2
    pivot_row = 0
    for column in range(work.shape[1]):
        choices = np.flatnonzero(work[pivot_row:, column])
        if choices.size == 0:
            continue
        selected = pivot_row + int(choices[0])
        if selected != pivot_row:
            work[[pivot_row, selected]] = work[[selected, pivot_row]]
        for row in range(work.shape[0]):
            if row != pivot_row and work[row, column]:
                work[row] ^= work[pivot_row]
        pivot_row += 1
        if pivot_row == work.shape[0]:
            break
    return pivot_row


def _in_stabilizer_span(checks: np.ndarray, residual: np.ndarray) -> bool:
    """Decide membership in the stabilizer's binary symplectic row span."""
    check_bits = _SYMPLECTIC[checks]
    residual_bits = _SYMPLECTIC[residual]
    rows = np.concatenate((check_bits[..., 0], check_bits[..., 1]), axis=1)
    target = np.concatenate((residual_bits[:, 0], residual_bits[:, 1]))
    return _gf2_rank(rows) == _gf2_rank(np.vstack((rows, target)))


def _commutation_action(residual: np.ndarray, logical_x: np.ndarray, logical_z: np.ndarray) -> LogicalAction:
    """Return the residual's declared logical Pauli coordinate per logical row."""
    residual_bits = _SYMPLECTIC[residual]

    def pairing(rows: np.ndarray) -> np.ndarray:
        bits = _SYMPLECTIC[rows]
        return np.asarray(
            (
                bits[..., 0] * residual_bits[np.newaxis, :, 1]
                + bits[..., 1] * residual_bits[np.newaxis, :, 0]
            ).sum(axis=1)
            % 2,
            dtype=np.uint8,
        )

    x_action = pairing(logical_z)
    z_action = pairing(logical_x)
    return tuple((int(x), int(z)) for x, z in zip(x_action, z_action, strict=True))


def _unavailable(outcome: Outcome, reason: str) -> QuaternaryEvaluation:
    return QuaternaryEvaluation(outcome, None, reason)


def evaluate_pauli_candidate(
    candidate: PauliCandidate, *, hidden_truth: object
) -> QuaternaryEvaluation:
    """Classify one frozen candidate against its immutable original problem.

    Classification order is fixed: candidate-syndrome validity, exact residual,
    stabilizer-span equivalence, then logical failure.  Candidate convergence or
    decoder-termination information is deliberately absent from this interface.
    """
    if not isinstance(candidate, PauliCandidate):
        raise ValueError("candidate must be a frozen PauliCandidate")
    original = candidate.working.original
    code: PauliCode = original.code
    checks = _labels(code.checks, name="original checks", shape=code.checks.shape)
    proposed = _labels(candidate.candidate, name="candidate Pauli labels", shape=(code.n,))
    truth = _labels(original.syndrome, name="original syndrome", shape=(checks.shape[0],))

    if not np.array_equal(_syndrome(checks, proposed), truth):
        return _unavailable("invalid_syndrome", "candidate syndrome differs from original observation")

    # Hidden truth crosses the boundary only after the decoder froze this
    # candidate.  It is not an attribute of the candidate or policy interface.
    true_error = _labels(hidden_truth, name="hidden Pauli truth", shape=(code.n,))
    residual = _multiply_mod_phase(true_error, proposed)

    if not np.any(residual):
        outcome: Outcome = "exact"
    elif _in_stabilizer_span(checks, residual):
        outcome = "stabilizer_equivalent"
    else:
        outcome = "logical_failure"

    if code.logical_x is None or code.logical_z is None:
        return _unavailable(outcome, "original code has no declared logical basis")
    action = _commutation_action(residual, code.logical_x, code.logical_z)
    span_is_trivial = outcome in {"exact", "stabilizer_equivalent"}
    if span_is_trivial != all(x == 0 and z == 0 for x, z in action):
        raise ValueError("declared logical basis disagrees with stabilizer span")
    return QuaternaryEvaluation(outcome, action, None)


__all__ = ["LogicalAction", "Outcome", "QuaternaryEvaluation", "evaluate_pauli_candidate"]
