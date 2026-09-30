"""Source-qualified binary BPGD with bounded, replayable finite-prior rounds.

This is an Algorithm 1 v2 interpretation. Zero, tie, final-fixation, and
infinite-reliability behavior are explicit local decisions, not source claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .budgets import BudgetLimit, BudgetTree, WorkVector
from .contracts import InterventionSpec
from .intervention_session import BpSession, InterventionProposal, SessionTransition
from .numerics import NumericalFailure
from .schedules import EdgeTable


@dataclass(frozen=True, slots=True)
class GuidedTransition:
    admitted: bool
    termination: str | None
    proposal: InterventionProposal | None
    session_transition: SessionTransition
    eligibility_set: tuple[int, ...]
    tie_indices: tuple[int, ...] = ()
    reliability: float | None = None
    zero_rule_applied: bool = False


@dataclass(frozen=True, slots=True)
class GuidedSweep:
    index: int
    state_before: str
    state_after: str
    admitted: bool
    reservation_leaf: str | None
    validation_leaf: str | None
    original_syndrome_valid: bool | None
    termination: str | None
    candidate: tuple[int, ...] | None


@dataclass(frozen=True, slots=True)
class GuidedRound:
    index: int
    state_before: str
    sweeps: tuple[GuidedSweep, ...]
    eligibility_set: tuple[int, ...]
    selected_target: int | None
    signed_prior: float | None
    reliability: float | None
    tie_indices: tuple[int, ...]
    zero_rule_applied: bool
    proposal_lineage: str | None
    fixation_leaf: str | None
    state_after: str
    terminal_reason: str | None
    source_variant: str
    final_round_rule: str


@dataclass(frozen=True, slots=True)
class GuidedDecimationResult:
    source_variant: str
    original_graph_identity: str
    session_owner: str
    initial_state_digest: str
    final_state_digest: str
    rounds: tuple[GuidedRound, ...]
    candidate: tuple[int, ...] | None
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]
    qualification: str = "algorithm_interpretation"


class GuidedDecimationController:
    """Algorithm 1 v2 interpretation over one compatible flooding session."""

    def __init__(self, spec: InterventionSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, InterventionSpec) else InterventionSpec.model_validate(spec)

    def fix_one(self, session: BpSession, *, posterior: np.ndarray | None, budgets: BudgetTree) -> GuidedTransition:
        state = session.state
        eligible = tuple(index for index in range(session.edge_table.variable_count) if index not in state.fixed_indices)
        if not eligible:
            return GuidedTransition(False, "no_eligible_target", None, SessionTransition(False, state, "no_eligible_target", None), ())
        if posterior is None:
            return GuidedTransition(False, "no_posterior", None, SessionTransition(False, state, "no_posterior", None), eligible)
        try:
            values = np.asarray(posterior, dtype=np.float64)
        except (TypeError, ValueError, OverflowError):
            values = np.empty(0)
        # Infinity is rejected alongside NaN for this finite-prior procedure.
        if values.shape != (session.edge_table.variable_count,) or not np.all(np.isfinite(values)):
            return GuidedTransition(False, "numerical_failure", None, SessionTransition(False, state, "numerical_failure", None), eligible)
        reliability = max(abs(float(values[index])) for index in eligible)
        ties = tuple(index for index in eligible if abs(float(values[index])) == reliability)
        target = ties[0]  # eligible is ascending original-coordinate order.
        zero = float(values[target]) == 0.0
        signed = self.spec.finite_bias_magnitude if values[target] >= 0 else -self.spec.finite_bias_magnitude
        proposal = session.propose_finite_prior(
            target, signed, source_variant=self.spec.variant, target_order=eligible,
        )
        transition = session.commit_intervention(
            proposal, budgets=budgets, leaf_id=f"guided-fix:{state.owner_identity}:{state.revision}:{target}",
        )
        return GuidedTransition(
            transition.admitted, transition.termination, proposal, transition,
            eligible, ties, reliability, zero,
        )

    def run(self, session: BpSession, *, check_matrix: np.ndarray, budgets: BudgetTree) -> GuidedDecimationResult:
        """Run at most T complete BP units per round and return all committed evidence."""
        matrix = np.asarray(check_matrix)
        if (matrix.shape != (session.edge_table.check_count, session.edge_table.variable_count)
                or EdgeTable.from_check_matrix(matrix).graph_sha256 != session.edge_table.graph_sha256):
            raise ValueError("BPGD original check matrix must equal the session graph")
        rounds: list[GuidedRound] = []
        initial_digest = session.state.digest
        candidate: tuple[int, ...] | None = None
        termination = "round_cap_reached"
        for round_index in range(self.spec.round_limit):
            start = session.state.digest
            sweeps: list[GuidedSweep] = []
            round_reason: str | None = None
            for sweep_index in range(self.spec.sweeps_per_round):
                before = session.state.digest
                leaf_id = f"guided-sweep:{session.owner_identity}:{round_index}:{sweep_index}"
                try:
                    transition = session.advance(
                        budgets=budgets, leaf_id=leaf_id, bp_call_start=sweep_index == 0,
                    )
                except (NumericalFailure, ValueError, FloatingPointError):
                    round_reason = "numerical_failure"
                    sweeps.append(GuidedSweep(sweep_index, before, session.state.digest, False, None, None, None, round_reason, None))
                    break
                if not transition.admitted:
                    round_reason = transition.termination or "count_budget_exhausted"
                    sweeps.append(GuidedSweep(sweep_index, before, session.state.digest, False, None, None, None, round_reason, None))
                    break
                check_leaf = f"guided-original-check:{session.owner_identity}:{round_index}:{sweep_index}"
                reservation = budgets.reserve("attempt", WorkVector(original_checks=1), leaf_id=check_leaf)
                if reservation is None:
                    round_reason = "count_budget_exhausted"
                    sweeps.append(GuidedSweep(sweep_index, before, session.state.digest, True, transition.leaf_id, None, None, round_reason, None))
                    break
                try:
                    valid = session.original_syndrome_valid(matrix)
                except BaseException:
                    reservation.rollback()
                    raise
                reservation.commit_once()
                visible = tuple(int(bit) for bit in session.state.candidate)
                sweeps.append(GuidedSweep(
                    sweep_index, before, session.state.digest, True, transition.leaf_id,
                    check_leaf, valid, None, visible,
                ))
                if valid:
                    candidate = visible
                    round_reason = "valid_original_candidate"
                    break
            guided: GuidedTransition | None = None
            if round_reason is None:
                guided = self.fix_one(session, posterior=session.state.posterior, budgets=budgets)
                if not guided.admitted:
                    round_reason = guided.termination or "no_proposal"
                elif round_index == self.spec.round_limit - 1:
                    # Explicitly return after the last fixation; no extra BP block.
                    round_reason = "round_cap_reached"
            rounds.append(GuidedRound(
                round_index, start, tuple(sweeps),
                () if guided is None else guided.eligibility_set,
                None if guided is None or guided.proposal is None else guided.proposal.target_index,
                None if guided is None or guided.proposal is None else guided.proposal.signed_prior,
                None if guided is None else guided.reliability,
                () if guided is None else guided.tie_indices,
                False if guided is None else guided.zero_rule_applied,
                None if guided is None or guided.proposal is None else guided.proposal.child_lineage_id,
                None if guided is None else guided.session_transition.leaf_id,
                session.state.digest, round_reason, self.spec.variant, self.spec.final_round_rule,
            ))
            if round_reason is not None:
                termination = round_reason
                break
        leaves = budgets.leaf_events()
        return GuidedDecimationResult(
            self.spec.variant, session.edge_table.graph_sha256, session.owner_identity,
            initial_digest, session.state.digest, tuple(rounds), candidate,
            termination, budgets.summary("attempt"), leaves,
        )


def reconstruct_guided_result(
    spec: InterventionSpec | Mapping[str, object], check_matrix: np.ndarray,
    syndrome: np.ndarray, error_rate: float, expected: GuidedDecimationResult,
    *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> GuidedDecimationResult:
    """Regenerate decisions and work from decoder-visible inputs and budget caps."""
    if not isinstance(expected, GuidedDecimationResult):
        raise ValueError("guided replay requires a typed result")
    session = BpSession(
        EdgeTable.from_check_matrix(check_matrix), syndrome, error_rate=error_rate,
        owner_identity=expected.session_owner,
    )
    rebuilt = GuidedDecimationController(spec).run(
        session, check_matrix=check_matrix,
        budgets=BudgetTree(limits=budget_limits, parents={}),
    )
    if rebuilt != expected:
        raise ValueError("guided replay disagrees with deterministic transitions or work")
    return rebuilt
