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
from typing import Literal, Mapping

from scipy.stats import binomtest

from .contracts import CampaignAssessmentV1, FiniteLookStoppingV1, TargetReferenceV1


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_SHOTS = 1_000_000
_RULE_ID = "target_interval_containment_v1"


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
