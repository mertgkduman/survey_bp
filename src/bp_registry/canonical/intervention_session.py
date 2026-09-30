"""Owned, transactional flooding session for decoder-visible interventions."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal

import numpy as np

from .budgets import BudgetTree, WorkVector
from .kernel import BinarySpaKernel
from .schedules import EdgeTable, FloodingSchedule


def _frozen_f64(value: np.ndarray, length: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (length,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite float64 vector of length {length}")
    copied = np.array(array, copy=True)
    copied.setflags(write=False)
    return copied


@dataclass(frozen=True, slots=True)
class BpSessionState:
    """Committed BP state; arrays are private snapshots and contain no truth."""

    prior: np.ndarray
    v2c: np.ndarray
    posterior: np.ndarray
    candidate: np.ndarray
    fixed_indices: tuple[int, ...]
    source_iteration: int
    revision: int
    digest: str


@dataclass(frozen=True, slots=True)
class InterventionProposal:
    """A finite-prior change that can be authorized only by its owning session."""

    action: Literal["finite_prior_bias"]
    target_index: int
    signed_prior: float
    expected_revision: int
    state_before: str
    owner: object


@dataclass(frozen=True, slots=True)
class SessionTransition:
    admitted: bool
    state: BpSessionState
    termination: str | None
    leaf_id: str | None


class BpSession:
    """One continuing flooding attempt with reserve-before-compute semantics."""

    def __init__(self, edge_table: EdgeTable, syndrome: np.ndarray, *, error_rate: float) -> None:
        self.edge_table = edge_table
        bits = np.asarray(syndrome)
        if bits.shape != (edge_table.check_count,) or not np.issubdtype(bits.dtype, np.integer) or np.any((bits != 0) & (bits != 1)):
            raise ValueError("session syndrome must match the graph and be binary")
        self.syndrome = np.array(bits, dtype=np.uint8, copy=True)
        self.syndrome.setflags(write=False)
        self.error_rate = error_rate
        self.kernel = BinarySpaKernel()
        self.schedule = FloodingSchedule(edge_table, kernel=self.kernel)
        self._owner = object()
        prior = np.full(edge_table.variable_count, self.kernel.prior(error_rate), dtype=np.float64)
        v2c = self.schedule.initialize(error_rate)
        posterior = np.array(prior, copy=True)
        candidate = self.kernel.candidate_from_beliefs(posterior)
        self._state = self._make_state(prior, v2c, posterior, candidate, (), 0, 0)

    @property
    def state(self) -> BpSessionState:
        return self._state

    def _make_state(
        self, prior: np.ndarray, v2c: np.ndarray, posterior: np.ndarray,
        candidate: np.ndarray, fixed_indices: tuple[int, ...], source_iteration: int, revision: int,
    ) -> BpSessionState:
        n, e = self.edge_table.variable_count, self.edge_table.edge_count
        p = _frozen_f64(prior, n, "prior")
        v = _frozen_f64(v2c, e, "v2c")
        b = _frozen_f64(posterior, n, "posterior")
        c = np.asarray(candidate)
        if c.shape != (n,) or not np.issubdtype(c.dtype, np.integer) or np.any((c != 0) & (c != 1)):
            raise ValueError("candidate must be a binary original-coordinate vector")
        c = np.array(c, dtype=np.uint8, copy=True)
        c.setflags(write=False)
        payload = {
            "prior": p.tolist(), "v2c": v.tolist(), "posterior": b.tolist(),
            "candidate": c.tolist(), "fixed_indices": fixed_indices,
            "source_iteration": source_iteration, "revision": revision,
        }
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        return BpSessionState(p, v, b, c, fixed_indices, source_iteration, revision, digest)

    def propose_finite_prior(self, target_index: int, signed_prior: float) -> InterventionProposal:
        state = self._state
        if type(target_index) is not int or not 0 <= target_index < self.edge_table.variable_count or target_index in state.fixed_indices:
            raise ValueError("finite-prior target is ineligible")
        if not np.isfinite(signed_prior) or abs(signed_prior) != 25.0:
            raise ValueError("the source-qualified finite prior must have magnitude 25")
        return InterventionProposal("finite_prior_bias", target_index, float(signed_prior), state.revision, state.digest, self._owner)

    def commit_intervention(self, proposal: InterventionProposal, *, budgets: BudgetTree, leaf_id: str) -> SessionTransition:
        state = self._state
        if (proposal.owner is not self._owner or proposal.expected_revision != state.revision
                or proposal.state_before != state.digest):
            raise ValueError("intervention proposal does not own the current session revision")
        reservation = budgets.reserve("attempt", WorkVector(intervention_actions=1), leaf_id=leaf_id)
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            prior = np.array(state.prior, copy=True)
            prior[proposal.target_index] = proposal.signed_prior
            next_state = self._make_state(
                prior, state.v2c, state.posterior, state.candidate,
                (*state.fixed_indices, proposal.target_index), state.source_iteration, state.revision + 1,
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        return SessionTransition(True, next_state, None, leaf_id)

    def advance(self, *, budgets: BudgetTree, leaf_id: str, bp_call_start: bool | None = None) -> SessionTransition:
        """Reserve a complete sweep, compute privately, then atomically swap state."""
        state = self._state
        if bp_call_start is None:
            bp_call_start = state.source_iteration == 0
        if type(bp_call_start) is not bool:
            raise ValueError("bp_call_start must be an explicit boolean")
        work = WorkVector.from_flooding_counts(
            edge_count=self.edge_table.edge_count, variable_count=self.edge_table.variable_count,
        ) + WorkVector(bp_calls=int(bp_call_start))
        reservation = budgets.reserve("attempt", work, leaf_id=leaf_id)
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            sweep = self.schedule.sweep(
                state.v2c, self.syndrome, error_rate=self.error_rate,
                source_iteration=state.source_iteration, prior_llrs=state.prior,
            )
            next_state = self._make_state(
                state.prior, sweep.new_v2c, sweep.beliefs, sweep.candidate,
                state.fixed_indices, state.source_iteration + 1, state.revision + 1,
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        return SessionTransition(True, next_state, None, leaf_id)

    def original_syndrome_valid(self, check_matrix: np.ndarray) -> bool:
        return bool(np.array_equal((np.asarray(check_matrix, dtype=np.int64) @ self._state.candidate) % 2, self.syndrome))
