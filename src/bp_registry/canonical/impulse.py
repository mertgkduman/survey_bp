"""Bounded CSS impulse search with source and structural realizations kept distinct."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Callable, Literal, Mapping, Sequence, TypeVar

import numpy as np

from .budgets import BudgetLimit, BudgetTree, WorkVector
from .intervention_session import BpSession, SessionTransition
from .numerics import NumericalFailure
from .problems import OriginalProblem
from .schedules import EdgeTable
from .transformations import lift_candidate, transform_fixed_coordinates


Realization = Literal["semantic_forced_one", "exact_shortening"]
Selection = Literal["minimum_original_weight", "first_convergence"]
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ImpulseSpec:
    realization: Realization
    selection: Selection
    baseline_sweeps: int
    attempt_sweeps: int
    attempt_cap: int
    coordinate_order: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if self.coordinate_order is not None:
            object.__setattr__(self, "coordinate_order", tuple(self.coordinate_order))
        if self.realization not in ("semantic_forced_one", "exact_shortening"):
            raise ValueError("impulse realization must name a supported source or structural route")
        if self.selection not in ("minimum_original_weight", "first_convergence"):
            raise ValueError("impulse selection mode is invalid")
        if any(type(value) is not int or not 1 <= value <= 100_000 for value in (self.baseline_sweeps, self.attempt_sweeps, self.attempt_cap)):
            raise ValueError("impulse sweeps and cap must be finite positive integers")
        if self.coordinate_order is not None and (
            any(type(index) is not int or index < 0 for index in self.coordinate_order)
            or len(set(self.coordinate_order)) != len(self.coordinate_order)
        ):
            raise ValueError("impulse coordinate order must be unique nonnegative original indices")


@dataclass(frozen=True, slots=True)
class ImpulseAttempt:
    order: int
    target_index: int
    realization: Realization
    source_operator: str
    qualification: str
    forced_value: int
    working_lineage_id: str
    graph_identity: str
    session_owner: str
    initial_state_digest: str | None
    initial_iteration: int
    final_state_digest: str | None
    diagnostic_candidate: tuple[int, ...] | None
    lifted_candidate: tuple[int, ...] | None
    lift_digest: str | None
    original_valid: bool | None
    termination: str
    action_leaf: str | None
    sweep_leaves: tuple[str, ...]
    validation_leaf: str | None
    local_order: int = 0


@dataclass(frozen=True, slots=True)
class ImpulseResult:
    realization: Realization
    canonical_identity: str
    native_status: str
    selection: Selection
    root_owner: str
    original_lineage_id: str
    baseline_graph_identity: str
    baseline_initial_digest: str
    baseline_final_digest: str
    baseline_diagnostic_candidate: tuple[int, ...] | None
    baseline_valid: bool | None
    baseline_termination: str
    attempts: tuple[ImpulseAttempt, ...]
    selected_candidate: tuple[int, ...] | None
    selected_origin: int | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]

    @property
    def qualification(self) -> str:
        return (
            "source_operator_semantic_adaptation" if self.realization == "semantic_forced_one"
            else "controlled_css_adaptation"
        )

    def as_evidence(self) -> dict[str, object]:
        """JSON-safe evidence; negative infinity is a symbolic operator only."""
        record = asdict(self)
        record["work"] = self.work.as_evidence(structural_event_version=4)
        record["leaves"] = [
            {"leaf_id": leaf_id, "scope": scope, "work": vector.as_evidence(structural_event_version=4)}
            for leaf_id, scope, vector in self.leaves
        ]
        return record


def _candidate(bits: np.ndarray) -> tuple[int, ...]:
    return tuple(int(bit) for bit in bits)


def _valid(original: OriginalProblem, bits: tuple[int, ...]) -> bool:
    return bool(np.array_equal(
        (original.hz.astype(np.int64) @ np.asarray(bits, dtype=np.int64)) % 2,
        original.syndrome,
    ))


def _reserve_check(
    budgets: BudgetTree, leaf_id: str, compute: Callable[[], T], *, lifted: int = 0,
) -> tuple[bool, T | None]:
    reservation = budgets.reserve(
        "attempt", WorkVector(original_checks=1, lifted_coordinates=lifted), leaf_id=leaf_id,
    )
    if reservation is None:
        return False, None
    try:
        result = compute()
    except BaseException:
        reservation.rollback()
        raise
    reservation.commit_once()
    return True, result


class _ForcedOneSession(BpSession):
    """Unchanged-graph, hard-bit forcing with finite SPA saturation.

    The source's -infinity channel instruction is represented symbolically.
    Every outgoing target edge and hard decision is clamped to one, while the
    finite numerical messages use -25. This is not a native trajectory claim.
    """

    def __init__(self, table: EdgeTable, syndrome: np.ndarray, *, error_rate: float, owner_identity: str, target: int) -> None:
        super().__init__(table, syndrome, error_rate=error_rate, owner_identity=owner_identity)
        self.target = target
        prior = np.array(self.state.prior, copy=True)
        prior[target] = -25.0
        v2c = np.array(self.state.v2c, copy=True)
        for edge_index, (_check, variable) in enumerate(table.edges):
            if variable == target:
                v2c[edge_index] = -25.0
        posterior = np.array(self.state.posterior, copy=True)
        posterior[target] = -25.0
        candidate = np.array(self.state.candidate, copy=True)
        candidate[target] = 1
        self._state = self._make_state(prior, v2c, posterior, candidate, (target,), 0, 0)

    def advance(self, *, budgets: BudgetTree, leaf_id: str, bp_call_start: bool | None = None) -> SessionTransition:
        state = self.state
        if bp_call_start is None:
            bp_call_start = state.source_iteration == 0
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
            v2c = np.array(sweep.new_v2c, copy=True)
            for edge_index, (_check, variable) in enumerate(self.edge_table.edges):
                if variable == self.target:
                    v2c[edge_index] = -25.0
            beliefs = np.array(sweep.beliefs, copy=True)
            beliefs[self.target] = -25.0
            candidate = np.array(sweep.candidate, copy=True)
            candidate[self.target] = 1
            next_state = self._make_state(
                state.prior, v2c, beliefs, candidate, state.fixed_indices,
                state.source_iteration + 1, state.revision + 1,
                c2v=sweep.check_to_variable,
                mutation_evidence={
                    "preserved": ("graph", "syndrome", "forced_target"),
                    "recomputed": ("c2v", "posterior", "candidate", "v2c"),
                    "invalidated": (),
                },
            )
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        self._state = next_state
        return SessionTransition(True, next_state, None, leaf_id)


def select_impulse_candidate(
    attempts: Sequence[ImpulseAttempt], original: OriginalProblem, *, mode: Selection,
) -> ImpulseAttempt | None:
    """Select only independently valid lifted candidates in declared order."""
    if mode not in ("minimum_original_weight", "first_convergence"):
        raise ValueError("unsupported impulse selection mode")
    eligible = [
        row for row in attempts
        if row.original_valid is True and row.lifted_candidate is not None
        and len(row.lifted_candidate) == original.hz.shape[1]
        and _valid(original, row.lifted_candidate)
    ]
    if mode == "first_convergence":
        return min(eligible, key=lambda row: (row.order, row.target_index, row.local_order), default=None)
    return min(
        eligible,
        key=lambda row: (sum(row.lifted_candidate or ()), row.order, row.target_index, row.local_order),
        default=None,
    )


class ImpulseController:
    def __init__(self, spec: ImpulseSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, ImpulseSpec) else ImpulseSpec(**spec)

    def run(
        self, original: OriginalProblem, *, error_rate: float, budgets: BudgetTree,
        owner_identity: str | None = None,
    ) -> ImpulseResult:
        if not isinstance(original, OriginalProblem):
            raise ValueError("impulse requires an immutable original problem")
        n = original.hz.shape[1]
        order = self.spec.coordinate_order or tuple(range(n))
        if tuple(sorted(order)) != tuple(range(n)):
            raise ValueError("impulse order must enumerate every original coordinate exactly once")
        root = owner_identity or "impulse-" + sha256(json.dumps(
            [original.lineage_id, original.hz.tolist(), original.syndrome.tolist(), error_rate, asdict(self.spec)],
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode()).hexdigest()[:20]
        if not isinstance(root, str) or not root:
            raise ValueError("impulse owner identity must be a nonempty string")
        baseline = BpSession(
            EdgeTable.from_check_matrix(original.hz), original.syndrome,
            error_rate=error_rate, owner_identity=f"{root}:baseline",
        )
        initial_digest = baseline.state.digest
        baseline_valid: bool | None = None
        baseline_term = "baseline_sweep_cap"
        for index in range(self.spec.baseline_sweeps):
            try:
                moved = baseline.advance(
                    budgets=budgets, leaf_id=f"{root}:baseline:sweep:{index}", bp_call_start=index == 0,
                )
            except (NumericalFailure, ValueError, FloatingPointError):
                baseline_term = "numerical_failure"
                break
            if not moved.admitted:
                baseline_term = moved.termination or "count_budget_exhausted"
                break
            check_leaf = f"{root}:baseline:original-check:{index}"
            admitted, baseline_valid = _reserve_check(
                budgets, check_leaf, lambda: baseline.original_syndrome_valid(original.hz),
            )
            if not admitted:
                baseline_term = "count_budget_exhausted"
                break
            if baseline_valid:
                baseline_term = "baseline_valid"
                break
        diagnostic = _candidate(baseline.state.candidate)
        attempts: list[ImpulseAttempt] = []
        selected: ImpulseAttempt | None = None
        termination = baseline_term if baseline_term != "baseline_sweep_cap" else "no_proposal"
        if baseline_valid:
            selected_candidate = diagnostic
            termination = "baseline_valid"
        elif baseline_term in ("count_budget_exhausted", "numerical_failure"):
            selected_candidate = None
            termination = baseline_term
        else:
            selected_candidate = None
            for attempt_order, target in enumerate(order[:self.spec.attempt_cap]):
                row = self._attempt(original, error_rate, budgets, root, attempt_order, target)
                attempts.append(row)
                if row.termination == "count_budget_exhausted":
                    termination = "count_budget_exhausted"
                    break
                if self.spec.selection == "first_convergence" and row.original_valid:
                    break
            if termination != "count_budget_exhausted":
                rank_leaf = f"{root}:selection"
                reservation = budgets.reserve(
                    "attempt", WorkVector(ranking_scans=len(attempts)), leaf_id=rank_leaf,
                )
                if reservation is None:
                    termination = "count_budget_exhausted"
                else:
                    try:
                        selected = select_impulse_candidate(attempts, original, mode=self.spec.selection)
                    except BaseException:
                        reservation.rollback()
                        raise
                    reservation.commit_once()
                    if selected is not None:
                        selected_candidate = selected.lifted_candidate
                        termination = "impulse_valid"
                    else:
                        termination = "attempt_cap_reached" if self.spec.attempt_cap < len(order) else "no_proposal"
        identity = (
            "impulse_negative_infinite_semantic_v1" if self.spec.realization == "semantic_forced_one"
            else "impulse_exact_shortening_css_v1"
        )
        return ImpulseResult(
            self.spec.realization, identity, "author_code_unverified", self.spec.selection,
            root, original.lineage_id, baseline.edge_table.graph_sha256,
            initial_digest, baseline.state.digest, diagnostic, baseline_valid, baseline_term,
            tuple(attempts), selected_candidate, None if selected is None else selected.order,
            termination, budgets.summary("attempt"), budgets.leaf_events(),
        )

    def _attempt(
        self, original: OriginalProblem, error_rate: float, budgets: BudgetTree,
        root: str, order: int, target: int,
    ) -> ImpulseAttempt:
        mode = self.spec.realization
        owner = f"{root}:attempt:{order}:target:{target}"
        action_leaf = f"{owner}:action"
        action_work = WorkVector(
            intervention_actions=1, fixation_actions=1,
            transformations=int(mode == "exact_shortening"),
        )
        reservation = budgets.reserve("attempt", action_work, leaf_id=action_leaf)
        if reservation is None:
            return self._row(order, target, mode, original.lineage_id, "", owner, None, None, None, None, None, "count_budget_exhausted", None, (), None)
        try:
            if mode == "exact_shortening":
                working, certificate = transform_fixed_coordinates(original, (target,), (1,))
                table = EdgeTable.from_check_matrix(working.check_matrix)
                session: BpSession = BpSession(table, working.syndrome, error_rate=error_rate, owner_identity=owner)
                working_id = working.lineage_id
                lift_digest = certificate.digest
            else:
                table = EdgeTable.from_check_matrix(original.hz)
                session = _ForcedOneSession(table, original.syndrome, error_rate=error_rate, owner_identity=owner, target=target)
                working_id = "identity:" + original.lineage_id + f":forced:{target}"
                lift_digest = None
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        initial = session.state.digest
        sweep_leaves: list[str] = []
        lifted: tuple[int, ...] | None = None
        diagnostic: tuple[int, ...] | None = None
        original_valid: bool | None = None
        validation_leaf: str | None = None
        term = "attempt_sweep_cap"
        for sweep_index in range(self.spec.attempt_sweeps):
            # A contradictory empty check is an exact algebraic terminal.
            if mode == "exact_shortening":
                empty = np.count_nonzero(working.check_matrix, axis=1) == 0
                if np.any(empty & (working.syndrome == 1)):
                    term = "contradictory_empty_check"
                    break
            leaf = f"{owner}:sweep:{sweep_index}"
            try:
                moved = session.advance(budgets=budgets, leaf_id=leaf, bp_call_start=sweep_index == 0)
            except (NumericalFailure, ValueError, FloatingPointError):
                term = "numerical_failure"
                break
            if not moved.admitted:
                term = moved.termination or "count_budget_exhausted"
                break
            sweep_leaves.append(leaf)
            diagnostic = _candidate(session.state.candidate)
            check_leaf = f"{owner}:lift-original-check:{sweep_index}"
            if mode == "exact_shortening":
                try:
                    admitted, lift = _reserve_check(
                        budgets, check_leaf,
                        lambda: lift_candidate(working, certificate, session.state.candidate),
                        lifted=original.hz.shape[1],
                    )
                except ValueError:
                    term = "invalid_lift"
                    break
                if not admitted:
                    term = "count_budget_exhausted"
                    break
                assert lift is not None
                validation_leaf = check_leaf
                lifted = _candidate(lift.candidate)
                original_valid = lift.original_valid and lift.working_valid
                term = "valid_original_candidate" if original_valid else (lift.reason or "working_syndrome_invalid")
            else:
                assert diagnostic is not None
                admitted, original_valid = _reserve_check(
                    budgets, check_leaf, lambda: _valid(original, diagnostic),
                )
                if not admitted:
                    term = "count_budget_exhausted"
                    break
                validation_leaf = check_leaf
                lifted = diagnostic
                term = "valid_original_candidate" if original_valid else "original_syndrome_invalid"
            if original_valid:
                break
        return self._row(
            order, target, mode, working_id, table.graph_sha256, owner,
            initial, session.state.digest, diagnostic, lifted, lift_digest,
            term, action_leaf, tuple(sweep_leaves), validation_leaf, original_valid,
        )

    @staticmethod
    def _row(
        order: int, target: int, mode: Realization, working_id: str, graph_id: str,
        owner: str, initial: str | None, final: str | None,
        diagnostic: tuple[int, ...] | None, lifted: tuple[int, ...] | None,
        lift_digest: str | None, term: str, action_leaf: str | None,
        sweeps: tuple[str, ...], validation_leaf: str | None,
        original_valid: bool | None = None,
    ) -> ImpulseAttempt:
        return ImpulseAttempt(
            order, target, mode,
            "negative_infinite_llr" if mode == "semantic_forced_one" else "exact_fixed_one",
            "source_operator_semantic_adaptation" if mode == "semantic_forced_one" else "controlled_css_adaptation",
            1, working_id, graph_id, owner, initial, 0, final,
            diagnostic, lifted, lift_digest, original_valid, term,
            action_leaf, sweeps, validation_leaf,
        )


def reconstruct_impulse_result(
    spec: ImpulseSpec | Mapping[str, object], original: OriginalProblem,
    error_rate: float, expected: ImpulseResult, *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> ImpulseResult:
    """Reexecute bounded attempts; reject semantically altered branches or work."""
    if not isinstance(expected, ImpulseResult):
        raise ValueError("impulse replay requires a typed result")
    rebuilt = ImpulseController(spec).run(
        original, error_rate=error_rate, budgets=BudgetTree(limits=budget_limits, parents={}),
        owner_identity=expected.root_owner,
    )
    if rebuilt != expected:
        raise ValueError("impulse replay disagrees with attempt, selection, or leaf work evidence")
    return rebuilt
