"""Sequential, posterior-only Relay-BP controller for canonical CSS flooding."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
from typing import Iterable, Literal

import numpy as np

from .budgets import BudgetTree, RelayWorkAccounting, WorkVector
from .contracts import MemoryBindingV4, RelayLegSpec, RelayMemoryTuningV4, RelaySpecV4
from .memory import AffinePriorMemory, MemoryAssignmentSpec, MemoryCompositionState, MemoryState
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
    score: "RelayCandidateScore | None" = None
    memory_application: "RelayMemoryApplication | None" = None


@dataclass(frozen=True, slots=True)
class RelayMemoryApplication:
    """The complete decoder-visible gamma assignment for one Relay leg.

    The vector itself remains bounded by a digest.  Its source interval and
    exact PCG64 seed are retained, so an auditor can reconstruct every applied
    variable coefficient without turning every routine ledger into a large
    trace sidecar.
    """

    leg_index: int
    mode: Literal["legacy_transfer_affine", "first_leg_uniform_gamma", "later_leg_disordered_gamma"]
    gamma: np.ndarray | None
    declared_first_leg_gamma: float | None
    later_leg_center: float | None
    later_leg_width: float | None
    later_leg_low: float | None
    later_leg_high: float | None
    seed_identity: str | None
    derived_seed_identity: str | None
    pcg64_seed_hex: str | None
    sample_seed_identity: str | None

    def as_evidence(self) -> dict[str, object]:
        gamma = self.gamma
        return {
            "source_semantics": "trmue/relay@v0.2.2: relay.rs:183-203; min_sum.rs:406-448",
            "equation": "effective_prior=(1-gamma)*channel_prior+gamma*previous_posterior",
            "applied_each_source_iteration": self.mode != "legacy_transfer_affine",
            "leg_index": self.leg_index,
            "mode": self.mode,
            "declared_first_leg_gamma": self.declared_first_leg_gamma,
            "later_leg_center": self.later_leg_center,
            "later_leg_width": self.later_leg_width,
            "later_leg_low": self.later_leg_low,
            "later_leg_high": self.later_leg_high,
            "seed_identity": self.seed_identity,
            "derived_seed_identity": self.derived_seed_identity,
            "pcg64_seed_hex": self.pcg64_seed_hex,
            "sample_seed_identity": self.sample_seed_identity,
            "gamma_sha256": None if gamma is None else sha256(np.asarray(gamma, dtype="<f8").tobytes()).hexdigest(),
            "gamma_count": None if gamma is None else int(gamma.size),
            "gamma_min": None if gamma is None else float(np.min(gamma)),
            "gamma_max": None if gamma is None else float(np.max(gamma)),
        }


@dataclass(frozen=True, slots=True)
class RelayCandidateScore:
    """A decoder-visible Relay candidate score; lower values win stably."""

    leg_index: int
    syndrome_weight: int
    prior_weight: float

    def __post_init__(self) -> None:
        if self.leg_index < 0 or self.syndrome_weight < 0 or not math.isfinite(self.prior_weight):
            raise ValueError("Relay candidate scores require finite decoder-visible values")

    @property
    def selection_key(self) -> tuple[int, float, int]:
        return (self.syndrome_weight, self.prior_weight, self.leg_index)


@dataclass(frozen=True, slots=True)
class RelayPreset:
    """Named immutable Relay controls, including their CSS adaptation status."""

    name: str
    procedure: Literal["source_internal_bp", "canonical_internal_bp"]
    fidelity_status: Literal["source_procedure_css_adaptation", "canonical_css_adaptation", "controlled_component_adaptation"]
    total_leg_limit: int
    first_leg_iteration_limit: int
    later_leg_iteration_limit: int
    solution_limit: int
    transfer: Literal["posterior_only", "disabled"]
    first_leg_memory: Literal["uniform"]
    later_leg_memory: Literal["uniform", "disordered"]
    numerical_profile: str
    source_parameter_sweep: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not self.name or self.total_leg_limit < 1 or self.solution_limit < 1:
            raise ValueError("Relay presets require a name and positive leg and solution limits")
        if self.first_leg_iteration_limit < 1 or self.later_leg_iteration_limit < 1:
            raise ValueError("Relay presets require positive iteration limits")
        if self.procedure == "source_internal_bp" and self.fidelity_status not in {
            "source_procedure_css_adaptation", "controlled_component_adaptation",
        }:
            raise ValueError("source Relay presets require a source or controlled CSS-adaptation status")
        if self.procedure == "canonical_internal_bp" and self.fidelity_status == "source_procedure_css_adaptation":
            raise ValueError("canonical Relay presets cannot claim source-procedure fidelity")
        if self.source_parameter_sweep is not None:
            low, high = self.source_parameter_sweep
            if not math.isfinite(low) or not math.isfinite(high) or low >= high:
                raise ValueError("Relay source parameter sweeps must be finite increasing intervals")

    @classmethod
    def source_procedure(cls) -> "RelayPreset":
        return cls(
            name="relay-source-internal-bp-v0.2.2", procedure="source_internal_bp",
            fidelity_status="source_procedure_css_adaptation", total_leg_limit=301,
            first_leg_iteration_limit=80, later_leg_iteration_limit=60, solution_limit=301,
            transfer="posterior_only", first_leg_memory="uniform", later_leg_memory="disordered",
            numerical_profile="cpu-float64-spa-v1", source_parameter_sweep=(-0.24, 0.66),
        )

    @classmethod
    def canonical_default(cls) -> "RelayPreset":
        return cls(
            name="relay-canonical-css-default-v1", procedure="canonical_internal_bp",
            fidelity_status="canonical_css_adaptation", total_leg_limit=2,
            first_leg_iteration_limit=4, later_leg_iteration_limit=4, solution_limit=2,
            transfer="posterior_only", first_leg_memory="uniform", later_leg_memory="uniform",
            numerical_profile="cpu-float64-spa-v1",
        )

    @property
    def legs(self) -> tuple[RelayLegSpec, ...]:
        return (RelayLegSpec(max_iterations=self.first_leg_iteration_limit),) + tuple(
            RelayLegSpec(max_iterations=self.later_leg_iteration_limit) for _ in range(self.total_leg_limit - 1)
        )

    def with_controls(
        self, *, total_leg_limit: int | None = None, solution_limit: int | None = None,
        transfer: Literal["posterior_only", "disabled"] | None = None,
        later_leg_memory: Literal["uniform", "disordered"] | None = None,
        numerical_profile: str | None = None, source_parameter_sweep: tuple[float, float] | None = None,
    ) -> "RelayPreset":
        """Return a separately named controlled adaptation without mutating this preset."""
        if all(value is None for value in (total_leg_limit, solution_limit, transfer, later_leg_memory, numerical_profile, source_parameter_sweep)):
            return self
        return replace(
            self, name=f"relay-controlled-{self.procedure}-v1", fidelity_status="controlled_component_adaptation",
            total_leg_limit=self.total_leg_limit if total_leg_limit is None else total_leg_limit,
            solution_limit=self.solution_limit if solution_limit is None else solution_limit,
            transfer=self.transfer if transfer is None else transfer,
            later_leg_memory=self.later_leg_memory if later_leg_memory is None else later_leg_memory,
            numerical_profile=self.numerical_profile if numerical_profile is None else numerical_profile,
            source_parameter_sweep=self.source_parameter_sweep if source_parameter_sweep is None else source_parameter_sweep,
        )

    def ablation(
        self, *, one_leg: bool = False, posterior_transfer: bool | None = None,
        later_leg_memory: Literal["uniform", "disordered"] | None = None,
        source_parameter_sweep: tuple[float, float] | None = None,
        numerical_profile: str | None = None,
    ) -> "RelayPreset":
        """Create a one-component Relay arm with an explicit controlled-adaptation label."""
        if posterior_transfer is not None and type(posterior_transfer) is not bool:
            raise ValueError("posterior_transfer must be a boolean control")
        return self.with_controls(
            total_leg_limit=1 if one_leg else None,
            transfer=None if posterior_transfer is None else ("posterior_only" if posterior_transfer else "disabled"),
            later_leg_memory=later_leg_memory, source_parameter_sweep=source_parameter_sweep,
            numerical_profile=numerical_profile,
        )

    def as_spec(self) -> RelaySpecV4:
        return RelaySpecV4(
            total_leg_limit=self.total_leg_limit, legs=self.legs, preset_name=self.name,
            first_leg_iteration_limit=self.first_leg_iteration_limit,
            later_leg_iteration_limit=self.later_leg_iteration_limit, solution_limit=self.solution_limit,
            transfer=self.transfer, first_leg_memory=self.first_leg_memory, later_leg_memory=self.later_leg_memory,
            numerical_profile=self.numerical_profile, procedure=self.procedure, fidelity_status=self.fidelity_status,
        )


@dataclass(frozen=True, slots=True)
class RelayRunResult:
    legs: tuple[RelayLegResult, ...]
    transfers: tuple[PosteriorTransferV2, ...]
    work_leaves: tuple[dict[str, object], ...]
    termination: str
    stopping_reason: Literal["solution_limit", "leg_limit", "budget_exhausted"]

    @property
    def candidate(self) -> np.ndarray | None:
        selected = RelayController.select_candidate(tuple(
            leg.score for leg in self.legs if leg.converged and leg.score is not None
        ))
        if selected is None:
            return None
        return next(leg.candidate for leg in self.legs if leg.leg_index == selected.leg_index)


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

    def __init__(
        self, *, memory_bindings: Iterable[MemoryBindingV4], numerical_profile: str,
        preset: RelayPreset | None = None, memory_tuning: RelayMemoryTuningV4 | None = None,
    ) -> None:
        bindings = tuple(sorted(memory_bindings, key=lambda binding: binding.order))
        if not bindings:
            raise ValueError("Relay requires at least one ordered memory binding")
        self._memory = tuple(AffinePriorMemory(binding.binding_id, float(binding.alpha)) for binding in bindings)
        self.numerical_profile = numerical_profile
        self.preset = preset
        self.memory_tuning = memory_tuning

    @staticmethod
    def _dynamic_prior(
        base_prior: np.ndarray, previous_posterior: np.ndarray, gamma: np.ndarray, *, kernel: object,
    ) -> np.ndarray:
        """Apply Relay's per-iteration affine prior without clipping gamma.

        The source permits finite gamma values outside the convex range.  The
        canonical numerical profile therefore clips the *resulting LLR* only at
        the existing named prior boundary, never the declared assignment.
        """
        if base_prior.shape != previous_posterior.shape or base_prior.shape != gamma.shape:
            raise ValueError("Relay dynamic memory operands must have equal variable shape")
        with np.errstate(over="raise", invalid="raise"):
            try:
                value = (1.0 - gamma) * base_prior + gamma * previous_posterior
            except FloatingPointError as error:
                raise ValueError("Relay dynamic memory produced nonfinite prior arithmetic") from error
        return finite_saturate(value, boundary="relay_dynamic_affine_prior", profile=kernel.profile)  # type: ignore[attr-defined]

    def _later_leg_assignment(
        self, *, tuning: RelayMemoryTuningV4, edge_table: EdgeTable,
        sample_seed_identity: str, leg_index: int, budgets: BudgetTree, scope: str,
        assignment: MemoryAssignmentSpec, assignment_state: object,
    ) -> tuple[np.ndarray, object, RelayMemoryApplication]:
        """Draw one deterministic, source-shaped per-variable gamma vector."""
        replay_identity = f"relay-memory-v022:{sample_seed_identity}:leg:{leg_index}"
        result = assignment.refresh(
            assignment_state, boundary="leg_start", replay_identity=replay_identity,
            variable_count=edge_table.variable_count, budgets=budgets, budget_scope=scope,
            history_state=MemoryCompositionState(), schedule_cursor=(), work=WorkVector.zero(),
        )
        if not result.admitted or result.evidence is None:
            raise RuntimeError("zero-work Relay memory assignment was unexpectedly denied")
        gamma = np.asarray(result.values, dtype=np.float64)
        # MemoryAssignmentSpec uses this exact digest as the PCG64 input.  Keep
        # it alongside the root identity and public sample identity so the draw
        # is independently reconstructible.
        derived_seed_identity = sha256(
            f"{result.state.derived_identity}:memory_assignment:{replay_identity}".encode("utf-8")
        ).hexdigest()
        application = RelayMemoryApplication(
            leg_index=leg_index, mode="later_leg_disordered_gamma", gamma=gamma,
            declared_first_leg_gamma=None, later_leg_center=tuning.later_leg_center,
            later_leg_width=tuning.later_leg_width, later_leg_low=tuning.later_leg_low,
            later_leg_high=tuning.later_leg_high, seed_identity=tuning.seed_identity,
            derived_seed_identity=derived_seed_identity, pcg64_seed_hex=derived_seed_identity[:32],
            sample_seed_identity=sample_seed_identity,
        )
        return gamma, result.state, application

    @staticmethod
    def select_candidate(scores: Iterable[RelayCandidateScore]) -> RelayCandidateScore | None:
        """Select only decoder-visible scores and preserve earlier-leg ties."""
        candidates = tuple(scores)
        return None if not candidates else min(candidates, key=lambda score: score.selection_key)

    def run(
        self, *, edge_table: EdgeTable, check_matrix: np.ndarray, syndrome: np.ndarray, kernel: object,
        error_rate: float, legs: tuple[RelayLegSpec, ...] | None, budgets: BudgetTree, scope: str, lineage_prefix: str,
        solution_limit: int | None = None, transfer: Literal["posterior_only", "disabled"] | None = None,
        sample_seed_identity: str | None = None,
    ) -> RelayRunResult:
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 1.0:
            raise ValueError("Relay requires a finite error rate strictly between zero and one")
        active_legs = legs if legs is not None else (self.preset.legs if self.preset is not None else None)
        if active_legs is None or not active_legs:
            raise ValueError("Relay requires one explicit pre-leg and zero or more later legs")
        active_solution_limit = solution_limit if solution_limit is not None else (
            self.preset.solution_limit if self.preset is not None else 1
        )
        active_transfer = transfer if transfer is not None else (
            self.preset.transfer if self.preset is not None else "posterior_only"
        )
        if active_solution_limit < 1:
            raise ValueError("Relay solution_limit must be positive")
        if self.memory_tuning is not None and (not isinstance(sample_seed_identity, str) or not sample_seed_identity):
            raise ValueError("active Relay memory tuning requires a public sample seed identity")
        base_prior = np.full(edge_table.variable_count, kernel.prior(error_rate), dtype=np.float64)  # type: ignore[attr-defined]
        previous: PosteriorTransferV2 | None = None
        leg_results: list[RelayLegResult] = []
        transfers: list[PosteriorTransferV2] = []
        accounting = RelayWorkAccounting(shot_identity=lineage_prefix)
        assignment: MemoryAssignmentSpec | None = None
        assignment_state: object | None = None
        if self.memory_tuning is not None:
            tuning = self.memory_tuning
            assignment = MemoryAssignmentSpec(
                mode="uniform", graph_sha256=edge_table.graph_sha256,
                root_seed_identity=sha256(tuning.seed_identity.encode("utf-8")).hexdigest(),
                refresh_boundary="leg_start", retain_history=False,
                low=tuning.later_leg_low, high=tuning.later_leg_high,
            )
            assignment_state = assignment.initial_state(
                configuration_identity=sha256(json.dumps(tuning.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                decoder_identity=tuning.seed_identity,
            )

        def finish(
            termination: str, stopping_reason: Literal["solution_limit", "leg_limit", "budget_exhausted"],
        ) -> RelayRunResult:
            # The budget tree is the reserve-before-mutation authority.  Relay
            # work leaves mirror only facts that it committed, so the public
            # ledger can retain per-leg ancestry without changing the cap.
            if accounting.summary() != budgets.summary(scope):
                raise RuntimeError("Relay committed leaves disagree with budgeted work")
            return RelayRunResult(
                tuple(leg_results), tuple(transfers), accounting.leaves(), termination, stopping_reason,
            )

        for index, leg in enumerate(active_legs):
            lineage_id = f"{lineage_prefix}:leg:{index}"
            prior = base_prior
            posterior_for_memory = np.array(base_prior, dtype=np.float64, copy=True)
            if previous is not None and active_transfer == "posterior_only":
                transfer_leaf_id = "relay-transfer:" + sha256(
                    f"{previous.producer_leg_lineage_id}:{previous.digest}".encode("utf-8")
                ).hexdigest()[:20]
                transfer_reservation = budgets.reserve(
                    scope, WorkVector(relay_transfers=1), leaf_id=transfer_leaf_id,
                )
                if transfer_reservation is None:
                    return finish("budget_exhausted", "budget_exhausted")
                prior = previous.as_array()
                posterior_for_memory = np.array(prior, dtype=np.float64, copy=True)
                # No history, gamma assignment, messages, iteration, or convergence crosses a leg boundary.
                if self.memory_tuning is None:
                    states: dict[str, MemoryState] = {}
                    for memory in self._memory:
                        proposal = memory.propose(base_prior, prior)
                        states[memory.binding_id] = memory.commit(proposal, states.get(memory.binding_id))
                        prior = proposal.prior
                transfer_reservation.commit_once()
                accounting.commit(
                    kind="transfer", leg_index=index,
                    lineage_id=previous.producer_leg_lineage_id, leaf_id=transfer_leaf_id,
                    delta=WorkVector(relay_transfers=1),
                )
                transfers.append(previous)

            memory_application: RelayMemoryApplication | None = None
            gamma: np.ndarray | None = None
            if self.memory_tuning is not None:
                tuning = self.memory_tuning
                if index == 0:
                    gamma = np.full(edge_table.variable_count, tuning.first_leg_gamma, dtype=np.float64)
                    memory_application = RelayMemoryApplication(
                        leg_index=index, mode="first_leg_uniform_gamma", gamma=gamma,
                        declared_first_leg_gamma=tuning.first_leg_gamma, later_leg_center=None,
                        later_leg_width=None, later_leg_low=None, later_leg_high=None,
                        seed_identity=tuning.seed_identity, derived_seed_identity=None,
                        pcg64_seed_hex=None, sample_seed_identity=sample_seed_identity,
                    )
                else:
                    assert assignment is not None and assignment_state is not None and sample_seed_identity is not None
                    gamma, assignment_state, memory_application = self._later_leg_assignment(
                        tuning=tuning, edge_table=edge_table, sample_seed_identity=sample_seed_identity,
                        leg_index=index, budgets=budgets, scope=scope, assignment=assignment,
                        assignment_state=assignment_state,
                    )

            # Each leg resets C2V/V2C state to channel priors.  For active
            # memory, only the posterior crosses a Relay boundary; the current
            # gamma vector is then applied before *every* source iteration.
            messages = np.asarray([base_prior[variable] for _check, variable in edge_table.edges], dtype=np.float64)
            posterior = np.array(posterior_for_memory if self.memory_tuning is not None else prior, dtype=np.float64, copy=True)
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
                    # Retain a started leg even when only a prefix of its
                    # sweeps committed.  Its explicit leaves are the durable
                    # record of that partial work.
                    candidate = np.array(candidate, dtype=np.uint8, copy=True)
                    candidate.setflags(write=False)
                    posterior = np.array(posterior, dtype=np.float64, copy=True)
                    posterior.setflags(write=False)
                    score = RelayCandidateScore(
                        leg_index=index,
                        syndrome_weight=int(np.count_nonzero(
                            (check_matrix.astype(np.int64) @ candidate.astype(np.int64)) % 2 != syndrome
                        )),
                        prior_weight=float(np.dot(candidate.astype(np.float64), base_prior)),
                    ) if converged else None
                    leg_results.append(RelayLegResult(index, lineage_id, candidate, posterior, completed, converged, score, memory_application))
                    return finish("budget_exhausted", "budget_exhausted")
                effective_prior = (
                    self._dynamic_prior(base_prior, posterior, gamma, kernel=kernel)
                    if gamma is not None else prior
                )
                schedule = FloodingSchedule(
                    edge_table, kernel=_PriorVectorKernel(kernel, effective_prior), profile=kernel.profile,
                )  # type: ignore[attr-defined]
                sweep = schedule.sweep(messages, syndrome, error_rate=error_rate, source_iteration=iteration - 1)
                messages = sweep.new_v2c
                posterior = sweep.beliefs
                candidate = sweep.candidate
                completed = iteration
                reservation.commit_once()
                accounting.commit(
                    kind="leg", leg_index=index, lineage_id=lineage_id,
                    leaf_id=f"relay:{lineage_prefix}:leg:{index}:sweep:{iteration}", delta=proposed,
                )
                if np.array_equal((check_matrix.astype(np.int64) @ candidate.astype(np.int64)) % 2, syndrome):
                    converged = True
                    break
            candidate = np.array(candidate, dtype=np.uint8, copy=True)
            candidate.setflags(write=False)
            posterior = np.array(posterior, dtype=np.float64, copy=True)
            posterior.setflags(write=False)
            syndrome_weight = int(np.count_nonzero(
                (check_matrix.astype(np.int64) @ candidate.astype(np.int64)) % 2 != syndrome
            ))
            score = None
            if converged:
                score = RelayCandidateScore(
                    leg_index=index, syndrome_weight=syndrome_weight,
                    prior_weight=float(np.dot(candidate.astype(np.float64), base_prior)),
                )
            result = RelayLegResult(index, lineage_id, candidate, posterior, completed, converged, score, memory_application)
            leg_results.append(result)
            previous = PosteriorTransferV2.from_posterior(
                posterior, producer_leg_lineage_id=lineage_id, numerical_profile=self.numerical_profile,
                clipping_evidence="canonical_finite_saturate:relay_belief_assembly",
            )
            if len(tuple(leg_result for leg_result in leg_results if leg_result.converged)) >= active_solution_limit:
                return finish("completed", "solution_limit")
        return finish("completed", "leg_limit")
