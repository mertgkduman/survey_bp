"""Study traversal only: all BP message equations use canonical sweep helpers."""
from dataclasses import replace
import math

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _policy_sweep_into as binary_sweep, _candidate_matches as binary_matches
from bp_registry.quaternary.compiled import _policy_sweep_into as pauli_sweep, _candidate_matches as pauli_matches

VERSION = 'roffe-joint-controls-loop-v1'


@njit(cache=True)
def binary_loop(row_ptr, variables, n, syndrome, initial, prior, cap, coefficients):
    old = np.full(len(variables), initial, dtype=np.float64)
    new, c2v = np.empty_like(old), np.empty_like(old)
    beliefs, candidate = np.empty(n, dtype=np.float64), np.empty(n, dtype=np.uint8)
    for iteration in range(1, cap+1):
        w = coefficients[min(iteration, len(coefficients))-1]
        binary_sweep(row_ptr, variables, n, old, syndrome, prior, 2, 1, False, 1,
                     w[0], w[1], w[2], w[3], c2v, beliefs, candidate, new, False, 1e-10)
        if binary_matches(row_ptr, variables, candidate, syndrome):
            return candidate, beliefs, True, iteration
        old, new = new, old
    return candidate, beliefs, False, cap


@njit(cache=True)
def pauli_loop(row_ptr, variable_ptr, variable_edges, variables, labels, priors,
               syndrome, cap, coefficients):
    n, edges = priors.shape[0], len(variables)
    old = priors[variables].copy()
    new = np.empty_like(old)
    comm, c2v = np.empty(edges, dtype=np.float64), np.empty(edges, dtype=np.float64)
    beliefs, candidate = np.empty_like(priors), np.empty(n, dtype=np.uint8)
    for iteration in range(1, cap+1):
        w = coefficients[min(iteration, len(coefficients))-1]
        pauli_sweep(row_ptr, variable_ptr, variable_edges, variables, labels, old, priors,
                    syndrome, 2, 1, 1, 1, w[0], w[1], w[2], w[3], 2,
                    comm, c2v, beliefs, new, candidate, False, 1e-10)
        if pauli_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, beliefs, True, iteration
        old, new = new, old
    return candidate, beliefs, False, cap


def coefficients(policy, controls):
    if set(controls) != {'damping', 'alpha', 'alpha_mode', 'beta'} or controls['alpha_mode'] not in {'paper', 'constant'}:
        raise ValueError('explicit damping, scale schedule/value and offset required')
    p = replace(policy, damping=controls['damping'], alpha=controls['alpha'], beta=controls['beta'])
    if controls['alpha_mode'] == 'paper':
        return np.array([replace(p, alpha=p.alpha*(1.-2.**-t)).coefficients for t in range(1, 55)])
    return np.array([p.coefficients])


class Prepared:
    def __init__(self, base, controls):
        self.job, self.n, self.packed, graphs = base
        self.graph, self.joint = graphs[0], self.job['decoder']['family'] == 'bp4'
        policy = self.graph.policy
        if (policy is None or policy.check_rule != 'min_sum' or policy.resolution.format != 'float64'
                or policy.resolution.scope != 'all_messages' or policy.zero_syndrome_shortcut
                or policy.version != 'bp-flooding-policy-v2' or policy.stabilization_args != (False, 1e-10)):
            raise ValueError('unsupported qualified canonical min-sum policy')
        if self.joint and policy.decision_code != 2:
            raise ValueError('joint study requires canonical MAP Pauli decisions')
        self.coefficients = coefficients(policy, controls)
        p = self.job['physical_p']
        self.initial = math.log((1-p)/p)
        self.prior = None if self.joint else self.graph.bind_error_rate(p).prior

    def decode(self, syndrome, cap):
        if type(cap) is not int or cap < 1:
            raise ValueError('positive integer iteration cap required')
        s = self.graph._syndrome(syndrome)
        g = self.graph
        result = (pauli_loop(g.row_ptr, g.variable_ptr, g.variable_edges, g.variables, g.labels,
                             g.prior_llrs, s, cap, self.coefficients) if self.joint else
                  binary_loop(g.row_ptr, g.variables, self.n, s, self.initial, self.prior, cap, self.coefficients))
        result[0].setflags(write=False); result[1].setflags(write=False)
        return result

    def public_reference(self, syndrome, cap):
        """Slow public sweeps for exact-state qualification, never timed as a competitor."""
        g = self.graph
        old = g.initial_v2c() if self.joint else np.full(len(g.variables), self.initial)
        for iteration in range(1, cap+1):
            w = self.coefficients[min(iteration, len(self.coefficients))-1]
            graph = replace(g, policy=replace(g.policy, damping=float(w[0]), alpha=float(w[2]), beta=float(w[3])))
            sweep = graph.sweep(old, syndrome, **({} if self.joint else {'error_rate': self.job['physical_p']}))
            old = sweep.v2c if self.joint else sweep.new_v2c
            candidate, beliefs = sweep.candidate, sweep.beliefs
            observed = (pauli_matches(g.row_ptr, g.variables, g.labels, candidate, syndrome) if self.joint else
                        binary_matches(g.row_ptr, g.variables, candidate, syndrome))
            if observed:
                return candidate, beliefs, True, iteration
        return candidate, beliefs, False, cap
