"""Optional compiled plain BP4 prototype with project-owned Pauli semantics.

This backend is for development qualification. It does not participate in
budget reservation, event ledgers, or publication execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numba import njit

from .algebra import Pauli
from .kernel import _priors
from .numerics import QBP4_F64_V1, probabilities_to_llrs
from .problems import PauliCode


@njit(cache=True)
def _clip(value: float, limit: float) -> float:
    return min(limit, max(-limit, value))


@njit(cache=True)
def _logaddexp(left: float, right: float) -> float:
    return max(left, right) + math.log1p(math.exp(-abs(left - right)))


@njit(cache=True)
def _boxplus_pair(left: float, right: float, limit: float) -> float:
    left = _clip(left, limit)
    right = _clip(right, limit)
    smaller, larger = min(abs(left), abs(right)), max(abs(left), abs(right))
    sign = -1.0 if left * right < 0.0 else 1.0
    correction = math.log1p(math.exp(-(smaller + larger))) - math.log1p(math.exp(-(larger - smaller)))
    return _clip(sign * (smaller + correction), limit)


@njit(cache=True)
def _anticommutes(label: int, state: int) -> bool:
    # I=0, X=1, Y=2, Z=3; symplectic anticommutation is exactly
    # "both are distinct nonidentity Paulis" for one qubit.
    return label != 0 and state != 0 and label != state


@njit(cache=True)
def _commutation_llr(values: np.ndarray, label: int, limit: float) -> float:
    x, y, z = _clip(values[0], limit), _clip(values[1], limit), _clip(values[2], limit)
    if label == 1:
        commute, anti = _logaddexp(0.0, -x), _logaddexp(-y, -z)
    elif label == 2:
        commute, anti = _logaddexp(0.0, -y), _logaddexp(-x, -z)
    else:
        commute, anti = _logaddexp(0.0, -z), _logaddexp(-x, -y)
    return _clip(_clip(commute, limit) - _clip(anti, limit), limit)


@njit(cache=True)
def _candidate_matches(
    row_ptr: np.ndarray, variables: np.ndarray, labels: np.ndarray,
    candidate: np.ndarray, syndrome: np.ndarray,
) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= int(_anticommutes(labels[edge], candidate[variables[edge]]))
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def _sweep(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, old_v2c: np.ndarray,
    prior_llrs: np.ndarray, syndrome: np.ndarray, limit: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n, edge_count = prior_llrs.shape[0], len(labels)
    quantized = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    new_v2c = np.empty((edge_count, 3), dtype=np.float64)
    candidate = np.empty(n, dtype=np.uint8)
    marginals = np.empty((n, 4), dtype=np.float64)
    _sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, old_v2c,
                prior_llrs, syndrome, limit, quantized, c2v, beliefs, new_v2c, candidate)
    _normalize_marginals(beliefs, marginals)
    return c2v, new_v2c, beliefs, marginals, candidate, quantized


@njit(cache=True)
def _sweep_into(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, old_v2c: np.ndarray,
    prior_llrs: np.ndarray, syndrome: np.ndarray, limit: float,
    quantized: np.ndarray, c2v: np.ndarray, beliefs: np.ndarray,
    new_v2c: np.ndarray, candidate: np.ndarray,
) -> None:
    n, edge_count = prior_llrs.shape[0], len(labels)
    for edge in range(edge_count):
        quantized[edge] = _commutation_llr(old_v2c[edge], labels[edge], limit)
    for check in range(len(row_ptr) - 1):
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            first = True
            message = limit
            for other in range(row_ptr[check], row_ptr[check + 1]):
                if other == edge:
                    continue
                if first:
                    message = quantized[other]
                    first = False
                else:
                    message = _boxplus_pair(message, quantized[other], limit)
            message = _clip(message, limit)
            if syndrome[check]:
                message = -message
            c2v[edge] = _clip(message, limit)
    for variable in range(n):
        for state in range(3):
            beliefs[variable, state] = prior_llrs[variable, state]
        for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
            edge = variable_edges[position]
            label = labels[edge]
            for state in range(1, 4):
                if _anticommutes(label, state):
                    beliefs[variable, state - 1] += c2v[edge]
        for state in range(3):
            beliefs[variable, state] = _clip(beliefs[variable, state], limit)
    for edge in range(edge_count):
        variable, label = variables[edge], labels[edge]
        for state in range(1, 4):
            value = beliefs[variable, state - 1]
            if _anticommutes(label, state):
                value -= c2v[edge]
            new_v2c[edge, state - 1] = _clip(value, limit)
    for variable in range(n):
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        if x > 0.0 and y > 0.0 and z > 0.0:
            candidate[variable] = 0
        elif x <= y and x <= z:
            candidate[variable] = 1
        elif y <= z:
            candidate[variable] = 2
        else:
            candidate[variable] = 3


@njit(cache=True)
def _normalize_marginals(beliefs: np.ndarray, marginals: np.ndarray) -> None:
    weights = np.empty(4, dtype=np.float64)
    for variable in range(len(beliefs)):
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        weights[0], weights[1], weights[2], weights[3] = 0.0, -x, -y, -z
        maximum = max(weights[0], weights[1], weights[2], weights[3])
        total = 0.0
        for state in range(4):
            weights[state] = math.exp(weights[state] - maximum)
            total += weights[state]
        for state in range(4):
            marginals[variable, state] = weights[state] / total


@njit(cache=True)
def _decode(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, prior_llrs: np.ndarray,
    syndrome: np.ndarray, limit: float, max_iterations: int, stop_on_convergence: bool,
) -> tuple[np.ndarray, int, bool]:
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, True
    v2c = np.empty((edge_count, 3), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    quantized = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    for edge in range(edge_count):
        for state in range(3):
            v2c[edge, state] = prior_llrs[variables[edge], state]
    for iteration in range(1, max_iterations + 1):
        _sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, v2c,
                    prior_llrs, syndrome, limit, quantized, c2v, beliefs, next_v2c, candidate)
        if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        v2c, next_v2c = next_v2c, v2c
    return candidate, max_iterations, _candidate_matches(row_ptr, variables, labels, candidate, syndrome)


@dataclass(frozen=True)
class CompiledBp4Sweep:
    c2v: np.ndarray
    v2c: np.ndarray
    beliefs: np.ndarray
    marginals: np.ndarray
    candidate: np.ndarray
    converged: bool


@dataclass(frozen=True)
class CompiledBp4Result:
    candidate: np.ndarray
    iterations: int
    converged: bool


@dataclass(frozen=True)
class CompiledBp4Graph:
    """Preindexed plain four-state BP4 with resolved I/X/Y/Z priors."""

    row_ptr: np.ndarray
    variable_ptr: np.ndarray
    variable_edges: np.ndarray
    variables: np.ndarray
    labels: np.ndarray
    prior_llrs: np.ndarray

    @classmethod
    def from_code(cls, code: PauliCode, priors: object) -> "CompiledBp4Graph":
        if not isinstance(code, PauliCode):
            raise TypeError("compiled BP4 prototype needs a validated PauliCode")
        probabilities = _priors(priors, n=code.n)
        rows, cols = np.nonzero(code.checks != Pauli.I)
        labels = np.asarray(code.checks[rows, cols], dtype=np.uint8)
        variables = np.asarray(cols, dtype=np.int64)
        row_ptr = np.zeros(code.checks.shape[0] + 1, dtype=np.int64)
        variable_ptr = np.zeros(code.n + 1, dtype=np.int64)
        for row in rows:
            row_ptr[int(row) + 1] += 1
        for variable in variables:
            variable_ptr[int(variable) + 1] += 1
        np.cumsum(row_ptr, out=row_ptr)
        np.cumsum(variable_ptr, out=variable_ptr)
        variable_edges = np.empty(len(labels), dtype=np.int64)
        offsets = variable_ptr[:-1].copy()
        for edge, variable in enumerate(variables):
            variable_edges[offsets[variable]] = edge
            offsets[variable] += 1
        prior_llrs = np.asarray([probabilities_to_llrs(row) for row in probabilities], dtype=np.float64)
        for array in (row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs):
            array.setflags(write=False)
        return cls(row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs)

    def _syndrome(self, value: np.ndarray) -> np.ndarray:
        syndrome = np.asarray(value)
        if syndrome.shape != (len(self.row_ptr) - 1,) or not np.issubdtype(syndrome.dtype, np.integer) or np.any((syndrome != 0) & (syndrome != 1)):
            raise ValueError("syndrome must be a binary vector matching the graph")
        return np.asarray(syndrome, dtype=np.uint8)

    def initial_v2c(self) -> np.ndarray:
        return np.asarray(self.prior_llrs[self.variables], dtype=np.float64)

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray) -> CompiledBp4Sweep:
        s = self._syndrome(syndrome)
        old = np.asarray(old_v2c, dtype=np.float64)
        if old.shape != (len(self.labels), 3) or not np.all(np.isfinite(old)):
            raise ValueError("old_v2c must be finite with one three-LLR row per edge")
        c2v, v2c, beliefs, marginals, candidate, _ = _sweep(
            self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
            self.labels, old, self.prior_llrs, s, QBP4_F64_V1.saturation,
        )
        converged = _candidate_matches(self.row_ptr, self.variables, self.labels, candidate, s)
        for array in (c2v, v2c, beliefs, marginals, candidate):
            array.setflags(write=False)
        return CompiledBp4Sweep(c2v, v2c, beliefs, marginals, candidate, bool(converged))

    def run(self, syndrome: np.ndarray, *, max_iterations: int, stop_on_convergence: bool = True) -> CompiledBp4Result:
        s = self._syndrome(syndrome)
        if type(max_iterations) is not int or max_iterations < 0 or type(stop_on_convergence) is not bool:
            raise ValueError("invalid compiled BP4 stopping request")
        candidate, iterations, converged = _decode(
            self.row_ptr, self.variable_ptr, self.variable_edges, self.variables, self.labels,
            self.prior_llrs, s, QBP4_F64_V1.saturation, max_iterations, stop_on_convergence,
        )
        candidate.setflags(write=False)
        return CompiledBp4Result(candidate, int(iterations), bool(converged))


__all__ = ["CompiledBp4Graph", "CompiledBp4Result", "CompiledBp4Sweep"]
