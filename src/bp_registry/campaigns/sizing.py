"""Prespecified exact paired design and bounded resource projections."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from typing import Any, Literal, Mapping

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


def _positive_integer(value: object, *, name: str) -> int:
    if type(value) is not int or value < 1 or value > 2**63 - 1:
        raise ValueError(f"{name} must be a positive bounded integer")
    return value


def project_measured_resources(
    *, design: PairedDesignV1, method: str, profile: Mapping[str, Any],
    local_wall_cap_ns: int, local_storage_cap_bytes: int, local_rss_cap_bytes: int,
    safety_numerator: int, safety_denominator: int,
) -> dict[str, Any]:
    """Apply only one independently verified mechanism profile to local caps."""
    if not isinstance(design, PairedDesignV1):
        raise ValueError("resource projection requires a frozen paired design")
    if method not in {"relay", "beam", "mbbp", "spa_flooding", "spa_check_node_serial"} or profile.get("method") != method:
        raise ValueError("mechanism profile method differs from its projection")
    if (profile.get("schema") != "mechanism_profile_receipt_v1"
            or profile.get("verified") is not True
            or profile.get("publication_slurm_authorization") != "deny"
            or profile.get("profile_namespace") != design.calibration_namespace):
        raise ValueError("mechanism profile lacks verified disjoint local identity")
    for name in ("source_receipt_sha256", "replay_receipt_sha256"):
        value = profile.get(name)
        if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("mechanism profile lacks a sealed source or replay digest")
    wall_cap = _positive_integer(local_wall_cap_ns, name="local_wall_cap_ns")
    storage_cap = _positive_integer(local_storage_cap_bytes, name="local_storage_cap_bytes")
    rss_cap = _positive_integer(local_rss_cap_bytes, name="local_rss_cap_bytes")
    numerator = _positive_integer(safety_numerator, name="safety_numerator")
    denominator = _positive_integer(safety_denominator, name="safety_denominator")
    if numerator < denominator:
        raise ValueError("resource safety factor must be at least one")
    measurements = profile.get("measurements")
    if not isinstance(measurements, Mapping):
        raise ValueError("mechanism profile lacks typed measurements")
    required = ("execution_wall_ns", "execution_cpu_ns", "replay_wall_ns",
                "peak_rss_bytes", "storage_bytes", "evidence_bytes")
    missing: list[str] = []
    values: dict[str, int] = {}
    for name in required:
        item = measurements.get(name)
        if not isinstance(item, Mapping) or item.get("status") != "observed":
            missing.append(name)
            continue
        value = item.get("value")
        unit = "ns" if name.endswith("_ns") else "bytes"
        if type(value) is not int or value < 1 or value > 2**63 - 1 or item.get("unit") != unit:
            raise ValueError("mechanism profile measurement is invalid")
        values[name] = value
    def scaled(name: str) -> int:
        value = values[name] * numerator
        if value > (2**63 - 1) * denominator:
            raise ValueError("resource projection overflows the supported counter")
        return (value + denominator - 1) // denominator
    if missing:
        bounded_n = 0
        bounded_power = None
        projected = None
        status = "blocked_no_matched_evidence"
    else:
        per_wall, per_storage, per_rss = scaled("execution_wall_ns"), scaled("storage_bytes"), scaled("peak_rss_bytes")
        bounded_n = min(design.max_pairs, wall_cap // per_wall, storage_cap // per_storage)
        if per_rss > rss_cap:
            bounded_n = 0
        projected = {name: scaled(name) * bounded_n for name in required}
        if any(value > 2**63 - 1 for value in projected.values()):
            raise ValueError("resource projection overflows the supported counter")
        bounded_power = (paired_design_size(design.model_copy(update={"max_pairs": bounded_n})).achieved_power_at_cap
                         if bounded_n else None)
        status = ("blocked_no_matched_evidence" if bounded_n == 0 else
                  "bounded_local_ready" if bounded_n == design.max_pairs else "bounded_exploratory")
    unsigned = {
        "schema": "measured_resource_projection_v1", "design_sha256": design.digest(),
        "profile_method": method, "source_receipt_sha256": profile["source_receipt_sha256"],
        "replay_receipt_sha256": profile["replay_receipt_sha256"],
        "status": status, "bounded_n": bounded_n, "achieved_power": bounded_power,
        "missing_measurements": missing, "projected_costs": projected,
        "local_caps": {"wall_ns": wall_cap, "storage_bytes": storage_cap, "rss_bytes": rss_cap},
        "safety_factor": {"numerator": numerator, "denominator": denominator},
        "site_ceiling_status": "unavailable", "publication_slurm_authorization": "deny",
    }
    return {**unsigned, "projection_sha256": sha256(b"bp-registry-measured-resource-projection-v1\0"
                                                 + canonical_json_bytes(unsigned)).hexdigest()}
