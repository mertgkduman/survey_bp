"""Project-owned deterministic binary sum-product flooding kernel."""

from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .numerics import (
    BinaryNumericalProfileV2, NumericalProfile, REFERENCE_CPU_F64,
    check_to_variable, finite_saturate, hard_decision, prior_llr,
)
from .updates import CheckUpdateRule


def _binary(value: np.ndarray, name: str, *, ndim: int) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a binary integer array with {ndim} dimensions")
    return np.array(array, dtype=np.uint8, copy=True)


@dataclass(frozen=True)
class KernelResult:
    candidate: np.ndarray
    converged: bool
    iterations: int


class BinarySpaKernel:
    """No native adapter: deterministic float64 LLR SPA with flooding updates."""

    def __init__(self, *, profile: NumericalProfile = REFERENCE_CPU_F64, update_rule: CheckUpdateRule | None = None) -> None:
        self.profile = profile
        self.update_rule = update_rule

    def prior(self, error_rate: float) -> float:
        """Pure numerical prior helper used by schedules and standalone callers."""
        return prior_llr(error_rate, profile=self.profile)

    def new_session(self, edge_table, syndrome: np.ndarray, *, error_rate: float):
        """Open an owned Phase 5 session without changing the legacy one-shot run."""
        from .intervention_session import InterventionSession

        if self.update_rule is not None or self.profile != REFERENCE_CPU_F64:
            raise ValueError("intervention sessions currently require the reference SPA kernel")
        return InterventionSession(edge_table, syndrome, error_rate=error_rate)

    def check_message(
        self, incoming: np.ndarray, syndrome: int, *, check_index: int = 0,
        edge_index: int = 0, source_iteration: int = 0,
    ) -> float:
        """Pure check-to-variable update for a single canonical edge."""
        if self.update_rule is not None:
            return self.update_rule.check_to_variable(
                incoming, syndrome=syndrome, check_index=check_index,
                edge_index=edge_index, source_iteration=source_iteration,
            )
        return check_to_variable(incoming, syndrome=syndrome, profile=self.profile)

    def assemble_beliefs(
        self, variable_count: int, edge_variables: tuple[int, ...], messages: np.ndarray, prior: float | np.ndarray,
    ) -> np.ndarray:
        """Pure belief assembly from a complete check-message buffer."""
        prior_values = np.asarray(prior, dtype=np.float64)
        if prior_values.ndim == 0:
            beliefs = np.full(variable_count, float(prior_values), dtype=np.float64)
        elif prior_values.shape == (variable_count,):
            beliefs = np.array(prior_values, dtype=np.float64, copy=True)
        else:
            raise ValueError("prior must be scalar or have one value per variable")
        for variable, message in zip(edge_variables, messages, strict=True):
            beliefs[variable] += message
        return finite_saturate(beliefs, boundary="belief_assembly", profile=self.profile)

    def variable_message(self, belief: float, check_message: float) -> float:
        """Pure variable-to-check exclusion update after beliefs are complete."""
        return float(finite_saturate(belief - check_message, boundary="variable_update", profile=self.profile))

    def candidate_from_beliefs(self, beliefs: np.ndarray) -> np.ndarray:
        """Pure deterministic hard decision with the profile's exact-zero rule."""
        return hard_decision(beliefs, profile=self.profile)

    def run(self, check_matrix: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iterations: int) -> KernelResult:
        from .schedules import EdgeTable, FloodingSchedule

        h = _binary(check_matrix, "check_matrix", ndim=2)
        s = _binary(syndrome, "syndrome", ndim=1)
        if s.shape != (h.shape[0],) or not isinstance(max_iterations, int) or max_iterations < 0 or not math.isfinite(error_rate) or not 0 < error_rate < 1:
            raise ValueError("invalid SPA dimensions or error_rate")
        table = EdgeTable.from_check_matrix(h)
        schedule = FloodingSchedule(table, kernel=self, profile=self.profile)
        v2c = schedule.initialize(error_rate)
        candidate = self.candidate_from_beliefs(np.full(table.variable_count, self.prior(error_rate), dtype=np.float64))
        if table.edge_count == 0:
            return KernelResult(candidate, bool(np.array_equal((h.astype(np.int64) @ candidate) % 2, s)), 0)
        for iteration in range(1, max_iterations + 1):
            sweep = schedule.sweep(v2c, s, error_rate=error_rate)
            candidate = sweep.candidate
            if np.array_equal((h.astype(np.int64) @ candidate) % 2, s):
                return KernelResult(candidate, True, iteration)
            if isinstance(self.profile, BinaryNumericalProfileV2):
                damping = self.profile.v2c_damping
                v2c = finite_saturate(
                    damping * v2c + (1.0 - damping) * sweep.new_v2c,
                    boundary="binary_spa_v2_damped_v2c", profile=self.profile,
                )
            else:
                v2c = sweep.new_v2c
        return KernelResult(candidate, False, max_iterations)
