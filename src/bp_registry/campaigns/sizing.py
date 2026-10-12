"""Prespecified exact paired design and bounded resource projections."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from typing import Any, Literal

import numpy as np
from pydantic import Field, StrictInt, field_validator, model_validator
from scipy.stats import binom

from ..manifests import StrictModel
from .contracts import canonical_json_bytes


_SHA256 = r"^[0-9a-f]{64}$"


class PairedDesignV1(StrictModel):
    """One fixed all-shot McNemar question calibrated outside evaluation."""

    schema_name: Literal["paired_design_v1"] = Field(alias="schema", serialization_alias="schema")
    family_id: str = Field(min_length=1, max_length=128)
    arm_order: tuple[str, ...] = Field(min_length=2, max_length=16)
    estimand: Literal["paired_all_shot_risk_difference_v1"]
    minimum_relevant_difference: float
    calibration_discordance: float
    target_power: float
    familywise_alpha: float
    family_size: StrictInt = Field(ge=1, le=120)
    max_pairs: StrictInt = Field(ge=1, le=5_000)
    calibration_namespace: str = Field(min_length=1, max_length=256)
    evaluation_namespace: str = Field(min_length=1, max_length=256)
    calibration_receipt_sha256: str = Field(pattern=_SHA256)
    evaluation_namespace_sha256: str = Field(pattern=_SHA256)

    @field_validator("arm_order", mode="before")
    @classmethod
    def tuple_arms(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def valid_disjoint_design(self) -> "PairedDesignV1":
        if len(set(self.arm_order)) != len(self.arm_order) or any(not arm for arm in self.arm_order):
            raise ValueError("paired design arms must be unique and nonempty")
        values = (self.minimum_relevant_difference, self.calibration_discordance,
                  self.target_power, self.familywise_alpha)
        if any(not math.isfinite(value) for value in values):
            raise ValueError("paired design probabilities must be finite")
        if not (0 < self.minimum_relevant_difference <= self.calibration_discordance <= 1):
            raise ValueError("relevant effect must fit the calibrated discordance")
        if not (0 < self.target_power < 1 and 0 < self.familywise_alpha < 1):
            raise ValueError("target power and familywise alpha must be in (0,1)")
        if (self.calibration_namespace == self.evaluation_namespace
                or self.calibration_receipt_sha256 == self.evaluation_namespace_sha256):
            raise ValueError("calibration and evaluation identities must be disjoint")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return sha256(b"bp-registry-paired-design-v1\0" + self.primitive_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class PairedSizingResultV1:
    status: Literal["powered", "blocked_precision"]
    design_sha256: str
    required_n: int | None
    power_at_required_n: float | None
    achieved_power_at_cap: float
    assumptions: dict[str, Any]

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes({
            "schema": "paired_sizing_result_v1", "status": self.status,
            "design_sha256": self.design_sha256, "required_n": self.required_n,
            "power_at_required_n": self.power_at_required_n,
            "achieved_power_at_cap": self.achieved_power_at_cap,
            "assumptions": self.assumptions,
        })


def _conditional_rejection_probability(m: int, *, alternative: float, alpha: float) -> float:
    if m == 0:
        return 0.0
    # The two-sided exact binomial test under p=1/2 rejects in symmetric
    # tails. Find the last integer whose doubled lower tail meets alpha.
    critical = int(binom.ppf(alpha / 2, m, 0.5))
    while critical >= 0 and 2 * binom.cdf(critical, m, 0.5) > alpha:
        critical -= 1
    if critical < 0:
        return 0.0
    if 2 * critical >= m:
        return 1.0
    return float(binom.cdf(critical, m, alternative)
                 + binom.sf(m - critical - 1, m, alternative))


def paired_design_size(design: PairedDesignV1) -> PairedSizingResultV1:
    """Return the first bounded N meeting exact unconditional paired power."""
    if not isinstance(design, PairedDesignV1):
        raise ValueError("paired sizing requires a validated prospective design")
    q = design.calibration_discordance
    theta = (q + design.minimum_relevant_difference) / (2 * q)
    local_alpha = design.familywise_alpha / design.family_size
    rejection = np.zeros(design.max_pairs + 1, dtype=np.float64)
    for m in range(1, design.max_pairs + 1):
        rejection[m] = _conditional_rejection_probability(m, alternative=theta, alpha=local_alpha)
    distribution = np.array([1.0], dtype=np.float64)
    required: int | None = None
    power_at_required: float | None = None
    achieved = 0.0
    for n in range(1, design.max_pairs + 1):
        distribution = np.pad(distribution * (1 - q), (0, 1)) + np.pad(distribution * q, (1, 0))
        achieved = float(np.dot(distribution, rejection[:n + 1]))
        if required is None and achieved >= design.target_power:
            required, power_at_required = n, achieved
    assumptions = design.model_dump(mode="json", by_alias=True)
    return PairedSizingResultV1(
        status="powered" if required is not None else "blocked_precision",
        design_sha256=design.digest(), required_n=required,
        power_at_required_n=power_at_required, achieved_power_at_cap=achieved,
        assumptions=assumptions,
    )
