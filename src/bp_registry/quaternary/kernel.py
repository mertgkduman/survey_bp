"""Source-equation scalar LLR-BP4 kernel with attempt-owned session state."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import numbers

import numpy as np

from ..canonical.budgets import BudgetTree, WorkVector
from .algebra import Pauli, anticommutes
from .numerics import (
    QBP4_F64_V2,
    QuaternaryNumericalFailure,
    QuaternaryNumericalProfile,
    QuaternaryNumericalProfileV2,
    check_message as numerical_check_message,
    commutation_llr,
    finite_saturate,
    llrs_to_probabilities,
    pauli_hard_decision,
    probabilities_to_llrs,
)
from .problems import QuaternaryOriginalProblem


def _readonly(value: object, *, dtype: np.dtype | type) -> np.ndarray:
    result = np.array(value, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


def _priors(value: object, *, n: int) -> np.ndarray:
    probabilities = np.asarray(value, dtype=np.float64)
    if probabilities.shape != (n, 4) or not np.all(np.isfinite(probabilities)) or np.any(probabilities <= 0.0):
        raise ValueError("priors must be finite strictly positive (n, 4) I/X/Y/Z probabilities")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("every quaternary prior must sum to one")
    result = np.array(probabilities, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


def _session_problem(value: object) -> bool:
    """Admit immutable decoder graphs, including certified aSCED transforms.

    CSS aSCED graphs can deliberately contain noncommuting splitter rows and
    therefore cannot be represented as ``QuaternaryOriginalProblem``.  BP4
    only consumes immutable ordered checks, an ordered syndrome, and ``n``.
    """
    code = getattr(value, "code", None)
    checks = getattr(code, "checks", None)
    syndrome = getattr(value, "syndrome", None)
    n = getattr(code, "n", None)
    return (
        isinstance(n, int) and n > 0 and isinstance(checks, np.ndarray)
        and checks.ndim == 2 and checks.shape[1] == n
        and isinstance(syndrome, np.ndarray) and syndrome.shape == (checks.shape[0],)
        and np.issubdtype(checks.dtype, np.integer) and np.issubdtype(syndrome.dtype, np.integer)
        and np.all((checks >= Pauli.I) & (checks <= Pauli.Z))
        and np.all((syndrome == 0) | (syndrome == 1))
        and not checks.flags.writeable and not syndrome.flags.writeable
    )


@dataclass(frozen=True, slots=True)
class QbpSweep:
    """Immutable state after one admitted scalar BP4 sweep or terminal boundary."""

    iteration: int
    c2v: np.ndarray
    v2c: np.ndarray
    beliefs: np.ndarray
    marginals: np.ndarray
    candidate: np.ndarray
    converged: bool
    terminal: str
    work: WorkVector

    def __post_init__(self) -> None:
        if self.iteration < 0 or self.terminal not in {"running", "converged", "capped", "max_iterations", "numerical_failure"}:
            raise ValueError("QBP sweep has an invalid iteration or terminal state")
        c2v = _readonly(self.c2v, dtype=np.float64)
        v2c = _readonly(self.v2c, dtype=np.float64)
        beliefs = _readonly(self.beliefs, dtype=np.float64)
        marginals = _readonly(self.marginals, dtype=np.float64)
        candidate = _readonly(self.candidate, dtype=np.uint8)
        if c2v.ndim != 1 or v2c.shape != (c2v.size, 3) or beliefs.ndim != 2 or beliefs.shape[1:] != (3,):
            raise ValueError("QBP sweep message shapes are invalid")
        if marginals.shape != (beliefs.shape[0], 4) or candidate.shape != (beliefs.shape[0],):
            raise ValueError("QBP sweep posterior shapes are invalid")
        if not np.all(np.isfinite(c2v)) or not np.all(np.isfinite(v2c)) or not np.all(np.isfinite(beliefs)) or not np.all(np.isfinite(marginals)):
            raise ValueError("QBP sweep must retain finite numerical state")
        if not np.allclose(marginals.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
            raise ValueError("QBP sweep marginals must each normalize over I/X/Y/Z")
        if np.any((candidate < Pauli.I) | (candidate > Pauli.Z)) or not isinstance(self.work, WorkVector):
            raise ValueError("QBP sweep candidate or work is invalid")
        object.__setattr__(self, "c2v", c2v)
        object.__setattr__(self, "v2c", v2c)
        object.__setattr__(self, "beliefs", beliefs)
        object.__setattr__(self, "marginals", marginals)
        object.__setattr__(self, "candidate", candidate)


class ScalarLlrBp4Kernel:
    """Pure source-defined scalar LLR operations; sessions own all mutable buffers."""

    def __init__(self, *, profile: QuaternaryNumericalProfile = QBP4_F64_V2) -> None:
        if not isinstance(profile, QuaternaryNumericalProfile):
            raise ValueError("profile must be a QuaternaryNumericalProfile")
        self.profile = profile

    def prior_llrs(self, probabilities: object) -> np.ndarray:
        """Convert a decoder-visible I/X/Y/Z prior without inspecting hidden truth."""
        values = np.asarray(probabilities, dtype=np.float64)
        if values.shape != (4,):
            raise ValueError("a four-state I/X/Y/Z prior is required")
        return probabilities_to_llrs(values, profile=self.profile)

    def check_message(self, incoming: object, syndrome: int) -> float:
        """Source check update over the exact excluded-neighbor reduction."""
        return numerical_check_message(incoming, syndrome=syndrome, profile=self.profile)

    def posterior(self, prior: object, c2v: object, labels: object) -> np.ndarray:
        """Assemble all three nonidentity posterior LLRs from an ordered C2V buffer."""
        belief = self.prior_llrs(prior)
        messages = np.asarray(c2v, dtype=np.float64)
        edge_labels = np.asarray(labels)
        if messages.ndim != 1 or edge_labels.shape != messages.shape:
            raise ValueError("posterior messages and labels must be matching one-dimensional arrays")
        for message, label in zip(messages, edge_labels, strict=True):
            for state in (Pauli.X, Pauli.Y, Pauli.Z):
                if anticommutes(int(label), int(state)):
                    belief[int(state) - 1] += float(message)
        return finite_saturate(belief, boundary="bp4_posterior", profile=self.profile)

    def variable_message(self, posterior: object, check_value: float, edge_label: int) -> np.ndarray:
        """Return the three-component excluded V2C LLR message for one edge."""
        values = np.asarray(posterior, dtype=np.float64)
        if values.shape != (3,) or not np.all(np.isfinite(values)):
            raise QuaternaryNumericalFailure("nonfinite arithmetic at variable_message_input")
        result = np.array(values, dtype=np.float64, copy=True)
        for state in (Pauli.X, Pauli.Y, Pauli.Z):
            if anticommutes(int(edge_label), int(state)):
                result[int(state) - 1] -= float(check_value)
        if not np.all(np.isfinite(result)):
            raise QuaternaryNumericalFailure("nonfinite arithmetic at variable_message_output")
        return finite_saturate(result, boundary="bp4_variable_message", profile=self.profile)

    def candidate_from_beliefs(self, beliefs: object) -> np.ndarray:
        """Apply the persisted I<X<Y<Z decision to each complete three-LLR belief."""
        values = np.asarray(beliefs, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != 3:
            raise ValueError("candidate beliefs must have shape (n, 3)")
        return np.asarray([pauli_hard_decision(value, profile=self.profile) for value in values], dtype=np.uint8)

    def new_session(
        self,
        problem: QuaternaryOriginalProblem,
        priors: object,
        *,
        budgets: BudgetTree | None = None,
        budget_scope: str = "attempt",
    ) -> "QbpSession":
        return QbpSession(self, problem, priors, budgets=budgets, budget_scope=budget_scope)


class QbpSession:
    """One decoder attempt whose only mutable values are its owned message buffers."""

    def __init__(
        self,
        kernel: ScalarLlrBp4Kernel,
        problem: QuaternaryOriginalProblem,
        priors: object,
        *,
        budgets: BudgetTree | None = None,
        budget_scope: str = "attempt",
    ) -> None:
        if not isinstance(kernel, ScalarLlrBp4Kernel) or not _session_problem(problem):
            raise ValueError("QBP sessions require a scalar kernel and immutable check/syndrome problem")
        if not isinstance(budget_scope, str) or not budget_scope:
            raise ValueError("budget_scope must be nonempty")
        self.kernel = kernel
        self.problem = problem
        self.priors = _priors(priors, n=problem.code.n)
        self.budgets = BudgetTree(limits=(), parents={}) if budgets is None else budgets
        if not isinstance(self.budgets, BudgetTree):
            raise ValueError("budgets must be a BudgetTree")
        self.budget_scope = budget_scope
        rows, columns = np.nonzero(problem.code.checks != Pauli.I)
        self._checks = np.asarray(rows, dtype=np.int64)
        self._variables = np.asarray(columns, dtype=np.int64)
        self._labels = np.asarray(problem.code.checks[rows, columns], dtype=np.uint8)
        # A graph is immutable for the lifetime of a session. Resolve incidence
        # once, preserving the original check-major edge order for reductions.
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
        self._iteration = 0
        self._terminal = "running"
        self._last = self._snapshot(converged=self._is_converged(), terminal="running", work=WorkVector.zero())

    @property
    def last(self) -> QbpSweep:
        return self._last

    @property
    def state_digest(self) -> str:
        """Stable decoder-visible identity for the owned priors and edge buffers."""
        payload = {
            "priors": self.priors.tolist(), "c2v": self._c2v.tolist(),
            "v2c": self._v2c.tolist(), "beliefs": self._beliefs.tolist(),
            "candidate": self._candidate.tolist(), "iteration": self._iteration,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def replace_prior(self, variable: int, probabilities: object) -> None:
        """Commit one decoder-visible prior without resetting the owned messages.

        Q-BPGD owns the decimation lifecycle.  It may alter one selected prior
        between complete QBP blocks, while the current C2V/V2C buffers remain
        committed attempt state for the next block.
        """
        if isinstance(variable, bool) or not isinstance(variable, numbers.Integral) or not 0 <= int(variable) < self.problem.code.n:
            raise ValueError("prior replacement requires a valid qubit index")
        replacement = _priors(np.asarray(probabilities, dtype=np.float64)[None, :], n=1)[0]
        updated = np.array(self.priors, dtype=np.float64, copy=True)
        updated[int(variable)] = replacement
        updated.setflags(write=False)
        self.priors = updated
        self._prior_llrs = np.asarray([self.kernel.prior_llrs(row) for row in self.priors], dtype=np.float64)

    def _is_converged(self) -> bool:
        return bool(np.array_equal(self.problem.code.syndrome(self._candidate), self.problem.syndrome))

    def _sweep_work(self) -> WorkVector:
        return WorkVector.from_flooding_counts(edge_count=int(self._labels.size), variable_count=self.problem.code.n) + WorkVector(bp_calls=1)

    def _snapshot(self, *, converged: bool, terminal: str, work: WorkVector) -> QbpSweep:
        return QbpSweep(
            iteration=self._iteration,
            c2v=self._c2v,
            v2c=self._v2c,
            beliefs=self._beliefs,
            marginals=self._marginals,
            candidate=self._candidate,
            converged=converged,
            terminal=terminal,
            work=work,
        )

    def sweep(self, *, stop_on_convergence: bool = True) -> QbpSweep:
        """Reserve all four-state sweep work before calculating or mutating buffers."""
        if not isinstance(stop_on_convergence, bool):
            raise ValueError("stop_on_convergence must be boolean")
        if self._terminal != "running":
            return self._last
        next_iteration = self._iteration + 1
        work = self._sweep_work()
        reservation = self.budgets.reserve(self.budget_scope, work, leaf_id=f"qbp:{self.problem.lineage_id}:{next_iteration}")
        if reservation is None:
            self._terminal = "capped"
            self._last = self._snapshot(converged=False, terminal="capped", work=WorkVector.zero())
            return self._last
        try:
            next_c2v = np.empty_like(self._c2v)
            # Quantization depends only on the previous committed V2C value and
            # its edge label. Every outgoing message at a check reads that same
            # value, so share it without changing the excluded-neighbor order.
            quantized_v2c = np.asarray([
                commutation_llr(self._v2c[edge], int(label), profile=self.kernel.profile)
                for edge, label in enumerate(self._labels)
            ], dtype=np.float64)
            for edge, check in enumerate(self._checks):
                excluded = [
                    float(quantized_v2c[index])
                    for index in self._check_incident[int(check)] if index != edge
                ]
                next_c2v[edge] = self.kernel.check_message(excluded, int(self.problem.syndrome[check]))
            next_beliefs = np.empty_like(self._beliefs)
            for variable in range(self.problem.code.n):
                incident = self._variable_incident[variable]
                next_beliefs[variable] = self.kernel.posterior(
                    self.priors[variable], next_c2v[list(incident)], self._labels[list(incident)],
                )
            next_v2c = np.empty_like(self._v2c)
            for edge, (variable, label) in enumerate(zip(self._variables, self._labels, strict=True)):
                next_v2c[edge] = self.kernel.variable_message(next_beliefs[variable], next_c2v[edge], int(label))
            if isinstance(self.kernel.profile, QuaternaryNumericalProfileV2):
                damping = self.kernel.profile.v2c_damping
                next_v2c = finite_saturate(
                    damping * self._v2c + (1.0 - damping) * next_v2c,
                    boundary="bp4_damped_variable_message", profile=self.kernel.profile,
                )
            next_marginals = np.asarray([llrs_to_probabilities(row, profile=self.kernel.profile) for row in next_beliefs])
            next_candidate = self.kernel.candidate_from_beliefs(next_beliefs)
        except Exception:
            reservation.rollback()
            self._terminal = "numerical_failure"
            self._last = self._snapshot(converged=False, terminal="numerical_failure", work=WorkVector.zero())
            raise
        reservation.commit_once()
        self._iteration = next_iteration
        self._c2v = next_c2v
        self._v2c = next_v2c
        self._beliefs = next_beliefs
        self._marginals = next_marginals
        self._candidate = next_candidate
        converged = self._is_converged()
        self._terminal = "converged" if converged and stop_on_convergence else "running"
        self._last = self._snapshot(converged=converged, terminal=self._terminal, work=self.budgets.summary(self.budget_scope))
        return self._last

    def run(self, *, max_iterations: int) -> QbpSweep:
        """Run bounded flooding sweeps, retaining capped and failed terminal state."""
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, numbers.Integral) or max_iterations < 0:
            raise ValueError("max_iterations must be a nonnegative integer")
        if self._is_converged() and self._iteration == 0 and not isinstance(self.kernel.profile, QuaternaryNumericalProfileV2):
            self._terminal = "converged"
            self._last = self._snapshot(converged=True, terminal="converged", work=WorkVector.zero())
            return self._last
        while self._iteration < int(max_iterations) and self._terminal == "running":
            self.sweep()
        if self._terminal == "running":
            self._terminal = "max_iterations"
            self._last = self._snapshot(converged=False, terminal="max_iterations", work=self.budgets.summary(self.budget_scope))
        return self._last


__all__ = ["QbpSession", "QbpSweep", "ScalarLlrBp4Kernel"]
