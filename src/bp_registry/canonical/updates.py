"""Closed check-update rules for the canonical binary CSS kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
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


class ParameterGeneratorSpec(BaseModel):
    """Closed, purpose-separated generator declaration for one assignment draw."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

    shape: Literal["scalar", "check", "edge"]
    graph_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    distribution: Literal["uniform"]
    low: float
    high: float
    root_seed_identity: str = Field(pattern=r"^[0-9a-f]{64}$")
    purpose: Literal["parameter_assignment"] = "parameter_assignment"
    algorithm: Literal["numpy.PCG64"] = "numpy.PCG64"
    generator_version: str = Field(default_factory=lambda: np.__version__, min_length=1)
    provenance: Literal["source_defined", "exploratory"] = "exploratory"
    source_anchor: str | None = None

    @field_validator("low", "high")
    @classmethod
    def bounds_are_finite_nonnegative(cls, value: float) -> float:
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("generator bounds must be finite and nonnegative")
        return value

    @model_validator(mode="after")
    def bounds_and_source_label_are_closed(self) -> "ParameterGeneratorSpec":
        if self.high < self.low:
            raise ValueError("generator high must be greater than or equal to low")
        if self.provenance == "source_defined" and not self.source_anchor:
            raise ValueError("source_defined generator requires a source_anchor")
        if self.provenance == "exploratory" and self.source_anchor is not None:
            raise ValueError("exploratory generator cannot carry a source_anchor")
        return self


@dataclass(frozen=True, slots=True)
class ParameterAssignmentState:
    """Immutable generator state; only an admitted refresh may advance it."""

    derived_identity: str
    rng_state: str
    resolved_assignments: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class ParameterRefreshResult:
    """One atomic generated-assignment boundary outcome."""

    admitted: bool
    state: ParameterAssignmentState
    assignment: ParameterAssignment | None
    evidence: dict[str, Any] | None
    termination: Any = None


class ParameterRefreshPlan(BaseModel):
    """Configuration, attempt, or source-iteration assignment refresh contract."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)

    scope: Literal["configuration", "attempt", "source_iteration"]
    generator: ParameterGeneratorSpec | None = None

    def _require_generator(self) -> ParameterGeneratorSpec:
        if self.generator is None:
            raise ValueError("parameter refresh requires an attached parameter generator")
        return self.generator

    def initial_state(self, *, configuration_identity: str, attempt_identity: str) -> ParameterAssignmentState:
        generator = self._require_generator()
        if not all(isinstance(value, str) and value for value in (configuration_identity, attempt_identity)):
            raise ValueError("parameter refresh identities must be nonempty strings")
        material: dict[str, Any] = {
            "purpose": "parameter_assignment",
            "root_seed_identity": generator.root_seed_identity,
            "generator": generator.model_dump(mode="json"),
            "configuration_identity": configuration_identity,
            "scope": self.scope,
        }
        if self.scope in {"attempt", "source_iteration"}:
            material["attempt_identity"] = attempt_identity
        derived = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        rng = np.random.Generator(np.random.PCG64(int(derived[:32], 16)))
        return ParameterAssignmentState(derived, json.dumps(rng.bit_generator.state, sort_keys=True), ())

    def refresh(
        self,
        state: ParameterAssignmentState,
        *,
        boundary: str,
        source_iteration: int,
        graph_sha256: str,
        check_count: int,
        edge_count: int,
        budgets: Any,
        budget_scope: str,
    ) -> ParameterRefreshResult:
        """Reserve before cloning/drawing and commit both assignment and RNG together."""
        from .budgets import WorkVector

        generator_spec = self._require_generator()
        if not isinstance(state, ParameterAssignmentState):
            raise ValueError("parameter refresh requires its own immutable state")
        if boundary != self.scope:
            raise ValueError(f"{self.scope} parameter refresh may occur only at its declared scope boundary")
        if type(source_iteration) is not int or source_iteration < 0:
            raise ValueError("source_iteration must be a nonnegative integer")
        if graph_sha256 != generator_spec.graph_sha256:
            raise ValueError("generated assignment graph_sha256 does not match the immutable graph")
        if self.scope != "source_iteration" and state.resolved_assignments:
            assignment = ParameterAssignment.model_validate(state.resolved_assignments[-1])
            return ParameterRefreshResult(True, state, assignment, self._evidence(state, assignment, source_iteration))
        reservation = budgets.reserve(
            budget_scope,
            WorkVector.zero(),
            leaf_id=f"{budget_scope}:parameter-assignment:{state.derived_identity}:{len(state.resolved_assignments)}",
        )
        if reservation is None:
            return ParameterRefreshResult(False, state, None, None, getattr(budgets, "last_termination", None))
        try:
            rng = np.random.Generator(np.random.PCG64())
            rng.bit_generator.state = json.loads(state.rng_state)
            count = 1 if generator_spec.shape == "scalar" else check_count if generator_spec.shape == "check" else edge_count
            if type(count) is not int or count < 1:
                raise ValueError("generated assignment requires a bounded nonempty graph dimension")
            values = tuple(float(value) for value in rng.uniform(generator_spec.low, generator_spec.high, size=count))
            payload: dict[str, Any] = {"shape": generator_spec.shape}
            if generator_spec.shape == "scalar":
                payload["value"] = values[0]
            else:
                payload.update({"graph_sha256": graph_sha256, "values": values})
            assignment = ParameterAssignment.model_validate(payload)
            next_state = ParameterAssignmentState(
                state.derived_identity,
                json.dumps(rng.bit_generator.state, sort_keys=True),
                state.resolved_assignments + (assignment.model_dump(mode="json"),),
            )
            evidence = self._evidence(next_state, assignment, source_iteration)
            reservation.commit_once()
            return ParameterRefreshResult(True, next_state, assignment, evidence)
        except BaseException:
            if reservation.active:
                reservation.rollback()
            raise

    def _evidence(self, state: ParameterAssignmentState, assignment: ParameterAssignment, source_iteration: int) -> dict[str, Any]:
        generator = self._require_generator()
        return {
            "purpose": "parameter_assignment",
            "algorithm": generator.algorithm,
            "generator_version": generator.generator_version,
            "distribution": {"kind": generator.distribution, "low": generator.low, "high": generator.high},
            "provenance": generator.provenance,
            "source_anchor": generator.source_anchor,
            "graph_sha256": generator.graph_sha256,
            "seed_derivation": state.derived_identity,
            "refresh_scope": self.scope,
            "source_iteration": source_iteration,
            "resolved_assignment": assignment.model_dump(mode="json"),
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


@dataclass(frozen=True, slots=True)
class OffsetMinSumUpdate:
    """Float64 offset min-sum with an explicit, never-broadcast beta assignment.

    The magnitude is formed from finite incoming values, then beta is subtracted
    in float64 and floored before the named output saturation boundary.  This is
    intentionally distinct from clipping each incoming value before the offset.
    """

    beta: ParameterAssignment
    profile: NumericalProfile = MIN_SUM_CPU_F64
    resolved_beta: tuple[float, ...] | None = None

    def _beta_for(self, *, edge_index: int, source_iteration: int) -> float:
        if type(edge_index) is not int or edge_index < 0:
            raise ValueError("edge_index must be a nonnegative integer")
        if type(source_iteration) is not int or source_iteration < 0:
            raise ValueError("source_iteration must be a nonnegative integer")
        if self.resolved_beta is not None:
            if edge_index >= len(self.resolved_beta):
                raise ValueError("edge_index is outside the resolved offset assignment")
            return self.resolved_beta[edge_index]
        if self.beta.shape == "scalar":
            assert self.beta.value is not None
            return self.beta.value
        if self.beta.shape == "source_iteration":
            assert self.beta.values is not None
            if source_iteration >= len(self.beta.values):
                raise ValueError("source_iteration assignment has no declared value for this iteration")
            return self.beta.values[source_iteration]
        raise ValueError("non-scalar offset assignment must be resolved against an immutable graph before use")

    def check_to_variable(
        self, incoming: np.ndarray, *, syndrome: int, check_index: int = 0,
        edge_index: int = 0, source_iteration: int = 0,
    ) -> float:
        values = np.asarray(incoming, dtype=np.float64)
        if values.ndim != 1:
            raise ValueError("offset_min_sum_input must be a one-dimensional LLR array")
        if not np.all(np.isfinite(values)):
            raise ValueError("offset_min_sum_input contains nonfinite values")
        if type(syndrome) not in (int, np.int64, np.int32) or int(syndrome) not in (0, 1):
            raise ValueError("syndrome must be a binary integer")
        magnitude = self.profile.saturation if values.size == 0 else float(np.min(np.abs(values)))
        beta = self._beta_for(edge_index=edge_index, source_iteration=source_iteration)
        reduced = max(0.0, float(np.float64(magnitude) - np.float64(beta)))
        sign = -1.0 if (int(np.count_nonzero(values < 0.0)) + int(syndrome)) % 2 else 1.0
        return float(finite_saturate(sign * reduced, boundary="offset_min_sum_output", profile=self.profile))

    def evidence(self) -> UpdateRuleEvidence:
        return UpdateRuleEvidence(
            kind="offset_min_sum", numerical_profile=self.profile.profile_id,
            procedure="signed extrinsic minimum minus explicit beta in float64, zero floor, then saturation",
            provenance=self.beta.provenance,
            declared_assignment=self.beta.model_dump(mode="json"),
            resolved_assignment=self.resolved_beta,
        )
