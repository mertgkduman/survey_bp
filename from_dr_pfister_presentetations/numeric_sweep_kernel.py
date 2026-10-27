"""Experimental uncapped and check-capped BP4/binary SPA kernels.

These are feasibility probes. Canonical profiles are changed only after
held-out evaluation and algebraic qualification.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from bp_registry.quaternary.compiled import _candidate_matches, _logaddexp


@njit(cache=True)
def _boxplus(left: float, right: float) -> float:
    a, b = abs(left), abs(right)
    smaller, larger = min(a, b), max(a, b)
    sign = -1.0 if left * right < 0.0 else 1.0
    return sign * (smaller + math.log1p(math.exp(-(smaller + larger)))
                   - math.log1p(math.exp(-(larger - smaller))))


@njit(cache=True)
def _tanh_half(value: float) -> float:
    if value > 40.0:
        return 1.0
    if value < -40.0:
        return -1.0
    return math.tanh(value / 2.0)


@njit(cache=True)
def _projection(values: np.ndarray, label: int) -> float:
    x, y, z = values[0], values[1], values[2]
    if label == 1:
        return _logaddexp(0.0, -x) - _logaddexp(-y, -z)
    if label == 2:
        return _logaddexp(0.0, -y) - _logaddexp(-x, -z)
    return _logaddexp(0.0, -z) - _logaddexp(-x, -y)


@njit(cache=True)
def _reference_tie(x: float, y: float, z: float) -> int:
    # Project I/X/Y/Z labels; reference strict ladder is I, X, Z, else Y.
    if x > 0.0 and y > 0.0 and z > 0.0:
        return 0
    if x < y and x < z:
        return 1
    if z < x and z < y:
        return 3
    return 2


@njit(cache=True)
def _check_message(incoming: np.ndarray, start: int, stop: int, target: int,
                   syndrome_bit: int, method: int, check_cap: float,
                   product_epsilon: float) -> float:
    if method == 0:
        product = -1.0 if syndrome_bit else 1.0
        for edge in range(start, stop):
            if edge != target:
                product *= _tanh_half(incoming[edge])
        if product >= 1.0:
            product = 1.0 - product_epsilon
        elif product <= -1.0:
            product = -1.0 + product_epsilon
        result = math.log1p(product) - math.log1p(-product)
    else:
        first = True
        result = 23.718998027710036  # Explicit degree-one convention only.
        for edge in range(start, stop):
            if edge == target:
                continue
            if first:
                result = incoming[edge]
                first = False
            else:
                result = _boxplus(result, incoming[edge])
        if syndrome_bit:
            result = -result
    if result > check_cap:
        result = check_cap
    elif result < -check_cap:
        result = -check_cap
    if not math.isfinite(result):
        raise ValueError("nonfinite BP check result")
    return result


@njit(cache=True)
def decode_bp4_numeric(row_ptr, variable_ptr, variable_edges, variables, labels,
                       prior_llrs, syndrome, max_iterations: int, method: int,
                       check_cap: float, product_epsilon: float, damping: float):
    n, edge_count = prior_llrs.shape[0], len(labels)
    old = prior_llrs[variables].copy()
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    for iteration in range(1, max_iterations + 1):
        for edge in range(edge_count):
            comm[edge] = _projection(old[edge], labels[edge])
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                c2v[edge] = _check_message(comm, start, stop, edge, int(syndrome[check]),
                                           method, check_cap, product_epsilon)
        for variable in range(n):
            for state in range(1, 4):
                value = prior_llrs[variable, state - 1]
                for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                    edge = variable_edges[position]
                    if labels[edge] != state:
                        value += c2v[edge]
                if not math.isfinite(value):
                    raise ValueError("nonfinite BP4 posterior")
                beliefs[variable, state - 1] = value
            candidate[variable] = _reference_tie(beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2])
        if _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        for edge in range(edge_count):
            variable, label = variables[edge], labels[edge]
            for state in range(1, 4):
                proposal = beliefs[variable, state - 1]
                if label != state:
                    proposal -= c2v[edge]
                value = damping * old[edge, state - 1] + (1.0 - damping) * proposal
                if not math.isfinite(value):
                    raise ValueError("nonfinite BP4 V2C")
                new[edge, state - 1] = value
        old, new = new, old
    return candidate, max_iterations, False


@njit(cache=True)
def _binary_matches(row_ptr, variables, candidate, syndrome) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= int(candidate[variables[edge]])
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def decode_binary_numeric(row_ptr, variables, n: int, prior: float, syndrome,
                          max_iterations: int, method: int, check_cap: float,
                          product_epsilon: float, damping: float):
    edge_count = len(variables)
    old = np.full(edge_count, prior, dtype=np.float64)
    new = np.empty_like(old)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty(n, dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    for iteration in range(1, max_iterations + 1):
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                c2v[edge] = _check_message(old, start, stop, edge, int(syndrome[check]),
                                           method, check_cap, product_epsilon)
        beliefs[:] = prior
        for edge in range(edge_count):
            beliefs[variables[edge]] += c2v[edge]
        for variable in range(n):
            if not math.isfinite(beliefs[variable]):
                raise ValueError("nonfinite binary posterior")
            candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
        if _binary_matches(row_ptr, variables, candidate, syndrome):
            return candidate, iteration, True
        for edge in range(edge_count):
            proposal = beliefs[variables[edge]] - c2v[edge]
            value = damping * old[edge] + (1.0 - damping) * proposal
            if not math.isfinite(value):
                raise ValueError("nonfinite binary V2C")
            new[edge] = value
        old, new = new, old
    return candidate, max_iterations, False
