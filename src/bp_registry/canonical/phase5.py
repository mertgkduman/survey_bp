"""Truth-free dispatch and deterministic evidence projection for public Phase 5 shots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
from typing import Any

import numpy as np

from .budgets import BudgetTree, WorkVector
from .contracts import Phase5InterventionContract
from .guided_decimation import GuidedDecimationController
from .impulse import ImpulseController, ImpulseSpec
from .intervention_session import BpSession
from .interventions import (
    FreezingController, FreezingSpec, SignFlipController, SignFlipSpec,
    SyndromeFlipController, SyndromeFlipSpec,
)
from .problems import OriginalProblem
from .restarting import RestartController, RestartSpec
from .schedules import EdgeTable


@dataclass(frozen=True, slots=True)
class Phase5Outcome:
    candidate: tuple[int, ...] | None
    termination: str
    qualification: str
    selected_origin: object
    header: dict[str, Any]
    branches: tuple[dict[str, Any], ...]
    attempts: tuple[dict[str, Any], ...]
    work: WorkVector
    leaves: tuple[tuple[str, str, WorkVector], ...]


def _json(value: object) -> Any:
    """Normalize typed control facts to finite JSON before ledger ownership."""
    if is_dataclass(value):
        value = asdict(value)
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))


def _project(result: object, *, rows_field: str | None, candidate_field: str, origin_field: str | None = None) -> Phase5Outcome:
    data = _json(result)
    work = result.work
    leaves = result.leaves
    if not isinstance(work, WorkVector):
        raise ValueError("Phase 5 controller did not return typed work")
    rows = tuple(data.pop(rows_field)) if rows_field is not None else (
        {
            "order": 0,
            "target_index": data.get("target_index"),
            "trigger": data.get("trigger"),
            "action_state_digest": data.get("action_state_digest"),
            "continuation_state_digest": data.get("continuation_state_digest"),
            "prior_before": data.get("prior_before"),
            "prior_after": data.get("prior_after"),
            "v2c_preserved": data.get("v2c_before") == data.get("v2c_after_action"),
            "c2v_preserved": data.get("c2v_before") == data.get("c2v_after_action"),
            "termination": data.get("termination"),
        },
    )
    branches: tuple[dict[str, Any], ...] = ()
    if rows_field == "branches":
        branch_rows: list[dict[str, Any]] = []
        attempt_rows: list[dict[str, Any]] = []
        for branch in rows:
            residuals = branch.pop("residuals")
            branch_rows.append(branch)
            attempt_rows.extend({"branch_order": branch["order"], "branch_lineage_id": branch["lineage_id"], **row} for row in residuals)
        branches = tuple(branch_rows)
        rows = tuple(attempt_rows)
    data.pop("work", None)
    data.pop("leaves", None)
    data["qualification"] = result.qualification
    return Phase5Outcome(
        None if getattr(result, candidate_field) is None else tuple(int(bit) for bit in getattr(result, candidate_field)),
        result.termination,
        result.qualification,
        None if origin_field is None else _json(getattr(result, origin_field)),
        data, branches, rows, work, leaves,
    )


def _identity_baseline(
    original: OriginalProblem, error_rate: float, budgets: BudgetTree,
    max_iterations: int, owner_identity: str,
) -> Phase5Outcome:
    session = BpSession(
        EdgeTable.from_check_matrix(original.hz), original.syndrome,
        error_rate=error_rate, owner_identity=owner_identity,
    )
    initial = session.state.digest
    rows: list[dict[str, Any]] = []
    candidate = None
    termination = "iteration_cap_reached"
    for index in range(max_iterations):
        before = session.state.digest
        try:
            moved = session.advance(
                budgets=budgets, leaf_id=f"{owner_identity}:baseline:sweep:{index}", bp_call_start=index == 0,
            )
        except (ValueError, FloatingPointError):
            termination = "numerical_failure"
            rows.append({"index": index, "state_before": before, "state_after": session.state.digest,
                         "sweep_leaf": None, "validation_leaf": None, "original_valid": None, "termination": termination})
            break
        if not moved.admitted:
            termination = moved.termination or "count_budget_exhausted"
            rows.append({"index": index, "state_before": before, "state_after": session.state.digest,
                         "sweep_leaf": None, "validation_leaf": None, "original_valid": None, "termination": termination})
            break
        check_leaf = f"{owner_identity}:baseline:original-check:{index}"
        reservation = budgets.reserve("attempt", WorkVector(original_checks=1), leaf_id=check_leaf)
        if reservation is None:
            termination = "count_budget_exhausted"
            rows.append({"index": index, "state_before": before, "state_after": session.state.digest,
                         "sweep_leaf": moved.leaf_id, "validation_leaf": None, "original_valid": None, "termination": termination})
            break
        try:
            valid = session.original_syndrome_valid(original.hz)
        except BaseException:
            reservation.rollback()
            raise
        reservation.commit_once()
        rows.append({"index": index, "state_before": before, "state_after": session.state.digest,
                     "sweep_leaf": moved.leaf_id, "validation_leaf": check_leaf, "original_valid": valid,
                     "candidate": [int(bit) for bit in session.state.candidate], "termination": None})
        if valid:
            candidate = tuple(int(bit) for bit in session.state.candidate)
            termination = "baseline_valid"
            break
    header = {
        "owner_identity": owner_identity, "initial_state_digest": initial,
        "final_state_digest": session.state.digest,
        "diagnostic_candidate": [int(bit) for bit in session.state.candidate],
        "qualification": "canonical_implemented", "termination": termination,
    }
    return Phase5Outcome(
        candidate, termination, "canonical_implemented", None, header, (), tuple(rows),
        budgets.summary("attempt"), budgets.leaf_events(),
    )


def execute_phase5_controller(
    spec: Phase5InterventionContract, original: OriginalProblem,
    *, error_rate: float, budgets: BudgetTree, max_iterations: int,
    owner_identity: str,
) -> Phase5Outcome:
    """Dispatch one declared family; no controller receives physical or logical truth."""
    if spec.kind == "identity":
        return _identity_baseline(original, error_rate, budgets, max_iterations, owner_identity)
    if spec.kind == "guided_decimation":
        session = BpSession(
            EdgeTable.from_check_matrix(original.hz), original.syndrome,
            error_rate=error_rate, owner_identity=owner_identity,
        )
        result = GuidedDecimationController({
            "kind": "guided_decimation", "variant": spec.variant,
            "source_revision": spec.source_revision,
            "finite_bias_magnitude": spec.finite_bias_magnitude,
            "zero_rule": spec.zero_rule, "final_round_rule": spec.final_round_rule,
            "round_limit": spec.round_limit, "sweeps_per_round": spec.sweeps_per_round,
        }).run(session, check_matrix=original.hz, budgets=budgets)
        return _project(result, rows_field="rounds", candidate_field="candidate")
    if spec.kind == "impulse":
        result = ImpulseController(ImpulseSpec(
            realization=spec.realization, selection=spec.selection,
            baseline_sweeps=spec.baseline_sweeps, attempt_sweeps=spec.attempt_sweeps,
            attempt_cap=spec.attempt_cap, coordinate_order=spec.coordinate_order,
        )).run(original, error_rate=error_rate, budgets=budgets, owner_identity=owner_identity)
        return _project(result, rows_field="attempts", candidate_field="selected_candidate", origin_field="selected_origin")
    if spec.kind == "freezing":
        result = FreezingController(FreezingSpec(
            period_sweeps=spec.period_sweeps, lifetime_sweeps=spec.lifetime_sweeps,
            retry_cap=spec.retry_cap, root_seed=spec.root_seed,
        )).run(original, error_rate=error_rate, budgets=budgets)
        return _project(result, rows_field="trials", candidate_field="selected_candidate")
    if spec.kind == "syndrome_flip":
        result = SyndromeFlipController(SyndromeFlipSpec(
            baseline_sweeps=spec.baseline_sweeps, attempt_sweeps=spec.attempt_sweeps,
            top_k=spec.top_k, max_weight=spec.max_weight, test_cap=spec.test_cap,
            root_seed=spec.root_seed,
        )).run(original, error_rate=error_rate, budgets=budgets)
        return _project(result, rows_field="tests", candidate_field="selected_candidate", origin_field="selected_test_order")
    if spec.kind == "sign_flip":
        result = SignFlipController(SignFlipSpec(
            alpha=spec.alpha, trunk_sweeps=spec.trunk_sweeps,
            continuation_sweeps=spec.continuation_sweeps,
        )).run(original, error_rate=error_rate, budgets=budgets)
        return _project(result, rows_field=None, candidate_field="selected_candidate", origin_field="target_index")
    if spec.kind == "restart_belief":
        result = RestartController(RestartSpec(
            preset=spec.preset, code_id=spec.code_id, eta=spec.eta, t_cap=spec.t_cap,
            root_sweeps=spec.root_sweeps, residual_sweeps=spec.residual_sweeps,
            exact_distance=spec.exact_distance,
        )).run(original, error_rate=error_rate, budgets=budgets)
        return _project(result, rows_field="branches", candidate_field="selected_candidate", origin_field="selected_origin")
    raise ValueError("unregistered Phase 5 intervention kind")


def phase5_work_evidence(outcome: Phase5Outcome) -> dict[str, Any]:
    leaves = [
        {"leaf_id": leaf_id, "scope": scope, "work_vector": delta.as_evidence(structural_event_version=4)}
        for leaf_id, scope, delta in outcome.leaves
    ]
    return {"work_vector": outcome.work.as_evidence(structural_event_version=4), "leaves": leaves}


def phase5_attempt_events(spec: Phase5InterventionContract, outcome: Phase5Outcome) -> tuple[tuple[str, dict[str, Any]], ...]:
    """Expose each declared transform, attempt, lift, and original check in order."""
    events: list[tuple[str, dict[str, Any]]] = []
    target_fields = (
        "target_index", "selected_target", "test_vector", "transformed_syndrome",
        "working_lineage_id", "branch_lineage_id", "residual_lineage_id",
        "proposal_lineage", "root_target", "realization", "forced_value",
    )
    for index, row in enumerate(outcome.attempts):
        target = {name: row[name] for name in target_fields if name in row}
        events.append(("transform", {
            "attempt_order": index, "operator": spec.operator,
            "reset_rule": spec.reset_rule, "target": target,
        }))
        events.append(("attempt", row))
        events.append(("lift", {
            "attempt_order": index, "lift_rule": spec.lift_rule,
            "lift_digest": row.get("lift_digest", row.get("lift_digests")),
            "lifted_candidate": row.get("lifted_candidate"),
            "termination": row.get("termination", row.get("terminal_reason")),
        }))
        validity = row.get("original_valid", row.get("original_syndrome_valid"))
        if validity is not None:
            events.append(("original_check", {
                "attempt_order": index, "valid": validity,
                "candidate": row.get("lifted_candidate", row.get("candidate")),
            }))
    return tuple(events)
