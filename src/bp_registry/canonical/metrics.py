"""Typed observed and unavailable metrics shared by decoder evidence paths."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import numbers
from typing import Any, Mapping


class MetricMissingness(str, Enum):
    """Whether a metric was observed or is explicitly unavailable."""

    OBSERVED = "observed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class MetricFact:
    """A qualified scalar fact that never turns unavailable data into zero."""

    metric: str
    missingness: MetricMissingness
    value: int | float | None
    method: str
    scope: str
    unit: str
    qualification: str
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        for name in ("metric", "method", "scope", "unit", "qualification"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"metric {name} must be a nonempty string")
        try:
            missingness = MetricMissingness(self.missingness)
        except (TypeError, ValueError) as error:
            raise ValueError("metric missingness must be observed or unavailable") from error
        object.__setattr__(self, "missingness", missingness)
        if missingness is MetricMissingness.OBSERVED:
            if isinstance(self.value, bool) or not isinstance(self.value, numbers.Real):
                raise ValueError("observed metric values must be finite nonnegative numbers")
            if not math.isfinite(float(self.value)):
                raise ValueError("observed metric values must be finite")
            if self.value < 0:
                raise ValueError("observed metric values must be nonnegative")
            if self.unavailable_reason is not None:
                raise ValueError("observed metric facts cannot carry an unavailable reason")
        else:
            if self.value is not None:
                raise ValueError("unavailable metric facts must have a null value")
            if not isinstance(self.unavailable_reason, str) or not self.unavailable_reason.strip():
                raise ValueError("unavailable metric facts require a nonempty reason")

    @classmethod
    def observed(
        cls, metric: str, value: int | float, *, method: str, scope: str,
        unit: str, qualification: str,
    ) -> "MetricFact":
        return cls(
            metric=metric, missingness=MetricMissingness.OBSERVED, value=value,
            method=method, scope=scope, unit=unit, qualification=qualification,
        )

    @classmethod
    def unavailable(
        cls, metric: str, *, method: str, scope: str, unit: str,
        qualification: str, reason: str,
    ) -> "MetricFact":
        return cls(
            metric=metric, missingness=MetricMissingness.UNAVAILABLE, value=None,
            method=method, scope=scope, unit=unit, qualification=qualification,
            unavailable_reason=reason,
        )

    def as_evidence(self) -> dict[str, int | float | str | None]:
        """Return the strict portable representation stored in durable evidence."""
        return {
            "metric": self.metric,
            "missingness": self.missingness.value,
            "value": self.value,
            "method": self.method,
            "scope": self.scope,
            "unit": self.unit,
            "qualification": self.qualification,
            "unavailable_reason": self.unavailable_reason,
        }

    @classmethod
    def from_evidence(cls, evidence: Mapping[str, Any]) -> "MetricFact":
        """Validate one tagged, portable metric representation."""
        expected = {
            "metric", "missingness", "value", "method", "scope", "unit",
            "qualification", "unavailable_reason",
        }
        if not isinstance(evidence, Mapping) or set(evidence) != expected:
            raise ValueError("metric evidence must contain exactly the metric-fact fields")
        return cls(**dict(evidence))


def unavailable_metric(
    metric: str, *, method: str, scope: str, unit: str, qualification: str,
    reason: str,
) -> MetricFact:
    """Construct an explicitly unavailable fact without a numeric surrogate."""
    return MetricFact.unavailable(
        metric, method=method, scope=scope, unit=unit,
        qualification=qualification, reason=reason,
    )
