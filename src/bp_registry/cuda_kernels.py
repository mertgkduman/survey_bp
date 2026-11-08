"""CUDA realization of the float64 flooding contract; one block per shot.

Check/variable reductions retain canonical edge order. No floating point atomics
or fast math are used. Only integer status flags are reduced across threads.
"""
import math
from numba import cuda, int32
from .check_numerics import stable_boxplus

_boxplus = cuda.jit(device=True)(stable_boxplus)


@cuda.jit(device=True)
def _logaddexp(a, b):
    maximum = max(a, b)
    return maximum + math.log(math.exp(a - maximum) + math.exp(b - maximum))


@cuda.jit(device=True)
def _decision(x, y, z, code):
    if code == 2:
        best, result = 0.0, 0
        if x < best:
            best, result = x, 1
        if y < best:
            best, result = y, 2
        if z < best:
            result = 3
        return result
    if x > 0 and y > 0 and z > 0:
        return 0
    if code == 0:
        return 1 if x <= y and x <= z else 2 if y <= z else 3
    return 1 if x < y and x < z else 3 if z < x and z < y else 2


@cuda.jit(device=True)
def _finite(value, status):
    if not math.isfinite(value):
        cuda.atomic.max(status, 1, 1)
        return 0.0
    return value


@cuda.jit
def flooding(rows, var_ptr, var_edges, variables, labels, prior, syndromes,
             max_iterations, min_sum, old_weight, fresh_weight, alpha, beta,
             epsilon, decision_code, shortcut, stop_on_convergence,
             old, comm, prefix, c2v, beliefs, candidates, iterations, valid, failures):
    shot, tid, stride = cuda.blockIdx.x, cuda.threadIdx.x, cuda.blockDim.x
    n, states, edges = prior.shape[0], prior.shape[1], len(variables)
    status = cuda.shared.array(2, int32)
    if tid == 0:
        status[0], status[1] = 0, 0
        iterations[shot] = 0
    for v in range(tid, n, stride):
        candidates[shot, v] = int(prior[v, 0] < 0) if states == 1 else _decision(
            prior[v, 0], prior[v, 1], prior[v, 2], decision_code)
    for e in range(tid, edges, stride):
        for state in range(states):
            old[shot, e, state] = prior[variables[e], state]
    cuda.syncthreads()
    for iteration in range(max_iterations + 1):
        # Check initial/final decision at one uniform block boundary.
        for check in range(tid, len(rows) - 1, stride):
            parity = 0
            for e in range(rows[check], rows[check + 1]):
                candidate = candidates[shot, variables[e]]
                parity ^= int(candidate != 0 and (states == 1 or candidate != labels[e]))
            if parity != syndromes[shot, check]:
                cuda.atomic.max(status, 0, 1)
        cuda.syncthreads()
        stop_now = (status[1] != 0 or iteration == max_iterations or
                    (stop_on_convergence and status[0] == 0 and (iteration > 0 or shortcut)))
        # Every thread must read the completed status before thread zero can
        # reset it. Otherwise even a uniform termination condition can race.
        cuda.syncthreads()
        if stop_now:
            if tid == 0:
                valid[shot] = status[0] == 0
                iterations[shot] = iteration
                failures[shot] = status[1]
            return
        if tid == 0:
            status[0] = 0
        for e in range(tid, edges, stride):
            if states == 1:
                projected = old[shot, e, 0]
            else:
                x, y, z = old[shot, e, 0], old[shot, e, 1], old[shot, e, 2]
                label = labels[e]
                if label == 1:
                    projected = _logaddexp(0.0, -x) - _logaddexp(-y, -z)
                elif label == 2:
                    projected = _logaddexp(0.0, -y) - _logaddexp(-x, -z)
                else:
                    projected = _logaddexp(0.0, -z) - _logaddexp(-x, -y)
            comm[shot, e] = _finite(projected, status)
        cuda.syncthreads()
        for check in range(tid, len(rows) - 1, stride):
            start, stop = rows[check], rows[check + 1]
            if min_sum:
                first, second, minimum, negatives = math.inf, math.inf, -1, 0
                for e in range(start, stop):
                    value = comm[shot, e]
                    magnitude = abs(value)
                    negatives += int(value < 0)
                    if magnitude < first:
                        second, first, minimum = first, magnitude, e
                    elif magnitude < second:
                        second = magnitude
                for e in range(start, stop):
                    magnitude = second if e == minimum else first
                    if stop - start == 1:
                        magnitude = 23.7189981105
                    value = alpha * max(0.0, magnitude - beta)
                    if (int(syndromes[shot, check]) + negatives - int(comm[shot, e] < 0)) % 2:
                        value = -value
                    c2v[shot, e] = _finite(value, status)
            else:
                accumulated = math.inf
                for e in range(start, stop):
                    prefix[shot, e] = accumulated
                    accumulated = _boxplus(accumulated, comm[shot, e])
                suffix = math.inf
                for e in range(stop - 1, start - 1, -1):
                    value = (math.log1p(1.0 - epsilon) - math.log(epsilon) if stop - start == 1
                             else _boxplus(prefix[shot, e], suffix))
                    c2v[shot, e] = _finite(-value if syndromes[shot, check] else value, status)
                    suffix = _boxplus(comm[shot, e], suffix)
        cuda.syncthreads()
        for v in range(tid, n, stride):
            for state in range(states):
                value = prior[v, state]
                for position in range(var_ptr[v], var_ptr[v + 1]):
                    e = var_edges[position]
                    if states == 1 or labels[e] != state + 1:
                        value += c2v[shot, e]
                beliefs[shot, v, state] = _finite(value, status)
            candidates[shot, v] = int(beliefs[shot, v, 0] < 0) if states == 1 else _decision(
                beliefs[shot, v, 0], beliefs[shot, v, 1], beliefs[shot, v, 2], decision_code)
        cuda.syncthreads()
        for e in range(tid, edges, stride):
            v = variables[e]
            for state in range(states):
                proposal = beliefs[shot, v, state]
                if states == 1 or labels[e] != state + 1:
                    proposal -= c2v[shot, e]
                proposal = _finite(proposal, status)
                old[shot, e, state] = _finite(
                    old_weight * old[shot, e, state] + fresh_weight * proposal, status)
        cuda.syncthreads()
