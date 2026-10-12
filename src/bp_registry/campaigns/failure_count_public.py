"""Public local failure-count reduction over sealed canonical attempts.

All projections in this module are rebuilt from the bounded runner's retained
sample, ledger, attempt, and partial receipts.  JSON merge and report files are
caches of that reduction, never substitutes for scientific evidence.
"""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .contracts import (
    FailureCountPartialAttemptV1, FailureCountTerminalReceiptV1,
    FailureCountWorkSpecV1, canonical_json_bytes,
)
from .execution import (
    _failure_count_executable_projection, _publish_bounded_cap_censor,
    _retained_bounded_actuals, run_canonical_bounded_batch,
)
from .planning import CampaignWorkPlan
from .statistics import exact_inverse_binomial_rate, multiplicative_target_decision


def _digest(value: object) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> str:
    raw = canonical_json_bytes(dict(payload)) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            raise ValueError("failure-count evidence conflicts with immutable bytes")
        return sha256(raw).hexdigest()
    descriptor, temporary_name = tempfile.mkstemp(prefix=".failure-count-public-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with open(descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256(raw).hexdigest()


def _ordered_projection(attempts: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [
        {"ordinal": ordinal, "unit_key": item["unit_key"],
         "receipt_sha256": item["receipt_sha256"],
         "logical_failure": item["terminal_fact"]["logical_failure"]}
        for ordinal, item in enumerate(attempts, 1)
    ]


def _target_ordinal(attempts: tuple[dict[str, Any], ...], target: int) -> int | None:
    failures = 0
    for ordinal, item in enumerate(attempts, 1):
        failure = item["terminal_fact"]["logical_failure"]
        if type(failure) is not bool:
            raise ValueError("canonical terminal lacks a boolean logical outcome")
        failures += failure
        if failures == target:
            return ordinal
    return None


def _target_receipt(
    *, plan: CampaignWorkPlan, attempts: tuple[dict[str, Any], ...],
    actuals: Mapping[str, int], walls: tuple[tuple[int, int, int], ...],
) -> FailureCountTerminalReceiptV1:
    spec = plan.work_spec
    assert isinstance(spec, FailureCountWorkSpecV1)
    policy = spec.policy
    terminal = _target_ordinal(attempts, policy.target_failures)
    if terminal is None:
        raise ValueError("target receipt requires the ordered target-th failure")
    batch_end = ((terminal - 1) // policy.batch_size + 1) * policy.batch_size
    if len(attempts) != batch_end:
        raise ValueError("target receipt requires exactly the verified terminal batch")
    ordered = _ordered_projection(attempts)
    tail = tuple(range(terminal + 1, len(attempts) + 1))
    receipt_path = None
    storage = actuals["storage_bytes"]
    for _ in range(8):
        receipt = FailureCountTerminalReceiptV1(
            schema="failure_count_terminal_receipt_v1",
            policy_sha256=policy.digest(), campaign_plan_sha256=policy.campaign_plan_sha256,
            executable_limit_receipt_sha256=policy.executable_limits.digest(),
            batch_authorization_sha256=policy.batch_authorization.digest(),
            terminal_state="target_reached", terminal_failure_ordinal=terminal,
            cumulative_failures=sum(item["logical_failure"] for item in ordered),
            total_completed_shots=len(attempts),
            inferential_prefix_sha256=_digest(ordered[:terminal]),
            authorized_tail_ordinals=tail,
            authorized_tail_sha256=_digest(ordered[terminal:]),
            first_exhausted_cap=None, realized_decoder_work=actuals["work"],
            realized_events=actuals["events"],
            realized_evidence_bytes=actuals["evidence_bytes"],
            realized_storage_bytes=storage, wall_boundaries=walls,
        ).validate_against(policy)
        envelope = {
            "schema": "failure_count_bounded_target_stop_v1",
            "campaign_plan_digest": plan.campaign_plan_digest,
            "terminal_receipt": receipt.model_dump(mode="json", by_alias=True),
        }
        receipt_path = canonical_json_bytes(envelope) + b"\n"
        next_storage = actuals["storage_bytes"] + len(receipt_path)
        if next_storage == storage:
            break
        storage = next_storage
    else:
        raise ValueError("target control receipt storage did not stabilize")
    if (len(receipt_path) > policy.executable_limits.partial_receipt_reserve_bytes
            or storage > policy.caps.max_storage_bytes):
        raise ValueError("target receipt does not fit the reserved control bytes")
    return receipt


def _wall_spent_ns(
    policy: Any, walls: tuple[tuple[int, int, int], ...],
    partial: FailureCountPartialAttemptV1 | None,
) -> int:
    timeout = policy.batch_authorization.per_unit_timeout_ns
    total = sum(max(0, observed - (deadline - timeout)) for deadline, observed, _ in walls)
    if partial is not None and partial.observed_ns is not None and partial.deadline_ns is not None:
        total += max(0, partial.observed_ns - (partial.deadline_ns - timeout))
    return total


def _next_cap(
    *, plan: CampaignWorkPlan, campaign_root: Path, actuals: Mapping[str, int],
    walls: tuple[tuple[int, int, int], ...], partial: FailureCountPartialAttemptV1 | None,
) -> str | None:
    policy = plan.work_spec.policy
    exhausted: set[str] = set()
    if (_wall_spent_ns(policy, walls, partial) >= int(policy.caps.max_wall_seconds * 1_000_000_000)
            or any(observed >= deadline for deadline, observed, _ in walls)
            or (partial is not None and partial.first_exhausted_cap == "wall" and partial.overshoot_ns)):
        exhausted.add("wall")
    next_ordinal = actuals["shots"] + 1
    if next_ordinal > policy.caps.max_shots or next_ordinal > len(plan.units):
        exhausted.add("shots")
    else:
        remaining = policy.batch_size - ((next_ordinal - 1) % policy.batch_size)
        if policy.dispatch_mode == "interruptible_unit":
            remaining = 1
        try:
            _failure_count_executable_projection(
                plan=plan, campaign_root=campaign_root, first_ordinal=next_ordinal,
                batch_size=remaining, accumulated=actuals,
            )
        except ValueError as error:
            prefix = "bounded canonical batch cannot fit hard resource cap: "
            if str(error).startswith(prefix):
                exhausted.add(str(error)[len(prefix):])
            else:
                raise
    return next((cap for cap in policy.cap_precedence if cap in exhausted), None)


def reconstruct_failure_count_state(
    *, plan: CampaignWorkPlan, campaign_root: Path, bounded_root: Path,
) -> dict[str, Any]:
    """Rebuild order, resources, interruption, and terminal evidence."""
    spec = plan.work_spec
    if not isinstance(spec, FailureCountWorkSpecV1):
        raise ValueError("failure-count replay requires a prospective work specification")
    if bounded_root.exists() and (bounded_root.is_symlink() or not bounded_root.is_dir()):
        raise ValueError("bounded evidence root must be a regular directory")
    actuals, attempts, walls = _retained_bounded_actuals(
        destination=bounded_root, campaign_root=campaign_root, plan=plan,
    )
    partial_paths = tuple(sorted((bounded_root / "attempts").glob("*/partial-attempt.json")))
    partial = None
    partial_digest = None
    pending_partials = []
    all_partials = []
    for path in partial_paths:
        candidate = FailureCountPartialAttemptV1.model_validate_json(path.read_bytes())
        all_partials.append(candidate)
        if candidate.attempt_ordinal > len(attempts) + 1:
            raise ValueError("partial attempt lies beyond the completed prefix")
        if candidate.attempt_ordinal == len(attempts) + 1:
            pending_partials.append(candidate)
    if pending_partials:
        partial = max(pending_partials, key=lambda item: item.attempt_sequence)
        partial_digest = partial.digest()
    ordered = _ordered_projection(attempts)
    hit = _target_ordinal(attempts, spec.policy.target_failures)
    target_path = bounded_root / "failure-count-target-stop.json"
    censor_path = bounded_root / "failure-count-cap-censor.json"
    if target_path.exists() and censor_path.exists():
        raise ValueError("failure-count evidence has competing terminal states")
    terminal = None
    terminal_path = None
    if target_path.exists():
        if target_path.is_symlink() or not target_path.is_file() or partial is not None:
            raise ValueError("target receipt requires regular completed evidence")
        terminal = _target_receipt(plan=plan, attempts=attempts, actuals=actuals, walls=walls)
        expected = {"schema": "failure_count_bounded_target_stop_v1",
                    "campaign_plan_digest": plan.campaign_plan_digest,
                    "terminal_receipt": terminal.model_dump(mode="json", by_alias=True)}
        if target_path.read_bytes() != canonical_json_bytes(expected) + b"\n":
            raise ValueError("target receipt differs from verified ordered evidence")
        terminal_path = target_path
    elif censor_path.exists():
        if censor_path.is_symlink() or not censor_path.is_file():
            raise ValueError("cap censor receipt must be a regular file")
        saved = json.loads(censor_path.read_bytes())
        if not isinstance(saved, dict) or saved.get("schema") != "failure_count_bounded_cap_censor_v1":
            raise ValueError("cap censor receipt has an invalid schema")
        if hit is not None and partial is None and len(attempts) >= ((hit - 1) // spec.policy.batch_size + 1) * spec.policy.batch_size:
            raise ValueError("cap censor cannot replace a verified reached target")
        claimed_cap = saved["terminal_receipt"].get("first_exhausted_cap")
        if claimed_cap != _next_cap(plan=plan, campaign_root=campaign_root, actuals=actuals, walls=walls, partial=partial):
            raise ValueError("cap censor does not match the first exhausted authorization")
        if saved.get("pending_ordinal") != len(attempts) + 1:
            raise ValueError("cap censor pending ordinal differs from verified prefix")
        if saved.get("retained_partial_attempt_sha256") != partial_digest:
            raise ValueError("cap censor differs from retained partial lineage")
        terminal, _, _ = _publish_bounded_cap_censor(
            destination=bounded_root, plan=plan, partial_digest=partial_digest,
            exhausted_cap=claimed_cap, actuals=actuals, terminals=attempts,
            walls=walls, pending_ordinal=len(attempts) + 1,
        )
        terminal_path = censor_path
    elif hit is not None and partial is None and len(attempts) >= ((hit - 1) // spec.policy.batch_size + 1) * spec.policy.batch_size:
        # A crash after terminal batch completion but before publication is
        # recoverable without dispatching another scientific shot.
        terminal = _target_receipt(plan=plan, attempts=attempts, actuals=actuals, walls=walls)
    return {
        "state": terminal.terminal_state if terminal_path is not None else "progress",
        "ordered": ordered, "attempts": attempts, "actuals": actuals, "walls": walls,
        "partial": partial, "partial_digest": partial_digest,
        "partial_attempts": tuple(sorted(all_partials, key=lambda item: (item.attempt_ordinal, item.attempt_sequence))),
        "terminal": terminal if terminal_path is not None else None,
        "terminal_path": terminal_path,
        "recoverable_target": terminal if terminal is not None and terminal_path is None else None,
        "next_cap": _next_cap(plan=plan, campaign_root=campaign_root, actuals=actuals, walls=walls, partial=partial)
        if terminal_path is None and (hit is None or terminal is None) else None,
    }


def dispatch_public_failure_count_batch(
    *, plan: CampaignWorkPlan, campaign_root: Path, bounded_root: Path,
) -> dict[str, Any]:
    """Dispatch one authorized next batch or recover a terminal control file."""
    state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    if state["terminal"] is not None:
        return state
    if state["recoverable_target"] is not None:
        receipt = state["recoverable_target"]
        _atomic_json(bounded_root / "failure-count-target-stop.json", {
            "schema": "failure_count_bounded_target_stop_v1",
            "campaign_plan_digest": plan.campaign_plan_digest,
            "terminal_receipt": receipt.model_dump(mode="json", by_alias=True),
        })
        return reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    if state["next_cap"] is not None:
        _publish_bounded_cap_censor(
            destination=bounded_root, plan=plan, partial_digest=state["partial_digest"],
            exhausted_cap=state["next_cap"], actuals=state["actuals"],
            terminals=state["attempts"], walls=state["walls"],
            pending_ordinal=len(state["attempts"]) + 1,
        )
        return reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    first = len(state["attempts"]) + 1
    policy = plan.work_spec.policy
    batch_size = policy.batch_size - ((first - 1) % policy.batch_size)
    if policy.dispatch_mode == "interruptible_unit":
        batch_size = 1
    run_canonical_bounded_batch(
        plan, campaign_root=campaign_root, output_root=bounded_root,
        first_ordinal=first, batch_size=batch_size,
        parent_partial_receipt_sha256=state["partial_digest"],
    )
    state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    if state["partial"] is not None:
        # The interruption itself is a durable, zero-credit progress state.
        # A later explicit resume decides whether a fresh attempt fits or the
        # accumulated cap must be sealed as censored.
        return state
    if state["recoverable_target"] is not None:
        receipt = state["recoverable_target"]
        _atomic_json(bounded_root / "failure-count-target-stop.json", {
            "schema": "failure_count_bounded_target_stop_v1",
            "campaign_plan_digest": plan.campaign_plan_digest,
            "terminal_receipt": receipt.model_dump(mode="json", by_alias=True),
        })
        state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    elif state["next_cap"] is not None:
        _publish_bounded_cap_censor(
            destination=bounded_root, plan=plan, partial_digest=state["partial_digest"],
            exhausted_cap=state["next_cap"], actuals=state["actuals"],
            terminals=state["attempts"], walls=state["walls"],
            pending_ordinal=len(state["attempts"]) + 1,
        )
        state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    return state


def failure_count_merge_payload(*, plan: CampaignWorkPlan, campaign_root: Path, bounded_root: Path) -> dict[str, Any]:
    state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    terminal_path = state["terminal_path"]
    byte_interruption = (state["partial"] is not None
                         and state["partial"].interruption_kind != "interrupted_wall")
    unsigned = {
        "schema": "failure_count_public_merge_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "policy_sha256": plan.work_spec.policy.digest(),
        "bounded_output_root": str(bounded_root.resolve(strict=True)),
        "state": state["state"], "ordered": state["ordered"],
        "partial_attempt_sha256": state["partial_digest"],
        "partial_attempt_lineage": [
            {"ordinal": item.attempt_ordinal, "sequence": item.attempt_sequence,
             "receipt_sha256": item.digest(), "parent_receipt_sha256": item.parent_partial_receipt_sha256,
             "kind": item.interruption_kind, "first_exhausted_cap": item.first_exhausted_cap}
            for item in state["partial_attempts"]
        ],
        "pending_ordinal": len(state["ordered"]) + 1 if state["state"] == "progress" else None,
        "terminal_receipt_sha256": sha256(terminal_path.read_bytes()).hexdigest() if terminal_path is not None else None,
        "actual_resources": {
            "completed_shots": state["actuals"]["shots"],
            "decoder_work": state["actuals"]["work"],
            "events": state["actuals"]["events"],
            "evidence_bytes": state["actuals"]["evidence_bytes"],
            "storage_bytes": (
                state["terminal"].realized_storage_bytes if state["terminal"] is not None
                else state["actuals"]["storage_bytes"]
            ),
            "wall_ns": None if byte_interruption else _wall_spent_ns(
                plan.work_spec.policy, state["walls"], state["partial"]),
            "wall_observation_status": (
                "unavailable_for_byte_interruption" if byte_interruption else "observed_boundaries"
            ),
        },
    }
    return {**unsigned, "merge_content_sha256": _digest(unsigned)}


def verify_failure_count_merge(
    *, payload: Mapping[str, Any], plan: CampaignWorkPlan, campaign_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root_value = payload.get("bounded_output_root")
    if not isinstance(root_value, str):
        raise ValueError("failure-count merge lacks its bounded evidence root")
    bounded_root = Path(root_value)
    if not bounded_root.is_dir() or bounded_root.is_symlink():
        raise ValueError("failure-count bounded evidence root is invalid")
    expected = failure_count_merge_payload(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    if dict(payload) != expected:
        raise ValueError("failure-count merge differs from sealed canonical evidence")
    state = reconstruct_failure_count_state(plan=plan, campaign_root=campaign_root, bounded_root=bounded_root)
    return expected, state


def failure_count_report_payload(
    *, plan: CampaignWorkPlan, merge: Mapping[str, Any], state: Mapping[str, Any],
) -> dict[str, Any]:
    spec = plan.work_spec
    assert isinstance(spec, FailureCountWorkSpecV1)
    policy = spec.policy
    terminal = state["terminal"]
    rate = exact_inverse_binomial_rate(policy=policy, terminal_receipt=terminal) if terminal is not None and terminal.terminal_state == "target_reached" else None
    targets = spec.campaign_work_spec.assessment.targets
    if len(targets) != 1:
        raise ValueError("public one-arm failure-count assessment requires one frozen target")
    target = targets[0]
    source_denominator = spec.campaign_work_spec.source_denominators.get(target.target_id)
    requires_denominator = spec.campaign_work_spec.source_denominator_required_by_target.get(target.target_id, False)
    decision = None
    if terminal is not None:
        decision = multiplicative_target_decision(
            rate, target, policy.multiplicative_rule,
            input_receipt_hashes={"merge": merge["merge_content_sha256"],
                                  "terminal": merge["terminal_receipt_sha256"]},
            source_denominator_required=requires_denominator,
            source_denominator=source_denominator,
            evidence_status="cap_censored" if terminal.terminal_state == "cap_censored" else None,
        )
    unsigned = {
        "schema": "failure_count_campaign_report_v1",
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "policy_sha256": policy.digest(),
        "merge_receipt_sha256": merge["merge_content_sha256"],
        "assessment_status": (
            "not_assessed" if terminal is None else
            "inconclusive_cap_censored" if terminal.terminal_state == "cap_censored" else
            "evidence_reconstructed"
        ),
        "terminal_state": terminal.terminal_state if terminal is not None else None,
        "total_completed_shots": len(state["ordered"]),
        "cumulative_failures": sum(item["logical_failure"] for item in state["ordered"]),
        "terminal_failure_ordinal": terminal.terminal_failure_ordinal if terminal is not None else None,
        "inferential_failures": policy.target_failures if rate is not None else None,
        "inferential_nonfailures": (terminal.terminal_failure_ordinal - policy.target_failures) if rate is not None else None,
        "inferential_prefix_sha256": terminal.inferential_prefix_sha256 if terminal is not None else None,
        "authorized_tail_ordinals": list(terminal.authorized_tail_ordinals) if terminal is not None else [],
        "authorized_tail_sha256": terminal.authorized_tail_sha256 if terminal is not None else None,
        "first_exhausted_cap": terminal.first_exhausted_cap if terminal is not None else None,
        "target_id": target.target_id,
        "target_receipt_sha256": target.target_receipt_sha256,
        "decision_rule": policy.multiplicative_rule.model_dump(mode="json", by_alias=True),
        "inverse_binomial_rate": asdict(rate) if rate is not None else None,
        "target_decision": asdict(decision) if decision is not None else None,
        "actual_resources": merge["actual_resources"],
        "wall_boundaries": [list(item) for item in state["walls"]],
        "partial_attempt_sha256": state["partial_digest"],
        "partial_attempt_lineage": merge["partial_attempt_lineage"],
        "pending_interruption": (
            None if state["partial"] is None else {
                "kind": state["partial"].interruption_kind,
                "first_exhausted_cap": state["partial"].first_exhausted_cap,
                "pending_ordinal": state["partial"].attempt_ordinal,
                "deadline_ns": state["partial"].deadline_ns,
                "observed_ns": state["partial"].observed_ns,
                "overshoot_ns": state["partial"].overshoot_ns,
                "consumed_decoder_work": state["partial"].consumed_decoder_work,
                "consumed_events": state["partial"].consumed_events,
                "consumed_evidence_bytes": state["partial"].consumed_evidence_bytes,
                "consumed_storage_bytes": state["partial"].consumed_storage_bytes,
                "consumed_control_receipt_bytes": state["partial"].consumed_control_receipt_bytes,
                "completed_shot_credit": state["partial"].completed_shot_credit,
                "failure_credit": state["partial"].failure_credit,
            }
        ),
    }
    return {**unsigned, "report_sha256": _digest(unsigned)}
