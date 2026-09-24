"""Public identity and structural reuse checks for canonical CSS evidence.

The ledger's content hashes make records durable, but they do not establish that
the record belongs to the currently preflighted public experiment.  This module
keeps that identity separate from hidden truth and gives both the runner and
CLI one reuse boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np

from .. import evaluator
from .budgets import BudgetLimit, BudgetTree, BudgetView, Measurement, QualifiedIteration, ScheduleTerminalEvidence, WorkVector
from .kernel import BinarySpaKernel
from .numerics import MIN_SUM_CPU_F64
from .lineage import stable_lineage_id
from .profiling import ProfileMeasurement, validate_public_clean_low_overhead_evidence
from .schedules import EdgeTable, FloodingSchedule, LayeredSchedule
from .updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment


class CanonicalStructuralVerificationError(ValueError):
    """Persisted canonical evidence is well-formed but not reusable."""


def reconstruct_schedule_terminal(evidence: Mapping[str, Any]) -> dict[str, object]:
    """Independently validate version-three schedule progress and dual budget views.

    This is intentionally a grammar and arithmetic reconstruction, not a claim
    that a C2V cap, a source iteration, or measured runtime are interchangeable.
    """
    required = {
        "structural_event_version", "schedule", "source_iteration", "completed_traversals",
        "local_cursor", "stopping_adaptation", "work_vector", "setup_runtime", "decode_runtime",
        "budget_views",
    }
    if not isinstance(evidence, Mapping) or set(evidence) != required:
        raise CanonicalStructuralVerificationError("schedule terminal has an invalid exact field set")
    if evidence["structural_event_version"] != 3:
        raise CanonicalStructuralVerificationError("schedule terminal must use structural event version 3")
    try:
        work = WorkVector.from_evidence(evidence["work_vector"], structural_event_version=3)
        source_iteration = QualifiedIteration.from_evidence(evidence["source_iteration"])
        setup_runtime = Measurement(**evidence["setup_runtime"])
        decode_runtime = Measurement(**evidence["decode_runtime"])
    except (TypeError, ValueError) as error:
        raise CanonicalStructuralVerificationError("schedule terminal contains invalid typed facts") from error
    views = evidence["budget_views"]
    if not isinstance(views, list) or len(views) != 2:
        raise CanonicalStructuralVerificationError("schedule terminal requires two budget views")
    parsed_views: list[BudgetView] = []
    view_fields = {"kind", "configured_limit", "qualified_iteration", "work_vector", "setup_runtime", "decode_runtime"}
    for view in views:
        if not isinstance(view, Mapping) or set(view) != view_fields:
            raise CanonicalStructuralVerificationError("budget view has an invalid exact field set")
        if view["work_vector"] != work.as_evidence() or view["setup_runtime"] != setup_runtime.as_evidence() or view["decode_runtime"] != decode_runtime.as_evidence():
            raise CanonicalStructuralVerificationError("budget views must retain the complete shared work and runtime facts")
        try:
            if view["kind"] == "common_check_to_variable_cap":
                parsed = BudgetView.common_c2v_cap(view["configured_limit"])
                if view["qualified_iteration"] is not None or work.check_to_variable_updates > parsed.configured_limit:
                    raise ValueError("invalid common C2V cap evidence")
            elif view["kind"] == "schedule_qualified_iteration_limit":
                qualified = QualifiedIteration.from_evidence(view["qualified_iteration"])
                parsed = BudgetView.schedule_iteration_limit(qualified)
                if qualified.schedule != evidence["schedule"] or parsed.configured_limit != view["configured_limit"]:
                    raise ValueError("invalid schedule-qualified iteration evidence")
            else:
                raise ValueError("unknown budget view")
        except (TypeError, ValueError) as error:
            raise CanonicalStructuralVerificationError("budget view is not independently reconstructable") from error
        parsed_views.append(parsed)
    try:
        terminal = ScheduleTerminalEvidence(
            schedule=evidence["schedule"], source_iteration=source_iteration,
            completed_traversals=evidence["completed_traversals"],
            local_cursor=tuple(evidence["local_cursor"]), stopping_adaptation=evidence["stopping_adaptation"],
            work=work, setup_runtime=setup_runtime, decode_runtime=decode_runtime,
            budget_views=tuple(parsed_views),
        ).as_evidence()
    except (TypeError, ValueError) as error:
        raise CanonicalStructuralVerificationError("schedule terminal progress facts are invalid") from error
    if terminal != dict(evidence):
        raise CanonicalStructuralVerificationError("schedule terminal differs from independently reconstructed evidence")
    return terminal


def _deterministic_schedule_terminal(evidence: Mapping[str, Any]) -> dict[str, object]:
    """Project the replay-equality facts from a typed V3 schedule terminal.

    Setup/decode timing is deliberately parsed by ``reconstruct_schedule_terminal``
    but omitted here: it is an observational same-ledger fact, not an equality
    claim for deterministic schedule replay.
    """
    terminal = reconstruct_schedule_terminal(evidence)
    views = []
    for view in terminal["budget_views"]:
        assert isinstance(view, Mapping)
        views.append({
            "kind": view["kind"],
            "configured_limit": view["configured_limit"],
            "qualified_iteration": view["qualified_iteration"],
            "work_vector": view["work_vector"],
        })
    return {
        "structural_event_version": terminal["structural_event_version"],
        "schedule": terminal["schedule"],
        "source_iteration": terminal["source_iteration"],
        "completed_traversals": terminal["completed_traversals"],
        "local_cursor": terminal["local_cursor"],
        "stopping_adaptation": terminal["stopping_adaptation"],
        "work_vector": terminal["work_vector"],
        "budget_views": views,
    }


def validate_schedule_terminal_shot(
    events: Sequence[Mapping[str, Any]], *, run_id: str, shot_id: int,
    expected_terminal: Mapping[str, Any], expected_deterministic_facts: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Verify a V3 local-schedule terminal against independently derived facts.

    Event IDs only authenticate the JSON bytes that were written.  This entry
    point compares the re-executed/preflight-derived progress, work, candidate,
    policy, and purpose-separated RNG facts, so recomputing an event hash cannot
    turn a semantic alteration into reusable scientific evidence.
    """
    if type(shot_id) is not int or shot_id < 0:
        raise CanonicalStructuralVerificationError("schedule verification requires a nonnegative shot ID")
    stream = [
        event for event in events
        if event.get("run_id") == run_id and event.get("shot_id") == shot_id
    ]
    if len(stream) != 2 or [event.get("kind") for event in stream] != ["shot_begin", "termination"]:
        raise CanonicalStructuralVerificationError("schedule verification requires one V3 begin/terminal pair")
    terminal = stream[-1]
    if terminal.get("ledger_version") != 3:
        raise CanonicalStructuralVerificationError("schedule verification only applies to V3 schedule evidence")
    data = terminal.get("data")
    if not isinstance(data, Mapping) or set(data) != {"schedule_terminal", "deterministic_facts"}:
        raise CanonicalStructuralVerificationError("schedule terminal has an invalid deterministic field grammar")
    try:
        actual_terminal = _deterministic_schedule_terminal(data["schedule_terminal"])
        reconstructed_terminal = _deterministic_schedule_terminal(expected_terminal)
    except (TypeError, ValueError, CanonicalStructuralVerificationError) as error:
        raise CanonicalStructuralVerificationError("schedule terminal cannot be independently reconstructed") from error
    if actual_terminal != reconstructed_terminal or data["deterministic_facts"] != dict(expected_deterministic_facts):
        raise CanonicalStructuralVerificationError("deterministic schedule terminal differs from independent reconstruction")
    return terminal


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def public_execution_identity(
    *, manifest_sha256: str, artifact_raw_sha256: str, artifact_semantic_sha256: str,
    compact_manifest: Mapping[str, Any], sample_seed_identity: str, run_id: str,
    shot_id: int, check_type: str, syndrome: Sequence[int],
) -> str:
    """Hash every public input that can change a structural shot or its lineage."""
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("public execution identity requires a nonnegative shot ID")
    payload = {
        "domain": "bp-registry-public-execution-v1",
        "manifest_sha256": manifest_sha256,
        "artifact_raw_sha256": artifact_raw_sha256,
        "artifact_semantic_sha256": artifact_semantic_sha256,
        "compact_manifest": dict(compact_manifest),
        "sample_seed_identity": sample_seed_identity,
        "run_id": run_id,
        "shot_id": shot_id,
        "check_type": check_type,
        "syndrome": list(syndrome),
    }
    return "sha256:" + sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class PublicShotContext:
    """Immutable preflighted context used to validate one public run/shot."""

    manifest_sha256: str
    artifact_raw_sha256: str
    artifact_semantic_sha256: str
    compact_manifest: Mapping[str, Any]
    sample_seed_identity: str
    run_id: str
    shot_id: int
    check_type: str
    syndrome: tuple[int, ...]
    code_id: str
    evidence_relation: str
    fixture: str
    assessment_status: str
    decoder_seed_identity: str
    code: Any | None = None
    hidden_truth: Any | None = None
    error_rate: float | None = None
    max_iterations: int | None = None
    work_limits: Mapping[str, Mapping[str, int]] | None = None
    composition_identity: str | None = None
    policy_effects: Mapping[str, Any] | None = None
    profile_plan: Mapping[str, Any] | None = None
    update_kind: str = "binary_spa"
    schedule_kind: str = "flooding"

    @property
    def execution_identity(self) -> str:
        return public_execution_identity(
            manifest_sha256=self.manifest_sha256,
            artifact_raw_sha256=self.artifact_raw_sha256,
            artifact_semantic_sha256=self.artifact_semantic_sha256,
            compact_manifest=self.compact_manifest,
            sample_seed_identity=self.sample_seed_identity,
            run_id=self.run_id,
            shot_id=self.shot_id,
            check_type=self.check_type,
            syndrome=self.syndrome,
        )


def _budget_denial(limits: Mapping[str, Mapping[str, int]], work: WorkVector, delta: WorkVector) -> dict[str, Any] | None:
    """Match BudgetTree's reservation order without consulting ledger evidence."""
    proposed = work + delta
    for scope in ("attempt", "search", "shot"):
        for resource in delta.as_evidence():
            limit = int(limits.get(scope, {}).get(resource, 10**9))
            if getattr(proposed, resource) > limit:
                return {
                    "binding_scope": scope, "resource": resource,
                    "configured_limit": limit, "consumed_amount": getattr(work, resource),
                    "reason": "count_budget_exhausted",
                }
    return None


def _expected_layered_attempt(context: PublicShotContext) -> dict[str, Any]:
    """Independently replay the closed SPA/layered public tracer without ledger facts."""
    if context.code is None or context.error_rate is None or context.max_iterations is None:
        return {}
    schedule_data = context.compact_manifest.get("policies", {}).get("schedule", {})
    if not isinstance(schedule_data, Mapping):
        raise CanonicalStructuralVerificationError("layered public context lacks a schedule policy")
    partitions = schedule_data.get("partitions")
    provenance = schedule_data.get("provenance")
    if not isinstance(partitions, list) or not isinstance(provenance, str):
        raise CanonicalStructuralVerificationError("layered public context lacks explicit partition evidence")
    code = context.code.validate()
    table = EdgeTable.from_check_matrix(code.hz)
    kernel = BinarySpaKernel()
    schedule = LayeredSchedule(
        table, kernel=kernel, partitions=partitions, provenance=provenance,
        construction_rule=schedule_data.get("construction_rule"),
    )
    limits = context.work_limits or {}
    budget_limits = [
        BudgetLimit(scope, resource, int(limit))
        for scope in ("shot", "search", "attempt")
        for resource, limit in limits.get(scope, {}).items()
    ]
    budgets = BudgetTree(limits=budget_limits, parents={"search": "shot", "attempt": "search"})
    bp_call = budgets.reserve("attempt", WorkVector(bp_calls=1), leaf_id="expected:bp-call")
    if bp_call is None:
        return {"termination": "count_budget_exhausted", "work_vector": WorkVector.zero().as_evidence(structural_event_version=2), "schedule_work_vector": WorkVector.zero().as_evidence(), "iterations": 0, "admitted": False}
    bp_call.commit_once()
    messages = np.full(table.edge_count, kernel.prior(context.error_rate), dtype=np.float64)
    executor = __import__("bp_registry.canonical.execution", fromlist=["CanonicalLocalStepExecutor"]).CanonicalLocalStepExecutor(budgets, scope="attempt")
    progress = __import__("bp_registry.canonical.execution", fromlist=["ScheduleProgress"]).ScheduleProgress(0, 0, (0,))
    candidate: np.ndarray | None = None
    for _ in range(context.max_iterations):
        step = schedule.execute_local_step(
            executor, messages, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate,
            progress=progress,
            is_converged=lambda proposed: bool(np.array_equal((code.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2, context.syndrome)),
        )
        progress = step.progress
        if not step.admitted:
            work = budgets.summary("attempt")
            return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(schedule.evidence())), "iterations": progress.local_steps, "admitted": True, "progress": progress}
        candidate = step.candidate
        if candidate is not None and np.array_equal((code.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2, context.syndrome):
            work = budgets.summary("attempt")
            return {"termination": "completed", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(schedule.evidence())), "iterations": progress.local_steps, "candidate": candidate, "admitted": True, "progress": progress}
        if progress.cursor == (schedule.unit_count,):
            progress = type(progress)(progress.iteration + 1, progress.local_steps, (0,), progress.rng_state)
    work = budgets.summary("attempt")
    return {"termination": "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(schedule.evidence())), "iterations": progress.local_steps, "candidate": candidate, "admitted": True, "progress": progress}


def _expected_attempt(context: PublicShotContext) -> dict[str, Any]:
    """Re-run the deterministic Phase 2 flooding baseline without ledger input."""
    if context.code is None or context.error_rate is None or context.max_iterations is None:
        return {}
    if context.schedule_kind == "layered":
        return _expected_layered_attempt(context)
    code = context.code.validate()
    limits = context.work_limits or {}
    zero = WorkVector.zero()
    bp_call = WorkVector(bp_calls=1)
    denial = _budget_denial(limits, zero, bp_call)
    if denial is not None:
        return {"termination": "count_budget_exhausted", "work_vector": zero.as_evidence(structural_event_version=2), "iterations": 0, "budget_termination": denial, "admitted": False}
    work = bp_call
    table = EdgeTable.from_check_matrix(code.hz)
    if context.update_kind == "min_sum":
        kernel = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    elif context.update_kind == "normalized_min_sum":
        declared = context.compact_manifest.get("policies", {}).get("update", {}).get("parameter_assignment")
        assignment = ParameterAssignment.model_validate(declared)
        resolved = assignment.resolve(
            graph_sha256=table.graph_sha256, check_count=table.check_count, edge_count=table.edge_count,
            source_iteration=0, edge_checks=tuple(check for check, _variable in table.edges),
        )
        kernel = BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=NormalizedMinSumUpdate(
                assignment,
                resolved_alpha=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            ),
        )
    elif context.update_kind == "offset_min_sum":
        declared = context.compact_manifest.get("policies", {}).get("update", {}).get("parameter_assignment")
        assignment = ParameterAssignment.model_validate(declared)
        resolved = assignment.resolve(
            graph_sha256=table.graph_sha256, check_count=table.check_count, edge_count=table.edge_count,
            source_iteration=0, edge_checks=tuple(check for check, _variable in table.edges),
        )
        kernel = BinarySpaKernel(
            profile=MIN_SUM_CPU_F64,
            update_rule=OffsetMinSumUpdate(
                assignment,
                resolved_beta=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            ),
        )
    elif context.update_kind == "binary_spa":
        kernel = BinarySpaKernel()
    else:
        raise CanonicalStructuralVerificationError(f"unsupported public update rule {context.update_kind!r}")
    schedule = FloodingSchedule(table, kernel=kernel, profile=kernel.profile)
    if table.edge_count == 0:
        candidate = kernel.candidate_from_beliefs(np.full(code.n, kernel.prior(context.error_rate), dtype=np.float64))
        converged = bool(np.array_equal((code.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2, context.syndrome))
        return {"termination": "completed" if converged else "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "iterations": 0, "candidate": candidate, "admitted": True}
    state = schedule.initialize(context.error_rate)
    for iteration in range(1, context.max_iterations + 1):
        delta = WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=table.variable_count)
        denial = _budget_denial(limits, work, delta)
        if denial is not None:
            return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(structural_event_version=2), "iterations": iteration - 1, "budget_termination": denial, "admitted": True}
        proposed = work + delta
        sweep = schedule.sweep(state, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate)
        state, work = sweep.new_v2c, proposed
        if np.array_equal((code.hz.astype(np.int64) @ sweep.candidate.astype(np.int64)) % 2, context.syndrome):
            return {"termination": "completed", "work_vector": work.as_evidence(structural_event_version=2), "iterations": iteration, "candidate": sweep.candidate, "admitted": True}
    return {"termination": "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "iterations": context.max_iterations, "admitted": True}


def _expect_equal(field: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise CanonicalStructuralVerificationError(f"canonical {field} differs from independently reconstructed evidence")


def _validate_profile(stream: Sequence[Mapping[str, Any]], terminal: Mapping[str, Any], context: PublicShotContext) -> None:
    runtime = [event for event in stream if event.get("kind") == "runtime"]
    profile = terminal.get("data", {}).get("profile")
    measured = terminal.get("data", {}).get("work_vector", {}).get("bp_calls", 0) > 0
    if not measured:
        if runtime or profile is not None:
            raise CanonicalStructuralVerificationError("profile evidence is fabricated for a pre-attempt denial")
        return
    if terminal.get("termination") == "numerical_failure":
        if runtime or profile is not None:
            raise CanonicalStructuralVerificationError("numerical failure must retain explicit missingness rather than runtime evidence")
        return
    if len(runtime) != 1 or not isinstance(profile, Mapping):
        raise CanonicalStructuralVerificationError("measured canonical attempt requires exactly one runtime profile")
    runtime_profile = runtime[0].get("data", {}).get("profile")
    if runtime_profile != profile:
        raise CanonicalStructuralVerificationError("profile runtime and terminal evidence differ")
    parsed = ProfileMeasurement.from_evidence(profile)
    plan = context.profile_plan or {}
    if parsed.enabled != bool(plan.get("enabled", False)) or parsed.level != plan.get("level", "low_overhead"):
        raise CanonicalStructuralVerificationError("profile plan does not match the admitted public plan")
    try:
        validate_public_clean_low_overhead_evidence(profile)
    except ValueError as error:
        raise CanonicalStructuralVerificationError(f"profile evidence violates admitted local profiler contract: {error}") from error


_COMMON_FIELDS = frozenset({
    "manifest_sha256", "artifact_raw_sha256", "artifact_semantic_sha256", "code_id", "evidence_relation", "fixture",
    "assessment_status", "decoder_seed_identity", "canonical_identity", "execution_identity", "composition_identity", "policy_effects",
})


def _exact_data(event: Mapping[str, Any], expected: frozenset[str]) -> Mapping[str, Any]:
    data = event.get("data")
    if not isinstance(data, Mapping) or set(data) != expected:
        raise CanonicalStructuralVerificationError(f"canonical {event.get('kind')} event has an invalid exact data-field set")
    return data


def _validate_common(event: Mapping[str, Any], context: PublicShotContext, baseline: Mapping[str, Any] | None) -> Mapping[str, Any]:
    data = event["data"]
    expected = {
        "manifest_sha256": context.manifest_sha256,
        "artifact_raw_sha256": context.artifact_raw_sha256,
        "artifact_semantic_sha256": context.artifact_semantic_sha256,
        "code_id": context.code_id,
        "evidence_relation": context.evidence_relation,
        "fixture": context.fixture,
        "assessment_status": context.assessment_status,
        "decoder_seed_identity": context.decoder_seed_identity,
        "canonical_identity": context.execution_identity,
        "execution_identity": context.execution_identity,
    }
    if context.composition_identity is not None:
        expected["composition_identity"] = context.composition_identity
    if context.policy_effects is not None:
        expected["policy_effects"] = context.policy_effects
    for field, value in expected.items():
        _expect_equal(field, data.get(field), value)
    if baseline is not None:
        for field in _COMMON_FIELDS - set(expected):
            _expect_equal(field, data.get(field), baseline[field])
    return data


def _validate_event_envelopes(stream: Sequence[Mapping[str, Any]], context: PublicShotContext, expected_kinds: Sequence[str]) -> tuple[Mapping[str, Any], Mapping[str, Mapping[str, Any]]]:
    if [event.get("kind") for event in stream] != list(expected_kinds):
        raise CanonicalStructuralVerificationError("canonical termination event grammar is invalid")
    baseline: Mapping[str, Any] | None = None
    by_kind: dict[str, Mapping[str, Any]] = {}
    for event in stream:
        kind = event.get("kind")
        if "sidecar" in event:
            raise CanonicalStructuralVerificationError("trace evidence is forbidden by the public trace-off plan")
        top = {"ledger_version", "event_id", "kind", "run_id", "shot_id", "data"}
        if kind == "shot_begin":
            top.add("sample_seed_identity")
        if kind == "termination":
            top.add("termination")
        if set(event) != top or event.get("ledger_version") != 2 or event.get("run_id") != context.run_id or event.get("shot_id") != context.shot_id:
            raise CanonicalStructuralVerificationError("canonical structural event envelope is invalid")
        if kind == "shot_begin" and event.get("sample_seed_identity") != context.sample_seed_identity:
            raise CanonicalStructuralVerificationError("canonical shot sample identity differs from preflight")
        data = event.get("data")
        if not isinstance(data, Mapping):
            raise CanonicalStructuralVerificationError("canonical structural event lacks typed data")
        if baseline is None:
            baseline = data
        _validate_common(event, context, baseline)
        by_kind[kind] = event
    assert baseline is not None
    return baseline, by_kind


def _expected_attempt_lineage(context: PublicShotContext) -> dict[str, str] | None:
    """Reconstruct the public attempt ancestry independently of ledger records."""
    if context.code is None:
        return None
    original = stable_lineage_id("original", {"identity": context.execution_identity})
    working = stable_lineage_id("working", {"original": original.value, "lift": "identity"})
    attempt = stable_lineage_id("attempt", {"working": working.value, "ordinal": 0})
    return {
        "original_lineage_id": original.value,
        "working_lineage_id": working.value,
        "attempt_lineage_id": attempt.value,
    }


def validate_canonical_shot(events: Sequence[Mapping[str, Any]], context: PublicShotContext) -> Mapping[str, Any]:
    """Reject a stale, duplicate, or identity-mismatched persisted shot.

    Task 2 extends this entry point into complete semantic reconstruction.  The
    early check here is deliberately strict enough to make terminal reuse safe
    before the executor ever returns a previous result.
    """
    stream = [
        event for event in events
        if event.get("run_id") == context.run_id and event.get("shot_id") == context.shot_id
    ]
    if not stream:
        raise CanonicalStructuralVerificationError("canonical shot has no structural evidence")
    terminals = [event for event in stream if event.get("kind") == "termination"]
    if len(terminals) != 1 or stream[-1] is not terminals[0]:
        raise CanonicalStructuralVerificationError("canonical shot must have exactly one final termination")
    terminal = terminals[0]
    common = _COMMON_FIELDS
    term = terminal.get("termination")
    lineage = _expected_attempt_lineage(context)
    if term == "numerical_failure":
        _, records = _validate_event_envelopes(stream, context, ["shot_begin", "attempt", "missingness", "work", "termination"])
        _exact_data(records["shot_begin"], common)
        attempt = _exact_data(records["attempt"], common | {"scope", "attempt_lineage_id", "max_iterations"})
        if attempt["scope"] != "attempt" or attempt["max_iterations"] != context.max_iterations or not isinstance(attempt["attempt_lineage_id"], str):
            raise CanonicalStructuralVerificationError("numerical failure attempt evidence is invalid")
        if lineage is not None:
            _expect_equal("attempt_lineage_id", attempt["attempt_lineage_id"], lineage["attempt_lineage_id"])
        missingness = _exact_data(records["missingness"], common | {"field", "reason"})
        if dict((field, missingness[field]) for field in ("field", "reason")) != {"field": "candidate", "reason": "numerical_failure"}:
            raise CanonicalStructuralVerificationError("numerical failure missingness evidence is invalid")
        work_data = _exact_data(records["work"], common | {"qualified_iterations", "work_vector"})
        _exact_data(terminal, common | {"numerical_failure", "selection_status", "outcome", "verification_status", "work_vector"})
        data = terminal["data"]
        if not isinstance(data["numerical_failure"], str) or not data["numerical_failure"]:
            raise CanonicalStructuralVerificationError("numerical failure requires a typed diagnostic")
        if data["selection_status"] != "unavailable_due_to_numerical_failure" or data["verification_status"] != "not_independently_reproduced_numerical_failure" or data["outcome"] is not None:
            raise CanonicalStructuralVerificationError("numerical failure terminal qualification is invalid")
        expected_work = WorkVector(bp_calls=1).as_evidence(structural_event_version=2)
        _expect_equal("work_vector", work_data["work_vector"], expected_work)
        _expect_equal("work_vector", data["work_vector"], expected_work)
        _expect_equal("qualified_iterations", work_data["qualified_iterations"], {"count": 0, "schedule": "flooding", "atomic_unit": "complete_double_buffered_sweep"})
        return terminal
    expected = _expected_attempt(context)
    if not expected:
        return terminals[0]
    _expect_equal("termination", terminal.get("termination"), expected["termination"])
    if term == "completed":
        kinds = ["shot_begin", "attempt", "runtime", "candidate", "selection", "work", "termination"]
    elif expected["termination"] == "count_budget_exhausted":
        kinds = ["shot_begin", "attempt"] + (["runtime"] if expected["admitted"] else []) + ["work", "termination"]
    else:
        kinds = ["shot_begin", "attempt", "runtime", "work", "termination"]
    _, records = _validate_event_envelopes(stream, context, kinds)
    _exact_data(records["shot_begin"], common)
    attempt = _exact_data(records["attempt"], common | {"scope", "attempt_lineage_id", "max_iterations"})
    if attempt["scope"] != "attempt" or attempt["max_iterations"] != context.max_iterations or not isinstance(attempt["attempt_lineage_id"], str):
        raise CanonicalStructuralVerificationError("canonical attempt evidence is invalid")
    if lineage is not None:
        _expect_equal("attempt_lineage_id", attempt["attempt_lineage_id"], lineage["attempt_lineage_id"])
    schedule_fields = frozenset({"schedule_terminal", "schedule_evidence"}) if context.schedule_kind == "layered" else frozenset()
    work_data = _exact_data(records["work"], common | {"qualified_iterations", "work_vector"} | schedule_fields)
    _expect_equal("work_vector", work_data["work_vector"], expected["work_vector"])
    expected_iteration = {
        "count": expected["iterations"],
        "schedule": "layered" if context.schedule_kind == "layered" else "flooding",
        "atomic_unit": "one_layer" if context.schedule_kind == "layered" else "complete_double_buffered_sweep",
    }
    _expect_equal("qualified_iterations", work_data["qualified_iterations"], expected_iteration)
    if context.schedule_kind == "layered":
        schedule_terminal = reconstruct_schedule_terminal(work_data["schedule_terminal"])
        _expect_equal("schedule work_vector", schedule_terminal["work_vector"], expected["schedule_work_vector"])
        _expect_equal("schedule source_iteration", schedule_terminal["source_iteration"], expected_iteration)
        _expect_equal("schedule evidence", work_data["schedule_evidence"], expected["schedule_evidence"])
    data = terminal["data"]
    _expect_equal("work_vector", data.get("work_vector"), expected["work_vector"])
    if context.schedule_kind == "layered":
        _expect_equal("terminal schedule evidence", data.get("schedule_terminal"), work_data["schedule_terminal"])
        _expect_equal("terminal schedule realization", data.get("schedule_evidence"), work_data["schedule_evidence"])
    if expected["admitted"]:
        _expect_equal("iterations", data.get("iterations"), expected["iterations"])
        _exact_data(records["runtime"], common | {"profile"})
        _validate_profile(stream, terminal, context)
    if expected["termination"] == "completed":
        _exact_data(terminal, common | {"attempt_lineage_id", "candidate", "candidate_lineage_id", "converged", "iterations", "logical_action_agrees", "original_lineage_id", "outcome", "profile", "selection_status", "work_vector", "working_lineage_id"} | schedule_fields)
        _exact_data(records["candidate"], common | {"attempt_lineage_id", "candidate", "candidate_lineage_id"})
        _exact_data(records["selection"], common | {"selection_status", "original_lineage_id", "working_lineage_id", "attempt_lineage_id", "candidate_lineage_id"})
        candidate = np.asarray(expected["candidate"], dtype=np.uint8)
        _expect_equal("candidate", data.get("candidate"), candidate.tolist())
        _expect_equal("iterations", data.get("iterations"), expected["iterations"])
        if lineage is None:
            raise CanonicalStructuralVerificationError("completed terminal requires a reconstructable public lineage")
        candidate_id = stable_lineage_id("candidate", {"working": lineage["working_lineage_id"], "attempt": lineage["attempt_lineage_id"], "candidate": candidate.tolist()})
        for field, value in {
            **lineage, "candidate_lineage_id": candidate_id.value,
        }.items():
            _expect_equal(field, data.get(field), value)
        candidate_event = next(event for event in stream if event.get("kind") == "candidate")
        _expect_equal("candidate", candidate_event.get("data", {}).get("candidate"), candidate.tolist())
        _expect_equal("attempt_lineage_id", candidate_event.get("data", {}).get("attempt_lineage_id"), lineage["attempt_lineage_id"])
        _expect_equal("candidate_lineage_id", candidate_event.get("data", {}).get("candidate_lineage_id"), candidate_id.value)
        selection = next(event for event in stream if event.get("kind") == "selection")
        for field, value in {
            **lineage, "candidate_lineage_id": candidate_id.value,
        }.items():
            _expect_equal(field, selection.get("data", {}).get(field), value)
        if data["converged"] is not True or data["selection_status"] != "frozen_decoder_visible_candidate":
            raise CanonicalStructuralVerificationError("completed terminal selection qualification is invalid")
        if selection.get("data", {}).get("selection_status") != "frozen_decoder_visible_candidate":
            raise CanonicalStructuralVerificationError("selection evidence is not frozen decoder-visible")
        if context.hidden_truth is not None:
            evaluation = evaluator.evaluate_candidate(context.code, true_x=context.hidden_truth.x, true_z=context.hidden_truth.z, candidate_x=candidate)
            _expect_equal("outcome", data.get("outcome"), evaluation.outcome)
            _expect_equal("logical_action_agrees", data.get("logical_action_agrees"), evaluation.logical_action_agrees)
    else:
        if expected["termination"] == "count_budget_exhausted":
            fields = common | {"budget_termination", "outcome", "selection_status", "work_vector"} | schedule_fields
            if expected["admitted"]:
                fields |= {"iterations", "profile"}
            _exact_data(terminal, fields)
            _expect_equal("budget_termination", data.get("budget_termination"), expected["budget_termination"])
            if data["selection_status"] != "unavailable_due_to_budget" or data["outcome"] is not None:
                raise CanonicalStructuralVerificationError("count budget terminal qualification is invalid")
        else:
            _exact_data(terminal, common | {"converged", "iterations", "outcome", "profile", "selection_status", "work_vector"} | schedule_fields)
            if data["converged"] is not False or data["selection_status"] != "unavailable_due_to_stopping" or data["outcome"] is not None:
                raise CanonicalStructuralVerificationError("maximum iteration terminal qualification is invalid")
    return terminals[0]
