"""Canonical four-state Q-BPGD interpretation over one persistent QBP session.

The source specifies Algorithm 3's fixation ratios and depolarizing setup.  It
does not settle the message-buffer lifecycle, normalization interface, or tie
rules.  Those three choices remain explicit canonical interpretations and keep
the whole run labelled ``canonical_adaptation``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import numbers
from typing import Mapping

import numpy as np

from ..canonical.budgets import BudgetLimit, BudgetTree, WorkVector
from .kernel import QbpSession, QbpSweep, ScalarLlrBp4Kernel
from .problems import QuaternaryOriginalProblem


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _tuple4(value: np.ndarray) -> tuple[float, float, float, float]:
    return tuple(float(item) for item in value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class QbpgdSpec:
    """Complete public meaning of the admitted Algorithm 3 interpretation."""

    iterations_per_round: int
    epsilon: float
    round_limit: int | None = None
    algorithm_component_id: str = "yao-2023-qbpgd-algorithm-3-v2"
    fixation_component_id: str = "yao-2023-qbpgd-literal-fixation-v2"
    depolarizing_component_id: str = "yao-2023-qbpgd-depolarizing-setup-v2"
    source_author_code_identity: str = "unverified"
    continued_messages_interpretation_id: str = "D-14"
    normalization_interpretation_id: str = "D-15"
    tie_interpretation_id: str = "D-16"

    def __post_init__(self) -> None:
        if isinstance(self.iterations_per_round, bool) or not isinstance(self.iterations_per_round, numbers.Integral) or self.iterations_per_round < 1:
            raise ValueError("Q-BPGD iterations_per_round must be a positive integer")
        if not isinstance(self.epsilon, numbers.Real) or not np.isfinite(self.epsilon) or not 0.0 < float(self.epsilon) < 1.0:
            raise ValueError("Q-BPGD epsilon must be finite and strictly between zero and one")
        if self.round_limit is not None and (isinstance(self.round_limit, bool) or not isinstance(self.round_limit, numbers.Integral) or self.round_limit < 1):
            raise ValueError("Q-BPGD round_limit must be a positive integer when supplied")
        if self.source_author_code_identity != "unverified":
            raise ValueError("Q-BPGD author implementation identity remains unverified")
        if (self.continued_messages_interpretation_id, self.normalization_interpretation_id, self.tie_interpretation_id) != ("D-14", "D-15", "D-16"):
            raise ValueError("Q-BPGD requires the locked D-14 through D-16 interpretation identities")


@dataclass(frozen=True, slots=True)
class QbpgdRound:
    index: int
    sweeps: tuple[QbpSweep, ...]
    eligibility_set: tuple[int, ...]
    selected_target: int | None
    selected_pauli: int | None
    reliability: float | None
    target_ties: tuple[int, ...]
    pauli_ties: tuple[int, ...]
    raw_prior: tuple[float, float, float, float] | None
    resolved_prior: tuple[float, float, float, float] | None
    message_digest_before: str
    message_digest_after: str
    original_syndrome_valid: bool | None
    original_check_leaf: str | None
    selection_leaf: str | None
    fixation_leaf: str | None
    terminal_reason: str | None


@dataclass(frozen=True, slots=True)
class QbpgdResult:
    spec_identity: str
    run_fidelity: str
    component_fidelity: Mapping[str, str]
    component_ids: Mapping[str, str]
    interpretation_ids: Mapping[str, str]
    source_author_code_identity: str
    initial_message_digest: str
    final_message_digest: str
    rounds: tuple[QbpgdRound, ...]
    candidate: tuple[int, ...]
    termination: str
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]


def select_qbpgd_target(
    marginals: object, *, eligibility: tuple[int, ...],
) -> tuple[int, int, float, tuple[int, ...], tuple[int, ...]]:
    """Select the highest I/X/Y/Z posterior with locked deterministic ties."""
    values = np.asarray(marginals, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 4 or not np.all(np.isfinite(values)):
        raise ValueError("Q-BPGD requires finite four-state marginals")
    if not eligibility or any(isinstance(item, bool) or not isinstance(item, int) or not 0 <= item < values.shape[0] for item in eligibility):
        raise ValueError("Q-BPGD eligibility must be nonempty valid original qubit indices")
    reliabilities = {index: float(np.max(values[index])) for index in eligibility}
    highest = max(reliabilities.values())
    targets = tuple(index for index in eligibility if reliabilities[index] == highest)
    target = targets[0]
    paulis = tuple(index for index, value in enumerate(values[target]) if float(value) == highest)
    return target, paulis[0], highest, targets, paulis


class QbpgdController:
    """Algorithm 3 with persistent session-owned QBP buffers and explicit evidence."""

    def __init__(self, spec: QbpgdSpec) -> None:
        if not isinstance(spec, QbpgdSpec):
            raise ValueError("Q-BPGD controller requires QbpgdSpec")
        self.spec = spec

    def _reserve(self, session: QbpSession, delta: WorkVector, leaf: str):
        return session.budgets.reserve(session.budget_scope, delta, leaf_id=leaf)

    def run(self, session: QbpSession) -> QbpgdResult:
        if not isinstance(session, QbpSession):
            raise ValueError("Q-BPGD requires one persistent QBP session")
        limit = min(session.problem.code.n, self.spec.round_limit or session.problem.code.n)
        eligible = tuple(range(session.problem.code.n))
        rounds: list[QbpgdRound] = []
        termination = "round_cap"
        initial_digest = session.state_digest
        for round_index in range(limit):
            before = session.state_digest
            eligible_before = eligible
            sweeps: list[QbpSweep] = []
            reason: str | None = None
            for _ in range(self.spec.iterations_per_round):
                try:
                    sweep = session.sweep(stop_on_convergence=False)
                except Exception:
                    reason = "numerical_failure"
                    break
                sweeps.append(sweep)
                if sweep.terminal == "capped":
                    reason = "work_cap"
                    break
            original_leaf: str | None = None
            selection_leaf: str | None = None
            fixation_leaf: str | None = None
            target: int | None = None
            pauli: int | None = None
            reliability: float | None = None
            target_ties: tuple[int, ...] = ()
            pauli_ties: tuple[int, ...] = ()
            raw: tuple[float, float, float, float] | None = None
            resolved: tuple[float, float, float, float] | None = None
            valid: bool | None = None
            if reason is None:
                original_leaf = f"qbpgd:original-check:{session.problem.lineage_id}:{round_index}"
                reservation = self._reserve(session, WorkVector(original_checks=1), original_leaf)
                if reservation is None:
                    reason = "work_cap"
                else:
                    valid = bool(np.array_equal(session.problem.code.syndrome(session.last.candidate), session.problem.syndrome))
                    reservation.commit_once()
                    if valid:
                        reason = "early_success"
            if reason is None and not eligible:
                reason = "no_eligible_target"
            if reason is None:
                selection_leaf = f"qbpgd:select:{session.problem.lineage_id}:{round_index}"
                reservation = self._reserve(session, WorkVector(order_generation=1, order_selection=1, ranking_scans=len(eligible)), selection_leaf)
                if reservation is None:
                    reason = "work_cap"
                else:
                    try:
                        target, pauli, reliability, target_ties, pauli_ties = select_qbpgd_target(session.last.marginals, eligibility=eligible)
                    except Exception:
                        reservation.rollback()
                        raise
                    reservation.commit_once()
                    literal = np.full(4, float(self.spec.epsilon), dtype=np.float64)
                    literal[int(pauli)] = 1.0 - float(self.spec.epsilon)
                    normalized = literal / float(literal.sum())
                    raw, resolved = _tuple4(literal), _tuple4(normalized)
                    fixation_leaf = f"qbpgd:fix:{session.problem.lineage_id}:{round_index}:{target}"
                    fixation = self._reserve(session, WorkVector(intervention_actions=1, fixation_actions=1), fixation_leaf)
                    if fixation is None:
                        reason = "work_cap"
                    else:
                        session.replace_prior(target, normalized)
                        fixation.commit_once()
                        eligible = tuple(item for item in eligible if item != target)
                        if round_index == limit - 1:
                            reason = "round_cap"
            after = session.state_digest
            rounds.append(QbpgdRound(
                round_index, tuple(sweeps), eligible_before,
                target, pauli, reliability, target_ties, pauli_ties, raw, resolved,
                before, after, valid, original_leaf, selection_leaf, fixation_leaf, reason,
            ))
            if reason is not None:
                termination = reason
                break
        component_ids = {
            "algorithm": self.spec.algorithm_component_id, "fixation": self.spec.fixation_component_id,
            "depolarizing_setup": self.spec.depolarizing_component_id,
        }
        result = QbpgdResult(
            spec_identity=_digest(asdict(self.spec)), run_fidelity="canonical_adaptation",
            component_fidelity={name: "source_backed" for name in component_ids}, component_ids=component_ids,
            interpretation_ids={"continued_messages": self.spec.continued_messages_interpretation_id, "normalization": self.spec.normalization_interpretation_id, "ties": self.spec.tie_interpretation_id},
            source_author_code_identity=self.spec.source_author_code_identity,
            initial_message_digest=initial_digest, final_message_digest=session.state_digest,
            rounds=tuple(rounds), candidate=tuple(int(item) for item in session.last.candidate), termination=termination,
            work=session.budgets.summary(session.budget_scope), leaves=session.budgets.leaf_events(),
        )
        return result


def _result_evidence(result: QbpgdResult) -> dict[str, object]:
    """Convert immutable arrays and work records to deterministic replay bytes."""
    return {
        "spec_identity": result.spec_identity, "run_fidelity": result.run_fidelity,
        "component_fidelity": dict(result.component_fidelity), "component_ids": dict(result.component_ids),
        "interpretation_ids": dict(result.interpretation_ids),
        "source_author_code_identity": result.source_author_code_identity,
        "initial_message_digest": result.initial_message_digest, "final_message_digest": result.final_message_digest,
        "candidate": list(result.candidate), "termination": result.termination,
        "work": result.work.as_evidence(structural_event_version=4),
        "leaves": [(leaf, scope, work.as_evidence(structural_event_version=4)) for leaf, scope, work in result.leaves],
        "rounds": [
            {
                "index": round_.index,
                "sweeps": [
                    {"iteration": sweep.iteration, "c2v": sweep.c2v.tolist(), "v2c": sweep.v2c.tolist(),
                     "beliefs": sweep.beliefs.tolist(), "marginals": sweep.marginals.tolist(),
                     "candidate": sweep.candidate.tolist(), "converged": sweep.converged,
                     "terminal": sweep.terminal, "work": sweep.work.as_evidence(structural_event_version=4)}
                    for sweep in round_.sweeps
                ],
                "eligibility_set": list(round_.eligibility_set), "selected_target": round_.selected_target,
                "selected_pauli": round_.selected_pauli, "reliability": round_.reliability,
                "target_ties": list(round_.target_ties), "pauli_ties": list(round_.pauli_ties),
                "raw_prior": None if round_.raw_prior is None else list(round_.raw_prior),
                "resolved_prior": None if round_.resolved_prior is None else list(round_.resolved_prior),
                "message_digest_before": round_.message_digest_before, "message_digest_after": round_.message_digest_after,
                "original_syndrome_valid": round_.original_syndrome_valid, "original_check_leaf": round_.original_check_leaf,
                "selection_leaf": round_.selection_leaf, "fixation_leaf": round_.fixation_leaf,
                "terminal_reason": round_.terminal_reason,
            }
            for round_ in result.rounds
        ],
    }


def reconstruct_qbpgd(
    spec: QbpgdSpec, problem: QuaternaryOriginalProblem, priors: object, expected: QbpgdResult,
    *, budget_limits: tuple[BudgetLimit, ...] = (),
) -> QbpgdResult:
    """Independently regenerate every decoder-visible transition and work leaf."""
    if not isinstance(expected, QbpgdResult):
        raise ValueError("Q-BPGD replay requires QbpgdResult")
    rebuilt = QbpgdController(spec).run(
        ScalarLlrBp4Kernel().new_session(problem, priors, budgets=BudgetTree(limits=budget_limits, parents={}))
    )
    if _result_evidence(rebuilt) != _result_evidence(expected):
        raise ValueError("Q-BPGD replay disagrees with transitions, fidelity, or work")
    return rebuilt


__all__ = [
    "QbpgdController", "QbpgdResult", "QbpgdRound", "QbpgdSpec", "ScalarLlrBp4Kernel",
    "reconstruct_qbpgd", "select_qbpgd_target",
]
