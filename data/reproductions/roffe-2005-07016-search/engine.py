"""Controlled CSS beam/relay traversal over the unchanged canonical BP sweep.

Import this module under the stable _roffe_search_engine name for Numba caches.
All masking, random-memory generation, pruning and candidate selection are
inside the measured decoder call. No simulation truth is an input.
"""
from dataclasses import dataclass, asdict
import math

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _policy_sweep_into, _candidate_matches

VERSION = 'canonical-css-search-traversal-v1'
MEMORY_BOUND = 1e6


@dataclass(frozen=True)
class Controls:
    method: str
    initial: int = 20
    per_unit: int = 20
    units: int = 16
    damping: float = .5
    alpha: float = 1.
    paper_scale: bool = True
    beta: float = 0.
    width: int = 2
    rounds: int = 8
    solutions: int = 1
    first_gamma: float = 0.
    gamma_low: float = -.24
    gamma_high: float = .66

    def __post_init__(self):
        if self.method not in ('beam', 'relay'):
            raise ValueError('beam or relay required')
        for key in ('initial', 'per_unit', 'units', 'width', 'rounds', 'solutions'):
            if type(getattr(self, key)) is not int or not 1 <= getattr(self, key) <= 4096:
                raise ValueError('positive bounded integer controls required')
        if type(self.paper_scale) is not bool:
            raise ValueError('explicit scaling schedule required')
        values = (self.damping, self.alpha, self.beta, self.first_gamma, self.gamma_low, self.gamma_high)
        if (not all(math.isfinite(x) for x in values) or not 0 <= self.damping < 1
                or not 0 < self.alpha <= 1.5 or not 0 <= self.beta <= 2
                or not -.75 <= self.gamma_low < self.gamma_high <= 1.
                or not -.75 <= self.first_gamma <= 1.):
            raise ValueError('invalid numerical or memory controls')

    def evidence(self):
        return asdict(self)


@njit(cache=True)
def uniform(seed, shot, leg, variable):
    """Indexed SplitMix64 stream, independent of control-dependent draw counts."""
    x = (np.uint64(seed) ^ (np.uint64(shot+1)*np.uint64(0x9e3779b97f4a7c15))
         ^ (np.uint64(leg+1)*np.uint64(0xd1b54a32d192ed03))
         ^ (np.uint64(variable+1)*np.uint64(0x94d049bb133111eb)))
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xbf58476d1ce4e5b9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94d049bb133111eb)
    x ^= x >> np.uint64(31)
    return float(x >> np.uint64(11)) * (1./9007199254740992.)


@njit(cache=True)
def segment(row_ptr, variables, n, syndrome, prior, fixed, inherited, start,
            gamma, cap, damping, alpha, paper_scale, beta):
    # Compact only active edges; original variable indices remain stable.
    rp = np.zeros(len(row_ptr), dtype=np.int64)
    vv = np.empty(len(variables), dtype=np.int64)
    mapping = np.empty(len(variables), dtype=np.int64)
    target = syndrome.copy()
    edges = 0
    for check in range(len(row_ptr)-1):
        for edge in range(row_ptr[check], row_ptr[check+1]):
            v = variables[edge]
            if fixed[v] < 0:
                vv[edges], mapping[edges] = v, edge
                edges += 1
            elif fixed[v] == 1:
                target[check] ^= np.uint8(1)
        rp[check+1] = edges
    vv = vv[:edges]
    old = np.empty(edges, dtype=np.float64)
    for e in range(edges):
        old[e] = inherited[mapping[e]]
    new, c2v = np.empty_like(old), np.empty_like(old)
    posterior = start.copy()
    effective = prior.copy()
    summed = np.zeros(n, dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    clips = 0
    done, valid = 0, False
    for t in range(1, cap+1):
        for v in range(n):
            value = (1.-gamma[v])*prior[v]+gamma[v]*posterior[v]
            bounded = min(MEMORY_BOUND, max(-MEMORY_BOUND, value))
            clips += int(value != bounded)
            effective[v] = bounded
        scale = alpha*(1.-2.**(-min(t, 54))) if paper_scale else alpha
        _policy_sweep_into(rp, vv, n, old, target, effective, 2, 1, False, 1,
                           damping, 1.-damping, scale, beta,
                           c2v, posterior, candidate, new, False, 1e-10)
        for v in range(n):
            if fixed[v] >= 0:
                candidate[v] = fixed[v]
            else:
                summed[v] += posterior[v]
        done = t
        old, new = new, old
        valid = _candidate_matches(row_ptr, variables, candidate, syndrome)
        if valid:
            break
    messages = inherited.copy()
    for e in range(edges):
        messages[mapping[e]] = old[e]
    return candidate, posterior, summed, messages, valid, done, edges, clips


@njit(cache=True)
def search(row_ptr, variables, n, syndrome, initial, prior, method, initial_cap,
           unit_cap, units, damping, alpha, paper_scale, beta, width, rounds,
           solutions, first_gamma, low, high, seed, shot):
    fixed = np.full(n, -1, dtype=np.int8)
    gamma = np.full(n, first_gamma if method == 1 else 0., dtype=np.float64)
    root = segment(row_ptr, variables, n, syndrome, prior, fixed,
                   np.full(len(variables), initial), prior, gamma, initial_cap,
                   damping, alpha, paper_scale, beta)
    # Trace: parent, masked variable/value, iterations, active edges, valid,
    # pruned, memory clips. Scores and complete posterior/message states are
    # returned separately for provenance hashing outside decoder timing.
    if root[4] and (method == 0 or solutions == 1):
        trace = np.array([[-1, -1, -1, root[5], root[6], 1, 0, root[7]]], dtype=np.int64)
        return root[0], root[1], True, 0, trace, np.array([0.]), root[1][None, :], root[3][None, :]
    trace = np.zeros((units+1, 8), dtype=np.int64)
    trace[0] = np.array([-1, -1, -1, root[5], root[6], int(root[4]), 0, root[7]])
    posts = np.empty((units+1, n), dtype=np.float64)
    messages = np.empty((units+1, len(variables)), dtype=np.float64)
    sums = np.empty((units+1, n), dtype=np.float64)
    masks = np.full((units+1, n), -1, dtype=np.int8)
    scores = np.zeros(units+1, dtype=np.float64)
    posts[0], messages[0], sums[0] = root[1], root[3], root[2]
    candidate, posterior = root[0], root[1]
    best, best_weight, valid_count = -1, 1e300, 0
    if root[4]:
        best, best_weight, valid_count = 0, float(np.dot(root[0].astype(np.float64), prior)), 1
    used = 0
    frontier = np.zeros(width, dtype=np.int64)
    frontier_count = 1
    for depth in range(rounds if method == 0 else units):
        children = np.empty(2*width, dtype=np.int64)
        child_count = 0
        for f in range(frontier_count if method == 0 else 1):
            parent = frontier[f] if method == 0 else used
            variable, reliability = -1, 1e300
            if method == 0:
                for v in range(n):
                    if masks[parent, v] < 0 and abs(sums[parent, v]) < reliability:
                        variable, reliability = v, abs(sums[parent, v])
                if variable < 0:
                    continue
            for bit in range(2 if method == 0 else 1):
                if used >= units:
                    break
                index = used+1
                masks[index] = masks[parent]
                if method == 0:
                    masks[index, variable] = bit
                    inherited = messages[parent]
                    gamma[:] = 0.
                else:
                    inherited = np.full(len(variables), initial)
                    for v in range(n):
                        gamma[v] = low+(high-low)*uniform(seed, shot, index, v)
                value = segment(row_ptr, variables, n, syndrome, prior, masks[index], inherited,
                                posts[parent], gamma, unit_cap, damping, alpha, paper_scale, beta)
                candidate, posterior = value[0], value[1]
                trace[index] = np.array([parent, variable, bit if method == 0 else -1,
                                         value[5], value[6], int(value[4]), 0, value[7]])
                posts[index], messages[index], sums[index] = value[1], value[3], value[2]
                for v in range(n):
                    if masks[index, v] < 0:
                        scores[index] += abs(value[2][v])/value[5]
                used = index
                if value[4]:
                    valid_count += 1
                    weight = float(np.dot(candidate.astype(np.float64), prior))
                    if weight < best_weight:
                        best, best_weight = index, weight
                    if valid_count >= solutions:
                        break
                elif method == 0:
                    children[child_count] = index
                    child_count += 1
            if used >= units or valid_count >= solutions:
                break
        if used >= units or valid_count >= solutions:
            break
        if method == 0:
            # Stable descending score, retaining earlier IDs on ties.
            for a in range(child_count):
                for b in range(a+1, child_count):
                    if (scores[children[b]] > scores[children[a]] or
                            (scores[children[b]] == scores[children[a]] and children[b] < children[a])):
                        children[a], children[b] = children[b], children[a]
            frontier_count = min(width, child_count)
            frontier[:frontier_count] = children[:frontier_count]
            for a in range(frontier_count, child_count):
                trace[children[a], 6] = 1
            if frontier_count == 0:
                break
    if best >= 0:
        posterior = posts[best].copy()
        candidate = (posterior < 0).astype(np.uint8)
        for v in range(n):
            if masks[best, v] >= 0:
                candidate[v] = masks[best, v]
    return candidate, posterior, best >= 0, best, trace[:used+1], scores[:used+1], posts[:used+1], messages[:used+1]


class Prepared:
    def __init__(self, graph, p, controls, seed):
        self.graph, self.controls, self.seed = graph, controls, seed
        self.n = graph.table.variable_count
        self.initial = math.log((1-p)/p)
        self.prior = np.full(self.n, graph.bind_error_rate(p).prior)

    def decode(self, syndrome, shot=0):
        if type(shot) is not int or shot < 0:
            raise ValueError('nonnegative public shot index required')
        s = self.graph._syndrome(syndrome)
        c = self.controls
        return search(self.graph.row_ptr, self.graph.variables, self.n, s, self.initial, self.prior,
                      int(c.method == 'relay'), c.initial, c.per_unit, c.units, c.damping, c.alpha,
                      c.paper_scale, c.beta, c.width, c.rounds, c.solutions, c.first_gamma,
                      c.gamma_low, c.gamma_high, self.seed, shot)
