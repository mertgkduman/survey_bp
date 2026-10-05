"""Version-dispatched, strict manifests and immutable simulation preflight."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Literal, TypeAlias

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .artifacts import LoadedArtifact, load_artifact
from .canonical.budgets import WorkVector
from .canonical.cluster_schedule import ClusterArtifactQualification, ClusterArtifactSpec, load_cluster_artifact
from .canonical.compatibility import validate_memory_compatibility
from .canonical.contracts import (
    CanonicalCompositionSpec, CanonicalCompositionSpecV3, CanonicalManifestV2,
    CanonicalCompositionSpecV6, MemoryCompositionSpec, Phase5InterventionContract,
    RelaySpecV4, parse_canonical_manifest, validate_composition,
)
from .css import CssCode, fixture_code


MAX_SHOTS = 1_000_000
MAX_ITERATIONS = 100_000
_SHA256 = r"^[0-9a-f]{64}$"


class StrictModel(BaseModel):
    """The persisted manifest never coerces settings or silently keeps extras."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class PaperV1(StrictModel):
    uri: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    experiment_anchor: str = Field(min_length=1)
    relation: Literal["pilot_adaptation", "source_faithful"]

    @field_validator("uri")
    @classmethod
    def https_uri(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("paper URI must use HTTPS")
        return value


class ImplementationV1(StrictModel):
    """Pinned executable source, recorded independently from paper evidence."""

    repository_uri: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    source_artifact_sha256: str = Field(pattern=_SHA256)
    source_artifact_status: Literal["verified", "unverified"]

    @field_validator("repository_uri")
    @classmethod
    def https_repository_uri(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("implementation repository URI must use HTTPS")
        return value


class MatrixHashesV1(StrictModel):
    """Separate role- and order-sensitive identities for each CSS object."""

    hx_raw_sha256: str = Field(pattern=_SHA256)
    hz_raw_sha256: str = Field(pattern=_SHA256)
    lx_raw_sha256: str = Field(pattern=_SHA256)
    lz_raw_sha256: str = Field(pattern=_SHA256)
    hx_semantic_sha256: str = Field(pattern=_SHA256)
    hz_semantic_sha256: str = Field(pattern=_SHA256)
    lx_semantic_sha256: str = Field(pattern=_SHA256)
    lz_semantic_sha256: str = Field(pattern=_SHA256)


class ArtifactV1(StrictModel):
    root: str = Field(min_length=1)
    path: str = Field(min_length=1)
    raw_sha256: str = Field(pattern=_SHA256)
    semantic_sha256: str = Field(pattern=_SHA256)
    matrix_hashes: MatrixHashesV1
    format_version: Literal[1]
    code_id: str = Field(min_length=1)


class DecoderV1(StrictModel):
    implementation: Literal["ldpc"]
    version: str = Field(min_length=1)
    entry_point: Literal["ldpc.BpDecoder"]
    bp_method: Literal["product_sum"]
    schedule: Literal["parallel"]
    input_vector_type: Literal["syndrome"]
    parameter_names: tuple[Literal[
        "error_rate", "max_iter", "bp_method", "schedule", "input_vector_type",
    ], ...] = Field(min_length=5, max_length=5)

    @field_validator("parameter_names", mode="before")
    @classmethod
    def json_array_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def exact_parameter_names(self) -> "DecoderV1":
        required = (
            "error_rate", "max_iter", "bp_method", "schedule", "input_vector_type",
        )
        if self.parameter_names != required:
            raise ValueError("decoder parameter names must be explicit and ordered")
        return self


class NoiseV1(StrictModel):
    channel: Literal["x_only_bit_flip"]
    x_error_rates: tuple[float, ...] = Field(min_length=1, max_length=1000)

    @field_validator("x_error_rates", mode="before")
    @classmethod
    def json_rates_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("x_error_rates")
    @classmethod
    def rates_are_finite_floats(cls, values: tuple[float, ...]) -> tuple[float, ...]:
        for value in values:
            if type(value) is not float or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("x_error_rates must be finite floats in [0, 1]")
        return values


class SeedPolicyV1(StrictModel):
    root_seed: int = Field(ge=0)
    derivation: Literal["sha256-manifest-shot-v1"]


class BudgetV1(StrictModel):
    max_shots: int = Field(ge=1, le=MAX_SHOTS)
    max_iter: int = Field(ge=1, le=MAX_ITERATIONS)
    stopping_rule: Literal["fixed_shots"]
    denominator_rule: Literal["all_terminal_shots"]


class EnvironmentV1(StrictModel):
    python: str = Field(min_length=1)
    numpy: str = Field(min_length=1)
    scipy: str = Field(min_length=1)
    ldpc: str = Field(min_length=1)
    backend: Literal["cpu"]
    omp_num_threads: Literal[1]


class ExpectedOutputV1(StrictModel):
    status: Literal["not_assessed", "assessed"]
    reason: str = Field(min_length=1)
    values: tuple[float, ...]
    tolerance: float | None = Field(default=None, ge=0)
    statistical_verdict: Literal["pass", "fail", "inconclusive"] | None = None

    @field_validator("values", mode="before")
    @classmethod
    def json_values_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def status_matches_criteria(self) -> "ExpectedOutputV1":
        if self.status == "not_assessed":
            if self.values or self.tolerance is not None or self.statistical_verdict is not None:
                raise ValueError("not_assessed output cannot carry values, tolerance, or verdict")
        elif not self.values or self.tolerance is None or self.statistical_verdict is None:
            raise ValueError("assessed output requires values, tolerance, and a verdict")
        return self


class ManifestV1(StrictModel):
    """Complete, immutable settings for a pinned CSS code-capacity experiment."""

    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    paper: PaperV1
    implementation: ImplementationV1
    artifact: ArtifactV1
    decoder: DecoderV1
    noise: NoiseV1
    seed_policy: SeedPolicyV1
    budget: BudgetV1
    environment: EnvironmentV1
    expected_output: ExpectedOutputV1
    discrepancies: tuple[str, ...] = Field(min_length=1)

    @field_validator("discrepancies", mode="before")
    @classmethod
    def json_discrepancies_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("discrepancies")
    @classmethod
    def discrepancies_are_explanatory(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("discrepancies must contain explanatory text")
        return values


# ``Manifest`` remains public for callers importing the original tracer name.
Manifest = ManifestV1


class LegacyManifestV1(StrictModel):
    """Read-only v1 tracer shape retained so saved pilot records still run."""

    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_anchor: str = Field(min_length=1)
    code_id: Literal["project-three-qubit-css-fixture"]
    experiment_relation: Literal["pilot_adaptation"]
    expected_output_status: Literal["not_assessed"]
    x_error_rate: float
    seed: int = Field(ge=0)
    max_iter: int = Field(ge=1, le=MAX_ITERATIONS)
    bp_method: Literal["product_sum"]
    schedule: Literal["parallel"]
    input_vector_type: Literal["syndrome"]

    @field_validator("source_uri")
    @classmethod
    def legacy_https_uri(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("source_uri must be an HTTPS source reference")
        return value

    @field_validator("x_error_rate")
    @classmethod
    def legacy_rate(cls, value: float) -> float:
        if type(value) is not float or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("x_error_rate must be a finite float in [0, 1]")
        return value


class CanonicalEnvironmentV2(StrictModel):
    """Runtime identity for the project-owned CPU implementation only."""

    python: str = Field(min_length=1)
    numpy: str = Field(min_length=1)
    scipy: str = Field(min_length=1)
    backend: Literal["cpu"]
    omp_num_threads: Literal[1]


class CanonicalWorkLimitsV2(StrictModel):
    """One complete, resource-specific hard cap vector for one lifecycle scope."""

    check_to_variable_updates: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    variable_to_check_updates: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    belief_assemblies: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    residual_priority_evaluations: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    bp_calls: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    candidate_checks: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    intervention_actions: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    branch_expansions: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    branch_prunes: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    relay_transfers: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)
    fallback_calls: int = Field(ge=0, le=MAX_ITERATIONS * 1_000)

    @model_validator(mode="after")
    def names_match_the_canonical_work_vector(self) -> "CanonicalWorkLimitsV2":
        if set(type(self).model_fields) != set(WorkVector.zero().as_evidence(structural_event_version=2)):
            raise ValueError("canonical work limit fields must exactly match WorkVector resources")
        return self

    def as_evidence(self) -> dict[str, int]:
        return self.model_dump(mode="json")


class CanonicalBudgetScopeV2(StrictModel):
    max_iterations: int = Field(ge=1, le=MAX_ITERATIONS)
    work_limits: CanonicalWorkLimitsV2


class CanonicalBudgetsV2(StrictModel):
    max_shots: int = Field(ge=1, le=MAX_SHOTS)
    shot: CanonicalBudgetScopeV2
    search: CanonicalBudgetScopeV2
    attempt: CanonicalBudgetScopeV2
    denominator_rule: Literal["all_terminal_shots"]

    @model_validator(mode="after")
    def nested_scopes_do_not_expand_the_shot_limit(self) -> "CanonicalBudgetsV2":
        if self.search.max_iterations > self.shot.max_iterations or self.attempt.max_iterations > self.search.max_iterations:
            raise ValueError("canonical nested iteration budgets may not exceed their parent scope")
        for resource in WorkVector.zero().as_evidence(structural_event_version=2):
            if getattr(self.search.work_limits, resource) > getattr(self.shot.work_limits, resource):
                raise ValueError(f"canonical search {resource} limit may not exceed its shot parent")
            if getattr(self.attempt.work_limits, resource) > getattr(self.search.work_limits, resource):
                raise ValueError(f"canonical attempt {resource} limit may not exceed its search parent")
        return self


class CanonicalTracePlanV2(StrictModel):
    level: Literal["off", "full", "filtered"]
    relative_dir: str = Field(min_length=1)
    max_records: int = Field(ge=0, le=1_000_000)
    max_bytes: int = Field(ge=0, le=64 * 1024 * 1024)
    label: Literal["development_default", "prespecified_campaign"]


class CanonicalProfilePlanV2(StrictModel):
    enabled: bool
    level: Literal["low_overhead", "representative"]
    cohort: Literal["clean", "representative", "diagnostic"]
    selected_before_outcome: bool


class CanonicalRandomnessV2(StrictModel):
    sample_seed: int = Field(ge=0)
    decoder_seed_identity: str = Field(min_length=1)
    sample_derivation: Literal["sha256-manifest-shot-v1"]
    physical_sample_identity: str | None = Field(default=None, min_length=1)


class CanonicalEvidenceV2(StrictModel):
    relation: Literal["canonical_implemented", "pilot_adaptation"]
    fixture: Literal["development_fixture", "pilot_adaptation"]
    assessment_status: Literal["not_assessed"]
    procedure: str = Field(min_length=1)
    sources: tuple[str, ...] = Field(min_length=1)
    discrepancies: tuple[str, ...] = Field(min_length=1)

    @field_validator("sources", "discrepancies", mode="before")
    @classmethod
    def evidence_lists_are_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def relation_and_fixture_are_honest(self) -> "CanonicalEvidenceV2":
        if self.relation == "canonical_implemented" and self.fixture != "development_fixture":
            raise ValueError("canonical implementation evidence requires a development_fixture label")
        if self.relation == "pilot_adaptation" and self.fixture != "pilot_adaptation":
            raise ValueError("pilot adaptation evidence requires a pilot_adaptation label")
        return self


class CanonicalExperimentV2(StrictModel):
    """Strict persisted public contract for canonical CSS development evidence."""

    schema_version: Literal[2]
    run_id: str = Field(min_length=1)
    numerical_profile: Literal["cpu-float64-spa-v1"]
    error_rate: float = Field(gt=0.0, lt=1.0)
    policies: CanonicalCompositionSpec
    budgets: CanonicalBudgetsV2
    trace_plan: CanonicalTracePlanV2
    profile_plan: CanonicalProfilePlanV2
    environment: CanonicalEnvironmentV2
    artifact: ArtifactV1
    randomness: CanonicalRandomnessV2
    evidence: CanonicalEvidenceV2

    @field_validator("error_rate")
    @classmethod
    def canonical_rate_is_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("canonical error rate must be finite")
        return value


class CanonicalExperimentV3(CanonicalExperimentV2):
    """Versioned public contract for promoted local-step schedule tracers."""

    schema_version: Literal[3]
    numerical_profile: Literal["cpu-float64-min-sum-v1", "cpu-float64-spa-v1"]
    policies: CanonicalCompositionSpecV3


class CanonicalExperimentV4(CanonicalExperimentV3):
    """Strict public composition contract for ordered Phase 4 memory bindings.

    V4 extends the complete V3 evidence contract so public execution retains the
    established artifact, budget, provenance, and outcome semantics.  The memory
    chain is persisted separately from the seven required policy roles because it
    may contain repeated policy kinds with private history owners.
    """

    schema_version: Literal[4]
    memory: MemoryCompositionSpec
    # Relay was added after V4 first exposed its memory-only public contract.
    # Retain those manifests as executable V4 evidence; a populated Relay spec
    # opts the canonical kernel into the distinct Phase 4 Relay execution path.
    relay: RelaySpecV4 | None = None

    @model_validator(mode="after")
    def relay_procedure_has_its_declared_kernel(self) -> "CanonicalExperimentV4":
        """Reject source labels that do not select the author's min-sum kernel."""
        if self.relay is None:
            return self
        if self.relay.procedure == "source_internal_bp":
            expected = ("min_sum", "cpu-float64-min-sum-v1")
        elif self.relay.memory_tuning is not None:
            expected = ("binary_spa", "cpu-float64-spa-v1")
        else:
            return self
        if self.policies.update.kind != expected[0]:
            raise ValueError(
                f"{self.relay.procedure} Relay requires update policy {expected[0]}"
            )
        if self.numerical_profile != expected[1]:
            raise ValueError(
                f"{self.relay.procedure} Relay requires numerical_profile {expected[1]}"
            )
        return self


class Phase5ExecutionLimits(StrictModel):
    """Finite controls for every Phase 5 work category and observation scope."""

    max_total_attempts: int = Field(ge=1, le=1_000_000)
    max_total_actions: int = Field(ge=1, le=1_000_000)
    max_runtime_seconds: float = Field(gt=0.0, le=86_400.0)
    max_trace_records: int = Field(ge=0, le=1_000_000)
    max_trace_bytes: int = Field(ge=0, le=64 * 1024 * 1024)
    work_caps: dict[str, int]

    @model_validator(mode="after")
    def all_work_caps_are_explicit(self) -> "Phase5ExecutionLimits":
        names = set(WorkVector.zero().as_evidence(structural_event_version=4))
        if set(self.work_caps) != names or any(type(value) is not int or not 0 <= value <= 10**12 for value in self.work_caps.values()):
            raise ValueError("Phase 5 work caps must name every bounded WorkVector resource")
        if not math.isfinite(self.max_runtime_seconds):
            raise ValueError("Phase 5 runtime cap must be finite")
        return self


class CanonicalExperimentV5(CanonicalExperimentV4):
    """Complete public V4 evidence contract with one Phase 5 intervention."""

    schema_version: Literal[5]
    policies: CanonicalCompositionSpecV6
    memory: None = None
    relay: None = None
    intervention: Phase5InterventionContract
    intervention_limits: Phase5ExecutionLimits

    @model_validator(mode="after")
    def intervention_is_compatible_before_artifacts(self) -> "CanonicalExperimentV5":
        if self.policies.intervention.kind != self.intervention.kind:
            raise ValueError("public intervention policy and control kind disagree")
        # BPGD retains its decoder session inside its intervention controller.
        # ``stateless`` means that the composition contributes no second memory
        # policy; it does not reset that controller-owned message session.
        allowed_memory = ({"identity", "stateless"} if self.intervention.kind == "guided_decimation"
                          else {"identity"})
        if self.policies.schedule.kind != "flooding" or self.policies.state_memory.kind not in allowed_memory:
            raise ValueError("Phase 5 public intervention requires flooding and its declared state-memory role")
        allowed_updates = ({"binary_spa", "min_sum"} if self.intervention.kind == "syndrome_flip"
                           else {"normalized_min_sum"} if self.intervention.kind == "sign_flip"
                           else {"binary_spa"})
        expected_profile = ("cpu-float64-spa-v1" if self.policies.update.kind == "binary_spa"
                            else "cpu-float64-min-sum-v1")
        if self.policies.update.kind not in allowed_updates or self.numerical_profile != expected_profile:
            raise ValueError("public intervention update and numerical profile are incompatible")
        if self.intervention.kind == "sign_flip":
            assignment = self.policies.update.parameter_assignment
            if assignment is None or assignment.shape != "scalar" or assignment.value != self.intervention.alpha:
                raise ValueError("sign-flip normalized-min-sum assignment must equal the declared alpha")
        if self.intervention.kind == "restart_belief" and self.intervention.code_id != self.artifact.code_id:
            raise ValueError("restart code identity must match the artifact")
        if self.intervention.kind == "restart_belief" and self.artifact.code_id == "b1-ghp-882":
            if self.artifact.raw_sha256 != "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6":
                raise ValueError("B1 restart adaptation requires the pinned artifact identity")
        if self.intervention.kind == "restart_belief" and self.evidence.relation != "pilot_adaptation":
            raise ValueError("B1 restart mechanism requires pilot_adaptation evidence")
        if self.artifact.code_id == "b1-ghp-882" and (
            self.artifact.raw_sha256 != "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6"
            or self.evidence.relation != "pilot_adaptation"
            or self.evidence.fixture != "pilot_adaptation"
            or self.evidence.assessment_status != "not_assessed"
        ):
            raise ValueError("B1 intervention shots require pinned pilot_adaptation and not_assessed evidence")
        if self.intervention.kind != "restart_belief" and self.evidence.relation != "canonical_implemented":
            # A matched B1 mechanism pilot uses the same separately qualified
            # single-arm controllers, never a source-faithful ranking label.
            if not (
                self.artifact.code_id == "b1-ghp-882"
                and self.artifact.raw_sha256 == "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6"
                and self.evidence.relation == "pilot_adaptation"
                and self.evidence.fixture == "pilot_adaptation"
                and self.evidence.assessment_status == "not_assessed"
            ):
                raise ValueError("Phase 5 controlled arms require development evidence or the pinned B1 pilot")
        for name in ("sweeps_per_round", "baseline_sweeps", "attempt_sweeps", "period_sweeps", "lifetime_sweeps", "trunk_sweeps", "continuation_sweeps", "root_sweeps", "residual_sweeps"):
            value = getattr(self.intervention, name)
            if value is not None and value > self.budgets.attempt.max_iterations:
                raise ValueError(f"{name} exceeds public per-attempt iteration cap")
        if self.trace_plan.max_records > self.intervention_limits.max_trace_records or self.trace_plan.max_bytes > self.intervention_limits.max_trace_bytes:
            raise ValueError("trace plan exceeds Phase 5 trace caps")
        if self.trace_plan.level != "off":
            raise ValueError("Phase 5 public intervention traces are not yet an executable evidence mode")
        inherited = self.budgets.attempt.work_limits.as_evidence()
        if any(self.intervention_limits.work_caps[name] != amount for name, amount in inherited.items()):
            raise ValueError("Phase 5 caps for historical work fields must equal public attempt limits")
        potential_attempts = {
            "identity": 1,
            "guided_decimation": self.intervention.round_limit,
            "impulse": self.intervention.attempt_cap,
            "freezing": self.intervention.retry_cap,
            "syndrome_flip": self.intervention.test_cap,
            "sign_flip": 1,
            "restart_belief": (self.intervention.eta or 0) * (self.intervention.t_cap or 0),
        }[self.intervention.kind]
        if potential_attempts > self.intervention_limits.max_total_attempts:
            raise ValueError("intervention attempt potential exceeds the public hard cap")
        # A reset, release, or insertion can require more than one action per
        # attempt.  Reserve a conservative finite envelope up front.
        if 2 * potential_attempts > self.intervention_limits.max_total_actions:
            raise ValueError("intervention action potential exceeds the public hard cap")
        return self


class CanonicalExperimentV6(CanonicalExperimentV5):
    """Phase 5 intervention with one explicit, attempt-reset V2C damping policy."""

    schema_version: Literal[6]
    memory: MemoryCompositionSpec

    @model_validator(mode="after")
    def admitted_intervention_memory(self) -> "CanonicalExperimentV6":
        if len(self.memory.bindings) != 1:
            raise ValueError("intervention damping requires exactly one memory binding")
        binding = self.memory.bindings[0]
        if (binding.kind != "v2c_damping" or binding.target != "v2c"
                or binding.advance_boundary.value != "source_iteration"
                or binding.refresh_boundary.value != "attempt_start"
                or binding.state_lifetime != "attempt" or binding.retain_history
                or binding.source_status != "canonical_adaptation"):
            raise ValueError("intervention damping requires attempt-reset source-iteration V2C memory")
        if self.intervention.kind == "impulse" and self.intervention.realization == "semantic_forced_one":
            raise ValueError("damped semantic forced-one impulse is not qualified")
        decision = validate_memory_compatibility(
            self.memory, update_rule=self.policies.update.kind,
            schedule=self.policies.schedule.kind,
        )
        if not decision.admitted:
            raise ValueError(decision.reason)
        return self


class MbbpBasisDescriptorV7(StrictModel):
    """A public, ordered duplicate-check basis for one independent member."""

    member_id: str = Field(min_length=1)
    local_ordinal: int = Field(ge=0)
    partition_identity: str = Field(min_length=1)
    permutation_identity: str = Field(min_length=1)
    transform_kind: Literal["one_hot_original_check_rows"]
    redundant_transforms: tuple[tuple[int, ...], ...] = Field(min_length=1)

    @field_validator("redundant_transforms", mode="before")
    @classmethod
    def transform_arrays_are_tuples(cls, value: Any) -> Any:
        if isinstance(value, list):
            return tuple(tuple(row) if isinstance(row, list) else row for row in value)
        return value

    @field_validator("redundant_transforms")
    @classmethod
    def source_rows_are_one_hot(cls, value: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
        if any(not row or any(type(bit) is not int or bit not in (0, 1) for bit in row) or sum(row) != 1 for row in value):
            raise ValueError("MBBP source-qualified transforms must be nonempty one-hot original-check rows")
        return value


class MbbpEnsembleV7(StrictModel):
    """Complete, finite MBBP-LD controls admitted by the public V7 boundary."""

    kind: Literal["mbbp_ld"]
    source_status: Literal["canonical_adaptation"]
    member_state: Literal["independent"]
    max_iterations: int = Field(ge=1, le=100_000)
    max_member_c2v_updates: int = Field(ge=0, le=10**12)
    max_total_members: int = Field(ge=1, le=100_000)
    no_member_terminal: Literal["no_member_converged_zero_return"]
    bases: tuple[MbbpBasisDescriptorV7, ...] = Field(min_length=1)

    @field_validator("bases", mode="before")
    @classmethod
    def basis_arrays_are_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def basis_order_and_caps_are_closed(self) -> "MbbpEnsembleV7":
        if len(self.bases) > self.max_total_members:
            raise ValueError("MBBP basis count exceeds max_total_members")
        observed = tuple((basis.local_ordinal, basis.member_id) for basis in self.bases)
        if observed != tuple(sorted(observed)) or len({basis.member_id for basis in self.bases}) != len(self.bases):
            raise ValueError("MBBP bases require unique member IDs in stable ordinal order")
        return self


class MbbpListSelectionV7(StrictModel):
    kind: Literal["frequency_over_weight_plus_one"]
    tie_rule: Literal["local_ordinal_then_lineage"]


class MbbpCoordinateVoteV7(StrictModel):
    object: Literal["correction_bits"]
    electorate_rule: Literal["admitted_members"]
    aggregation: Literal["coordinate_majority"]
    tie_bit: Literal[0, 1]


class CanonicalExperimentV7(CanonicalExperimentV3):
    """Strict public MBBP-LD experiment; earlier schemas retain their meaning."""

    schema_version: Literal[7]
    numerical_profile: Literal["cpu-float64-min-sum-v1"]
    ensemble: MbbpEnsembleV7
    list_selection: MbbpListSelectionV7
    vote: MbbpCoordinateVoteV7 | None = None

    @model_validator(mode="after")
    def is_the_closed_mbbp_ld_profile(self) -> "CanonicalExperimentV7":
        roles = {role.value: policy.kind for role, policy in self.policies.in_role_order()}
        required = {
            "update": "normalized_min_sum", "schedule": "check_node_serial",
            "state_memory": "identity", "intervention": "identity",
            "stopping": "syndrome_or_budget", "selection": "stable_first",
            "postprocessing": "identity",
        }
        assignment = self.policies.update.parameter_assignment
        if roles != required or assignment is None or assignment.shape != "scalar" or assignment.value != 0.875:
            raise ValueError("MBBP-LD requires normalized-min-sum alpha=0.875, serial checks, and independent identity members")
        if (self.evidence.relation, self.evidence.fixture) not in {
            ("canonical_implemented", "development_fixture"),
            ("pilot_adaptation", "pilot_adaptation"),
        } or self.evidence.assessment_status != "not_assessed":
            raise ValueError("public MBBP-LD requires a not-assessed canonical or pilot-adaptation evidence label")
        if self.vote is not None:
            raise ValueError("coordinate-majority voting is declared but not yet executable in the public MBBP-LD contract")
        if self.ensemble.max_iterations != self.budgets.attempt.max_iterations:
            raise ValueError("MBBP ensemble and public attempt iteration caps must agree")
        total_c2v = len(self.ensemble.bases) * self.ensemble.max_member_c2v_updates
        if total_c2v > self.budgets.attempt.work_limits.check_to_variable_updates:
            raise ValueError("MBBP declared member C2V work exceeds the public attempt work cap")
        return self


ManifestRecord: TypeAlias = ManifestV1 | LegacyManifestV1 | CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV6 | CanonicalExperimentV7


_EXECUTABLE_BASELINE_KINDS = {
    "update": "binary_spa",
    "schedule": "flooding",
    "state_memory": "stateless",
    "intervention": "identity",
    "stopping": "syndrome_or_budget",
    "selection": "stable_first",
    "postprocessing": "identity",
}
_EXECUTABLE_MIN_SUM_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "update": "min_sum"}
_EXECUTABLE_NORMALIZED_MIN_SUM_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "update": "normalized_min_sum"}
_EXECUTABLE_OFFSET_MIN_SUM_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "update": "offset_min_sum"}
_EXECUTABLE_LAYERED_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "layered"}
_EXECUTABLE_CHECK_SERIAL_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "check_node_serial"}
_EXECUTABLE_VARIABLE_SERIAL_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "variable_node_serial"}
_EXECUTABLE_RESIDUAL_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "residual"}
_EXECUTABLE_RANDOMIZED_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "randomized"}
_EXECUTABLE_GROUP_SHUFFLED_SPA_KINDS = {**_EXECUTABLE_BASELINE_KINDS, "schedule": "group_shuffled"}
_EXECUTABLE_LOCAL_SPA_KINDS = (
    _EXECUTABLE_LAYERED_SPA_KINDS,
    _EXECUTABLE_CHECK_SERIAL_SPA_KINDS,
    _EXECUTABLE_VARIABLE_SERIAL_SPA_KINDS,
    _EXECUTABLE_RESIDUAL_SPA_KINDS,
    _EXECUTABLE_RANDOMIZED_SPA_KINDS,
    _EXECUTABLE_GROUP_SHUFFLED_SPA_KINDS,
)
_EXECUTABLE_LOCAL_MIN_SUM_KINDS = tuple(
    {**local, "update": update}
    for local in (
        _EXECUTABLE_LAYERED_SPA_KINDS,
        _EXECUTABLE_CHECK_SERIAL_SPA_KINDS,
        _EXECUTABLE_VARIABLE_SERIAL_SPA_KINDS,
    )
    for update in ("min_sum", "normalized_min_sum", "offset_min_sum")
)
_IDENTITY_ONLY_ROLES = frozenset({"state_memory", "intervention", "postprocessing"})


def validate_executable_canonical_baseline(composition: CanonicalCompositionSpec):
    """Admit only the Phase 2 policy composition with implemented public behavior."""
    from .canonical.contracts import validate_composition

    resolved = validate_composition(composition)
    actual = {binding.role.value: binding.kind for binding in resolved.bindings}
    if actual not in (_EXECUTABLE_BASELINE_KINDS, _EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS, *_EXECUTABLE_LOCAL_SPA_KINDS, *_EXECUTABLE_LOCAL_MIN_SUM_KINDS):
        raise ValueError(
            "executable canonical baseline compatibility requires a closed flooding/layered min-sum family or a binary_spa local schedule composition with stateless/"
            "identity/syndrome_or_budget/stable_first/identity policy kinds"
        )
    return resolved


def executable_canonical_policy_effects(composition: CanonicalCompositionSpec) -> dict[str, dict[str, str]]:
    """Return public binding IDs with their implemented or identity-only effect."""
    resolved = validate_executable_canonical_baseline(composition)
    return {
        binding.role.value: {
            "binding_id": binding.binding_id,
            "effect": "identity_only" if binding.role.value in _IDENTITY_ONLY_ROLES else "active",
        }
        for binding in resolved.bindings
    }


@dataclass(frozen=True)
class ResolvedExperiment:
    """Preflight output; runner receives verified code instead of manifest paths."""

    manifest: ManifestRecord
    code: CssCode
    artifact: LoadedArtifact | None


def _read_value(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, (str, Path)):
        path = Path(value)
        if not path.is_file():
            raise FileNotFoundError(path)
        decoded = json.loads(path.read_text(encoding="utf-8"))
    else:
        decoded = value
    if not isinstance(decoded, dict):
        raise ValueError("manifest must be a JSON object")
    return decoded


def parse_manifest(value: ManifestV1 | CanonicalManifestV2 | CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV6 | CanonicalExperimentV7 | dict[str, Any] | str | Path) -> ManifestRecord:
    """Dispatch complete native and canonical schemas without changing v1 meanings."""
    if isinstance(value, (ManifestV1, CanonicalManifestV2, CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV6, CanonicalExperimentV7)):
        return value
    decoded = _read_value(value)
    if decoded.get("schema_version") == 7 and "ensemble" in decoded:
        return CanonicalExperimentV7.model_validate(decoded)
    if decoded.get("schema_version") == 6:
        return CanonicalExperimentV6.model_validate(decoded)
    if decoded.get("schema_version") == 5:
        return CanonicalExperimentV5.model_validate(decoded)
    if decoded.get("schema_version") == 4:
        return CanonicalExperimentV4.model_validate(decoded)
    if decoded.get("schema_version") == 3:
        return CanonicalExperimentV3.model_validate(decoded)
    if decoded.get("schema_version") == 2:
        return CanonicalExperimentV2.model_validate(decoded) if "budgets" in decoded else parse_canonical_manifest(decoded)
    if decoded.get("schema_version") != 1:
        raise ValueError(f"unsupported manifest schema version {decoded.get('schema_version')!r}")
    return ManifestV1.model_validate(decoded)


def _parse_for_preflight(value: ManifestRecord | dict[str, Any] | str | Path) -> ManifestRecord:
    if isinstance(value, (ManifestV1, LegacyManifestV1, CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV6, CanonicalExperimentV7)):
        return value
    decoded = _read_value(value)
    if decoded.get("schema_version") == 7 and "ensemble" in decoded:
        return CanonicalExperimentV7.model_validate(decoded)
    if decoded.get("schema_version") == 6:
        return CanonicalExperimentV6.model_validate(decoded)
    if decoded.get("schema_version") == 5:
        return CanonicalExperimentV5.model_validate(decoded)
    if decoded.get("schema_version") == 4:
        return CanonicalExperimentV4.model_validate(decoded)
    if decoded.get("schema_version") == 3:
        return CanonicalExperimentV3.model_validate(decoded)
    if decoded.get("schema_version") == 2:
        return CanonicalExperimentV2.model_validate(decoded)
    if decoded.get("schema_version") != 1:
        raise ValueError(f"unsupported manifest schema version {decoded.get('schema_version')!r}")
    complete_fields = {
        "paper", "artifact", "decoder", "noise", "seed_policy", "budget", "environment",
        "expected_output", "discrepancies",
    }
    if complete_fields.issubset(decoded):
        return ManifestV1.model_validate(decoded)
    return LegacyManifestV1.model_validate(decoded)


def preflight_manifest_bytes(manifest_path: str | Path, manifest_bytes: bytes) -> ResolvedExperiment:
    """Preflight one caller-owned manifest snapshot without rereading its path.

    ``manifest_path`` remains an explicit provenance/artifact-resolution
    boundary for callers that bind a snapshot to a retained source path.  The
    parsed bytes are the only manifest document used by this helper.
    """
    if not isinstance(manifest_path, (str, Path)):
        raise TypeError("manifest snapshot requires its original path")
    if not isinstance(manifest_bytes, bytes):
        raise TypeError("manifest snapshot must be bytes")
    try:
        decoded = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("manifest snapshot is not UTF-8 JSON") from error
    if not isinstance(decoded, dict):
        raise ValueError("manifest snapshot must be a JSON object")
    return preflight(decoded)


def _actual_environment() -> dict[str, str]:
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "numpy": version("numpy"),
        "scipy": version("scipy"),
        "ldpc": version("ldpc"),
        "backend": "cpu",
    }


def _actual_canonical_environment() -> dict[str, str]:
    """Discover only dependencies required by project-owned canonical execution."""
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "numpy": version("numpy"),
        "scipy": version("scipy"),
        "backend": "cpu",
    }


def _matrix_raw_bytes(matrix: np.ndarray) -> bytes:
    """Stable JSON-value bytes preserve each artifact matrix's stored row order."""
    return json.dumps(matrix.tolist(), separators=(",", ":")).encode("utf-8")


def _matrix_semantic_bytes(role: str, matrix: np.ndarray) -> bytes:
    """Role, shape, and bit ordering make the semantic identity unambiguous."""
    return b"BPREG-MATRIX-V1\0" + role.encode("ascii") + b"\0" + (
        f"{matrix.shape[0]}x{matrix.shape[1]}\0".encode("ascii")
    ) + np.packbits(matrix.reshape(-1), bitorder="little").tobytes()


def matrix_hashes(code: CssCode) -> dict[str, str]:
    """Return v1 raw and semantic digests for Hx, Hz, Lx, and Lz in order."""
    validated = code.validate()
    if validated.lx is None or validated.lz is None:
        raise ValueError("matrix identities require the ordered paired logical basis")
    values: dict[str, str] = {}
    for name, role, matrix in (
        ("hx", "Hx", validated.hx), ("hz", "Hz", validated.hz),
        ("lx", "Lx", validated.lx), ("lz", "Lz", validated.lz),
    ):
        values[f"{name}_raw_sha256"] = hashlib.sha256(_matrix_raw_bytes(matrix)).hexdigest()
        values[f"{name}_semantic_sha256"] = hashlib.sha256(
            _matrix_semantic_bytes(role, matrix)
        ).hexdigest()
    return values


def _verify_environment(environment: EnvironmentV1, decoder: DecoderV1) -> None:
    actual = _actual_environment()
    expected = environment.model_dump(exclude={"omp_num_threads"})
    if actual != expected:
        raise ValueError("manifest environment does not match this execution environment")
    if os.environ.get("OMP_NUM_THREADS") != str(environment.omp_num_threads):
        raise ValueError("OMP_NUM_THREADS does not match the manifest requirement")
    if decoder.version != actual["ldpc"]:
        raise ValueError("native decoder version does not match the execution environment")


def _verify_canonical_environment(environment: CanonicalEnvironmentV2) -> None:
    actual = _actual_canonical_environment()
    expected = environment.model_dump(exclude={"omp_num_threads"})
    actual = {key: actual[key] for key in expected}
    if actual != expected:
        raise ValueError("canonical manifest environment does not match this execution environment")
    if os.environ.get("OMP_NUM_THREADS") != str(environment.omp_num_threads):
        raise ValueError("OMP_NUM_THREADS does not match the canonical manifest requirement")


def _resolved_artifact_root(root: str) -> str:
    """Resolve a repository-relative pin without serializing a machine path."""
    if not root.startswith("repo:"):
        return root
    relative = Path(root.removeprefix("repo:"))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("repository artifact root must be a non-traversing relative path")
    repository = Path(__file__).resolve().parents[2]
    resolved = (repository / relative).resolve()
    if not resolved.is_relative_to(repository.resolve()):
        raise ValueError("repository artifact root escapes the repository")
    return str(resolved)


def preflight(value: ManifestRecord | dict[str, Any] | str | Path) -> ResolvedExperiment:
    """Resolve immutable CSS input and runtime identity before any simulation work."""
    manifest = _parse_for_preflight(value)
    if isinstance(manifest, LegacyManifestV1):
        # Original minimal v1 tracer records are immutable historical evidence.
        # They are retained for replay only; new records must use ManifestV1.
        return ResolvedExperiment(manifest=manifest, code=fixture_code(), artifact=None)
    if isinstance(manifest, CanonicalExperimentV7):
        # All controls except the artifact-row dimension are closed by model
        # validation.  Resolve the immutable matrix only after that boundary.
        _verify_canonical_environment(manifest.environment)
        if manifest.trace_plan.level != "off" or manifest.profile_plan.level != "low_overhead" or manifest.profile_plan.cohort != "clean":
            raise ValueError("Phase 6 public MBBP requires trace-off clean low-overhead profiling")
        artifact = load_artifact(
            _resolved_artifact_root(manifest.artifact.root), manifest.artifact.path,
            expected_raw_sha256=manifest.artifact.raw_sha256,
            expected_semantic_sha256=manifest.artifact.semantic_sha256,
        )
        if artifact.format_version != manifest.artifact.format_version:
            raise ValueError("Phase 6 artifact format version disagrees with the manifest")
        code = artifact.code.validate()
        for name, expected in manifest.artifact.matrix_hashes.model_dump().items():
            if matrix_hashes(code)[name] != expected:
                raise ValueError("Phase 6 matrix identity does not match the artifact")
        check_count = code.hz.shape[0]
        for basis in manifest.ensemble.bases:
            if any(len(row) != check_count for row in basis.redundant_transforms):
                raise ValueError("MBBP source-row transforms must match the artifact check count")
        return ResolvedExperiment(manifest=manifest, code=code, artifact=artifact)
    if isinstance(manifest, CanonicalExperimentV5):
        # All source/operator/kernel/cap checks above run during strict model
        # validation, before this branch can open an artifact or sample.
        _verify_canonical_environment(manifest.environment)
        validate_composition(manifest.policies)
        if isinstance(manifest, CanonicalExperimentV6):
            from .canonical.memory_execution import validate_single_attempt_memory

            validate_single_attempt_memory(
                manifest.memory, schedule=manifest.policies.schedule.kind,
                update=manifest.policies.update,
                max_iterations=manifest.budgets.attempt.max_iterations,
            )
        if manifest.profile_plan.level != "low_overhead" or manifest.profile_plan.cohort != "clean":
            raise ValueError("Phase 5 public profiling requires a clean low_overhead cohort")
        if manifest.trace_plan.level != "off":
            raise ValueError("Phase 5 semantic trace sidecars are not admitted by this public contract")
        artifact = load_artifact(
            _resolved_artifact_root(manifest.artifact.root), manifest.artifact.path,
            expected_raw_sha256=manifest.artifact.raw_sha256,
            expected_semantic_sha256=manifest.artifact.semantic_sha256,
        )
        if artifact.format_version != manifest.artifact.format_version:
            raise ValueError("Phase 5 artifact format version disagrees with the manifest")
        code = artifact.code.validate()
        hashes = matrix_hashes(code)
        for name, expected in manifest.artifact.matrix_hashes.model_dump().items():
            if hashes[name] != expected:
                raise ValueError("Phase 5 matrix identity does not match the artifact")
        if manifest.intervention.kind == "restart_belief" and manifest.artifact.code_id == "b1-ghp-882":
            if code.hz.shape != (441, 882) or code.hx.shape != (441, 882):
                raise ValueError("B1 restart artifact dimensions are not source compatible")
        return ResolvedExperiment(manifest=manifest, code=code, artifact=artifact)
    if isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3)):
        _verify_canonical_environment(manifest.environment)
        if manifest.trace_plan.level != "off":
            if not isinstance(manifest, CanonicalExperimentV4) or manifest.relay is not None:
                raise ValueError("enabled canonical traces require a non-Relay CanonicalExperimentV4 memory manifest")
            # Validate the existing semantic-sidecar grammar before artifact
            # resolution, sample generation, or ledger ownership.  The root is
            # deliberately inert here; the runner confines the real sidecar to
            # its public output directory.
            from .canonical.tracing import TracePlan

            try:
                TracePlan(
                    root=Path.cwd(), level=manifest.trace_plan.level,
                    relative_dir=manifest.trace_plan.relative_dir,
                    max_records=manifest.trace_plan.max_records,
                    max_bytes=manifest.trace_plan.max_bytes,
                    label=manifest.trace_plan.label,
                )
            except ValueError as error:
                raise ValueError(f"canonical trace plan is not a bounded semantic-sidecar contract: {error}") from error
            if manifest.trace_plan.label != "prespecified_campaign":
                raise ValueError("enabled canonical traces require a prespecified_campaign trace label")
        if manifest.profile_plan.level != "low_overhead" or manifest.profile_plan.cohort != "clean":
            raise ValueError(
                "canonical public profile plan requires a clean low_overhead cohort until a bounded quota exists"
            )
        # Closed registry resolution is deliberately before any sample, ledger, or kernel work.
        composition = validate_executable_canonical_baseline(manifest.policies)
        if isinstance(manifest, CanonicalExperimentV4):
            memory_decision = validate_memory_compatibility(
                manifest.memory,
                update_rule=manifest.policies.update.kind,
                schedule=manifest.policies.schedule.kind,
            )
            if not memory_decision.admitted:
                raise ValueError(memory_decision.reason)
            if manifest.relay is None:
                from .canonical.memory_execution import validate_single_attempt_memory

                validate_single_attempt_memory(
                    manifest.memory, schedule=manifest.policies.schedule.kind,
                    update=manifest.policies.update, max_iterations=manifest.budgets.attempt.max_iterations,
                )
        if type(manifest) is CanonicalExperimentV2 and manifest.policies.update.kind != "binary_spa":
            raise ValueError("CanonicalExperimentV2 preserves only historical binary_spa semantics")
        if isinstance(manifest, CanonicalExperimentV3):
            actual = {binding.role.value: binding.kind for binding in composition.bindings}
            refresh = manifest.policies.update.parameter_refresh
            assignment = manifest.policies.update.parameter_assignment
            if assignment is not None and assignment.shape == "source_iteration":
                assert assignment.values is not None
                if len(assignment.values) < manifest.budgets.attempt.max_iterations:
                    raise ValueError(
                        "source_iteration parameter assignment must declare every attempted canonical iteration"
                    )
            if refresh is not None and (refresh.scope != "configuration" or manifest.policies.schedule.kind != "flooding"):
                raise ValueError("executable generated assignments require configuration refresh under flooding")
            if actual in _EXECUTABLE_LOCAL_SPA_KINDS and manifest.numerical_profile != "cpu-float64-spa-v1":
                raise ValueError("CanonicalExperimentV3 local SPA schedules require the cpu-float64-spa-v1 profile")
            if actual in (_EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS, *_EXECUTABLE_LOCAL_MIN_SUM_KINDS) and manifest.numerical_profile != "cpu-float64-min-sum-v1":
                raise ValueError("CanonicalExperimentV3 min-sum updates require the cpu-float64-min-sum-v1 profile")
            if actual not in (_EXECUTABLE_BASELINE_KINDS, *_EXECUTABLE_LOCAL_SPA_KINDS, *_EXECUTABLE_LOCAL_MIN_SUM_KINDS, _EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS):
                raise ValueError("CanonicalExperimentV3 requires a closed promoted local-step composition")
        artifact = load_artifact(
            _resolved_artifact_root(manifest.artifact.root), manifest.artifact.path,
            expected_raw_sha256=manifest.artifact.raw_sha256,
            expected_semantic_sha256=manifest.artifact.semantic_sha256,
        )
        if artifact.format_version != manifest.artifact.format_version:
            raise ValueError("canonical artifact format version does not match manifest")
        code = artifact.code.validate()
        if isinstance(manifest, CanonicalExperimentV3) and manifest.policies.schedule.kind == "group_shuffled" and code.hz.shape[0] < 2:
            raise ValueError("group_shuffled requires at least two checks")
        for name, expected in manifest.artifact.matrix_hashes.model_dump().items():
            if matrix_hashes(code)[name] != expected:
                raise ValueError("canonical matrix identity does not match the artifact")
        return ResolvedExperiment(manifest=manifest, code=code, artifact=artifact)
    if manifest.implementation.source_artifact_status != "verified":
        raise ValueError("source artifact is not verified")
    _verify_environment(manifest.environment, manifest.decoder)
    artifact = load_artifact(
        _resolved_artifact_root(manifest.artifact.root),
        manifest.artifact.path,
        expected_raw_sha256=manifest.artifact.raw_sha256,
        expected_semantic_sha256=manifest.artifact.semantic_sha256,
    )
    if artifact.format_version != manifest.artifact.format_version:
        raise ValueError("artifact format version does not match manifest")
    # Explicitly validate again at the trust boundary even though the loader does.
    code = artifact.code.validate()
    expected_hashes = manifest.artifact.matrix_hashes.model_dump()
    actual_hashes = matrix_hashes(code)
    for name, expected in expected_hashes.items():
        if actual_hashes[name] != expected:
            matrix, hash_kind, _ = name.split("_", 2)
            label = f"{matrix.upper()[0]}{matrix[1:]} {hash_kind} SHA-256"
            raise ValueError(f"{label} does not match the artifact")
    return ResolvedExperiment(manifest=manifest, code=code, artifact=artifact)


def manifest_digest(manifest: ManifestRecord) -> str:
    document = manifest.model_dump(mode="json")
    # Preserve the legacy digest when this optional extension is absent: that
    # digest is also the default deterministic physical-sample identity.
    randomness = document.get("randomness")
    if isinstance(randomness, dict) and randomness.get("physical_sample_identity") is None:
        randomness.pop("physical_sample_identity", None)
    payload = json.dumps(
        document, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def qualify_cluster_artifact(
    value: dict[str, Any] | str | Path, *, approved_root: str | Path
) -> ClusterArtifactQualification:
    """Public preflight for a non-executable, externally supplied cluster artifact.

    The root is supplied independently of the serialized specification so a report
    binds source bytes and compatibility facts without treating a local path as
    source evidence.  The result is deliberately not a canonical experiment and
    cannot enter sampling or schedule execution.
    """
    decoded = _read_value(value)
    if "approved_root" in decoded:
        raise ValueError("cluster artifact specification must not serialize its approved root")
    return load_cluster_artifact(ClusterArtifactSpec.from_mapping({**decoded, "approved_root": str(approved_root)}))
