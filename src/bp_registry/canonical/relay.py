"""Sequential, posterior-only Relay-BP controller for canonical CSS flooding."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from typing import Iterable

import numpy as np

from .budgets import BudgetTree, WorkVector
from .contracts import MemoryBindingV4, RelayLegSpec
from .memory import AffinePriorMemory, MemoryState
from .numerics import finite_saturate
from .schedules import EdgeTable, FloodingSchedule


@dataclass(frozen=True, slots=True)
class PosteriorTransferV2:
    """A finite float64 posterior LLR vector and no warm-start state."""

    representation: str
    values: tuple[float, ...]
    vector_length: int
    producer_leg_lineage_id: str
    numerical_profile: str
    clipping_evidence: str
    digest: str

    @classmethod
    def from_posterior(
        cls, posterior: np.ndarray, *, producer_leg_lineage_id: str,
        numerical_profile: str, clipping_evidence: str,
    ) -> "PosteriorTransferV2":
        values = np.asarray(posterior, dtype=np.float64)
        if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
            raise ValueError("Relay transfer requires a nonempty finite posterior LLR vector")
        if not producer_leg_lineage_id or not numerical_profile or not clipping_evidence:
            raise ValueError("Relay transfer requires producer, numerical profile, and clipping evidence")
        canonical = np.asarray(values, dtype="<f8")
        return cls(
            representation="llr_log_p0_over_p1",
            values=tuple(float(value) for value in canonical), vector_length=int(canonical.size),
            producer_leg_lineage_id=producer_leg_lineage_id, numerical_profile=numerical_profile,
            clipping_evidence=clipping_evidence, digest=sha256(canonical.tobytes()).hexdigest(),
        )

    def as_array(self) -> np.ndarray:
        values = np.asarray(self.values, dtype=np.float64)
        if (
            self.representation != "llr_log_p0_over_p1" or values.ndim != 1
            or values.shape != (self.vector_length,) or not np.all(np.isfinite(values))
            or sha256(np.asarray(values, dtype="<f8").tobytes()).hexdigest() != self.digest
        ):
            raise ValueError("Relay transfer payload is invalid or tampered")
        values.setflags(write=False)
        return values

    def as_evidence(self) -> dict[str, object]:
        return {
            "representation": self.representation, "vector_length": self.vector_length,
            "producer_leg_lineage_id": self.producer_leg_lineage_id,
            "numerical_profile": self.numerical_profile,
            "clipping_evidence": self.clipping_evidence, "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class RelayLegResult:
    leg_index: int
    lineage_id: str
    candidate: np.ndarray
    posterior: np.ndarray
    iterations: int
    converged: bool


@dataclass(frozen=True, slots=True)
class RelayRunResult:
    legs: tuple[RelayLegResult, ...]
    transfers: tuple[PosteriorTransferV2, ...]
    termination: str

    @property
    def candidate(self) -> np.ndarray | None:
        converged = tuple(leg for leg in self.legs if leg.converged)
        return None if not converged else converged[0].candidate


class _PriorVectorKernel:
    """Delegates BP rules while injecting a per-variable decoder-visible prior vector."""

    def __init__(self, kernel: object, prior: np.ndarray) -> None:
        self._kernel = kernel
        self._prior = np.asarray(prior, dtype=np.float64)

    def prior(self, _error_rate: float) -> float:
        return 0.0

    def check_message(self, *args: object, **kwargs: object) -> float:
        return self._kernel.check_message(*args, **kwargs)  # type: ignore[attr-defined]

    def assemble_beliefs(self, variable_count: int, edge_variables: tuple[int, ...], messages: np.ndarray, _prior: float) -> np.ndarray:
        if self._prior.shape != (variable_count,):
            raise ValueError("Relay prior length does not match the canonical graph")
        beliefs = np.array(self._prior, dtype=np.float64, copy=True)
        for variable, message in zip(edge_variables, messages, strict=True):
            beliefs[variable] += message
        return finite_saturate(beliefs, boundary="relay_belief_assembly", profile=self._kernel.profile)  # type: ignore[attr-defined]

    def variable_message(self, *args: object, **kwargs: object) -> float:
        return self._kernel.variable_message(*args, **kwargs)  # type: ignore[attr-defined]

    def candidate_from_beliefs(self, beliefs: np.ndarray) -> np.ndarray:
        return self._kernel.candidate_from_beliefs(beliefs)  # type: ignore[attr-defined]


class RelayController:
    """Runs fresh legs sequentially; only a validated posterior crosses leg boundaries."""

    def __init__(self, *, memory_bindings: Iterable[MemoryBindingV4], numerical_profile: str) -> None:
        bindings = tuple(sorted(memory_bindings, key=lambda binding: binding.order))
        if not bindings:
            raise ValueError("Relay requires at least one ordered memory binding")
        self._memory = tuple(AffinePriorMemory(binding.binding_id, float(binding.alpha)) for binding in bindings)
        self.numerical_profile = numerical_profile

    def run(
        self, *, edge_table: EdgeTable, check_matrix: np.ndarray, syndrome: np.ndarray, kernel: object,
        error_rate: float, legs: tuple[RelayLegSpec, ...], budgets: BudgetTree, scope: str, lineage_prefix: str,
    ) -> RelayRunResult:
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("Relay requires a finite error rate strictly between zero and one")
        base_prior = np.full(edge_table.variable_count, kernel.prior(error_rate), dtype=np.float64)  # type: ignore[attr-defined]
        states: dict[str, MemoryState] = {}
        previous: PosteriorTransferV2 | None = None
        leg_results: list[RelayLegResult] = []
        transfers: list[PosteriorTransferV2] = []

        for index, leg in enumerate(legs):
            prior = base_prior
            if previous is not None:
                transfer_reservation = budgets.reserve(
                    scope, WorkVector(relay_transfers=1), leaf_id=f"relay:{lineage_prefix}:transfer:{index}",
                )
                if transfer_reservation is None:
                    return RelayRunResult(tuple(leg_results), tuple(transfers), "budget_exhausted")
                prior = previous.as_array()
                for memory in self._memory:
                    proposal = memory.propose(base_prior, prior)
                    states[memory.binding_id] = memory.commit(proposal, states.get(memory.binding_id))
                    prior = proposal.prior
                transfer_reservation.commit_once()
                transfers.append(previous)

            # Each loop builds a new schedule and V2C snapshot, intentionally resetting all leg-local state.
            schedule = FloodingSchedule(edge_table, kernel=_PriorVectorKernel(kernel, prior), profile=kernel.profile)  # type: ignore[attr-defined]
            messages = np.asarray([prior[variable] for _check, variable in edge_table.edges], dtype=np.float64)
            posterior = np.array(prior, dtype=np.float64, copy=True)
            candidate = kernel.candidate_from_beliefs(posterior)  # type: ignore[attr-defined]
            converged = bool(np.array_equal((check_matrix.astype(np.int64) @ candidate.astype(np.int64)) % 2, syndrome))
            completed = 0
            for iteration in range(1, leg.max_iterations + 1):
                proposed = WorkVector.from_flooding_counts(
                    edge_count=edge_table.edge_count, variable_count=edge_table.variable_count,
                )
                reservation = budgets.reserve(
                    scope, proposed, leaf_id=f"relay:{lineage_prefix}:leg:{index}:sweep:{iteration}",
                )
                if reservation is None:
                    return RelayRunResult(tuple(leg_results), tuple(transfers), "budget_exhausted")
                sweep = schedule.sweep(messages, syndrome, error_rate=error_rate, source_iteration=iteration - 1)
                messages = sweep.new_v2c
                posterior = sweep.beliefs
                candidate = sweep.candidate
                completed = iteration
                reservation.commit_once()
                if np.array_equal((check_matrix.astype(np.int64) @ candidate.astype(np.int64)) % 2, syndrome):
                    converged = True
                    break
            candidate = np.array(candidate, dtype=np.uint8, copy=True)
            candidate.setflags(write=False)
            posterior = np.array(posterior, dtype=np.float64, copy=True)
            posterior.setflags(write=False)
            lineage_id = f"{lineage_prefix}:leg:{index}"
            result = RelayLegResult(index, lineage_id, candidate, posterior, completed, converged)
            leg_results.append(result)
            previous = PosteriorTransferV2.from_posterior(
                posterior, producer_leg_lineage_id=lineage_id, numerical_profile=self.numerical_profile,
                clipping_evidence="canonical_finite_saturate:relay_belief_assembly",
            )
        return RelayRunResult(tuple(leg_results), tuple(transfers), "completed")
