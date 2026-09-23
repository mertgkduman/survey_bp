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
from .budgets import WorkVector
from .kernel import BinarySpaKernel
from .lineage import LineageEdge, stable_lineage_id
from .problems import OriginalProblem, WorkingProblem
from .profiling import ProfileMeasurement
from .schedules import EdgeTable, FloodingSchedule


class CanonicalStructuralVerificationError(ValueError):
    """Persisted canonical evidence is well-formed but not reusable."""


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
    code: Any | None = None
    hidden_truth: Any | None = None
    error_rate: float | None = None
    max_iterations: int | None = None
    work_limits: Mapping[str, Mapping[str, int]] | None = None
    composition_identity: str | None = None
    policy_effects: Mapping[str, Any] | None = None
    profile_plan: Mapping[str, Any] | None = None

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


def _expected_attempt(context: PublicShotContext) -> dict[str, Any]:
    """Re-run the deterministic Phase 2 flooding baseline without ledger input."""
    if context.code is None or context.error_rate is None or context.max_iterations is None:
        return {}
    code = context.code.validate()
    limits = context.work_limits or {}
    zero = WorkVector.zero()
    bp_call = WorkVector(bp_calls=1)
    # Every ancestor must admit the first BP-call reservation before work begins.
    for scope in ("attempt", "search", "shot"):
        for resource, amount in bp_call.as_evidence().items():
            if amount > int(limits.get(scope, {}).get(resource, 10**9)):
                return {"termination": "count_budget_exhausted", "work_vector": zero.as_evidence(), "iterations": 0}
    work = bp_call
    kernel = BinarySpaKernel()
    table = EdgeTable.from_check_matrix(code.hz)
    schedule = FloodingSchedule(table, kernel=kernel)
    if table.edge_count == 0:
        candidate = kernel.candidate_from_beliefs(np.full(code.n, kernel.prior(context.error_rate), dtype=np.float64))
        converged = bool(np.array_equal((code.hz.astype(np.int64) @ candidate.astype(np.int64)) % 2, context.syndrome))
        return {"termination": "completed" if converged else "max_iterations", "work_vector": work.as_evidence(), "iterations": 0, "candidate": candidate}
    state = schedule.initialize(context.error_rate)
    for iteration in range(1, context.max_iterations + 1):
        delta = WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=table.variable_count)
        proposed = work + delta
        for scope in ("attempt", "search", "shot"):
            for resource, amount in proposed.as_evidence().items():
                if amount > int(limits.get(scope, {}).get(resource, 10**9)):
                    return {"termination": "count_budget_exhausted", "work_vector": work.as_evidence(), "iterations": iteration - 1}
        sweep = schedule.sweep(state, np.asarray(context.syndrome, dtype=np.uint8), error_rate=context.error_rate)
        state, work = sweep.new_v2c, proposed
        if np.array_equal((code.hz.astype(np.int64) @ sweep.candidate.astype(np.int64)) % 2, context.syndrome):
            return {"termination": "completed", "work_vector": work.as_evidence(), "iterations": iteration, "candidate": sweep.candidate}
    return {"termination": "max_iterations", "work_vector": work.as_evidence(), "iterations": context.max_iterations}


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
    if stream[0].get("kind") != "shot_begin":
        raise CanonicalStructuralVerificationError("canonical shot must start with shot_begin")
    terminals = [event for event in stream if event.get("kind") == "termination"]
    if len(terminals) != 1 or stream[-1] is not terminals[0]:
        raise CanonicalStructuralVerificationError("canonical shot must have exactly one final termination")
    if stream[0].get("sample_seed_identity") != context.sample_seed_identity:
        raise CanonicalStructuralVerificationError("canonical shot sample identity differs from preflight")
    expected = {
        "manifest_sha256": context.manifest_sha256,
        "artifact_raw_sha256": context.artifact_raw_sha256,
        "artifact_semantic_sha256": context.artifact_semantic_sha256,
        "canonical_identity": context.execution_identity,
    }
    for event in stream:
        data = event.get("data")
        if not isinstance(data, Mapping):
            raise CanonicalStructuralVerificationError("canonical structural event lacks typed data")
        for field, value in expected.items():
            if data.get(field) != value:
                raise CanonicalStructuralVerificationError(
                    f"canonical {field} differs from current public execution identity"
                )
        if event.get("sidecar") is not None or event.get("kind") in {"trace_link", "trace_truncated"}:
            raise CanonicalStructuralVerificationError("trace evidence is forbidden by the public trace-off plan")
    expected = _expected_attempt(context)
    if not expected:
        return terminals[0]
    terminal = terminals[0]
    data = terminal["data"]
    if terminal.get("termination") == "numerical_failure":
        if data.get("verification_status") != "not_independently_reproduced_numerical_failure":
            raise CanonicalStructuralVerificationError("numerical failure lacks not-independently-reproduced status")
        if data.get("candidate") is not None or data.get("outcome") is not None:
            raise CanonicalStructuralVerificationError("numerical failure carries forbidden candidate or outcome")
        work = data.get("work_vector")
        if not isinstance(work, Mapping) or work.get("bp_calls") != 1 or any(
            amount != 0 for resource, amount in work.items() if resource != "bp_calls"
        ):
            raise CanonicalStructuralVerificationError("numerical failure lacks atomic-sweep rollback work evidence")
        if [event.get("kind") for event in stream] != ["shot_begin", "attempt", "missingness", "work", "termination"]:
            raise CanonicalStructuralVerificationError("numerical failure event grammar is invalid")
        return terminal
    _expect_equal("termination", terminal.get("termination"), expected["termination"])
    _expect_equal("work_vector", data.get("work_vector"), expected["work_vector"])
    work = [event for event in stream if event.get("kind") == "work"]
    if len(work) != 1 or work[0].get("data", {}).get("work_vector") != expected["work_vector"]:
        raise CanonicalStructuralVerificationError("canonical work_vector does not match terminal evidence")
    _expect_equal("policy_effects", data.get("policy_effects"), context.policy_effects)
    if context.composition_identity is not None:
        _expect_equal("composition_identity", data.get("composition_identity"), context.composition_identity)
    _validate_profile(stream, terminal, context)
    if expected["termination"] == "completed":
        candidate = np.asarray(expected["candidate"], dtype=np.uint8)
        _expect_equal("candidate", data.get("candidate"), candidate.tolist())
        _expect_equal("iterations", data.get("iterations"), expected["iterations"])
        original_id = stable_lineage_id("original", {"identity": context.execution_identity})
        original = OriginalProblem(original_id.value, context.code.hx, context.code.hz, np.asarray(context.syndrome, dtype=np.uint8))
        working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
        working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
        attempt_id = stable_lineage_id("attempt", {"working": working.lineage_id, "ordinal": 0})
        candidate_id = stable_lineage_id("candidate", {"working": working.lineage_id, "attempt": attempt_id.value, "candidate": candidate.tolist()})
        for field, value in {
            "original_lineage_id": original_id.value, "working_lineage_id": working_id.value,
            "attempt_lineage_id": attempt_id.value, "candidate_lineage_id": candidate_id.value,
        }.items():
            _expect_equal(field, data.get(field), value)
        attempt = next(event for event in stream if event.get("kind") == "attempt")
        _expect_equal("attempt_lineage_id", attempt.get("data", {}).get("attempt_lineage_id"), attempt_id.value)
        candidate_event = next(event for event in stream if event.get("kind") == "candidate")
        _expect_equal("candidate", candidate_event.get("data", {}).get("candidate"), candidate.tolist())
        _expect_equal("candidate_lineage_id", candidate_event.get("data", {}).get("candidate_lineage_id"), candidate_id.value)
        selection = next(event for event in stream if event.get("kind") == "selection")
        for field, value in {
            "original_lineage_id": original_id.value, "working_lineage_id": working_id.value,
            "attempt_lineage_id": attempt_id.value, "candidate_lineage_id": candidate_id.value,
        }.items():
            _expect_equal(field, selection.get("data", {}).get(field), value)
        if context.hidden_truth is not None:
            evaluation = evaluator.evaluate_candidate(context.code, true_x=context.hidden_truth.x, true_z=context.hidden_truth.z, candidate_x=candidate)
            _expect_equal("outcome", data.get("outcome"), evaluation.outcome)
            _expect_equal("logical_action_agrees", data.get("logical_action_agrees"), evaluation.logical_action_agrees)
        required = ["shot_begin", "attempt", "runtime", "candidate", "selection", "work", "termination"]
    else:
        if data.get("candidate") is not None or data.get("outcome") is not None:
            raise CanonicalStructuralVerificationError("non-completed terminal carries forbidden candidate or outcome")
        required = (
            ["shot_begin", "attempt", "runtime", "work", "termination"]
            if data.get("work_vector", {}).get("bp_calls", 0) > 0
            else ["shot_begin", "attempt", "work", "termination"]
        )
    if [event.get("kind") for event in stream] != required:
        raise CanonicalStructuralVerificationError("canonical termination event grammar is invalid")
    return terminals[0]
