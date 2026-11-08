"""Compiled ordinary fault-space attempts; the scalar schedules remain the oracle."""
import math
import numpy as np
from numba import njit
from bp_registry.canonical.compiled import _candidate_matches, _v2_sweep_into, _clip
from bp_registry.check_numerics import minsum_summary


@njit(cache=True)
def decode_attempt(rows, variables, prior, syndrome, max_iterations, rule, parameter):
    n, edges = len(prior), len(variables)
    old = np.empty(edges, np.float64)
    new, c2v = np.empty_like(old), np.empty_like(old)
    posterior = prior.copy()
    candidate = (prior < 0).astype(np.uint8)
    for e in range(edges):
        value = prior[variables[e]]
        old[e] = value if rule == 0 else _clip(value, 25.0)
    if _candidate_matches(rows, variables, candidate, syndrome):
        return candidate, posterior, 0, True
    for iteration in range(1, max_iterations + 1):
        if rule == 0:
            # Exact-unity SPA v3, including its 0.1 old-message damping.
            _v2_sweep_into(rows, variables, n, old, syndrome, prior, math.inf,
                           1e-10, .1, c2v, posterior, candidate, new)
        else:
            for check in range(len(rows) - 1):
                start, stop = rows[check], rows[check + 1]
                first, second, minimum, negatives = minsum_summary(old, start, stop)
                for e in range(start, stop):
                    magnitude = 25.0 if stop - start == 1 else second if e == minimum else first
                    if rule == 2:
                        magnitude *= parameter
                    elif rule == 3:
                        magnitude = max(0.0, magnitude - parameter)
                    message = -magnitude if (int(syndrome[check]) + negatives - int(old[e] < 0)) % 2 else magnitude
                    c2v[e] = _clip(message, 25.0)
            posterior[:] = prior
            for e in range(edges):
                posterior[variables[e]] += c2v[e]
            for v in range(n):
                if not math.isfinite(posterior[v]):
                    raise ValueError("nonfinite circuit posterior")
                posterior[v] = _clip(posterior[v], 25.0)
                candidate[v] = int(posterior[v] < 0)
            for e in range(edges):
                new[e] = _clip(posterior[variables[e]] - c2v[e], 25.0)
        if _candidate_matches(rows, variables, candidate, syndrome):
            return candidate, posterior, iteration, True
        old, new = new, old
    return candidate, posterior, max_iterations, _candidate_matches(rows, variables, candidate, syndrome)
