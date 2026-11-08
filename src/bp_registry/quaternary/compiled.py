"""Optional compiled plain BP4 prototype with project-owned Pauli semantics.

This backend is for development qualification. It does not participate in
budget reservation, event ledgers, or publication execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from bp_registry.check_numerics import stabilized_log_ratio, minsum_summary, tanh_factors

import numpy as np
from numba import njit

from bp_registry.css import CssCode
from bp_registry.compiled_contracts import csr_pointer, integer_vector, immutable_array
from bp_registry.resolution import BpFloodingPolicy, DEFAULT_BP4_MIN_SUM, round_message

from .algebra import Pauli
from .kernel import _priors
from .numerics import (
    DEFAULT_QBP4_F64, QuaternaryNumericalProfileV3,
    QBP4_F64_V1, QBP4_F64_V2, QuaternaryNumericalProfile,
    QuaternaryNumericalProfileV2, probabilities_to_llrs,
)
from .problems import PauliCode


@njit(cache=True)
def _map_pauli(x, y, z):
    best, state = 0.0, 0
    for index, value in enumerate((x, y, z)):
        if value < best:
            best, state = value, index + 1
    return state


@njit(cache=True)
def _clip(value: float, limit: float) -> float:
    return min(limit, max(-limit, value))


@njit(cache=True)
def _logaddexp(left: float, right: float) -> float:
    return max(left, right) + math.log1p(math.exp(-abs(left - right)))


@njit(cache=True)
def _boxplus_pair(left: float, right: float, limit: float) -> float:
    left = _clip(left, limit)
    right = _clip(right, limit)
    smaller, larger = min(abs(left), abs(right)), max(abs(left), abs(right))
    sign = -1.0 if left * right < 0.0 else 1.0
    correction = math.log1p(math.exp(-(smaller + larger))) - math.log1p(math.exp(-(larger - smaller)))
    return _clip(sign * (smaller + correction), limit)


@njit(cache=True)
def _anticommutes(label: int, state: int) -> bool:
    # I=0, X=1, Y=2, Z=3; symplectic anticommutation is exactly
    # "both are distinct nonidentity Paulis" for one qubit.
    return label != 0 and state != 0 and label != state


@njit(cache=True)
def _commutation_llr(values: np.ndarray, label: int, limit: float) -> float:
    x, y, z = _clip(values[0], limit), _clip(values[1], limit), _clip(values[2], limit)
    if label == 1:
        commute, anti = _logaddexp(0.0, -x), _logaddexp(-y, -z)
    elif label == 2:
        commute, anti = _logaddexp(0.0, -y), _logaddexp(-x, -z)
    else:
        commute, anti = _logaddexp(0.0, -z), _logaddexp(-x, -y)
    return _clip(_clip(commute, limit) - _clip(anti, limit), limit)


@njit(cache=True)
def _candidate_matches(
    row_ptr: np.ndarray, variables: np.ndarray, labels: np.ndarray,
    candidate: np.ndarray, syndrome: np.ndarray,
) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= int(_anticommutes(labels[edge], candidate[variables[edge]]))
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def _sweep(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, old_v2c: np.ndarray,
    prior_llrs: np.ndarray, syndrome: np.ndarray, limit: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n, edge_count = prior_llrs.shape[0], len(labels)
    quantized = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    new_v2c = np.empty((edge_count, 3), dtype=np.float64)
    candidate = np.empty(n, dtype=np.uint8)
    marginals = np.empty((n, 4), dtype=np.float64)
    _sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, old_v2c,
                prior_llrs, syndrome, limit, quantized, c2v, beliefs, new_v2c, candidate)
    _normalize_marginals(beliefs, marginals)
    return c2v, new_v2c, beliefs, marginals, candidate, quantized


@njit(cache=True)
def _sweep_into(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, old_v2c: np.ndarray,
    prior_llrs: np.ndarray, syndrome: np.ndarray, limit: float,
    quantized: np.ndarray, c2v: np.ndarray, beliefs: np.ndarray,
    new_v2c: np.ndarray, candidate: np.ndarray,
) -> None:
    n, edge_count = prior_llrs.shape[0], len(labels)
    for edge in range(edge_count):
        quantized[edge] = _commutation_llr(old_v2c[edge], labels[edge], limit)
    for check in range(len(row_ptr) - 1):
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            first = True
            message = limit
            for other in range(row_ptr[check], row_ptr[check + 1]):
                if other == edge:
                    continue
                if first:
                    message = quantized[other]
                    first = False
                else:
                    message = _boxplus_pair(message, quantized[other], limit)
            message = _clip(message, limit)
            if syndrome[check]:
                message = -message
            c2v[edge] = _clip(message, limit)
    for variable in range(n):
        for state in range(3):
            beliefs[variable, state] = prior_llrs[variable, state]
        for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
            edge = variable_edges[position]
            label = labels[edge]
            for state in range(1, 4):
                if _anticommutes(label, state):
                    beliefs[variable, state - 1] += c2v[edge]
        for state in range(3):
            beliefs[variable, state] = _clip(beliefs[variable, state], limit)
    for edge in range(edge_count):
        variable, label = variables[edge], labels[edge]
        for state in range(1, 4):
            value = beliefs[variable, state - 1]
            if _anticommutes(label, state):
                value -= c2v[edge]
            new_v2c[edge, state - 1] = _clip(value, limit)
    for variable in range(n):
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        if x > 0.0 and y > 0.0 and z > 0.0:
            candidate[variable] = 0
        elif x <= y and x <= z:
            candidate[variable] = 1
        elif y <= z:
            candidate[variable] = 2
        else:
            candidate[variable] = 3


@njit(cache=True)
def _normalize_marginals(beliefs: np.ndarray, marginals: np.ndarray) -> None:
    weights = np.empty(4, dtype=np.float64)
    for variable in range(len(beliefs)):
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        weights[0], weights[1], weights[2], weights[3] = 0.0, -x, -y, -z
        maximum = max(weights[0], weights[1], weights[2], weights[3])
        total = 0.0
        for state in range(4):
            weights[state] = math.exp(weights[state] - maximum)
            total += weights[state]
        for state in range(4):
            marginals[variable, state] = weights[state] / total


@njit(cache=True)
def _decode(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, prior_llrs: np.ndarray,
    syndrome: np.ndarray, limit: float, max_iterations: int, stop_on_convergence: bool,
) -> tuple[np.ndarray, int, bool]:
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, True
    v2c = np.empty((edge_count, 3), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    quantized = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    for edge in range(edge_count):
        for state in range(3):
            v2c[edge, state] = prior_llrs[variables[edge], state]
    for iteration in range(1, max_iterations + 1):
        _sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, v2c,
                    prior_llrs, syndrome, limit, quantized, c2v, beliefs, next_v2c, candidate)
        if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        v2c, next_v2c = next_v2c, v2c
    return candidate, max_iterations, _candidate_matches(row_ptr, variables, labels, candidate, syndrome)


@njit(cache=True)
def _v2_check(comm: np.ndarray, start: int, stop: int, target: int,
              syndrome_bit: int, cap: float, epsilon: float, precomputed: bool = False) -> float:
    product = -1.0 if syndrome_bit else 1.0
    for other in range(start, stop):
        if other == target:
            continue
        value = comm[other]
        factor = value if precomputed else (1.0 if value > 40.0 else -1.0 if value < -40.0 else math.tanh(value / 2.0))
        product *= factor
    value = stabilized_log_ratio(product, epsilon)
    if not math.isfinite(value):
        raise ValueError("nonfinite v2 check message")
    return _clip(value, cap)


@njit(cache=True)
def _v2_sweep_into(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, old_v2c: np.ndarray,
    prior_llrs: np.ndarray, syndrome: np.ndarray, cap: float, epsilon: float,
    damping: float, comm: np.ndarray, c2v: np.ndarray, beliefs: np.ndarray,
    new_v2c: np.ndarray, candidate: np.ndarray, corrected: bool = False,
) -> None:
    for edge in range(len(labels)):
        values, label = old_v2c[edge], labels[edge]
        x, y, z = values[0], values[1], values[2]
        if label == 1:
            comm[edge] = _logaddexp(0.0, -x) - _logaddexp(-y, -z)
        elif label == 2:
            comm[edge] = _logaddexp(0.0, -y) - _logaddexp(-x, -z)
        else:
            comm[edge] = _logaddexp(0.0, -z) - _logaddexp(-x, -y)
        if not math.isfinite(comm[edge]):
            raise ValueError("nonfinite v2 BP4 edge projection")
    factors = tanh_factors(comm)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        for edge in range(start, stop):
            c2v[edge] = _v2_check(factors, start, stop, edge, int(syndrome[check]), cap, epsilon, True)
    for variable in range(prior_llrs.shape[0]):
        for state in range(1, 4):
            value = prior_llrs[variable, state - 1]
            for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                edge = variable_edges[position]
                if labels[edge] != state:
                    value += c2v[edge]
            if not math.isfinite(value):
                raise ValueError("nonfinite v2 BP4 posterior")
            beliefs[variable, state - 1] = value
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        if corrected:
            candidate[variable] = _map_pauli(x, y, z)
        elif x > 0.0 and y > 0.0 and z > 0.0:
            candidate[variable] = 0
        elif x < y and x < z:
            candidate[variable] = 1
        elif z < x and z < y:
            candidate[variable] = 3
        else:
            candidate[variable] = 2
    for edge in range(len(labels)):
        variable, label = variables[edge], labels[edge]
        for state in range(1, 4):
            proposal = beliefs[variable, state - 1]
            if label != state:
                proposal -= c2v[edge]
            value = damping * old_v2c[edge, state - 1] + (1.0 - damping) * proposal
            if not math.isfinite(value):
                raise ValueError("nonfinite v2 BP4 V2C")
            new_v2c[edge, state - 1] = value


@njit(cache=True)
def _decode_v2(
    row_ptr: np.ndarray, variable_ptr: np.ndarray, variable_edges: np.ndarray,
    variables: np.ndarray, labels: np.ndarray, prior_llrs: np.ndarray,
    syndrome: np.ndarray, max_iterations: int, cap: float, epsilon: float,
    damping: float, stop_on_convergence: bool, corrected: bool = False,
) -> tuple[np.ndarray, int, bool]:
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if corrected:
        for variable in range(n):
            candidate[variable] = _map_pauli(prior_llrs[variable, 0], prior_llrs[variable, 1], prior_llrs[variable, 2])
    old = prior_llrs[variables].copy()
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    for iteration in range(1, max_iterations + 1):
        _v2_sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, old,
                       prior_llrs, syndrome, cap, epsilon, damping, comm, c2v,
                       beliefs, new, candidate, corrected)
        if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        old, new = new, old
    return candidate, max_iterations, _candidate_matches(row_ptr, variables, labels, candidate, syndrome)


@njit(cache=True)
def _policy_sweep_into(
    row_ptr, variable_ptr, variable_edges, variables, labels, old_v2c,
    prior_llrs, syndrome, format_code, scale, scope, check_rule,
    old_weight, fresh_weight, alpha, beta, hard_decision,
    comm, c2v, beliefs, new_v2c, candidate, clamp_band=True, epsilon=1e-10,
):
    """Corrected MS: exact four-state projection before scalar rounding."""
    edge_count = len(labels)
    for edge in range(edge_count):
        values, label = old_v2c[edge], labels[edge]
        x, y, z = values[0], values[1], values[2]
        if label == 1:
            projected = _logaddexp(0.0, -x) - _logaddexp(-y, -z)
        elif label == 2:
            projected = _logaddexp(0.0, -y) - _logaddexp(-x, -z)
        else:
            projected = _logaddexp(0.0, -z) - _logaddexp(-x, -y)
        comm[edge] = round_message(projected, format_code, scale)
    fixed_bound = ((2 ** ((8 if format_code == 3 else 16 if format_code == 4 else 32) - 1) - 1) / scale
                   if format_code >= 3 else math.inf)
    check_values = comm if check_rule == 1 else tanh_factors(comm)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        if check_rule == 1:
            first, second, minimum_edge, negative_count = minsum_summary(comm, start, stop)
        for edge in range(start, stop):
            if check_rule == 1:
                magnitude = min(fixed_bound, second if edge == minimum_edge else first)
                negatives = int(syndrome[check]) + negative_count - int(comm[edge] < 0.0)
                if stop - start == 1 and format_code < 3:
                    magnitude = 23.7189981105
                message = alpha * max(0.0, magnitude - beta)
                if negatives % 2:
                    message = -message
            else:
                product = -1.0 if syndrome[check] else 1.0
                for other in range(start, stop):
                    if other != edge:
                        product *= check_values[other]
                message = stabilized_log_ratio(product, epsilon, clamp_band)
            c2v[edge] = round_message(message, format_code, scale)
    for variable in range(prior_llrs.shape[0]):
        for state in range(1, 4):
            value = prior_llrs[variable, state - 1]
            for position in range(variable_ptr[variable], variable_ptr[variable + 1]):
                edge = variable_edges[position]
                if _anticommutes(labels[edge], state):
                    value += c2v[edge]
            beliefs[variable, state - 1] = round_message(value, format_code, scale) if scope == 2 else value
        x, y, z = beliefs[variable, 0], beliefs[variable, 1], beliefs[variable, 2]
        if hard_decision == 2:
            candidate[variable] = _map_pauli(x, y, z)
        elif x > 0.0 and y > 0.0 and z > 0.0:
            candidate[variable] = 0
        elif hard_decision == 0:
            if x <= y and x <= z:
                candidate[variable] = 1
            elif y <= z:
                candidate[variable] = 2
            else:
                candidate[variable] = 3
        elif x < y and x < z:
            candidate[variable] = 1
        elif z < x and z < y:
            candidate[variable] = 3
        else:
            candidate[variable] = 2
    for edge in range(edge_count):
        variable, label = variables[edge], labels[edge]
        for state in range(1, 4):
            proposal = beliefs[variable, state - 1]
            if _anticommutes(label, state):
                proposal -= c2v[edge]
            if scope >= 1:
                proposal = round_message(proposal, format_code, scale)
            value = old_weight * old_v2c[edge, state - 1] + fresh_weight * proposal
            new_v2c[edge, state - 1] = round_message(value, format_code, scale) if scope >= 1 else value


@njit(cache=True)
def _decode_policy(row_ptr, variable_ptr, variable_edges, variables, labels,
                   prior_llrs, syndrome, max_iterations, format_code, scale, scope,
                   check_rule, old_weight, fresh_weight, alpha, beta,
                   hard_decision, zero_shortcut, stop_on_convergence, clamp_band=True, epsilon=1e-10, corrected=False):
    n, edge_count = prior_llrs.shape[0], len(labels)
    candidate = np.zeros(n, dtype=np.uint8)
    if corrected:
        for variable in range(n):
            values = prior_llrs[variable].copy()
            if scope == 2:
                for state in range(3):
                    values[state] = round_message(values[state], format_code, scale)
            x, y, z = values[0], values[1], values[2]
            if hard_decision == 2:
                candidate[variable] = _map_pauli(x, y, z)
            elif x > 0 and y > 0 and z > 0:
                candidate[variable] = 0
            elif hard_decision == 0:
                candidate[variable] = 1 if x <= y and x <= z else 2 if y <= z else 3
            else:
                candidate[variable] = 1 if x < y and x < z else 3 if z < x and z < y else 2
    if zero_shortcut and stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, True
    old = np.empty((edge_count, 3), dtype=np.float64)
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    for edge in range(edge_count):
        for state in range(3):
            value = prior_llrs[variables[edge], state]
            old[edge, state] = round_message(value, format_code, scale) if scope >= 1 else value
    for iteration in range(1, max_iterations + 1):
        _policy_sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels,
                           old, prior_llrs, syndrome, format_code, scale, scope,
                           check_rule, old_weight, fresh_weight, alpha, beta,
                           hard_decision, comm, c2v, beliefs, new, candidate, clamp_band, epsilon)
        if stop_on_convergence and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, iteration, True
        old, new = new, old
    return candidate, max_iterations, _candidate_matches(row_ptr, variables, labels, candidate, syndrome)


@dataclass(frozen=True)
class CompiledBp4Sweep:
    c2v: np.ndarray
    v2c: np.ndarray
    beliefs: np.ndarray
    marginals: np.ndarray
    candidate: np.ndarray
    converged: bool


@dataclass(frozen=True)
class CompiledBp4Result:
    candidate: np.ndarray
    iterations: int
    converged: bool


@dataclass(frozen=True)
class CompiledQbpgdResult:
    """Development-only persistent-message Q-BPGD result."""

    candidate: np.ndarray
    iterations: int
    rounds: int
    fixations: int
    converged: bool


@njit(cache=True)
def _decode_qbpgd_v2(
    row_ptr, variable_ptr, variable_edges, variables, labels, original_priors,
    syndrome, iterations_per_round, epsilon_fix, max_rounds, cap, product_epsilon, damping,
):
    """Algorithm 3 blocks with the same persistent V2C and prior-update order as QbpgdController."""
    n, edge_count = original_priors.shape[0], len(labels)
    priors = original_priors.copy()
    old = priors[variables].copy()
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    marginals = np.empty((n, 4), dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    eligible = np.ones(n, dtype=np.uint8)
    sweeps = 0
    fixations = 0
    for round_index in range(max_rounds):
        for _ in range(iterations_per_round):
            _v2_sweep_into(row_ptr, variable_ptr, variable_edges, variables, labels, old,
                           priors, syndrome, cap, product_epsilon, damping,
                           comm, c2v, beliefs, new, candidate)
            old, new = new, old
            sweeps += 1
        if _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, sweeps, round_index + 1, fixations, True
        _normalize_marginals(beliefs, marginals)
        target = -1
        pauli = 0
        reliability = -1.0
        for variable in range(n):
            if eligible[variable] == 0:
                continue
            for state in range(4):
                value = marginals[variable, state]
                if value > reliability:
                    target = variable
                    pauli = state
                    reliability = value
        if target < 0:
            return candidate, sweeps, round_index + 1, fixations, False
        eligible[target] = 0
        # The canonical controller normalizes raw (1-epsilon, epsilon, ...).
        total = 1.0 + 2.0 * epsilon_fix
        for state in range(1, 4):
            probability = (1.0 - epsilon_fix if state == pauli else epsilon_fix) / total
            identity = (1.0 - epsilon_fix if pauli == 0 else epsilon_fix) / total
            priors[target, state - 1] = math.log(identity / probability)
        fixations += 1
    return candidate, sweeps, max_rounds, fixations, False


@njit(cache=True)
def _decode_qbpgd_policy(
    row_ptr, variable_ptr, variable_edges, variables, labels, original_priors,
    syndrome, iterations_per_round, epsilon_fix, max_rounds,
    format_code, scale, scope, check_rule, old_weight, fresh_weight, alpha,
    beta, hard_decision, zero_shortcut,
):
    """Q-BPGD's intervention loop using the shared policy flooding sweep.

    The controller continues to own fixation and its persistent changed prior.
    It deliberately delegates every BP sweep to ``_policy_sweep_into`` so a
    damping/resolution/check policy cannot accidentally become a second BP
    implementation inside guided decimation.
    """
    n, edge_count = original_priors.shape[0], len(labels)
    priors = original_priors.copy()
    old = np.empty((edge_count, 3), dtype=np.float64)
    new = np.empty_like(old)
    comm = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty((n, 3), dtype=np.float64)
    marginals = np.empty((n, 4), dtype=np.float64)
    candidate = np.zeros(n, dtype=np.uint8)
    eligible = np.ones(n, dtype=np.uint8)
    if zero_shortcut and _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
        return candidate, 0, 0, 0, True
    for edge in range(edge_count):
        for state in range(3):
            value = priors[variables[edge], state]
            old[edge, state] = round_message(value, format_code, scale) if scope >= 1 else value
    sweeps = 0
    fixations = 0
    for round_index in range(max_rounds):
        for _ in range(iterations_per_round):
            _policy_sweep_into(row_ptr, variable_ptr, variable_edges, variables,
                               labels, old, priors, syndrome, format_code, scale,
                               scope, check_rule, old_weight, fresh_weight, alpha,
                               beta, hard_decision, comm, c2v, beliefs, new,
                               candidate)
            old, new = new, old
            sweeps += 1
        if _candidate_matches(row_ptr, variables, labels, candidate, syndrome):
            return candidate, sweeps, round_index + 1, fixations, True
        _normalize_marginals(beliefs, marginals)
        target = -1
        pauli = 0
        reliability = -1.0
        for variable in range(n):
            if eligible[variable] == 0:
                continue
            for state in range(4):
                value = marginals[variable, state]
                if value > reliability:
                    target = variable
                    pauli = state
                    reliability = value
        if target < 0:
            return candidate, sweeps, round_index + 1, fixations, False
        eligible[target] = 0
        total = 1.0 + 2.0 * epsilon_fix
        for state in range(1, 4):
            probability = (1.0 - epsilon_fix if state == pauli else epsilon_fix) / total
            identity = (1.0 - epsilon_fix if pauli == 0 else epsilon_fix) / total
            priors[target, state - 1] = math.log(identity / probability)
        # Match the controller contract: a fixation changes the prior only.
        # The committed V2C buffer remains the input to the next sweep.
        fixations += 1
    return candidate, sweeps, max_rounds, fixations, False


@dataclass(frozen=True)
class CompiledBp4Graph:
    """Preindexed plain four-state BP4 with resolved I/X/Y/Z priors."""

    row_ptr: np.ndarray
    variable_ptr: np.ndarray
    variable_edges: np.ndarray
    variables: np.ndarray
    labels: np.ndarray
    prior_llrs: np.ndarray
    profile: QuaternaryNumericalProfile = DEFAULT_QBP4_F64
    policy: BpFloodingPolicy | None = None

    def __post_init__(self):
        profile, policy = self.profile, self.policy
        if not isinstance(profile, QuaternaryNumericalProfile):
            raise ValueError("invalid compiled BP4 numerical profile")
        if policy is not None and not isinstance(policy, BpFloodingPolicy):
            raise ValueError("compiled BP4 policy must be a BpFloodingPolicy")
        if policy is not None and not isinstance(profile, QuaternaryNumericalProfileV2):
            raise ValueError("resolved BP4 flooding policy requires unbounded v2 numerical coordinates")
        if isinstance(profile, QuaternaryNumericalProfileV2) and profile.check_rule != "tanh_product":
            raise ValueError("compiled v2 BP4 currently supports tanh_product checks")
        variables = integer_vector(self.variables, "variables")
        labels = integer_vector(self.labels, "labels")
        count = len(variables)
        rows = csr_pointer(self.row_ptr, count, "row_ptr")
        pointers = csr_pointer(self.variable_ptr, count, "variable_ptr")
        edges = integer_vector(self.variable_edges, "variable_edges")
        priors = np.asarray(self.prior_llrs)
        n = len(pointers) - 1
        if priors.shape != (n, 3) or not np.issubdtype(priors.dtype, np.number) or np.iscomplexobj(priors) or not np.all(np.isfinite(priors)):
            raise ValueError("prior_llrs must contain three finite real LLRs per variable")
        if len(labels) != count or np.any((labels < 1) | (labels > 3)):
            raise ValueError("labels must contain one nonidentity Pauli per edge")
        if np.any((variables < 0) | (variables >= n)) or len(edges) != count or not np.array_equal(np.sort(edges), np.arange(count)):
            raise ValueError("compiled BP4 edge indexes are out of bounds or duplicated")
        for start, stop in zip(rows[:-1], rows[1:]):
            if start == stop or np.any(variables[start+1:stop] <= variables[start:stop-1]):
                raise ValueError("BP4 rows require distinct variables in canonical order")
        expected_ptr = np.concatenate(([0], np.cumsum(np.bincount(variables.astype(np.int64), minlength=n))))
        if not np.array_equal(pointers, expected_ptr) or not np.array_equal(edges, np.argsort(variables, kind="stable")):
            raise ValueError("variable CSR does not match check CSR")
        for name, array, dtype in (("row_ptr", rows, np.int64), ("variable_ptr", pointers, np.int64),
                ("variable_edges", edges, np.int64), ("variables", variables, np.int64),
                ("labels", labels, np.uint8), ("prior_llrs", priors, np.float64)):
            object.__setattr__(self, name, immutable_array(array, dtype))

    @property
    def effective_numerics(self) -> dict[str, object]:
        return (self.policy.as_evidence() if self.policy is not None
                else self.profile.as_evidence())

    @classmethod
    def from_css(cls, code: CssCode, p0: float, *, rule: str = "sum_product",
                 policy: BpFloodingPolicy | None = None) -> "CompiledBp4Graph":
        """Index a validated CSS code without a dense Pauli commutation proof.

        X rows precede Z rows. The caller owns the original CSS code's
        stabilizer and logical validation; this only checks graph shape and
        cross-check commutation before constructing decoder-visible state.
        """
        if not isinstance(code, CssCode) or rule not in {"sum_product", "min_sum"}:
            raise ValueError("from_css requires a CSS code and a known BP4 check rule")
        hx, hz = np.asarray(code.hx), np.asarray(code.hz)
        if (hx.ndim != 2 or hz.ndim != 2 or hx.shape[1] == 0 or hx.shape[1] != hz.shape[1]
                or not np.issubdtype(hx.dtype, np.integer) or not np.issubdtype(hz.dtype, np.integer)
                or np.any((hx != 0) & (hx != 1)) or np.any((hz != 0) & (hz != 1))
                or np.any((hx.astype(np.int64) @ hz.astype(np.int64).T) % 2)):
            raise ValueError("CSS check matrices must be binary, aligned, and commuting")
        if (np.any(~np.any(hx, axis=1)) or np.any(~np.any(hz, axis=1))
                or np.any(~(np.any(hx, axis=0) | np.any(hz, axis=0)))):
            raise ValueError("CSS BP4 graph cannot have empty checks or isolated qubits")
        if not math.isfinite(p0) or not 0.0 < p0 < 1.0:
            raise ValueError("depolarizing decoder prior p0 must lie in (0,1)")
        if policy is not None and (not isinstance(policy, BpFloodingPolicy) or policy.check_rule != rule):
            raise ValueError("CSS BP4 policy conflicts with the selected check rule")
        if policy is None and rule == "min_sum":
            policy = DEFAULT_BP4_MIN_SUM
        n = hx.shape[1]
        x_rows, x_vars = np.nonzero(hx)
        z_rows, z_vars = np.nonzero(hz)
        rows = np.concatenate((x_rows, z_rows + hx.shape[0]))
        variables = np.concatenate((x_vars, z_vars)).astype(np.int64)
        labels = np.concatenate((np.full(len(x_rows), Pauli.X), np.full(len(z_rows), Pauli.Z))).astype(np.uint8)
        row_ptr = np.bincount(rows, minlength=hx.shape[0] + hz.shape[0]).astype(np.int64)
        row_ptr = np.concatenate((np.asarray((0,), dtype=np.int64), np.cumsum(row_ptr)))
        variable_ptr = np.bincount(variables, minlength=n).astype(np.int64)
        variable_ptr = np.concatenate((np.asarray((0,), dtype=np.int64), np.cumsum(variable_ptr)))
        variable_edges = np.empty(len(labels), dtype=np.int64)
        offsets = variable_ptr[:-1].copy()
        for edge, variable in enumerate(variables):
            variable_edges[offsets[variable]] = edge
            offsets[variable] += 1
        llr = math.log((1.0 - p0) / (p0 / 3.0))
        prior_llrs = np.full((n, 3), llr, dtype=np.float64)
        for array in (row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs):
            array.setflags(write=False)
        return cls(row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs, QBP4_F64_V2, policy)

    @classmethod
    def from_code(cls, code: PauliCode, priors: object, *,
                  profile: QuaternaryNumericalProfile = DEFAULT_QBP4_F64,
                  rule: str | None = None,
                  policy: BpFloodingPolicy | None = None) -> "CompiledBp4Graph":
        if not isinstance(code, PauliCode):
            raise TypeError("compiled BP4 prototype needs a validated PauliCode")
        probabilities = _priors(priors, n=code.n)
        rows, cols = np.nonzero(code.checks != Pauli.I)
        labels = np.asarray(code.checks[rows, cols], dtype=np.uint8)
        variables = np.asarray(cols, dtype=np.int64)
        row_ptr = np.zeros(code.checks.shape[0] + 1, dtype=np.int64)
        variable_ptr = np.zeros(code.n + 1, dtype=np.int64)
        for row in rows:
            row_ptr[int(row) + 1] += 1
        for variable in variables:
            variable_ptr[int(variable) + 1] += 1
        np.cumsum(row_ptr, out=row_ptr)
        np.cumsum(variable_ptr, out=variable_ptr)
        variable_edges = np.empty(len(labels), dtype=np.int64)
        offsets = variable_ptr[:-1].copy()
        for edge, variable in enumerate(variables):
            variable_edges[offsets[variable]] = edge
            offsets[variable] += 1
        if not isinstance(profile, QuaternaryNumericalProfile):
            raise ValueError("invalid compiled BP4 numerical profile")
        if rule not in {None, "sum_product", "min_sum"}:
            raise ValueError("compiled BP4 rule must be sum_product or min_sum")
        if policy is not None and not isinstance(policy, BpFloodingPolicy):
            raise ValueError("compiled BP4 policy must be a BpFloodingPolicy")
        if policy is not None and rule is not None and policy.check_rule != rule:
            raise ValueError("BP4 rule conflicts with explicit policy")
        if policy is None and rule == "min_sum":
            policy = DEFAULT_BP4_MIN_SUM
        if policy is not None and not isinstance(profile, QuaternaryNumericalProfileV2):
            raise ValueError("resolved BP4 flooding policy requires unbounded v2 numerical coordinates")
        if isinstance(profile, QuaternaryNumericalProfileV2) and profile.check_rule != "tanh_product":
            raise ValueError("compiled v2 BP4 currently supports tanh_product checks")
        prior_llrs = np.asarray([probabilities_to_llrs(row, profile=profile) for row in probabilities], dtype=np.float64)
        for array in (row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs):
            array.setflags(write=False)
        return cls(row_ptr, variable_ptr, variable_edges, variables, labels, prior_llrs, profile, policy)

    def _syndrome(self, value: np.ndarray) -> np.ndarray:
        syndrome = np.asarray(value)
        if syndrome.shape != (len(self.row_ptr) - 1,) or not np.issubdtype(syndrome.dtype, np.integer) or np.any((syndrome != 0) & (syndrome != 1)):
            raise ValueError("syndrome must be a binary vector matching the graph")
        return np.asarray(syndrome, dtype=np.uint8)

    def initial_v2c(self) -> np.ndarray:
        values = np.asarray(self.prior_llrs[self.variables], dtype=np.float64)
        if self.policy is not None and self.policy.resolution.scope != "scalar_edges":
            resolution = self.policy.resolution
            for index in np.ndindex(values.shape):
                values[index] = resolution.quantize(values[index])
        return values

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray) -> CompiledBp4Sweep:
        s = self._syndrome(syndrome)
        old = np.asarray(old_v2c, dtype=np.float64)
        if old.shape != (len(self.labels), 3) or not np.all(np.isfinite(old)):
            raise ValueError("old_v2c must be finite with one three-LLR row per edge")
        if self.policy is not None:
            policy = self.policy
            resolution = policy.resolution
            if resolution.scope != "scalar_edges":
                old = old.copy()
                for index in np.ndindex(old.shape):
                    old[index] = resolution.quantize(old[index])
            old_weight, fresh_weight, alpha, beta = policy.coefficients
            comm = np.empty(len(self.labels), dtype=np.float64)
            c2v = np.empty(len(self.labels), dtype=np.float64)
            beliefs = np.empty_like(self.prior_llrs)
            v2c = np.empty_like(old)
            candidate = np.empty(self.prior_llrs.shape[0], dtype=np.uint8)
            marginals = np.empty((self.prior_llrs.shape[0], 4), dtype=np.float64)
            _policy_sweep_into(self.row_ptr, self.variable_ptr, self.variable_edges,
                               self.variables, self.labels, old, self.prior_llrs, s,
                               resolution.format_code, resolution.fixed_scale,
                               {"scalar_edges": 0, "all_messages": 1, "all_state": 2}[resolution.scope],
                               1 if policy.check_rule == "min_sum" else 0,
                               old_weight, fresh_weight, alpha, beta,
                               policy.decision_code,
                               comm, c2v, beliefs, v2c, candidate, *policy.stabilization_args)
            _normalize_marginals(beliefs, marginals)
        elif isinstance(self.profile, QuaternaryNumericalProfileV2):
            comm = np.empty(len(self.labels), dtype=np.float64)
            c2v = np.empty(len(self.labels), dtype=np.float64)
            beliefs = np.empty_like(self.prior_llrs)
            v2c = np.empty_like(old)
            candidate = np.empty(self.prior_llrs.shape[0], dtype=np.uint8)
            marginals = np.empty((self.prior_llrs.shape[0], 4), dtype=np.float64)
            _v2_sweep_into(self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
                           self.labels, old, self.prior_llrs, s, math.inf if self.profile.check_cap is None else self.profile.check_cap,
                           self.profile.product_epsilon, self.profile.v2c_damping,
                           comm, c2v, beliefs, v2c, candidate, isinstance(self.profile, QuaternaryNumericalProfileV3))
            _normalize_marginals(beliefs, marginals)
        else:
            c2v, v2c, beliefs, marginals, candidate, _ = _sweep(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
                self.labels, old, self.prior_llrs, s, self.profile.saturation,
            )
        converged = _candidate_matches(self.row_ptr, self.variables, self.labels, candidate, s)
        for array in (c2v, v2c, beliefs, marginals, candidate):
            array.setflags(write=False)
        return CompiledBp4Sweep(c2v, v2c, beliefs, marginals, candidate, bool(converged))

    def run_batch(self, syndromes, *, max_iterations: int, workers: int = 1, stop_on_convergence: bool = True):
        """Decode independent observations using the same qualified flooding loop."""
        from bp_registry.cpu_batch import pauli_batch
        return pauli_batch(self, syndromes, max_iterations=max_iterations, workers=workers, stop_on_convergence=stop_on_convergence)

    def run(self, syndrome: np.ndarray, *, max_iterations: int, stop_on_convergence: bool = True) -> CompiledBp4Result:
        s = self._syndrome(syndrome)
        if type(max_iterations) is not int or max_iterations < 0 or type(stop_on_convergence) is not bool:
            raise ValueError("invalid compiled BP4 stopping request")
        if self.policy is not None:
            policy = self.policy
            resolution = policy.resolution
            candidate, iterations, converged = _decode_policy(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
                self.labels, self.prior_llrs, s, max_iterations,
                resolution.format_code, resolution.fixed_scale,
                {"scalar_edges": 0, "all_messages": 1, "all_state": 2}[resolution.scope],
                1 if policy.check_rule == "min_sum" else 0,
                *policy.coefficients,
                policy.decision_code,
                policy.zero_syndrome_shortcut, stop_on_convergence, *policy.stabilization_args, policy.version == "bp-flooding-policy-v2",
            )
        elif isinstance(self.profile, QuaternaryNumericalProfileV2):
            candidate, iterations, converged = _decode_v2(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables, self.labels,
                self.prior_llrs, s, max_iterations, math.inf if self.profile.check_cap is None else self.profile.check_cap,
                self.profile.product_epsilon, self.profile.v2c_damping, stop_on_convergence, isinstance(self.profile, QuaternaryNumericalProfileV3),
            )
        else:
            candidate, iterations, converged = _decode(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables, self.labels,
                self.prior_llrs, s, self.profile.saturation, max_iterations, stop_on_convergence,
            )
        candidate.setflags(write=False)
        return CompiledBp4Result(candidate, int(iterations), bool(converged))

    def run_qbpgd(self, syndrome: np.ndarray, *, iterations_per_round: int = 10,
                  epsilon: float = 1e-10, round_limit: int | None = None) -> CompiledQbpgdResult:
        """Run four-state Q-BPGD with frozen v2 BP4 numerics; development evidence only."""
        s = self._syndrome(syndrome)
        if self.policy is not None and self.policy.version != "bp-flooding-policy-v1":
            raise ValueError("compiled Q-BPGD policy v2 is not qualified")
        if isinstance(self.profile, QuaternaryNumericalProfileV3):
            raise ValueError("compiled Q-BPGD requires an explicit historical v2 profile")
        if not isinstance(self.profile, QuaternaryNumericalProfileV2):
            raise ValueError("compiled Q-BPGD requires the v2 BP4 execution family")
        if type(iterations_per_round) is not int or iterations_per_round < 1:
            raise ValueError("iterations_per_round must be a positive integer")
        if not math.isfinite(epsilon) or not 0.0 < epsilon < 1.0:
            raise ValueError("epsilon must be in (0,1)")
        if round_limit is not None and (type(round_limit) is not int or round_limit < 1):
            raise ValueError("round_limit must be a positive integer")
        if self.policy is None:
            candidate, sweeps, rounds, fixations, converged = _decode_qbpgd_v2(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
                self.labels, self.prior_llrs, s, iterations_per_round, epsilon,
                min(len(self.prior_llrs), round_limit or len(self.prior_llrs)),
                math.inf if self.profile.check_cap is None else self.profile.check_cap,
                self.profile.product_epsilon, self.profile.v2c_damping,
            )
        else:
            policy = self.policy
            resolution = policy.resolution
            candidate, sweeps, rounds, fixations, converged = _decode_qbpgd_policy(
                self.row_ptr, self.variable_ptr, self.variable_edges, self.variables,
                self.labels, self.prior_llrs, s, iterations_per_round, epsilon,
                min(len(self.prior_llrs), round_limit or len(self.prior_llrs)),
                resolution.format_code, resolution.fixed_scale,
                {"scalar_edges": 0, "all_messages": 1, "all_state": 2}[resolution.scope],
                1 if policy.check_rule == "min_sum" else 0, *policy.coefficients,
                policy.decision_code, policy.zero_syndrome_shortcut,
            )
        candidate.setflags(write=False)
        return CompiledQbpgdResult(candidate, int(sweeps), int(rounds), int(fixations), bool(converged))


__all__ = ["CompiledBp4Graph", "CompiledBp4Result", "CompiledBp4Sweep", "CompiledQbpgdResult"]
