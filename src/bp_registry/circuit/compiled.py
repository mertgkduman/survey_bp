"""Opt-in compiled CPU flooding on DEM fault variables.

This preserves the canonical binary SPA box-plus, saturation, edge ordering,
hard-decision, and syndrome-check rules while allowing one prior per fault.
"""

from __future__ import annotations

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _boxplus_pair, _candidate_matches, _clip


@njit(cache=True)
def _decode_one(
    row_ptr: np.ndarray, variables: np.ndarray, prior_llrs: np.ndarray,
    syndrome: np.ndarray, limit: float, max_iterations: int, rule: int,
    tie_break_one: bool,
) -> tuple[np.ndarray, bool, int]:
    n = len(prior_llrs)
    v2c = np.empty(len(variables), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    c2v = np.empty_like(v2c)
    prefix = np.empty_like(v2c)
    suffix = np.empty_like(v2c)
    beliefs = np.empty(n, dtype=np.float64)
    candidate = np.empty(n, dtype=np.uint8)
    for variable in range(n):
        candidate[variable] = 1 if (prior_llrs[variable] <= 0 if tie_break_one else prior_llrs[variable] < 0) else 0
    if _candidate_matches(row_ptr, variables, candidate, syndrome):
        return candidate, True, 0
    for edge in range(len(variables)):
        v2c[edge] = _clip(prior_llrs[variables[edge]], limit)
    for iteration in range(1, max_iterations + 1):
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            if rule == 0:
                if start < stop:
                    prefix[start] = v2c[start]
                    suffix[stop - 1] = v2c[stop - 1]
                for edge in range(start + 1, stop):
                    prefix[edge] = _boxplus_pair(prefix[edge - 1], v2c[edge], limit)
                for edge in range(stop - 2, start - 1, -1):
                    suffix[edge] = _boxplus_pair(v2c[edge], suffix[edge + 1], limit)
                for edge in range(start, stop):
                    if edge == start and edge == stop - 1:
                        message = limit
                    elif edge == start:
                        message = suffix[edge + 1]
                    elif edge == stop - 1:
                        message = prefix[edge - 1]
                    else:
                        message = _boxplus_pair(prefix[edge - 1], suffix[edge + 1], limit)
                    message = _clip(message, limit)
                    if syndrome[check]:
                        message = -message
                    c2v[edge] = _clip(message, limit)
            else:
                negative_count = 0
                first_min = limit
                second_min = limit
                first_edge = -1
                for edge in range(start, stop):
                    value = v2c[edge]
                    if value < 0:
                        negative_count += 1
                    magnitude = abs(value)
                    if magnitude < first_min:
                        second_min = first_min
                        first_min = magnitude
                        first_edge = edge
                    elif magnitude < second_min:
                        second_min = magnitude
                for edge in range(start, stop):
                    magnitude = second_min if edge == first_edge else first_min
                    negative = (negative_count - (1 if v2c[edge] < 0 else 0) + syndrome[check]) % 2
                    c2v[edge] = -magnitude if negative else magnitude
        for variable in range(n):
            beliefs[variable] = prior_llrs[variable]
        for edge in range(len(variables)):
            beliefs[variables[edge]] += c2v[edge]
        for variable in range(n):
            beliefs[variable] = _clip(beliefs[variable], limit)
            candidate[variable] = 1 if (beliefs[variable] <= 0 if tie_break_one else beliefs[variable] < 0) else 0
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, True, iteration
        for edge in range(len(variables)):
            next_v2c[edge] = _clip(beliefs[variables[edge]] - c2v[edge], limit)
        v2c, next_v2c = next_v2c, v2c
    return candidate, False, max_iterations


@njit(cache=True)
def _decode_batch(
    row_ptr: np.ndarray, variables: np.ndarray, prior_llrs: np.ndarray,
    observable_matrix: np.ndarray, syndromes: np.ndarray, limit: float,
    max_iterations: int, rule: int, tie_break_one: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = len(syndromes)
    predictions = np.zeros((count, len(observable_matrix)), dtype=np.uint8)
    converged = np.zeros(count, dtype=np.uint8)
    iterations = np.zeros(count, dtype=np.int32)
    for shot in range(count):
        candidate, success, sweeps = _decode_one(
            row_ptr, variables, prior_llrs, syndromes[shot], limit, max_iterations, rule, tie_break_one,
        )
        converged[shot] = success
        iterations[shot] = sweeps
        for observable in range(len(observable_matrix)):
            parity = 0
            for variable in range(len(candidate)):
                parity ^= observable_matrix[observable, variable] & candidate[variable]
            predictions[shot, observable] = parity
    return predictions, converged, iterations
