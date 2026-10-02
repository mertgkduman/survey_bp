"""Truth-sealed canonical CSS shot orchestration and durable terminal evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .. import evaluator
from ..css import CssCode
from ..ledger import CanonicalEventWriter, LedgerWriter, ShotOwnershipError, read_canonical_events, reconcile
from ..sampling import DecoderObservation, HiddenTruth
from .contracts import (
    CanonicalManifestV2,
    CanonicalManifestV3,
    CanonicalManifestV4,
    CanonicalManifestV5,
    CanonicalManifestV6,
    CanonicalManifestV7,
    Hook,
    PolicyBinding,
    PolicyDecision,
    ResolvedComposition,
    parse_canonical_manifest,
    validate_composition,
)
from .budgets import BudgetLimit, BudgetTermination, BudgetTree, BudgetView, Measurement, QualifiedIteration, ScheduleTerminalEvidence, WallClockLimit, WorkVector
from .kernel import BinarySpaKernel
from .group_shuffled import HsuGroupSchedule
from .profiling import LocalProfiler, ProfilingPlan
from .lineage import LineageEdge, LineageId, stable_lineage_id
from .numerics import NumericalFailure
from .numerics import MIN_SUM_CPU_F64
from .updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, resolve_generated_configuration_assignment
from .problems import OriginalProblem, OriginalSpaceCandidate, WorkingProblem, select_stable_candidate
from .schedules import (
    CheckNodeSerialSchedule, EdgeTable, FloodingSchedule, FloodingSweep,
    LayeredSchedule, RandomizedTraversalPlan, VariableNodeSerialSchedule,
)
from .verification import PublicShotContext, validate_canonical_shot
from .relay import RelayController
from .memory_execution import LocalMemoryExecution, MemoryFloodingSchedule, validate_single_attempt_memory
from .tracing import TracePlan, TraceSink
from .contracts import Phase5InterventionContract
from .phase5 import execute_phase5_controller, finalize_phase5_deadline, phase5_attempt_events, phase5_work_evidence


class CanonicalConflictError(ValueError):
    """A stable run/shot key was reused with different canonical content."""


@dataclass(frozen=True)
class LifecycleEvent:
    """An engine-owned lifecycle boundary available to later policy families."""

    hook: Hook


@dataclass(frozen=True)
class CapabilityView:
    """Copied, immutable decoder-visible values; no hidden truth or engine state."""

    values: Mapping[str, Any]


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, np.ndarray):
        copied = np.array(value, copy=True)
        copied.setflags(write=False)
        return copied
    return value


class PolicyRuntime:
    """Engine-owned state allocator and decision validator for a resolved composition."""

    _LIFECYCLE = (
        Hook.SHOT, Hook.SEARCH, Hook.MEMBER, Hook.LEG, Hook.BRANCH,
        Hook.ATTEMPT, Hook.ITERATION, Hook.MESSAGE,
    )

    def __init__(self, composition: ResolvedComposition):
        self._bindings = {binding.binding_id: binding for binding in composition.bindings}
        self._private_state: dict[tuple[str, str], dict[str, int | None]] = {}

    def traverse_lifecycle(self) -> tuple[LifecycleEvent, ...]:
        return tuple(LifecycleEvent(hook) for hook in self._LIFECYCLE)

    def capability_view(self, values: Mapping[str, Any]) -> CapabilityView:
        return CapabilityView(MappingProxyType({str(key): _freeze_value(value) for key, value in values.items()}))

    def private_state(self, binding_id: str, *, sibling_id: str) -> dict[str, int | None]:
        binding = self._binding(binding_id)
        key = (binding.binding_id, f"{binding.state_lifetime.value}:{sibling_id}")
        return self._private_state.setdefault(key, {name: None for name in binding.owned_state})

    def apply_decision(self, decision: PolicyDecision, *, sibling_id: str = "default") -> PolicyDecision:
        binding = self._binding(decision.binding_id)
        if decision.hook != binding.hook.value:
            raise ValueError(f"decision hook {decision.hook!r} does not match binding hook {binding.hook.value!r}")
        if decision.action == "state_update":
            unknown = set(decision.state_updates).difference(binding.owned_state)
            if unknown:
                raise ValueError(f"binding {binding.binding_id!r} does not own state {sorted(unknown)!r}")
            state = self.private_state(binding.binding_id, sibling_id=sibling_id)
            state.update(decision.state_updates)
        return decision

    def _binding(self, binding_id: str) -> PolicyBinding:
        try:
            return self._bindings[binding_id]
        except KeyError as error:
            raise ValueError(f"unknown policy binding {binding_id!r}") from error


@dataclass(frozen=True)
class CanonicalExecutionResult:
    run_id: str
    shot_id: int
    termination: str
    evaluation: evaluator.Evaluation | None
    candidate: np.ndarray | None


@dataclass(frozen=True)
class AtomicFloodingResult:
    """An attempt result whose completed sweeps each committed one leaf vector."""

    v2c: np.ndarray
    iterations: int
    termination: BudgetTermination | None
    last_sweep: FloodingSweep | None
    converged: bool = False


@dataclass(frozen=True, slots=True)
class ScheduleProgress:
    """Serializable schedule-owned progress with no mutable hidden cursor."""

    iteration: int
    local_steps: int
    cursor: tuple[int, ...] = ()
    rng_state: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class LocalStepProposal:
    """The whole local mutation plus its mandatory convergence check work."""

    label: str
    proposed_work: WorkVector
    compute: Callable[[], np.ndarray]


@dataclass(frozen=True, slots=True)
class LocalStepResult:
    admitted: bool
    progress: ScheduleProgress
    converged: bool
    termination: BudgetTermination | None = None


class CanonicalLocalStepExecutor:
    """Schedule-neutral reserve → compute → commit → check local-step boundary."""

    def __init__(self, budgets: BudgetTree, *, scope: str) -> None:
        self.budgets = budgets
        self.scope = scope
        self._ordinal = 0

    def execute(
        self,
        proposal: LocalStepProposal,
        *,
        messages: np.ndarray,
        progress: ScheduleProgress,
        policy_state: Mapping[str, Any],
        cache: Mapping[str, Any],
        is_converged: Callable[[np.ndarray], bool],
    ) -> LocalStepResult:
        """Leave every supplied state untouched when the complete bundle is denied."""
        if proposal.proposed_work.convergence_checks != 1:
            raise ValueError("a canonical local step must reserve one convergence check")
        leaf_id = f"{self.scope}:local-step:{self._ordinal}:{proposal.label}"
        reservation = self.budgets.reserve(self.scope, proposal.proposed_work, leaf_id=leaf_id)
        if reservation is None:
            return LocalStepResult(False, progress, False, self.budgets.last_termination)
        before = np.array(messages, dtype=np.float64, copy=True)
        try:
            temporary = np.asarray(proposal.compute(), dtype=np.float64)
            if temporary.shape != messages.shape:
                raise ValueError("local-step computation must preserve the message-buffer shape")
            if not np.all(np.isfinite(temporary)):
                raise NumericalFailure("nonfinite arithmetic at canonical_local_step")
            messages[...] = temporary
            converged = bool(is_converged(messages))
            reservation.commit_once()
            self._ordinal += 1
            return LocalStepResult(
                True,
                ScheduleProgress(progress.iteration, progress.local_steps + 1, progress.cursor, progress.rng_state),
                converged,
            )
        except BaseException:
            messages[...] = before
            if reservation.active:
                reservation.rollback()
            raise


def _kernel_for_manifest(manifest: CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5, edge_table: EdgeTable | None = None) -> BinarySpaKernel:
    """Resolve only the closed update registry; policies never receive hidden truth."""
    update = manifest.policies.update.kind
    if update == "min_sum":
        return BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    if update == "normalized_min_sum":
        if edge_table is None:
            raise ValueError("normalized_min_sum requires a resolved immutable EdgeTable assignment")
        assignment = manifest.policies.update.parameter_assignment
        if assignment is None and isinstance(manifest, (CanonicalManifestV3, CanonicalManifestV5)):
            assignment, _ = resolve_generated_configuration_assignment(
                manifest.policies.update.model_dump(mode="json"), manifest.model_dump(mode="json"),
                graph_sha256=edge_table.graph_sha256, check_count=edge_table.check_count,
                edge_count=edge_table.edge_count,
            )
        if assignment is None:
            raise ValueError("normalized_min_sum requires a resolved immutable EdgeTable assignment")
        resolved = assignment.resolve(
            graph_sha256=edge_table.graph_sha256, check_count=edge_table.check_count,
            edge_count=edge_table.edge_count, source_iteration=0,
            edge_checks=tuple(check for check, _variable in edge_table.edges),
        )
        return BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=NormalizedMinSumUpdate(
                assignment,
                resolved_alpha=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            ),
        )
    if update == "offset_min_sum":
        if edge_table is None:
            raise ValueError("offset_min_sum requires a resolved immutable EdgeTable assignment")
        assignment = manifest.policies.update.parameter_assignment
        if assignment is None and isinstance(manifest, (CanonicalManifestV3, CanonicalManifestV5)):
            assignment, _ = resolve_generated_configuration_assignment(
                manifest.policies.update.model_dump(mode="json"), manifest.model_dump(mode="json"),
                graph_sha256=edge_table.graph_sha256, check_count=edge_table.check_count,
                edge_count=edge_table.edge_count,
            )
        if assignment is None:
            raise ValueError("offset_min_sum requires a resolved immutable EdgeTable assignment")
        resolved = assignment.resolve(
            graph_sha256=edge_table.graph_sha256, check_count=edge_table.check_count,
            edge_count=edge_table.edge_count, source_iteration=0,
            edge_checks=tuple(check for check, _variable in edge_table.edges),
        )
        return BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=OffsetMinSumUpdate(
                assignment,
                resolved_beta=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            ),
        )
    if update == "binary_spa":
        return BinarySpaKernel()
    raise ValueError(f"unsupported executable update rule {update!r}")


class AtomicFloodingExecutor:
    """Reserve a whole flooding sweep before calculation or message-buffer swap."""

    def __init__(
        self,
        schedule: FloodingSchedule,
        budgets: BudgetTree,
        *,
        scope: str,
        wall_clock: WallClockLimit | None = None,
    ) -> None:
        self.schedule = schedule
        self.budgets = budgets
        self.scope = scope
        self.wall_clock = wall_clock

    def _wall_boundary(self, kind: str) -> BudgetTermination | None:
        return None if self.wall_clock is None else self.wall_clock.check(kind, scope=self.scope)

    def run_attempt(
        self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iterations: int,
        is_converged: Callable[[FloodingSweep], bool] | None = None,
    ) -> AtomicFloodingResult:
        """Finish in-flight work, then stop only at a named operational boundary."""
        state = np.array(old_v2c, dtype=np.float64, copy=True)
        local_steps = CanonicalLocalStepExecutor(self.budgets, scope=self.scope)
        progress = ScheduleProgress(iteration=0, local_steps=0)
        terminal = self._wall_boundary("attempt_start")
        if terminal is not None:
            return AtomicFloodingResult(state, 0, terminal, None)
        last_sweep: FloodingSweep | None = None
        for iteration in range(1, max_iterations + 1):
            terminal = self._wall_boundary("iteration_boundary")
            if terminal is not None:
                return AtomicFloodingResult(state, iteration - 1, terminal, last_sweep)
            proposed = WorkVector.from_flooding_counts(
                edge_count=self.schedule.edge_table.edge_count,
                variable_count=self.schedule.edge_table.variable_count,
            )
            completed: list[FloodingSweep] = []

            def compute() -> np.ndarray:
                rule = getattr(self.schedule.kernel, "update_rule", None)
                assignment = getattr(rule, "alpha", getattr(rule, "beta", None))
                if isinstance(self.schedule, MemoryFloodingSchedule) or getattr(assignment, "shape", None) == "source_iteration":
                    sweep = self.schedule.sweep(
                        state, syndrome, error_rate=error_rate, source_iteration=iteration - 1,
                    )
                else:
                    # Preserve the V2 public flooding call surface and existing instrumentation hooks.
                    sweep = self.schedule.sweep(state, syndrome, error_rate=error_rate)
                completed.append(sweep)
                return sweep.new_v2c

            try:
                result = local_steps.execute(
                    LocalStepProposal(f"flooding:{iteration}", proposed, compute),
                    messages=state,
                    progress=progress,
                    policy_state={},
                    cache={},
                    is_converged=(lambda _messages: is_converged(completed[-1])) if is_converged is not None else (lambda _messages: False),
                )
            except BaseException:
                raise
            if not result.admitted:
                return AtomicFloodingResult(state, iteration - 1, result.termination, last_sweep)
            if isinstance(self.schedule, MemoryFloodingSchedule):
                self.schedule.commit(completed[-1])
                self.schedule.observe_candidate(
                    origin={
                        "candidate_origin": "last_committed_sweep",
                        "source_iteration": iteration - 1,
                        "status": "diagnostic",
                    },
                    candidate=completed[-1].candidate,
                )
            progress = result.progress
            last_sweep = completed[-1]
            if result.converged:
                return AtomicFloodingResult(state, iteration, None, last_sweep, True)
            terminal = self._wall_boundary("candidate_selection_boundary")
            if terminal is not None:
                return AtomicFloodingResult(state, iteration, terminal, last_sweep)
        terminal = self._wall_boundary("attempt_end")
        return AtomicFloodingResult(state, max_iterations, terminal, last_sweep)


def _budget_tree(execution_controls: Mapping[str, Any] | None) -> BudgetTree:
    """Materialize public scoped WorkVector caps without a scalar conversion."""
    if execution_controls is None:
        return BudgetTree(limits=(), parents={"search": "shot", "attempt": "search"})
    configured = execution_controls.get("work_limits")
    if not isinstance(configured, Mapping):
        raise ValueError("canonical execution controls require scoped work_limits")
    # Public V2/V3 flooding manifests retain their historical cap grammar;
    # V3 schedule terminals carry the expanded vector separately.
    resources = set(WorkVector.zero().as_evidence(structural_event_version=2))
    phase5_caps = execution_controls.get("phase5_work_caps")
    if phase5_caps is not None and (
        not isinstance(phase5_caps, Mapping)
        or set(phase5_caps) != set(WorkVector.zero().as_evidence(structural_event_version=4))
    ):
        raise ValueError("Phase 5 execution controls require a complete work cap vector")
    limits: list[BudgetLimit] = []
    for scope in ("shot", "search", "attempt"):
        values = configured.get(scope)
        if not isinstance(values, Mapping) or set(values) != resources:
            raise ValueError("canonical scoped work limits must exactly match WorkVector resources")
        for resource, limit in values.items():
            limits.append(BudgetLimit(scope, resource, limit))
    if phase5_caps is not None:
        for resource, limit in phase5_caps.items():
            if resource not in resources:
                limits.append(BudgetLimit("attempt", resource, limit))
    return BudgetTree(limits=limits, parents={"search": "shot", "attempt": "search"})


def _public_trace_sink(execution_controls: Mapping[str, Any] | None, ledger_path: Path) -> TraceSink | None:
    """Materialize the manifest-declared observer inside its output root."""
    declared = None if execution_controls is None else execution_controls.get("trace_plan")
    if not isinstance(declared, Mapping) or declared.get("level") == "off":
        return None
    try:
        plan = TracePlan(
            root=ledger_path.parent, level=declared["level"], relative_dir=declared["relative_dir"],
            max_records=declared["max_records"], max_bytes=declared["max_bytes"], label=declared["label"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("canonical execution controls contain an invalid trace plan") from error
    return TraceSink(plan)


def _memory_execution_context(execution_context: Mapping[str, str] | None, *, identity: str, shot_id: int) -> dict[str, str]:
    supplied = execution_context
    if isinstance(supplied, Mapping):
        values = dict(supplied)
        if set(values) == {"configuration_identity", "decoder_identity"} and all(
            isinstance(value, str) and value for value in values.values()
        ):
            return values
        raise ValueError("public memory execution context is incomplete")
    # Direct kernel fixtures have no manifest-level public context.  Keep a
    # deterministic fallback while public runner calls always use the branch
    # above, independently of optional tracing.
    return {
        "configuration_identity": f"memory:{identity}",
        "decoder_identity": f"memory-decoder:{identity}:shot:{shot_id}",
    }


def _termination_evidence(termination: BudgetTermination) -> dict[str, Any]:
    return {
        "binding_scope": termination.binding_scope,
        "resource": termination.resource,
        "configured_limit": termination.configured_limit,
        "consumed_amount": termination.consumed_amount,
        "reason": termination.reason,
    }


def _identity(manifest: CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5 | CanonicalManifestV6, observation: DecoderObservation) -> str:
    payload = {"manifest": manifest.model_dump(mode="json"), "check_type": observation.check_type,
               "syndrome": np.asarray(observation.syndrome, dtype=np.uint8).tolist()}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _attempt_lineage_id(working: WorkingProblem, ordinal: int) -> LineageId:
    """Identify an engine attempt independently of retry timing or append order."""
    return stable_lineage_id(
        "attempt", {"working": working.lineage_id, "ordinal": ordinal},
    )


def _candidate_lineage_id(
    working: WorkingProblem, attempt_id: LineageId, candidate: np.ndarray,
) -> LineageId:
    return stable_lineage_id(
        "candidate",
        {
            "working": working.lineage_id,
            "attempt": attempt_id.value,
            "candidate": candidate.tolist(),
        },
    )


def _require_current_candidate(
    candidate: OriginalSpaceCandidate,
    *,
    working: WorkingProblem,
    attempt_id: LineageId,
) -> OriginalSpaceCandidate:
    """Reject selector output that is detached from the current engine lineage."""
    if candidate.working is not working:
        raise ValueError("selected candidate is detached from the current working problem")
    expected_id = _candidate_lineage_id(working, attempt_id, candidate.candidate)
    if candidate.lineage_id != expected_id.value:
        raise ValueError("selected candidate is detached from the current attempt lineage")
    return candidate


def _existing(path: Path, run_id: str, shot_id: int, identity: str) -> CanonicalExecutionResult | None:
    if not path.exists():
        return None
    for row in reconcile(path):
        if row["run_id"] == run_id and row["shot_id"] == shot_id:
            if row.get("canonical_identity") != identity:
                raise CanonicalConflictError("conflicting canonical content for run/shot identity")
            outcome = row.get("outcome")
            evaluation = evaluator.Evaluation(outcome, row.get("logical_action_agrees")) if outcome else None
            candidate = row.get("candidate")
            return CanonicalExecutionResult(run_id, shot_id, row["termination"], evaluation,
                                            None if candidate is None else np.asarray(candidate, dtype=np.uint8))
    return None


def _layered_schedule_for_manifest(
    manifest: CanonicalManifestV3, edge_table: EdgeTable, kernel: BinarySpaKernel,
) -> LayeredSchedule:
    """Instantiate the closed layered factory only after manifest preflight."""
    policy = manifest.policies.schedule
    if policy.kind != "layered" or policy.partitions is None or policy.provenance is None:
        raise ValueError("layered factory requires a validated layered schedule policy")
    return LayeredSchedule(
        edge_table,
        kernel=kernel,
        partitions=policy.partitions,
        provenance=policy.provenance,
        construction_rule=policy.construction_rule,
    )


def _local_schedule_for_manifest(
    manifest: CanonicalManifestV3, edge_table: EdgeTable, kernel: BinarySpaKernel,
    *, attempt_identity: str,
) -> tuple[Any, RandomizedTraversalPlan | None]:
    """Build the validated V3 schedule named in the manifest."""
    policy = manifest.policies.schedule
    if policy.kind == "layered":
        return _layered_schedule_for_manifest(manifest, edge_table, kernel), None
    if policy.kind == "check_node_serial":
        return CheckNodeSerialSchedule(edge_table, kernel=kernel), None
    if policy.kind == "variable_node_serial":
        return VariableNodeSerialSchedule(edge_table, kernel=kernel), None
    if policy.kind == "residual":
        from .residual import SyndromeResidualSchedule
        return SyndromeResidualSchedule(edge_table, kernel=kernel), None
    if policy.kind == "group_shuffled":
        assert policy.root_identity is not None and policy.source_id == "hsu-ndgsbp-2012-v1"
        return HsuGroupSchedule(edge_table, kernel=kernel, root_identity=policy.root_identity, attempt_identity=attempt_identity), None
    if policy.kind == "randomized":
        if policy.base_schedule != "layered":
            raise ValueError("public randomized V3 admission currently requires the declared layered base schedule")
        if policy.partitions is None or policy.provenance is None:
            raise ValueError("randomized layered admission requires explicit validated partitions and provenance")
        base = LayeredSchedule(
            edge_table, kernel=kernel, partitions=policy.partitions,
            provenance=policy.provenance, construction_rule=policy.construction_rule,
        )
        assert policy.refresh_scope is not None and policy.root_identity is not None
        return base, RandomizedTraversalPlan(
            base, refresh_scope=policy.refresh_scope, root_identity=policy.root_identity,
        )
    raise ValueError(f"unsupported local schedule {policy.kind!r}")


def _local_schedule_metadata(schedule_kind: str, schedule: Any, randomized: RandomizedTraversalPlan | None = None, randomized_state: Any | None = None) -> tuple[str, str, int, str, dict[str, object]]:
    """Keep terminal facts schedule-qualified instead of treating local work as flooding."""
    if schedule_kind == "residual":
        return (
            "residual", "one_residual_selected_c2v_commit", schedule.edge_table.edge_count,
            schedule.stopping_adaptation,
            {
                "schedule": "residual", "atomic_unit": "one_residual_selected_c2v_commit",
                "source_iteration": schedule.source_iteration, "tie_rule": schedule.tie_rule,
                "policy_name": schedule.policy_name, "mutable_state_lifetime": "attempt",
            },
        )
    evidence = dict(schedule.evidence())
    atomic_unit = str(evidence.get("atomic_unit", "one_layer"))
    if randomized is not None:
        if randomized_state is None:
            raise ValueError("randomized schedule evidence requires its immutable attempt state")
        evidence["randomized_traversal"] = randomized.evidence(randomized_state)
    return (
        schedule_kind, atomic_unit, int(schedule.unit_count),
        str(evidence["stopping_adaptation"]), evidence,
    )


def run_canonical_shot(manifest: CanonicalManifestV2 | CanonicalManifestV3 | dict[str, object] | str, *, code: CssCode,
                       observation: DecoderObservation, hidden_truth: HiddenTruth, shot_id: int,
                       ledger_path: str | Path, evaluate: Callable[..., evaluator.Evaluation] = evaluator.evaluate_candidate,
                       policy: Callable[[OriginalProblem, WorkingProblem, tuple[OriginalSpaceCandidate, ...]], Sequence[OriginalSpaceCandidate]] | None = None) -> CanonicalExecutionResult:
    """Run decoder-visible work first; only this outer function receives hidden truth."""
    parsed = parse_canonical_manifest(manifest)
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("canonical tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    resolved = validate_composition(parsed.policies)
    if isinstance(parsed, (CanonicalManifestV4, CanonicalManifestV5, CanonicalManifestV6)):
        raise ValueError("memory, Relay, and interventions require run_canonical_structural_shot")
    runtime = PolicyRuntime(resolved)
    runtime.traverse_lifecycle()
    identity = _identity(parsed, observation)
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
    path = Path(ledger_path)
    existing = _existing(path, parsed.run_id, shot_id, identity)
    if existing is not None:
        return existing
    for attempt_ordinal in range(30):
        try:
            with LedgerWriter(path) as ledger:
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=identity,
                             canonical_identity=identity, decoder_config=parsed.model_dump(mode="json"))
                try:
                    kernel_result = _kernel_for_manifest(parsed).run(validated.hz, observation.syndrome,
                                                          error_rate=parsed.error_rate, max_iterations=parsed.max_iterations)
                except NumericalFailure as error:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                    termination="numerical_failure", numerical_failure=str(error),
                                    selection_status="unavailable_due_to_numerical_failure", outcome=None)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "numerical_failure", None, None)
                frozen_candidate = np.array(kernel_result.candidate, dtype=np.uint8, copy=True)
                frozen_candidate.setflags(write=False)
                attempt_id = _attempt_lineage_id(working, attempt_ordinal)
                candidate_id = _candidate_lineage_id(working, attempt_id, frozen_candidate)
                candidates = (OriginalSpaceCandidate(candidate_id.value, working, frozen_candidate, 0),)
                eligible = tuple(policy(original, working, candidates)) if policy is not None else candidates
                selected = select_stable_candidate(eligible)
                if selected is None:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                    termination="no_eligible_candidate", selection_status="no_eligible_candidate",
                                    outcome=None, candidate=None, original_lineage_id=original_id.value,
                                    working_lineage_id=working_id.value)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "no_eligible_candidate", None, None)
                selected = _require_current_candidate(
                    selected, working=working, attempt_id=attempt_id,
                )
                frozen_candidate = selected.candidate
                evaluation_result = evaluate(validated, true_x=hidden_truth.x, true_z=hidden_truth.z,
                                             candidate_x=frozen_candidate)
                ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                termination="completed", candidate=frozen_candidate.tolist(),
                                iterations=kernel_result.iterations, converged=kernel_result.converged,
                                selection_status="frozen_decoder_visible_candidate", outcome=evaluation_result.outcome,
                                logical_action_agrees=evaluation_result.logical_action_agrees,
                                original_lineage_id=original_id.value, working_lineage_id=working_id.value,
                                candidate_lineage_id=selected.lineage_id)
                return CanonicalExecutionResult(parsed.run_id, shot_id, "completed", evaluation_result, frozen_candidate)
        except ShotOwnershipError:
            time.sleep(0.01)
            existing = _existing(path, parsed.run_id, shot_id, identity)
            if existing is not None:
                return existing
    raise ShotOwnershipError("canonical shot remained owned beyond bounded retry window")


def _existing_structural(
    path: Path, run_id: str, shot_id: int, identity: str,
    verification_context: PublicShotContext | None = None,
) -> CanonicalExecutionResult | None:
    events = read_canonical_events(path)
    matching = [
        event for event in events
        if event["run_id"] == run_id and event["shot_id"] == shot_id
    ]
    if not matching:
        return None
    if verification_context is not None:
        try:
            event = validate_canonical_shot(events, verification_context, trace_root=path.parent)
        except ValueError as error:
            raise CanonicalConflictError(
                f"conflicting canonical content for run/shot identity: {error}"
            ) from error
    else:
        terminals = [event for event in matching if event["kind"] == "termination"]
        if len(terminals) != 1:
            raise CanonicalConflictError("canonical shot has ambiguous terminal evidence")
        event = terminals[0]
        if event["data"].get("canonical_identity") != identity:
            raise CanonicalConflictError("conflicting canonical content for run/shot identity")
    data = event["data"]
    if event["ledger_version"] == 5:
        if data["identity"].get("execution_identity") != identity:
            raise CanonicalConflictError("conflicting Phase 5 execution identity")
        data = data["payload"]
    outcome = data.get("outcome")
    evaluation = evaluator.Evaluation(outcome, data.get("logical_action_agrees")) if outcome else None
    candidate = data.get("candidate")
    return CanonicalExecutionResult(run_id, shot_id, event["termination"], evaluation,
                                    None if candidate is None else np.asarray(candidate, dtype=np.uint8))


def _run_relay_structural_shot(
    parsed: CanonicalManifestV4, *, code: CssCode, observation: DecoderObservation,
    hidden_truth: HiddenTruth, shot_id: int, ledger_path: str | Path,
    sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None,
    verification_context: PublicShotContext | None,
    evaluate: Callable[..., evaluator.Evaluation],
) -> CanonicalExecutionResult:
    """Execute the V4 Relay topology while keeping hidden truth outside the controller."""
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("canonical Relay tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    resolved = validate_composition(parsed.policies)
    PolicyRuntime(resolved).traverse_lifecycle()
    identity = verification_context.execution_identity if verification_context is not None else _identity(parsed, observation)
    path = Path(ledger_path)
    existing = _existing_structural(path, parsed.run_id, shot_id, identity, verification_context)
    if existing is not None:
        return existing
    budgets = _budget_tree(execution_controls)
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
    edge_table = EdgeTable.from_check_matrix(validated.hz)
    controller = RelayController(
        memory_bindings=parsed.memory_bindings, numerical_profile=parsed.numerical_profile,
        memory_tuning=parsed.relay.memory_tuning,
    )

    for attempt_ordinal in range(30):
        try:
            with CanonicalEventWriter(path) as ledger:
                common = {
                    **dict(context), "canonical_identity": identity,
                    "composition_identity": resolved.semantic_identity,
                    "schema_version": 4,
                    "relay_topology": "sequential_posterior_only",
                    "relay_preset_name": parsed.relay.preset_name,
                    "relay_procedure": parsed.relay.procedure,
                    "relay_fidelity_status": parsed.relay.fidelity_status,
                    "relay_numerical_profile": parsed.relay.numerical_profile,
                    "relay_memory_tuning": None if parsed.relay.memory_tuning is None else parsed.relay.memory_tuning.model_dump(mode="json"),
                    "relay_memory_mode": "legacy_transfer_affine" if parsed.relay.memory_tuning is None else "dynamic_affine_prior_each_source_iteration",
                }
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity, **common)
                attempt_id = _attempt_lineage_id(working, attempt_ordinal)
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="attempt", data={
                    **common, "scope": "attempt", "attempt_lineage_id": attempt_id.value,
                    "total_leg_limit": parsed.relay.total_leg_limit,
                })
                run = controller.run(
                    edge_table=edge_table, check_matrix=validated.hz, syndrome=observation.syndrome,
                    kernel=_kernel_for_manifest(parsed, edge_table), error_rate=parsed.error_rate,
                    legs=parsed.relay.legs, budgets=budgets, scope="attempt", lineage_prefix=attempt_id.value,
                    solution_limit=parsed.relay.solution_limit, transfer=parsed.relay.transfer,
                    sample_seed_identity=sample_seed_identity,
                )
                for transfer in run.transfers:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="relay_transfer", data={
                        **common, **transfer.as_evidence(),
                        "reset": ("c2v", "v2c", "leg_history", "iteration", "convergence", "rng_identity"),
                    })
                work = budgets.summary("attempt")
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work", data={
                    **common, "work_vector": work.as_evidence(structural_event_version=2),
                    # RelayController retains each reserve/commit fact with
                    # its leg ancestry.  Do not ask the ledger to infer it
                    # from an aggregate after the fact.
                    "relay_work_leaves": list(run.work_leaves),
                    "relay_legs": tuple({"index": leg.leg_index, "lineage_id": leg.lineage_id,
                                          "iterations": leg.iterations, "converged": leg.converged,
                                          "score": None if leg.score is None else {
                                              "syndrome_weight": leg.score.syndrome_weight,
                                              "prior_weight": leg.score.prior_weight,
                                          }, "memory": None if leg.memory_application is None else leg.memory_application.as_evidence()}
                                        for leg in run.legs),
                    "relay_stopping_reason": run.stopping_reason,
                })
                if run.termination != "completed" or run.candidate is None:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, termination=run.termination, data={
                        **common, "selection_status": "unavailable_due_to_budget" if run.termination == "budget_exhausted" else "unavailable_due_to_stopping",
                        "outcome": None,
                    })
                    return CanonicalExecutionResult(parsed.run_id, shot_id, run.termination, None, None)
                candidate = np.array(run.candidate, dtype=np.uint8, copy=True)
                candidate.setflags(write=False)
                candidate_id = _candidate_lineage_id(working, attempt_id, candidate)
                selected = select_stable_candidate((OriginalSpaceCandidate(candidate_id.value, working, candidate, 0),))
                assert selected is not None
                selected = _require_current_candidate(selected, working=working, attempt_id=attempt_id)
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="candidate", data={
                    **common, "candidate": selected.candidate.tolist(), "candidate_lineage_id": selected.lineage_id,
                    "selection_score": "stable_minimum_prior_weighted_valid_candidate",
                    "relay_stopping_reason": run.stopping_reason,
                })
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="selection", data={
                    **common, "selection_status": "frozen_decoder_visible_candidate",
                    "candidate_lineage_id": selected.lineage_id,
                })
                # This is the first use of hidden truth; the controller and selection never receive it.
                evaluation_result = evaluate(
                    validated, true_x=hidden_truth.x, true_z=hidden_truth.z, candidate_x=selected.candidate,
                )
                ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, termination="completed", data={
                    **common, "candidate": selected.candidate.tolist(), "outcome": evaluation_result.outcome,
                    "logical_action_agrees": evaluation_result.logical_action_agrees,
                    "selection_status": "frozen_decoder_visible_candidate",
                    "candidate_lineage_id": selected.lineage_id,
                })
                return CanonicalExecutionResult(parsed.run_id, shot_id, "completed", evaluation_result, selected.candidate)
        except ShotOwnershipError:
            time.sleep(0.01)
            existing = _existing_structural(path, parsed.run_id, shot_id, identity, verification_context)
            if existing is not None:
                return existing
        except ValueError as error:
            if "shot_begin is duplicated" in str(error):
                existing = _existing_structural(path, parsed.run_id, shot_id, identity, verification_context)
                if existing is not None:
                    return existing
            raise
    raise ShotOwnershipError("canonical Relay shot remained owned beyond bounded retry window")


def _run_guided_structural_shot(
    parsed: CanonicalManifestV6, *, code: CssCode, observation: DecoderObservation,
    hidden_truth: HiddenTruth, shot_id: int, ledger_path: str | Path,
    sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None,
    verification_context: PublicShotContext | None,
    evaluate: Callable[..., evaluator.Evaluation],
) -> CanonicalExecutionResult:
    """One production BPGD tracer through the original-problem truth boundary."""
    from .guided_decimation import GuidedDecimationController
    from .intervention_session import BpSession

    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("guided tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    resolved = validate_composition(parsed.policies)
    PolicyRuntime(resolved).traverse_lifecycle()
    identity = verification_context.execution_identity if verification_context is not None else _identity(parsed, observation)
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
    session = BpSession(
        EdgeTable.from_check_matrix(original.hz), original.syndrome,
        error_rate=parsed.error_rate, owner_identity=f"{identity}:shot:{shot_id}:attempt:0",
    )
    controller = GuidedDecimationController(parsed.intervention)
    budgets = _budget_tree(execution_controls)
    common = {
        **dict(context), "schema_version": 6, "canonical_identity": identity,
        "composition_identity": resolved.semantic_identity,
        "source_revision": parsed.intervention.source_revision,
        "source_variant": parsed.intervention.variant,
    }
    selected: OriginalSpaceCandidate | None = None
    termination = "round_limit_without_valid_candidate"
    with CanonicalEventWriter(ledger_path) as ledger:
        ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity, **common)
        attempt_id = _attempt_lineage_id(working, 0)
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="attempt", data={
            **common, "attempt_lineage_id": attempt_id.value, "scope": "attempt",
            "max_iterations": parsed.max_iterations,
        })
        for round_index in range(parsed.intervention.round_limit):
            for sweep_index in range(parsed.intervention.sweeps_per_round):
                transition = session.advance(
                    budgets=budgets, leaf_id=f"guided-sweep:{shot_id}:{round_index}:{sweep_index}",
                    bp_call_start=sweep_index == 0,
                )
                if not transition.admitted:
                    termination = transition.termination or "count_budget_exhausted"
                    break
                if session.original_syndrome_valid(original.hz):
                    candidate_id = _candidate_lineage_id(working, attempt_id, session.state.candidate)
                    selected = OriginalSpaceCandidate(candidate_id.value, working, session.state.candidate, 0)
                    termination = "completed"
                    break
            if selected is not None or termination == "count_budget_exhausted":
                break
            before = session.state
            guided = controller.fix_one(session, posterior=before.posterior, budgets=budgets)
            ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="intervention", data={
                **common,
                "action": "finite_prior_bias", "admitted": guided.admitted,
                "termination": guided.termination,
                "target_index": None if guided.proposal is None else guided.proposal.target_index,
                "signed_prior": None if guided.proposal is None else guided.proposal.signed_prior,
                "finite_bias_magnitude": parsed.intervention.finite_bias_magnitude,
                "zero_rule": parsed.intervention.zero_rule,
                "final_round_rule": parsed.intervention.final_round_rule,
                "eligibility_set": list(guided.eligibility_set),
                "state_before": before.digest,
                "state_after": session.state.digest,
                "reservation_leaf": guided.session_transition.leaf_id,
                "original_syndrome_valid": session.original_syndrome_valid(original.hz),
            })
            if not guided.admitted:
                termination = guided.termination or "no_eligible_target"
                break
            # Algorithm 1 returns after the final fixation; no invented BP call.
        work = budgets.summary("attempt")
        if selected is not None:
            ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="candidate", data={
                **common, "candidate_lineage_id": selected.lineage_id,
                "candidate": selected.candidate.tolist(), "original_syndrome_valid": True,
            })
            ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="selection", data={
                **common, "candidate_lineage_id": selected.lineage_id,
                "selection_status": "frozen_decoder_visible_candidate",
            })
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work", data={
            **common, "work_vector": work.as_evidence(structural_event_version=2),
            "leaf_ids": [leaf_id for leaf_id, _, _ in budgets.leaf_events()],
        })
        # Truth is first consulted after the candidate has passed original checks
        # and its decoder-visible selection has been written.
        assessment = None if selected is None else evaluate(
            validated, true_x=hidden_truth.x, true_z=hidden_truth.z, candidate_x=selected.candidate,
        )
        ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, termination=termination, data={
            **common, "candidate": None if selected is None else selected.candidate.tolist(),
            "diagnostic_candidate": session.state.candidate.tolist(),
            "original_syndrome_valid": session.original_syndrome_valid(original.hz),
            "outcome": None if assessment is None else assessment.outcome,
            "logical_action_agrees": None if assessment is None else assessment.logical_action_agrees,
            "selection_status": "no_valid_candidate" if selected is None else "frozen_decoder_visible_candidate",
            "work_vector": work.as_evidence(structural_event_version=2),
        })
    return CanonicalExecutionResult(parsed.run_id, shot_id, termination, assessment, None if selected is None else selected.candidate)


def _run_phase5_structural_shot(
    parsed: CanonicalManifestV6 | CanonicalManifestV7, *, code: CssCode, observation: DecoderObservation,
    hidden_truth: HiddenTruth, shot_id: int, ledger_path: str | Path,
    sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None,
    verification_context: PublicShotContext | None,
    evaluate: Callable[..., evaluator.Evaluation],
) -> CanonicalExecutionResult:
    """Run one source-qualified controller behind the sealed public shot boundary."""
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("Phase 5 requires a nonnegative Z-check shot")
    spec = parsed.intervention
    if not isinstance(spec, Phase5InterventionContract):
        raise ValueError("Phase 5 public execution requires the complete intervention contract")
    validated = code.validate()
    identity = verification_context.execution_identity if verification_context is not None else _identity(parsed, observation)
    path = Path(ledger_path)
    existing = _existing_structural(path, parsed.run_id, shot_id, identity, verification_context)
    if existing is not None:
        return existing
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    identity_data = {
        "execution_identity": identity,
        "manifest_sha256": context.get("manifest_sha256"),
        "artifact_raw_sha256": context.get("artifact_raw_sha256"),
        "artifact_semantic_sha256": context.get("artifact_semantic_sha256"),
        "sample_seed_identity": sample_seed_identity,
        "source_variant": spec.variant,
        "source_revision": spec.source_revision,
        "qualification": spec.qualification,
        "native_availability": spec.native_availability,
        "intervention_kind": spec.kind,
    }
    damping_gamma = None
    if isinstance(parsed, CanonicalManifestV7):
        binding = parsed.memory.bindings[0]
        damping_gamma = binding.parameters["gamma"]
        identity_data["memory_binding"] = binding.binding_id
        identity_data["damping_gamma"] = damping_gamma
        identity_data["memory_source_status"] = binding.source_status
    for _ in range(30):
        try:
            with CanonicalEventWriter(path, structural_event_version=5) as ledger:
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity,
                             schema_version=5, compact_schema_version=parsed.schema_version, identity=identity_data,
                             payload={"original_lineage_id": original_id.value, "syndrome": [int(bit) for bit in original.syndrome]})
                budgets = _budget_tree(execution_controls)
                cap = None if execution_controls is None else execution_controls.get("phase5_max_runtime_seconds")
                wall_clock = None if cap is None else WallClockLimit(int(cap * 1_000_000_000), clock=time.monotonic_ns)
                if wall_clock is not None:
                    wall_clock.check("attempt_start", scope="attempt")
                outcome = execute_phase5_controller(
                    spec, original, error_rate=parsed.error_rate, budgets=budgets,
                    max_iterations=parsed.max_iterations, owner_identity=identity,
                    wall_clock=wall_clock,
                    damping_gamma=damping_gamma,
                )
                outcome = finalize_phase5_deadline(outcome, wall_clock)
                candidate = None if outcome.candidate is None else np.asarray(outcome.candidate, dtype=np.uint8)
                if candidate is not None and (candidate.shape != (validated.hz.shape[1],)
                                              or not np.array_equal((validated.hz @ candidate) % 2, observation.syndrome)):
                    raise ValueError("Phase 5 controller selected an invalid original-space candidate")
                assessment = None if candidate is None or outcome.termination == "wall_clock_deadline" else evaluate(
                    validated, true_x=hidden_truth.x, true_z=hidden_truth.z, candidate_x=candidate,
                )
                terminal = {
                    "candidate": None if candidate is None else candidate.tolist(),
                    "selected_origin": outcome.selected_origin,
                    "qualification": outcome.qualification,
                    "selection_status": "no_valid_candidate" if candidate is None else "frozen_original_valid_candidate",
                    "outcome": None if assessment is None else assessment.outcome,
                    "logical_action_agrees": None if assessment is None else assessment.logical_action_agrees,
                    "work_vector": outcome.work.as_evidence(structural_event_version=4),
                    "termination": outcome.termination,
                }
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="intervention",
                             data={"identity": identity_data, "payload": outcome.header})
                for branch in outcome.branches:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="branch",
                                 data={"identity": identity_data, "payload": branch})
                for kind, payload in phase5_attempt_events(spec, outcome):
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind=kind,
                                 data={"identity": identity_data, "payload": payload})
                if candidate is not None:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="candidate",
                                 data={"identity": identity_data, "payload": {"bits": candidate.tolist(), "origin": outcome.selected_origin}})
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="original_check",
                                 data={"identity": identity_data, "payload": {"candidate": candidate.tolist(), "valid": True}})
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="selection",
                             data={"identity": identity_data, "payload": {"candidate": terminal["candidate"], "origin": outcome.selected_origin,
                                                                        "status": terminal["selection_status"]}})
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work",
                             data={"identity": identity_data, "payload": phase5_work_evidence(outcome)})
                if assessment is not None:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="evaluation",
                                 data={"identity": identity_data, "payload": {"outcome": assessment.outcome,
                                                                            "logical_action_agrees": assessment.logical_action_agrees}})
                if wall_clock is not None and wall_clock.first_termination is not None:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="runtime",
                                 data={"identity": identity_data, "payload": {
                                     "deadline": asdict(wall_clock.first_termination),
                                     "check_count": wall_clock.first_termination_check,
                                 }})
                ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, termination=outcome.termination,
                                data={"identity": identity_data, "payload": terminal})
            return CanonicalExecutionResult(parsed.run_id, shot_id, outcome.termination, assessment, candidate)
        except ShotOwnershipError:
            time.sleep(0.01)
            existing = _existing_structural(path, parsed.run_id, shot_id, identity, verification_context)
            if existing is not None:
                return existing
    raise ShotOwnershipError("Phase 5 shot remained owned beyond bounded retry window")


def run_canonical_structural_shot(
    manifest: CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5 | CanonicalManifestV6 | dict[str, object] | str, *, code: CssCode,
    observation: DecoderObservation, hidden_truth: HiddenTruth, shot_id: int,
    ledger_path: str | Path, sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None = None,
    verification_context: PublicShotContext | None = None,
    memory_execution_context: Mapping[str, str] | None = None,
    evaluate: Callable[..., evaluator.Evaluation] = evaluator.evaluate_candidate,
) -> CanonicalExecutionResult:
    """Run the kernel with v2 structural evidence and an outer truth boundary."""
    parsed = parse_canonical_manifest(manifest)
    if isinstance(parsed, CanonicalManifestV6):
        if isinstance(parsed.intervention, Phase5InterventionContract):
            return _run_phase5_structural_shot(
                parsed, code=code, observation=observation, hidden_truth=hidden_truth,
                shot_id=shot_id, ledger_path=ledger_path, sample_seed_identity=sample_seed_identity,
                context=context, execution_controls=execution_controls,
                verification_context=verification_context, evaluate=evaluate,
            )
        return _run_guided_structural_shot(
            parsed, code=code, observation=observation, hidden_truth=hidden_truth,
            shot_id=shot_id, ledger_path=ledger_path, sample_seed_identity=sample_seed_identity,
            context=context, execution_controls=execution_controls,
            verification_context=verification_context, evaluate=evaluate,
        )
    if isinstance(parsed, CanonicalManifestV4):
        return _run_relay_structural_shot(
            parsed, code=code, observation=observation, hidden_truth=hidden_truth, shot_id=shot_id,
            ledger_path=ledger_path, sample_seed_identity=sample_seed_identity, context=context,
            execution_controls=execution_controls, verification_context=verification_context, evaluate=evaluate,
        )
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("canonical tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    resolved = validate_composition(parsed.policies)
    if isinstance(parsed, CanonicalManifestV5):
        validate_single_attempt_memory(
            parsed.memory, schedule=parsed.policies.schedule.kind,
            update=parsed.policies.update, max_iterations=parsed.max_iterations,
        )
    PolicyRuntime(resolved).traverse_lifecycle()
    budgets = _budget_tree(execution_controls)
    identity = verification_context.execution_identity if verification_context is not None else _identity(parsed, observation)
    path = Path(ledger_path)
    existing = _existing_structural(
        path, parsed.run_id, shot_id, identity, verification_context,
    )
    if existing is not None:
        return existing
    trace_sink = _public_trace_sink(execution_controls, path)
    memory_context = _memory_execution_context(memory_execution_context, identity=identity, shot_id=shot_id)
    trace_context = {
        **memory_context,
        "run_id": parsed.run_id,
        "shot_id": str(shot_id),
    }
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
    local_progress: ScheduleProgress | None = None
    local_schedule: Any | None = None
    memory_schedule: MemoryFloodingSchedule | None = None
    local_memory: LocalMemoryExecution | None = None
    randomized_plan: RandomizedTraversalPlan | None = None
    local_random_state: Any | None = None
    local_random_order: tuple[int, ...] | None = None
    setup_before_profile_ns = 0
    setup_inside_profile_ns = 0
    if parsed.policies.schedule.kind != "flooding":
        if not isinstance(parsed, (CanonicalManifestV3, CanonicalManifestV5)):
            raise ValueError("local public execution requires the version-three kernel contract")
        setup_started_ns = time.perf_counter_ns()
        local_table = EdgeTable.from_check_matrix(validated.hz)
        local_schedule, randomized_plan = _local_schedule_for_manifest(
            parsed, local_table, _kernel_for_manifest(parsed, local_table),
            attempt_identity=f"{identity}:attempt:0",
        )
        local_progress = ScheduleProgress(iteration=0, local_steps=0, cursor=(0,))
        if randomized_plan is not None:
            local_random_state = randomized_plan.initial_state(
                configuration_identity=identity, attempt_identity=f"{identity}:attempt:0",
            )
        setup_before_profile_ns = time.perf_counter_ns() - setup_started_ns
    for attempt_ordinal in range(30):
        try:
            with CanonicalEventWriter(path) as ledger:
                policy_effects = None if execution_controls is None else execution_controls.get("policy_effects")
                common = {
                    **dict(context), "canonical_identity": identity,
                    "composition_identity": resolved.semantic_identity,
                    "policy_effects": policy_effects,
                }
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity, **common)
                attempt_id = _attempt_lineage_id(working, attempt_ordinal)
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="attempt", data={**common, "scope": "attempt", "attempt_lineage_id": attempt_id.value, "max_iterations": parsed.max_iterations})
                profile_evidence: dict[str, object] | None = None
                trace_link_emitted = False

                def emit_trace_link(termination: str, data: Mapping[str, Any]) -> None:
                    """Link only terminal, committed-state observations to the ledger."""
                    nonlocal trace_link_emitted
                    if trace_sink is None or trace_link_emitted:
                        return
                    schedule = memory_schedule if memory_schedule is not None else local_memory
                    reason = "attempt_not_admitted" if schedule is None else "no_committed_decoder_state"
                    if schedule is not None:
                        try:
                            candidate = data.get("candidate", data.get("diagnostic_candidate"))
                            if candidate is not None:
                                schedule.observe_candidate(
                                    origin={
                                        "termination": termination,
                                        "selection_status": data.get("selection_status"),
                                        "candidate_lineage_id": data.get("candidate_lineage_id"),
                                    },
                                    candidate=np.asarray(candidate, dtype=np.uint8),
                                )
                            result = schedule.trace_result()
                            assert result is not None
                            link = result.ledger_link()
                            if link is not None:
                                ledger.event(
                                    run_id=parsed.run_id, shot_id=shot_id, kind="trace_link",
                                    data={**common, "trace_kind": "ordinary_memory", "status": "linked"}, sidecar=link,
                                )
                                trace_link_emitted = True
                                return
                        except (OSError, ValueError) as error:
                            # Sidecar I/O is observational.  A bounded trace
                            # failure must not erase already committed decoder
                            # work or turn trace configuration into a control.
                            reason = f"sidecar_finalization_unavailable:{type(error).__name__}"
                    ledger.event(
                        run_id=parsed.run_id, shot_id=shot_id, kind="trace_link",
                        data={**common, "trace_kind": "ordinary_memory", "status": "unavailable", "reason": reason},
                    )
                    trace_link_emitted = True

                def terminal_with_work(termination: str, **data: Any) -> None:
                    is_local = parsed.policies.schedule.kind != "flooding"
                    if isinstance(parsed, CanonicalManifestV5) and termination in {"count_budget_exhausted", "max_iterations"}:
                        # A diagnostic is decoder-visible output from the last
                        # committed sweep. It is not selected as a recovery.
                        data.setdefault("diagnostic_candidate", None)
                        data["diagnostic_candidate_origin"] = (
                            "last_committed_local_unit" if is_local else "last_committed_sweep"
                        ) if data["diagnostic_candidate"] is not None else None
                    work = budgets.summary("attempt")
                    setup_elapsed_ns = setup_before_profile_ns + setup_inside_profile_ns
                    setup_runtime = (
                        Measurement.observed(
                            setup_elapsed_ns, method="time.perf_counter_ns:v1",
                            scope="canonical_setup", unit="ns", precision="1 ns",
                        ) if setup_elapsed_ns else Measurement.unavailable(
                            method="not_measured", scope="canonical_setup", unit="ns", precision="unknown",
                            reason="attempt ended before canonical setup began",
                        )
                    )
                    profiled_wall = None if profile_evidence is None else profile_evidence["runtime"]["wall_time"]["value"]
                    decode_runtime = (
                        Measurement.observed(
                            max(0, int(profiled_wall) - setup_inside_profile_ns),
                            method="time.perf_counter_ns:profile-minus-setup:v1",
                            scope="canonical_decode_attempt", unit="ns", precision="1 ns",
                        ) if profiled_wall is not None else Measurement.unavailable(
                            method="not_measured", scope="canonical_decode_attempt", unit="ns", precision="unknown",
                            reason="attempt ended before the runtime profiler returned",
                        )
                    )
                    if is_local:
                        assert local_progress is not None and local_schedule is not None
                        schedule_name, atomic_unit, unit_count, stopping_adaptation, schedule_evidence = _local_schedule_metadata(
                            parsed.policies.schedule.kind, local_schedule, randomized_plan, local_random_state,
                        )
                        qualified = QualifiedIteration(
                            local_progress.local_steps, schedule=schedule_name, atomic_unit=atomic_unit,
                        )
                        c2v_cap = int(dict(execution_controls or {}).get("work_limits", {}).get("attempt", {}).get("check_to_variable_updates", 0))
                        schedule_terminal = ScheduleTerminalEvidence(
                            schedule=schedule_name,
                            source_iteration=qualified,
                            completed_traversals=qualified.count // unit_count,
                            local_cursor=local_progress.cursor,
                            stopping_adaptation=stopping_adaptation,
                            work=work,
                            setup_runtime=setup_runtime,
                            decode_runtime=decode_runtime,
                            budget_views=(
                                BudgetView.common_c2v_cap(c2v_cap),
                                BudgetView.schedule_iteration_limit(qualified),
                            ),
                        ).as_evidence()
                        work_data = {
                            **common,
                            "qualified_iterations": qualified.as_evidence(),
                            "work_vector": work.as_evidence(structural_event_version=2),
                            "schedule_terminal": schedule_terminal,
                            "schedule_evidence": schedule_evidence,
                        }
                    else:
                        work_data = {
                            **common,
                            "qualified_iterations": {
                                "count": data.get("iterations", 0), "schedule": "flooding",
                                "atomic_unit": "complete_double_buffered_sweep",
                            },
                            "work_vector": work.as_evidence(structural_event_version=2),
                        }
                    emit_trace_link(termination, data)
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work", data=work_data)
                    ledger.terminal(
                        run_id=parsed.run_id, shot_id=shot_id, termination=termination,
                        data={
                            **common, **data, "work_vector": work.as_evidence(structural_event_version=2),
                            "setup_runtime": setup_runtime.as_evidence(),
                            "decode_runtime": decode_runtime.as_evidence(),
                            **({"schedule_terminal": schedule_terminal, "schedule_evidence": schedule_evidence} if is_local else {}),
                            **({"profile": profile_evidence} if profile_evidence is not None else {}),
                            **({"memory_execution": (memory_schedule if memory_schedule is not None else local_memory).evidence()}
                               if memory_schedule is not None or local_memory is not None else {}),
                        },
                    )

                attempt_reservation = budgets.reserve(
                    "attempt", WorkVector(bp_calls=1), leaf_id=f"attempt:{shot_id}:bp-call"
                )
                if attempt_reservation is None:
                    termination = budgets.last_termination
                    assert termination is not None
                    terminal_with_work(
                        termination.reason, budget_termination=_termination_evidence(termination),
                        selection_status="unavailable_due_to_budget", outcome=None,
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, termination.reason, None, None)
                attempt_reservation.commit_once()
                try:
                    def admitted_attempt() -> tuple[np.ndarray | None, int, bool, BudgetTermination | None]:
                        nonlocal local_progress, local_schedule, local_random_state, setup_inside_profile_ns, memory_schedule, local_memory
                        setup_started_ns = time.perf_counter_ns()
                        edge_table = EdgeTable.from_check_matrix(validated.hz)
                        kernel = _kernel_for_manifest(parsed, edge_table)
                        if parsed.policies.schedule.kind != "flooding":
                            assert local_schedule is not None and local_progress is not None
                            messages = np.full(
                                edge_table.edge_count, kernel.prior(parsed.error_rate), dtype=np.float64,
                            )
                            if isinstance(parsed, CanonicalManifestV5):
                                local_memory = LocalMemoryExecution(
                                    edge_table, memory=parsed.memory,
                                    profile=kernel.profile,
                                    execution_context=memory_context,
                                    trace_sink=trace_sink, trace_context=trace_context,
                                )
                                local_memory.initialize(
                                    error_rate=parsed.error_rate, initial_v2c=messages,
                                    initial_beliefs=np.full(edge_table.variable_count, kernel.prior(parsed.error_rate), dtype=np.float64),
                                )
                            setup_inside_profile_ns = time.perf_counter_ns() - setup_started_ns
                            candidate: np.ndarray | None = None
                            local_prior_llrs: np.ndarray | None = None
                            executor = CanonicalLocalStepExecutor(budgets, scope="attempt")
                            if parsed.policies.schedule.kind == "residual":
                                from .residual import ResidualSetupBudgetDenied
                                c2v = np.zeros(edge_table.edge_count, dtype=np.float64)
                                try:
                                    cache = local_schedule.initialize(messages, c2v, observation.syndrome, error_rate=parsed.error_rate, budgets=budgets)
                                except ResidualSetupBudgetDenied as error:
                                    return None, 0, False, error.termination
                                # A residual source iteration is a complete traversal
                                # of the E selected C2V commits, not one local commit.
                                while local_progress.iteration < parsed.max_iterations:
                                    proposal = local_schedule.propose_local_step(messages, c2v, cache, observation.syndrome, error_rate=parsed.error_rate)
                                    step = local_schedule.execute_local_step(executor, proposal, v2c=messages, c2v=c2v, cache=cache, progress=local_progress, is_converged=lambda proposed: bool(np.array_equal((validated.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2, observation.syndrome)))
                                    local_progress, cache, c2v = step.progress, step.cache, step.c2v
                                    if not step.admitted:
                                        return candidate, local_progress.local_steps, False, step.termination
                                    candidate = step.candidate
                                    if step.converged:
                                        return candidate, local_progress.local_steps, True, None
                                return candidate, local_progress.local_steps, False, None
                            # Layered/node-serial and randomized traversals use
                            # max_iterations as complete source traversals.  The
                            # Hsu group schedule predates this contract and pins
                            # its bound in declared local groups.
                            def local_iteration_remaining() -> bool:
                                if parsed.policies.schedule.kind in {
                                    "layered", "check_node_serial", "variable_node_serial", "randomized",
                                }:
                                    return local_progress.iteration < parsed.max_iterations
                                return local_progress.local_steps < parsed.max_iterations

                            while local_iteration_remaining():
                                progress_for_step = local_progress
                                if local_memory is not None and local_progress.cursor == (0,):
                                    local_prior_llrs = local_memory.begin_source_iteration()
                                if parsed.policies.schedule.kind == "group_shuffled" and local_progress.cursor == (0,):
                                    refreshed, order_termination = local_schedule.refresh_order(local_progress, budgets=budgets)
                                    if not refreshed:
                                        return candidate, local_progress.local_steps, False, order_termination
                                if randomized_plan is not None:
                                    assert local_random_state is not None
                                    # An order belongs to its declared boundary.  Reusing it
                                    # within a traversal makes every local unit part of the
                                    # same realized permutation.
                                    if local_progress.cursor == (0,):
                                        boundary: str | None = None
                                        if randomized_plan.refresh_scope == "sweep":
                                            boundary = "sweep"
                                        elif local_progress.iteration == 0:
                                            boundary = randomized_plan.refresh_scope
                                        if boundary is not None:
                                            refresh = randomized_plan.refresh(
                                                local_random_state, boundary=boundary,
                                                budgets=budgets, budget_scope="attempt",
                                            )
                                            if not refresh.admitted:
                                                return candidate, local_progress.local_steps, False, refresh.termination
                                            local_random_state = refresh.state
                                            local_random_order = refresh.order
                                    if local_random_order is None:
                                        raise RuntimeError("randomized traversal has no admitted order")
                                    logical_index = local_progress.cursor[0]
                                    progress_for_step = ScheduleProgress(
                                        local_progress.iteration, local_progress.local_steps,
                                        (local_random_order[logical_index],), local_progress.rng_state,
                                    )
                                if local_memory is not None:
                                    local_memory.begin_step()
                                try:
                                    step = local_schedule.execute_local_step(
                                        executor, messages, observation.syndrome,
                                        error_rate=parsed.error_rate, progress=progress_for_step,
                                        is_converged=lambda proposed: bool(np.array_equal(
                                            (validated.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2,
                                            observation.syndrome,
                                        )),
                                        **({
                                            "prior_llrs": local_prior_llrs,
                                            "transform_beliefs": local_memory.transform_beliefs,
                                            "transform_v2c": local_memory.transform_v2c,
                                        } if local_memory is not None else {}),
                                    )
                                except BaseException:
                                    if local_memory is not None:
                                        local_memory.discard()
                                        local_memory.abort_source_iteration()
                                    raise
                                if randomized_plan is not None:
                                    local_progress = ScheduleProgress(local_progress.iteration, step.progress.local_steps, (local_progress.cursor[0] + 1,), local_progress.rng_state)
                                else:
                                    local_progress = step.progress
                                if not step.admitted:
                                    if local_memory is not None:
                                        local_memory.discard()
                                        local_memory.abort_source_iteration()
                                    return candidate, local_progress.local_steps, False, step.termination
                                if local_memory is not None:
                                    local_memory.commit(local_memory.proposal())
                                complete_source_iteration = local_progress.cursor == (local_schedule.unit_count,)
                                if local_memory is not None and complete_source_iteration:
                                    local_memory.complete_source_iteration()
                                candidate = step.candidate
                                if step.candidate is not None and np.array_equal(
                                    (validated.hz.astype(np.int64) @ step.candidate.astype(np.int64)) % 2,
                                    observation.syndrome,
                                ):
                                    if local_memory is not None and not complete_source_iteration:
                                        local_memory.abort_source_iteration()
                                    return candidate, local_progress.local_steps, True, None
                                if complete_source_iteration:
                                    local_progress = ScheduleProgress(
                                        iteration=local_progress.iteration + 1,
                                        local_steps=local_progress.local_steps,
                                        cursor=(0,),
                                        rng_state=local_progress.rng_state,
                                    )
                                    local_prior_llrs = None
                            if local_memory is not None:
                                local_memory.abort_source_iteration()
                            return candidate, local_progress.local_steps, False, None
                        if isinstance(parsed, CanonicalManifestV5):
                            memory_schedule = MemoryFloodingSchedule(
                                edge_table, kernel=kernel, memory=parsed.memory,
                                execution_context=memory_context, trace_sink=trace_sink,
                                trace_context=trace_context,
                            )
                            schedule = memory_schedule
                            initialized = schedule.initialize(parsed.error_rate)
                        else:
                            schedule = FloodingSchedule(edge_table, kernel=kernel, profile=kernel.profile)
                            initialized = schedule.initialize(parsed.error_rate) if edge_table.edge_count else None
                        setup_inside_profile_ns = time.perf_counter_ns() - setup_started_ns
                        if edge_table.edge_count == 0:
                            candidate = kernel.candidate_from_beliefs(
                                np.full(validated.n, kernel.prior(parsed.error_rate), dtype=np.float64)
                            )
                            converged = bool(np.array_equal(
                                (validated.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2,
                                observation.syndrome,
                            ))
                            return candidate, 0, converged, None
                        executor = AtomicFloodingExecutor(schedule, budgets, scope="attempt")
                        attempt = executor.run_attempt(
                            initialized, observation.syndrome,
                            error_rate=parsed.error_rate, max_iterations=parsed.max_iterations,
                            is_converged=lambda sweep: bool(np.array_equal(
                                (validated.hz.astype(np.int64) @ sweep.candidate.astype(np.int64)) % 2,
                                observation.syndrome,
                            )),
                        )
                        return (
                            None if attempt.last_sweep is None else attempt.last_sweep.candidate,
                            attempt.iterations,
                            attempt.converged,
                            attempt.termination,
                        )

                    plan_data = {} if execution_controls is None else dict(execution_controls.get("profile_plan", {}))
                    profile_plan = ProfilingPlan(
                        enabled=bool(plan_data.get("enabled", False)),
                        level=plan_data.get("level", "low_overhead"),
                        track_python_allocations=plan_data.get("level") == "representative",
                    )
                    (candidate, iterations, converged, budget_termination), profile = LocalProfiler(profile_plan).measure(admitted_attempt)
                    profile_evidence = profile.as_evidence()
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="runtime", data={**common, "profile": profile_evidence})
                except NumericalFailure as error:
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="missingness", data={**common, "field": "candidate", "reason": "numerical_failure"})
                    committed_iterations = (
                        local_progress.local_steps if local_memory is not None and local_progress is not None
                        else 0 if memory_schedule is None
                        else memory_schedule.evidence()["committed_iterations"]
                    )
                    terminal_with_work(
                        "numerical_failure", numerical_failure=str(error),
                        selection_status="unavailable_due_to_numerical_failure", outcome=None,
                        verification_status="not_independently_reproduced_numerical_failure",
                        **({"iterations": committed_iterations} if isinstance(parsed, CanonicalManifestV5) else {}),
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "numerical_failure", None, None)
                if budget_termination is not None:
                    terminal_with_work(
                        budget_termination.reason, iterations=iterations,
                        budget_termination=_termination_evidence(budget_termination),
                        selection_status="unavailable_due_to_budget", outcome=None,
                        **({"diagnostic_candidate": None if candidate is None else candidate.tolist()} if isinstance(parsed, CanonicalManifestV5) else {}),
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, budget_termination.reason, None, None)
                if candidate is None or not converged:
                    terminal_with_work(
                        "max_iterations", iterations=iterations, converged=False,
                        selection_status="unavailable_due_to_stopping", outcome=None,
                        **({"diagnostic_candidate": None if candidate is None else candidate.tolist()} if isinstance(parsed, CanonicalManifestV5) else {}),
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "max_iterations", None, None)
                candidate = np.array(candidate, dtype=np.uint8, copy=True)
                candidate.setflags(write=False)
                candidate_id = _candidate_lineage_id(working, attempt_id, candidate)
                selected = select_stable_candidate((OriginalSpaceCandidate(candidate_id.value, working, candidate, 0),))
                if selected is None:  # defensive; the identity composition always supplies one candidate.
                    terminal_with_work("no_eligible_candidate", iterations=iterations,
                                       selection_status="no_eligible_candidate", outcome=None)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "no_eligible_candidate", None, None)
                selected = _require_current_candidate(
                    selected, working=working, attempt_id=attempt_id,
                )
                frozen = selected.candidate
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="candidate", data={**common, "attempt_lineage_id": attempt_id.value, "candidate": frozen.tolist(), "candidate_lineage_id": selected.lineage_id})
                ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="selection", data={**common, "selection_status": "frozen_decoder_visible_candidate", "original_lineage_id": original_id.value, "working_lineage_id": working_id.value, "attempt_lineage_id": attempt_id.value, "candidate_lineage_id": selected.lineage_id})
                evaluation_result = evaluate(validated, true_x=hidden_truth.x, true_z=hidden_truth.z, candidate_x=frozen)
                terminal_with_work(
                    "completed", candidate=frozen.tolist(), iterations=iterations, converged=converged,
                    selection_status="frozen_decoder_visible_candidate", outcome=evaluation_result.outcome,
                    logical_action_agrees=evaluation_result.logical_action_agrees,
                    original_lineage_id=original_id.value, working_lineage_id=working_id.value,
                    attempt_lineage_id=attempt_id.value,
                    candidate_lineage_id=selected.lineage_id,
                )
                return CanonicalExecutionResult(parsed.run_id, shot_id, "completed", evaluation_result, frozen)
        except ShotOwnershipError:
            time.sleep(0.01)
            existing = _existing_structural(
                path, parsed.run_id, shot_id, identity, verification_context,
            )
            if existing is not None:
                return existing
    raise ShotOwnershipError("canonical shot remained owned beyond bounded retry window")
