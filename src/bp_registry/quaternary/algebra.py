"""Typed, immutable Pauli algebra for the canonical quaternary family.

The persisted label order is explicit: ``I=0, X=1, Y=2, Z=3``.  Each label
maps to its binary symplectic pair ``(x, z)``.  All array-valued public
results are owned and read-only so callers cannot mutate mathematical inputs
after validation.
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot


class Pauli(IntEnum):
    """The fixed persisted I/X/Y/Z label encoding."""

    I = 0
    X = 1
    Y = 2
    Z = 3


_SYMPLECTIC = np.asarray(((0, 0), (1, 0), (1, 1), (0, 1)), dtype=np.uint8)
_SYMPLECTIC = immutable_snapshot(_SYMPLECTIC)
_FROM_SYMPLECTIC = np.asarray(((Pauli.I, Pauli.Z), (Pauli.X, Pauli.Y)), dtype=np.uint8)
_FROM_SYMPLECTIC = immutable_snapshot(_FROM_SYMPLECTIC)


def _readonly(value: np.ndarray) -> np.ndarray:
    result = immutable_snapshot(value)
    return result


def _labels(value: object, *, name: str) -> np.ndarray:
    if value is None:
        raise ValueError(f"{name} must not be null")
    array = np.asarray(value)
    if not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must contain integer Pauli labels")
    if np.any((array < int(Pauli.I)) | (array > int(Pauli.Z))):
        raise ValueError(f"{name} must use I=0, X=1, Y=2, Z=3 labels")
    return np.array(array, dtype=np.uint8, copy=True)


def _checks(value: object) -> np.ndarray:
    checks = _labels(value, name="checks")
    if checks.ndim != 2:
        raise ValueError("checks must be a two-dimensional Pauli matrix")
    if checks.shape[0] == 0 or checks.shape[1] == 0:
        raise ValueError("checks require at least one row and one qubit")
    if np.any(np.all(checks == Pauli.I, axis=1)):
        raise ValueError("checks must not contain identity-only rows")
    return checks


def to_symplectic(value: object) -> np.ndarray:
    """Map Pauli labels to owned, read-only ``(..., 2)`` symplectic bits."""
    return _readonly(_SYMPLECTIC[_labels(value, name="Pauli labels")])


def anticommutes(left: object, right: object) -> bool | np.ndarray:
    """Whether matching-shape Pauli labels anticommute under the symplectic form."""
    lhs = _labels(left, name="left Pauli labels")
    rhs = _labels(right, name="right Pauli labels")
    if lhs.shape != rhs.shape:
        raise ValueError("Pauli operands must have the same shape")
    lhs_bits, rhs_bits = _SYMPLECTIC[lhs], _SYMPLECTIC[rhs]
    value = (lhs_bits[..., 0] * rhs_bits[..., 1] + lhs_bits[..., 1] * rhs_bits[..., 0]) % 2
    if value.ndim == 0:
        return bool(value)
    return _readonly(value.astype(bool, copy=False))


def multiply_mod_phase(left: object, right: object) -> Pauli | np.ndarray:
    """Multiply Pauli labels while discarding their global phase."""
    lhs = _labels(left, name="left Pauli labels")
    rhs = _labels(right, name="right Pauli labels")
    if lhs.shape != rhs.shape:
        raise ValueError("Pauli operands must have the same shape")
    product_bits = _SYMPLECTIC[lhs] ^ _SYMPLECTIC[rhs]
    values = _FROM_SYMPLECTIC[product_bits[..., 0], product_bits[..., 1]]
    if values.ndim == 0:
        return Pauli(int(values))
    return _readonly(values)


def pauli_weight(value: object) -> int:
    """Return the number of nonidentity Pauli labels in a vector or array."""
    return int(np.count_nonzero(_labels(value, name="Pauli labels") != Pauli.I))


def syndrome(checks: object, error: object) -> np.ndarray:
    """Return immutable commutation syndrome bits in the declared check order."""
    check_matrix = _checks(checks)
    candidate = _labels(error, name="error")
    if candidate.shape != (check_matrix.shape[1],):
        raise ValueError("error must be a Pauli vector matching the check qubits")
    check_bits = _SYMPLECTIC[check_matrix]
    error_bits = _SYMPLECTIC[candidate]
    parity = (
        check_bits[..., 0] * error_bits[np.newaxis, :, 1]
        + check_bits[..., 1] * error_bits[np.newaxis, :, 0]
    ).sum(axis=1) % 2
    return _readonly(parity.astype(np.uint8, copy=False))


__all__ = [
    "Pauli",
    "anticommutes",
    "multiply_mod_phase",
    "pauli_weight",
    "syndrome",
    "to_symplectic",
]
