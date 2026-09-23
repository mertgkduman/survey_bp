"""Closed, immutable contracts for canonical CSS policy compositions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class PolicyRole(str, Enum):
    UPDATE = "update"
    SCHEDULE = "schedule"
    STATE_MEMORY = "state_memory"
    INTERVENTION = "intervention"
    STOPPING = "stopping"
    SELECTION = "selection"
    POSTPROCESSING = "postprocessing"


class Hook(str, Enum):
    SHOT = "shot"
    SEARCH = "search"
    MEMBER = "member"
    ATTEMPT = "attempt"
    ITERATION = "iteration"
    MESSAGE = "message"


class StateLifetime(str, Enum):
    SHOT = "shot"
    SEARCH = "search"
    MEMBER = "member"
    ATTEMPT = "attempt"
    ITERATION = "iteration"
    MESSAGE = "message"


_ROLE_HOOKS: dict[PolicyRole, Hook] = {
    PolicyRole.UPDATE: Hook.MESSAGE,
    PolicyRole.SCHEDULE: Hook.ITERATION,
    PolicyRole.STATE_MEMORY: Hook.ITERATION,
    PolicyRole.INTERVENTION: Hook.SEARCH,
    PolicyRole.STOPPING: Hook.ITERATION,
    PolicyRole.SELECTION: Hook.ATTEMPT,
    PolicyRole.POSTPROCESSING: Hook.ATTEMPT,
}
_POLICY_KINDS: dict[PolicyRole, frozenset[str]] = {
    role: frozenset({"identity"}) for role in PolicyRole
}


class PolicySpec(_Strict):
    """Persisted data only: no module paths, callables, or implicit defaults."""

    kind: str = Field(min_length=1, max_length=64)
    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    state_lifetime: Literal["shot", "search", "member", "attempt", "iteration", "message"]
    owned_state: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    hook: Literal["shot", "search", "member", "attempt", "iteration", "message"] | None = None

    @field_validator("owned_state", "requires", "provides", mode="before")
    @classmethod
    def json_arrays_to_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("owned_state", "requires", "provides")
    @classmethod
    def identifiers_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not entry or not entry.replace("_", "").replace("-", "").isalnum() for entry in value):
            raise ValueError("state and capability names must be nonempty identifiers")
        if len(value) != len(set(value)):
            raise ValueError("state and capability declarations must not contain duplicates")
        return value


class CanonicalCompositionSpec(_Strict):
    """Seven explicit roles; omission is never an inactive-policy shorthand."""

    update: PolicySpec
    schedule: PolicySpec
    state_memory: PolicySpec
    intervention: PolicySpec
    stopping: PolicySpec
    selection: PolicySpec
    postprocessing: PolicySpec

    @model_validator(mode="after")
    def has_a_valid_static_graph(self) -> "CanonicalCompositionSpec":
        validate_composition(self)
        return self

    def in_role_order(self) -> tuple[tuple[PolicyRole, PolicySpec], ...]:
        return tuple((role, getattr(self, role.value)) for role in PolicyRole)


@dataclass(frozen=True)
class PolicyBinding:
    """Resolved closed-registry policy identity and declared ownership."""

    binding_id: str
    role: PolicyRole
    hook: Hook
    state_lifetime: StateLifetime
    kind: str
    owned_state: tuple[str, ...]
    requires: tuple[str, ...]
    provides: tuple[str, ...]
    compatibility_reason: str


@dataclass(frozen=True)
class ResolvedComposition:
    bindings: tuple[PolicyBinding, ...]
    semantic_identity: str


class PolicyEvidence(_Strict):
    """Adjacent source/procedure basis and deterministic invariant order."""

    source_anchors: tuple[str, ...] = ()
    procedure: str | None = None
    invariants: tuple[str, ...]

    @field_validator("source_anchors", "invariants", mode="before")
    @classmethod
    def evidence_arrays_to_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def requires_basis_and_invariants(self) -> "PolicyEvidence":
        if not self.source_anchors and not self.procedure:
            raise ValueError("policy evidence requires a source anchor or precise procedure")
        if not self.invariants or any(not item.strip() for item in self.invariants):
            raise ValueError("policy evidence requires nonempty ordered invariants")
        return self


def validate_composition(composition: CanonicalCompositionSpec) -> ResolvedComposition:
    """Resolve only known in-code kinds and reject invalid static ownership graphs."""

    binding_ids: set[str] = set()
    owned_state: set[str] = set()
    provided: set[str] = set()
    bindings: list[PolicyBinding] = []
    for role, spec in composition.in_role_order():
        if spec.kind not in _POLICY_KINDS[role]:
            raise ValueError(f"unknown policy kind {spec.kind!r}; expected a known policy kind for {role.value}")
        if spec.binding_id in binding_ids:
            raise ValueError(f"duplicate binding_id {spec.binding_id!r}")
        binding_ids.add(spec.binding_id)
        expected_hook = _ROLE_HOOKS[role]
        if spec.hook is not None and spec.hook != expected_hook.value:
            raise ValueError(f"unsupported hook {spec.hook!r} for {role.value}; expected {expected_hook.value!r}")
        overlap = owned_state.intersection(spec.owned_state)
        if overlap:
            raise ValueError(f"owned state overlaps across bindings: {sorted(overlap)!r}")
        owned_state.update(spec.owned_state)
        provided.update(spec.provides)
        bindings.append(
            PolicyBinding(
                binding_id=spec.binding_id,
                role=role,
                hook=expected_hook,
                state_lifetime=StateLifetime(spec.state_lifetime),
                kind=spec.kind,
                owned_state=spec.owned_state,
                requires=spec.requires,
                provides=spec.provides,
                compatibility_reason="closed identity-policy registry v1",
            )
        )
    required = {capability for binding in bindings for capability in binding.requires}
    undefined = required.difference(provided)
    if undefined:
        raise ValueError(f"undeclared capabilities: {sorted(undefined)!r}")
    payload = [
        {
            "binding_id": binding.binding_id,
            "role": binding.role.value,
            "hook": binding.hook.value,
            "state_lifetime": binding.state_lifetime.value,
            "kind": binding.kind,
            "owned_state": binding.owned_state,
            "requires": binding.requires,
            "provides": binding.provides,
        }
        for binding in bindings
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return ResolvedComposition(tuple(bindings), hashlib.sha256(encoded.encode("utf-8")).hexdigest())


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
    """Parse only the versioned strict canonical representation."""
    if isinstance(value, CanonicalManifestV2):
        return value
    if isinstance(value, str):
        return CanonicalManifestV2.model_validate_json(value)
    return CanonicalManifestV2.model_validate(value)
