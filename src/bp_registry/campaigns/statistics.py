"""Prespecified exact-rate and target-assessment procedures.

These functions consume frozen campaign contracts and content receipts.  They
do not derive a target, tolerance, stopping rule, or confidence level from
outcomes.  Exact binomial limits are deliberately delegated to SciPy's
``binomtest(...).proportion_ci(method="exact")`` implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Literal, Mapping, Sequence

from scipy.stats import binomtest

from .contracts import (
    CampaignAssessmentV1,
    FiniteLookStoppingV1,
    OutcomeMatrixV1,
    TargetReferenceV1,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_SHOTS = 1_000_000
_RULE_ID = "target_interval_containment_v1"
_TERMINAL_STATUSES = frozenset({
    "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
    "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
    "infrastructure_interruption",
})
_ALL_SHOT_SUCCESSES = frozenset({"exact", "stabilizer_equivalent"})


def _bounded_int(value: int, *, name: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= _MAX_SHOTS:
        raise ValueError(f"{name} must be an integer in [{minimum}, {_MAX_SHOTS}]")
    return value


def _probability(value: float, *, name: str) -> float:
    if type(value) is not float or not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be a finite probability in (0, 1)")
    return value


def _sha256(value: str, *, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _identifier(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError(f"{name} must be a nonempty bounded string")
    return value


def _receipt_hashes(value: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping) or not value or len(value) > 64:
        raise ValueError("input_receipt_hashes must be a nonempty bounded mapping")
    verified: list[tuple[str, str]] = []
    for name, digest in value.items():
        if not isinstance(name, str) or not name or len(name) > 128:
            raise ValueError("input receipt names must be nonempty bounded strings")
        verified.append((name, _sha256(digest, name=f"input receipt {name}")))
    return tuple(sorted(verified))


@dataclass(frozen=True, slots=True)
class ExactBinomialRateV1:
    """A two-sided exact Clopper-Pearson rate report with integer evidence."""

    failures: int
    shots: int
    estimate: float
    alpha: float
    confidence_level: float
    method: Literal["exact_clopper_pearson"]
    sidedness: Literal["two_sided"]
    interval: tuple[float, float]
    count_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class TargetIntervalDecisionV1:
    """The complete retained algebra for a frozen target-interval verdict."""

    verdict: Literal["pass", "fail", "inconclusive"]
    reason: str
    rule_id: Literal["target_interval_containment_v1"]
    computed_interval: tuple[float, float]
    target_interval: tuple[float, float]
    tolerance: float
    acceptable_interval: tuple[float, float]
    input_receipt_hashes: tuple[tuple[str, str], ...]
    source_denominator_required: bool
    source_denominator: int | None


@dataclass(frozen=True, slots=True)
class FiniteLookObservationV1:
    """One observed dispatch boundary, including any whole-batch overshoot."""

    look: int
    dispatched_shots: int
    realized_shots: int
    failures_by_target: Mapping[str, int]
    count_receipt_sha256_by_target: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class FiniteLookRecordV1:
    """A retained decision or partial state for one declared look."""

    look: int
    planned_boundary: int
    dispatched_shots: int
    realized_shots: int
    overshoot: int
    complete: bool
    alpha_spent: float
    target_decisions: Mapping[str, TargetIntervalDecisionV1]


@dataclass(frozen=True, slots=True)
class FiniteLookAssessmentV1:
    """The entire finite-look evidence trail, including an incomplete tail."""

    status: Literal["complete", "inconclusive_partial_batch"]
    completed_looks: tuple[int, ...]
    look_records: tuple[FiniteLookRecordV1, ...]
    stop_reason: Literal[
        "all_primary_decisions_resolved", "maximum_reached", "partial_batch",
    ] | None
    input_receipt_hashes: tuple[tuple[str, str], ...]


def exact_binomial_rate(
    *, failures: int, shots: int, alpha: float, count_receipt_sha256: str,
) -> ExactBinomialRateV1:
    """Compute one exact two-sided fixed-shot Bernoulli interval.

    ``alpha`` must be frozen before observing outcomes.  A finite nonzero
    denominator and a bounded integer numerator prevent invalid SciPy calls.
    """
    shots = _bounded_int(shots, name="shots", minimum=1)
    failures = _bounded_int(failures, name="failures")
    if failures > shots:
        raise ValueError("failures cannot exceed shots")
    alpha = _probability(alpha, name="alpha")
    receipt = _sha256(count_receipt_sha256, name="count_receipt_sha256")
    confidence_level = 1.0 - alpha
    limits = binomtest(failures, n=shots).proportion_ci(
        confidence_level=confidence_level,
        method="exact",
    )
    lower, upper = float(limits.low), float(limits.high)
    if not (math.isfinite(lower) and math.isfinite(upper) and 0.0 <= lower <= upper <= 1.0):
        raise ValueError("SciPy returned a nonfinite or out-of-domain exact interval")
    return ExactBinomialRateV1(
        failures=failures,
        shots=shots,
        estimate=failures / shots,
        alpha=alpha,
        confidence_level=confidence_level,
        method="exact_clopper_pearson",
        sidedness="two_sided",
        interval=(lower, upper),
        count_receipt_sha256=receipt,
    )


def target_interval_decision(
    rate: ExactBinomialRateV1,
    target: TargetReferenceV1,
    *,
    input_receipt_hashes: Mapping[str, str],
    source_denominator_required: bool = False,
    source_denominator: int | None = None,
) -> TargetIntervalDecisionV1:
    """Compare an exact rate interval to one frozen target plus tolerance.

    The acceptable band is ``[target.lower - delta, target.upper + delta]``
    clipped to the Bernoulli estimand domain.  Containment passes, strict
    disjointness fails, and every overlap or unavailable required source
    denominator remains inconclusive.
    """
    if not isinstance(rate, ExactBinomialRateV1):
        raise ValueError("rate must be an ExactBinomialRateV1")
    if not isinstance(target, TargetReferenceV1):
        raise ValueError("target must be a frozen TargetReferenceV1")
    if type(source_denominator_required) is not bool:
        raise ValueError("source_denominator_required must be a bool")
    if source_denominator is not None:
        source_denominator = _bounded_int(
            source_denominator, name="source_denominator", minimum=1,
        )
    receipts = _receipt_hashes(input_receipt_hashes)
    lower, upper = rate.interval
    target_lower, target_upper = target.lower, target.upper
    acceptable = (
        max(0.0, target_lower - target.absolute_tolerance),
        min(1.0, target_upper + target.absolute_tolerance),
    )
    if source_denominator_required and source_denominator is None:
        verdict: Literal["pass", "fail", "inconclusive"] = "inconclusive"
        reason = "missing_required_source_denominator"
    elif acceptable[0] <= lower and upper <= acceptable[1]:
        verdict = "pass"
        reason = "computed_interval_contained_in_acceptable_interval"
    elif upper < acceptable[0] or lower > acceptable[1]:
        verdict = "fail"
        reason = "computed_interval_disjoint_from_acceptable_interval"
    else:
        verdict = "inconclusive"
        reason = "computed_interval_overlaps_acceptable_interval"
    return TargetIntervalDecisionV1(
        verdict=verdict,
        reason=reason,
        rule_id=_RULE_ID,
        computed_interval=(lower, upper),
        target_interval=(target_lower, target_upper),
        tolerance=target.absolute_tolerance,
        acceptable_interval=acceptable,
        input_receipt_hashes=receipts,
        source_denominator_required=source_denominator_required,
        source_denominator=source_denominator,
    )


@dataclass(frozen=True, slots=True)
class PairedArmOutcomeV1:
    """One terminal arm result, bound to its shared physical sample identity."""

    campaign_spec_digest: str
    cohort_id: str
    point_id: str
    sample_identity: str
    arm_id: str
    terminal_status: str

    def __post_init__(self) -> None:
        _sha256(self.campaign_spec_digest, name="campaign_spec_digest")
        _identifier(self.cohort_id, name="cohort_id")
        _identifier(self.point_id, name="point_id")
        _identifier(self.sample_identity, name="sample_identity")
        _identifier(self.arm_id, name="arm_id")
        if self.terminal_status not in _TERMINAL_STATUSES:
            raise ValueError("terminal_status is not in the frozen outcome matrix domain")


@dataclass(frozen=True, slots=True)
class PairedOutcomeTableV1:
    """Complete matched failure table and conservative paired effect evidence."""

    arm_ids: tuple[str, str]
    complete_pairs: int
    table: Mapping[str, int]
    first_failure_rate: float
    second_failure_rate: float
    risk_difference: float
    risk_difference_interval: tuple[float, float]
    risk_difference_method: Literal["simultaneous_exact_discordant_cells_v1"]
    exact_discordance_p_value: float
    exact_discordance_method: Literal["exact_conditional_mcnemar_v1"]
    alpha: float
    count_receipt_sha256: str


def _all_shot_failure(status: str, outcome_matrix: OutcomeMatrixV1 | None = None) -> bool:
    """Apply the frozen all-shot mapping before paired inference."""
    if status == "infrastructure_interruption":
        raise ValueError("infrastructure interruption leaves a partial paired outcome")
    if outcome_matrix is not None:
        if not isinstance(outcome_matrix, OutcomeMatrixV1):
            raise ValueError("paired comparison requires a validated outcome matrix")
        treatment = next(item for item in outcome_matrix.treatments if item.terminal_status == status)
        if treatment.all_shot == "incomplete":
            raise ValueError("incomplete mapped outcome cannot enter paired inference")
        return treatment.all_shot == "failure"
    return status not in _ALL_SHOT_SUCCESSES


def paired_outcome_table(
    *,
    outcomes: Sequence[PairedArmOutcomeV1],
    arm_ids: tuple[str, str],
    alpha: float,
    count_receipt_sha256: str,
    outcome_matrix: OutcomeMatrixV1 | None = None,
) -> PairedOutcomeTableV1:
    """Join two arms on the entire frozen physical-sample identity.

    The table is intentionally unavailable for partial or duplicate arms.  A
    caller must resume/finalize those samples through its declared incomplete
    policy rather than silently turn unequal samples into a paired result.
    """
    if not isinstance(arm_ids, tuple) or len(arm_ids) != 2:
        raise ValueError("paired comparison requires exactly two arm IDs")
    first_arm, second_arm = (_identifier(arm_ids[0], name="first arm ID"), _identifier(arm_ids[1], name="second arm ID"))
    if first_arm == second_arm:
        raise ValueError("paired comparison requires distinct arm IDs")
    if not isinstance(outcomes, Sequence) or isinstance(outcomes, (str, bytes)) or not outcomes:
        raise ValueError("paired comparison requires at least one paired terminal outcome")
    alpha = _probability(alpha, name="alpha")
    receipt = _sha256(count_receipt_sha256, name="count_receipt_sha256")
    by_sample: dict[tuple[str, str, str, str], dict[str, PairedArmOutcomeV1]] = {}
    campaign_points: set[tuple[str, str, str]] = set()
    for outcome in outcomes:
        if not isinstance(outcome, PairedArmOutcomeV1):
            raise ValueError("paired outcomes must be PairedArmOutcomeV1 records")
        if outcome.arm_id not in {first_arm, second_arm}:
            raise ValueError("paired outcome has an undeclared arm ID")
        campaign_point = (outcome.campaign_spec_digest, outcome.cohort_id, outcome.point_id)
        campaign_points.add(campaign_point)
        identity = (*campaign_point, outcome.sample_identity)
        arms = by_sample.setdefault(identity, {})
        if outcome.arm_id in arms:
            raise ValueError("paired comparison has duplicate arm evidence for a sample identity")
        arms[outcome.arm_id] = outcome
    if len(campaign_points) != 1:
        raise ValueError("paired comparison must use one identical campaign, cohort, and point")
    expected_arms = {first_arm, second_arm}
    if any(set(arms) != expected_arms for arms in by_sample.values()):
        raise ValueError("paired comparison has a partial matched sample")
    table = {
        "first_success_second_success": 0,
        "first_failure_second_success": 0,
        "first_success_second_failure": 0,
        "first_failure_second_failure": 0,
    }
    for arms in by_sample.values():
        first_failure = _all_shot_failure(arms[first_arm].terminal_status, outcome_matrix)
        second_failure = _all_shot_failure(arms[second_arm].terminal_status, outcome_matrix)
        table[(
            "first_failure_second_failure" if first_failure and second_failure
            else "first_failure_second_success" if first_failure
            else "first_success_second_failure" if second_failure
            else "first_success_second_success"
        )] += 1
    pairs = len(by_sample)
    first_only = table["first_failure_second_success"]
    second_only = table["first_success_second_failure"]
    first_rate = (first_only + table["first_failure_second_failure"]) / pairs
    second_rate = (second_only + table["first_failure_second_failure"]) / pairs
    difference = first_rate - second_rate
    # Two simultaneous exact intervals each receive half of the frozen alpha.
    first_discordant = exact_binomial_rate(
        failures=first_only, shots=pairs, alpha=alpha / 2.0, count_receipt_sha256=receipt,
    )
    second_discordant = exact_binomial_rate(
        failures=second_only, shots=pairs, alpha=alpha / 2.0, count_receipt_sha256=receipt,
    )
    interval = (
        first_discordant.interval[0] - second_discordant.interval[1],
        first_discordant.interval[1] - second_discordant.interval[0],
    )
    discordant = first_only + second_only
    exact_p = 1.0 if discordant == 0 else float(binomtest(first_only, n=discordant, p=0.5).pvalue)
    return PairedOutcomeTableV1(
        arm_ids=(first_arm, second_arm),
        complete_pairs=pairs,
        table=table,
        first_failure_rate=first_rate,
        second_failure_rate=second_rate,
        risk_difference=difference,
        risk_difference_interval=interval,
        risk_difference_method="simultaneous_exact_discordant_cells_v1",
        exact_discordance_p_value=exact_p,
        exact_discordance_method="exact_conditional_mcnemar_v1",
        alpha=alpha,
        count_receipt_sha256=receipt,
    )


@dataclass(frozen=True, slots=True)
class HolmFamilyMemberV1:
    """One predeclared comparison, including an explicit unavailable value."""

    comparison_id: str
    raw_p_value: float | None

    def __post_init__(self) -> None:
        _identifier(self.comparison_id, name="comparison_id")
        if self.raw_p_value is not None and (
            type(self.raw_p_value) is not float
            or not math.isfinite(self.raw_p_value)
            or not 0.0 <= self.raw_p_value <= 1.0
        ):
            raise ValueError("raw_p_value must be finite in [0, 1], or unavailable")


@dataclass(frozen=True, slots=True)
class HolmMemberResultV1:
    comparison_id: str
    status: Literal["available", "unavailable"]
    order: int
    rank: int
    multiplier: int
    raw_p_value: float | None
    sentinel_p_value: float
    adjusted_p_value: float
    conclusion: Literal["rejected", "not_rejected", "inconclusive"]


@dataclass(frozen=True, slots=True)
class HolmFamilyResultV1:
    family_id: str
    alpha: float
    frozen_family_size: int
    members: tuple[HolmMemberResultV1, ...]
    verdict: Literal["rejected", "not_rejected", "inconclusive"]


def holm_adjusted_family(
    *, family_id: str, alpha: float, members: Sequence[HolmFamilyMemberV1],
) -> HolmFamilyResultV1:
    """Apply Holm to a frozen family without letting missing results reduce it."""
    family_id = _identifier(family_id, name="family_id")
    alpha = _probability(alpha, name="alpha")
    if not isinstance(members, Sequence) or isinstance(members, (str, bytes)) or not members:
        raise ValueError("Holm adjustment requires a nonempty frozen family")
    if any(not isinstance(member, HolmFamilyMemberV1) for member in members):
        raise ValueError("Holm members must be HolmFamilyMemberV1 records")
    member_ids = [member.comparison_id for member in members]
    if len(set(member_ids)) != len(member_ids):
        raise ValueError("Holm comparison IDs must be unique")
    available = sorted(
        (member for member in members if member.raw_p_value is not None),
        key=lambda member: (member.raw_p_value, member.comparison_id),
    )
    unavailable = sorted(
        (member for member in members if member.raw_p_value is None),
        key=lambda member: member.comparison_id,
    )
    ordered = [*available, *unavailable]
    family_size = len(ordered)
    results: list[HolmMemberResultV1] = []
    running_adjusted = 0.0
    for order, member in enumerate(ordered, start=1):
        multiplier = family_size - order + 1
        if member.raw_p_value is None:
            results.append(HolmMemberResultV1(
                comparison_id=member.comparison_id,
                status="unavailable",
                order=order,
                rank=order,
                multiplier=multiplier,
                raw_p_value=None,
                sentinel_p_value=1.0,
                adjusted_p_value=1.0,
                conclusion="inconclusive",
            ))
            continue
        candidate = min(1.0, multiplier * member.raw_p_value)
        running_adjusted = max(running_adjusted, candidate)
        results.append(HolmMemberResultV1(
            comparison_id=member.comparison_id,
            status="available",
            order=order,
            rank=order,
            multiplier=multiplier,
            raw_p_value=member.raw_p_value,
            sentinel_p_value=member.raw_p_value,
            adjusted_p_value=running_adjusted,
            conclusion="rejected" if running_adjusted <= alpha else "not_rejected",
        ))
    if unavailable:
        verdict: Literal["rejected", "not_rejected", "inconclusive"] = "inconclusive"
    elif any(result.conclusion == "rejected" for result in results):
        verdict = "rejected"
    else:
        verdict = "not_rejected"
    return HolmFamilyResultV1(
        family_id=family_id,
        alpha=alpha,
        frozen_family_size=family_size,
        members=tuple(results),
        verdict=verdict,
    )


@dataclass(frozen=True, slots=True)
class CampaignTerminalOutcomeV1:
    """A retained arm terminal with separately accumulated decoder work."""

    sample_identity: str
    arm_id: str
    terminal_status: str
    actual_work: Mapping[str, int]

    def __post_init__(self) -> None:
        _identifier(self.sample_identity, name="sample_identity")
        _identifier(self.arm_id, name="arm_id")
        if self.terminal_status not in _TERMINAL_STATUSES:
            raise ValueError("terminal_status is not in the frozen outcome matrix domain")
        if not isinstance(self.actual_work, Mapping) or not self.actual_work:
            raise ValueError("actual_work must be a nonempty mapping of named work dimensions")
        for dimension, value in self.actual_work.items():
            _identifier(dimension, name="actual work dimension")
            _bounded_int(value, name=f"actual work for {dimension}")


@dataclass(frozen=True, slots=True)
class ExactProportionV1:
    """An exact proportion interval whose numerator is named for its estimand."""

    numerator: int
    denominator: int
    estimate: float
    alpha: float
    interval: tuple[float, float]
    method: Literal["exact_clopper_pearson"]


@dataclass(frozen=True, slots=True)
class OutcomeDenominatorSummaryV1:
    """All denominators and retained status counts for one arm."""

    arm_id: str
    outcome_matrix_rule_id: str
    planned_samples: int
    dispatched_samples: int
    terminal_samples: int
    incomplete_samples: int
    accepted_samples: int
    status_counts: Mapping[str, int]
    all_shot_performance: ExactBinomialRateV1
    acceptance_probability: ExactProportionV1
    conditional_performance: ExactBinomialRateV1 | None
    conditional_unavailable_reason: Literal["zero accepted samples"] | None
    actual_work: Mapping[str, int]
    count_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class PairedCompletionSummaryV1:
    """Coverage evidence that must precede paired inferential arithmetic."""

    complete_pairs: int
    incomplete_pairs: int
    paired_inference_status: Literal["complete", "inconclusive_incomplete_pairs"]
    missing_arms_by_sample: Mapping[str, tuple[str, ...]]


def _exact_proportion(*, numerator: int, denominator: int, alpha: float) -> ExactProportionV1:
    numerator = _bounded_int(numerator, name="numerator")
    denominator = _bounded_int(denominator, name="denominator", minimum=1)
    if numerator > denominator:
        raise ValueError("proportion numerator cannot exceed denominator")
    alpha = _probability(alpha, name="alpha")
    interval = binomtest(numerator, n=denominator).proportion_ci(
        confidence_level=1.0 - alpha, method="exact",
    )
    return ExactProportionV1(
        numerator=numerator,
        denominator=denominator,
        estimate=numerator / denominator,
        alpha=alpha,
        interval=(float(interval.low), float(interval.high)),
        method="exact_clopper_pearson",
    )


def outcome_denominator_summary(
    *,
    outcomes: Sequence[CampaignTerminalOutcomeV1],
    arm_id: str,
    planned_samples: int,
    dispatched_samples: int,
    outcome_matrix: OutcomeMatrixV1,
    alpha: float,
    count_receipt_sha256: str,
) -> OutcomeDenominatorSummaryV1:
    """Summarize an arm through its total frozen terminal-status matrix.

    Infrastructure interruptions remain incomplete.  Every other terminal is
    mapped to the primary all-shot result and, independently, the accepted
    conditional denominator.  Actual decoder work is reported as a sum rather
    than renamed as an iteration count.
    """
    arm_id = _identifier(arm_id, name="arm_id")
    planned = _bounded_int(planned_samples, name="planned_samples", minimum=1)
    dispatched = _bounded_int(dispatched_samples, name="dispatched_samples")
    if dispatched > planned:
        raise ValueError("dispatched_samples cannot exceed planned_samples")
    if not isinstance(outcome_matrix, OutcomeMatrixV1):
        raise ValueError("outcome_matrix must be a frozen OutcomeMatrixV1")
    alpha = _probability(alpha, name="alpha")
    receipt = _sha256(count_receipt_sha256, name="count_receipt_sha256")
    if not isinstance(outcomes, Sequence) or isinstance(outcomes, (str, bytes)):
        raise ValueError("outcomes must be a finite sequence of terminal records")
    status_mapping = {item.terminal_status: item for item in outcome_matrix.treatments}
    seen_samples: set[str] = set()
    status_counts: dict[str, int] = {}
    primary_failures = 0
    terminal_samples = 0
    accepted = 0
    conditional_failures = 0
    work: dict[str, int] = {}
    for outcome in outcomes:
        if not isinstance(outcome, CampaignTerminalOutcomeV1):
            raise ValueError("outcomes must be CampaignTerminalOutcomeV1 records")
        if outcome.arm_id != arm_id:
            raise ValueError("outcome arm ID differs from denominator-summary arm")
        if outcome.sample_identity in seen_samples:
            raise ValueError("outcome denominator summary has duplicate sample evidence")
        seen_samples.add(outcome.sample_identity)
        treatment = status_mapping[outcome.terminal_status]
        status_counts[outcome.terminal_status] = status_counts.get(outcome.terminal_status, 0) + 1
        for dimension, value in outcome.actual_work.items():
            work[dimension] = work.get(dimension, 0) + value
        if treatment.all_shot == "incomplete":
            continue
        terminal_samples += 1
        primary_failures += int(treatment.all_shot == "failure")
        if treatment.conditional == "accepted":
            accepted += 1
            conditional_failures += int(treatment.all_shot == "failure")
    if len(seen_samples) > dispatched:
        raise ValueError("outcome records cannot exceed dispatched_samples")
    incomplete = dispatched - terminal_samples
    all_shot = exact_binomial_rate(
        failures=primary_failures,
        shots=terminal_samples,
        alpha=alpha,
        count_receipt_sha256=receipt,
    ) if terminal_samples else None
    if all_shot is None:
        raise ValueError("at least one non-incomplete terminal is required for a rate summary")
    acceptance = _exact_proportion(numerator=accepted, denominator=terminal_samples, alpha=alpha)
    conditional = exact_binomial_rate(
        failures=conditional_failures,
        shots=accepted,
        alpha=alpha,
        count_receipt_sha256=receipt,
    ) if accepted else None
    return OutcomeDenominatorSummaryV1(
        arm_id=arm_id,
        outcome_matrix_rule_id=outcome_matrix.rule_id,
        planned_samples=planned,
        dispatched_samples=dispatched,
        terminal_samples=terminal_samples,
        incomplete_samples=incomplete,
        accepted_samples=accepted,
        status_counts=status_counts,
        all_shot_performance=all_shot,
        acceptance_probability=acceptance,
        conditional_performance=conditional,
        conditional_unavailable_reason=None if conditional is not None else "zero accepted samples",
        actual_work=dict(sorted(work.items())),
        count_receipt_sha256=receipt,
    )


def paired_completion_summary(
    *, outcomes: Sequence[PairedArmOutcomeV1], arm_ids: tuple[str, str],
    outcome_matrix: OutcomeMatrixV1 | None = None,
) -> PairedCompletionSummaryV1:
    """Retain partial sample coverage and withhold paired inference until complete."""
    if not isinstance(arm_ids, tuple) or len(arm_ids) != 2:
        raise ValueError("paired completion requires exactly two arm IDs")
    first_arm, second_arm = (_identifier(arm_ids[0], name="first arm ID"), _identifier(arm_ids[1], name="second arm ID"))
    if first_arm == second_arm:
        raise ValueError("paired completion requires distinct arm IDs")
    if not isinstance(outcomes, Sequence) or isinstance(outcomes, (str, bytes)) or not outcomes:
        raise ValueError("paired completion requires at least one outcome")
    expected = {first_arm, second_arm}
    by_sample: dict[tuple[str, str, str, str], dict[str, PairedArmOutcomeV1]] = {}
    campaign_points: set[tuple[str, str, str]] = set()
    for outcome in outcomes:
        if not isinstance(outcome, PairedArmOutcomeV1):
            raise ValueError("paired completion outcomes must be PairedArmOutcomeV1 records")
        if outcome.arm_id not in expected:
            raise ValueError("paired completion has an undeclared arm ID")
        point = (outcome.campaign_spec_digest, outcome.cohort_id, outcome.point_id)
        campaign_points.add(point)
        identity = (*point, outcome.sample_identity)
        arms = by_sample.setdefault(identity, {})
        if outcome.arm_id in arms:
            raise ValueError("paired completion has duplicate arm evidence for a sample identity")
        arms[outcome.arm_id] = outcome
    if len(campaign_points) != 1:
        raise ValueError("paired completion must use one identical campaign, cohort, and point")
    missing: dict[str, tuple[str, ...]] = {}
    complete = 0
    treatments = None if outcome_matrix is None else {
        item.terminal_status: item.all_shot for item in outcome_matrix.treatments
    }
    for identity, arms in by_sample.items():
        eligible = {
            arm for arm, outcome in arms.items()
            if (outcome.terminal_status != "infrastructure_interruption" if treatments is None
                else treatments[outcome.terminal_status] != "incomplete")
        }
        if eligible == expected:
            complete += 1
        else:
            missing[identity[-1]] = tuple(sorted(expected - eligible))
    return PairedCompletionSummaryV1(
        complete_pairs=complete,
        incomplete_pairs=len(missing),
        paired_inference_status="complete" if not missing else "inconclusive_incomplete_pairs",
        missing_arms_by_sample=missing,
    )


def _finite_observation(
    observation: FiniteLookObservationV1,
    *,
    target_ids: tuple[str, ...],
    maximum_shots: int,
) -> tuple[int, int, int, dict[str, int], dict[str, str]]:
    if not isinstance(observation, FiniteLookObservationV1):
        raise ValueError("finite-look observations must be FiniteLookObservationV1 records")
    look = _bounded_int(observation.look, name="look", minimum=1)
    dispatched = _bounded_int(observation.dispatched_shots, name="dispatched_shots", minimum=1)
    realized = _bounded_int(observation.realized_shots, name="realized_shots")
    if dispatched > maximum_shots or realized > maximum_shots:
        raise ValueError("finite-look observation exceeds the frozen maximum shots")
    if realized > dispatched:
        raise ValueError("realized shots cannot exceed dispatched shots")
    failures = dict(observation.failures_by_target)
    receipts = dict(observation.count_receipt_sha256_by_target)
    if set(failures) != set(target_ids) or set(receipts) != set(target_ids):
        raise ValueError("finite-look observation must cover every declared target exactly once")
    for target_id in target_ids:
        failures[target_id] = _bounded_int(failures[target_id], name=f"failures for {target_id}")
        if failures[target_id] > realized:
            raise ValueError("target failures cannot exceed realized shots")
        receipts[target_id] = _sha256(receipts[target_id], name=f"count receipt for {target_id}")
    return look, dispatched, realized, failures, receipts


def finite_look_assessment(
    assessment: CampaignAssessmentV1,
    *,
    observations: tuple[FiniteLookObservationV1, ...],
    input_receipt_hashes: Mapping[str, str],
) -> FiniteLookAssessmentV1:
    """Assess a prefix of the frozen finite-look schedule with alpha spending.

    Only an in-order prefix of declared boundaries is valid.  A partial batch
    retains its dispatch and realized evidence but produces no target verdict;
    it can only be resumed as the same frozen campaign.  Every complete look
    uses its own prespecified local alpha rather than the nominal fixed-final
    interval confidence level.
    """
    if not isinstance(assessment, CampaignAssessmentV1):
        raise ValueError("assessment must be a frozen CampaignAssessmentV1")
    if not isinstance(assessment.stopping, FiniteLookStoppingV1):
        raise ValueError("finite-look assessment rejects fixed-shot stopping plans")
    if not isinstance(observations, tuple) or not observations:
        raise ValueError("finite-look assessment requires a nonempty observation tuple")
    receipts = _receipt_hashes(input_receipt_hashes)
    stopping = assessment.stopping
    target_ids = tuple(target.target_id for target in assessment.targets)
    targets = {target.target_id: target for target in assessment.targets}
    family_memberships: dict[str, list[str]] = {target_id: [] for target_id in target_ids}
    for family in assessment.families:
        for target_id in family.member_target_ids:
            family_memberships[target_id].append(family.family_id)
    if any(len(memberships) != 1 for memberships in family_memberships.values()):
        raise ValueError("finite-look assessment requires each target in exactly one family")
    family_by_target = {
        target_id: memberships[0] for target_id, memberships in family_memberships.items()
    }
    allocation = {
        (item.family_id, item.target_id, item.look): item.alpha
        for item in stopping.alpha_allocations
    }
    records: list[FiniteLookRecordV1] = []
    completed: list[int] = []
    stop_reason: Literal[
        "all_primary_decisions_resolved", "maximum_reached", "partial_batch",
    ] | None = None
    for index, observation in enumerate(observations):
        look, dispatched, realized, failures, count_receipts = _finite_observation(
            observation,
            target_ids=target_ids,
            maximum_shots=assessment.resources.max_shots,
        )
        if index >= len(stopping.cumulative_looks) or look != stopping.cumulative_looks[index]:
            raise ValueError("finite-look observations must be an in-order declared look prefix")
        planned = stopping.cumulative_looks[index]
        if dispatched < planned:
            raise ValueError("declared look cannot be assessed before its planned boundary is dispatched")
        overshoot = realized - planned if realized >= planned else 0
        if realized < planned:
            if index != len(observations) - 1:
                raise ValueError("a partial batch must be the last observed finite look")
            records.append(FiniteLookRecordV1(
                look=look,
                planned_boundary=planned,
                dispatched_shots=dispatched,
                realized_shots=realized,
                overshoot=0,
                complete=False,
                alpha_spent=0.0,
                target_decisions={},
            ))
            return FiniteLookAssessmentV1(
                status="inconclusive_partial_batch",
                completed_looks=tuple(completed),
                look_records=tuple(records),
                stop_reason="partial_batch",
                input_receipt_hashes=receipts,
            )
        decisions: dict[str, TargetIntervalDecisionV1] = {}
        alpha_spent = 0.0
        for target_id in target_ids:
            local_alpha = allocation[(family_by_target[target_id], target_id, look)]
            rate = exact_binomial_rate(
                failures=failures[target_id],
                shots=realized,
                alpha=local_alpha,
                count_receipt_sha256=count_receipts[target_id],
            )
            decision_receipts = dict(receipts)
            decision_receipts[f"count:{target_id}"] = count_receipts[target_id]
            decisions[target_id] = target_interval_decision(
                rate,
                targets[target_id],
                input_receipt_hashes=decision_receipts,
            )
            alpha_spent += local_alpha
        records.append(FiniteLookRecordV1(
            look=look,
            planned_boundary=planned,
            dispatched_shots=dispatched,
            realized_shots=realized,
            overshoot=overshoot,
            complete=True,
            alpha_spent=alpha_spent,
            target_decisions=decisions,
        ))
        completed.append(look)
        resolved = all(item.verdict != "inconclusive" for item in decisions.values())
        if realized >= stopping.minimum_terminal_shots and resolved:
            stop_reason = "all_primary_decisions_resolved"
            if index != len(observations) - 1:
                raise ValueError("finite-look evidence continues after the frozen stop predicate resolved")
            break
        if look == stopping.cumulative_looks[-1]:
            stop_reason = "maximum_reached"
    return FiniteLookAssessmentV1(
        status="complete",
        completed_looks=tuple(completed),
        look_records=tuple(records),
        stop_reason=stop_reason,
        input_receipt_hashes=receipts,
    )
