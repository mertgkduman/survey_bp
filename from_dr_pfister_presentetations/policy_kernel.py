"""Experimental Q8 policy wrappers around project-owned compiled Tanner graphs.

This is a spike adapter, not a canonical publication backend. It reuses the
project's compiled graph indexing and BP4 commutation primitives while making
slide-omitted choices explicit: round-to-even after each public message,
variable-to-check damping, flooding, and syndrome-match stopping.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from bp_registry.quaternary.compiled import _anticommutes, _boxplus_pair, _commutation_llr


@njit(cache=True)
def _q(value: float, scale: int) -> float:
    bound = 127.0 / scale
    return min(bound, max(-bound, np.rint(value * scale) / scale))


@njit(cache=True)
def _bp4_matches(row_ptr, variables, labels, candidate, syndrome) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= int(_anticommutes(labels[edge], candidate[variables[edge]]))
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def decode_bp4(row_ptr, variable_ptr, variable_edges, variables, labels,
               prior_llrs, syndrome, max_iterations: int, scale: int,
               damping: float, min_sum: bool):
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if _bp4_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, True
    v2c = np.empty((edge_count, 3), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    bound = 127.0 / scale
    for edge in range(edge_count):
        for state in range(3):
            v2c[edge, state] = _q(prior_llrs[variables[edge], state], scale)
    for iteration in range(1, max_iterations + 1):
        for edge in range(edge_count):
            comm[edge] = _q(_commutation_llr(v2c[edge], labels[edge], bound), scale)
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                if min_sum:
                    magnitude = bound
                    negatives = int(syndrome[check])
                    for other in range(start, stop):
                        if other != edge:
                            magnitude = min(magnitude, abs(comm[other]))
                            negatives += int(comm[other] < 0.0)
                    message = -magnitude if negatives % 2 else magnitude
                else:
                    first = True
                    message = bound
                    for other in range(start, stop):
                        if other == edge:
                            continue
                        if first:
                            message = comm[other]
                            first = False
                        else:
                            message = _boxplus_pair(message, comm[other], bound)
                    if syndrome[check]:
                        message = -message
                c2v[edge] = _q(message, scale)
        for variable in range(n):
            for state in range(1, 4):
                value = prior_llrs[variable, state - 1]
                for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                    edge = variable_edges[position]
                    if _anticommutes(labels[edge], state):
                        value += c2v[edge]
                beliefs[variable, state - 1] = value
            x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
            if x > 0.0 and y > 0.0 and z > 0.0:
                candidate[variable] = 0
            elif x <= y and x <= z:
                candidate[variable] = 1
            elif y <= z:
                candidate[variable] = 2
            else:
                candidate[variable] = 3
        if _bp4_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        for edge in range(edge_count):
            variable, label = variables[edge], labels[edge]
            for state in range(1, 4):
                proposal = beliefs[variable, state - 1]
                if _anticommutes(label, state):
                    proposal -= c2v[edge]
                proposal = _q(proposal, scale)
                next_v2c[edge, state - 1] = _q(damping * v2c[edge, state - 1] + (1.0 - damping) * proposal, scale)
        v2c, next_v2c = next_v2c, v2c
    return candidate, max_iterations, False


@njit(cache=True)
def decode_bp4_variable_serial(row_ptr, variable_ptr, variable_edges, edge_checks,
                               variables, labels, prior_llrs, syndrome,
                               max_iterations: int, scale: int, damping: float):
    """Diagnostic alternate schedule: refresh one variable before the next."""
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if _bp4_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, True
    v2c = np.empty((edge_count, 3), dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    bound = 127.0 / scale
    for edge in range(edge_count):
        for state in range(3):
            v2c[edge, state] = _q(prior_llrs[variables[edge], state], scale)
    for iteration in range(1, max_iterations + 1):
        for variable in range(n):
            start_v, stop_v = variable_ptr[variable], variable_ptr[variable + 1]
            for position in range(start_v, stop_v):
                edge = variable_edges[position]
                check = edge_checks[edge]
                first = True
                message = bound
                for other in range(row_ptr[check], row_ptr[check + 1]):
                    if other == edge:
                        continue
                    incoming = _q(_commutation_llr(v2c[other], labels[other], bound), scale)
                    if first:
                        message = incoming
                        first = False
                    else:
                        message = _boxplus_pair(message, incoming, bound)
                if syndrome[check]:
                    message = -message
                c2v[edge] = _q(message, scale)
            for state in range(1, 4):
                value = prior_llrs[variable, state - 1]
                for position in range(start_v, stop_v):
                    edge = variable_edges[position]
                    if _anticommutes(labels[edge], state):
                        value += c2v[edge]
                beliefs[variable, state - 1] = value
            x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
            if x > 0.0 and y > 0.0 and z > 0.0:
                candidate[variable] = 0
            elif x <= y and x <= z:
                candidate[variable] = 1
            elif y <= z:
                candidate[variable] = 2
            else:
                candidate[variable] = 3
            for position in range(start_v, stop_v):
                edge = variable_edges[position]
                label = labels[edge]
                for state in range(1, 4):
                    proposal = beliefs[variable, state - 1]
                    if _anticommutes(label, state):
                        proposal -= c2v[edge]
                    proposal = _q(proposal, scale)
                    v2c[edge, state - 1] = _q(damping * v2c[edge, state - 1] + (1.0 - damping) * proposal, scale)
        if _bp4_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
    return candidate, max_iterations, False


@njit(cache=True)
def _binary_matches(row_ptr, variables, candidate, syndrome) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= candidate[variables[edge]]
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def decode_binary_oms(row_ptr, variables, n: int, syndrome, prior: float,
                      max_iterations: int, scale: int, damping: float,
                      alpha: float, beta: float):
    candidate = np.zeros(n, dtype=np.uint8)
    if _binary_matches(row_ptr, variables, candidate, syndrome):
        return candidate, 0, True
    edge_count = len(variables)
    v2c = np.full(edge_count, _q(prior, scale), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    c2v = np.empty_like(v2c)
    beliefs = np.empty(n, dtype=np.float64)
    bound = 127.0 / scale
    for iteration in range(1, max_iterations + 1):
        for check in range(len(row_ptr) - 1):
            start, stop = row_ptr[check], row_ptr[check + 1]
            for edge in range(start, stop):
                magnitude = bound
                negatives = int(syndrome[check])
                for other in range(start, stop):
                    if other != edge:
                        magnitude = min(magnitude, abs(v2c[other]))
                        negatives += int(v2c[other] < 0.0)
                magnitude = alpha * max(0.0, magnitude - beta)
                c2v[edge] = _q(-magnitude if negatives % 2 else magnitude, scale)
        beliefs.fill(prior)
        for edge in range(edge_count):
            beliefs[variables[edge]] += c2v[edge]
        for variable in range(n):
            candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
        if _binary_matches(row_ptr, variables, candidate, syndrome):
            return candidate, iteration, True
        for edge in range(edge_count):
            proposal = _q(beliefs[variables[edge]] - c2v[edge], scale)
            next_v2c[edge] = _q(damping * v2c[edge] + (1.0 - damping) * proposal, scale)
        v2c, next_v2c = next_v2c, v2c
    return candidate, max_iterations, False


def binary_prior(p: float) -> float:
    marginal = 2.0 * p / 3.0
    return math.log((1.0 - marginal) / marginal)
