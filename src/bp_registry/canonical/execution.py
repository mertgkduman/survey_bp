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
from ..ledger import LedgerWriter, ShotOwnershipError, reconcile
from ..sampling import DecoderObservation, HiddenTruth
from .contracts import (
    CanonicalManifestV2,
    Hook,
    PolicyBinding,
    PolicyDecision,
    ResolvedComposition,
    parse_canonical_manifest,
    validate_composition,
)
from .budgets import BudgetTermination, BudgetTree, WallClockLimit, WorkVector
from .kernel import BinarySpaKernel
from .lineage import LineageEdge, LineageId, stable_lineage_id
from .numerics import NumericalFailure
from .problems import OriginalProblem, OriginalSpaceCandidate, WorkingProblem, select_stable_candidate
from .schedules import FloodingSchedule, FloodingSweep


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
        self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iterations: int
    ) -> AtomicFloodingResult:
        """Finish in-flight work, then stop only at a named operational boundary."""
        state = np.array(old_v2c, dtype=np.float64, copy=True)
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
            reservation = self.budgets.reserve(self.scope, proposed, leaf_id=f"{self.scope}:flooding:{iteration}")
            if reservation is None:
                return AtomicFloodingResult(state, iteration - 1, self.budgets.last_termination, last_sweep)
            try:
                sweep = self.schedule.sweep(state, syndrome, error_rate=error_rate)
                # Only a complete finite sweep becomes visible before its work commits.
                state = np.array(sweep.new_v2c, dtype=np.float64, copy=True)
                state.setflags(write=False)
                reservation.commit_once()
            except BaseException:
                if reservation.active:
                    reservation.rollback()
                raise
            last_sweep = sweep
            terminal = self._wall_boundary("candidate_selection_boundary")
            if terminal is not None:
                return AtomicFloodingResult(state, iteration, terminal, last_sweep)
        terminal = self._wall_boundary("attempt_end")
        return AtomicFloodingResult(state, max_iterations, terminal, last_sweep)


def _identity(manifest: CanonicalManifestV2, observation: DecoderObservation) -> str:
    payload = {"manifest": manifest.model_dump(mode="json"), "check_type": observation.check_type,
               "syndrome": np.asarray(observation.syndrome, dtype=np.uint8).tolist()}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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


def run_canonical_shot(manifest: CanonicalManifestV2 | dict[str, object] | str, *, code: CssCode,
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
    for attempt in range(30):
        try:
            with LedgerWriter(path) as ledger:
                ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=identity,
                             canonical_identity=identity, decoder_config=parsed.model_dump(mode="json"))
                try:
                    kernel_result = BinarySpaKernel().run(validated.hz, observation.syndrome,
                                                          error_rate=parsed.error_rate, max_iterations=parsed.max_iterations)
                except NumericalFailure as error:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                    termination="numerical_failure", numerical_failure=str(error),
                                    selection_status="unavailable_due_to_numerical_failure", outcome=None)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "numerical_failure", None, None)
                frozen_candidate = np.array(kernel_result.candidate, dtype=np.uint8, copy=True)
                frozen_candidate.setflags(write=False)
                candidate_id = stable_lineage_id("candidate", {"working": working_id.value, "candidate": frozen_candidate.tolist()})
                candidates = (OriginalSpaceCandidate(candidate_id.value, working, frozen_candidate, 0),)
                eligible = tuple(policy(original, working, candidates)) if policy is not None else candidates
                selected = select_stable_candidate(eligible)
                if selected is None:
                    ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, canonical_identity=identity,
                                    termination="no_eligible_candidate", selection_status="no_eligible_candidate",
                                    outcome=None, candidate=None, original_lineage_id=original_id.value,
                                    working_lineage_id=working_id.value)
                    return CanonicalExecutionResult(parsed.run_id, shot_id, "no_eligible_candidate", None, None)
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
