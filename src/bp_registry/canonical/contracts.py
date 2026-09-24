"""Closed, immutable contracts for canonical CSS policy compositions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .updates import ParameterAssignment, ParameterGeneratorSpec, ParameterRefreshPlan


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
    LEG = "leg"
    BRANCH = "branch"
    ATTEMPT = "attempt"
    ITERATION = "iteration"
    MESSAGE = "message"


class StateLifetime(str, Enum):
    SHOT = "shot"
    SEARCH = "search"
    MEMBER = "member"
    LEG = "leg"
    BRANCH = "branch"
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
    PolicyRole.UPDATE: frozenset({"identity", "binary_spa", "min_sum", "normalized_min_sum", "offset_min_sum"}),
    PolicyRole.SCHEDULE: frozenset({
        "identity", "flooding", "layered", "check_node_serial",
        "variable_node_serial", "residual", "randomized", "group_shuffled",
    }),
    PolicyRole.STATE_MEMORY: frozenset({"identity", "stateless"}),
    PolicyRole.INTERVENTION: frozenset({"identity"}),
    PolicyRole.STOPPING: frozenset({"identity", "syndrome_or_budget"}),
    PolicyRole.SELECTION: frozenset({"identity", "stable_first"}),
    PolicyRole.POSTPROCESSING: frozenset({"identity"}),
}


class PolicySpec(_Strict):
    """Persisted data only: no module paths, callables, or implicit defaults."""

    kind: str = Field(min_length=1, max_length=64)
    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    state_lifetime: Literal["shot", "search", "member", "leg", "branch", "attempt", "iteration", "message"]
    owned_state: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    hook: Literal["shot", "search", "member", "leg", "branch", "attempt", "iteration", "message"] | None = None

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


class PolicySpecV3(PolicySpec):
    """V3-only update extension; V2's persisted policy schema remains byte-stable."""

    parameter_assignment: ParameterAssignment | None = None
    parameter_generator: ParameterGeneratorSpec | None = None
    parameter_refresh: ParameterRefreshPlan | None = None

    @model_validator(mode="after")
    def normalization_is_explicit_and_scoped_to_the_update_role(self) -> "PolicySpecV3":
        parameterized = {"normalized_min_sum", "offset_min_sum"}
        generated = self.parameter_generator is not None or self.parameter_refresh is not None
        if self.kind in parameterized and self.parameter_assignment is None and not generated:
            raise ValueError(f"{self.kind} requires one explicit parameter_assignment or generated assignment plan")
        if self.kind not in parameterized and (self.parameter_assignment is not None or generated):
            raise ValueError("parameter assignment controls are valid only for normalized_min_sum or offset_min_sum")
        if self.parameter_assignment is not None and generated:
            raise ValueError("explicit parameter_assignment cannot be combined with generated assignment controls")
        if generated and (self.parameter_generator is None or self.parameter_refresh is None):
            raise ValueError("generated assignments require both parameter_generator and parameter_refresh")
        if self.parameter_generator is not None and self.parameter_refresh is not None:
            if self.parameter_refresh.generator is not None and self.parameter_refresh.generator != self.parameter_generator:
                raise ValueError("parameter_refresh generator must match parameter_generator")
        return self


class SchedulePolicySpecV3(PolicySpec):
    """Persisted layered membership is explicit, graph-bound configuration data."""

    partitions: tuple[tuple[int, ...], ...] | None = None
    provenance: Literal["explicit", "source_explicit", "graph_coloring"] | None = None
    construction_rule: str | None = None
    base_schedule: Literal["layered", "check_node_serial", "variable_node_serial"] | None = None
    refresh_scope: Literal["configuration", "attempt", "sweep"] | None = None
    root_identity: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_id: Literal["hsu-ndgsbp-2012-v1"] | None = None

    @field_validator("partitions", mode="before")
    @classmethod
    def json_partitions_to_tuples(cls, value: Any) -> Any:
        if isinstance(value, list):
            return tuple(tuple(layer) if isinstance(layer, list) else layer for layer in value)
        return value

    @model_validator(mode="after")
    def layered_controls_match_the_declared_kind(self) -> "SchedulePolicySpecV3":
        layered = self.kind == "layered"
        randomized = self.kind == "randomized"
        group_shuffled = self.kind == "group_shuffled"
        if randomized and self.base_schedule is not None and self.base_schedule != "layered":
            raise ValueError("public randomized schedules require a layered base_schedule")
        needs_layers = layered or (randomized and self.base_schedule == "layered")
        if needs_layers:
            if self.partitions is None or self.provenance is None:
                raise ValueError("layered schedules require explicit partitions and provenance")
            if self.provenance == "graph_coloring" and not self.construction_rule:
                raise ValueError("graph_coloring layered schedules require a construction_rule")
            if self.provenance != "graph_coloring" and self.construction_rule is not None:
                raise ValueError("only graph_coloring layered schedules may carry construction_rule")
        elif self.partitions is not None or self.provenance is not None or self.construction_rule is not None:
            raise ValueError("schedule controls are valid only for layered schedules")
        randomized_controls = (self.base_schedule, self.refresh_scope)
        if randomized:
            if any(value is None for value in randomized_controls) or self.root_identity is None or self.source_id is not None:
                raise ValueError("randomized schedules require base_schedule, refresh_scope, and root_identity")
        elif group_shuffled:
            if any(value is not None for value in randomized_controls) or self.root_identity is None or self.source_id != "hsu-ndgsbp-2012-v1":
                raise ValueError("group_shuffled requires the Hsu source_id and a root_identity only")
        elif any(value is not None for value in randomized_controls) or self.root_identity is not None or self.source_id is not None:
            raise ValueError("randomized controls are valid only for randomized schedules")
        return self


class CanonicalCompositionSpecV3(CanonicalCompositionSpec):
    """V3 carries NMS assignments only on the update binding."""

    update: PolicySpecV3
    schedule: SchedulePolicySpecV3


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
    evidence: "PolicyEvidence"


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


class SearchRelationship(str, Enum):
    INDEPENDENT = "independent"
    RESTARTED = "restarted"
    BRANCHED = "branched"
    RELAYED = "relayed"


class ExecutionTopology(str, Enum):
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    BATCHED = "batched"


class RelayPayload(_Strict):
    """The only transferable relay state is a registered, typed payload."""

    kind: Literal["canonical-relay-v1"]
    values: tuple[int, ...] = Field(min_length=1)

    @field_validator("values", mode="before")
    @classmethod
    def relay_values_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("values")
    @classmethod
    def relay_values_are_bits(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(type(item) is not int or item not in (0, 1) for item in value):
            raise ValueError("relay payload values must be binary integers")
        return value


class SearchPlan(_Strict):
    """Relationship and execution topology are deliberately separate dimensions."""

    model_config = ConfigDict(extra="forbid", strict=False, frozen=True, allow_inf_nan=False)
    relationship: SearchRelationship
    topology: ExecutionTopology
    budget_scope: Literal["shot", "search", "member", "leg", "branch", "attempt"]
    relay_payload: RelayPayload | None = None

    @model_validator(mode="after")
    def relay_is_explicit_and_exclusive(self) -> "SearchPlan":
        if self.relationship is SearchRelationship.RELAYED and self.relay_payload is None:
            raise ValueError("relayed relationships require a registered relay payload")
        if self.relationship is not SearchRelationship.RELAYED and self.relay_payload is not None:
            raise ValueError("relay payload is only valid for a relayed relationship")
        return self


class PolicyDecision(_Strict):
    """Policy output is data the engine validates before applying any mutation."""

    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    hook: Literal["shot", "search", "member", "leg", "branch", "attempt", "iteration", "message"]
    action: Literal["continue", "terminate", "state_update"]
    state_updates: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def state_updates_match_action(self) -> "PolicyDecision":
        if self.action != "state_update" and self.state_updates:
            raise ValueError("only state_update decisions may carry state updates")
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
                compatibility_reason="closed canonical CSS policy registry v1",
                evidence=PolicyEvidence(
                    procedure=f"Registered {spec.kind} policy follows the canonical CSS v1 procedure.",
                    invariants=(
                        "The policy receives only its declared decoder-visible capability view.",
                        "The policy may mutate only declared private state through a typed decision.",
                    ),
                ),
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


class CanonicalManifestV3(_Strict):
    """Compact kernel contract for promoted V3 local-step tracers."""

    schema_version: Literal[3]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-min-sum-v1", "cpu-float64-spa-v1"]
    max_iterations: int = Field(ge=1, le=100_000)
    error_rate: float = Field(ge=0.0, le=1.0)
    policies: CanonicalCompositionSpecV3

    @field_validator("error_rate")
    @classmethod
    def finite_rate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("error_rate must be finite")
        return value


class MemoryAdvanceBoundary(str, Enum):
    """The one declared point at which a binding may replace its history."""

    LOCAL_UPDATE = "local_update"
    SOURCE_ITERATION = "source_iteration"


class MemoryRefreshBoundary(str, Enum):
    """The controller-owned boundary that starts a retained or reset lifetime."""

    ATTEMPT_START = "attempt_start"
    LEG_START = "leg_start"
    LOCAL_UPDATE = "local_update"
    SOURCE_ITERATION = "source_iteration"


class MemoryBindingSpec(_Strict):
    """One ordered, separately owned memory policy binding.

    The binding is intentionally declarative.  It records every ownership and
    lifecycle choice before a schedule can sample, advance, or commit state.
    """

    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    kind: Literal["affine_prior", "v2c_damping", "pdbp_field_mix", "pdprime_delta_mix", "posterior_momentum"]
    target: Literal["prior", "v2c", "belief", "posterior"]
    parameters: dict[str, float]
    order: int = Field(ge=0, le=1_000)
    history_owner: str = Field(pattern=r"^[a-z][a-z0-9:_-]{0,127}$")
    state_lifetime: Literal["shot", "search", "member", "leg", "branch", "attempt", "iteration", "message"]
    advance_boundary: MemoryAdvanceBoundary
    refresh_boundary: MemoryRefreshBoundary
    source_status: Literal["source_defined", "canonical_adaptation", "exploratory"]
    retain_history: bool = False

    @field_validator("parameters")
    @classmethod
    def parameters_are_finite(cls, value: dict[str, float]) -> dict[str, float]:
        if not value or any(not isinstance(name, str) or not name or not isinstance(item, float) or not math.isfinite(item)
                            for name, item in value.items()):
            raise ValueError("memory parameters must be a nonempty finite float mapping")
        return value

    @model_validator(mode="after")
    def kind_target_and_parameters_are_explicit(self) -> "MemoryBindingSpec":
        expected = {
            "affine_prior": ("prior", {"alpha"}),
            "v2c_damping": ("v2c", {"gamma"}),
            "pdbp_field_mix": ("belief", {"gamma"}),
            "pdprime_delta_mix": ("belief", {"gamma"}),
            "posterior_momentum": ("posterior", {"beta"}),
        }
        target, parameter_names = expected[self.kind]
        if self.target != target:
            raise ValueError(f"{self.kind} may target only {target}")
        if set(self.parameters) != parameter_names:
            raise ValueError(f"{self.kind} requires exactly {sorted(parameter_names)!r} parameters")
        coefficient = next(iter(self.parameters.values()))
        if not 0.0 <= coefficient <= 1.0:
            raise ValueError("memory coefficients must be in [0, 1]")
        if self.retain_history and self.refresh_boundary not in {MemoryRefreshBoundary.ATTEMPT_START, MemoryRefreshBoundary.LEG_START}:
            raise ValueError("retained memory history requires an attempt_start or leg_start refresh boundary")
        return self


class MemoryCompositionSpec(_Strict):
    """A closed ordered chain of memory bindings with no implicit owner/order."""

    bindings: tuple[MemoryBindingSpec, ...] = Field(min_length=1, max_length=64)

    @field_validator("bindings", mode="before")
    @classmethod
    def bindings_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def ordering_and_ownership_are_disjoint(self) -> "MemoryCompositionSpec":
        ids = tuple(binding.binding_id for binding in self.bindings)
        orders = tuple(binding.order for binding in self.bindings)
        owners = tuple(binding.history_owner for binding in self.bindings)
        if len(ids) != len(set(ids)):
            raise ValueError("memory bindings must have distinct binding_id values")
        if len(owners) != len(set(owners)):
            raise ValueError("memory bindings must have disjoint history_owner values")
        if tuple(sorted(orders)) != tuple(range(len(self.bindings))):
            raise ValueError("memory binding order must be a contiguous explicit sequence beginning at zero")
        if orders != tuple(range(len(self.bindings))):
            raise ValueError("memory bindings must be stored in their explicit execution order")
        return self


class CanonicalManifestV5(_Strict):
    """Versioned manifest carrying the ordered Phase 4 memory composition."""

    schema_version: Literal[5]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-min-sum-v1", "cpu-float64-spa-v1"]
    max_iterations: int = Field(ge=1, le=100_000)
    error_rate: float = Field(ge=0.0, le=1.0)
    policies: CanonicalCompositionSpecV3
    memory: MemoryCompositionSpec

    @field_validator("error_rate")
    @classmethod
    def finite_rate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("error_rate must be finite")
        return value


class MemoryBindingV4(_Strict):
    """One explicitly ordered affine-prior memory binding."""

    binding_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    kind: Literal["affine_prior"]
    target: Literal["prior"]
    order: int = Field(ge=0, le=1_000)
    alpha: float = Field(ge=0.0, le=1.0)
    state_lifetime: Literal["leg"]

    @field_validator("alpha")
    @classmethod
    def finite_alpha(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("affine prior alpha must be finite")
        return value


class RelayLegSpec(_Strict):
    """A fresh canonical BP leg; no predecessor messages or history are persisted."""

    max_iterations: int = Field(ge=1, le=100_000)


class RelaySpecV4(_Strict):
    """Sequential Relay topology with an unambiguous total leg count."""

    total_leg_limit: int = Field(ge=2, le=10_000)
    legs: tuple[RelayLegSpec, ...] = Field(min_length=2)

    @field_validator("legs", mode="before")
    @classmethod
    def relay_legs_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def leg_limit_matches_explicit_legs(self) -> "RelaySpecV4":
        if self.total_leg_limit != len(self.legs):
            raise ValueError("total_leg_limit must equal the number of explicit Relay legs")
        return self


class CanonicalManifestV4(_Strict):
    """Phase 4 strict Relay-BP extension; V2/V3 contracts stay unchanged."""

    schema_version: Literal[4]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-spa-v1"]
    max_iterations: int = Field(ge=1, le=100_000)
    error_rate: float = Field(ge=0.0, le=1.0)
    policies: CanonicalCompositionSpec
    memory_bindings: tuple[MemoryBindingV4, ...] = Field(min_length=1)
    relay: RelaySpecV4

    @field_validator("memory_bindings", mode="before")
    @classmethod
    def memory_bindings_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("error_rate")
    @classmethod
    def finite_rate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("error_rate must be finite")
        return value

    @model_validator(mode="after")
    def memory_order_and_ownership_are_explicit(self) -> "CanonicalManifestV4":
        ids = tuple(binding.binding_id for binding in self.memory_bindings)
        orders = tuple(binding.order for binding in self.memory_bindings)
        if len(ids) != len(set(ids)):
            raise ValueError("memory bindings must have distinct binding_id values")
        if len(orders) != len(set(orders)) or tuple(sorted(orders)) != tuple(range(len(orders))):
            raise ValueError("memory binding order must be a contiguous explicit sequence beginning at zero")
        return self


def parse_canonical_manifest(value: CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5 | dict[str, Any] | str) -> CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5:
    """Parse only the versioned strict canonical representation."""
    if isinstance(value, (CanonicalManifestV2, CanonicalManifestV3, CanonicalManifestV4, CanonicalManifestV5)):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
    else:
        decoded = value
    if not isinstance(decoded, dict):
        raise ValueError("canonical manifest must be an object")
    schema_version = decoded.get("schema_version")
    if schema_version == 5:
        return CanonicalManifestV5.model_validate(decoded)
    if schema_version == 4:
        return CanonicalManifestV4.model_validate(decoded)
    return CanonicalManifestV3.model_validate(decoded) if schema_version == 3 else CanonicalManifestV2.model_validate(decoded)
