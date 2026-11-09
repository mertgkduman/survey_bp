"""Pinned Huang--Ueng conventional syndrome-based residual BP scheduling.

This module deliberately exposes one source-qualified procedure only.  Its
cache is a lifecycle object: values are initialized or dependency-refreshed
with min-sum predictions, the selected entry is reset to zero, and entries
outside the changed V2C dependency cone are preserved verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .budgets import BudgetTermination, BudgetTree, WorkVector
from .execution import CanonicalLocalStepExecutor, LocalStepProposal, ScheduleProgress
from .kernel import BinarySpaKernel
from .schedules import EdgeTable
from .updates import MinSumUpdate


@dataclass(frozen=True, slots=True)
class ResidualWork:
    """Source-visible setup or decode work without inventing a score variant."""

    residual_precomputations: int = 0
    residual_differences: int = 0
    priority_comparisons: int = 0
    check_to_variable_commits: int = 0
    variable_to_check_updates: int = 0
    belief_assemblies: int = 0
    candidate_checks: int = 0

    def as_work_vector(self) -> WorkVector:
        """Map source-visible setup and decode operations to the full Phase-3 vector."""
        return WorkVector(
            check_to_variable_updates=self.check_to_variable_commits,
            variable_to_check_updates=self.variable_to_check_updates,
            belief_assemblies=self.belief_assemblies,
            candidate_constructions=1 if self.candidate_checks else 0,
            convergence_checks=self.candidate_checks,
            residual_precomputations=self.residual_precomputations,
            residual_differences=self.residual_differences,
            priority_maintenance=self.priority_comparisons,
            residual_priority_evaluations=(
                self.residual_precomputations
                + self.residual_differences
                + self.priority_comparisons
            ),
            candidate_checks=self.candidate_checks,
        )


@dataclass(frozen=True, slots=True)
class ResidualCache:
    """Immutable full-pool cache and separately reported initialization work."""

    values: np.ndarray
    setup_work: ResidualWork

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.float64)
        if values.ndim != 1 or not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise ValueError("residual cache values must be finite nonnegative one-dimensional values")
        copied = np.array(values, dtype=np.float64, copy=True)
        copied.setflags(write=False)
        object.__setattr__(self, "values", copied)


class ResidualSetupBudgetDenied(RuntimeError):
    """Initial full-pool source work could not be admitted without mutation."""

    def __init__(self, termination: BudgetTermination | None) -> None:
        super().__init__("sRBP setup work was denied before residual calculation")
        self.termination = termination


@dataclass(frozen=True, slots=True)
class ResidualSelection:
    """One full-pool maximum selection with the sole disclosed tie adaptation."""

    index: int
    edge: tuple[int, int]
    residual: float
    comparisons: int
    tie_rule: str = "canonical_edge_order"


@dataclass(frozen=True, slots=True)
class ResidualProposal:
    """A pure local computation paired with exact source-accounting facts."""

    selection: ResidualSelection
    invalidated_indices: tuple[int, ...]
    decode_work: ResidualWork
    local_step: LocalStepProposal
    computed_state: list[_ComputedStep]


@dataclass(frozen=True, slots=True)
class ResidualStepResult:
    """Committed local state, cache replacement, and schedule-qualified progress."""

    admitted: bool
    selection: ResidualSelection | None
    cache: ResidualCache
    c2v: np.ndarray
    candidate: np.ndarray | None
    progress: ScheduleProgress
    converged: bool
    termination: object | None = None


@dataclass(frozen=True, slots=True)
class _ComputedStep:
    v2c: np.ndarray
    c2v: np.ndarray
    cache: ResidualCache
    candidate: np.ndarray


class SyndromeResidualSchedule:
    """The one admitted Phase-3 Huang--Ueng conventional sRBP schedule.

    Min-sum is used solely to predict priorities.  The selected C2V message
    is always committed through ``BinarySpaKernel.check_message``.  The
    schedule contains no score, heap, or tie-rule option by design.
    """

    policy_name = "huang_ueng_conventional_srbp"
    tie_rule = "canonical_edge_order"
    stopping_adaptation = "D-09 after residual-selected local unit"
    source_iteration = "E residual-selected C2V commits"

    def __init__(self, edge_table: EdgeTable, *, kernel: BinarySpaKernel) -> None:
        if not isinstance(edge_table, EdgeTable) or not isinstance(kernel, BinarySpaKernel):
            raise ValueError("sRBP requires an EdgeTable and BinarySpaKernel")
        if kernel.update_rule is not None:
            raise ValueError("conventional sRBP commits SPA messages; a non-SPA kernel is not admitted")
        if getattr(kernel.profile, "v2c_damping", 0.0) != 0.0:
            raise ValueError("conventional sRBP requires an undamped numerical profile")
        if edge_table.edge_count == 0:
            raise ValueError("conventional sRBP requires a nonempty full C2V edge pool")
        self.edge_table = edge_table
        self.kernel = kernel
        self._min_sum = MinSumUpdate(profile=kernel.profile)
        self._check_edges = tuple(
            tuple(index for index, (check, _variable) in enumerate(edge_table.edges) if check == current)
            for current in range(edge_table.check_count)
        )
        self._variable_edges = tuple(
            tuple(index for index, (_check, variable) in enumerate(edge_table.edges) if variable == current)
            for current in range(edge_table.variable_count)
        )
        self._edge_variables = tuple(variable for _check, variable in edge_table.edges)
        self._setup_ordinal = 0

    def _validate_state(self, v2c: np.ndarray, c2v: np.ndarray, syndrome: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        expected_edges = (self.edge_table.edge_count,)
        validated: list[np.ndarray] = []
        for value, name in ((v2c, "v2c"), (c2v, "c2v")):
            array = np.asarray(value, dtype=np.float64)
            if array.shape != expected_edges or not np.all(np.isfinite(array)):
                raise ValueError(f"{name} must be a finite vector over the complete canonical EdgeTable")
            validated.append(np.array(array, dtype=np.float64, copy=True))
        bits = np.asarray(syndrome)
        if (
            bits.shape != (self.edge_table.check_count,)
            or not np.issubdtype(bits.dtype, np.integer)
            or np.any((bits != 0) & (bits != 1))
        ):
            raise ValueError("syndrome must be a binary vector matching the check count")
        return validated[0], validated[1], np.asarray(bits, dtype=np.uint8)

    def _prediction(self, v2c: np.ndarray, syndrome: np.ndarray, edge_index: int) -> float:
        check, _variable = self.edge_table.edges[edge_index]
        incoming = v2c[[other for other in self._check_edges[check] if other != edge_index]]
        return self._min_sum.check_to_variable(incoming, syndrome=int(syndrome[check]))

    def initialize(
        self,
        v2c: np.ndarray,
        c2v: np.ndarray,
        syndrome: np.ndarray,
        *,
        error_rate: float,
        budgets: BudgetTree | None = None,
        scope: str = "attempt",
    ) -> ResidualCache:
        """Fill the full source cache before decoding; no selection occurs here."""
        del error_rate  # The supplied V2C state already encodes the declared channel prior.
        next_v2c, current_c2v, bits = self._validate_state(v2c, c2v, syndrome)
        edge_count = self.edge_table.edge_count
        setup_work = ResidualWork(residual_precomputations=edge_count, residual_differences=edge_count)
        reservation = None
        if budgets is not None:
            leaf_id = f"{scope}:srbp:setup:{self._setup_ordinal}"
            reservation = budgets.reserve(scope, setup_work.as_work_vector(), leaf_id=leaf_id)
            if reservation is None:
                raise ResidualSetupBudgetDenied(budgets.last_termination)
        try:
            values = np.asarray(
                [abs(self._prediction(next_v2c, bits, index) - current_c2v[index]) for index in range(edge_count)],
                dtype=np.float64,
            )
            cache = ResidualCache(values, setup_work)
        except BaseException:
            if reservation is not None and reservation.active:
                reservation.rollback()
            raise
        if reservation is not None:
            reservation.commit_once()
            self._setup_ordinal += 1
        return cache

    def _select(self, cache: ResidualCache) -> ResidualSelection:
        if cache.values.shape != (self.edge_table.edge_count,):
            raise ValueError("residual cache does not cover the complete canonical EdgeTable")
        selected = 0
        maximum = float(cache.values[0])
        for index in range(1, self.edge_table.edge_count):
            value = float(cache.values[index])
            # Strict comparison deliberately retains the first canonical edge on ties.
            if value > maximum:
                selected, maximum = index, value
        return ResidualSelection(
            index=selected,
            edge=self.edge_table.edges[selected],
            residual=maximum,
            comparisons=self.edge_table.edge_count - 1,
        )

    def _invalidation_indices(self, selection: ResidualSelection) -> tuple[int, ...]:
        selected_check, selected_variable = selection.edge
        invalidated: set[int] = set()
        for v2c_index in self._variable_edges[selected_variable]:
            check, _variable = self.edge_table.edges[v2c_index]
            if check == selected_check:
                continue
            invalidated.update(
                c2v_index
                for c2v_index in self._check_edges[check]
                if self.edge_table.edges[c2v_index][1] != selected_variable
            )
        return tuple(sorted(invalidated))

    def propose_local_step(
        self, v2c: np.ndarray, c2v: np.ndarray, cache: ResidualCache, syndrome: np.ndarray, *, error_rate: float,
        prior_llrs: np.ndarray | None = None,
    ) -> ResidualProposal:
        """Create the complete reserve-before-mutation local proposal."""
        state_v2c, state_c2v, bits = self._validate_state(v2c, c2v, syndrome)
        from .intervention_session import _frozen_f64
        prior = (self.kernel.prior(error_rate) if prior_llrs is None else
                 _frozen_f64(prior_llrs, self.edge_table.variable_count, "prior_llrs"))
        selection = self._select(cache)
        invalidated = self._invalidation_indices(selection)
        selected_check, selected_variable = selection.edge
        v2c_updates = len(self._variable_edges[selected_variable]) - 1
        decode_work = ResidualWork(
            residual_precomputations=len(invalidated),
            residual_differences=len(invalidated),
            priority_comparisons=selection.comparisons,
            check_to_variable_commits=1,
            variable_to_check_updates=v2c_updates,
            belief_assemblies=self.edge_table.variable_count,
            candidate_checks=1,
        )
        computed: list[_ComputedStep] = []

        def compute() -> np.ndarray:
            next_v2c = np.array(state_v2c, dtype=np.float64, copy=True)
            next_c2v = np.array(state_c2v, dtype=np.float64, copy=True)
            incoming = next_v2c[[other for other in self._check_edges[selected_check] if other != selection.index]]
            # This is the source-mandated SPA commit, intentionally not the MS prediction.
            next_c2v[selection.index] = self.kernel.check_message(incoming, int(bits[selected_check]))
            beliefs = self.kernel.assemble_beliefs(
                self.edge_table.variable_count, self._edge_variables, next_c2v, prior,
            )
            candidate = self.kernel.candidate_from_beliefs(beliefs)
            for index in self._variable_edges[selected_variable]:
                if index != selection.index:
                    next_v2c[index] = self.kernel.variable_message(float(beliefs[selected_variable]), float(next_c2v[index]))
            next_values = np.array(cache.values, dtype=np.float64, copy=True)
            # Reset is a source-lifecycle action, not a stateless reevaluation.
            next_values[selection.index] = 0.0
            for index in invalidated:
                next_values[index] = abs(self._prediction(next_v2c, bits, index) - next_c2v[index])
            computed.append(
                _ComputedStep(next_v2c, next_c2v, ResidualCache(next_values, cache.setup_work), np.array(candidate, dtype=np.uint8, copy=True))
            )
            return next_v2c

        return ResidualProposal(
            selection=selection,
            invalidated_indices=invalidated,
            decode_work=decode_work,
            local_step=LocalStepProposal(
                label=f"srbp:{selection.index}", proposed_work=decode_work.as_work_vector(), compute=compute,
            ),
            computed_state=computed,
        )

    def execute_local_step(
        self,
        executor: CanonicalLocalStepExecutor,
        proposal: ResidualProposal,
        *,
        v2c: np.ndarray,
        c2v: np.ndarray,
        cache: ResidualCache,
        progress: ScheduleProgress,
        is_converged: Callable[[np.ndarray], bool],
    ) -> ResidualStepResult:
        """Commit exactly one selected edge, its dependent V2C updates, and one check."""
        result = executor.execute(
            proposal.local_step,
            messages=v2c,
            progress=progress,
            policy_state={},
            cache={},
            is_converged=lambda _messages: bool(is_converged(proposal.computed_state[-1].candidate)),
        )
        if not result.admitted:
            return ResidualStepResult(False, None, cache, np.array(c2v, dtype=np.float64, copy=True), None, progress, False, result.termination)
        completed = progress.local_steps + 1
        next_progress = ScheduleProgress(
            iteration=completed // self.edge_table.edge_count,
            local_steps=completed,
            cursor=(completed % self.edge_table.edge_count,),
            rng_state=progress.rng_state,
        )
        if len(proposal.computed_state) != 1:
            raise RuntimeError("residual proposal must compute exactly one immutable local state")
        state = proposal.computed_state[-1]
        return ResidualStepResult(True, proposal.selection, state.cache, state.c2v, state.candidate, next_progress, result.converged)
