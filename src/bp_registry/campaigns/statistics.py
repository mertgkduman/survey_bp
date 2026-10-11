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

from .contracts import TargetReferenceV1


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
