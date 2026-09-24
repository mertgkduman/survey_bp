"""Truth-sealed canonical CSS shot orchestration and durable terminal evidence."""

from __future__ import annotations

from dataclasses import dataclass
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
    Hook,
    PolicyBinding,
    PolicyDecision,
    ResolvedComposition,
    parse_canonical_manifest,
    validate_composition,
)
from .budgets import BudgetLimit, BudgetTermination, BudgetTree, WallClockLimit, WorkVector
from .kernel import BinarySpaKernel
from .profiling import LocalProfiler, ProfilingPlan
from .lineage import LineageEdge, LineageId, stable_lineage_id
from .numerics import NumericalFailure
from .numerics import MIN_SUM_CPU_F64
from .updates import MinSumUpdate
from .problems import OriginalProblem, OriginalSpaceCandidate, WorkingProblem, select_stable_candidate
from .schedules import EdgeTable, FloodingSchedule, FloodingSweep
from .verification import PublicShotContext, validate_canonical_shot


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
        if proposal.proposed_work.candidate_checks < 1:
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


def _kernel_for_manifest(manifest: CanonicalManifestV2 | CanonicalManifestV3) -> BinarySpaKernel:
    """Resolve only the closed update registry; policies never receive hidden truth."""
    update = manifest.policies.update.kind
    if update == "min_sum":
        return BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
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
    resources = set(WorkVector.zero().as_evidence())
    limits: list[BudgetLimit] = []
    for scope in ("shot", "search", "attempt"):
        values = configured.get(scope)
        if not isinstance(values, Mapping) or set(values) != resources:
            raise ValueError("canonical scoped work limits must exactly match WorkVector resources")
        for resource, limit in values.items():
            limits.append(BudgetLimit(scope, resource, limit))
    return BudgetTree(limits=limits, parents={"search": "shot", "attempt": "search"})


def _termination_evidence(termination: BudgetTermination) -> dict[str, Any]:
    return {
        "binding_scope": termination.binding_scope,
        "resource": termination.resource,
        "configured_limit": termination.configured_limit,
        "consumed_amount": termination.consumed_amount,
        "reason": termination.reason,
    }


def _identity(manifest: CanonicalManifestV2 | CanonicalManifestV3, observation: DecoderObservation) -> str:
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
            event = validate_canonical_shot(events, verification_context)
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
    outcome = data.get("outcome")
    evaluation = evaluator.Evaluation(outcome, data.get("logical_action_agrees")) if outcome else None
    candidate = data.get("candidate")
    return CanonicalExecutionResult(run_id, shot_id, event["termination"], evaluation,
                                    None if candidate is None else np.asarray(candidate, dtype=np.uint8))


def run_canonical_structural_shot(
    manifest: CanonicalManifestV2 | CanonicalManifestV3 | dict[str, object] | str, *, code: CssCode,
    observation: DecoderObservation, hidden_truth: HiddenTruth, shot_id: int,
    ledger_path: str | Path, sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None = None,
    verification_context: PublicShotContext | None = None,
    evaluate: Callable[..., evaluator.Evaluation] = evaluator.evaluate_candidate,
) -> CanonicalExecutionResult:
    """Run the kernel with v2 structural evidence and an outer truth boundary."""
    parsed = parse_canonical_manifest(manifest)
    if type(shot_id) is not int or shot_id < 0 or observation.check_type != "Z":
        raise ValueError("canonical tracer accepts a nonnegative Z-check shot")
    validated = code.validate()
    resolved = validate_composition(parsed.policies)
    PolicyRuntime(resolved).traverse_lifecycle()
    budgets = _budget_tree(execution_controls)
    identity = verification_context.execution_identity if verification_context is not None else _identity(parsed, observation)
    path = Path(ledger_path)
    existing = _existing_structural(
        path, parsed.run_id, shot_id, identity, verification_context,
    )
    if existing is not None:
        return existing
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
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

                def terminal_with_work(termination: str, **data: Any) -> None:
                    work = budgets.summary("attempt")
                    work_data = {
                        **common,
                        "qualified_iterations": {
                            "count": data.get("iterations", 0), "schedule": "flooding",
                            "atomic_unit": "complete_double_buffered_sweep",
                        },
                        "work_vector": work.as_evidence(),
                    }
                    ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work", data=work_data)
                    ledger.terminal(
                        run_id=parsed.run_id, shot_id=shot_id, termination=termination,
                        data={
                            **common, **data, "work_vector": work.as_evidence(),
                            **({"profile": profile_evidence} if profile_evidence is not None else {}),
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
                        kernel = _kernel_for_manifest(parsed)
                        edge_table = EdgeTable.from_check_matrix(validated.hz)
                        schedule = FloodingSchedule(edge_table, kernel=kernel, profile=kernel.profile)
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
                            schedule.initialize(parsed.error_rate), observation.syndrome,
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
                    terminal_with_work(
                        "numerical_failure", numerical_failure=str(error),
                        selection_status="unavailable_due_to_numerical_failure", outcome=None,
                        verification_status="not_independently_reproduced_numerical_failure",
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "numerical_failure", None, None)
                if budget_termination is not None:
                    terminal_with_work(
                        budget_termination.reason, iterations=iterations,
                        budget_termination=_termination_evidence(budget_termination),
                        selection_status="unavailable_due_to_budget", outcome=None,
                    )
                    return CanonicalExecutionResult(parsed.run_id, shot_id, budget_termination.reason, None, None)
                if candidate is None or not converged:
                    terminal_with_work(
                        "max_iterations", iterations=iterations, converged=False,
                        selection_status="unavailable_due_to_stopping", outcome=None,
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
