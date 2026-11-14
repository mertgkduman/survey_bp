"""Qualified compiled controller for the Roffe float64 min-sum experiment.

All message arithmetic remains in the existing canonical sweep. This controller
only moves allocation, schedule traversal and syndrome stopping into one call.
It deliberately preserves the historical initial-message/update-prior distinction.
"""
import math

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _policy_sweep_into, _candidate_matches

VERSION = 'roffe-canonical-sweep-loop-v1'


@njit(cache=True)
def _run(row_ptr, variables, n, syndrome, initial, prior, cap, coefficients,
         scale, all_state, stabilization, epsilon):
    old = np.full(len(variables), initial, dtype=np.float64)
    new = np.empty_like(old)
    c2v = np.empty_like(old)
    beliefs = np.empty(n, dtype=np.float64)
    candidate = np.empty(n, dtype=np.uint8)
    for iteration in range(1, cap+1):
        weights = coefficients[min(iteration, len(coefficients))-1]
        _policy_sweep_into(row_ptr, variables, n, old, syndrome, prior,
                           2, scale, all_state, 1, weights[0], weights[1], weights[2], weights[3],
                           c2v, beliefs, candidate, new, stabilization, epsilon)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, beliefs, True, iteration
        old, new = new, old
    return candidate, beliefs, False, cap


class PreparedRoffeBp:
    """Bind only the qualified undamped, uniform binary Roffe configuration."""

    def __init__(self, base):
        job, self.n, _, graphs = base
        settings = job['decoder']
        if (settings['family'] != 'binary_css' or settings['noise_model'] != 'x_only'
                or settings['check_rule'] != 'min_sum' or settings['v2c_damping'] != 0
                or settings['alpha_schedule'] != '1-2**(-iteration)'
                or type(settings['max_iterations']) is not int or settings['max_iterations'] < 1):
            raise ValueError('compiled controller requires undamped binary Roffe min-sum')
        self.cap = settings['max_iterations']
        p = job['physical_p']
        if not 0 < p < .5:
            raise ValueError('compiled controller requires a finite binary prior below one half')
        graph = graphs[0]
        policy = graph.policy
        resolution = policy.resolution
        if (resolution.format_code != 2 or policy.zero_syndrome_shortcut
                or policy.version != 'bp-flooding-policy-v2' or graph.rule != 'min_sum'):
            raise ValueError('unsupported canonical policy for compiled controller')
        for other in graphs:
            if (other.table != graph.table or other.policy.resolution != resolution
                    or other.policy.stabilization_args != policy.stabilization_args
                    or other.policy.coefficients[:2] != (0., 1.) or other.policy.coefficients[3] != 0.):
                raise ValueError('incompatible graph or schedule in compiled controller')
        self.row_ptr, self.variables = graph.row_ptr, graph.variables
        self.initial = math.log((1-p)/p)
        self.prior = graph.bind_error_rate(p).prior
        self.coefficients = np.asarray([g.policy.coefficients for g in graphs], dtype=np.float64)
        self.scale, self.all_state = resolution.fixed_scale, resolution.scope == 'all_state'
        self.stabilization, self.epsilon = policy.stabilization_args

    def decode(self, syndrome):
        s = np.asarray(syndrome)
        if (s.shape != (len(self.row_ptr)-1,) or not np.issubdtype(s.dtype, np.integer)
                or np.any((s != 0) & (s != 1))):
            raise ValueError('invalid original binary syndrome')
        result = _run(self.row_ptr, self.variables, self.n, np.ascontiguousarray(s, dtype=np.uint8),
                      self.initial, self.prior, self.cap, self.coefficients, self.scale,
                      self.all_state, self.stabilization, self.epsilon)
        result[0].setflags(write=False)
        result[1].setflags(write=False)
        return result
