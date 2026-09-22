"""Small, independently validated CSS algebra and artifact identity helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct

import numpy as np


_SEMANTIC_MAGIC = b"BPREGCSS"
_SEMANTIC_VERSION = 1
_PAIR_CONVENTION = b"XZ"


def _bits(value: np.ndarray, name: str) -> np.ndarray:
    """Return a copied two-dimensional GF(2) matrix, rejecting coercions."""
    array = np.asarray(value)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a 2D integer matrix")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be binary")
    return np.array(array, dtype=np.uint8, copy=True)


def _bit_vector(value: np.ndarray, name: str, length: int) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (length,) or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a binary vector of length {length}")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be binary")
    return np.array(array, dtype=np.uint8, copy=True)


def gf2_rank(matrix: np.ndarray) -> int:
    """Compute matrix rank by Gaussian elimination over GF(2)."""
    a = _bits(matrix, "matrix")
    row = 0
    for column in range(a.shape[1]):
        pivots = np.flatnonzero(a[row:, column])
        if pivots.size == 0:
            continue
        pivot = row + int(pivots[0])
        if pivot != row:
            a[[row, pivot]] = a[[pivot, row]]
        for other in range(a.shape[0]):
            if other != row and a[other, column]:
                a[other] ^= a[row]
        row += 1
        if row == a.shape[0]:
            break
    return row


def in_row_space(matrix: np.ndarray, vector: np.ndarray) -> bool:
    """Whether a binary vector belongs to the GF(2) row span of ``matrix``."""
    rows = _bits(matrix, "matrix")
    candidate = _bit_vector(vector, "vector", rows.shape[1])
    return gf2_rank(np.vstack((rows, candidate))) == gf2_rank(rows)


@dataclass(frozen=True)
class CssCode:
    """CSS checks with an optional ordered paired logical basis."""

    hx: np.ndarray
    hz: np.ndarray
    lx: np.ndarray | None = None
    lz: np.ndarray | None = None

    def validate(self) -> "CssCode":
        hx, hz = _bits(self.hx, "Hx"), _bits(self.hz, "Hz")
        if hx.shape[1] == 0 or hx.shape[1] != hz.shape[1]:
            raise ValueError("CSS checks need the same nonzero column count")
        if np.any((hx.astype(np.int64) @ hz.astype(np.int64).T) % 2):
            raise ValueError("Hx and Hz do not commute")
        k = hx.shape[1] - gf2_rank(hx) - gf2_rank(hz)
        if k < 0:
            raise ValueError("CSS check ranks exceed the number of qubits")
        if (self.lx is None) != (self.lz is None):
            raise ValueError("logical basis needs both Lx and Lz")

        lx: np.ndarray | None = None
        lz: np.ndarray | None = None
        if self.lx is not None and self.lz is not None:
            lx, lz = _bits(self.lx, "Lx"), _bits(self.lz, "Lz")
            if lx.shape != (k, hx.shape[1]) or lz.shape != (k, hx.shape[1]):
                raise ValueError("logical bases must have shape (k, n)")
            if np.any((hz.astype(np.int64) @ lx.astype(np.int64).T) % 2):
                raise ValueError("Lx does not commute with Hz")
            if np.any((hx.astype(np.int64) @ lz.astype(np.int64).T) % 2):
                raise ValueError("Lz does not commute with Hx")
            pairing = (lx.astype(np.int64) @ lz.astype(np.int64).T) % 2
            if not np.array_equal(pairing, np.eye(k, dtype=np.int64)):
                raise ValueError("logical pair ordering or pairing is invalid")
            if gf2_rank(np.vstack((hx, lx))) != gf2_rank(hx) + k:
                raise ValueError("Lx logical rows are not quotient independent")
            if gf2_rank(np.vstack((hz, lz))) != gf2_rank(hz) + k:
                raise ValueError("Lz logical rows are not quotient independent")

        object.__setattr__(self, "hx", hx)
        object.__setattr__(self, "hz", hz)
        object.__setattr__(self, "lx", lx)
        object.__setattr__(self, "lz", lz)
        return self

    @property
    def n(self) -> int:
        return int(np.asarray(self.hx).shape[1])

    @property
    def k(self) -> int:
        return self.n - gf2_rank(self.hx) - gf2_rank(self.hz)


def fixture_code() -> CssCode:
    """Project-owned fixture, never a source-identity claim."""
    return CssCode(
        hx=np.array([[1, 1, 0]], dtype=np.uint8),
        hz=np.array([[0, 0, 1]], dtype=np.uint8),
        lx=np.array([[1, 0, 0]], dtype=np.uint8),
        lz=np.array([[1, 1, 0]], dtype=np.uint8),
    ).validate()


def semantic_bytes(code: CssCode) -> bytes:
    """Return v1 role/order-sensitive CSS bytes with little-bit-endian payloads."""
    validated = code.validate()
    if validated.lx is None or validated.lz is None:
        raise ValueError("semantic artifacts require an ordered paired logical basis")
    result = bytearray(_SEMANTIC_MAGIC)
    result.extend(struct.pack("<H", _SEMANTIC_VERSION))
    result.extend(struct.pack("<H", len(_PAIR_CONVENTION)))
    result.extend(_PAIR_CONVENTION)
    for role, matrix in ((b"X", validated.hx), (b"Z", validated.hz),
                         (b"x", validated.lx), (b"z", validated.lz)):
        result.extend(role)
        result.extend(struct.pack("<II", *matrix.shape))
        result.extend(np.packbits(matrix.reshape(-1), bitorder="little").tobytes())
    return bytes(result)


def semantic_sha256(code: CssCode) -> str:
    """SHA-256 identity for exact :func:`semantic_bytes` output."""
    return hashlib.sha256(semantic_bytes(code)).hexdigest()


def sample_x(code: CssCode, *, seed: int, shot_id: int, rate: float) -> np.ndarray:
    """Legacy fixture helper; production sampling moves to ``sampling.py``."""
    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError("rate must be finite and in [0,1]")
    if shot_id < 0:
        raise ValueError("shot_id must be nonnegative")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, shot_id])))
    return np.asarray(rng.random(code.n) < rate, dtype=np.uint8)


def syndrome_x(code: CssCode, error_x: np.ndarray) -> np.ndarray:
    """Z-check observation for a hidden X error: ``sZ = Hz eX``."""
    error = _bit_vector(error_x, "X error", code.n)
    return np.asarray((code.hz.astype(np.int64) @ error.astype(np.int64)) % 2, dtype=np.uint8)


def classify(code: CssCode, *, true_error: np.ndarray, candidate: np.ndarray) -> str:
    """Legacy X-only classifier retained until evaluator.py owns this interface."""
    truth = _bit_vector(true_error, "true error", code.n)
    proposed = _bit_vector(candidate, "candidate", code.n)
    if not np.array_equal(syndrome_x(code, truth), syndrome_x(code, proposed)):
        return "syndrome_failure"
    difference = truth ^ proposed
    if not difference.any():
        return "exact"
    if in_row_space(code.hx, difference):
        return "degenerate"
    return "logical_failure"
