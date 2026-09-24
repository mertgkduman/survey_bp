"""Closed check-update rules for the canonical binary CSS kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Literal, Protocol

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .numerics import MIN_SUM_CPU_F64, NumericalProfile, finite_saturate


class CheckUpdateRule(Protocol):
    """A decoder-visible, deterministic check-to-variable rule."""

    def check_to_variable(
        self, incoming: np.ndarray, *, syndrome: int, check_index: int = 0,
        edge_index: int = 0, source_iteration: int = 0,
    ) -> float: ...

    def evidence(self) -> "UpdateRuleEvidence": ...


@dataclass(frozen=True, slots=True)
class UpdateRuleEvidence:
    """Named procedure and numerical identity retained beside terminal evidence."""

    kind: str
    numerical_profile: str
    procedure: str
    provenance: str = "source_defined"
    declared_assignment: dict[str, Any] | None = None
    resolved_assignment: tuple[float, ...] | None = None

    def as_evidence(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MinSumUpdate:
    """Float64 binary min-sum with inherited degree-one and sign conventions."""

    profile: NumericalProfile = MIN_SUM_CPU_F64

    def check_to_variable(
        self, incoming: np.ndarray, *, syndrome: int, check_index: int = 0,
        edge_index: int = 0, source_iteration: int = 0,
    ) -> float:
        values = finite_saturate(incoming, boundary="min_sum_input", profile=self.profile)
        if values.ndim != 1:
            raise ValueError("min_sum_input must be a one-dimensional LLR array")
        if type(syndrome) not in (int, np.int64, np.int32) or int(syndrome) not in (0, 1):
            raise ValueError("syndrome must be a binary integer")
        # An empty extrinsic set is a degree-one check.  Zero has positive sign
        # for the product, preserving the inherited deterministic convention.
        magnitude = self.profile.saturation if values.size == 0 else float(np.min(np.abs(values)))
        negative_count = int(np.count_nonzero(values < 0.0))
        sign = -1.0 if (negative_count + int(syndrome)) % 2 else 1.0
        return float(finite_saturate(sign * magnitude, boundary="min_sum_output", profile=self.profile))

    def evidence(self) -> UpdateRuleEvidence:
        return UpdateRuleEvidence(
            kind="min_sum",
            numerical_profile=self.profile.profile_id,
            procedure="signed extrinsic minimum with zero-positive sign product and post-magnitude saturation",
        )


class ParameterAssignment(BaseModel):
    """One explicit normalization assignment, never an inferred broadcast."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

    shape: Literal["scalar", "source_iteration", "check", "edge"]
    value: float | None = None
    values: tuple[float, ...] | None = None
    graph_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("values", mode="before")
    @classmethod
    def values_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("value")
    @classmethod
    def scalar_is_nonnegative_finite(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or value < 0.0):
            raise ValueError("parameter values must be finite and nonnegative")
        return value

    @field_validator("values")
    @classmethod
    def vector_is_nonnegative_finite(cls, value: tuple[float, ...] | None) -> tuple[float, ...] | None:
        if value is not None and (not value or any(not math.isfinite(item) or item < 0.0 for item in value)):
            raise ValueError("parameter values must be a nonempty finite nonnegative vector")
        return value

    @model_validator(mode="after")
    def shape_has_one_unambiguous_payload(self) -> "ParameterAssignment":
        if self.shape == "scalar":
            if self.value is None or self.values is not None or self.graph_sha256 is not None:
                raise ValueError("scalar assignment requires exactly value")
        elif self.shape == "source_iteration":
            if self.values is None or self.value is not None or self.graph_sha256 is not None:
                raise ValueError("source_iteration assignment requires exactly values")
        elif self.values is None or self.value is not None or self.graph_sha256 is None:
            raise ValueError(f"{self.shape} assignment requires graph_sha256 and exactly values")
        return self

    @property
    def provenance(self) -> str:
        value = self.value if self.shape == "scalar" else max(self.values or (0.0,))
        return "conventional" if 0.0 < value <= 1.0 else "exploratory"

    def resolve(
        self, *, graph_sha256: str, check_count: int, edge_count: int,
        source_iteration: int, edge_checks: tuple[int, ...] | None = None,
    ) -> np.ndarray:
        """Resolve against immutable canonical identities before numerical execution."""
        if not all(type(item) is int and item >= 0 for item in (check_count, edge_count, source_iteration)):
            raise ValueError("assignment dimensions and source_iteration must be nonnegative integers")
        if self.shape == "scalar":
            assert self.value is not None
            return np.full(edge_count, self.value, dtype=np.float64)
        if self.shape == "source_iteration":
            assert self.values is not None
            if source_iteration >= len(self.values):
                raise ValueError("source_iteration assignment has no declared value for this iteration")
            return np.full(edge_count, self.values[source_iteration], dtype=np.float64)
        if self.graph_sha256 != graph_sha256:
            raise ValueError("parameter assignment graph_sha256 does not match the immutable graph")
        assert self.values is not None
        if self.shape == "edge":
            if len(self.values) != edge_count:
                raise ValueError("edge assignment length must equal canonical EdgeTable edge_count")
            return np.asarray(self.values, dtype=np.float64)
        if len(self.values) != check_count:
            raise ValueError("check assignment length must equal immutable check_count")
        if edge_checks is None or len(edge_checks) != edge_count or any(not 0 <= check < check_count for check in edge_checks):
            raise ValueError("check assignment requires one canonical check identity per edge")
        return np.asarray([self.values[check] for check in edge_checks], dtype=np.float64)

    def as_evidence(self, resolved: np.ndarray) -> dict[str, Any]:
        return {
            "declared": self.model_dump(mode="json"), "resolved": [float(item) for item in resolved],
            "provenance": self.provenance,
        }


@dataclass(frozen=True, slots=True)
class NormalizedMinSumUpdate:
    """Float64 min-sum whose magnitude is scaled before final saturation."""

    alpha: ParameterAssignment
    profile: NumericalProfile = MIN_SUM_CPU_F64
    resolved_alpha: tuple[float, ...] | None = None

    def check_to_variable(
        self, incoming: np.ndarray, *, syndrome: int, check_index: int = 0,
        edge_index: int = 0, source_iteration: int = 0,
    ) -> float:
        if type(edge_index) is not int or edge_index < 0:
            raise ValueError("edge_index must be a nonnegative integer")
        if self.resolved_alpha is None:
            if self.alpha.shape != "scalar":
                raise ValueError("non-scalar normalization must be resolved against an immutable graph before use")
            multiplier = self.alpha.value
        else:
            if edge_index >= len(self.resolved_alpha):
                raise ValueError("edge_index is outside the resolved normalization assignment")
            multiplier = self.resolved_alpha[edge_index]
        assert multiplier is not None
        values = finite_saturate(incoming, boundary="normalized_min_sum_input", profile=self.profile)
        if values.ndim != 1:
            raise ValueError("normalized_min_sum_input must be a one-dimensional LLR array")
        if type(syndrome) not in (int, np.int64, np.int32) or int(syndrome) not in (0, 1):
            raise ValueError("syndrome must be a binary integer")
        magnitude = self.profile.saturation if values.size == 0 else float(np.min(np.abs(values)))
        sign = -1.0 if (int(np.count_nonzero(values < 0.0)) + int(syndrome)) % 2 else 1.0
        return float(finite_saturate(sign * float(multiplier) * magnitude, boundary="normalized_min_sum_output", profile=self.profile))

    def evidence(self) -> UpdateRuleEvidence:
        return UpdateRuleEvidence(
            kind="normalized_min_sum", numerical_profile=self.profile.profile_id,
            procedure="signed extrinsic minimum scaled by an explicit graph-bound normalization before saturation",
            provenance=self.alpha.provenance,
            declared_assignment=self.alpha.model_dump(mode="json"),
            resolved_assignment=self.resolved_alpha,
        )
