"""Dedicated structural execution and replay for the Phase 7 LSD tracer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .. import evaluator
from ..css import CssCode
from ..ledger import CanonicalEventWriter, read_canonical_events
from ..sampling import DecoderObservation, HiddenTruth
from .budgets import WorkVector
from .contracts import parse_canonical_manifest
from .execution import AtomicFloodingExecutor, _budget_tree, _kernel_for_manifest
from .lineage import LineageEdge, stable_lineage_id
from .problems import OriginalProblem, WorkingProblem
from .schedules import EdgeTable, FloodingSchedule

from .postprocessing import FailedAttemptSnapshot, LsdPostprocessor, PostprocessingController, PostprocessingResult


def phase7_events(result: PostprocessingResult) -> tuple[tuple[str, dict[str, Any]], ...]:
    """Persist BP-only and final facts separately before any evaluation boundary."""
    bp_only = None if result.bp_only_candidate is None else list(result.bp_only_candidate)
    final = None if result.candidate is None else list(result.candidate)
    return (
        ("bp_only", {"candidate": bp_only, "selected_attempt_lineage_id": result.selected_attempt_lineage_id}),
        ("fallback", {"status": result.status, "native_calls": result.native_calls,
                      "selected_attempt_lineage_id": result.selected_attempt_lineage_id,
                      "stable_tie_order": list(result.stable_tie_order), "error": result.error}),
        ("final", {"candidate": final, "original_valid": result.original_valid,
                   "bp_only_candidate": bp_only}),
    )


def run_phase7_structural_shot(
    manifest: dict[str, object], *, code: CssCode, observation: DecoderObservation,
    hidden_truth: HiddenTruth, shot_id: int, ledger_path: str | Path,
    sample_seed_identity: str, context: Mapping[str, Any],
    execution_controls: Mapping[str, Any] | None = None,
):
    """Run one complete flooding attempt and seal the optional terminal once.

    The V8 route owns the terminal so fallback facts are written before the
    append-only journal closes.  Hidden truth is only read after ``final`` is
    frozen.
    """
    config = manifest.get("postprocessing_config")
    if not isinstance(config, dict):
        raise ValueError("Phase 7 compact manifest requires postprocessing_config")
    base = dict(manifest)
    base.pop("postprocessing_config", None)
    base["schema_version"] = 3
    parsed = parse_canonical_manifest(base)
    if parsed.policies.schedule.kind != "flooding":
        raise ValueError("Phase 7 tracer admits one flooding composition")
    validated = code.validate()
    identity = str(context["manifest_sha256"])
    original_id = stable_lineage_id("original", {"identity": identity, "shot": shot_id})
    original = OriginalProblem(original_id.value, validated.hx, validated.hz, observation.syndrome)
    working_id = stable_lineage_id("working", {"original": original_id.value, "lift": "identity"})
    working = WorkingProblem(working_id.value, original, LineageEdge("identity", original_id, working_id))
    path = Path(ledger_path)
    existing = [row for row in read_canonical_events(path) if row["kind"] == "termination" and row["run_id"] == parsed.run_id and row["shot_id"] == shot_id]
    if existing:
        return existing[0]
    budgets = _budget_tree(execution_controls)
    table = EdgeTable.from_check_matrix(validated.hz)
    kernel = _kernel_for_manifest(parsed, table)
    schedule = FloodingSchedule(table, kernel=kernel, profile=kernel.profile)
    initialized = schedule.initialize(parsed.error_rate)
    attempt = AtomicFloodingExecutor(schedule, budgets, scope="attempt").run_attempt(
        initialized, observation.syndrome, error_rate=parsed.error_rate, max_iterations=parsed.max_iterations,
        is_converged=lambda sweep: bool(np.array_equal((validated.hz @ sweep.candidate) % 2, observation.syndrome)),
    )
    sweep = attempt.last_sweep
    bp_candidate = None if sweep is None else np.asarray(sweep.candidate, dtype=np.uint8)
    bp_succeeded = bool(attempt.converged and bp_candidate is not None)
    snapshots: tuple[FailedAttemptSnapshot, ...] = ()
    if bp_candidate is not None and not bp_succeeded:
        residual = (validated.hz @ bp_candidate) % 2
        snapshots = (FailedAttemptSnapshot(
            attempt_lineage_id=f"attempt-{shot_id}-0", working=working, candidate=bp_candidate,
            posterior_llr=np.asarray(sweep.beliefs, dtype=np.float64),
            original_residual_weight=int(np.count_nonzero(residual != observation.syndrome)),
            original_channel_nll=float(np.sum(np.abs(sweep.beliefs))), declared_attempt_ordinal=0,
        ),)
    enabled = bool(config.get("enabled"))
    processor = (LsdPostprocessor(method=str(config["method"]), order=int(config["order"])) if enabled else None)
    result = PostprocessingController(processor).execute(snapshots, bp_succeeded=bp_succeeded)
    final = (np.asarray(result.candidate, dtype=np.uint8) if result.status == "success" and result.candidate is not None
             else bp_candidate)
    evaluation = None if final is None else evaluator.evaluate_candidate(
        validated, true_x=hidden_truth.x, true_z=hidden_truth.z, candidate_x=final,
    )
    common = {**dict(context), "canonical_identity": identity, "schema_version": 8}
    with CanonicalEventWriter(path, structural_event_version=7) as ledger:
        ledger.begin(run_id=parsed.run_id, shot_id=shot_id, sample_seed_identity=sample_seed_identity, **common)
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="attempt", data={**common, "iterations": attempt.iterations})
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="bp_only", data={"candidate": None if bp_candidate is None else bp_candidate.tolist(), "converged": bp_succeeded})
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="fallback", data={"status": result.status, "native_calls": result.native_calls, "selected_attempt_lineage_id": result.selected_attempt_lineage_id, "stable_tie_order": list(result.stable_tie_order)})
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="final", data={"candidate": None if final is None else final.tolist(), "original_valid": result.original_valid})
        ledger.event(run_id=parsed.run_id, shot_id=shot_id, kind="work", data={"work_vector": budgets.summary("attempt").as_evidence(structural_event_version=2)})
        ledger.terminal(run_id=parsed.run_id, shot_id=shot_id, termination="completed_postprocessing", data={"bp_only_candidate": None if bp_candidate is None else bp_candidate.tolist(), "final_candidate": None if final is None else final.tolist(), "fallback_status": result.status, "outcome": None if evaluation is None else evaluation.outcome, "converged": bp_succeeded})
    return {"termination": "completed_postprocessing", "candidate": final, "evaluation": evaluation}


def validate_phase7_shot(events: list[dict[str, Any]], *, run_id: str, shot_id: int) -> None:
    """Independent V8 replay checks exact control-flow order and result split."""
    rows = [row for row in events if row["run_id"] == run_id and row["shot_id"] == shot_id]
    kinds = [row["kind"] for row in rows]
    expected = ["shot_begin", "attempt", "bp_only", "fallback", "final", "work", "termination"]
    if kinds != expected:
        raise ValueError("Phase 7 replay rejects altered event order or cardinality")
    terminal = rows[-1]["data"]
    if terminal["bp_only_candidate"] != rows[2]["data"]["candidate"] or terminal["final_candidate"] != rows[4]["data"]["candidate"]:
        raise ValueError("Phase 7 replay rejects BP-only/final evidence collapse")
