"""Public identity and structural reuse checks for canonical CSS evidence.

The ledger's content hashes make records durable, but they do not establish that
the record belongs to the currently preflighted public experiment.  This module
keeps that identity separate from hidden truth and gives both the runner and
CLI one reuse boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

import numpy as np

from .. import evaluator
from ..ledger import CANONICAL_RELAY_LEDGER_VERSION, read_canonical_events
from .budgets import BudgetLimit, BudgetTree, BudgetView, Measurement, QualifiedIteration, ScheduleTerminalEvidence, WallClockLimit, WorkVector
from .kernel import BinarySpaKernel
from .contracts import CanonicalManifestV7, MemoryCompositionSpec, Phase5InterventionContract, parse_canonical_manifest
from .phase5 import execute_phase5_controller, finalize_phase5_deadline, phase5_attempt_events, phase5_work_evidence
from .problems import OriginalProblem
from .memory_execution import LocalMemoryExecution, MemoryFloodingSchedule
from .group_shuffled import HsuGroupSchedule
from .numerics import MIN_SUM_CPU_F64
from .lineage import stable_lineage_id
from .profiling import ProfileMeasurement, validate_public_clean_low_overhead_evidence
from .schedules import (
    CheckNodeSerialSchedule, EdgeTable, FloodingSchedule, LayeredSchedule,
    RandomizedTraversalPlan, VariableNodeSerialSchedule,
)
from .updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment, resolve_generated_configuration_assignment
from .tracing import TracePlan, TraceSink


class CanonicalStructuralVerificationError(ValueError):
    """Persisted canonical evidence is well-formed but not reusable."""


def reconstruct_relay_work(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Reduce Phase 4's unique Relay leaves and reject ambiguous accounting.

    The durable work record is authoritative only when its total is exactly the
    sum of typed leaf contributions.  A repeated byte-identical ledger event is
    already collapsed by ``read_canonical_events``; repeated leaf IDs with a
    differing payload remain an error here.
    """
    work_events = [event for event in events if event.get("kind") == "work"]
    if len(work_events) != 1:
        raise CanonicalStructuralVerificationError("Phase 4 shot requires exactly one work event")
    data = work_events[0].get("data")
    if not isinstance(data, Mapping) or not isinstance(data.get("relay_work_leaves"), list):
        raise CanonicalStructuralVerificationError("Phase 4 work requires typed Relay leaves")
    try:
        declared = WorkVector.from_evidence(data["work_vector"], structural_event_version=2)
    except (TypeError, ValueError) as error:
        raise CanonicalStructuralVerificationError("Phase 4 work vector is invalid") from error
    leaves = data["relay_work_leaves"]
    seen: dict[str, Mapping[str, Any]] = {}
    deltas: list[WorkVector] = []
    for leaf in leaves:
        if not isinstance(leaf, Mapping):
            raise CanonicalStructuralVerificationError("Phase 4 work leaf is not an object")
        leaf_id = leaf.get("leaf_id")
        if not isinstance(leaf_id, str) or not leaf_id:
            raise CanonicalStructuralVerificationError("Phase 4 work leaf lacks a stable ID")
        previous = seen.get(leaf_id)
        if previous is not None:
            if previous != leaf:
                raise CanonicalStructuralVerificationError("Phase 4 work leaf ID has conflicting evidence")
            continue
        if leaf.get("kind") not in {"leg", "transfer", "candidate", "selection"}:
            raise CanonicalStructuralVerificationError("Phase 4 work leaf has an unknown type")
        if type(leaf.get("leg_index")) is not int or leaf["leg_index"] < 0:
            raise CanonicalStructuralVerificationError("Phase 4 work leaf has invalid leg ancestry")
        try:
            deltas.append(WorkVector.from_evidence(leaf["work_vector"], structural_event_version=2))
        except (KeyError, TypeError, ValueError) as error:
            raise CanonicalStructuralVerificationError("Phase 4 work leaf has invalid work evidence") from error
        seen[leaf_id] = leaf
    reduced = WorkVector.sum(deltas)
    if reduced != declared:
        raise CanonicalStructuralVerificationError("Phase 4 work total does not equal the unique leaf reduction")
    transfer_events = [
        event for event in events
        if event.get("kind") == "relay_transfer" and isinstance(event.get("data"), Mapping)
    ]
    transfer_ids = {event["data"].get("relay_leaf_id") for event in transfer_events}
    leaf_transfers = {leaf_id for leaf_id, leaf in seen.items() if leaf.get("kind") == "transfer"}
    if transfer_ids != leaf_transfers:
        raise CanonicalStructuralVerificationError("Phase 4 transfer events and transfer work leaves disagree")
    # New execution records the leg table alongside explicit committed leaves.
    # Use it to reject an aggregate which is numerically correct but attributed
    # to the wrong Relay leg.  Older journals lack relay_legs and continue
    # through the compatibility path above.
    relay_legs = data.get("relay_legs")
    if relay_legs is not None:
        if not isinstance(relay_legs, (list, tuple)):
            raise CanonicalStructuralVerificationError("Phase 4 Relay leg table is invalid")
        leg_lineages: dict[int, str] = {}
        for row in relay_legs:
            if not isinstance(row, Mapping) or type(row.get("index")) is not int or row["index"] < 0:
                raise CanonicalStructuralVerificationError("Phase 4 Relay leg table has invalid indices")
            lineage_id = row.get("lineage_id")
            if not isinstance(lineage_id, str) or not lineage_id or row["index"] in leg_lineages:
                raise CanonicalStructuralVerificationError("Phase 4 Relay leg table has ambiguous lineage")
            leg_lineages[row["index"]] = lineage_id
        for leaf in seen.values():
            if leaf.get("kind") == "leg":
                if leg_lineages.get(leaf["leg_index"]) != leaf.get("lineage_id"):
                    raise CanonicalStructuralVerificationError("Phase 4 leg work leaf disagrees with Relay leg lineage")
        for index, event in enumerate(transfer_events, start=1):
            leaf = seen.get(event["data"].get("relay_leaf_id"))
            if leaf is None or leaf.get("leg_index") != index or leaf.get("lineage_id") != event["data"].get("producer_leg_lineage_id"):
                raise CanonicalStructuralVerificationError("Phase 4 transfer work leaf disagrees with Relay leg lineage")
    return declared.as_evidence(structural_event_version=2)


def _validate_phase4_trace(event: Mapping[str, Any], *, trace_root: Path) -> dict[str, object]:
    """Load a bounded sidecar through its confined content-addressed reference."""
    sidecar = event.get("sidecar")
    if not isinstance(sidecar, Mapping):
        raise CanonicalStructuralVerificationError("Phase 4 trace event lacks a sidecar link")
    path, digest = sidecar.get("path"), sidecar.get("sha256")
    if not isinstance(path, str) or not isinstance(digest, str):
        raise CanonicalStructuralVerificationError("Phase 4 trace link is incomplete")
    from .tracing import TraceSink

    try:
        document = TraceSink.load(trace_root, path, expected_sha256=digest)
    except ValueError as error:
        raise CanonicalStructuralVerificationError("Phase 4 trace sidecar failed confinement or rehash validation") from error
    records = document.get("records")
    if not isinstance(records, list) or sidecar.get("records") != len(records):
        raise CanonicalStructuralVerificationError("Phase 4 trace record count disagrees with its link")
    candidate = trace_root / path
    if sidecar.get("bytes") != candidate.stat().st_size:
        raise CanonicalStructuralVerificationError("Phase 4 trace byte count disagrees with its link")
    if not isinstance(sidecar.get("truncated"), bool) or not isinstance(sidecar.get("dropped_records"), int):
        raise CanonicalStructuralVerificationError("Phase 4 trace truncation evidence is incomplete")
    if bool(document.get("truncated")) != sidecar["truncated"] or document.get("dropped_records") != sidecar["dropped_records"]:
        raise CanonicalStructuralVerificationError("Phase 4 trace truncation facts disagree with its sidecar")
    return document


def reconstruct_phase4_shot(
    events: Sequence[Mapping[str, Any]], *, run_id: str, shot_id: int, trace_root: str | Path,
) -> dict[str, object]:
    """Reconstruct one V4 Relay shot from an already validated ledger stream.

    Callers that reuse an inventory must obtain ``events`` from
    :func:`read_canonical_events` after binding the source bytes to their
    inventory.  This function intentionally retains all shot grammar, work
    reconstruction, and sidecar checks while avoiding another whole-ledger
    parse for each selected shot.
    """
    if not isinstance(run_id, str) or not run_id or type(shot_id) is not int or shot_id < 0:
        raise CanonicalStructuralVerificationError("Phase 4 verification requires a run ID and nonnegative shot ID")
    events = [
        event for event in events
        if event["run_id"] == run_id and event["shot_id"] == shot_id
    ]
    if not events or any(event["ledger_version"] != CANONICAL_RELAY_LEDGER_VERSION for event in events):
        raise CanonicalStructuralVerificationError("Phase 4 verification requires V4 Relay ledger evidence")
    if events[0]["kind"] != "shot_begin" or events[-1]["kind"] != "termination":
        raise CanonicalStructuralVerificationError("Phase 4 shot lacks a durable begin-to-terminal boundary")
    candidates = [event for event in events if event["kind"] == "candidate"]
    selections = [event for event in events if event["kind"] == "selection"]
    if len(selections) > 1:
        raise CanonicalStructuralVerificationError("Phase 4 shot has ambiguous selection evidence")
    if selections:
        chosen = selections[0]["data"].get("candidate_lineage_id")
        known = {event["data"].get("candidate_lineage_id") for event in candidates}
        if not isinstance(chosen, str) or chosen not in known:
            raise CanonicalStructuralVerificationError("Phase 4 selection does not name a retained candidate")
    for event in events:
        if event["kind"] == "missingness":
            data = event["data"]
            if data.get("value") is not None or not isinstance(data.get("field"), str) or not data["field"] or not isinstance(data.get("reason"), str) or not data["reason"]:
                raise CanonicalStructuralVerificationError("Phase 4 unavailable facts must remain typed and explicit")
    root = Path(trace_root)
    traces = [_validate_phase4_trace(event, trace_root=root) for event in events if event["kind"] == "trace_link"]
    work = reconstruct_relay_work(events) if any(event["kind"] == "work" for event in events) else None
    terminal = events[-1]
    if work is not None and terminal["data"].get("work_vector") != work:
        raise CanonicalStructuralVerificationError("Phase 4 terminal work disagrees with reconstructed leaves")
    return {
        "events": events,
        "transfers": [event["data"] for event in events if event["kind"] == "relay_transfer"],
        "candidates": [event["data"] for event in candidates],
        "selection": None if not selections else selections[0]["data"],
        "terminal": terminal,
        "work": work,
        "traces": traces,
    }


def validate_phase4_shot(
    ledger_path: str | Path, *, run_id: str, shot_id: int, trace_root: str | Path,
) -> dict[str, object]:
    """Read, validate, and reconstruct one V4 Relay shot from durable evidence.

    The path API remains the public validation boundary.  Inventory callers
    may reuse its already validated stream through ``reconstruct_phase4_shot``.
    """
    return reconstruct_phase4_shot(
        read_canonical_events(ledger_path), run_id=run_id, shot_id=shot_id,
        trace_root=trace_root,
    )


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


def public_memory_execution_context(
    *, compact_manifest: Mapping[str, Any], composition_identity: str | None,
    decoder_seed_identity: str, sample_seed_identity: str, shot_id: int,
) -> dict[str, str]:
    """Derive ordinary-memory RNG keys independently of optional observation.

    Trace-plan fields and ledger paths are intentionally absent.  The compact
    manifest carries decoder policy and memory bindings, while the public
    sample identity and shot distinguish independently admitted executions.
    """
    if type(shot_id) is not int or shot_id < 0:
        raise ValueError("memory execution context requires a nonnegative shot ID")
    configuration = {
        "domain": "bp-registry-memory-configuration-v1",
        "compact_manifest": dict(compact_manifest),
        "composition_identity": composition_identity,
        "decoder_seed_identity": decoder_seed_identity,
    }
    configuration_identity = "sha256:" + sha256(_canonical_json(configuration)).hexdigest()
    decoder = {
        "domain": "bp-registry-memory-decoder-v1",
        "configuration_identity": configuration_identity,
        "sample_seed_identity": sample_seed_identity,
        "shot_id": shot_id,
    }
    return {
        "configuration_identity": configuration_identity,
        "decoder_identity": "sha256:" + sha256(_canonical_json(decoder)).hexdigest(),
    }


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
    trace_plan: Mapping[str, Any] | None = None
    phase5_limits: Mapping[str, Any] | None = None
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

    @property
    def memory_execution_context(self) -> dict[str, str]:
        return public_memory_execution_context(
            compact_manifest=self.compact_manifest,
            composition_identity=self.composition_identity,
            decoder_seed_identity=self.decoder_seed_identity,
            sample_seed_identity=self.sample_seed_identity,
            shot_id=self.shot_id,
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


def _expected_kernel(context: PublicShotContext, table: EdgeTable) -> BinarySpaKernel:
    """Reconstruct the declared update/profile kernel for any public schedule."""
    if context.update_kind == "min_sum":
        return BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
    if context.update_kind in {"normalized_min_sum", "offset_min_sum"}:
        update = context.compact_manifest.get("policies", {}).get("update", {})
        declared = update.get("parameter_assignment")
        assignment = ParameterAssignment.model_validate(declared) if declared is not None else resolve_generated_configuration_assignment(
            dict(update), dict(context.compact_manifest), graph_sha256=table.graph_sha256,
            check_count=table.check_count, edge_count=table.edge_count,
        )[0]
        resolved = assignment.resolve(
            graph_sha256=table.graph_sha256, check_count=table.check_count, edge_count=table.edge_count,
            source_iteration=0, edge_checks=tuple(check for check, _variable in table.edges),
        )
        if context.update_kind == "normalized_min_sum":
            rule = NormalizedMinSumUpdate(
                assignment,
                resolved_alpha=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            )
        else:
            rule = OffsetMinSumUpdate(
                assignment,
                resolved_beta=None if assignment.shape == "source_iteration" else tuple(float(value) for value in resolved),
            )
        return BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=rule)
    if context.update_kind == "binary_spa":
        return BinarySpaKernel()
    raise CanonicalStructuralVerificationError(f"unsupported public update rule {context.update_kind!r}")


def _expected_local_attempt(
    context: PublicShotContext, *, trace_sink: TraceSink | None = None,
    trace_context: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Independently replay a closed public local schedule without ledger facts."""
    if context.code is None or context.error_rate is None or context.max_iterations is None:
        return {}
    schedule_data = context.compact_manifest.get("policies", {}).get("schedule", {})
    if not isinstance(schedule_data, Mapping):
        raise CanonicalStructuralVerificationError("local public context lacks a schedule policy")
    schedule_kind = context.schedule_kind
    partitions = schedule_data.get("partitions")
    provenance = schedule_data.get("provenance")
    if schedule_kind in {"layered", "randomized"} and (not isinstance(partitions, list) or not isinstance(provenance, str)):
        raise CanonicalStructuralVerificationError("layered local public context lacks explicit partition evidence")
    code = context.code.validate()
    table = EdgeTable.from_check_matrix(code.hz)
    kernel = _expected_kernel(context, table)
    is_memory = context.compact_manifest.get("schema_version") == 5
    if schedule_kind in {"layered", "randomized"}:
        schedule = LayeredSchedule(table, kernel=kernel, partitions=partitions, provenance=provenance, construction_rule=schedule_data.get("construction_rule"))
    elif schedule_kind == "check_node_serial":
        schedule = CheckNodeSerialSchedule(table, kernel=kernel)
    elif schedule_kind == "variable_node_serial":
        schedule = VariableNodeSerialSchedule(table, kernel=kernel)
    elif schedule_kind == "residual":
        from .residual import SyndromeResidualSchedule
        schedule = SyndromeResidualSchedule(table, kernel=kernel)
    elif schedule_kind == "group_shuffled":
        root_identity = schedule_data.get("root_identity")
        if schedule_data.get("source_id") != "hsu-ndgsbp-2012-v1" or not isinstance(root_identity, str):
            raise CanonicalStructuralVerificationError("group_shuffled context lacks its source and root identity")
        schedule = HsuGroupSchedule(table, kernel=kernel, root_identity=root_identity, attempt_identity=f"{context.execution_identity}:attempt:0")
    else:
        raise CanonicalStructuralVerificationError(f"unsupported public local schedule {schedule_kind!r}")
    limits = context.work_limits or {}
    budget_limits = [
        BudgetLimit(scope, resource, int(limit))
        for scope in ("shot", "search", "attempt")
        for resource, limit in limits.get(scope, {}).items()
    ]
    budgets = BudgetTree(limits=budget_limits, parents={"search": "shot", "attempt": "search"})
    def budget_termination() -> dict[str, object]:
        termination = budgets.last_termination
        if termination is None:
            raise CanonicalStructuralVerificationError("budget denial lacks a typed reason")
        return {
            "binding_scope": termination.binding_scope,
            "resource": termination.resource,
            "configured_limit": termination.configured_limit,
            "consumed_amount": termination.consumed_amount,
            "reason": termination.reason,
        }
    bp_call = budgets.reserve("attempt", WorkVector(bp_calls=1), leaf_id="expected:bp-call")
    if bp_call is None:
        return {"termination": "count_budget_exhausted", "work_vector": WorkVector.zero().as_evidence(structural_event_version=2), "schedule_work_vector": WorkVector.zero().as_evidence(), "iterations": 0, "budget_termination": budget_termination(), "admitted": False}
    bp_call.commit_once()
    messages = np.full(table.edge_count, kernel.prior(context.error_rate), dtype=np.float64)
    local_memory = None
    if is_memory:
        local_memory = LocalMemoryExecution(
            table, memory=MemoryCompositionSpec.model_validate(context.compact_manifest["memory"]),
            profile=kernel.profile,
            execution_context=context.memory_execution_context,
            trace_sink=trace_sink, trace_context=trace_context,
        )
        local_memory.initialize(
            error_rate=context.error_rate, initial_v2c=messages,
            initial_beliefs=np.full(table.variable_count, kernel.prior(context.error_rate), dtype=np.float64),
        )

    def memory_evidence() -> dict[str, Any]:
        return {} if local_memory is None else {"memory_execution": local_memory.evidence()}
    executor = __import__("bp_registry.canonical.execution", fromlist=["CanonicalLocalStepExecutor"]).CanonicalLocalStepExecutor(budgets, scope="attempt")
    progress = __import__("bp_registry.canonical.execution", fromlist=["ScheduleProgress"]).ScheduleProgress(0, 0, (0,))
    randomized: RandomizedTraversalPlan | None = None
    randomized_state = None
    randomized_order: tuple[int, ...] | None = None
    if schedule_kind == "randomized":
        root_identity = schedule_data.get("root_identity")
        refresh_scope = schedule_data.get("refresh_scope")
        if not isinstance(root_identity, str) or not isinstance(refresh_scope, str):
            raise CanonicalStructuralVerificationError("randomized local context lacks replay identity")
        randomized = RandomizedTraversalPlan(schedule, refresh_scope=refresh_scope, root_identity=root_identity)
        randomized_state = randomized.initial_state(configuration_identity=context.execution_identity, attempt_identity=f"{context.execution_identity}:attempt:0")
    if schedule_kind == "residual":
        c2v = np.zeros(table.edge_count, dtype=np.float64)
        try:
            cache = schedule.initialize(messages, c2v, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate, budgets=budgets)
        except Exception as error:
            termination = getattr(error, "termination", None)
            return {"termination": "count_budget_exhausted", "work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2), "schedule_work_vector": budgets.summary("attempt").as_evidence(), "iterations": 0, "budget_termination": budget_termination(), "admitted": True, "progress": progress, "schedule_evidence": {"schedule": "residual"}}
        # The residual schedule advances its iteration only after E selected
        # C2V commits, so max_iterations bounds complete source traversals.
        while progress.iteration < context.max_iterations:
            proposal = schedule.propose_local_step(messages, c2v, cache, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate)
            step = schedule.execute_local_step(executor, proposal, v2c=messages, c2v=c2v, cache=cache, progress=progress, is_converged=lambda proposed: bool(np.array_equal((code.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2, context.syndrome)))
            progress, cache, c2v = step.progress, step.cache, step.c2v
            if not step.admitted:
                return {"termination": "count_budget_exhausted", "work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2), "schedule_work_vector": budgets.summary("attempt").as_evidence(), "iterations": progress.local_steps, "budget_termination": budget_termination(), "admitted": True, "progress": progress, "schedule_evidence": {"schedule": "residual", "atomic_unit": "one_residual_selected_c2v_commit", "source_iteration": schedule.source_iteration, "tie_rule": schedule.tie_rule, "policy_name": schedule.policy_name, "mutable_state_lifetime": "attempt"}}
            if step.converged:
                return {"termination": "completed", "work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2), "schedule_work_vector": budgets.summary("attempt").as_evidence(), "iterations": progress.local_steps, "candidate": step.candidate, "admitted": True, "progress": progress, "schedule_evidence": {"schedule": "residual", "atomic_unit": "one_residual_selected_c2v_commit", "source_iteration": schedule.source_iteration, "tie_rule": schedule.tie_rule, "policy_name": schedule.policy_name, "mutable_state_lifetime": "attempt"}}
        return {"termination": "max_iterations", "work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2), "schedule_work_vector": budgets.summary("attempt").as_evidence(), "iterations": progress.local_steps, "admitted": True, "progress": progress, "schedule_evidence": {"schedule": "residual", "atomic_unit": "one_residual_selected_c2v_commit", "source_iteration": schedule.source_iteration, "tie_rule": schedule.tie_rule, "policy_name": schedule.policy_name, "mutable_state_lifetime": "attempt"}}
    candidate: np.ndarray | None = None
    local_prior_llrs: np.ndarray | None = None
    # Layered/node-serial and randomized schedules expose one local unit at a
    # time, but their public iteration limit bounds complete traversals.  Hsu's
    # retained group schedule pins its historical bound in declared local groups.
    def local_iteration_remaining() -> bool:
        if schedule_kind in {"layered", "check_node_serial", "variable_node_serial", "randomized"}:
            return progress.iteration < context.max_iterations
        return progress.local_steps < context.max_iterations

    while local_iteration_remaining():
        progress_for_step = progress
        if local_memory is not None and progress.cursor == (0,):
            local_prior_llrs = local_memory.begin_source_iteration()
        if schedule_kind == "group_shuffled" and progress.cursor == (0,):
            refreshed, _ = schedule.refresh_order(progress, budgets=budgets)
            if not refreshed:
                work = budgets.summary("attempt")
                return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(schedule.evidence())), "iterations": progress.local_steps, "budget_termination": budget_termination(), "admitted": True, "progress": progress}
        if randomized is not None:
            assert randomized_state is not None
            if progress.cursor == (0,):
                boundary: str | None = None
                if randomized.refresh_scope == "sweep":
                    boundary = "sweep"
                elif progress.iteration == 0:
                    boundary = randomized.refresh_scope
                if boundary is not None:
                    refresh = randomized.refresh(
                        randomized_state, boundary=boundary, budgets=budgets,
                        budget_scope="attempt",
                    )
                    if not refresh.admitted:
                        return {"termination": "count_budget_exhausted", "work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2), "schedule_work_vector": budgets.summary("attempt").as_evidence(), "iterations": progress.local_steps, "budget_termination": budget_termination(), "admitted": True, "progress": progress, "schedule_evidence": dict(schedule.evidence())}
                    randomized_state = refresh.state
                    randomized_order = refresh.order
            if randomized_order is None:
                raise CanonicalStructuralVerificationError("randomized traversal has no admitted order")
            progress_for_step = type(progress)(
                progress.iteration, progress.local_steps,
                (randomized_order[progress.cursor[0]],), progress.rng_state,
            )
        if local_memory is not None:
            local_memory.begin_step()
        try:
            step = schedule.execute_local_step(
                executor, messages, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate,
                progress=progress_for_step,
                is_converged=lambda proposed: bool(np.array_equal((code.hz.astype(np.int64) @ proposed.astype(np.int64)) % 2, context.syndrome)),
                **({"prior_llrs": local_prior_llrs, "transform_beliefs": local_memory.transform_beliefs, "transform_v2c": local_memory.transform_v2c}
                   if local_memory is not None else {}),
            )
        except BaseException:
            if local_memory is not None:
                local_memory.discard()
                local_memory.abort_source_iteration()
            raise
        progress = (type(progress)(progress.iteration, step.progress.local_steps, (progress.cursor[0] + 1,), progress.rng_state) if randomized is not None else step.progress)
        evidence = dict(schedule.evidence())
        if randomized is not None:
            evidence["randomized_traversal"] = randomized.evidence(randomized_state)
        if not step.admitted:
            if local_memory is not None:
                local_memory.discard()
                local_memory.abort_source_iteration()
            work = budgets.summary("attempt")
            return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(evidence)), "iterations": progress.local_steps, "budget_termination": budget_termination(), "admitted": True, "progress": progress, **memory_evidence()}
        if local_memory is not None:
            local_memory.commit(local_memory.proposal())
        complete_source_iteration = progress.cursor == (schedule.unit_count,)
        if local_memory is not None and complete_source_iteration:
            local_memory.complete_source_iteration()
        candidate = step.candidate
        if candidate is not None and np.array_equal((code.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2, context.syndrome):
            if local_memory is not None and not complete_source_iteration:
                local_memory.abort_source_iteration()
            work = budgets.summary("attempt")
            return {"termination": "completed", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(evidence)), "iterations": progress.local_steps, "candidate": candidate, "admitted": True, "progress": progress, **memory_evidence()}
        if complete_source_iteration:
            progress = type(progress)(progress.iteration + 1, progress.local_steps, (0,), progress.rng_state)
            local_prior_llrs = None
    work = budgets.summary("attempt")
    if local_memory is not None:
        local_memory.abort_source_iteration()
    evidence = dict(schedule.evidence())
    if randomized is not None:
        evidence["randomized_traversal"] = randomized.evidence(randomized_state)
    return {"termination": "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "schedule_work_vector": work.as_evidence(), "schedule_evidence": json.loads(json.dumps(evidence)), "iterations": progress.local_steps, "candidate": candidate, "admitted": True, "progress": progress, **memory_evidence()}


def _expected_attempt(
    context: PublicShotContext, *, trace_sink: TraceSink | None = None,
    trace_context: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Re-run the deterministic Phase 2 flooding baseline without ledger input."""
    if context.code is None or context.error_rate is None or context.max_iterations is None:
        return {}
    if context.schedule_kind != "flooding":
        return _expected_local_attempt(context, trace_sink=trace_sink, trace_context=trace_context)
    code = context.code.validate()
    limits = context.work_limits or {}
    zero = WorkVector.zero()
    bp_call = WorkVector(bp_calls=1)
    denial = _budget_denial(limits, zero, bp_call)
    if denial is not None:
        return {"termination": "count_budget_exhausted", "work_vector": zero.as_evidence(structural_event_version=2), "iterations": 0, "budget_termination": denial, "admitted": False}
    work = bp_call
    table = EdgeTable.from_check_matrix(code.hz)
    kernel = _expected_kernel(context, table)
    is_memory = context.compact_manifest.get("schema_version") == 5
    if is_memory:
        schedule = MemoryFloodingSchedule(
            table, kernel=kernel, memory=MemoryCompositionSpec.model_validate(context.compact_manifest["memory"]),
            execution_context=context.memory_execution_context,
            trace_sink=trace_sink, trace_context=trace_context,
        )
        state = schedule.initialize(context.error_rate)
    else:
        schedule = FloodingSchedule(table, kernel=kernel, profile=kernel.profile)

    def memory_evidence() -> dict[str, Any]:
        return {"memory_execution": schedule.evidence()} if is_memory else {}

    if table.edge_count == 0:
        candidate = kernel.candidate_from_beliefs(np.full(code.n, kernel.prior(context.error_rate), dtype=np.float64))
        converged = bool(np.array_equal((code.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2, context.syndrome))
        return {"termination": "completed" if converged else "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "iterations": 0, "candidate": candidate, "admitted": True, **memory_evidence()}
    if not is_memory:
        state = schedule.initialize(context.error_rate)
    last_candidate = None
    for iteration in range(1, context.max_iterations + 1):
        delta = WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=table.variable_count)
        denial = _budget_denial(limits, work, delta)
        if denial is not None:
            return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(structural_event_version=2), "iterations": iteration - 1, "budget_termination": denial, "admitted": True, "diagnostic_candidate": last_candidate, **memory_evidence()}
        proposed = work + delta
        assignment = getattr(kernel.update_rule, "alpha", getattr(kernel.update_rule, "beta", None))
        sweep = schedule.sweep(
            state, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate,
            **({"source_iteration": iteration - 1}
               if is_memory or getattr(assignment, "shape", None) == "source_iteration" else {}),
        )
        if is_memory:
            schedule.commit(sweep)
            schedule.observe_candidate(
                origin={
                    "candidate_origin": "last_committed_sweep",
                    "source_iteration": iteration - 1,
                    "status": "diagnostic",
                },
                candidate=sweep.candidate,
            )
        last_candidate = sweep.candidate.tolist()
        state, work = sweep.new_v2c, proposed
        if np.array_equal((code.hz.astype(np.int64) @ sweep.candidate.astype(np.int64)) % 2, context.syndrome):
            return {"termination": "completed", "work_vector": work.as_evidence(structural_event_version=2), "iterations": iteration, "candidate": sweep.candidate, "admitted": True, **memory_evidence()}
    return {"termination": "max_iterations", "work_vector": work.as_evidence(structural_event_version=2), "iterations": context.max_iterations, "admitted": True, "diagnostic_candidate": last_candidate, **memory_evidence()}


def _expect_equal(field: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise CanonicalStructuralVerificationError(f"canonical {field} differs from independently reconstructed evidence")


def _validate_memory_element_updates(evidence: Mapping[str, Any], context: PublicShotContext) -> None:
    """Independently check per-binding history-state accounting evidence."""
    if context.code is None:
        return
    bindings = evidence.get("bindings")
    updates = evidence.get("memory_element_updates")
    count = evidence.get("committed_iterations", evidence.get("committed_local_updates"))
    source_count = evidence.get("committed_source_iterations", count)
    if (not isinstance(bindings, list) or not isinstance(updates, Mapping)
            or type(count) is not int or count < 0
            or type(source_count) is not int or source_count < 0):
        raise CanonicalStructuralVerificationError("memory operation evidence is malformed")
    table = EdgeTable.from_check_matrix(context.code.validate().hz)
    expected: dict[str, int] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or not isinstance(binding.get("binding_id"), str) or not isinstance(binding.get("kind"), str):
            raise CanonicalStructuralVerificationError("memory operation binding evidence is malformed")
        kind = binding["kind"]
        width = (
            table.edge_count if kind == "v2c_damping" else
            2 * table.variable_count if kind in {"pdprime_delta_mix", "posterior_momentum"}
            else table.variable_count
        )
        expected[binding["binding_id"]] = (source_count if kind == "affine_prior" else count) * width
    if dict(updates) != expected:
        raise CanonicalStructuralVerificationError("memory element updates do not match owned history state")


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


def _expected_public_memory_trace(
    context: PublicShotContext, plan: Mapping[str, Any], terminal: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Replay the bounded observer independently of persisted sidecar bytes."""
    with TemporaryDirectory(prefix="bp-registry-trace-replay-") as directory:
        root = Path(directory)
        trace_plan = TracePlan(
            root=root, level=plan["level"], relative_dir=plan["relative_dir"],
            max_records=plan["max_records"], max_bytes=plan["max_bytes"], label=plan["label"],
        )
        sink = TraceSink(trace_plan)
        trace_context = {
            **context.memory_execution_context,
            "run_id": context.run_id,
            "shot_id": str(context.shot_id),
        }
        replay_context = context
        if terminal.get("termination") == "numerical_failure":
            terminal_data = terminal.get("data", {})
            count = terminal_data.get("iterations") if isinstance(terminal_data, Mapping) else None
            if type(count) is not int or not 0 <= count < context.max_iterations:
                raise CanonicalStructuralVerificationError("numerical trace lacks a valid committed memory prefix")
            replay_context = replace(context, max_iterations=count)
        expected = _expected_attempt(replay_context, trace_sink=sink, trace_context=trace_context)
        terminal_data = terminal.get("data", {})
        candidate = terminal_data.get("candidate", terminal_data.get("diagnostic_candidate"))
        if candidate is not None:
            sink.observe(
                kind="memory_candidate",
                payload={
                    **trace_context,
                    "origin": {
                        "termination": terminal.get("termination"),
                        "selection_status": terminal_data.get("selection_status"),
                        "candidate_lineage_id": terminal_data.get("candidate_lineage_id"),
                    },
                    "candidate": np.asarray(candidate, dtype=np.uint8),
                },
            )
        result = sink.finish()
        if result.sidecar_path is None:
            raise CanonicalStructuralVerificationError("canonical trace replay produced no observable records")
        document = TraceSink.load(root, result.sidecar_path, expected_sha256=result.sha256)
        if (expected.get("termination") != terminal.get("termination")
                and not (terminal.get("termination") == "numerical_failure"
                         and expected.get("termination") == "max_iterations")):
            raise CanonicalStructuralVerificationError("canonical trace replay has a different termination")
        return document


def _validate_public_memory_trace(
    event: Mapping[str, Any], *, context: PublicShotContext, trace_root: Path | None,
    terminal: Mapping[str, Any],
) -> None:
    """Validate the one optional ordinary-memory sidecar for a public shot."""
    plan = {} if context.trace_plan is None else dict(context.trace_plan)
    enabled = plan.get("level", "off") != "off"
    data = event.get("data")
    if not isinstance(data, Mapping):
        raise CanonicalStructuralVerificationError("canonical trace link lacks data")
    common = _COMMON_FIELDS | frozenset({"trace_kind", "status"})
    if data.get("trace_kind") != "ordinary_memory":
        raise CanonicalStructuralVerificationError("canonical trace link has an unknown trace kind")
    if data.get("status") == "unavailable":
        if set(data) != common | {"reason"} or "sidecar" in event:
            raise CanonicalStructuralVerificationError("canonical unavailable trace lacks explicit missingness")
        return
    if not enabled or data.get("status") != "linked" or set(data) != common:
        raise CanonicalStructuralVerificationError("canonical trace link disagrees with the public trace plan")
    if trace_root is None:
        raise CanonicalStructuralVerificationError("canonical trace validation requires its public output root")
    top = {"ledger_version", "event_id", "kind", "run_id", "shot_id", "data", "sidecar"}
    if set(event) != top:
        raise CanonicalStructuralVerificationError("canonical trace link has an invalid envelope")
    document = _validate_phase4_trace(event, trace_root=trace_root)
    try:
        expected_selection = TracePlan(
            root=trace_root, level=plan["level"], relative_dir=plan["relative_dir"],
            max_records=plan["max_records"], max_bytes=plan["max_bytes"], label=plan["label"],
        ).selection_basis()
    except (KeyError, TypeError, ValueError) as error:
        raise CanonicalStructuralVerificationError("canonical public trace plan is invalid") from error
    if document.get("selection_basis") != expected_selection:
        raise CanonicalStructuralVerificationError("canonical trace selection basis differs from the public trace plan")
    execution_context = context.memory_execution_context
    for record in document["records"]:
        payload = record.get("payload") if isinstance(record, Mapping) else None
        if not isinstance(payload, Mapping):
            raise CanonicalStructuralVerificationError("canonical trace has an invalid record payload")
        if payload.get("configuration_identity") != execution_context["configuration_identity"] or payload.get("decoder_identity") != execution_context["decoder_identity"]:
            raise CanonicalStructuralVerificationError("canonical trace record has the wrong decoder execution identity")
    expected = _expected_public_memory_trace(context, plan, terminal)
    if document != expected:
        raise CanonicalStructuralVerificationError("canonical trace differs from independently replayed committed memory observations")


def validate_phase5_shot(
    events: Sequence[Mapping[str, Any]], context: PublicShotContext,
) -> Mapping[str, Any]:
    """Reexecute the declared controller and compare every durable scientific fact."""
    from .execution import _budget_tree

    stream = [event for event in events if event.get("run_id") == context.run_id and event.get("shot_id") == context.shot_id]
    if not stream or any(event.get("ledger_version") != 5 for event in stream):
        raise CanonicalStructuralVerificationError("Phase 5 shot requires version-five structural evidence")
    parsed = parse_canonical_manifest(context.compact_manifest)
    spec = parsed.intervention
    if not isinstance(spec, Phase5InterventionContract):
        raise CanonicalStructuralVerificationError("Phase 5 shot requires the complete intervention contract")
    if context.code is None or context.hidden_truth is None or context.work_limits is None or context.phase5_limits is None:
        raise CanonicalStructuralVerificationError("Phase 5 replay requires the full preflighted public context")
    identity = context.execution_identity
    identity_data = {
        "execution_identity": identity,
        "manifest_sha256": context.manifest_sha256,
        "artifact_raw_sha256": context.artifact_raw_sha256,
        "artifact_semantic_sha256": context.artifact_semantic_sha256,
        "sample_seed_identity": context.sample_seed_identity,
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
    code = context.code.validate()
    original_id = stable_lineage_id("original", {"identity": identity})
    original = OriginalProblem(original_id.value, code.hx, code.hz, np.asarray(context.syndrome, dtype=np.uint8))
    budgets = _budget_tree({"work_limits": context.work_limits, "phase5_work_caps": context.phase5_limits["work_caps"]})
    runtime_rows = [row for row in stream if row.get("kind") == "runtime"]
    if len(runtime_rows) > 1:
        raise CanonicalStructuralVerificationError("Phase 5 shot has duplicate runtime evidence")
    wall_clock = None
    if runtime_rows:
        runtime = runtime_rows[0].get("data", {}).get("payload")
        cap_ns = int(context.phase5_limits["max_runtime_seconds"] * 1_000_000_000)
        if not isinstance(runtime, Mapping) or set(runtime) != {"deadline", "check_count"}:
            raise CanonicalStructuralVerificationError("Phase 5 runtime evidence is malformed")
        deadline = runtime["deadline"]
        check_count = runtime["check_count"]
        if (not isinstance(deadline, Mapping) or type(check_count) is not int or check_count < 2
                or deadline.get("reason") != "wall_clock_deadline"
                or deadline.get("resource") != "wall_clock_ns"
                or deadline.get("configured_limit") != cap_ns
                or type(deadline.get("observed_elapsed_ns")) is not int
                or deadline["observed_elapsed_ns"] < cap_ns
                or deadline.get("overshoot_ns") != deadline["observed_elapsed_ns"] - cap_ns):
            raise CanonicalStructuralVerificationError("Phase 5 runtime deadline differs from the sealed cap")
        clock_checks = 0

        def replay_clock() -> int:
            nonlocal clock_checks
            clock_checks += 1
            return deadline["observed_elapsed_ns"] if clock_checks == check_count else 0

        wall_clock = WallClockLimit(cap_ns, clock=replay_clock)
        wall_clock.check("attempt_start", scope="attempt")
    outcome = execute_phase5_controller(
        spec, original, error_rate=context.error_rate, budgets=budgets,
        max_iterations=context.max_iterations, owner_identity=identity,
        wall_clock=wall_clock,
        damping_gamma=damping_gamma,
        update_kind=parsed.policies.update.kind,
    )
    outcome = finalize_phase5_deadline(outcome, wall_clock)
    if runtime_rows and (wall_clock is None or wall_clock.first_termination is None
                         or wall_clock.first_termination_check != runtime["check_count"]
                         or asdict(wall_clock.first_termination) != runtime["deadline"]):
        raise CanonicalStructuralVerificationError("Phase 5 runtime boundary cannot be independently replayed")
    candidate = None if outcome.candidate is None else np.asarray(outcome.candidate, dtype=np.uint8)
    if candidate is not None and (candidate.shape != (code.hz.shape[1],)
                                  or not np.array_equal((code.hz @ candidate) % 2, original.syndrome)):
        raise CanonicalStructuralVerificationError("replayed candidate fails original syndrome validation")
    assessment = None if candidate is None or outcome.termination == "wall_clock_deadline" else evaluator.evaluate_candidate(
        code, true_x=context.hidden_truth.x, true_z=context.hidden_truth.z, candidate_x=candidate,
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
    expected: list[tuple[str, Mapping[str, Any]]] = [
        ("shot_begin", {"original_lineage_id": original_id.value, "syndrome": [int(bit) for bit in original.syndrome]}),
        ("intervention", outcome.header),
    ]
    expected.extend(("branch", row) for row in outcome.branches)
    expected.extend(phase5_attempt_events(spec, outcome))
    if candidate is not None:
        expected.append(("candidate", {"bits": candidate.tolist(), "origin": outcome.selected_origin}))
        expected.append(("original_check", {"candidate": candidate.tolist(), "valid": True}))
    expected.extend([
        ("selection", {"candidate": terminal["candidate"], "origin": outcome.selected_origin,
                       "status": terminal["selection_status"]}),
        ("work", phase5_work_evidence(outcome)),
    ])
    if assessment is not None:
        expected.append(("evaluation", {"outcome": assessment.outcome,
                                         "logical_action_agrees": assessment.logical_action_agrees}))
    if runtime_rows:
        expected.append(("runtime", runtime))
    expected.append(("termination", terminal))
    if len(stream) != len(expected):
        raise CanonicalStructuralVerificationError("Phase 5 event count differs from deterministic replay")
    for index, (event, (kind, payload)) in enumerate(zip(stream, expected)):
        data = event.get("data", {})
        actual_payload = data.get("payload")
        if kind == "termination" and isinstance(actual_payload, Mapping) and "decode_runtime" in actual_payload:
            evidence = actual_payload["decode_runtime"]
            try:
                if not isinstance(evidence, Mapping) or set(evidence) != {
                    "value", "method", "scope", "unit", "precision", "unavailable_reason"
                }:
                    raise ValueError("invalid intervention runtime fields")
                measured = Measurement(**evidence)
                if (type(measured.value) is not int or measured.value < 0
                        or measured.method != "time.perf_counter_ns:phase5-controller:v1"
                        or measured.scope != "canonical_intervention_controller"
                        or measured.unit != "ns" or measured.precision != "1 ns"):
                    raise ValueError("invalid intervention runtime measurement")
            except (TypeError, ValueError) as error:
                raise CanonicalStructuralVerificationError("Phase 5 decode runtime is invalid") from error
            actual_payload = {key: value for key, value in actual_payload.items() if key != "decode_runtime"}
        if event.get("kind") != kind or data.get("identity") != identity_data or actual_payload != payload:
            raise CanonicalStructuralVerificationError(f"Phase 5 event {index} differs from deterministic replay")
        if kind == "shot_begin":
            if data.get("schema_version") != 5 or data.get("compact_schema_version") != parsed.schema_version or event.get("sample_seed_identity") != context.sample_seed_identity:
                raise CanonicalStructuralVerificationError("Phase 5 begin identity or schema differs")
        if kind == "termination" and event.get("termination") != outcome.termination:
            raise CanonicalStructuralVerificationError("Phase 5 terminal status differs from deterministic replay")
    work_payload = next(event["data"]["payload"] for event in stream if event["kind"] == "work")
    leaves = work_payload["leaves"]
    if len({leaf["leaf_id"] for leaf in leaves}) != len(leaves):
        raise CanonicalStructuralVerificationError("Phase 5 duplicate work leaf")
    reduced = WorkVector.sum(
        WorkVector.from_evidence(leaf["work_vector"], structural_event_version=4) for leaf in leaves
    )
    if reduced != WorkVector.from_evidence(work_payload["work_vector"], structural_event_version=4):
        raise CanonicalStructuralVerificationError("Phase 5 work total differs from leaf reduction")
    return stream[-1]


def validate_phase6_shot(events: Sequence[Mapping[str, Any]], context: PublicShotContext) -> Mapping[str, Any]:
    """Replay the complete V7 ensemble without trusting persisted summaries."""
    from ..manifests import CanonicalExperimentV7, parse_manifest
    from .mbbp import MbbpBasis, MbbpController, MbbpSpec
    from .phase6 import phase6_events

    parsed = parse_manifest(context.compact_manifest)
    if not isinstance(parsed, CanonicalExperimentV7):
        raise CanonicalStructuralVerificationError("Phase 6 replay requires the complete V7 ensemble contract")
    if context.code is None or context.hidden_truth is None or context.error_rate is None:
        raise CanonicalStructuralVerificationError("Phase 6 replay requires code, observation, and hidden truth at the evaluator boundary")
    stream = [event for event in events if event.get("run_id") == context.run_id and event.get("shot_id") == context.shot_id]
    if not stream or any(event.get("ledger_version") != 6 for event in stream):
        raise CanonicalStructuralVerificationError("Phase 6 shot requires version-six structural evidence")
    code = context.code.validate()
    identity = context.execution_identity
    original = OriginalProblem(stable_lineage_id("original", {"identity": identity}).value,
                               code.hx, code.hz, np.asarray(context.syndrome, dtype=np.uint8))
    bases = tuple(MbbpBasis(item.member_id, item.local_ordinal, item.partition_identity,
                            item.permutation_identity, item.redundant_transforms)
                  for item in parsed.ensemble.bases)
    result = MbbpController(MbbpSpec(bases, max_iterations=parsed.ensemble.max_iterations,
                                     max_member_c2v_updates=parsed.ensemble.max_member_c2v_updates)).run(
                                         original, error_rate=context.error_rate)
    projection = phase6_events(
        original, bases=bases, result=result,
        vote_tie_bit=None if parsed.vote is None else parsed.vote.tie_bit,
    )
    candidate = None if projection.candidate is None else np.asarray(projection.candidate, dtype=np.uint8)
    if candidate is not None and not np.array_equal((code.hz @ candidate) % 2, original.syndrome):
        raise CanonicalStructuralVerificationError("replayed Phase 6 selection fails the original syndrome")
    assessment = None if candidate is None else evaluator.evaluate_candidate(
        code, true_x=context.hidden_truth.x, true_z=context.hidden_truth.z, candidate_x=candidate,
    )
    identity_data = {"execution_identity": identity, "source_status": parsed.ensemble.source_status,
                     "ensemble_kind": parsed.ensemble.kind}
    expected: list[tuple[str, Mapping[str, Any]]] = [
        ("shot_begin", {"original_lineage_id": original.lineage_id, "syndrome": original.syndrome.tolist()}),
    ]
    expected.extend((kind, payload) for kind, payload in projection.events if kind not in {"header", "termination"})
    if assessment is not None:
        expected.append(("evaluation", {"outcome": assessment.outcome,
                                           "logical_action_agrees": assessment.logical_action_agrees}))
    terminal = dict(projection.events[-1][1])
    terminal["outcome"] = None if assessment is None else assessment.outcome
    terminal["logical_action_agrees"] = None if assessment is None else assessment.logical_action_agrees
    expected.append(("termination", terminal))
    if len(stream) != len(expected):
        raise CanonicalStructuralVerificationError("Phase 6 event count differs from deterministic replay")
    for index, (event, (kind, payload)) in enumerate(zip(stream, expected)):
        data = event.get("data")
        if event.get("kind") != kind or not isinstance(data, Mapping):
            raise CanonicalStructuralVerificationError(f"Phase 6 event {index} has an invalid kind or payload")
        if kind == "shot_begin":
            if data.get("schema_version") != 7 or data.get("identity") != identity_data or data.get("payload") != payload:
                raise CanonicalStructuralVerificationError("Phase 6 header differs from deterministic replay")
        elif data.get("identity") != identity_data or data.get("payload") != payload:
            raise CanonicalStructuralVerificationError(f"Phase 6 event {index} differs from deterministic replay")
        if kind == "termination" and event.get("termination") != projection.terminal:
            raise CanonicalStructuralVerificationError("Phase 6 terminal status differs from deterministic replay")
    if result.terminal_status == "no_member_converged_zero_return":
        forbidden = {"selection", "original_check", "evaluation"}
        if any(event.get("kind") in forbidden for event in stream):
            raise CanonicalStructuralVerificationError("Phase 6 zero-return sentinel crossed selection/evaluation boundary")
    return stream[-1]


def validate_canonical_shot(
    events: Sequence[Mapping[str, Any]], context: PublicShotContext, *, trace_root: str | Path | None = None,
) -> Mapping[str, Any]:
    """Reject a stale, duplicate, or identity-mismatched persisted shot.

    Task 2 extends this entry point into complete semantic reconstruction.  The
    early check here is deliberately strict enough to make terminal reuse safe
    before the executor ever returns a previous result.
    """
    if context.compact_manifest.get("schema_version") == 7 and "ensemble" in context.compact_manifest:
        return validate_phase6_shot(events, context)
    if context.compact_manifest.get("schema_version") in {6, 7}:
        parsed = parse_canonical_manifest(context.compact_manifest)
        if isinstance(parsed.intervention, Phase5InterventionContract):
            return validate_phase5_shot(events, context)
    stream = [
        event for event in events
        if event.get("run_id") == context.run_id and event.get("shot_id") == context.shot_id
    ]
    if not stream:
        raise CanonicalStructuralVerificationError("canonical shot has no structural evidence")
    terminals = [event for event in stream if event.get("kind") == "termination"]
    if len(terminals) != 1 or stream[-1] is not terminals[0]:
        raise CanonicalStructuralVerificationError("canonical shot must have exactly one final termination")
    traces = [event for event in stream if event.get("kind") == "trace_link"]
    trace_enabled = bool((context.trace_plan or {}).get("level", "off") != "off")
    if trace_enabled:
        if len(traces) != 1:
            raise CanonicalStructuralVerificationError("enabled public trace plan requires exactly one terminal trace link")
        trace_index = stream.index(traces[0])
        if trace_index + 1 >= len(stream) or stream[trace_index + 1].get("kind") != "work":
            raise CanonicalStructuralVerificationError("canonical trace must follow committed decoder state and precede work evidence")
        _validate_common(traces[0], context, None)
        _validate_public_memory_trace(
            traces[0], context=context, trace_root=None if trace_root is None else Path(trace_root),
            terminal=terminals[0],
        )
    elif traces:
        raise CanonicalStructuralVerificationError("trace evidence is forbidden by the public trace-off plan")
    stream = [event for event in stream if event.get("kind") != "trace_link"]
    terminal = terminals[0]
    terminal_data = terminal.get("data", {})
    has_setup = "setup_runtime" in terminal_data
    has_decode = "decode_runtime" in terminal_data
    if has_setup != has_decode:
        raise CanonicalStructuralVerificationError("canonical runtime split must contain both setup and decode")
    runtime_fields = frozenset({"setup_runtime", "decode_runtime"}) if has_setup else frozenset()
    if has_setup:
        for field in runtime_fields:
            evidence = terminal_data[field]
            try:
                if not isinstance(evidence, Mapping) or set(evidence) != {
                    "value", "method", "scope", "unit", "precision", "unavailable_reason"
                }:
                    raise ValueError("invalid runtime measurement fields")
                measured = Measurement(**evidence)
                if measured.unit != "ns" or (measured.value is not None and measured.value < 0):
                    raise ValueError("runtime measurement must be nonnegative nanoseconds")
                expected_scope = "canonical_setup" if field == "setup_runtime" else "canonical_decode_attempt"
                expected_method = "time.perf_counter_ns:v1" if field == "setup_runtime" else "time.perf_counter_ns:profile-minus-setup:v1"
                if measured.scope != expected_scope or measured.method != (expected_method if measured.value is not None else "not_measured"):
                    raise ValueError("runtime measurement scope or method is invalid")
            except (TypeError, ValueError) as error:
                raise CanonicalStructuralVerificationError(f"canonical {field} is invalid") from error
    common = _COMMON_FIELDS
    term = terminal.get("termination")
    lineage = _expected_attempt_lineage(context)
    if term == "numerical_failure":
        failed_memory = context.compact_manifest.get("schema_version") == 5
        is_local = context.schedule_kind != "flooding"
        schedule_fields = frozenset({"schedule_terminal", "schedule_evidence"}) if is_local else frozenset()
        prefix: dict[str, Any] | None = None
        count = 0
        if failed_memory:
            runtime_fields |= {"iterations", "memory_execution"}
            count = terminal_data.get("iterations")
            if type(count) is not int or not 0 <= count < context.max_iterations:
                raise CanonicalStructuralVerificationError("numerical failure has an invalid memory commit count")
            prefix = _expected_attempt(replace(context, max_iterations=count))
            if prefix["termination"] != "max_iterations":
                raise CanonicalStructuralVerificationError("numerical failure follows a reconstructed terminal prefix")
            _expect_equal("memory execution", terminal_data.get("memory_execution"), prefix["memory_execution"])
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
        work_data = _exact_data(records["work"], common | {"qualified_iterations", "work_vector"} | schedule_fields)
        _exact_data(terminal, common | {"numerical_failure", "selection_status", "outcome", "verification_status", "work_vector"} | runtime_fields | schedule_fields)
        if is_local and not failed_memory:
            qualified = work_data["qualified_iterations"]
            if (not isinstance(qualified, Mapping) or type(qualified.get("count")) is not int
                    or qualified["count"] < 0 or qualified["count"] >= context.max_iterations):
                raise CanonicalStructuralVerificationError("local numerical failure has an invalid committed iteration count")
            count = qualified["count"]
            prefix = _expected_attempt(replace(context, max_iterations=count))
            if prefix.get("termination") != "max_iterations":
                raise CanonicalStructuralVerificationError("numerical failure follows a reconstructed local terminal prefix")
        data = terminal["data"]
        if not isinstance(data["numerical_failure"], str) or not data["numerical_failure"]:
            raise CanonicalStructuralVerificationError("numerical failure requires a typed diagnostic")
        if data["selection_status"] != "unavailable_due_to_numerical_failure" or data["verification_status"] != "not_independently_reproduced_numerical_failure" or data["outcome"] is not None:
            raise CanonicalStructuralVerificationError("numerical failure terminal qualification is invalid")
        expected_work = prefix["work_vector"] if failed_memory or is_local else WorkVector(bp_calls=1).as_evidence(structural_event_version=2)
        _expect_equal("work_vector", work_data["work_vector"], expected_work)
        _expect_equal("work_vector", data["work_vector"], expected_work)
        if is_local:
            assert prefix is not None
            local_atomic_units = {
                "layered": "one_layer",
                "check_node_serial": "one_check_all_c2v_then_affected_v2c",
                "variable_node_serial": "one_variable_belief_then_incident_v2c",
                "residual": "one_residual_selected_c2v_commit",
                "randomized": "one_layer",
                "group_shuffled": "one_overlapping_check_group",
            }
            expected_iteration = {
                "count": count,
                "schedule": context.schedule_kind,
                "atomic_unit": local_atomic_units[context.schedule_kind],
            }
            _expect_equal("qualified_iterations", work_data["qualified_iterations"], expected_iteration)
            schedule_terminal = reconstruct_schedule_terminal(work_data["schedule_terminal"])
            _expect_equal("schedule work_vector", schedule_terminal["work_vector"], prefix["schedule_work_vector"])
            _expect_equal("schedule source_iteration", schedule_terminal["source_iteration"], expected_iteration)
            _expect_equal("schedule evidence", work_data["schedule_evidence"], prefix["schedule_evidence"])
            _expect_equal("terminal schedule evidence", data["schedule_terminal"], work_data["schedule_terminal"])
            _expect_equal("terminal schedule realization", data["schedule_evidence"], work_data["schedule_evidence"])
        else:
            _expect_equal("qualified_iterations", work_data["qualified_iterations"], {"count": count if failed_memory else 0, "schedule": "flooding", "atomic_unit": "complete_double_buffered_sweep"})
        return terminal
    expected = _expected_attempt(context)
    if not expected:
        return terminals[0]
    _expect_equal("termination", terminal.get("termination"), expected["termination"])
    memory_fields = frozenset({"memory_execution"}) if "memory_execution" in expected else frozenset()
    if memory_fields:
        _expect_equal("memory execution", terminal_data.get("memory_execution"), expected["memory_execution"])
    runtime_fields |= memory_fields
    if context.compact_manifest.get("schema_version") == 5 and expected["termination"] in {"count_budget_exhausted", "max_iterations"}:
        runtime_fields |= {"diagnostic_candidate", "diagnostic_candidate_origin"}
        _expect_equal("diagnostic candidate", terminal_data.get("diagnostic_candidate"), expected.get("diagnostic_candidate"))
        origin = "last_committed_local_unit" if context.schedule_kind != "flooding" else "last_committed_sweep"
        _expect_equal("diagnostic candidate origin", terminal_data.get("diagnostic_candidate_origin"), origin if expected.get("diagnostic_candidate") is not None else None)
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
    is_local = context.schedule_kind != "flooding"
    schedule_fields = frozenset({"schedule_terminal", "schedule_evidence"}) if is_local else frozenset()
    work_data = _exact_data(records["work"], common | {"qualified_iterations", "work_vector"} | schedule_fields)
    _expect_equal("work_vector", work_data["work_vector"], expected["work_vector"])
    local_atomic_units = {
        "layered": "one_layer",
        "check_node_serial": "one_check_all_c2v_then_affected_v2c",
        "variable_node_serial": "one_variable_belief_then_incident_v2c",
        "residual": "one_residual_selected_c2v_commit",
        "randomized": "one_layer",
        "group_shuffled": "one_overlapping_check_group",
    }
    expected_iteration = {
        "count": expected["iterations"],
        "schedule": context.schedule_kind if is_local else "flooding",
        "atomic_unit": local_atomic_units[context.schedule_kind] if is_local else "complete_double_buffered_sweep",
    }
    _expect_equal("qualified_iterations", work_data["qualified_iterations"], expected_iteration)
    if is_local:
        schedule_terminal = reconstruct_schedule_terminal(work_data["schedule_terminal"])
        _expect_equal("schedule work_vector", schedule_terminal["work_vector"], expected["schedule_work_vector"])
        _expect_equal("schedule source_iteration", schedule_terminal["source_iteration"], expected_iteration)
        _expect_equal("schedule evidence", work_data["schedule_evidence"], expected["schedule_evidence"])
    data = terminal["data"]
    _expect_equal("work_vector", data.get("work_vector"), expected["work_vector"])
    if is_local:
        _expect_equal("terminal schedule evidence", data.get("schedule_terminal"), work_data["schedule_terminal"])
        _expect_equal("terminal schedule realization", data.get("schedule_evidence"), work_data["schedule_evidence"])
        if runtime_fields:
            _expect_equal("schedule setup runtime", data["setup_runtime"], data["schedule_terminal"]["setup_runtime"])
            _expect_equal("schedule decode runtime", data["decode_runtime"], data["schedule_terminal"]["decode_runtime"])
    if expected["admitted"]:
        _expect_equal("iterations", data.get("iterations"), expected["iterations"])
        _exact_data(records["runtime"], common | {"profile"})
        _validate_profile(stream, terminal, context)
    if expected["termination"] == "completed":
        _exact_data(terminal, common | {"attempt_lineage_id", "candidate", "candidate_lineage_id", "converged", "iterations", "logical_action_agrees", "original_lineage_id", "outcome", "profile", "selection_status", "work_vector", "working_lineage_id"} | schedule_fields | runtime_fields)
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
            fields = common | {"budget_termination", "outcome", "selection_status", "work_vector"} | schedule_fields | runtime_fields
            if expected["admitted"]:
                fields |= {"iterations", "profile"}
            _exact_data(terminal, fields)
            _expect_equal("budget_termination", data.get("budget_termination"), expected["budget_termination"])
            if data["selection_status"] != "unavailable_due_to_budget" or data["outcome"] is not None:
                raise CanonicalStructuralVerificationError("count budget terminal qualification is invalid")
        else:
            _exact_data(terminal, common | {"converged", "iterations", "outcome", "profile", "selection_status", "work_vector"} | schedule_fields | runtime_fields)
            if data["converged"] is not False or data["selection_status"] != "unavailable_due_to_stopping" or data["outcome"] is not None:
                raise CanonicalStructuralVerificationError("maximum iteration terminal qualification is invalid")
    return terminals[0]
