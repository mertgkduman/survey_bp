"""Finite deterministic numerical primitives for binary LLR SPA."""

from __future__ import annotations

import math
import numpy as np

SATURATION = 30.0


class NumericalFailure(RuntimeError):
    """A nonfinite numerical result that must become terminal evidence."""


def finite_saturate(value: np.ndarray | float, *, boundary: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise NumericalFailure(f"nonfinite arithmetic at {boundary}")
    return np.clip(array, -SATURATION, SATURATION)


def boxplus(values: np.ndarray) -> float:
    """Stable LLR-domain check update, including the degree-one identity."""
    vector = finite_saturate(values, boundary="boxplus_input").reshape(-1)
    if vector.size == 0:
        return float(SATURATION)
    signs = -1.0 if int(np.count_nonzero(vector < 0)) % 2 else 1.0
    magnitudes = np.abs(vector)
    # -log(tanh(x/2)) is stable enough after the named finite clipping above.
    transformed = -np.log(np.tanh(np.maximum(magnitudes, np.finfo(float).tiny) / 2.0))
    result = signs * float(-np.log(np.tanh(np.maximum(np.sum(transformed), np.finfo(float).tiny) / 2.0)))
    return float(finite_saturate(result, boundary="boxplus_output"))
