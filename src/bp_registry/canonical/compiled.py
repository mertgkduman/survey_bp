"""Optional Numba prototype for the canonical binary flooding hot loop.

This module is opt-in. It accepts a project-owned graph and explicit numerical
policy, and leaves provenance, budgets, and publication execution to the
reference engine until those contracts are qualified for this backend.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numba import njit

from .kernel import KernelResult
from .numerics import MIN_SUM_CPU_F64, REFERENCE_CPU_F64, prior_llr
from .schedules import EdgeTable, FloodingSweep, FloodingWork


@njit(cache=True)
def _clip(value: float, limit: float) -> float:
    return min(limit, max(-limit, value))


@njit(cache=True)
def _boxplus_pair(left: float, right: float, limit: float) -> float:
    left = _clip(left, limit)
    right = _clip(right, limit)
    a, b = abs(left), abs(right)
    smaller, larger = min(a, b), max(a, b)
    sign = -1.0 if left * right < 0.0 else 1.0
    correction = math.log1p(math.exp(-(smaller + larger))) - math.log1p(math.exp(-(larger - smaller)))
    return _clip(sign * (smaller + correction), limit)


@njit(cache=True)
def _flooding_sweep(
    row_ptr: np.ndarray, variables: np.ndarray, n: int, old_v2c: np.ndarray,
    syndrome: np.ndarray, prior: float, limit: float, rule: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    edge_count = len(variables)
    old = np.empty(edge_count, dtype=np.float64)
    for edge in range(edge_count):
        old[edge] = _clip(old_v2c[edge], limit)
    c2v = np.empty(edge_count, dtype=np.float64)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        for edge in range(start, stop):
            first = True
            result = limit
            negative_count = 0
            magnitude = limit
            for other in range(start, stop):
                if other == edge:
                    continue
                value = old[other]
                if rule == 0:
                    if first:
                        result = value
                        first = False
                    else:
                        result = _boxplus_pair(result, value, limit)
                else:
                    magnitude = min(magnitude, abs(value))
                    if value < 0.0:
                        negative_count += 1
            if rule == 0:
                message = result
                # The reference fold clips the complete result as a named boundary.
                message = _clip(message, limit)
                if syndrome[check]:
                    message = -message
            else:
                message = -magnitude if (negative_count + syndrome[check]) % 2 else magnitude
            c2v[edge] = _clip(message, limit)
    beliefs = np.full(n, prior, dtype=np.float64)
    for edge in range(edge_count):
        beliefs[variables[edge]] += c2v[edge]
    candidate = np.empty(n, dtype=np.uint8)
    for variable in range(n):
        beliefs[variable] = _clip(beliefs[variable], limit)
        candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
    new_v2c = np.empty(edge_count, dtype=np.float64)
    for edge in range(edge_count):
        new_v2c[edge] = _clip(beliefs[variables[edge]] - c2v[edge], limit)
    return old, c2v, beliefs, candidate, new_v2c


@njit(cache=True)
def _candidate_matches(row_ptr: np.ndarray, variables: np.ndarray, candidate: np.ndarray, syndrome: np.ndarray) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= candidate[variables[edge]]
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def _decode(
    row_ptr: np.ndarray, variables: np.ndarray, n: int, syndrome: np.ndarray,
    prior: float, limit: float, rule: int, max_iterations: int,
) -> tuple[np.ndarray, bool, int]:
    candidate = np.zeros(n, dtype=np.uint8)
    if len(variables) == 0:
        return candidate, _candidate_matches(row_ptr, variables, candidate, syndrome), 0
    v2c = np.full(len(variables), prior, dtype=np.float64)
    for iteration in range(1, max_iterations + 1):
        _, _, _, candidate, v2c = _flooding_sweep(row_ptr, variables, n, v2c, syndrome, prior, limit, rule)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, True, iteration
    return candidate, False, max_iterations


@dataclass(frozen=True)
class CompiledBinaryFlooding:
    """Preindexed, optional backend for plain SPA or plain min-sum flooding."""

    table: EdgeTable
    row_ptr: np.ndarray
    variables: np.ndarray
    rule: str

    @classmethod
    def from_check_matrix(cls, check_matrix: np.ndarray, *, rule: str = "spa") -> "CompiledBinaryFlooding":
        if rule not in {"spa", "min_sum"}:
            raise ValueError("compiled prototype supports only plain spa or min_sum")
        table = EdgeTable.from_check_matrix(check_matrix)
        row_ptr = np.zeros(table.check_count + 1, dtype=np.int64)
        variables = np.empty(table.edge_count, dtype=np.int64)
        for edge, (check, variable) in enumerate(table.edges):
            row_ptr[check + 1] += 1
            variables[edge] = variable
        np.cumsum(row_ptr, out=row_ptr)
        row_ptr.setflags(write=False)
        variables.setflags(write=False)
        return cls(table, row_ptr, variables, rule)

    @property
    def profile(self):
        return REFERENCE_CPU_F64 if self.rule == "spa" else MIN_SUM_CPU_F64

    def _syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        s = np.asarray(syndrome)
        if s.shape != (self.table.check_count,) or not np.issubdtype(s.dtype, np.integer) or np.any((s != 0) & (s != 1)):
            raise ValueError("syndrome must be a binary vector matching the graph")
        return np.asarray(s, dtype=np.uint8)

    def _inputs(self, syndrome: np.ndarray, error_rate: float) -> tuple[np.ndarray, float]:
        s = self._syndrome(syndrome)
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be finite and between zero and one")
        return s, prior_llr(error_rate, profile=self.profile)

    def bind_error_rate(self, error_rate: float) -> "BoundBinaryFlooding":
        """Resolve a fixed prior once for a same-parameter shot batch."""
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be finite and between zero and one")
        return BoundBinaryFlooding(self, prior_llr(error_rate, profile=self.profile))

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float) -> FloodingSweep:
        s, prior = self._inputs(syndrome, error_rate)
        old = np.asarray(old_v2c, dtype=np.float64)
        if old.shape != (self.table.edge_count,) or not np.all(np.isfinite(old)):
            raise ValueError("old_v2c must be finite and match the graph edges")
        arrays = _flooding_sweep(self.row_ptr, self.variables, self.table.variable_count, old, s,
                                 prior, self.profile.saturation, 0 if self.rule == "spa" else 1)
        for array in arrays:
            array.setflags(write=False)
        return FloodingSweep(
            edge_count=self.table.edge_count, old_v2c=arrays[0], check_to_variable=arrays[1],
            new_v2c=arrays[4], beliefs=arrays[2], candidate=arrays[3],
            proposed_work=FloodingWork(self.table.edge_count, self.table.edge_count,
                                       self.table.variable_count, self.table.variable_count),
        )

    def run(self, syndrome: np.ndarray, *, error_rate: float, max_iterations: int) -> KernelResult:
        s, prior = self._inputs(syndrome, error_rate)
        if type(max_iterations) is not int or max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        candidate, converged, iterations = _decode(
            self.row_ptr, self.variables, self.table.variable_count, s,
            prior, self.profile.saturation, 0 if self.rule == "spa" else 1, max_iterations,
        )
        candidate.setflags(write=False)
        return KernelResult(candidate, bool(converged), int(iterations))


@dataclass(frozen=True)
class BoundBinaryFlooding:
    """One declared binary graph, rule, and physical error rate."""

    graph: CompiledBinaryFlooding
    prior: float

    def run(self, syndrome: np.ndarray, *, max_iterations: int) -> KernelResult:
        s = self.graph._syndrome(syndrome)
        if type(max_iterations) is not int or max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        candidate, converged, iterations = _decode(
            self.graph.row_ptr, self.graph.variables, self.graph.table.variable_count, s,
            self.prior, self.graph.profile.saturation, 0 if self.graph.rule == "spa" else 1,
            max_iterations,
        )
        candidate.setflags(write=False)
        return KernelResult(candidate, bool(converged), int(iterations))


__all__ = ["BoundBinaryFlooding", "CompiledBinaryFlooding"]
