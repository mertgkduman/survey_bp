"""Small CSS algebra used by the tracer; expanded in Plan 04."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def _bits(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a 2D integer matrix")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be binary")
    return np.array(array, dtype=np.uint8, copy=True)


@dataclass(frozen=True)
class CssCode:
    hx: np.ndarray
    hz: np.ndarray

    def validate(self) -> "CssCode":
        hx, hz = _bits(self.hx, "Hx"), _bits(self.hz, "Hz")
        if hx.shape[1] == 0 or hx.shape[1] != hz.shape[1]:
            raise ValueError("CSS checks need the same nonzero column count")
        if np.any((hx.astype(np.int64) @ hz.astype(np.int64).T) % 2):
            raise ValueError("Hx and Hz do not commute")
        object.__setattr__(self, "hx", hx)
        object.__setattr__(self, "hz", hz)
        return self

    @property
    def n(self) -> int:
        return int(np.asarray(self.hx).shape[1])


def fixture_code() -> CssCode:
    return CssCode(
        hx=np.array([[1, 1, 0]], dtype=np.uint8),
        hz=np.array([[0, 0, 1]], dtype=np.uint8),
    ).validate()


def sample_x(code: CssCode, *, seed: int, shot_id: int, rate: float) -> np.ndarray:
    import math

    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError("rate must be finite and in [0,1]")
    if shot_id < 0:
        raise ValueError("shot_id must be nonnegative")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, shot_id])))
    return np.asarray(rng.random(code.n) < rate, dtype=np.uint8)


def syndrome_x(code: CssCode, error_x: np.ndarray) -> np.ndarray:
    """Z-check observation for a hidden X error: s_Z = H_Z e_X."""
    error = np.asarray(error_x, dtype=np.uint8)
    if error.shape != (code.n,) or np.any(error > 1):
        raise ValueError("invalid X error")
    return np.asarray((code.hz.astype(np.int64) @ error.astype(np.int64)) % 2, dtype=np.uint8)


def _gf2_rank(matrix: np.ndarray) -> int:
    a = np.array(matrix, dtype=np.uint8, copy=True) % 2
    row = 0
    for col in range(a.shape[1]):
        pivot = next((i for i in range(row, a.shape[0]) if a[i, col]), None)
        if pivot is None:
            continue
        a[[row, pivot]] = a[[pivot, row]]
        for i in range(a.shape[0]):
            if i != row and a[i, col]:
                a[i] ^= a[row]
        row += 1
        if row == a.shape[0]:
            break
    return row


def classify(code: CssCode, *, true_error: np.ndarray, candidate: np.ndarray) -> str:
    """Classify against the original syndrome and hidden truth."""
    truth = np.asarray(true_error, dtype=np.uint8)
    proposed = np.asarray(candidate, dtype=np.uint8)
    if truth.shape != (code.n,) or proposed.shape != (code.n,):
        raise ValueError("error and candidate must have code length")
    if np.any(truth > 1) or np.any(proposed > 1):
        raise ValueError("error and candidate must be binary")
    if not np.array_equal(syndrome_x(code, truth), syndrome_x(code, proposed)):
        return "syndrome_failure"
    difference = truth ^ proposed
    if not difference.any():
        return "exact"
    if _gf2_rank(np.vstack([code.hx, difference])) == _gf2_rank(code.hx):
        return "degenerate"
    return "logical_failure"
