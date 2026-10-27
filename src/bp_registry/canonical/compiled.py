"""Optional Numba prototype for the canonical binary flooding hot loop.

This module is opt-in. It accepts a project-owned graph and explicit numerical
policy, and leaves provenance, budgets, and publication execution to the
reference engine until those contracts are qualified for this backend.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numba import njit

from bp_registry.resolution import BpFloodingPolicy, round_message

from .kernel import KernelResult
from .numerics import (
    BinaryNumericalProfileV2, MIN_SUM_CPU_F64,
    DEFAULT_BINARY_SPA_F64, NumericalProfile, REFERENCE_CPU_F64, prior_llr,
)
from .schedules import EdgeTable, FloodingSweep, FloodingWork


@njit(cache=True)
def _clip(value: float, limit: float) -> float:
    return min(limit, max(-limit, value))


@njit(cache=True)
def _boxplus_pair(left: float, right: float, limit: float) -> float:
    left = _clip(left, limit)
    right = _clip(right, limit)
    a, b = abs(left), abs(right)
    smaller, larger = min(a, b), max(a, b)
    sign = -1.0 if left * right < 0.0 else 1.0
    correction = math.log1p(math.exp(-(smaller + larger))) - math.log1p(math.exp(-(larger - smaller)))
    return _clip(sign * (smaller + correction), limit)


@njit(cache=True)
def _flooding_sweep(
    row_ptr: np.ndarray, variables: np.ndarray, n: int, old_v2c: np.ndarray,
    syndrome: np.ndarray, prior: float, limit: float, rule: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    edge_count = len(variables)
    old = np.empty(edge_count, dtype=np.float64)
    c2v = np.empty(edge_count, dtype=np.float64)
    beliefs = np.empty(n, dtype=np.float64)
    candidate = np.empty(n, dtype=np.uint8)
    new_v2c = np.empty(edge_count, dtype=np.float64)
    _flooding_sweep_into(row_ptr, variables, n, old_v2c, syndrome, prior, limit, rule,
                         old, c2v, beliefs, candidate, new_v2c, True)
    return old, c2v, beliefs, candidate, new_v2c


@njit(cache=True)
def _flooding_sweep_into(
    row_ptr: np.ndarray, variables: np.ndarray, n: int, old_v2c: np.ndarray,
    syndrome: np.ndarray, prior: float, limit: float, rule: int,
    old: np.ndarray, c2v: np.ndarray, beliefs: np.ndarray,
    candidate: np.ndarray, new_v2c: np.ndarray, clip_old: bool,
) -> None:
    edge_count = len(variables)
    if clip_old:
        for edge in range(edge_count):
            old[edge] = _clip(old_v2c[edge], limit)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        for edge in range(start, stop):
            first = True
            result = limit
            negative_count = 0
            magnitude = limit
            for other in range(start, stop):
                if other == edge:
                    continue
                value = old[other]
                if rule == 0:
                    if first:
                        result = value
                        first = False
                    else:
                        result = _boxplus_pair(result, value, limit)
                else:
                    magnitude = min(magnitude, abs(value))
                    if value < 0.0:
                        negative_count += 1
            if rule == 0:
                message = result
                # The reference fold clips the complete result as a named boundary.
                message = _clip(message, limit)
                if syndrome[check]:
                    message = -message
            else:
                message = -magnitude if (negative_count + syndrome[check]) % 2 else magnitude
            c2v[edge] = _clip(message, limit)
    beliefs.fill(prior)
    for edge in range(edge_count):
        beliefs[variables[edge]] += c2v[edge]
    for variable in range(n):
        beliefs[variable] = _clip(beliefs[variable], limit)
        candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
    for edge in range(edge_count):
        new_v2c[edge] = _clip(beliefs[variables[edge]] - c2v[edge], limit)


@njit(cache=True)
def _candidate_matches(row_ptr: np.ndarray, variables: np.ndarray, candidate: np.ndarray, syndrome: np.ndarray) -> bool:
    for check in range(len(row_ptr) - 1):
        parity = 0
        for edge in range(row_ptr[check], row_ptr[check + 1]):
            parity ^= candidate[variables[edge]]
        if parity != syndrome[check]:
            return False
    return True


@njit(cache=True)
def _decode(
    row_ptr: np.ndarray, variables: np.ndarray, n: int, syndrome: np.ndarray,
    prior: float, limit: float, rule: int, max_iterations: int,
) -> tuple[np.ndarray, bool, int]:
    candidate = np.zeros(n, dtype=np.uint8)
    if len(variables) == 0:
        return candidate, _candidate_matches(row_ptr, variables, candidate, syndrome), 0
    v2c = np.full(len(variables), _clip(prior, limit), dtype=np.float64)
    next_v2c = np.empty_like(v2c)
    c2v = np.empty_like(v2c)
    beliefs = np.empty(n, dtype=np.float64)
    for iteration in range(1, max_iterations + 1):
        _flooding_sweep_into(row_ptr, variables, n, v2c, syndrome, prior, limit, rule,
                             v2c, c2v, beliefs, candidate, next_v2c, False)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, True, iteration
        v2c, next_v2c = next_v2c, v2c
    return candidate, False, max_iterations


@njit(cache=True)
def _v2_check(old: np.ndarray, start: int, stop: int, target: int,
              syndrome_bit: int, cap: float, epsilon: float) -> float:
    product = -1.0 if syndrome_bit else 1.0
    for other in range(start, stop):
        if other == target:
            continue
        value = old[other]
        if not math.isfinite(value):
            raise ValueError("nonfinite binary SPA v2 V2C input")
        product *= (1.0 if value > 40.0 else -1.0 if value < -40.0 else math.tanh(value / 2.0))
    if product >= 1.0:
        product = 1.0 - epsilon
    elif product <= -1.0:
        product = -1.0 + epsilon
    result = math.log1p(product) - math.log1p(-product)
    if not math.isfinite(result):
        raise ValueError("nonfinite binary SPA v2 check")
    return _clip(result, cap)


@njit(cache=True)
def _v2_sweep_into(row_ptr: np.ndarray, variables: np.ndarray, n: int,
                   old: np.ndarray, syndrome: np.ndarray, prior: float,
                   cap: float, epsilon: float, damping: float,
                   c2v: np.ndarray, beliefs: np.ndarray, candidate: np.ndarray,
                   new: np.ndarray) -> None:
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        for edge in range(start, stop):
            c2v[edge] = _v2_check(old, start, stop, edge, int(syndrome[check]), cap, epsilon)
    beliefs[:] = prior
    for edge in range(len(variables)):
        beliefs[variables[edge]] += c2v[edge]
    for variable in range(n):
        if not math.isfinite(beliefs[variable]):
            raise ValueError("nonfinite binary SPA v2 posterior")
        candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
    for edge in range(len(variables)):
        proposal = beliefs[variables[edge]] - c2v[edge]
        value = damping * old[edge] + (1.0 - damping) * proposal
        if not math.isfinite(value):
            raise ValueError("nonfinite binary SPA v2 V2C")
        new[edge] = value


@njit(cache=True)
def _decode_v2(row_ptr: np.ndarray, variables: np.ndarray, n: int,
               syndrome: np.ndarray, prior: float, max_iterations: int,
               cap: float, epsilon: float, damping: float) -> tuple[np.ndarray, bool, int]:
    candidate = np.zeros(n, dtype=np.uint8)
    if len(variables) == 0:
        return candidate, _candidate_matches(row_ptr, variables, candidate, syndrome), 0
    old = np.full(len(variables), prior, dtype=np.float64)
    new = np.empty_like(old)
    c2v = np.empty_like(old)
    beliefs = np.empty(n, dtype=np.float64)
    for iteration in range(1, max_iterations + 1):
        _v2_sweep_into(row_ptr, variables, n, old, syndrome, prior,
                       cap, epsilon, damping, c2v, beliefs, candidate, new)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, True, iteration
        old, new = new, old
    return candidate, False, max_iterations


@njit(cache=True)
def _policy_sweep_into(row_ptr, variables, n, old, syndrome, prior,
                       format_code, scale, all_state, check_rule,
                       old_weight, fresh_weight, alpha, beta,
                       c2v, beliefs, candidate, new):
    edge_count = len(variables)
    fixed_bound = ((2 ** ((8 if format_code == 3 else 16 if format_code == 4 else 32) - 1) - 1) / scale
                   if format_code >= 3 else math.inf)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        for edge in range(start, stop):
            if check_rule == 1:
                magnitude = fixed_bound
                negatives = int(syndrome[check])
                for other in range(start, stop):
                    if other != edge:
                        magnitude = min(magnitude, abs(old[other]))
                        negatives += int(old[other] < 0.0)
                if stop - start == 1 and format_code < 3:
                    magnitude = 23.7189981105
                message = alpha * max(0.0, magnitude - beta)
                if negatives % 2:
                    message = -message
            else:
                product = -1.0 if syndrome[check] else 1.0
                for other in range(start, stop):
                    if other != edge:
                        value = old[other]
                        product *= 1.0 if value > 40.0 else -1.0 if value < -40.0 else math.tanh(value / 2.0)
                product = min(1.0 - 1e-10, max(-1.0 + 1e-10, product))
                message = math.log1p(product) - math.log1p(-product)
            c2v[edge] = round_message(message, format_code, scale)
    beliefs[:] = prior
    for edge in range(edge_count):
        beliefs[variables[edge]] += c2v[edge]
    for variable in range(n):
        if all_state:
            beliefs[variable] = round_message(beliefs[variable], format_code, scale)
        candidate[variable] = 1 if beliefs[variable] < 0.0 else 0
    for edge in range(edge_count):
        proposal = round_message(beliefs[variables[edge]] - c2v[edge], format_code, scale)
        new[edge] = round_message(old_weight * old[edge] + fresh_weight * proposal, format_code, scale)


@njit(cache=True)
def _decode_policy(row_ptr, variables, n, syndrome, prior, max_iterations,
                   format_code, scale, all_state, check_rule,
                   old_weight, fresh_weight, alpha, beta, zero_shortcut):
    candidate = np.zeros(n, dtype=np.uint8)
    if zero_shortcut and _candidate_matches(row_ptr, variables, candidate, syndrome):
        return candidate, True, 0
    old = np.full(len(variables), round_message(prior, format_code, scale), dtype=np.float64)
    new = np.empty_like(old)
    c2v = np.empty_like(old)
    beliefs = np.empty(n, dtype=np.float64)
    for iteration in range(1, max_iterations + 1):
        _policy_sweep_into(row_ptr, variables, n, old, syndrome, prior,
                           format_code, scale, all_state, check_rule,
                           old_weight, fresh_weight, alpha, beta,
                           c2v, beliefs, candidate, new)
        if _candidate_matches(row_ptr, variables, candidate, syndrome):
            return candidate, True, iteration
        old, new = new, old
    return candidate, _candidate_matches(row_ptr, variables, candidate, syndrome), max_iterations


@dataclass(frozen=True)
class CompiledBinaryFlooding:
    """Preindexed, optional backend for plain SPA or plain min-sum flooding."""

    table: EdgeTable
    row_ptr: np.ndarray
    variables: np.ndarray
    rule: str
    numerical_profile: NumericalProfile = DEFAULT_BINARY_SPA_F64
    policy: BpFloodingPolicy | None = None

    @property
    def effective_numerics(self) -> dict[str, object]:
        return (self.policy.as_evidence() if self.policy is not None
                else self.numerical_profile.as_evidence())

    @classmethod
    def from_check_matrix(cls, check_matrix: np.ndarray, *, rule: str = "spa",
                          profile: NumericalProfile | None = None,
                          policy: BpFloodingPolicy | None = None) -> "CompiledBinaryFlooding":
        if rule not in {"spa", "min_sum"}:
            raise ValueError("compiled prototype supports only plain spa or min_sum")
        table = EdgeTable.from_check_matrix(check_matrix)
        row_ptr = np.zeros(table.check_count + 1, dtype=np.int64)
        variables = np.empty(table.edge_count, dtype=np.int64)
        for edge, (check, variable) in enumerate(table.edges):
            row_ptr[check + 1] += 1
            variables[edge] = variable
        np.cumsum(row_ptr, out=row_ptr)
        row_ptr.setflags(write=False)
        variables.setflags(write=False)
        selected = (DEFAULT_BINARY_SPA_F64 if rule == "spa" else MIN_SUM_CPU_F64) if profile is None else profile
        if not isinstance(selected, NumericalProfile):
            raise ValueError("invalid compiled binary numerical profile")
        if policy is not None and not isinstance(policy, BpFloodingPolicy):
            raise ValueError("binary flooding policy must be a BpFloodingPolicy")
        if policy is not None and policy.check_rule != ("sum_product" if rule == "spa" else "min_sum"):
            raise ValueError("binary check rule conflicts with explicit policy")
        if policy is not None and profile is not None and not isinstance(profile, BinaryNumericalProfileV2):
            raise ValueError("resolved binary policy requires unbounded v2 prior coordinates")
        if rule == "min_sum" and selected != MIN_SUM_CPU_F64 and policy is None:
            raise ValueError("compiled min-sum requires its v1 numerical profile")
        if rule == "spa" and selected == MIN_SUM_CPU_F64 and policy is None:
            raise ValueError("compiled SPA requires an SPA numerical profile")
        return cls(table, row_ptr, variables, rule, selected, policy)

    @property
    def profile(self):
        return self.numerical_profile

    def _syndrome(self, syndrome: np.ndarray) -> np.ndarray:
        s = np.asarray(syndrome)
        if s.shape != (self.table.check_count,) or not np.issubdtype(s.dtype, np.integer) or np.any((s != 0) & (s != 1)):
            raise ValueError("syndrome must be a binary vector matching the graph")
        return np.asarray(s, dtype=np.uint8)

    def _inputs(self, syndrome: np.ndarray, error_rate: float) -> tuple[np.ndarray, float]:
        s = self._syndrome(syndrome)
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be finite and between zero and one")
        return s, (math.log((1.0 - error_rate) / error_rate) if self.policy is not None
                   else prior_llr(error_rate, profile=self.profile))

    def bind_error_rate(self, error_rate: float) -> "BoundBinaryFlooding":
        """Resolve a fixed prior once for a same-parameter shot batch."""
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be finite and between zero and one")
        prior = (math.log((1.0 - error_rate) / error_rate) if self.policy is not None
                 else prior_llr(error_rate, profile=self.profile))
        return BoundBinaryFlooding(self, prior)

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float) -> FloodingSweep:
        """Return one completed flooding sweep, including v2 V2C damping."""
        s, prior = self._inputs(syndrome, error_rate)
        old = np.asarray(old_v2c, dtype=np.float64)
        if old.shape != (self.table.edge_count,) or not np.all(np.isfinite(old)):
            raise ValueError("old_v2c must be finite and match the graph edges")
        if self.policy is not None:
            policy = self.policy
            resolution = policy.resolution
            old = np.asarray([resolution.quantize(value) for value in old], dtype=np.float64)
            old_weight, fresh_weight, alpha, beta = policy.coefficients
            c2v = np.empty(self.table.edge_count, dtype=np.float64)
            beliefs = np.empty(self.table.variable_count, dtype=np.float64)
            candidate = np.empty(self.table.variable_count, dtype=np.uint8)
            new = np.empty(self.table.edge_count, dtype=np.float64)
            _policy_sweep_into(self.row_ptr, self.variables, self.table.variable_count,
                               old, s, prior, resolution.format_code, resolution.fixed_scale,
                               resolution.scope == "all_state", 1 if self.rule == "min_sum" else 0,
                               old_weight, fresh_weight, alpha, beta, c2v, beliefs, candidate, new)
            arrays = (old.copy(), c2v, beliefs, candidate, new)
        elif isinstance(self.profile, BinaryNumericalProfileV2):
            c2v = np.empty(self.table.edge_count, dtype=np.float64)
            beliefs = np.empty(self.table.variable_count, dtype=np.float64)
            candidate = np.empty(self.table.variable_count, dtype=np.uint8)
            new = np.empty(self.table.edge_count, dtype=np.float64)
            _v2_sweep_into(self.row_ptr, self.variables, self.table.variable_count, old, s,
                           prior, math.inf if self.profile.check_cap is None else self.profile.check_cap, self.profile.product_epsilon,
                           self.profile.v2c_damping, c2v, beliefs, candidate, new)
            arrays = (old.copy(), c2v, beliefs, candidate, new)
        else:
            arrays = _flooding_sweep(self.row_ptr, self.variables, self.table.variable_count, old, s,
                                     prior, self.profile.saturation, 0 if self.rule == "spa" else 1)
        for array in arrays:
            array.setflags(write=False)
        return FloodingSweep(
            edge_count=self.table.edge_count, old_v2c=arrays[0], check_to_variable=arrays[1],
            new_v2c=arrays[4], beliefs=arrays[2], candidate=arrays[3],
            proposed_work=FloodingWork(self.table.edge_count, self.table.edge_count,
                                       self.table.variable_count, self.table.variable_count),
        )

    def run(self, syndrome: np.ndarray, *, error_rate: float, max_iterations: int) -> KernelResult:
        s, prior = self._inputs(syndrome, error_rate)
        if type(max_iterations) is not int or max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        if self.policy is not None:
            policy = self.policy
            resolution = policy.resolution
            candidate, converged, iterations = _decode_policy(
                self.row_ptr, self.variables, self.table.variable_count, s, prior,
                max_iterations, resolution.format_code, resolution.fixed_scale,
                resolution.scope == "all_state", 1 if self.rule == "min_sum" else 0,
                *policy.coefficients, policy.zero_syndrome_shortcut,
            )
        elif isinstance(self.profile, BinaryNumericalProfileV2):
            candidate, converged, iterations = _decode_v2(
                self.row_ptr, self.variables, self.table.variable_count, s, prior,
                max_iterations, math.inf if self.profile.check_cap is None else self.profile.check_cap, self.profile.product_epsilon,
                self.profile.v2c_damping,
            )
        else:
            candidate, converged, iterations = _decode(
                self.row_ptr, self.variables, self.table.variable_count, s,
                prior, self.profile.saturation, 0 if self.rule == "spa" else 1, max_iterations,
            )
        candidate.setflags(write=False)
        return KernelResult(candidate, bool(converged), int(iterations))


@dataclass(frozen=True)
class BoundBinaryFlooding:
    """One declared binary graph, rule, and physical error rate."""

    graph: CompiledBinaryFlooding
    prior: float

    def run(self, syndrome: np.ndarray, *, max_iterations: int) -> KernelResult:
        s = self.graph._syndrome(syndrome)
        if type(max_iterations) is not int or max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        if self.graph.policy is not None:
            policy = self.graph.policy
            resolution = policy.resolution
            candidate, converged, iterations = _decode_policy(
                self.graph.row_ptr, self.graph.variables, self.graph.table.variable_count,
                s, self.prior, max_iterations, resolution.format_code,
                resolution.fixed_scale, resolution.scope == "all_state",
                1 if self.graph.rule == "min_sum" else 0,
                *policy.coefficients, policy.zero_syndrome_shortcut,
            )
        elif isinstance(self.graph.profile, BinaryNumericalProfileV2):
            candidate, converged, iterations = _decode_v2(
                self.graph.row_ptr, self.graph.variables, self.graph.table.variable_count,
                s, self.prior, max_iterations, math.inf if self.graph.profile.check_cap is None else self.graph.profile.check_cap,
                self.graph.profile.product_epsilon, self.graph.profile.v2c_damping,
            )
        else:
            candidate, converged, iterations = _decode(
                self.graph.row_ptr, self.graph.variables, self.graph.table.variable_count, s,
                self.prior, self.graph.profile.saturation, 0 if self.graph.rule == "spa" else 1,
                max_iterations,
            )
        candidate.setflags(write=False)
        return KernelResult(candidate, bool(converged), int(iterations))


__all__ = ["BoundBinaryFlooding", "CompiledBinaryFlooding"]
