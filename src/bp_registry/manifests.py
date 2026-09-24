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
from .canonical.contracts import CanonicalCompositionSpec, CanonicalCompositionSpecV3, CanonicalManifestV2, parse_canonical_manifest
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


class CanonicalEvidenceV2(StrictModel):
    relation: Literal["canonical_implemented"]
    fixture: Literal["development_fixture"]
    assessment_status: Literal["not_assessed"]
    procedure: str = Field(min_length=1)
    sources: tuple[str, ...] = Field(min_length=1)
    discrepancies: tuple[str, ...] = Field(min_length=1)

    @field_validator("sources", "discrepancies", mode="before")
    @classmethod
    def evidence_lists_are_tuples(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value


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


ManifestRecord: TypeAlias = ManifestV1 | LegacyManifestV1 | CanonicalExperimentV2 | CanonicalExperimentV3


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
_EXECUTABLE_LOCAL_SPA_KINDS = (
    _EXECUTABLE_LAYERED_SPA_KINDS,
    _EXECUTABLE_CHECK_SERIAL_SPA_KINDS,
    _EXECUTABLE_VARIABLE_SERIAL_SPA_KINDS,
    _EXECUTABLE_RESIDUAL_SPA_KINDS,
    _EXECUTABLE_RANDOMIZED_SPA_KINDS,
)
_IDENTITY_ONLY_ROLES = frozenset({"state_memory", "intervention", "postprocessing"})


def validate_executable_canonical_baseline(composition: CanonicalCompositionSpec):
    """Admit only the Phase 2 policy composition with implemented public behavior."""
    from .canonical.contracts import validate_composition

    resolved = validate_composition(composition)
    actual = {binding.role.value: binding.kind for binding in resolved.bindings}
    if actual not in (_EXECUTABLE_BASELINE_KINDS, _EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS, *_EXECUTABLE_LOCAL_SPA_KINDS):
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


def parse_manifest(value: ManifestV1 | CanonicalManifestV2 | CanonicalExperimentV2 | CanonicalExperimentV3 | dict[str, Any] | str | Path) -> ManifestV1 | CanonicalManifestV2 | CanonicalExperimentV2 | CanonicalExperimentV3:
    """Dispatch complete native and canonical schemas without changing v1 meanings."""
    if isinstance(value, (ManifestV1, CanonicalManifestV2, CanonicalExperimentV2, CanonicalExperimentV3)):
        return value
    decoded = _read_value(value)
    if decoded.get("schema_version") == 3:
        return CanonicalExperimentV3.model_validate(decoded)
    if decoded.get("schema_version") == 2:
        return CanonicalExperimentV2.model_validate(decoded) if "budgets" in decoded else parse_canonical_manifest(decoded)
    if decoded.get("schema_version") != 1:
        raise ValueError(f"unsupported manifest schema version {decoded.get('schema_version')!r}")
    return ManifestV1.model_validate(decoded)


def _parse_for_preflight(value: ManifestRecord | dict[str, Any] | str | Path) -> ManifestRecord:
    if isinstance(value, (ManifestV1, LegacyManifestV1, CanonicalExperimentV2, CanonicalExperimentV3)):
        return value
    decoded = _read_value(value)
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


def preflight(value: ManifestRecord | dict[str, Any] | str | Path) -> ResolvedExperiment:
    """Resolve immutable CSS input and runtime identity before any simulation work."""
    manifest = _parse_for_preflight(value)
    if isinstance(manifest, LegacyManifestV1):
        # Original minimal v1 tracer records are immutable historical evidence.
        # They are retained for replay only; new records must use ManifestV1.
        return ResolvedExperiment(manifest=manifest, code=fixture_code(), artifact=None)
    if isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3)):
        _verify_canonical_environment(manifest.environment)
        if manifest.trace_plan.level != "off":
            raise ValueError("canonical trace plan must be off until a public trace hook is implemented")
        if manifest.profile_plan.level != "low_overhead" or manifest.profile_plan.cohort != "clean":
            raise ValueError(
                "canonical public profile plan requires a clean low_overhead cohort until a bounded quota exists"
            )
        # Closed registry resolution is deliberately before any sample, ledger, or kernel work.
        composition = validate_executable_canonical_baseline(manifest.policies)
        if type(manifest) is CanonicalExperimentV2 and manifest.policies.update.kind != "binary_spa":
            raise ValueError("CanonicalExperimentV2 preserves only historical binary_spa semantics")
        if isinstance(manifest, CanonicalExperimentV3):
            actual = {binding.role.value: binding.kind for binding in composition.bindings}
            if actual in _EXECUTABLE_LOCAL_SPA_KINDS and manifest.numerical_profile != "cpu-float64-spa-v1":
                raise ValueError("CanonicalExperimentV3 local SPA schedules require the cpu-float64-spa-v1 profile")
            if actual in (_EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS) and manifest.numerical_profile != "cpu-float64-min-sum-v1":
                raise ValueError("CanonicalExperimentV3 min-sum updates require the cpu-float64-min-sum-v1 profile")
            if actual not in (*_EXECUTABLE_LOCAL_SPA_KINDS, _EXECUTABLE_MIN_SUM_KINDS, _EXECUTABLE_NORMALIZED_MIN_SUM_KINDS, _EXECUTABLE_OFFSET_MIN_SUM_KINDS):
                raise ValueError("CanonicalExperimentV3 requires a closed promoted local-step composition")
        artifact = load_artifact(
            manifest.artifact.root, manifest.artifact.path,
            expected_raw_sha256=manifest.artifact.raw_sha256,
            expected_semantic_sha256=manifest.artifact.semantic_sha256,
        )
        if artifact.format_version != manifest.artifact.format_version:
            raise ValueError("canonical artifact format version does not match manifest")
        code = artifact.code.validate()
        for name, expected in manifest.artifact.matrix_hashes.model_dump().items():
            if matrix_hashes(code)[name] != expected:
                raise ValueError("canonical matrix identity does not match the artifact")
        return ResolvedExperiment(manifest=manifest, code=code, artifact=artifact)
    if manifest.implementation.source_artifact_status != "verified":
        raise ValueError("source artifact is not verified")
    _verify_environment(manifest.environment, manifest.decoder)
    artifact = load_artifact(
        manifest.artifact.root,
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
    payload = json.dumps(
        manifest.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
