"""Reconstruct campaign assessment reports from sealed merge evidence only.

The report layer deliberately consumes the merge receipt produced from verified
shards.  It has no path for shard summary counters: terminal facts are counted
again against the frozen work plan, and every report remains replayable from
the same immutable receipt bytes and frozen assessment inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Literal, Mapping, Sequence

from .contracts import (
    CampaignAssessmentV1,
    MaterializedPhysicalSampleV1,
    TargetReferenceV1,
    canonical_json_bytes,
)
from .planning import CampaignWorkPlan, UnitKey
from .statistics import (
    CampaignTerminalOutcomeV1,
    ExactBinomialRateV1,
    FiniteLookObservationV1,
    PairedArmOutcomeV1,
    PairedCompletionSummaryV1,
    PairedOutcomeTableV1,
    OutcomeDenominatorSummaryV1,
    TargetIntervalDecisionV1,
    exact_binomial_rate,
    finite_look_assessment,
    paired_completion_summary,
    paired_outcome_table,
    outcome_denominator_summary,
    target_interval_decision,
    HolmFamilyMemberV1,
    holm_adjusted_family,
)

from .controlled import ControlledFamilyReceiptV1


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


def require_complete_ordered_campaign(*, plan: CampaignWorkPlan, merged: Mapping[str, Any]) -> None:
    """Allow controlled inference only after every frozen matched group closes."""
    from json import loads

    preimage = loads(plan.campaign_plan_preimage)
    if preimage.get("schema") != "ordered_campaign_work_plan_v1":
        raise ValueError("ordered assessment requires an ordered frozen plan")
    terminal = merged.get("terminal_unit_keys")
    if terminal != list(plan.unit_keys):
        raise ValueError("ordered assessment requires every frozen matched group to be complete")
    if any(merged.get(field) for field in (
        "missing_unit_keys", "incomplete_unit_keys", "explicit_final_nonterminal_keys",
        "unexpected_unit_keys", "conflicting_unit_keys", "authorized_undispatched_keys",
    )):
        raise ValueError("ordered assessment rejects partial or conflicting evidence")
    if any(group["unit_keys"] != list(plan.unit_keys[(group["group_ordinal"] - 1) * plan.units_per_sample_group:group["group_ordinal"] * plan.units_per_sample_group])
           for group in preimage["groups"]):
        raise ValueError("ordered assessment group membership differs from frozen order")


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
    outcome_denominator_summaries: tuple[OutcomeDenominatorSummaryV1, ...]
    outcome_treatment_table: tuple[tuple[str, str, str], ...]
    work_and_resources: WorkAndResourceReportV1


@dataclass(frozen=True, slots=True)
class CampaignReportV1:
    """A byte-replayable campaign report; observations never enter its verdict."""

    schema: Literal["campaign_report_v1"]
    status: Literal["complete", "inconclusive"]
    inconclusive_reasons: tuple[str, ...]
    merge_receipt_sha256: str
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
    provided = work_vectors_by_unit
    if not isinstance(provided, Mapping):
        raise ValueError("every verified terminal requires a named work vector")
    terminal_keys = {row["unit"].key for row in terminal_rows}
    if set(provided) != terminal_keys:
        raise ValueError("work vectors must cover every verified terminal exactly once")
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


def _verified_materialized_sample_hashes(
    *,
    terminal_rows: Sequence[dict[str, Any]],
    materialized_samples_by_identity: Mapping[str, MaterializedPhysicalSampleV1] | None,
) -> tuple[tuple[str, str], ...]:
    """Revalidate immutable samples before their digests enter report provenance."""
    if materialized_samples_by_identity is None:
        raise ValueError("every report requires verified materialized sample evidence")
    if not isinstance(materialized_samples_by_identity, Mapping):
        raise ValueError("materialized samples must be keyed by frozen physical sample identity")
    expected: dict[str, Any] = {}
    for row in terminal_rows:
        unit = row["unit"]
        expected[unit.physical_sample_identity] = unit
    if set(materialized_samples_by_identity) != set(expected):
        raise ValueError("materialized samples must cover every verified physical sample exactly once")
    hashes: list[tuple[str, str]] = []
    for identity in sorted(expected):
        artifact = materialized_samples_by_identity[identity]
        if not isinstance(artifact, MaterializedPhysicalSampleV1):
            raise ValueError("materialized samples must be validated immutable artifacts")
        verified = MaterializedPhysicalSampleV1.model_validate(
            artifact.model_dump(mode="json", by_alias=True)
        )
        unit = expected[identity]
        if (
            verified.physical_sample_identity != identity
            or verified.cohort_id != unit.cohort_id
            or verified.point_id != unit.point_id
            or verified.sample_namespace != unit.sample_namespace
            or verified.sample_id != unit.sample_id
        ):
            raise ValueError("materialized sample differs from frozen point/sample identity")
        hashes.extend((
            (f"materialized_sample:{identity}", verified.materialized_sample_sha256),
            (f"physical_error:{identity}", verified.physical_error_sha256),
        ))
    return tuple(sorted(hashes))


def reconstruct_campaign_report(
    *, plan: CampaignWorkPlan, assessment: CampaignAssessmentV1, merge_receipt: Mapping[str, Any],
    input_receipt_hashes: Mapping[str, str], source_denominator_required_by_target: Mapping[str, bool] | None = None,
    source_denominators: Mapping[str, int | None] | None = None,
    target_arm_ids: Mapping[str, str] | None = None,
    work_vectors_by_unit: Mapping[str, Mapping[str, int]] | None = None,
    materialized_samples_by_identity: Mapping[str, MaterializedPhysicalSampleV1] | None = None,
    observations: Mapping[str, Any] | None = None,
) -> CampaignReportV1:
    """Recompute all report rows from a verified merge receipt and frozen inputs."""
    hashes = _immutable_hashes(plan=plan, assessment=assessment, merge_receipt=merge_receipt,
                              input_receipt_hashes=input_receipt_hashes)
    terminal_rows = _verified_merge(plan=plan, merge_receipt=merge_receipt)
    if not terminal_rows:
        raise ValueError("report cannot compute an interval without verified terminal evidence")
    materialized_hashes = _verified_materialized_sample_hashes(
        terminal_rows=terminal_rows,
        materialized_samples_by_identity=materialized_samples_by_identity,
    )
    if set(name for name, _ in hashes) & set(name for name, _ in materialized_hashes):
        raise ValueError("report input hashes cannot shadow verified materialized sample hashes")
    hashes = tuple(sorted((*hashes, *materialized_hashes)))
    validated_work = {
        key: dict(vector)
        for key, vector in _work_and_resources(
            terminal_rows=terminal_rows,
            work_vectors_by_unit=work_vectors_by_unit,
            observations=observations,
        ).work_vectors
    }
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
        denominator_summaries: list[OutcomeDenominatorSummaryV1] = []
        for arm_id in arm_ids:
            arm_units = [unit for unit in point_units if unit.arm_id == arm_id]
            arm_rows = [row for row in rows if row["unit"].arm_id == arm_id]
            arm_outcomes = tuple(CampaignTerminalOutcomeV1(
                sample_identity=row["unit"].physical_sample_identity,
                arm_id=arm_id,
                terminal_status=row["terminal"]["outcome"],
                actual_work=validated_work[row["unit"].key],
            ) for row in arm_rows)
            denominator_summaries.append(outcome_denominator_summary(
                outcomes=arm_outcomes,
                arm_id=arm_id,
                planned_samples=len(arm_units),
                dispatched_samples=len(arm_rows),
                outcome_matrix=assessment.outcome_matrix,
                alpha=1.0 - assessment.interval.confidence_level,
                count_receipt_sha256=dict(hashes)["merge"],
            ))
        report_points.append(PointReportV1(
            point_id=point_id, planned_samples=len(point_units), dispatched_samples=len(rows),
            terminal_samples=terminal_count, incomplete_samples=len(rows) - terminal_count,
            accepted_samples=accepted, conditional_samples=accepted,
            status_counts=tuple(sorted(statuses.items())), all_shot=rate, pair_status=pair_status,
            paired=paired, work_and_resources=_work_and_resources(
                terminal_rows=rows,
                work_vectors_by_unit={row["unit"].key: validated_work[row["unit"].key] for row in rows},
                observations=observations,
            ),
            outcome_denominator_summaries=tuple(denominator_summaries),
            outcome_treatment_table=tuple(
                (treatment.terminal_status, treatment.all_shot, treatment.conditional)
                for treatment in assessment.outcome_matrix.treatments
            ),
        ))
    target_rates: dict[str, ExactBinomialRateV1] = {}
    target_arms_by_id: dict[str, str] = {}
    for target in assessment.targets:
        matching = rows_by_point.get(target.target_id, [])
        # A prespecified target ID need not be the physical point ID.  The
        # one-point campaign has an unambiguous point even when its target is
        # named for the development claim; multi-point work still requires
        # exact point-ID binding rather than guessing.
        if not matching and len(all_plan_by_point) == 1:
            matching = next(iter(rows_by_point.values()))
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
        merge_receipt_sha256=dict(hashes)["merge"], input_receipt_hashes=hashes,
        point_reports=tuple(report_points), verdicts=verdicts,
        stopping=stopping, report_sha256="",
    )
    return CampaignReportV1(
        schema=preliminary.schema, status=preliminary.status,
        inconclusive_reasons=preliminary.inconclusive_reasons,
        merge_receipt_sha256=preliminary.merge_receipt_sha256,
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


def _route_report_projection(report: CampaignReportV1) -> dict[str, Any]:
    """Keep only report facts that must agree across executor routes."""
    def science(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: science(item) for key, item in value.items()
                if key not in {"report_sha256", "merge_receipt_sha256", "count_receipt_sha256"}
            }
        if isinstance(value, tuple):
            if len(value) == 2 and value[0] == "merge":
                return None
            return tuple(item for item in (science(item) for item in value) if item is not None)
        if isinstance(value, list):
            return [item for item in (science(item) for item in value) if item is not None]
        return value

    projection = science(asdict(report))
    for point in projection["point_reports"]:
        point["work_and_resources"]["observations"] = []
    return projection


def _route_merge_projection(merge_receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Compare canonical terminal science while excluding profiler-only facts."""
    fields = (
        "campaign_plan_digest", "terminal_unit_keys", "explicit_final_nonterminal_keys",
        "incomplete_unit_keys", "authorized_undispatched_keys", "unexpected_unit_keys",
        "conflicting_unit_keys", "missing_unit_keys", "terminal_facts",
    )
    if not isinstance(merge_receipt, Mapping) or any(field not in merge_receipt for field in fields):
        raise ValueError("route verification requires independently reconstructed merge receipts")
    events = merge_receipt.get("events")
    if not isinstance(events, list):
        raise ValueError("route merge receipt lacks canonical events")
    normalized_events: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, Mapping) or not isinstance(event.get("data"), Mapping):
            raise ValueError("route merge event has an invalid canonical shape")
        normalized = dict(event)
        normalized.pop("event_id", None)
        data = dict(normalized["data"])
        for observation in ("profile", "decode_runtime", "setup_runtime"):
            data.pop(observation, None)
        normalized["data"] = data
        normalized_events.append(normalized)
    # Merge receipts sort event records by event ID.  Those IDs include the
    # profiler observations removed above, so establish route-neutral order
    # only after retaining every remaining canonical semantic field.
    normalized_events.sort(key=canonical_json_bytes)
    return {**{field: merge_receipt[field] for field in fields}, "events": normalized_events}


def verify_campaign_routes(
    *, local_report: CampaignReportV1, slurm_report: CampaignReportV1,
    local_merge_receipt: Mapping[str, Any], slurm_merge_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove route-neutral campaign science after both routes are independently replayed."""
    if not isinstance(local_report, CampaignReportV1) or not isinstance(slurm_report, CampaignReportV1):
        raise ValueError("route verification requires two reconstructed campaign reports")
    local_science = {
        "report": _route_report_projection(local_report),
        "merge": _route_merge_projection(local_merge_receipt),
    }
    slurm_science = {
        "report": _route_report_projection(slurm_report),
        "merge": _route_merge_projection(slurm_merge_receipt),
    }
    if canonical_json_bytes(local_science) != canonical_json_bytes(slurm_science):
        raise ValueError("local and Slurm routes differ in scientific campaign evidence")
    local_observations = {
        item.point_id: asdict(item.work_and_resources)["observations"]
        for item in local_report.point_reports
    }
    slurm_observations = {
        item.point_id: asdict(item.work_and_resources)["observations"]
        for item in slurm_report.point_reports
    }
    differences = {
        point_id: {"local": local_observations[point_id], "slurm": slurm_observations[point_id]}
        for point_id in sorted(set(local_observations) | set(slurm_observations))
        if local_observations.get(point_id) != slurm_observations.get(point_id)
    }
    return {
        "schema": "campaign_route_equivalence_v1",
        "scientific_records_match": True,
        "observational_differences": differences,
    }


def reconstruct_controlled_family(
    *, plan: CampaignWorkPlan, family_id: str, source_design_sha256: str,
    terminal_status_by_unit: Mapping[str, str], alpha: float,
) -> ControlledFamilyReceiptV1:
    """Assess only the complete frozen groups and primary family contrasts.

    A partial family retains its exact missing unit set.  Its paired tables
    remain absent and Holm receives unavailable members at the full frozen
    family size, so no completed subset can acquire a significance claim.
    """
    if plan.work_spec is None or not isinstance(terminal_status_by_unit, Mapping):
        raise ValueError("controlled family requires a frozen plan and terminal mapping")
    preimage = json.loads(plan.campaign_plan_preimage)
    if preimage.get("schema") != "ordered_campaign_work_plan_v1":
        raise ValueError("controlled family requires a frozen ordered work plan")
    families = {
        "relay_beam": (("initial_bp", "relay", "beam"),
                       (("initial_bp", "relay"), ("initial_bp", "beam"))),
        "mbbp_list_vote": (("list", "vote"), (("list", "vote"),)),
        "schedule": (("spa_flooding", "spa_check_node_serial"),
                     (("spa_flooding", "spa_check_node_serial"),)),
    }
    if family_id not in families:
        raise ValueError("unknown controlled family")
    arm_order, comparisons = families[family_id]
    if tuple(preimage["execution_order"]["arm_order"]) != arm_order:
        raise ValueError("controlled family arm order differs from frozen plan")
    if set(terminal_status_by_unit) - set(plan.unit_keys):
        raise ValueError("controlled family contains an undeclared unit")
    by_key = {unit.key: unit for unit in plan.units}
    missing = tuple(key for key in plan.unit_keys if key not in terminal_status_by_unit)
    expected = tuple(by_key[group["unit_keys"][0]].physical_sample_identity for group in preimage["groups"])
    complete = tuple(by_key[group["unit_keys"][0]].physical_sample_identity
                     for group in preimage["groups"] if all(key in terminal_status_by_unit for key in group["unit_keys"]))
    tables: dict[str, dict[str, Any]] = {}
    holm_members = []
    for first_arm, second_arm in comparisons:
        comparison_id = f"{first_arm}-vs-{second_arm}"
        if missing:
            holm_members.append(HolmFamilyMemberV1(comparison_id, None))
            continue
        selected = []
        for group in preimage["groups"]:
            for key in group["unit_keys"]:
                unit = by_key[key]
                if unit.arm_id not in {first_arm, second_arm}:
                    continue
                selected.append(PairedArmOutcomeV1(
                    campaign_spec_digest=plan.campaign_spec_digest,
                    cohort_id=unit.cohort_id, point_id=unit.point_id,
                    sample_identity=unit.physical_sample_identity, arm_id=unit.arm_id,
                    terminal_status=terminal_status_by_unit[key],
                ))
        count_digest = sha256(b"bp-registry-controlled-contrast-v1\0" + canonical_json_bytes({
            "campaign_plan_digest": plan.campaign_plan_digest,
            "source_design_sha256": source_design_sha256,
            "comparison_id": comparison_id,
            "outcomes": [asdict(item) for item in selected],
        })).hexdigest()
        table = paired_outcome_table(
            outcomes=selected, arm_ids=(first_arm, second_arm), alpha=alpha,
            count_receipt_sha256=count_digest,
            outcome_matrix=plan.work_spec.assessment.outcome_matrix,
        )
        tables[comparison_id] = asdict(table)
        holm_members.append(HolmFamilyMemberV1(comparison_id, table.exact_discordance_p_value))
    holm = holm_adjusted_family(family_id=family_id, alpha=alpha, members=holm_members)
    return ControlledFamilyReceiptV1.model_validate({
        "schema": "controlled_family_receipt_v1", "family_id": family_id,
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "source_design_sha256": source_design_sha256,
        "arm_order": arm_order, "comparisons": comparisons,
        "expected_sample_identities": expected,
        "complete_sample_identities": complete,
        "missing_unit_keys": missing, "paired_tables": tables,
        "holm_result": asdict(holm),
        "status": "inconclusive_partial" if missing else "complete",
    })
