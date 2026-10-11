"""Owned, transactional flooding session for decoder-visible interventions."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Callable, Iterator, Literal, Mapping

import numpy as np

from .budgets import BudgetTree, WallClockLimit, WorkVector
from .contracts import FinitePriorBiasAction
from .kernel import BinarySpaKernel
from .memory import V2CDamping, V2CDampingState, TargetMemoryProposal
from .schedules import EdgeTable, FloodingSchedule


_phase5_boundary_observer: ContextVar[Callable[[str, WorkVector | None, str | None], None] | None] = ContextVar(
    "phase5_boundary_observer", default=None,
)


@contextmanager
def observe_phase5_boundaries(
    observer: Callable[[str, WorkVector | None, str | None], None] | None,
) -> Iterator[None]:
    """Scope optional runtime boundary observation to one Phase-5 controller call."""
    token = _phase5_boundary_observer.set(observer)
    try:
        yield
    finally:
        _phase5_boundary_observer.reset(token)


def _before_phase5_work(leaf_id: str) -> None:
    observer = _phase5_boundary_observer.get()
    if observer is not None:
        observer(f"phase5:{leaf_id}:before_work", None, None)


def _after_phase5_work(leaf_id: str, budgets: BudgetTree, *, scope: str = "attempt") -> None:
    observer = _phase5_boundary_observer.get()
    if observer is not None:
        observer(f"phase5:{leaf_id}:after_work", budgets.summary(scope), leaf_id)


def before_phase5_work(leaf_id: str) -> None:
    """Expose a named pre-commit boundary for controller-owned atomic work."""
    _before_phase5_work(leaf_id)


def after_phase5_work(leaf_id: str, budgets: BudgetTree, *, scope: str = "attempt") -> None:
    """Expose an exact post-commit boundary for controller-owned atomic work."""
    _after_phase5_work(leaf_id, budgets, scope=scope)


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
    c2v: np.ndarray
    graph_identity: str
    prior_identity: str
    dtype: Literal["float64"]
    owner_identity: str
    coordinate_identity: str
    schedule_cursor: tuple[int, ...]
    residual_cache: None
    private_histories: tuple[object, ...]
    mutation_evidence: Mapping[str, tuple[str, ...]]
    pending_sign_target: int | None


@dataclass(frozen=True, slots=True)
class InterventionProposal:
    """A finite-prior change that can be authorized only by its owning session."""

    action: Literal["finite_prior_bias"]
    target_index: int
    signed_prior: float
    expected_revision: int
    state_before: str
    owner: object
    action_payload: FinitePriorBiasAction
    anticipated_work: WorkVector
    source_variant: str = "algorithm1_v2_interpretation"
    target_order: tuple[int, ...] = ()
    reset_fields: tuple[str, ...] = ()
    preserved_fields: tuple[str, ...] = ("graph", "syndrome", "v2c", "c2v")
    stream_identity: str = "not_applicable"
    child_lineage_id: str = ""


@dataclass(frozen=True, slots=True)
class SessionTransition:
    admitted: bool
    state: BpSessionState
    termination: str | None
    leaf_id: str | None


def decoder_stream_identity(root: str, decoder: str, intervention: str, attempt: int, purpose: str) -> str:
    """Stable decoder RNG namespace, disjoint from physical sampling."""
    if (any(not isinstance(value, str) or not value for value in (root, decoder, intervention, purpose))
            or type(attempt) is not int or attempt < 0 or purpose == "physical_sampling"):
        raise ValueError("decoder stream needs nonempty identities, a bounded attempt, and a decoder-only purpose")
    content = ["decoder-intervention-stream-v1", root, decoder, intervention, attempt, purpose]
    return "decoder-stream-" + sha256(json.dumps(content, separators=(",", ":")).encode()).hexdigest()


class BpSession:
    """One continuing flooding attempt with reserve-before-compute semantics."""

    def __init__(
        self, edge_table: EdgeTable, syndrome: np.ndarray, *, error_rate: float,
        owner_identity: str | None = None, kernel: BinarySpaKernel | None = None,
        damping_gamma: float | None = None,
        v2c_clip: float | None = None,
    ) -> None:
        self.edge_table = edge_table
        bits = np.asarray(syndrome)
        if bits.shape != (edge_table.check_count,) or not np.issubdtype(bits.dtype, np.integer) or np.any((bits != 0) & (bits != 1)):
            raise ValueError("session syndrome must match the graph and be binary")
        self.syndrome = np.array(bits, dtype=np.uint8, copy=True)
        self.syndrome.setflags(write=False)
        self.error_rate = error_rate
        if kernel is not None and not isinstance(kernel, BinarySpaKernel):
            raise ValueError("intervention session kernel must be a canonical binary kernel")
        self.kernel = kernel or BinarySpaKernel()
        self.schedule = FloodingSchedule(edge_table, kernel=self.kernel)
        if v2c_clip is not None and (
            type(v2c_clip) not in (int, float) or not math.isfinite(v2c_clip) or v2c_clip <= 0.0 or v2c_clip != 25.0
        ):
            raise ValueError("v2c clip must be the registered finite source control of magnitude 25")
        if damping_gamma is not None and v2c_clip is not None:
            raise ValueError("v2c clip cannot be combined with damping")
        self.damping_gamma = damping_gamma
        self.v2c_clip = None if v2c_clip is None else float(v2c_clip)
        self._damping_policy = None if damping_gamma is None else V2CDamping("phase5-v2c-damping", damping_gamma)
        self._owner = object()
        if owner_identity is not None and (not isinstance(owner_identity, str) or not owner_identity):
            raise ValueError("owner identity must be a nonempty string")
        self.owner_identity = owner_identity or "session-" + sha256(json.dumps(
            [edge_table.graph_sha256, self.syndrome.tolist(), error_rate],
            separators=(",", ":"), allow_nan=False,
        ).encode()).hexdigest()[:20]
        prior = np.full(edge_table.variable_count, self.kernel.prior(error_rate), dtype=np.float64)
        v2c = self.schedule.initialize(error_rate)
        self._damping_state: V2CDampingState | None = (
            None if self._damping_policy is None else self._damping_policy.initial_state(v2c)
        )
        posterior = np.array(prior, copy=True)
        candidate = self.kernel.candidate_from_beliefs(posterior)
        self._state = self._make_state(prior, v2c, posterior, candidate, (), 0, 0)

    @property
    def state(self) -> BpSessionState:
        return self._state

    def _make_state(
        self, prior: np.ndarray, v2c: np.ndarray, posterior: np.ndarray,
        candidate: np.ndarray, fixed_indices: tuple[int, ...], source_iteration: int, revision: int,
        *, c2v: np.ndarray | None = None,
        mutation_evidence: Mapping[str, tuple[str, ...]] | None = None,
        pending_sign_target: int | None = None,
        memory_history: np.ndarray | None = None,
    ) -> BpSessionState:
        n, e = self.edge_table.variable_count, self.edge_table.edge_count
        p = _frozen_f64(prior, n, "prior")
        v = _frozen_f64(v2c, e, "v2c")
        b = _frozen_f64(posterior, n, "posterior")
        c2v_snapshot = _frozen_f64(np.zeros(e) if c2v is None else c2v, e, "c2v")
        c = np.asarray(candidate)
        if c.shape != (n,) or not np.issubdtype(c.dtype, np.integer) or np.any((c != 0) & (c != 1)):
            raise ValueError("candidate must be a binary original-coordinate vector")
        c = np.array(c, dtype=np.uint8, copy=True)
        c.setflags(write=False)
        if pending_sign_target is not None and (type(pending_sign_target) is not int or not 0 <= pending_sign_target < n):
            raise ValueError("pending sign target must be a valid variable")
        prior_identity = sha256(p.tobytes()).hexdigest()
        coordinate_identity = sha256(json.dumps(list(range(n))).encode()).hexdigest()
        evidence = MappingProxyType(dict(mutation_evidence or {}))
        payload = {
            "prior": p.tolist(), "v2c": v.tolist(), "posterior": b.tolist(),
            "c2v": c2v_snapshot.tolist(), "graph_identity": self.edge_table.graph_sha256,
            "prior_identity": prior_identity, "dtype": "float64", "owner_identity": self.owner_identity,
            "coordinate_identity": coordinate_identity,
            "candidate": c.tolist(), "fixed_indices": fixed_indices,
            "source_iteration": source_iteration, "revision": revision,
            "schedule_cursor": (source_iteration,), "mutation_evidence": dict(evidence),
            "pending_sign_target": pending_sign_target,
        }
        if self.v2c_clip is not None:
            payload["v2c_clip"] = self.v2c_clip
        if self._damping_state is not None:
            history = _frozen_f64(
                self._damping_state.v2c if memory_history is None else memory_history,
                e, "damping_history",
            )
            payload["damping_gamma"] = self.damping_gamma
            payload["damping_history_sha256"] = sha256(history.tobytes()).hexdigest()
            private_histories: tuple[object, ...] = (history,)
        else:
            private_histories = ()
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        return BpSessionState(
            p, v, b, c, fixed_indices, source_iteration, revision, digest,
            c2v_snapshot, self.edge_table.graph_sha256, prior_identity, "float64",
            self.owner_identity, coordinate_identity, (source_iteration,), None, private_histories, evidence,
            pending_sign_target,
        )

    def _v2c_transform(self, fresh: np.ndarray) -> np.ndarray:
        """Apply the source V2C-only control after construction, before commit."""
        if self.v2c_clip is None:
            return fresh
        return np.clip(np.asarray(fresh, dtype=np.float64), -self.v2c_clip, self.v2c_clip)

    def propose_finite_prior(
        self, target_index: int, signed_prior: float, *,
        source_variant: str = "algorithm1_v2_interpretation",
        target_order: tuple[int, ...] | None = None,
    ) -> InterventionProposal:
        state = self._state
        if type(target_index) is not int or not 0 <= target_index < self.edge_table.variable_count or target_index in state.fixed_indices:
            raise ValueError("finite-prior target is ineligible")
        if not np.isfinite(signed_prior) or abs(signed_prior) != 25.0:
            raise ValueError("the source-qualified finite prior must have magnitude 25")
        order = (target_index,) if target_order is None else tuple(target_order)
        if (not order or target_index not in order or len(order) != len(set(order))
                or any(type(index) is not int or not 0 <= index < self.edge_table.variable_count for index in order)
                or not source_variant):
            raise ValueError("proposal target order and source variant must be explicit and valid")
        child_identity = sha256(json.dumps(
            [state.digest, target_index, signed_prior], separators=(",", ":")
        ).encode()).hexdigest()
        return InterventionProposal(
            "finite_prior_bias", target_index, float(signed_prior), state.revision,
            state.digest, self._owner,
            FinitePriorBiasAction(kind="finite_prior_bias", target_index=target_index, signed_llr=float(signed_prior)),
            WorkVector(intervention_actions=1, fixation_actions=1),
            source_variant=source_variant, target_order=order,
            child_lineage_id="working-" + child_identity[:20],
        )

    def commit_intervention(
        self, proposal: InterventionProposal, *, budgets: BudgetTree, leaf_id: str,
        wall_clock: WallClockLimit | None = None,
    ) -> SessionTransition:
        state = self._state
        if proposal.owner is not self._owner:
            raise ValueError("foreign intervention proposal owner")
        if proposal.expected_revision != state.revision or proposal.state_before != state.digest:
            raise ValueError("stale intervention proposal revision or before-state")
        expected_work = WorkVector(intervention_actions=1, fixation_actions=1)
        if (proposal.action != "finite_prior_bias" or proposal.action_payload.kind != proposal.action
                or proposal.action_payload.target_index != proposal.target_index
                or proposal.action_payload.signed_llr != proposal.signed_prior
                or proposal.anticipated_work != expected_work
                or not proposal.child_lineage_id.startswith("working-")
                or proposal.target_index not in proposal.target_order):
            raise ValueError("untrusted intervention proposal action or work declaration")
        _before_phase5_work(leaf_id)
        if wall_clock is not None and wall_clock.check("candidate_selection_boundary", scope="attempt") is not None:
            return SessionTransition(False, state, "wall_clock_deadline", None)
        reservation = budgets.reserve("attempt", proposal.anticipated_work, leaf_id=leaf_id)
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            prior = np.array(state.prior, copy=True)
            prior[proposal.target_index] = proposal.signed_prior
            next_state = self._make_state(
                prior, state.v2c, state.posterior, state.candidate,
                (*state.fixed_indices, proposal.target_index), state.source_iteration, state.revision + 1,
                c2v=state.c2v,
                mutation_evidence={
                    "preserved": ("graph", "syndrome", "v2c", "c2v", "posterior"),
                    "recomputed": ("prior_identity",), "invalidated": (),
                },
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        _after_phase5_work(leaf_id, budgets)
        return SessionTransition(True, next_state, None, leaf_id)

    def advance(
        self, *, budgets: BudgetTree, leaf_id: str, bp_call_start: bool | None = None,
        wall_clock: WallClockLimit | None = None,
    ) -> SessionTransition:
        """Reserve a complete sweep, compute privately, then atomically swap state."""
        state = self._state
        if bp_call_start is None:
            bp_call_start = state.source_iteration == 0
        if type(bp_call_start) is not bool:
            raise ValueError("bp_call_start must be an explicit boolean")
        work = WorkVector.from_flooding_counts(
            edge_count=self.edge_table.edge_count, variable_count=self.edge_table.variable_count,
        ) + WorkVector(bp_calls=int(bp_call_start))
        pending_edges = tuple(
            index for index, (_check, variable) in enumerate(self.edge_table.edges)
            if variable == state.pending_sign_target
        ) if state.pending_sign_target is not None else ()
        if pending_edges:
            work = work + WorkVector(variable_to_check_updates=len(pending_edges))
        _before_phase5_work(leaf_id)
        if wall_clock is not None and wall_clock.check("iteration_boundary", scope="attempt") is not None:
            return SessionTransition(False, state, "wall_clock_deadline", None)
        reservation = budgets.reserve("attempt", work, leaf_id=leaf_id)
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            input_v2c = np.array(state.v2c, copy=True)
            for edge_index in pending_edges:
                input_v2c[edge_index] = self.kernel.variable_message(
                    float(state.posterior[state.pending_sign_target]), float(state.c2v[edge_index]),
                )
            memory_proposal: TargetMemoryProposal | None = None

            def transform_v2c(fresh: np.ndarray) -> np.ndarray:
                nonlocal memory_proposal
                transformed = self._v2c_transform(fresh)
                if self._damping_policy is not None:
                    assert self._damping_state is not None
                    memory_proposal = self._damping_policy.propose(
                        self._damping_state.v2c, transformed, boundary="source_iteration",
                    )
                    return memory_proposal.value
                return transformed

            sweep = self.schedule.sweep(
                input_v2c, self.syndrome, error_rate=self.error_rate,
                source_iteration=state.source_iteration, prior_llrs=state.prior,
                transform_v2c=transform_v2c if self._damping_policy is not None or self.v2c_clip is not None else None,
            )
            next_state = self._make_state(
                state.prior, sweep.new_v2c, sweep.beliefs, sweep.candidate,
                state.fixed_indices, state.source_iteration + 1, state.revision + 1,
                c2v=sweep.check_to_variable,
                mutation_evidence={
                    "preserved": ("graph", "syndrome", "prior"),
                    "recomputed": ("c2v", "posterior", "candidate", "v2c"),
                    "invalidated": ("pending_sign_target",) if pending_edges else (),
                },
                memory_history=None if memory_proposal is None else memory_proposal.history[0],
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        if memory_proposal is not None:
            assert self._damping_policy is not None and self._damping_state is not None
            self._damping_state = self._damping_policy.commit(memory_proposal, self._damping_state)
        self._state = next_state
        _after_phase5_work(leaf_id, budgets)
        return SessionTransition(True, next_state, None, leaf_id)

    def original_syndrome_valid(self, check_matrix: np.ndarray) -> bool:
        return bool(np.array_equal((np.asarray(check_matrix, dtype=np.int64) @ self._state.candidate) % 2, self.syndrome))

    def continue_units(
        self, count: int, *, budgets: BudgetTree, leaf_prefix: str,
        wall_clock: WallClockLimit | None = None,
    ) -> tuple[SessionTransition, ...]:
        if type(count) is not int or not 1 <= count <= 100_000 or not leaf_prefix:
            raise ValueError("continuation requires a finite positive unit count and leaf prefix")
        results: list[SessionTransition] = []
        for index in range(count):
            result = self.advance(
                budgets=budgets, leaf_id=f"{leaf_prefix}:{index}", bp_call_start=index == 0,
                wall_clock=wall_clock,
            )
            results.append(result)
            if not result.admitted:
                break
        return tuple(results)

    def reset_fresh(
        self, *, budgets: BudgetTree, leaf_id: str, edge_table: EdgeTable | None = None,
        syndrome: np.ndarray | None = None, error_rate: float | None = None,
        preserve: tuple[str, ...] = (), owner_identity: str | None = None,
        wall_clock: WallClockLimit | None = None,
    ) -> "BpSession":
        """Create an independent branch; only a complete compatible state may carry over."""
        table = self.edge_table if edge_table is None else edge_table
        next_syndrome = self.syndrome if syndrome is None else syndrome
        next_rate = self.error_rate if error_rate is None else error_rate
        preserve_set = frozenset(preserve)
        complete = frozenset({"v2c", "c2v", "posterior", "candidate"})
        if preserve_set and (
            preserve_set != complete or table.graph_sha256 != self.edge_table.graph_sha256
            or not np.array_equal(next_syndrome, self.syndrome)
            or next_rate != self.error_rate
            or (owner_identity is not None and owner_identity != self.state.owner_identity)
        ):
            raise ValueError("incompatible graph, coordinate, prior, dtype, or owner for preserved BP state")
        _before_phase5_work(leaf_id)
        if wall_clock is not None and wall_clock.check("candidate_selection_boundary", scope="attempt") is not None:
            raise ValueError("reset denied by wall-clock deadline; parent state remains unchanged")
        reservation = budgets.reserve("attempt", WorkVector(intervention_actions=1), leaf_id=leaf_id)
        if reservation is None:
            raise ValueError("reset denied by count budget; parent state remains unchanged")
        try:
            branch_owner = "session-" + sha256(json.dumps(
                [self.state.owner_identity, leaf_id, table.graph_sha256, next_rate],
                separators=(",", ":"), allow_nan=False,
            ).encode()).hexdigest()[:20]
            child = type(self)(
                table, next_syndrome, error_rate=next_rate, owner_identity=branch_owner,
                kernel=self.kernel, damping_gamma=self.damping_gamma, v2c_clip=self.v2c_clip,
            )
            if preserve_set:
                if self._damping_state is not None:
                    child._damping_state = self._damping_state
                old = self.state
                child._state = child._make_state(
                    old.prior, old.v2c, old.posterior, old.candidate,
                    old.fixed_indices, old.source_iteration, 0, c2v=old.c2v,
                    mutation_evidence={
                        "preserved": tuple(sorted(preserve_set)), "recomputed": (), "invalidated": (),
                    },
                    pending_sign_target=old.pending_sign_target,
                )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        _after_phase5_work(leaf_id, budgets)
        return child

    def mutate_posterior_sign(
        self, target_index: int, *, budgets: BudgetTree, leaf_id: str,
        wall_clock: WallClockLimit | None = None,
    ) -> SessionTransition:
        """Flip a committed posterior and refresh only its outgoing V2C edges."""
        state = self.state
        if (type(target_index) is not int or not 0 <= target_index < self.edge_table.variable_count
                or state.source_iteration == 0):
            raise ValueError("posterior sign mutation requires a completed sweep and valid target")
        edge_indices = tuple(i for i, (_, variable) in enumerate(self.edge_table.edges) if variable == target_index)
        work = WorkVector(intervention_actions=1, variable_to_check_updates=len(edge_indices), candidate_constructions=1)
        _before_phase5_work(leaf_id)
        if wall_clock is not None and wall_clock.check("candidate_selection_boundary", scope="attempt") is not None:
            return SessionTransition(False, state, "wall_clock_deadline", None)
        reservation = budgets.reserve("attempt", work, leaf_id=leaf_id)
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            posterior = np.array(state.posterior, copy=True)
            posterior[target_index] = -posterior[target_index]
            v2c = np.array(state.v2c, copy=True)
            for edge_index in edge_indices:
                v2c[edge_index] = self.kernel.variable_message(float(posterior[target_index]), float(state.c2v[edge_index]))
            candidate = self.kernel.candidate_from_beliefs(posterior)
            next_state = self._make_state(
                state.prior, v2c, posterior, candidate, state.fixed_indices,
                state.source_iteration, state.revision + 1, c2v=state.c2v,
                mutation_evidence={
                    "preserved": ("prior", "c2v", "graph", "syndrome"),
                    "recomputed": ("target_v2c", "target_hard_decision"), "invalidated": (),
                },
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        _after_phase5_work(leaf_id, budgets)
        return SessionTransition(True, next_state, None, leaf_id)

    def stage_posterior_sign(
        self, target_index: int, *, budgets: BudgetTree, leaf_id: str,
        wall_clock: WallClockLimit | None = None,
    ) -> SessionTransition:
        """Change only posterior and decision now; use it on outgoing edges next sweep."""
        state = self.state
        if (type(target_index) is not int or not 0 <= target_index < self.edge_table.variable_count
                or state.source_iteration == 0 or state.pending_sign_target is not None):
            raise ValueError("staged posterior sign requires a completed sweep and no pending mutation")
        _before_phase5_work(leaf_id)
        if wall_clock is not None and wall_clock.check("candidate_selection_boundary", scope="attempt") is not None:
            return SessionTransition(False, state, "wall_clock_deadline", None)
        reservation = budgets.reserve(
            "attempt", WorkVector(intervention_actions=1, candidate_constructions=1), leaf_id=leaf_id,
        )
        if reservation is None:
            return SessionTransition(False, state, "count_budget_exhausted", None)
        try:
            posterior = np.array(state.posterior, copy=True)
            posterior[target_index] = -posterior[target_index]
            candidate = self.kernel.candidate_from_beliefs(posterior)
            next_state = self._make_state(
                state.prior, state.v2c, posterior, candidate, state.fixed_indices,
                state.source_iteration, state.revision + 1, c2v=state.c2v,
                mutation_evidence={
                    "preserved": ("prior", "v2c", "c2v", "graph", "syndrome"),
                    "recomputed": ("target_posterior", "target_hard_decision"),
                    "invalidated": ("pending_outgoing_target",),
                },
                pending_sign_target=target_index,
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        _after_phase5_work(leaf_id, budgets)
        return SessionTransition(True, next_state, None, leaf_id)


class InterventionSession(BpSession):
    """Named reusable Phase 5 session API; BpSession remains the tracer alias."""
