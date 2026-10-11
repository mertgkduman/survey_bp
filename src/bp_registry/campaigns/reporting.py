"""Reconstruct campaign assessment reports from sealed merge evidence only.

The report layer deliberately consumes the merge receipt produced from verified
shards.  It has no path for shard summary counters: terminal facts are counted
again against the frozen work plan, and every report remains replayable from
the same immutable receipt bytes and frozen assessment inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Literal, Mapping, Sequence

from .contracts import CampaignAssessmentV1, TargetReferenceV1, canonical_json_bytes
from .planning import CampaignWorkPlan, UnitKey
from .statistics import (
    CampaignTerminalOutcomeV1,
    ExactBinomialRateV1,
    FiniteLookObservationV1,
    PairedArmOutcomeV1,
    PairedCompletionSummaryV1,
    PairedOutcomeTableV1,
    TargetIntervalDecisionV1,
    exact_binomial_rate,
    finite_look_assessment,
    paired_completion_summary,
    paired_outcome_table,
    target_interval_decision,
)


_SHA256_LENGTH = 64
_ALL_SHOT_FAILURES = frozenset({
    "wrong_logical_action", "invalid_syndrome", "no_proposal", "nonconvergence",
    "timeout", "postselected_rejection",
})
_TERMINAL_STATUSES = frozenset({
    "exact", "stabilizer_equivalent", *_ALL_SHOT_FAILURES,
    "infrastructure_interruption",
})
_MISSING_WORK_DIMENSIONS = (
    "iterations", "bp_calls", "message_work", "branch_work", "relay_work",
    "candidate_work", "fallback_work", "runtime", "cpu", "memory", "shard_bytes",
    "parallel_allocation",
)
_THREAD_ENVIRONMENT = frozenset({
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
})


def _sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str) or len(value) != _SHA256_LENGTH or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _immutable_hashes(
    *, plan: CampaignWorkPlan, assessment: CampaignAssessmentV1,
    merge_receipt: Mapping[str, Any], input_receipt_hashes: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    """Verify all report inputs before terminal evidence becomes a denominator."""
    if not isinstance(plan, CampaignWorkPlan):
        raise ValueError("report reconstruction requires a frozen CampaignWorkPlan")
    if not isinstance(assessment, CampaignAssessmentV1):
        raise ValueError("report reconstruction requires a frozen CampaignAssessmentV1")
    if not isinstance(input_receipt_hashes, Mapping):
        raise ValueError("report input receipt hashes must be a mapping")
    hashes = tuple(sorted((str(name), _sha256(digest, name=f"input receipt {name}"))
                          for name, digest in input_receipt_hashes.items()))
    supplied = dict(hashes)
    expected = {
        "campaign": plan.campaign_spec_digest,
        "plan": plan.campaign_plan_digest,
        "assessment": assessment.digest(),
        "merge": merge_receipt.get("receipt_sha256"),
    }
    for target in assessment.targets:
        expected[f"target:{target.target_id}"] = target.target_receipt_sha256
    if any(supplied.get(name) != value for name, value in expected.items()):
        raise ValueError("report input receipt hashes differ from frozen evidence")
    return hashes


def _verified_merge(*, plan: CampaignWorkPlan, merge_receipt: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Validate the canonical merge byte snapshot and bind facts to plan units."""
    if not isinstance(merge_receipt, Mapping):
        raise ValueError("report requires a validated campaign merge receipt")
    receipt = dict(merge_receipt)
    required = {
        "schema", "campaign_plan_digest", "terminal_unit_keys", "explicit_final_nonterminal_keys",
        "incomplete_unit_keys", "authorized_undispatched_keys", "unexpected_unit_keys",
        "redundant_attempt_receipt_hashes", "conflicting_unit_keys", "missing_unit_keys",
        "attempt_receipt_hashes", "stop_receipt_hashes", "terminal_facts", "events",
        "receipt_bytes", "receipt_sha256",
    }
    if set(receipt) != required or receipt.get("schema") != "campaign_merge_receipt_v1":
        raise ValueError("report requires an exact validated merge receipt")
    if receipt["campaign_plan_digest"] != plan.campaign_plan_digest:
        raise ValueError("merge receipt differs from frozen campaign plan")
    payload = {name: value for name, value in receipt.items() if name not in {"receipt_bytes", "receipt_sha256"}}
    bytes_value = receipt["receipt_bytes"]
    if not isinstance(bytes_value, bytes) or canonical_json_bytes(payload) != bytes_value:
        raise ValueError("merge receipt canonical bytes differ from reported evidence")
    if sha256(bytes_value).hexdigest() != _sha256(receipt["receipt_sha256"], name="merge receipt"):
        raise ValueError("merge receipt hash differs from canonical bytes")
    expected_units = {unit.key: unit for unit in plan.units}
    terminals = receipt["terminal_facts"]
    terminal_keys = receipt["terminal_unit_keys"]
    if not isinstance(terminals, list) or not isinstance(terminal_keys, list):
        raise ValueError("merge receipt terminal evidence has an invalid shape")
    if terminal_keys != [item.get("unit_key") for item in terminals]:
        raise ValueError("merge receipt terminal key order differs from terminal evidence")
    if len(set(terminal_keys)) != len(terminal_keys) or any(key not in expected_units for key in terminal_keys):
        raise ValueError("merge receipt terminal evidence is not a unique plan subset")
    terminal_set = set(terminal_keys)
    for field in (
        "explicit_final_nonterminal_keys", "incomplete_unit_keys", "authorized_undispatched_keys",
        "unexpected_unit_keys", "conflicting_unit_keys", "missing_unit_keys",
    ):
        values = receipt[field]
        if not isinstance(values, list) or len(values) != len(set(values)):
            raise ValueError("merge receipt coverage evidence has an invalid shape")
    if receipt["unexpected_unit_keys"] or receipt["conflicting_unit_keys"]:
        raise ValueError("merge receipt contains unexpected or conflicting evidence")
    reconstructed: list[dict[str, Any]] = []
    for terminal in terminals:
        if not isinstance(terminal, Mapping) or set(terminal) != {
            "unit_key", "termination", "outcome", "logical_failure",
        }:
            raise ValueError("merge terminal fact has an invalid field set")
        unit = expected_units[terminal["unit_key"]]
        if terminal["outcome"] not in _TERMINAL_STATUSES or type(terminal["logical_failure"]) is not bool:
            raise ValueError("merge terminal fact has an invalid outcome")
        if terminal["logical_failure"] != (terminal["outcome"] not in {"exact", "stabilizer_equivalent"}):
            raise ValueError("merge terminal logical failure differs from outcome")
        reconstructed.append({"unit": unit, "terminal": dict(terminal)})
    return tuple(reconstructed)


@dataclass(frozen=True, slots=True)
class WorkAndResourceReportV1:
    """Separate observed work dimensions from explicitly unavailable measurements."""

    work_vectors: tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
    unavailable: tuple[tuple[str, str], ...]
    observations: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class PointReportV1:
    point_id: str
    planned_samples: int
    dispatched_samples: int
    terminal_samples: int
    incomplete_samples: int
    accepted_samples: int
    conditional_samples: int
    status_counts: tuple[tuple[str, int], ...]
    all_shot: ExactBinomialRateV1
    pair_status: Literal["complete", "inconclusive_incomplete_pairs", "not_applicable"]
    paired: PairedOutcomeTableV1 | None
    work_and_resources: WorkAndResourceReportV1


@dataclass(frozen=True, slots=True)
class CampaignReportV1:
    """A byte-replayable campaign report; observations never enter its verdict."""

    schema: Literal["campaign_report_v1"]
    status: Literal["complete", "inconclusive"]
    inconclusive_reasons: tuple[str, ...]
    input_receipt_hashes: tuple[tuple[str, str], ...]
    point_reports: tuple[PointReportV1, ...]
    verdicts: Mapping[str, TargetIntervalDecisionV1]
    stopping: Mapping[str, Any]
    report_sha256: str

    def semantic_bytes(self) -> bytes:
        payload = asdict(self)
        payload.pop("report_sha256")
        return canonical_json_bytes(payload)


def _source_denominator(
    *, target_id: str, required: Mapping[str, bool], values: Mapping[str, int | None],
) -> tuple[bool, int | None]:
    required_value = required.get(target_id, False)
    if type(required_value) is not bool:
        raise ValueError("source denominator requirements must be bools")
    value = values.get(target_id)
    if value is not None and (type(value) is not int or value < 1):
        raise ValueError("source denominator must be a positive integer when observed")
    return required_value, value


def _work_and_resources(
    *, terminal_rows: Sequence[dict[str, Any]], work_vectors_by_unit: Mapping[str, Mapping[str, int]] | None,
    observations: Mapping[str, Any] | None,
) -> WorkAndResourceReportV1:
    vectors: list[tuple[str, tuple[tuple[str, int], ...]]] = []
    unavailable = {dimension: "not present in verified merge terminal evidence" for dimension in _MISSING_WORK_DIMENSIONS}
    provided = work_vectors_by_unit or {}
    if not isinstance(provided, Mapping):
        raise ValueError("work vectors must be a mapping when supplied")
    terminal_keys = {row["unit"].key for row in terminal_rows}
    if set(provided) - terminal_keys:
        raise ValueError("work vector refers to a unit absent from verified terminals")
    for key in sorted(provided):
        vector = provided[key]
        if not isinstance(vector, Mapping) or not vector:
            raise ValueError("each observed work vector must be a nonempty mapping")
        checked: list[tuple[str, int]] = []
        for dimension, value in vector.items():
            if not isinstance(dimension, str) or not dimension or type(value) is not int or value < 0:
                raise ValueError("work-vector dimensions must be named nonnegative integers")
            checked.append((dimension, value))
            unavailable.pop(dimension, None)
        vectors.append((key, tuple(sorted(checked))))
    allowed_observations = {"environment", "timing", "resources", "parallel_allocation"}
    supplied_observations = observations or {}
    if not isinstance(supplied_observations, Mapping) or set(supplied_observations) - allowed_observations:
        raise ValueError("report observations must use the allowlisted operational fields")
    environment = supplied_observations.get("environment")
    if environment is not None:
        if not isinstance(environment, Mapping) or set(environment) - _THREAD_ENVIRONMENT or any(
            not isinstance(value, str) or not value.isdecimal() or int(value) < 1
            for value in environment.values()
        ):
            raise ValueError("environment observations must use allowlisted positive thread settings")
    timing = supplied_observations.get("timing")
    if timing is not None:
        if not isinstance(timing, Mapping) or set(timing) - {"wall_time_ns", "cpu_time_ns"} or any(
            type(value) is not int or value < 0 for value in timing.values()
        ):
            raise ValueError("timing observations must contain allowlisted nonnegative measurements")
        if "wall_time_ns" in timing:
            unavailable.pop("runtime", None)
        if "cpu_time_ns" in timing:
            unavailable.pop("cpu", None)
    resources = supplied_observations.get("resources")
    if resources is not None:
        resource_names = {"cpu_time_ns": "cpu", "memory_bytes": "memory", "shard_bytes": "shard_bytes"}
        if not isinstance(resources, Mapping) or set(resources) - set(resource_names) or any(
            type(value) is not int or value < 0 for value in resources.values()
        ):
            raise ValueError("resource observations must contain allowlisted nonnegative measurements")
        for name in resources:
            unavailable.pop(resource_names[name], None)
    allocation = supplied_observations.get("parallel_allocation")
    if allocation is not None:
        if not isinstance(allocation, Mapping) or set(allocation) - {"workers", "tasks"} or any(
            type(value) is not int or value < 1 for value in allocation.values()
        ):
            raise ValueError("parallel allocation must contain allowlisted positive measurements")
        unavailable.pop("parallel_allocation", None)
    return WorkAndResourceReportV1(
        work_vectors=tuple(vectors), unavailable=tuple(sorted(unavailable.items())),
        observations=tuple(sorted((str(name), value) for name, value in supplied_observations.items())),
    )


def reconstruct_campaign_report(
    *, plan: CampaignWorkPlan, assessment: CampaignAssessmentV1, merge_receipt: Mapping[str, Any],
    input_receipt_hashes: Mapping[str, str], source_denominator_required_by_target: Mapping[str, bool] | None = None,
    source_denominators: Mapping[str, int | None] | None = None,
    target_arm_ids: Mapping[str, str] | None = None,
    work_vectors_by_unit: Mapping[str, Mapping[str, int]] | None = None,
    observations: Mapping[str, Any] | None = None,
) -> CampaignReportV1:
    """Recompute all report rows from a verified merge receipt and frozen inputs."""
    hashes = _immutable_hashes(plan=plan, assessment=assessment, merge_receipt=merge_receipt,
                              input_receipt_hashes=input_receipt_hashes)
    terminal_rows = _verified_merge(plan=plan, merge_receipt=merge_receipt)
    if not terminal_rows:
        raise ValueError("report cannot compute an interval without verified terminal evidence")
    treatments = {item.terminal_status: item for item in assessment.outcome_matrix.treatments}
    required = source_denominator_required_by_target or {}
    source_counts = source_denominators or {}
    target_arms = target_arm_ids or {}
    if set(required) - {target.target_id for target in assessment.targets} or set(source_counts) - {target.target_id for target in assessment.targets}:
        raise ValueError("source denominator evidence names an undeclared target")
    rows_by_point: dict[str, list[dict[str, Any]]] = {}
    for row in terminal_rows:
        rows_by_point.setdefault(row["unit"].point_id, []).append(row)
    all_plan_by_point: dict[str, list[UnitKey]] = {}
    for unit in plan.units:
        all_plan_by_point.setdefault(unit.point_id, []).append(unit)
    report_points: list[PointReportV1] = []
    rate_by_point: dict[str, ExactBinomialRateV1] = {}
    for point_id, point_units in sorted(all_plan_by_point.items()):
        rows = rows_by_point.get(point_id, [])
        statuses: dict[str, int] = {}
        terminal_count = 0
        accepted = 0
        failures = 0
        paired_outcomes: list[PairedArmOutcomeV1] = []
        for row in rows:
            unit, terminal = row["unit"], row["terminal"]
            status = terminal["outcome"]
            statuses[status] = statuses.get(status, 0) + 1
            if treatments[status].all_shot != "incomplete":
                terminal_count += 1
                failures += int(treatments[status].all_shot == "failure")
                accepted += int(treatments[status].conditional == "accepted")
            paired_outcomes.append(PairedArmOutcomeV1(
                campaign_spec_digest=plan.campaign_spec_digest, cohort_id=unit.cohort_id,
                point_id=point_id, sample_identity=unit.physical_sample_identity,
                arm_id=unit.arm_id, terminal_status=status,
            ))
        if not terminal_count:
            raise ValueError("report point has no completed all-shot terminals")
        rate = exact_binomial_rate(
            failures=failures, shots=terminal_count, alpha=1.0 - assessment.interval.confidence_level,
            count_receipt_sha256=dict(hashes)["merge"],
        )
        rate_by_point[point_id] = rate
        arm_ids = tuple(sorted({unit.arm_id for unit in point_units}))
        paired: PairedOutcomeTableV1 | None = None
        pair_status: Literal["complete", "inconclusive_incomplete_pairs", "not_applicable"] = "not_applicable"
        if len(arm_ids) == 2:
            completion: PairedCompletionSummaryV1 = paired_completion_summary(
                outcomes=paired_outcomes, arm_ids=(arm_ids[0], arm_ids[1]),
                outcome_matrix=assessment.outcome_matrix,
            )
            pair_status = completion.paired_inference_status
            if pair_status == "complete":
                paired = paired_outcome_table(
                    outcomes=paired_outcomes, arm_ids=(arm_ids[0], arm_ids[1]),
                    alpha=assessment.families[0].alpha, count_receipt_sha256=dict(hashes)["merge"],
                    outcome_matrix=assessment.outcome_matrix,
                )
        report_points.append(PointReportV1(
            point_id=point_id, planned_samples=len(point_units), dispatched_samples=len(rows),
            terminal_samples=terminal_count, incomplete_samples=len(rows) - terminal_count,
            accepted_samples=accepted, conditional_samples=accepted,
            status_counts=tuple(sorted(statuses.items())), all_shot=rate, pair_status=pair_status,
            paired=paired, work_and_resources=_work_and_resources(
                terminal_rows=rows, work_vectors_by_unit=work_vectors_by_unit, observations=observations,
            ),
        ))
    target_rates: dict[str, ExactBinomialRateV1] = {}
    target_arms_by_id: dict[str, str] = {}
    for target in assessment.targets:
        matching = rows_by_point.get(target.target_id, [])
        point_arms = sorted({row["unit"].arm_id for row in matching})
        selected_arm = target_arms.get(target.target_id)
        if selected_arm is None and len(point_arms) != 1:
            raise ValueError("each multi-arm assessment target requires its explicit arm ID")
        if selected_arm is not None:
            if selected_arm not in point_arms:
                raise ValueError("assessment target arm has no verified terminal evidence")
            matching = [row for row in matching if row["unit"].arm_id == selected_arm]
        target_arms_by_id[target.target_id] = selected_arm or point_arms[0]
        completed = [
            row for row in matching
            if treatments[row["terminal"]["outcome"]].all_shot != "incomplete"
        ]
        if not completed:
            raise ValueError("assessment target has no completed all-shot terminals")
        target_rates[target.target_id] = exact_binomial_rate(
            failures=sum(treatments[row["terminal"]["outcome"]].all_shot == "failure" for row in completed),
            shots=len(completed), alpha=1.0 - assessment.interval.confidence_level,
            count_receipt_sha256=dict(hashes)["merge"],
        )
    verdicts: dict[str, TargetIntervalDecisionV1] = {}
    reasons: list[str] = []
    merge_incomplete = any(merge_receipt[field] for field in (
        "explicit_final_nonterminal_keys", "incomplete_unit_keys", "missing_unit_keys",
    ))
    if merge_incomplete:
        reasons.append("incomplete_verified_merge_evidence")
    if any(point.pair_status == "inconclusive_incomplete_pairs" for point in report_points):
        reasons.append("incomplete_required_pairs")
    stopping: dict[str, Any] = {
        "mode": assessment.stopping.mode,
        "planned": (
            assessment.stopping.final_shots if assessment.stopping.mode == "fixed_shot"
            else list(assessment.stopping.cumulative_looks)
        ),
        "realized_terminals_by_point": {point.point_id: point.terminal_samples for point in report_points},
        "authorized_undispatched": tuple(merge_receipt["authorized_undispatched_keys"]),
    }
    if assessment.stopping.mode == "finite_look":
        terminal_by_key = {row["unit"].key: row["terminal"] for row in terminal_rows}
        observations_for_looks: list[FiniteLookObservationV1] = []
        for look_index, boundary in enumerate(assessment.stopping.cumulative_looks, start=1):
            prefix = set(plan.completed_prefix(look_index))
            counts: dict[str, tuple[int, int, int]] = {}
            for target in assessment.targets:
                planned_units = [
                    unit for unit in plan.units
                    if unit.key in prefix and unit.point_id == target.target_id
                    and unit.arm_id == target_arms_by_id[target.target_id]
                ]
                completed_statuses = [
                    terminal_by_key[unit.key]["outcome"] for unit in planned_units
                    if unit.key in terminal_by_key
                    and treatments[terminal_by_key[unit.key]["outcome"]].all_shot != "incomplete"
                ]
                counts[target.target_id] = (
                    len(planned_units), len(completed_statuses),
                    sum(treatments[status].all_shot == "failure" for status in completed_statuses),
                )
            dispatched_counts = {item[0] for item in counts.values()}
            realized_counts = {item[1] for item in counts.values()}
            if len(dispatched_counts) != 1 or len(realized_counts) != 1:
                raise ValueError("finite-look report requires equal target denominators at each declared look")
            dispatched = dispatched_counts.pop()
            realized = realized_counts.pop()
            if dispatched != boundary:
                raise ValueError("finite-look report target denominator differs from frozen look boundary")
            observations_for_looks.append(FiniteLookObservationV1(
                look=boundary, dispatched_shots=dispatched, realized_shots=realized,
                failures_by_target={target_id: values[2] for target_id, values in counts.items()},
                count_receipt_sha256_by_target={target.target_id: dict(hashes)["merge"] for target in assessment.targets},
            ))
            if realized < dispatched:
                break
        finite = finite_look_assessment(
            assessment, observations=tuple(observations_for_looks), input_receipt_hashes=dict(hashes),
        )
        stopping["finite_look_status"] = finite.status
        stopping["completed_looks"] = finite.completed_looks
        stopping["records"] = finite.look_records
        if finite.status != "complete":
            reasons.append(finite.status)
        if finite.look_records and finite.look_records[-1].complete:
            verdicts.update(finite.look_records[-1].target_decisions)
    for target in assessment.targets:
        if target.target_id not in target_rates:
            raise ValueError("assessment target has no frozen campaign point")
        needed, source_count = _source_denominator(
            target_id=target.target_id, required=required, values=source_counts,
        )
        if needed:
            verdicts[target.target_id] = target_interval_decision(
                target_rates[target.target_id], target, input_receipt_hashes=dict(hashes),
                source_denominator_required=True, source_denominator=source_count,
            )
        elif target.target_id not in verdicts:
            verdicts[target.target_id] = target_interval_decision(
                target_rates[target.target_id], target, input_receipt_hashes=dict(hashes),
            )
        if verdicts[target.target_id].verdict == "inconclusive":
            reasons.append(f"target:{target.target_id}:{verdicts[target.target_id].reason}")
    status: Literal["complete", "inconclusive"] = "inconclusive" if reasons else "complete"
    preliminary = CampaignReportV1(
        schema="campaign_report_v1", status=status, inconclusive_reasons=tuple(sorted(set(reasons))),
        input_receipt_hashes=hashes, point_reports=tuple(report_points), verdicts=verdicts,
        stopping=stopping, report_sha256="",
    )
    return CampaignReportV1(
        schema=preliminary.schema, status=preliminary.status,
        inconclusive_reasons=preliminary.inconclusive_reasons,
        input_receipt_hashes=preliminary.input_receipt_hashes,
        point_reports=preliminary.point_reports, verdicts=preliminary.verdicts,
        stopping=preliminary.stopping,
        report_sha256=sha256(preliminary.semantic_bytes()).hexdigest(),
    )


def verify_campaign_report(**kwargs: Any) -> bool:
    """Repeat report reconstruction and require semantic bytes and hash to match."""
    report = kwargs.pop("report", None)
    if not isinstance(report, CampaignReportV1):
        raise ValueError("report verification requires a CampaignReportV1")
    expected = reconstruct_campaign_report(**kwargs)
    if report.report_sha256 != sha256(report.semantic_bytes()).hexdigest():
        raise ValueError("campaign report hash differs from its semantic bytes")
    if report.semantic_bytes() != expected.semantic_bytes() or report.report_sha256 != expected.report_sha256:
        raise ValueError("campaign report differs from independent reconstruction")
    return True
