"""Source-defined fixed-alpha MBP4 with explicit recurrence and replay state.

Kuo and Lai's MBP4 changes the variable recurrence itself.  It is not a
binary memory adapter: Eq. (17) divides the whole anticommuting C2V sum by
``alpha`` and Eq. (18) subtracts the destination C2V message without that
scaling.  The deliberate distinction from normalized BP4 lives here so it is
observable in code, test fixtures, manifests, and replay evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import numbers

import numpy as np
from bp_registry.compiled_contracts import immutable_snapshot

from ..canonical.budgets import BudgetTree, WorkVector
from .algebra import Pauli, anticommutes
from .kernel import QbpSweep, ScalarLlrBp4Kernel, _priors, _session_problem
from .numerics import QBP4_F64_V1, QuaternaryNumericalFailure, QuaternaryNumericalProfile, llrs_to_probabilities
from .problems import QuaternaryOriginalProblem


_SCHEDULES = frozenset({"qbp_flooding", "qbp_variable_serial"})
_EQUATION_ID = "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18"
_SOURCE_REVISION = "kuo-lai-2023-arxiv-2104.13659v2"


def _readonly(value: object, *, dtype: np.dtype | type) -> np.ndarray:
    result = immutable_snapshot(value, dtype=dtype)
    return result


@dataclass(frozen=True, slots=True)
class Mbp4Spec:
    """One fixed-alpha MBP4 procedure declaration, never an adaptive search."""

    alpha: float
    schedule: str
    max_iterations: int = 20
    algorithm: str = "fixed_alpha_mbp4"
    source_revision: str = _SOURCE_REVISION
    equation_identity: str = _EQUATION_ID

    def __post_init__(self) -> None:
        if isinstance(self.alpha, (tuple, list, np.ndarray)):
            raise ValueError("fixed alpha MBP4 does not admit an alpha search list")
        if isinstance(self.alpha, bool) or not isinstance(self.alpha, (numbers.Real, np.integer, np.floating)):
            raise ValueError("MBP4 alpha must be finite and positive")
        alpha = float(self.alpha)
        if not math.isfinite(alpha) or alpha <= 0.0:
            raise ValueError("MBP4 alpha must be finite and positive")
        if self.schedule not in _SCHEDULES:
            raise ValueError("MBP4 schedule must be source-qualified qbp_flooding or qbp_variable_serial")
        if self.algorithm in {"ambp4", "adaptive_mbp4"}:
            raise ValueError("AMBP4 is a separate adaptive algorithm and is not admitted by fixed-alpha MBP4")
        if self.algorithm != "fixed_alpha_mbp4":
            raise ValueError("MBP4 algorithm must declare fixed_alpha_mbp4")
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, numbers.Integral) or self.max_iterations < 0:
            raise ValueError("MBP4 max_iterations must be a nonnegative integer")
        if self.source_revision != _SOURCE_REVISION or self.equation_identity != _EQUATION_ID:
            raise ValueError("MBP4 source revision and equation identity are closed")
        object.__setattr__(self, "alpha", alpha)
        object.__setattr__(self, "max_iterations", int(self.max_iterations))

    def as_evidence(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "alpha": self.alpha,
            "schedule": self.schedule,
            "max_iterations": self.max_iterations,
            "source_revision": self.source_revision,
            "equation_identity": self.equation_identity,
            "posterior": "prior_plus_sum_anticommuting_delta_divided_by_alpha",
            "edge_inhibition": "subtract_unscaled_destination_delta",
        }


@dataclass(frozen=True, slots=True)
class Mbp4Result:
    """Replayable terminal evidence for a complete fixed-alpha MBP4 session."""

    spec: Mbp4Spec
    sweeps: tuple[QbpSweep, ...]
    candidate: np.ndarray
    termination: str
    work: WorkVector
    initial_state_digest: str
    state_digest: str
    schedule_freshness: str
    equation_identity: str = _EQUATION_ID

    def __post_init__(self) -> None:
        if not isinstance(self.spec, Mbp4Spec) or not isinstance(self.work, WorkVector):
            raise ValueError("MBP4 result must retain typed spec and work")
        if self.termination not in {"converged", "max_iterations", "work_cap"}:
            raise ValueError("MBP4 terminal is invalid")
        candidate = _readonly(self.candidate, dtype=np.uint8)
        if candidate.ndim != 1 or np.any((candidate < Pauli.I) | (candidate > Pauli.Z)):
            raise ValueError("MBP4 candidate is invalid")
        if not self.initial_state_digest or not self.state_digest or not self.schedule_freshness:
            raise ValueError("MBP4 replay evidence is incomplete")
        object.__setattr__(self, "candidate", candidate)

    def as_evidence(self) -> dict[str, object]:
        return {
            "spec": self.spec.as_evidence(),
            "termination": self.termination,
            "candidate": self.candidate.tolist(),
            "work": self.work.as_evidence(structural_event_version=4),
            "initial_state_digest": self.initial_state_digest,
            "state_digest": self.state_digest,
            "schedule_freshness": self.schedule_freshness,
            "equation_identity": self.equation_identity,
            "sweep_digests": [
                sha256(json.dumps({
                    "iteration": sweep.iteration,
                    "c2v": sweep.c2v.tolist(), "v2c": sweep.v2c.tolist(),
                    "beliefs": sweep.beliefs.tolist(), "candidate": sweep.candidate.tolist(),
                    "terminal": sweep.terminal,
                }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                for sweep in self.sweeps
            ],
        }


class FixedAlphaMbp4Kernel:
    """The source-defined variable recurrence for a single declared alpha."""

    def __init__(self, spec: Mbp4Spec, *, profile: QuaternaryNumericalProfile = QBP4_F64_V1) -> None:
        if not isinstance(spec, Mbp4Spec):
            raise ValueError("fixed-alpha MBP4 requires Mbp4Spec")
        self.spec = spec
        self.scalar = ScalarLlrBp4Kernel(profile=profile)
        self.profile = profile

    def prior_llrs(self, probabilities: object) -> np.ndarray:
        return self.scalar.prior_llrs(probabilities)

    def check_message(self, incoming: object, syndrome: int) -> float:
        return self.scalar.check_message(incoming, syndrome)

    def candidate_from_beliefs(self, beliefs: object) -> np.ndarray:
        return self.scalar.candidate_from_beliefs(beliefs)

    def posterior(self, prior: object, c2v: object, labels: object) -> np.ndarray:
        """Apply MBP4 Eq. (17): scale the full anticommuting sum by ``1/alpha``."""
        belief = self.prior_llrs(prior)
        messages = np.asarray(c2v, dtype=np.float64)
        edge_labels = np.asarray(labels)
        if messages.ndim != 1 or edge_labels.shape != messages.shape:
            raise ValueError("MBP4 posterior messages and labels must be matching one-dimensional arrays")
        for state in (Pauli.X, Pauli.Y, Pauli.Z):
            total = sum(float(message) for message, label in zip(messages, edge_labels, strict=True) if anticommutes(int(label), int(state)))
            belief[int(state) - 1] += total / self.spec.alpha
        return np.clip(belief, -self.profile.saturation, self.profile.saturation)

    def variable_message(self, posterior: object, check_value: float, edge_label: int) -> np.ndarray:
        """Apply MBP4 Eq. (18): inhibit the destination edge by unscaled Delta."""
        return self.scalar.variable_message(posterior, check_value, edge_label)

    def normalized_variable_message(self, posterior: object, check_value: float, edge_label: int) -> np.ndarray:
        """Reference-only normalized-BP4 comparator; never used by MBP4 sessions."""
        return self.scalar.variable_message(posterior, float(check_value) / self.spec.alpha, edge_label)

    def new_session(
        self, problem: QuaternaryOriginalProblem, priors: object, *, budgets: BudgetTree | None = None, budget_scope: str = "attempt",
    ) -> "Mbp4Session":
        return Mbp4Session(self, problem, priors, budgets=budgets, budget_scope=budget_scope)


class Mbp4Session:
    """Attempt-owned MBP4 buffers with source-qualified flooding or serial freshness."""

    def __init__(
        self, kernel: FixedAlphaMbp4Kernel, problem: QuaternaryOriginalProblem, priors: object, *, budgets: BudgetTree | None = None,
        budget_scope: str = "attempt",
    ) -> None:
        if not isinstance(kernel, FixedAlphaMbp4Kernel) or not _session_problem(problem):
            raise ValueError("MBP4 requires its quaternary kernel and immutable check/syndrome problem")
        if not budget_scope:
            raise ValueError("MBP4 budget scope must be nonempty")
        self.kernel, self.problem = kernel, problem
        self.priors = _priors(priors, n=problem.code.n)
        self.budgets = BudgetTree(limits=(), parents={}) if budgets is None else budgets
        if not isinstance(self.budgets, BudgetTree):
            raise ValueError("MBP4 budgets must be a BudgetTree")
        self.budget_scope = budget_scope
        rows, columns = np.nonzero(problem.code.checks != Pauli.I)
        self._checks = np.asarray(rows, dtype=np.int64)
        self._variables = np.asarray(columns, dtype=np.int64)
        self._labels = np.asarray(problem.code.checks[rows, columns], dtype=np.uint8)
        self._check_incident = tuple(tuple(int(edge) for edge in np.flatnonzero(self._checks == check))
                                     for check in range(problem.code.checks.shape[0]))
        self._variable_incident = tuple(tuple(int(edge) for edge in np.flatnonzero(self._variables == variable))
                                        for variable in range(problem.code.n))
        self._prior_llrs = np.asarray([kernel.prior_llrs(row) for row in self.priors], dtype=np.float64)
        self._c2v = np.zeros(self._labels.size, dtype=np.float64)
        self._v2c = self._prior_llrs[self._variables].copy()
        self._beliefs = self._prior_llrs.copy()
        self._marginals = np.asarray([llrs_to_probabilities(row, profile=kernel.profile) for row in self._beliefs])
        self._candidate = kernel.candidate_from_beliefs(self._beliefs)
        self._iteration, self._terminal = 0, "running"
        self._sweeps: list[QbpSweep] = []
        self._last = self._snapshot(converged=self._is_converged(), terminal="running", work=WorkVector.zero())
        self._initial_state_digest = self.state_digest

    @property
    def state_digest(self) -> str:
        payload = {
            "spec": self.kernel.spec.as_evidence(), "priors": self.priors.tolist(), "c2v": self._c2v.tolist(),
            "v2c": self._v2c.tolist(), "beliefs": self._beliefs.tolist(), "candidate": self._candidate.tolist(),
            "iteration": self._iteration,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _is_converged(self) -> bool:
        return bool(np.array_equal(self.problem.code.syndrome(self._candidate), self.problem.syndrome))

    def _sweep_work(self) -> WorkVector:
        return WorkVector.from_flooding_counts(edge_count=int(self._labels.size), variable_count=self.problem.code.n) + WorkVector(bp_calls=1)

    def _snapshot(self, *, converged: bool, terminal: str, work: WorkVector) -> QbpSweep:
        return QbpSweep(
            iteration=self._iteration, c2v=self._c2v, v2c=self._v2c, beliefs=self._beliefs, marginals=self._marginals,
            candidate=self._candidate, converged=converged, terminal=terminal, work=work,
        )

    def _edge_delta(self, edge: int, v2c: np.ndarray) -> float:
        check = int(self._checks[edge])
        reduced = [
            self.scalar_commutation(v2c[index], int(self._labels[index]))
            for index in self._check_incident[check] if index != edge
        ]
        return self.kernel.check_message(reduced, int(self.problem.syndrome[check]))

    def scalar_commutation(self, v2c: np.ndarray, label: int) -> float:
        from .numerics import commutation_llr
        return commutation_llr(v2c, label, profile=self.kernel.profile)

    def sweep(self) -> QbpSweep:
        if self._terminal != "running":
            return self._last
        next_iteration = self._iteration + 1
        reservation = self.budgets.reserve(
            self.budget_scope, self._sweep_work(), leaf_id=f"mbp4:{self.problem.lineage_id}:{next_iteration}"
        )
        if reservation is None:
            self._terminal = "work_cap"
            self._last = self._snapshot(converged=False, terminal="capped", work=self.budgets.summary(self.budget_scope))
            return self._last
        try:
            if self.kernel.spec.schedule == "qbp_flooding":
                c2v, beliefs, v2c = self._flooding_pass()
            else:
                c2v, beliefs, v2c = self._serial_pass()
            marginals = np.asarray([llrs_to_probabilities(row, profile=self.kernel.profile) for row in beliefs])
            candidate = self.kernel.candidate_from_beliefs(beliefs)
        except Exception:
            reservation.rollback()
            self._terminal = "numerical_failure"
            self._last = self._snapshot(converged=False, terminal="numerical_failure", work=self.budgets.summary(self.budget_scope))
            raise
        reservation.commit_once()
        self._iteration += 1
        self._c2v, self._beliefs, self._v2c = c2v, beliefs, v2c
        self._marginals, self._candidate = marginals, candidate
        converged = self._is_converged()
        self._terminal = "converged" if converged else "running"
        self._last = self._snapshot(converged=converged, terminal=self._terminal, work=self.budgets.summary(self.budget_scope))
        self._sweeps.append(self._last)
        return self._last

    def _flooding_pass(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Flooding reads one complete old V2C snapshot, so each edge's scalar
        # commutation value is identical for all neighboring exclusions.
        quantized_v2c = np.asarray([
            self.scalar_commutation(self._v2c[edge], int(label))
            for edge, label in enumerate(self._labels)
        ], dtype=np.float64)
        c2v = np.asarray([
            self.kernel.check_message(
                [float(quantized_v2c[index]) for index in self._check_incident[int(check)] if index != edge],
                int(self.problem.syndrome[check]),
            )
            for edge, check in enumerate(self._checks)
        ])
        beliefs = np.asarray([
            self.kernel.posterior(
                self.priors[variable], c2v[list(self._variable_incident[variable])],
                self._labels[list(self._variable_incident[variable])],
            )
            for variable in range(self.problem.code.n)
        ])
        v2c = np.asarray([
            self.kernel.variable_message(beliefs[variable], c2v[edge], int(label))
            for edge, (variable, label) in enumerate(zip(self._variables, self._labels, strict=True))
        ])
        return c2v, beliefs, v2c

    def _serial_pass(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        c2v, v2c, beliefs = self._c2v.copy(), self._v2c.copy(), self._beliefs.copy()
        for variable in range(self.problem.code.n):
            incident = list(self._variable_incident[variable])
            for edge in incident:
                c2v[edge] = self._edge_delta(int(edge), v2c)
            beliefs[variable] = self.kernel.posterior(self.priors[variable], c2v[incident], self._labels[incident])
            for edge in incident:
                v2c[edge] = self.kernel.variable_message(beliefs[variable], c2v[edge], int(self._labels[edge]))
        return c2v, beliefs, v2c

    def run(self) -> Mbp4Result:
        if self._is_converged() and self._iteration == 0:
            self._terminal = "converged"
        while self._terminal == "running" and self._iteration < self.kernel.spec.max_iterations:
            self.sweep()
        if self._terminal == "running":
            self._terminal = "max_iterations"
            self._last = self._snapshot(converged=False, terminal="max_iterations", work=self.budgets.summary(self.budget_scope))
        termination = self._terminal
        if termination == "numerical_failure":
            raise QuaternaryNumericalFailure("MBP4 numerical failure")
        freshness = (
            "complete_old_v2c_snapshot_then_complete_commit"
            if self.kernel.spec.schedule == "qbp_flooding"
            else "variable_serial_current_v2c_then_immediate_incident_commit"
        )
        return Mbp4Result(
            spec=self.kernel.spec, sweeps=tuple(self._sweeps), candidate=self._candidate, termination=termination,
            work=self.budgets.summary(self.budget_scope), initial_state_digest=self._initial_state_digest,
            state_digest=self.state_digest, schedule_freshness=freshness,
        )


def reconstruct_mbp4(
    spec: Mbp4Spec, problem: QuaternaryOriginalProblem, priors: object, expected: Mbp4Result, *, budgets: BudgetTree | None = None,
) -> Mbp4Result:
    """Re-run only decoder-visible inputs and reject changed alpha, state, work, or candidate evidence."""
    if not isinstance(expected, Mbp4Result):
        raise ValueError("MBP4 replay requires an Mbp4Result")
    rebuilt = FixedAlphaMbp4Kernel(spec).new_session(problem, priors, budgets=budgets).run()
    if rebuilt.as_evidence() != expected.as_evidence():
        raise ValueError("MBP4 replay evidence differs from the declared recurrence result")
    return rebuilt


__all__ = ["FixedAlphaMbp4Kernel", "Mbp4Result", "Mbp4Session", "Mbp4Spec", "reconstruct_mbp4"]
