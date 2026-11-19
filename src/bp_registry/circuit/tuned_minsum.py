"""Flooding min-sum with damping, scaling and offset on the canonical sweep."""
from dataclasses import dataclass
import math

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _candidate_matches, _policy_sweep_into
from bp_registry.canonical.prior_tilt import PriorResult


@dataclass(frozen=True, slots=True)
class MinSumSpec:
    iterations: int = 18080
    damping: float = 0.0
    alpha: float = 1.0
    beta: float = 0.0

    def __post_init__(self):
        if type(self.iterations) is not int or not 1 <= self.iterations <= 100000:
            raise ValueError("invalid iteration limit")
        if not all(math.isfinite(x) for x in (self.damping, self.alpha, self.beta)):
            raise ValueError("nonfinite BP parameters")
        if not 0 <= self.damping < 1 or not 0 < self.alpha <= 1 or self.beta < 0:
            raise ValueError("invalid damping, scaling or offset")


@njit(cache=True)
def decode(rows, variables, prior, syndrome, cap, damping, alpha, beta):
    old = prior[variables].copy()
    new = np.empty_like(old)
    c2v = np.empty_like(old)
    posterior = prior.copy()
    candidate = np.empty(len(prior), np.uint8)
    converged = False
    working_prior = prior.copy()
    working_beta = beta
    rescales = 0
    # With no fixed unary magnitude, min-sum and the damping mix are
    # homogeneous in messages, priors and offset. Leave headroom for the
    # next sweep's incoming sum and lower the exponent by an exact power of two.
    scale_threshold = 2.0 ** 480
    scale_down = 2.0 ** -400
    for iteration in range(1, cap + 1):
        _policy_sweep_into(rows, variables, len(prior), old, syndrome, working_prior,
                           2, 1, False, 1, damping, 1.0 - damping, alpha, working_beta,
                           c2v, posterior, candidate, new, False, 1e-10)
        for v in range(len(prior)):
            if not math.isfinite(posterior[v]):
                raise ValueError("nonfinite BP posterior")
            candidate[v] = int(posterior[v] <= 0.0)
        peak = 0.0
        for e in range(len(new)):
            if not math.isfinite(new[e]):
                raise ValueError("nonfinite BP message")
            peak = max(peak, abs(new[e]))
        converged = _candidate_matches(rows, variables, candidate, syndrome)
        if converged or iteration == cap:
            break
        if peak >= scale_threshold:
            for e in range(len(new)):
                new[e] *= scale_down
            for v in range(len(working_prior)):
                working_prior[v] *= scale_down
            working_beta *= scale_down
            rescales += 1
        old, new = new, old
    return candidate, posterior, converged, iteration, rescales


class TunableMinSum:
    def __init__(self, model, spec):
        if np.any(np.diff(model.row_ptr) == 1):
            raise ValueError("scaled min-sum requires no fixed unary check magnitudes")
        self.model = model
        self.spec = spec

    def decode(self, syndrome, *, shot):
        model, spec = self.model, self.spec
        candidate, posterior, converged, iterations, rescales = decode(
            model.row_ptr, model.variables, model.prior_llrs,
            syndrome ^ model.syndrome_bias, spec.iterations, spec.damping, spec.alpha, spec.beta,
        )
        return PriorResult(candidate, posterior, converged, iterations,
                           2 * model.table.edge_count * iterations, np.empty((0, 8), np.int64), 0, 0, int(rescales))
