"""Compiled heterogeneous-prior execution of existing flooding policies."""
import numpy as np
from numba import njit

from bp_registry.resolution import round_message
from .compiled import _policy_sweep_into, _candidate_matches


@njit(cache=True)
def decode_vector_policy(row_ptr, variables, prior, syndrome, max_iterations,
                         format_code, scale, all_state, check_rule,
                         old_weight, fresh_weight, alpha, beta,
                         shortcut, stabilization, epsilon):
    n = len(prior)
    beliefs = prior.copy()
    candidate = np.empty(n, dtype=np.uint8)
    for v in range(n):
        if all_state:
            beliefs[v] = round_message(beliefs[v], format_code, scale)
        candidate[v] = int(beliefs[v] < 0.0)
    if shortcut and _candidate_matches(row_ptr, variables, candidate, syndrome):
        return candidate, beliefs, 0, True
    old = np.empty(len(variables))
    for e in range(len(variables)):
        old[e] = round_message(prior[variables[e]], format_code, scale)
    new, c2v = np.empty_like(old), np.empty_like(old)
    for iteration in range(1, max_iterations + 1):
        _policy_sweep_into(row_ptr, variables, n, old, syndrome, prior,
                           format_code, scale, all_state, check_rule,
                           old_weight, fresh_weight, alpha, beta,
                           c2v, beliefs, candidate, new, stabilization, epsilon)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, beliefs, iteration, True
        old, new = new, old
    return candidate, beliefs, max_iterations, _candidate_matches(row_ptr, variables, candidate, syndrome)
