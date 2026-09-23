"""Strict, persisted configuration for the first canonical CSS tracer."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class PolicySpec(_Strict):
    kind: str = Field(min_length=1)


class CanonicalCompositionSpec(_Strict):
    update: PolicySpec
    schedule: PolicySpec
    state_memory: PolicySpec
    intervention: PolicySpec
    stopping: PolicySpec
    selection: PolicySpec
    postprocessing: PolicySpec


class CanonicalManifestV2(_Strict):
    schema_version: Literal[2]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-spa-v1"]
    max_iterations: int = Field(ge=1, le=100_000)
    error_rate: float = Field(ge=0.0, le=1.0)
    policies: CanonicalCompositionSpec

    @field_validator("error_rate")
    @classmethod
    def finite_rate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("error_rate must be finite")
        return value


def parse_canonical_manifest(value: CanonicalManifestV2 | dict[str, Any] | str) -> CanonicalManifestV2:
    """Parse only the versioned, strict canonical representation."""
    if isinstance(value, CanonicalManifestV2):
        return value
    if isinstance(value, str):
        return CanonicalManifestV2.model_validate_json(value)
    return CanonicalManifestV2.model_validate(value)
