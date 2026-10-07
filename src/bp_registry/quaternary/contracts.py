"""Strict public policy contracts for the four-state quaternary kernel.

These contracts intentionally describe composition data only.  They do not
admit a binary policy merely because it has a familiar name: compatibility is
resolved by :mod:`bp_registry.quaternary.compatibility` before artifact loading
or sampling begins.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class QuaternaryPolicySpec(_Strict):
    """One named policy binding with explicit data-only configuration."""

    kind: str = Field(min_length=1, max_length=80)
    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    state_lifetime: Literal["shot", "attempt", "iteration", "message"] = "attempt"
    owned_state: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("owned_state", "requires", "provides", mode="before")
    @classmethod
    def arrays_are_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("owned_state", "requires", "provides")
    @classmethod
    def names_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)) or any(not item or not item.replace("_", "").isalnum() for item in value):
            raise ValueError("state and capability declarations must be unique identifiers")
        return value


class QuaternaryCompositionSpec(_Strict):
    """The complete Phase 10 composition surface, with no implicit bindings."""

    kernel: QuaternaryPolicySpec | None
    schedule: QuaternaryPolicySpec | None
    transforms: tuple[QuaternaryPolicySpec, ...] = ()
    intervention: QuaternaryPolicySpec | None = None

    @field_validator("transforms", mode="before")
    @classmethod
    def transforms_are_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def roles_are_complete_and_distinct(self) -> "QuaternaryCompositionSpec":
        if self.kernel is None:
            raise ValueError("quaternary composition requires kernel binding")
        if self.schedule is None:
            raise ValueError("quaternary composition requires schedule binding")
        if self.intervention is None:
            raise ValueError("quaternary composition requires intervention binding")
        bindings = (self.kernel, self.schedule, *self.transforms, self.intervention)
        ids = tuple(binding.binding_id for binding in bindings)
        if len(ids) != len(set(ids)):
            raise ValueError("quaternary composition binding IDs must be unique")
        return self

    def in_role_order(self) -> tuple[tuple[str, QuaternaryPolicySpec], ...]:
        assert self.kernel is not None and self.schedule is not None and self.intervention is not None
        return (
            ("kernel", self.kernel),
            ("schedule", self.schedule),
            *(("transform", binding) for binding in self.transforms),
            ("intervention", self.intervention),
        )


class QuaternaryResolvedComposition(_Strict):
    """Persisted compatibility decision, including source and lifecycle evidence."""

    component_fidelity: dict[str, Literal["source_backed", "canonical_adaptation"]]
    run_fidelity: Literal["source_backed", "canonical_adaptation"]
    procedure_basis: str = Field(min_length=1)
    effective_order: tuple[str, ...] = Field(min_length=1)
    equations: dict[str, str] = Field(min_length=1)
    source_revision: tuple[str, ...] = Field(min_length=1)
    lifecycle: dict[str, str] = Field(min_length=1)
    adaptation_reasons: tuple[str, ...] = ()
    semantic_identity: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("effective_order", "source_revision", "adaptation_reasons", mode="before")
    @classmethod
    def sequences_are_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value


__all__ = [
    "QuaternaryCompositionSpec",
    "QuaternaryPolicySpec",
    "QuaternaryResolvedComposition",
]
