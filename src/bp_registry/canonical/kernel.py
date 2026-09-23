"""Project-owned deterministic binary sum-product flooding kernel."""

from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .numerics import NumericalFailure, boxplus, finite_saturate


def _binary(value: np.ndarray, name: str, *, ndim: int) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary integer array with {ndim} dimensions")
    return np.array(array, dtype=np.uint8, copy=True)


@dataclass(frozen=True)
class KernelResult:
    candidate: np.ndarray
    converged: bool
    iterations: int


class BinarySpaKernel:
    """No native adapter: deterministic float64 LLR SPA with flooding updates."""

    def run(self, check_matrix: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iterations: int) -> KernelResult:
        h = _binary(check_matrix, "check_matrix", ndim=2)
        s = _binary(syndrome, "syndrome", ndim=1)
        if s.shape != (h.shape[0],) or h.shape[1] == 0 or not math.isfinite(error_rate) or not 0 < error_rate < 1:
            raise ValueError("invalid SPA dimensions or error_rate")
        prior = float(math.log((1.0 - error_rate) / error_rate))
        edges = [(check, variable) for check in range(h.shape[0]) for variable in np.flatnonzero(h[check])]
        v2c = {edge: prior for edge in edges}
        checks = [np.flatnonzero(h[row]).tolist() for row in range(h.shape[0])]
        for iteration in range(1, max_iterations + 1):
            c2v: dict[tuple[int, int], float] = {}
            for check, variables in enumerate(checks):
                for variable in variables:
                    message = boxplus(np.asarray([v2c[(check, other)] for other in variables if other != variable]))
                    c2v[(check, variable)] = -message if s[check] else message
            beliefs = np.full(h.shape[1], prior, dtype=np.float64)
            for (check, variable), message in c2v.items():
                beliefs[variable] += message
            beliefs = finite_saturate(beliefs, boundary="belief_assembly")
            candidate = np.asarray(beliefs < 0, dtype=np.uint8)
            if np.array_equal((h.astype(np.int64) @ candidate) % 2, s):
                return KernelResult(candidate, True, iteration)
            v2c = {
                (check, variable): float(finite_saturate(beliefs[variable] - c2v[(check, variable)], boundary="variable_update"))
                for check, variable in edges
            }
        return KernelResult(candidate, False, max_iterations)
