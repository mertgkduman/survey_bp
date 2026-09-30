"""Closed, immutable contracts for canonical CSS policy compositions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer, model_validator

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


class CanonicalCompositionSpecV6(_Strict):
    """Phase 5 composition; earlier versions keep their closed intervention registry."""

    update: PolicySpecV3
    schedule: SchedulePolicySpecV3
    state_memory: PolicySpec
    intervention: PolicySpec
    stopping: PolicySpec
    selection: PolicySpec
    postprocessing: PolicySpec

    def in_role_order(self) -> tuple[tuple[PolicyRole, PolicySpec], ...]:
        return tuple((role, getattr(self, role.value)) for role in PolicyRole)

    @model_validator(mode="after")
    def has_a_valid_static_graph(self) -> "CanonicalCompositionSpecV6":
        validate_composition(self)
        return self


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


class FinitePriorBiasAction(_Strict):
    kind: Literal["finite_prior_bias"]
    target_index: int = Field(ge=0)
    signed_llr: float

    @model_validator(mode="after")
    def nonzero_finite_field(self) -> "FinitePriorBiasAction":
        if self.signed_llr == 0.0:
            raise ValueError("finite-prior action requires a nonzero signed field")
        return self


class ExactCoordinateFixAction(_Strict):
    kind: Literal["exact_coordinate_fix"]
    target_index: int = Field(ge=0)
    bit_value: Literal[0, 1]


class SyndromeXorAction(_Strict):
    kind: Literal["syndrome_xor"]
    test_vector: tuple[int, ...] = Field(min_length=1)

    @field_validator("test_vector", mode="before")
    @classmethod
    def json_vector_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("test_vector")
    @classmethod
    def binary_test_vector(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(type(bit) is not int or bit not in (0, 1) for bit in value):
            raise ValueError("syndrome XOR test vector must be binary")
        return value


class PosteriorSignFlipAction(_Strict):
    kind: Literal["posterior_sign_flip"]
    target_index: int = Field(ge=0)


InterventionAction = Annotated[
    FinitePriorBiasAction | ExactCoordinateFixAction | SyndromeXorAction | PosteriorSignFlipAction,
    Field(discriminator="kind"),
]


def validate_composition(composition: CanonicalCompositionSpec | CanonicalCompositionSpecV6) -> ResolvedComposition:
    """Resolve only known in-code kinds and reject invalid static ownership graphs."""

    binding_ids: set[str] = set()
    owned_state: set[str] = set()
    provided: set[str] = set()
    bindings: list[PolicyBinding] = []
    for role, spec in composition.in_role_order():
        phase5_intervention = (
            isinstance(composition, CanonicalCompositionSpecV6)
            and role is PolicyRole.INTERVENTION
            and spec.kind in {
                "guided_decimation", "impulse", "freezing", "syndrome_flip",
                "sign_flip", "restart_belief",
            }
        )
        if spec.kind not in _POLICY_KINDS[role] and not phase5_intervention:
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
                    source_anchors=("phase5-source-decisions-v1",) if phase5_intervention else (),
                    procedure=(
                        f"Source-qualified Phase 5 {spec.kind} intervention under its own bounded controller."
                        if phase5_intervention else f"Registered {spec.kind} policy follows the canonical CSS v1 procedure."
                    ),
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


class DisorderedAffinePriorAssignmentSpec(_Strict):
    """Public deterministic per-variable affine-prior coefficients.

    The sole supported ordinary-memory disordered form is a fresh uniform
    coefficient vector at each flooding source iteration.  Its seed identity
    is decoder-local and therefore cannot depend on physical-error truth.
    """

    mode: Literal["uniform"]
    low: float = Field(ge=0.0, le=1.0)
    high: float = Field(ge=0.0, le=1.0)
    root_seed_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    refresh_boundary: Literal["source_iteration"] = "source_iteration"
    rng_algorithm: Literal["numpy.PCG64"] = "numpy.PCG64"

    @model_validator(mode="after")
    def ordered_finite_interval(self) -> "DisorderedAffinePriorAssignmentSpec":
        if not math.isfinite(self.low) or not math.isfinite(self.high) or self.low > self.high:
            raise ValueError("disordered affine-prior assignment requires ordered finite endpoints")
        return self


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
    assignment: DisorderedAffinePriorAssignmentSpec | None = None

    @model_serializer(mode="wrap")
    def serialize_optional_assignment(self, handler):
        """Keep the pre-assignment persisted binding representation stable.

        ``assignment`` was added after the first public Relay manifests.  A
        null extension is semantically absent, so serializing it would change
        their manifest/sample identities despite no declared policy change.
        A real disordered assignment remains part of the serialized contract.
        """
        document = handler(self)
        if self.assignment is None:
            document.pop("assignment", None)
        return document

    @field_validator("advance_boundary", mode="before")
    @classmethod
    def advance_boundary_from_json(cls, value: Any) -> Any:
        """Convert only declared JSON labels; strict models otherwise reject enum strings."""
        return MemoryAdvanceBoundary(value) if isinstance(value, str) else value

    @field_validator("refresh_boundary", mode="before")
    @classmethod
    def refresh_boundary_from_json(cls, value: Any) -> Any:
        """Convert only declared JSON labels; strict models otherwise reject enum strings."""
        return MemoryRefreshBoundary(value) if isinstance(value, str) else value

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
            "posterior_momentum": ("posterior", {"alpha", "gamma"}),
        }
        target, parameter_names = expected[self.kind]
        if self.target != target:
            raise ValueError(f"{self.kind} may target only {target}")
        if set(self.parameters) != parameter_names:
            raise ValueError(f"{self.kind} requires exactly {sorted(parameter_names)!r} parameters")
        if any(not 0.0 <= coefficient <= 1.0 for coefficient in self.parameters.values()):
            raise ValueError("memory coefficients must be in [0, 1]")
        if self.kind in {"pdbp_field_mix", "pdprime_delta_mix", "posterior_momentum"} and self.parameters["gamma"] == 1.0:
            raise ValueError(f"{self.kind} gamma must be in [0, 1)")
        if self.kind == "posterior_momentum" and self.parameters["alpha"] == 0.0:
            raise ValueError("posterior_momentum alpha must be in (0, 1]")
        if self.assignment is not None:
            if self.kind != "affine_prior":
                raise ValueError("only affine_prior supports a disordered assignment")
            if self.advance_boundary is not MemoryAdvanceBoundary.SOURCE_ITERATION:
                raise ValueError("disordered affine-prior assignment requires source_iteration advancement")
            if self.refresh_boundary is not MemoryRefreshBoundary.ATTEMPT_START or self.retain_history:
                raise ValueError("ordinary disordered affine-prior assignment requires reset attempt history")
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


class RelayMemoryTuningV4(_Strict):
    """Opt-in source-linked Relay memory assignment for controlled CSS arms.

    ``first_leg_gamma`` is scalar across variables.  Every later leg derives a
    fresh per-variable Uniform interval from the declared root identity and the
    public shot identity.  The interval is deliberately not clipped to [0, 1]:
    the approved Relay reference accepts the declared finite endpoints.
    """

    semantics: Literal["relay_v022_dynamic_affine_prior_css_adaptation"]
    first_leg_gamma: float
    later_leg_center: float
    later_leg_width: float = Field(ge=0.0)
    seed_identity: str = Field(min_length=1, max_length=256)
    rng_algorithm: Literal["numpy.PCG64"] = "numpy.PCG64"
    refresh: Literal["per_later_leg"] = "per_later_leg"

    @field_validator("first_leg_gamma", "later_leg_center", "later_leg_width")
    @classmethod
    def finite_memory_tuning(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Relay memory tuning values must be finite")
        return value

    @property
    def later_leg_low(self) -> float:
        return self.later_leg_center - self.later_leg_width / 2.0

    @property
    def later_leg_high(self) -> float:
        return self.later_leg_center + self.later_leg_width / 2.0

    @model_validator(mode="after")
    def finite_interval_endpoints(self) -> "RelayMemoryTuningV4":
        if not math.isfinite(self.later_leg_low) or not math.isfinite(self.later_leg_high):
            raise ValueError("Relay memory tuning interval endpoints must be finite")
        return self


class RelaySpecV4(_Strict):
    """Sequential Relay topology with an unambiguous total leg count."""

    total_leg_limit: int = Field(ge=1, le=10_000)
    legs: tuple[RelayLegSpec, ...] = Field(min_length=1)
    preset_name: str = Field(default="relay-canonical-css-default-v1", min_length=1, max_length=96)
    first_leg_iteration_limit: int | None = Field(default=None, ge=1, le=100_000)
    later_leg_iteration_limit: int | None = Field(default=None, ge=1, le=100_000)
    solution_limit: int | None = Field(default=None, ge=1, le=10_000)
    transfer: Literal["posterior_only", "disabled"] = "posterior_only"
    first_leg_memory: Literal["uniform"] = "uniform"
    later_leg_memory: Literal["uniform", "disordered"] = "uniform"
    numerical_profile: Literal["cpu-float64-spa-v1", "cpu-float64-min-sum-v1"] = "cpu-float64-spa-v1"
    procedure: Literal["source_internal_bp", "canonical_internal_bp"] = "canonical_internal_bp"
    fidelity_status: Literal["source_procedure_css_adaptation", "canonical_css_adaptation", "controlled_component_adaptation"] = "canonical_css_adaptation"
    memory_tuning: RelayMemoryTuningV4 | None = None

    @field_validator("legs", mode="before")
    @classmethod
    def relay_legs_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def leg_limit_matches_explicit_legs(self) -> "RelaySpecV4":
        if self.total_leg_limit != len(self.legs):
            raise ValueError("total_leg_limit must equal the number of explicit Relay legs")
        first_limit = self.legs[0].max_iterations
        later_limit = self.legs[1].max_iterations if len(self.legs) > 1 else first_limit
        if self.first_leg_iteration_limit is None:
            object.__setattr__(self, "first_leg_iteration_limit", first_limit)
        elif self.first_leg_iteration_limit != first_limit:
            raise ValueError("first_leg_iteration_limit must match the explicit pre-leg")
        if self.later_leg_iteration_limit is None:
            object.__setattr__(self, "later_leg_iteration_limit", later_limit)
        elif any(leg.max_iterations != self.later_leg_iteration_limit for leg in self.legs[1:]):
            raise ValueError("later_leg_iteration_limit must match every declared later leg")
        if self.solution_limit is None:
            object.__setattr__(self, "solution_limit", self.total_leg_limit)
        if self.procedure == "source_internal_bp" and self.fidelity_status not in {
            "source_procedure_css_adaptation", "controlled_component_adaptation",
        }:
            raise ValueError("source Relay procedure requires a source or controlled CSS-adaptation fidelity label")
        if self.procedure == "canonical_internal_bp" and self.fidelity_status == "source_procedure_css_adaptation":
            raise ValueError("canonical Relay procedure cannot claim source-procedure fidelity")
        if self.memory_tuning is not None and self.fidelity_status != "controlled_component_adaptation":
            raise ValueError("active Relay memory tuning requires a controlled_component_adaptation label")
        if self.memory_tuning is not None and self.later_leg_memory != "disordered":
            raise ValueError("active Relay memory tuning requires disordered later_leg_memory")
        return self


class CanonicalManifestV4(_Strict):
    """Phase 4 strict Relay-BP extension; V2/V3 contracts stay unchanged."""

    schema_version: Literal[4]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-spa-v1", "cpu-float64-min-sum-v1"]
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

    @model_validator(mode="after")
    def relay_numerical_profile_matches_manifest(self) -> "CanonicalManifestV4":
        if self.relay.numerical_profile != self.numerical_profile:
            raise ValueError("Relay numerical_profile must match the canonical manifest numerical_profile")
        return self

    @model_validator(mode="after")
    def active_relay_procedure_has_its_declared_kernel(self) -> "CanonicalManifestV4":
        """Prevent label-only source/canonical active-memory procedure arms."""
        if self.relay.memory_tuning is None:
            return self
        expected = (
            ("min_sum", "cpu-float64-min-sum-v1")
            if self.relay.procedure == "source_internal_bp"
            else ("binary_spa", "cpu-float64-spa-v1")
        )
        if self.policies.update.kind != expected[0]:
            raise ValueError(
                f"active {self.relay.procedure} Relay requires update policy {expected[0]}"
            )
        if self.numerical_profile != expected[1]:
            raise ValueError(
                f"active {self.relay.procedure} Relay requires numerical_profile {expected[1]}"
            )
        return self


class InterventionSpec(_Strict):
    """Source-qualified, bounded BPGD interpretation for the Phase 5 tracer."""

    kind: Literal["guided_decimation"]
    variant: Literal["algorithm1_v2_interpretation"]
    source_revision: Literal["arxiv:2312.10950v2"]
    finite_bias_magnitude: float
    zero_rule: Literal["positive_prior_for_zero_posterior"]
    final_round_rule: Literal["return_after_last_fixation"]
    round_limit: int = Field(ge=1, le=10_000)
    sweeps_per_round: int = Field(ge=1, le=100_000)

    @model_validator(mode="after")
    def source_parameters_are_explicit(self) -> "InterventionSpec":
        if self.finite_bias_magnitude != 25.0:
            raise ValueError("the Algorithm 1 v2 tracer requires finite prior magnitude 25")
        return self


class Phase5InterventionContract(_Strict):
    """Strict source-qualified controls for a single public intervention arm."""

    kind: Literal[
        "identity", "guided_decimation", "impulse", "freezing",
        "syndrome_flip", "sign_flip", "restart_belief",
    ]
    variant: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    qualification: Literal[
        "canonical_implemented", "algorithm_interpretation",
        "source_operator_semantic_adaptation", "controlled_css_adaptation",
        "bsfbp_sign_only_controlled_adaptation", "mechanism_only_adaptation",
    ]
    native_availability: Literal["unverified", "repository_revision_verified_in_phase_research", "not_applicable"]
    trigger: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    selection: str = Field(min_length=1)
    lift_rule: str = Field(min_length=1)
    reset_rule: str = Field(min_length=1)
    preserved_fields: tuple[str, ...]
    unresolved: tuple[str, ...]
    stream_status: Literal["not_applicable", "derived_decoder_stream"]
    source_code_commit: str | None = None

    finite_bias_magnitude: float | None = None
    zero_rule: Literal["positive_prior_for_zero_posterior"] | None = None
    final_round_rule: Literal["return_after_last_fixation"] | None = None
    round_limit: int | None = Field(default=None, ge=1, le=10_000)
    sweeps_per_round: int | None = Field(default=None, ge=1, le=100_000)
    realization: Literal["semantic_forced_one", "exact_shortening"] | None = None
    baseline_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    attempt_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    attempt_cap: int | None = Field(default=None, ge=1, le=100_000)
    coordinate_order: tuple[int, ...] | None = None
    period_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    lifetime_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    retry_cap: int | None = Field(default=None, ge=1, le=100_000)
    root_seed: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=100_000)
    max_weight: int | None = Field(default=None, ge=1, le=100_000)
    test_cap: int | None = Field(default=None, ge=1, le=100_000)
    alpha: float | None = Field(default=None, gt=0.0, le=1.0)
    trunk_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    continuation_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    preset: Literal["source_exact_distance", "b1_tcap8_mechanism"] | None = None
    code_id: str | None = None
    eta: int | None = Field(default=None, ge=1, le=100_000)
    t_cap: int | None = Field(default=None, ge=1, le=100_000)
    root_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    residual_sweeps: int | None = Field(default=None, ge=1, le=100_000)
    exact_distance: int | None = Field(default=None, ge=2, le=100_000)

    @field_validator("preserved_fields", "unresolved", "coordinate_order", mode="before")
    @classmethod
    def lists_to_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_arm_and_controls(self) -> "Phase5InterventionContract":
        identities = {
            "identity": ("identity_baseline_v1", "project:canonical-baseline", "canonical_implemented", "not_applicable", "not_applicable"),
            "guided_decimation": ("algorithm1_v2_interpretation", "arxiv:2312.10950v2", "algorithm_interpretation", "unverified", "not_applicable"),
            "freezing": ("freezing_binary_css_controlled_v1", "arxiv:0801.1241", "controlled_css_adaptation", "unverified", "derived_decoder_stream"),
            "syndrome_flip": ("bpsf_stable_order_css_v1", "arxiv:2507.00254v1", "controlled_css_adaptation", "repository_revision_verified_in_phase_research", "derived_decoder_stream"),
            "sign_flip": ("bsfbp_sign_only_controlled_adaptation", "doi:10.1109/TQE.2023.3279379", "bsfbp_sign_only_controlled_adaptation", "unverified", "not_applicable"),
            "restart_belief": ("restart_belief_b1_tcap8_mechanism_v1", "arxiv:2511.13281v1", "mechanism_only_adaptation", "repository_revision_verified_in_phase_research", "not_applicable"),
        }
        if self.kind == "impulse":
            expected = (
                "impulse_negative_infinite_semantic_v1" if self.realization == "semantic_forced_one"
                else "impulse_exact_shortening_css_v1",
                "arxiv:2606.18240v1",
                "source_operator_semantic_adaptation" if self.realization == "semantic_forced_one" else "controlled_css_adaptation",
                "unverified", "not_applicable",
            )
        else:
            expected = identities[self.kind]
        if (self.variant, self.source_revision, self.qualification, self.native_availability, self.stream_status) != expected:
            raise ValueError("intervention variant, source, qualification, native, or stream status is unsupported")
        semantics = {
            "identity": ("attempt_start", "identity", "stable_first", "identity", "not_applicable", ()),
            "guided_decimation": ("failed_bp_round", "finite_prior_bias", "max_abs_reliability", "identity", "continue_messages", ("graph", "syndrome", "messages")),
            "freezing": ("frustrated_check", "temporary_zero_freeze", "first_valid", "restore_fixed", "fresh_structural_branch_then_release_to_original", ("original_graph", "original_syndrome")),
            "syndrome_flip": ("baseline_invalid_after_oscillation_count", "syndrome_xor_test_vector", "first_declared_valid", "xor_test_vector", "fresh_per_test", ("original_graph", "original_syndrome")),
            "sign_flip": ("failed_normalized_min_sum_trunk", "posterior_sign_flip", "global_mismatched_check_target", "identity", "continue_messages_at_next_sweep", ("prior", "v2c", "c2v")),
            "restart_belief": ("root_bp_failure", "inserted_error_residual_restart", "strict_lower_weight", "xor_inserted_error", "fresh_per_residual", ("inserted_error",)),
        }
        if self.kind == "impulse":
            expected_semantics = (
                "baseline_invalid", "semantic_forced_one" if self.realization == "semantic_forced_one" else "exact_shortening",
                "minimum_original_weight" if self.selection == "minimum_original_weight" else "first_convergence",
                "identity" if self.realization == "semantic_forced_one" else "restore_fixed",
                "fresh_per_coordinate", ("original_graph", "original_syndrome"),
            )
        else:
            expected_semantics = semantics[self.kind]
        actual_semantics = (
            self.trigger, self.operator, self.selection, self.lift_rule,
            self.reset_rule, self.preserved_fields,
        )
        if actual_semantics != expected_semantics:
            raise ValueError("intervention trigger, operator, selection, lift, reset, or preservation is unsupported")
        controls = {
            "finite_bias_magnitude", "zero_rule", "final_round_rule", "round_limit", "sweeps_per_round",
            "realization", "baseline_sweeps", "attempt_sweeps", "attempt_cap", "coordinate_order",
            "period_sweeps", "lifetime_sweeps", "retry_cap", "root_seed", "top_k", "max_weight",
            "test_cap", "alpha", "trunk_sweeps", "continuation_sweeps", "preset", "code_id",
            "eta", "t_cap", "root_sweeps", "residual_sweeps", "exact_distance",
        }
        required = {
            "identity": set(),
            "guided_decimation": {"finite_bias_magnitude", "zero_rule", "final_round_rule", "round_limit", "sweeps_per_round"},
            "impulse": {"realization", "baseline_sweeps", "attempt_sweeps", "attempt_cap"},
            "freezing": {"period_sweeps", "lifetime_sweeps", "retry_cap", "root_seed"},
            "syndrome_flip": {"baseline_sweeps", "attempt_sweeps", "top_k", "max_weight", "test_cap", "root_seed"},
            "sign_flip": {"alpha", "trunk_sweeps", "continuation_sweeps"},
            "restart_belief": {"preset", "code_id", "eta", "t_cap", "root_sweeps", "residual_sweeps"},
        }[self.kind]
        optional = {"coordinate_order"} if self.kind == "impulse" else {"exact_distance"} if self.kind == "restart_belief" else set()
        active = {name for name in controls if getattr(self, name) is not None}
        if not required <= active or active - required - optional:
            raise ValueError("intervention controls do not match the declared arm")
        if (self.kind == "guided_decimation" and self.finite_bias_magnitude != 25.0
                or self.kind == "impulse" and self.coordinate_order is not None
                and (len(self.coordinate_order) != len(set(self.coordinate_order)) or any(type(i) is not int or i < 0 for i in self.coordinate_order))):
            raise ValueError("guided magnitude or impulse coordinate order is invalid")
        if self.kind == "restart_belief":
            from .restarting import RestartSpec

            RestartSpec(
                preset=self.preset, code_id=self.code_id, eta=self.eta, t_cap=self.t_cap,
                root_sweeps=self.root_sweeps, residual_sweeps=self.residual_sweeps,
                exact_distance=self.exact_distance,
            )
        if self.kind in {"freezing", "syndrome_flip"} and not self.root_seed:
            raise ValueError("randomized intervention requires a decoder-only root seed")
        if self.kind == "syndrome_flip" and self.baseline_sweeps < 2:
            raise ValueError("BP-SF requires at least two baseline decisions for oscillation counts")
        if self.kind == "syndrome_flip" and self.source_code_commit != "0417d33fc2ffb3b442d0397bb09954fc1c6c3938":
            raise ValueError("BP-SF source code commit is not pinned")
        if self.kind == "restart_belief" and self.source_code_commit != "275535ec981763166c8549d91959dc6e371ec4b1":
            raise ValueError("Restart Belief source code commit is not pinned")
        if self.kind not in {"syndrome_flip", "restart_belief"} and self.source_code_commit is not None:
            raise ValueError("unverified native code cannot carry a pinned commit")
        if self.kind != "identity" and (not self.unresolved or not self.preserved_fields):
            raise ValueError("source-linked interventions must disclose unresolved details and preserved fields")
        return self


class CanonicalManifestV6(_Strict):
    """Compact Phase 5 intervention contract; V2–V5 remain unchanged."""

    schema_version: Literal[6]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-spa-v1", "cpu-float64-min-sum-v1"]
    max_iterations: int = Field(ge=1, le=100_000)
    error_rate: float = Field(gt=0.0, lt=1.0)
    policies: CanonicalCompositionSpecV6
    intervention: InterventionSpec | Phase5InterventionContract

    @model_validator(mode="after")
    def tracer_uses_compatible_kernel_and_state(self) -> "CanonicalManifestV6":
        if (self.policies.schedule.kind != "flooding"
                or self.policies.intervention.kind != self.intervention.kind
                or self.policies.state_memory.kind != "identity"):
            raise ValueError("Phase 5 interventions require flooding, identity state memory, and a matching policy")
        expected_update = "normalized_min_sum" if self.intervention.kind == "sign_flip" else "binary_spa"
        expected_profile = "cpu-float64-min-sum-v1" if expected_update == "normalized_min_sum" else "cpu-float64-spa-v1"
        if self.policies.update.kind != expected_update or self.numerical_profile != expected_profile:
            raise ValueError("intervention kernel/profile combination is unsupported")
        if self.intervention.kind == "guided_decimation" and self.intervention.sweeps_per_round > self.max_iterations:
            raise ValueError("guided sweeps_per_round exceeds the declared per-round max_iterations")
        return self


def parse_canonical_manifest(value: CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5 | CanonicalManifestV6 | dict[str, Any] | str) -> CanonicalManifestV2 | CanonicalManifestV3 | CanonicalManifestV4 | CanonicalManifestV5 | CanonicalManifestV6:
    """Parse only the versioned strict canonical representation."""
    if isinstance(value, (CanonicalManifestV2, CanonicalManifestV3, CanonicalManifestV4, CanonicalManifestV5, CanonicalManifestV6)):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
    else:
        decoded = value
    if not isinstance(decoded, dict):
        raise ValueError("canonical manifest must be an object")
    schema_version = decoded.get("schema_version")
    if schema_version == 6:
        return CanonicalManifestV6.model_validate(decoded)
    if schema_version == 5:
        return CanonicalManifestV5.model_validate(decoded)
    if schema_version == 4:
        return CanonicalManifestV4.model_validate(decoded)
    return CanonicalManifestV3.model_validate(decoded) if schema_version == 3 else CanonicalManifestV2.model_validate(decoded)
