"""Strict campaign-specification and acyclic one-unit plan records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import base64
import json
import math
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ..manifests import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"
_MAX_EVENTS = 1_000_000
_MAX_EVIDENCE_BYTES = 16 * 1_024 * 1024 * 1024
_MAX_STORAGE_BYTES = 16 * 1_024 * 1024 * 1024
_MAX_DECODER_WORK = 1_000_000_000_000
_TERMINAL_STATUSES = frozenset({
    "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
    "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
    "infrastructure_interruption",
})


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole compact, finite JSON representation used for identities."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _digest(domain: str, payload: bytes) -> str:
    return sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


def _finite_probability(value: float, *, name: str, allow_zero: bool = False) -> float:
    if not math.isfinite(value) or value < 0.0 or value >= 1.0 or (not allow_zero and value == 0.0):
        raise ValueError(f"{name} must be a finite probability in the declared range")
    return value


class ScientificResourceCapsV1(StrictModel):
    """Digest-bound scientific limits; scheduler allocation is intentionally absent."""

    max_shots: int = Field(ge=1, le=_MAX_EVENTS)
    max_looks: int = Field(ge=1, le=1_000)
    max_batch_size: int = Field(ge=1, le=_MAX_EVENTS)
    max_decoder_work: int = Field(ge=1, le=_MAX_DECODER_WORK)
    max_events: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    max_storage_bytes: int = Field(ge=1, le=_MAX_STORAGE_BYTES)


class TargetReferenceV1(StrictModel):
    """One frozen target interval and its content-addressed provenance receipt."""

    target_id: str = Field(min_length=1, max_length=128)
    target_receipt_sha256: str = Field(pattern=_SHA256)
    lower: float
    upper: float
    absolute_tolerance: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def valid_target_band(self) -> "TargetReferenceV1":
        for name in ("lower", "upper", "absolute_tolerance"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.lower > self.upper:
            raise ValueError("target lower bound cannot exceed its upper bound")
        return self


class ExactIntervalV1(StrictModel):
    method: Literal["exact_clopper_pearson"]
    confidence_level: float

    @field_validator("confidence_level")
    @classmethod
    def finite_confidence_level(cls, value: float) -> float:
        return _finite_probability(value, name="confidence_level")


class ExactInverseBinomialIntervalV1(StrictModel):
    """Exact interval input for a completed ordered failure-count prefix."""

    method: Literal["exact_inverse_binomial"]
    confidence_level: float
    stopping_event: Literal["decoder_logical_failure_v1"]
    target_failures: int = Field(ge=1, le=_MAX_EVENTS)
    inferential_trials: int = Field(ge=1, le=_MAX_EVENTS)
    inferential_prefix_sha256: str = Field(pattern=_SHA256)
    authorized_tail_count: int = Field(ge=0, le=_MAX_EVENTS)
    authorized_tail_sha256: str = Field(pattern=_SHA256)

    @field_validator("confidence_level")
    @classmethod
    def finite_confidence_level(cls, value: float) -> float:
        return _finite_probability(value, name="confidence_level")

    @model_validator(mode="after")
    def target_fits_prefix(self) -> "ExactInverseBinomialIntervalV1":
        if self.inferential_trials < self.target_failures:
            raise ValueError("inverse-binomial inferential trials cannot precede target failures")
        return self


class MultiplicativeTargetRuleV1(StrictModel):
    """Frozen equivalence factor, separate from source target precision."""

    rule: Literal["multiplicative_target_interval_containment_v1"]
    factor: float

    @field_validator("factor")
    @classmethod
    def finite_factor(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 1.0 or value > 100.0:
            raise ValueError("multiplicative target factor must be finite and in (1, 100]")
        return value


class AssessmentFamilyV1(StrictModel):
    family_id: str = Field(min_length=1, max_length=128)
    alpha: float
    member_target_ids: tuple[str, ...] = Field(min_length=1, max_length=1_000)

    @field_validator("member_target_ids", mode="before")
    @classmethod
    def tuple_members(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("alpha")
    @classmethod
    def finite_alpha(cls, value: float) -> float:
        return _finite_probability(value, name="family alpha")

    @model_validator(mode="after")
    def unique_members(self) -> "AssessmentFamilyV1":
        if len(set(self.member_target_ids)) != len(self.member_target_ids) or any(not member for member in self.member_target_ids):
            raise ValueError("assessment-family target membership must be nonempty and unique")
        return self


class FixedShotStoppingV1(StrictModel):
    mode: Literal["fixed_shot"]
    final_shots: int = Field(ge=1, le=_MAX_EVENTS)
    batch_size: int = Field(ge=1, le=_MAX_EVENTS)

    @model_validator(mode="after")
    def full_final_batch(self) -> "FixedShotStoppingV1":
        if self.batch_size > self.final_shots:
            raise ValueError("fixed-shot batch_size cannot exceed final_shots")
        return self


class LookAlphaAllocationV1(StrictModel):
    family_id: str = Field(min_length=1, max_length=128)
    target_id: str = Field(min_length=1, max_length=128)
    look: int = Field(ge=1, le=_MAX_EVENTS)
    alpha: float

    @field_validator("alpha")
    @classmethod
    def finite_local_alpha(cls, value: float) -> float:
        return _finite_probability(value, name="local alpha")


class FiniteLookStoppingV1(StrictModel):
    mode: Literal["finite_look"]
    cumulative_looks: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    batch_sizes: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    minimum_terminal_shots: int = Field(ge=1, le=_MAX_EVENTS)
    stop_rule: Literal["all_primary_decisions_resolved_or_maximum_reached"]
    alpha_allocations: tuple[LookAlphaAllocationV1, ...] = Field(min_length=1, max_length=1_000_000)

    @field_validator("cumulative_looks", "batch_sizes", mode="before")
    @classmethod
    def tuple_ints(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("alpha_allocations", mode="before")
    @classmethod
    def tuple_allocations(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def whole_batch_boundaries(self) -> "FiniteLookStoppingV1":
        if len(self.cumulative_looks) != len(self.batch_sizes):
            raise ValueError("finite-look boundaries and batch sizes must have equal length")
        previous = 0
        for boundary, batch_size in zip(self.cumulative_looks, self.batch_sizes, strict=True):
            if boundary <= previous or boundary > _MAX_EVENTS or batch_size < 1 or batch_size > _MAX_EVENTS:
                raise ValueError("finite-look boundaries must be strictly increasing bounded integers")
            if (boundary - previous) % batch_size:
                raise ValueError("each finite-look increment must contain whole declared batches")
            previous = boundary
        if self.minimum_terminal_shots > self.cumulative_looks[-1]:
            raise ValueError("minimum terminal evidence cannot exceed the final look")
        return self


class FailureCountStoppingV1(StrictModel):
    """A bounded, ordered negative-binomial stopping record.

    The target-th decoder failure is the inferential terminal. Completed shots
    later in that already-authorized batch remain provenance and cost evidence,
    never additional inverse-binomial trials.
    """

    mode: Literal["failure_count"]
    target_failures: int = Field(ge=1, le=_MAX_EVENTS)
    batch_size: int = Field(ge=1, le=_MAX_EVENTS)
    shot_order: Literal["campaign_cohort_point_sample_ordinal_v1"]
    failure_event: Literal["decoder_logical_failure_v1"]
    terminal_batch_authorization_sha256: str = Field(pattern=_SHA256)
    cap_authorization_sha256: str = Field(pattern=_SHA256)
    terminal_state: Literal["target_reached", "cap_censored"]
    terminal_failure_ordinal: int | None = Field(default=None, ge=1, le=_MAX_EVENTS)
    cumulative_failures_before_terminal: int | None = Field(default=None, ge=0, le=_MAX_EVENTS)
    cumulative_failures_at_terminal: int = Field(ge=0, le=_MAX_EVENTS)
    authorized_tail_ordinals: tuple[int, ...] = Field(default=(), max_length=_MAX_EVENTS)

    @field_validator("authorized_tail_ordinals", mode="before")
    @classmethod
    def tuple_tail_ordinals(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def exact_target_prefix_or_censored_cap(self) -> "FailureCountStoppingV1":
        if self.terminal_state == "target_reached":
            if self.terminal_failure_ordinal is None or self.cumulative_failures_before_terminal is None:
                raise ValueError("target-reached stopping requires the exact target-th-failure ordinal and prefix count")
            if (self.cumulative_failures_before_terminal != self.target_failures - 1
                    or self.cumulative_failures_at_terminal != self.target_failures):
                raise ValueError("target-reached stopping must bind the exact target-th failure prefix")
            terminal_batch_end = ((self.terminal_failure_ordinal - 1) // self.batch_size + 1) * self.batch_size
            if (tuple(sorted(self.authorized_tail_ordinals)) != self.authorized_tail_ordinals
                    or len(set(self.authorized_tail_ordinals)) != len(self.authorized_tail_ordinals)
                    or any(ordinal <= self.terminal_failure_ordinal or ordinal > terminal_batch_end
                           for ordinal in self.authorized_tail_ordinals)):
                raise ValueError("authorized tail ordinals must be unique later shots in the terminal batch")
        else:
            if (self.terminal_failure_ordinal is not None
                    or self.cumulative_failures_before_terminal is not None
                    or self.cumulative_failures_at_terminal >= self.target_failures
                    or self.authorized_tail_ordinals):
                raise ValueError("cap-censored stopping cannot claim a target terminal or authorized tail")
        return self


def _checked_product(left: int, right: int, *, name: str, maximum: int) -> int:
    """Multiply nonnegative bounded integers without accepting an overflow."""
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        raise ValueError(f"{name} operands must be nonnegative integers")
    if left and right > maximum // left:
        raise ValueError(f"{name} exceeds the executable checked-arithmetic bound")
    return left * right


class InverseBinomialProcedureV1(StrictModel):
    """Inference procedure frozen before any failure-count work begins."""

    method: Literal["exact_inverse_binomial"]
    confidence_level: float
    sidedness: Literal["two_sided"]

    @field_validator("confidence_level")
    @classmethod
    def finite_confidence_level(cls, value: float) -> float:
        return _finite_probability(value, name="confidence_level")


class FailureCountCampaignCapsV1(StrictModel):
    """Prospective finite caps; wall time is an observed-boundary authorization."""

    max_shots: int = Field(ge=1, le=_MAX_EVENTS)
    max_decoder_work: int = Field(ge=1, le=_MAX_DECODER_WORK)
    max_events: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    max_storage_bytes: int = Field(ge=1, le=_MAX_STORAGE_BYTES)
    max_wall_seconds: float = Field(gt=0.0, le=86_400.0)

    @field_validator("max_wall_seconds")
    @classmethod
    def finite_wall_cap(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("max_wall_seconds must be finite")
        return value


class FailureCountExecutableLimitReceiptV1(StrictModel):
    """Independently derived per-unit maxima for a prospective policy.

    The derived fields are checked equations over validated manifest, decoder,
    ledger, serializer, and artifact dimensions.  They are therefore evidence
    of executable limits, not a second set of user-declared caps.
    """

    schema_name: Literal["failure_count_executable_limit_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    derivation_version: Literal["v1"]
    manifest_dimensions_sha256: str = Field(pattern=_SHA256)
    policy_binding_sha256: str = Field(pattern=_SHA256)
    serializer_sha256: str = Field(pattern=_SHA256)
    artifact_layout_sha256: str = Field(pattern=_SHA256)
    verifier_sha256: str = Field(pattern=_SHA256)
    max_decoder_iterations: int = Field(ge=1, le=_MAX_EVENTS)
    work_per_iteration: int = Field(ge=1, le=_MAX_DECODER_WORK)
    max_ledger_events_per_unit: int = Field(ge=1, le=_MAX_EVENTS)
    serializer_bytes_per_event: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    artifact_storage_bytes_per_unit: int = Field(ge=0, le=_MAX_STORAGE_BYTES)
    partial_receipt_reserve_bytes: int = Field(ge=1, le=_MAX_STORAGE_BYTES)
    derived_work_per_unit: int = Field(ge=1, le=_MAX_DECODER_WORK)
    derived_events_per_unit: int = Field(ge=1, le=_MAX_EVENTS)
    derived_evidence_bytes_per_unit: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    derived_storage_bytes_per_unit: int = Field(ge=1, le=_MAX_STORAGE_BYTES)

    @model_validator(mode="after")
    def derived_values_match_executable_dimensions(self) -> "FailureCountExecutableLimitReceiptV1":
        work = _checked_product(
            self.max_decoder_iterations, self.work_per_iteration,
            name="derived work", maximum=_MAX_DECODER_WORK,
        )
        evidence_without_reserve = _checked_product(
            self.max_ledger_events_per_unit, self.serializer_bytes_per_event,
            name="derived evidence", maximum=_MAX_EVIDENCE_BYTES,
        )
        evidence = evidence_without_reserve + self.partial_receipt_reserve_bytes
        storage = self.artifact_storage_bytes_per_unit + evidence
        if evidence > _MAX_EVIDENCE_BYTES or storage > _MAX_STORAGE_BYTES:
            raise ValueError("derived executable bytes exceed the supported bound")
        if (self.derived_work_per_unit, self.derived_events_per_unit,
                self.derived_evidence_bytes_per_unit, self.derived_storage_bytes_per_unit) != (
                    work, self.max_ledger_events_per_unit, evidence, storage,
                ):
            raise ValueError("derived executable maxima must match validated dimensions")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-executable-limits-v1", self.primitive_bytes())


class FailureCountBatchAuthorizationV1(StrictModel):
    """Finite local authorization; timeout is enforced only at boundaries."""

    schema_name: Literal["failure_count_batch_authorization_v1"] = Field(alias="schema", serialization_alias="schema")
    executable_limit_receipt_sha256: str = Field(pattern=_SHA256)
    policy_binding_sha256: str = Field(pattern=_SHA256)
    max_local_workers: int = Field(ge=1, le=1_024)
    max_shots_per_batch: int = Field(ge=1, le=_MAX_EVENTS)
    max_work_per_batch: int = Field(ge=1, le=_MAX_DECODER_WORK)
    max_events_per_batch: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes_per_batch: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    max_storage_bytes_per_batch: int = Field(ge=1, le=_MAX_STORAGE_BYTES)
    monotonic_clock: Literal["monotonic_ns_v1"]
    per_unit_timeout_ns: int = Field(ge=1, le=86_400 * 1_000_000_000)

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-batch-authorization-v1", self.primitive_bytes())


class FailureCountPolicyV1(StrictModel):
    """Outcome-independent identity for a bounded failure-count campaign."""

    schema_name: Literal["failure_count_policy_v1"] = Field(alias="schema", serialization_alias="schema")
    policy_binding_sha256: str = Field(pattern=_SHA256)
    campaign_plan_sha256: str = Field(pattern=_SHA256)
    target_failures: int = Field(ge=1, le=_MAX_EVENTS)
    batch_size: int = Field(ge=1, le=_MAX_EVENTS)
    shot_order: Literal["campaign_cohort_point_sample_ordinal_v1"]
    failure_event: Literal["decoder_logical_failure_v1"]
    procedure: InverseBinomialProcedureV1
    multiplicative_rule: MultiplicativeTargetRuleV1
    caps: FailureCountCampaignCapsV1
    cap_precedence: tuple[Literal["wall", "storage", "evidence", "events", "work", "shots"], ...] = Field(min_length=6, max_length=6)
    executable_limits: FailureCountExecutableLimitReceiptV1
    batch_authorization: FailureCountBatchAuthorizationV1
    # Historical policy bytes were strict before guarded interruption support.
    # Pydantic's explicit exclusion keeps those frozen documents byte-stable.
    dispatch_mode: Literal["strict_full_batch", "interruptible_unit"] = Field(
        default="strict_full_batch", exclude_if=lambda value: value == "strict_full_batch",
    )
    interruptible_evidence_bytes: int | None = Field(
        default=None, ge=1, le=_MAX_EVIDENCE_BYTES, exclude_if=lambda value: value is None,
    )
    interruptible_storage_bytes: int | None = Field(
        default=None, ge=1, le=_MAX_STORAGE_BYTES, exclude_if=lambda value: value is None,
    )

    @field_validator("cap_precedence", mode="before")
    @classmethod
    def tuple_cap_precedence(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def independently_authorized_bounds(self) -> "FailureCountPolicyV1":
        if set(self.cap_precedence) != {"wall", "storage", "evidence", "events", "work", "shots"}:
            raise ValueError("cap precedence must contain each finite cap exactly once")
        if self.dispatch_mode == "strict_full_batch" and (
                self.interruptible_evidence_bytes is not None or self.interruptible_storage_bytes is not None):
            raise ValueError("strict failure-count policy cannot declare interruptible byte budgets")
        if self.dispatch_mode == "interruptible_unit" and (
                self.interruptible_evidence_bytes is None or self.interruptible_storage_bytes is None):
            raise ValueError("interruptible failure-count policy requires both scientific byte budgets")
        if (self.dispatch_mode == "strict_full_batch"
                and (self.caps.max_shots < self.batch_size or self.caps.max_shots % self.batch_size)):
            raise ValueError("failure-count shot cap must contain whole authorized batches")
        limits = self.executable_limits
        authorization = self.batch_authorization
        if limits.policy_binding_sha256 != self.policy_binding_sha256:
            raise ValueError("executable limits bind a different prospective policy")
        if (authorization.policy_binding_sha256 != self.policy_binding_sha256
                or authorization.executable_limit_receipt_sha256 != limits.digest()):
            raise ValueError("batch authorization does not bind the verified executable limits")
        if authorization.per_unit_timeout_ns > int(self.caps.max_wall_seconds * 1_000_000_000):
            raise ValueError("per-unit wall authorization exceeds the prospective campaign wall cap")
        required_units = self.batch_size if self.dispatch_mode == "strict_full_batch" else 1
        expected_work = _checked_product(limits.derived_work_per_unit, required_units, name="dispatch work", maximum=_MAX_DECODER_WORK)
        expected_events = _checked_product(limits.derived_events_per_unit, required_units, name="dispatch events", maximum=_MAX_EVENTS)
        expected_evidence = _checked_product(limits.derived_evidence_bytes_per_unit, required_units, name="dispatch evidence", maximum=_MAX_EVIDENCE_BYTES) + limits.partial_receipt_reserve_bytes
        expected_storage = _checked_product(limits.derived_storage_bytes_per_unit, required_units, name="dispatch storage", maximum=_MAX_STORAGE_BYTES) + limits.partial_receipt_reserve_bytes
        if expected_evidence > _MAX_EVIDENCE_BYTES or expected_storage > _MAX_STORAGE_BYTES:
            raise ValueError("batch authorization cannot represent the derived receipt reserve")
        if (authorization.max_shots_per_batch < required_units
                or authorization.max_work_per_batch < expected_work
                or authorization.max_events_per_batch < expected_events
                or authorization.max_evidence_bytes_per_batch < expected_evidence
                or authorization.max_storage_bytes_per_batch < expected_storage):
            raise ValueError("batch authorization is below a derived executable maximum")
        # A campaign cap may deliberately stop before its shot cap.  It must
        # still admit one complete authorized batch (and its control reserve)
        # so the executor can make bounded forward progress honestly.
        if (self.caps.max_decoder_work < expected_work or self.caps.max_events < expected_events
                or self.caps.max_evidence_bytes < expected_evidence
                or self.caps.max_storage_bytes < expected_storage):
            raise ValueError("campaign cap is below one independently derived executable batch")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-policy-v1", self.primitive_bytes())


class FailureCountPartialAttemptV1(StrictModel):
    """Immutable zero-credit evidence for one interrupted failure-count ordinal."""

    schema_name: Literal["failure_count_partial_attempt_v1"] = Field(alias="schema", serialization_alias="schema")
    attempt_id: str = Field(pattern=_SHA256)
    attempt_ordinal: int = Field(ge=1, le=_MAX_EVENTS)
    attempt_sequence: int = Field(ge=1, le=_MAX_EVENTS)
    unit_key: str = Field(min_length=1, max_length=512)
    parent_partial_receipt_sha256: str | None = Field(default=None, pattern=_SHA256)
    campaign_spec_digest: str = Field(pattern=_SHA256)
    campaign_plan_digest: str = Field(pattern=_SHA256)
    policy_sha256: str = Field(pattern=_SHA256)
    authorization_sha256: str = Field(pattern=_SHA256)
    profile_sha256: str = Field(pattern=_SHA256)
    materialized_sample_path: str = Field(min_length=1, max_length=4096)
    materialized_sample_sha256: str | None = Field(default=None, pattern=_SHA256)
    canonical_ledger_path: str = Field(min_length=1, max_length=4096)
    canonical_ledger_sha256: str | None = Field(default=None, pattern=_SHA256)
    interruption_kind: Literal["interrupted_wall", "interrupted_evidence", "interrupted_storage"]
    first_exhausted_cap: Literal["wall", "evidence", "storage"]
    last_completed_boundary: str | None = Field(default=None, max_length=512)
    attempted_bytes: int | None = Field(default=None, ge=1, le=_MAX_STORAGE_BYTES)
    deadline_ns: int | None = Field(default=None, ge=0)
    observed_ns: int | None = Field(default=None, ge=0)
    overshoot_ns: int | None = Field(default=None, ge=0)
    consumed_decoder_work: int = Field(ge=0, le=_MAX_DECODER_WORK)
    consumed_events: int = Field(ge=0, le=_MAX_EVENTS)
    consumed_evidence_bytes: int = Field(ge=0, le=_MAX_EVIDENCE_BYTES)
    consumed_storage_bytes: int = Field(ge=0, le=_MAX_STORAGE_BYTES)
    consumed_control_receipt_bytes: int = Field(ge=0, le=_MAX_STORAGE_BYTES)
    completed_shot_credit: Literal[0] = 0
    failure_credit: Literal[0] = 0

    @model_validator(mode="after")
    def partial_is_zero_credit_and_has_exact_wall_facts(self) -> "FailureCountPartialAttemptV1":
        if self.interruption_kind == "interrupted_wall":
            if (self.deadline_ns is None or self.observed_ns is None or self.overshoot_ns is None
                    or self.overshoot_ns != max(0, self.observed_ns - self.deadline_ns)):
                raise ValueError("wall partial requires exact deadline observation and overshoot")
        elif any(value is not None for value in (self.deadline_ns, self.observed_ns, self.overshoot_ns)):
            raise ValueError("byte partial cannot claim wall interruption facts")
        elif self.attempted_bytes is None:
            raise ValueError("byte partial requires the denied operation's attempted bytes")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-partial-attempt-v1", self.primitive_bytes())


class FailureCountTerminalReceiptV1(StrictModel):
    """Sealed observed terminal facts; this type is forbidden from plans."""

    schema_name: Literal["failure_count_terminal_receipt_v1"] = Field(alias="schema", serialization_alias="schema")
    policy_sha256: str = Field(pattern=_SHA256)
    campaign_plan_sha256: str = Field(pattern=_SHA256)
    executable_limit_receipt_sha256: str = Field(pattern=_SHA256)
    batch_authorization_sha256: str = Field(pattern=_SHA256)
    terminal_state: Literal["target_reached", "cap_censored"]
    terminal_failure_ordinal: int | None = Field(default=None, ge=1, le=_MAX_EVENTS)
    cumulative_failures: int = Field(ge=0, le=_MAX_EVENTS)
    total_completed_shots: int = Field(ge=0, le=_MAX_EVENTS)
    inferential_prefix_sha256: str | None = Field(default=None, pattern=_SHA256)
    authorized_tail_ordinals: tuple[int, ...] = Field(default=(), max_length=_MAX_EVENTS)
    authorized_tail_sha256: str | None = Field(default=None, pattern=_SHA256)
    first_exhausted_cap: Literal["wall", "storage", "evidence", "events", "work", "shots"] | None = None
    realized_decoder_work: int = Field(ge=0, le=_MAX_DECODER_WORK)
    realized_events: int = Field(ge=0, le=_MAX_EVENTS)
    realized_evidence_bytes: int = Field(ge=0, le=_MAX_EVIDENCE_BYTES)
    realized_storage_bytes: int = Field(ge=0, le=_MAX_STORAGE_BYTES)
    wall_boundaries: tuple[tuple[int, int, int], ...] = Field(default=(), max_length=_MAX_EVENTS)

    @field_validator("authorized_tail_ordinals", "wall_boundaries", mode="before")
    @classmethod
    def tuple_observed_values(cls, value: Any) -> Any:
        return tuple(tuple(item) if isinstance(item, list) else item for item in value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def sealed_terminal_shape(self) -> "FailureCountTerminalReceiptV1":
        for deadline, observed, overshoot in self.wall_boundaries:
            if deadline < 0 or observed < 0 or overshoot != max(0, observed - deadline):
                raise ValueError("wall boundary observations must expose exact nonnegative overshoot")
        if self.total_completed_shots and not self.wall_boundaries:
            raise ValueError("dispatched terminal evidence requires a wall boundary observation")
        if self.terminal_state == "target_reached":
            if (self.total_completed_shots < 1 or self.terminal_failure_ordinal is None or self.cumulative_failures < 1
                    or self.inferential_prefix_sha256 is None or self.authorized_tail_sha256 is None
                    or self.first_exhausted_cap is not None):
                raise ValueError("target receipt requires exact observed prefix and tail facts")
            if self.terminal_failure_ordinal > self.total_completed_shots:
                raise ValueError("target terminal ordinal cannot exceed completed shots")
            if (tuple(sorted(self.authorized_tail_ordinals)) != self.authorized_tail_ordinals
                    or any(item <= self.terminal_failure_ordinal for item in self.authorized_tail_ordinals)
                    or self.total_completed_shots != self.terminal_failure_ordinal + len(self.authorized_tail_ordinals)):
                raise ValueError("target receipt tail must be the later completed terminal-batch evidence")
        elif (self.terminal_failure_ordinal is not None or self.inferential_prefix_sha256 is not None
              or self.authorized_tail_ordinals or self.authorized_tail_sha256 is not None
              or self.first_exhausted_cap is None):
            raise ValueError("cap-censored receipt cannot claim inference and must name an exhausted cap")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-terminal-receipt-v1", self.primitive_bytes())

    def validate_against(self, policy: FailureCountPolicyV1) -> "FailureCountTerminalReceiptV1":
        if not isinstance(policy, FailureCountPolicyV1):
            raise ValueError("terminal receipt requires a prospective failure-count policy")
        if (self.policy_sha256 != policy.digest() or self.campaign_plan_sha256 != policy.campaign_plan_sha256
                or self.executable_limit_receipt_sha256 != policy.executable_limits.digest()
                or self.batch_authorization_sha256 != policy.batch_authorization.digest()):
            raise ValueError("terminal receipt does not bind the frozen policy and authorizations")
        if self.total_completed_shots > policy.caps.max_shots:
            raise ValueError("terminal receipt exceeds the frozen shot cap")
        if (self.realized_decoder_work > policy.caps.max_decoder_work or self.realized_events > policy.caps.max_events
                or self.realized_evidence_bytes > policy.caps.max_evidence_bytes
                or self.realized_storage_bytes > policy.caps.max_storage_bytes):
            raise ValueError("terminal receipt exceeds a frozen resource cap")
        if self.terminal_state == "target_reached":
            if self.cumulative_failures != policy.target_failures:
                raise ValueError("target receipt cumulative failures differ from policy target")
            assert self.terminal_failure_ordinal is not None
            batch_end = ((self.terminal_failure_ordinal - 1) // policy.batch_size + 1) * policy.batch_size
            if any(item > batch_end for item in self.authorized_tail_ordinals):
                raise ValueError("target receipt tail escapes the authorized terminal batch")
        else:
            if self.first_exhausted_cap not in policy.cap_precedence:
                raise ValueError("cap-censored receipt names an unauthorized cap")
            if self.cumulative_failures >= policy.target_failures:
                raise ValueError("cap-censored receipt cannot contain the target failure")
        return self


class OutcomeTreatmentV1(StrictModel):
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    all_shot: Literal["success", "failure", "incomplete"]
    conditional: Literal["accepted", "excluded", "incomplete"]


class OutcomeMatrixV1(StrictModel):
    rule_id: Literal["all_shot_v1"]
    treatments: tuple[OutcomeTreatmentV1, ...] = Field(min_length=len(_TERMINAL_STATUSES), max_length=len(_TERMINAL_STATUSES))

    @field_validator("treatments", mode="before")
    @classmethod
    def tuple_treatments(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def total_no_silent_drop_mapping(self) -> "OutcomeMatrixV1":
        mapping = {item.terminal_status: item for item in self.treatments}
        if set(mapping) != _TERMINAL_STATUSES or len(mapping) != len(self.treatments):
            raise ValueError("outcome matrix must cover each terminal status exactly once")
        interruption = mapping["infrastructure_interruption"]
        if interruption.all_shot != "incomplete" or interruption.conditional != "incomplete":
            raise ValueError("infrastructure interruption must remain incomplete")
        for status in ("invalid_syndrome", "no_proposal", "nonconvergence", "timeout"):
            treatment = mapping[status]
            if treatment.all_shot != "failure" or treatment.conditional != "excluded":
                raise ValueError(f"{status} must be all-shot failure and conditionally excluded")
        return self


class CampaignAssessmentV1(StrictModel):
    """All outcome-independent assessment semantics that must freeze before launch."""

    schema_name: Literal["campaign_assessment_v1"] = Field(alias="schema", serialization_alias="schema")
    targets: tuple[TargetReferenceV1, ...] = Field(min_length=1, max_length=1_000)
    interval: ExactIntervalV1 | ExactInverseBinomialIntervalV1 | InverseBinomialProcedureV1 | None
    families: tuple[AssessmentFamilyV1, ...] = Field(min_length=1, max_length=1_000)
    stopping: FixedShotStoppingV1 | FiniteLookStoppingV1 | FailureCountStoppingV1 | FailureCountPolicyV1
    outcome_matrix: OutcomeMatrixV1
    decision_rule: Literal["target_interval_containment_v1"] | MultiplicativeTargetRuleV1
    resources: ScientificResourceCapsV1

    @field_validator("targets", "families", mode="before")
    @classmethod
    def tuple_records(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def complete_frozen_assessment(self) -> "CampaignAssessmentV1":
        target_ids = tuple(target.target_id for target in self.targets)
        family_ids = tuple(family.family_id for family in self.families)
        if len(set(target_ids)) != len(target_ids) or len(set(family_ids)) != len(family_ids):
            raise ValueError("target and family identities must be unique")
        if any(member not in target_ids for family in self.families for member in family.member_target_ids):
            raise ValueError("assessment family references an unknown target")
        if set(member for family in self.families for member in family.member_target_ids) != set(target_ids):
            raise ValueError("every target must belong to a declared comparison family")
        if isinstance(self.stopping, FixedShotStoppingV1):
            if self.resources.max_looks != 1 or self.resources.max_shots != self.stopping.final_shots:
                raise ValueError("fixed-shot resources must declare exactly one final look")
            if not isinstance(self.interval, ExactIntervalV1) or self.decision_rule != "target_interval_containment_v1":
                raise ValueError("fixed-shot assessments require the historical exact interval and decision rule")
        elif isinstance(self.stopping, FiniteLookStoppingV1):
            if self.resources.max_looks != len(self.stopping.cumulative_looks) or self.resources.max_shots != self.stopping.cumulative_looks[-1]:
                raise ValueError("finite-look resources must match the declared final look")
            if self.resources.max_batch_size < max(self.stopping.batch_sizes):
                raise ValueError("resource batch cap cannot be below a declared finite-look batch")
            expected = {
                (family.family_id, target_id, look)
                for family in self.families
                for target_id in family.member_target_ids
                for look in self.stopping.cumulative_looks
            }
            allocations = {(item.family_id, item.target_id, item.look): item.alpha for item in self.stopping.alpha_allocations}
            if set(allocations) != expected or len(allocations) != len(self.stopping.alpha_allocations):
                raise ValueError("finite-look alpha allocations must cover every family target and declared look exactly once")
            for family in self.families:
                spent = sum(value for (family_id, _, _), value in allocations.items() if family_id == family.family_id)
                if spent > family.alpha + 1e-15:
                    raise ValueError("finite-look alpha allocations cannot exceed their family alpha")
            if not isinstance(self.interval, ExactIntervalV1) or self.decision_rule != "target_interval_containment_v1":
                raise ValueError("finite-look assessments require the historical exact interval and decision rule")
        elif isinstance(self.stopping, FailureCountPolicyV1):
            policy = self.stopping
            if (self.resources.max_looks != 1 or self.resources.max_shots != policy.caps.max_shots
                    or self.resources.max_batch_size < policy.batch_size
                    or self.resources.max_decoder_work != policy.caps.max_decoder_work
                    or self.resources.max_events != policy.caps.max_events
                    or self.resources.max_evidence_bytes != policy.caps.max_evidence_bytes
                    or self.resources.max_storage_bytes != policy.caps.max_storage_bytes):
                raise ValueError("failure-count assessment resources must exactly bind prospective policy caps")
            if self.interval is not None:
                raise ValueError("failure-count procedure belongs only to the prospective policy")
            if self.decision_rule != policy.multiplicative_rule:
                raise ValueError("failure-count assessment rule must bind the prospective policy")
        else:
            # The former mixed model remains available as a typed parser for
            # retained receipt evidence, but cannot be frozen into a new plan.
            raise ValueError("legacy mixed failure-count stopping is parser-only; use FailureCountPolicyV1")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-assessment-v1", self.primitive_bytes())


class CampaignSpecV1(StrictModel):
    """Primitive scientific inputs for one fixed-shot CSS campaign unit.

    Executor and scheduler observations deliberately have no field here.  They
    may be recorded in a receipt, but cannot change this specification digest.
    """

    schema_name: Literal["campaign_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    inner_manifest_path: str = Field(min_length=1, max_length=512)
    inner_manifest_sha256: str = Field(pattern=_SHA256)
    source_lock_sha256: str = Field(pattern=_SHA256)
    environment_lock_sha256: str = Field(pattern=_SHA256)
    cohort_id: str = Field(min_length=1, max_length=128)
    point_id: str = Field(min_length=1, max_length=128)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_id: int = Field(ge=0, le=1_000_000)
    arm_id: str = Field(min_length=1, max_length=128)
    decoder_seed_identity: str = Field(min_length=1, max_length=256)
    final_look: int = Field(ge=1, le=1_000_000)
    alpha: float = Field(gt=0.0, lt=1.0)
    outcome_rule: Literal["all_terminal_shots_are_logical_failures"]
    max_events: int = Field(ge=1, le=_MAX_EVENTS)
    max_evidence_bytes: int = Field(ge=1, le=_MAX_EVIDENCE_BYTES)
    assessment: CampaignAssessmentV1 | None = None

    @field_validator("inner_manifest_path")
    @classmethod
    def confined_relative_manifest_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("inner_manifest_path must be a confined relative path")
        return value

    @field_validator("alpha")
    @classmethod
    def finite_alpha(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("alpha must be finite")
        return value

    @model_validator(mode="after")
    def assessment_stopping_matches_campaign_look(self) -> "CampaignSpecV1":
        """Legacy one-unit records have no assessment; assessed campaigns bind its look index."""
        if self.assessment is None:
            return self
        expected_final_look = 1 if isinstance(
            self.assessment.stopping, (FixedShotStoppingV1, FailureCountPolicyV1),
        ) else len(self.assessment.stopping.cumulative_looks)
        if self.final_look != expected_final_look:
            raise ValueError("campaign final_look must equal the frozen assessment final look")
        return self

    def primitive_bytes(self) -> bytes:
        """Canonical bytes before any derived unit or plan identity exists."""
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-spec-v1", self.primitive_bytes())


class CampaignArmV1(StrictModel):
    """One canonical decoder arm confined to its caller-owned campaign root."""

    arm_id: str = Field(min_length=1, max_length=128)
    manifest_path: str = Field(min_length=1, max_length=512)
    manifest_sha256: str = Field(pattern=_SHA256)
    decoder_seed_identity: str = Field(min_length=1, max_length=256)

    @field_validator("manifest_path")
    @classmethod
    def confined_manifest_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("manifest_path must be a confined relative path")
        return value


class SharedSamplerContractV1(StrictModel):
    """All material that must agree before one physical error can be paired."""

    code_id: str = Field(min_length=1, max_length=256)
    artifact_raw_sha256: str = Field(pattern=_SHA256)
    artifact_semantic_sha256: str = Field(pattern=_SHA256)
    matrix_sha256: str = Field(pattern=_SHA256)
    channel_family: Literal["css_code_capacity_v1"]
    x_error_rate: float = Field(ge=0.0, le=1.0)
    z_error_rate: float = Field(ge=0.0, le=1.0)
    sampler_algorithm: Literal["bp_registry_sample_shot_v1"]
    sampler_version: Literal["v1"]
    physical_sample_namespace: str = Field(min_length=1, max_length=256)
    physical_sample_seed: int = Field(ge=0, le=2**63 - 1)

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json"))

    def digest(self) -> str:
        return _digest("bp-registry-shared-sampler-v1", self.primitive_bytes())


class CampaignWorkCoordinateV1(StrictModel):
    """Arm-neutral point and finite physical sample identifiers."""

    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_ids: tuple[int, ...] = Field(min_length=1, max_length=_MAX_EVENTS)

    @field_validator("sample_ids", mode="before")
    @classmethod
    def coerce_sequence_to_tuple(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def unique_sample_ids(self) -> "CampaignWorkCoordinateV1":
        if (len(set(self.sample_ids)) != len(self.sample_ids)
                or any(type(value) is not int or value < 0 or value > _MAX_EVENTS for value in self.sample_ids)):
            raise ValueError("sample_ids must be unique bounded integers")
        return self


class CampaignWorkSpecV1(StrictModel):
    """Strict primitive input for a complete canonical campaign."""

    schema_name: Literal["campaign_work_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    arms: tuple[CampaignArmV1, ...] = Field(min_length=1, max_length=128)
    shared_sampler: SharedSamplerContractV1
    coordinates: tuple[CampaignWorkCoordinateV1, ...] = Field(min_length=1, max_length=_MAX_EVENTS)
    look_sample_boundaries: tuple[int, ...] = Field(min_length=1, max_length=1_000)
    units_per_shard: int = Field(ge=1, le=_MAX_EVENTS)
    assessment: CampaignAssessmentV1
    source_lock_sha256: str = Field(pattern=_SHA256)
    environment_lock_sha256: str = Field(pattern=_SHA256)
    dependency_lock_sha256: str = Field(pattern=_SHA256)
    target_arm_ids: dict[str, str] = Field(min_length=1, max_length=1_000)
    source_denominator_required_by_target: dict[str, bool] = Field(default_factory=dict)
    source_denominators: dict[str, int | None] = Field(default_factory=dict)

    @field_validator("arms", "coordinates", "look_sample_boundaries", mode="before")
    @classmethod
    def tuple_fields(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def complete_pairing_contract(self) -> "CampaignWorkSpecV1":
        arm_ids = tuple(arm.arm_id for arm in self.arms)
        coordinate_ids = tuple((item.cohort_id, item.point_id, item.sample_namespace) for item in self.coordinates)
        sample_count = sum(len(item.sample_ids) for item in self.coordinates)
        if len(set(arm_ids)) != len(arm_ids) or len(set(coordinate_ids)) != len(coordinate_ids):
            raise ValueError("campaign work arm and coordinate identities must be unique")
        if any(item.sample_namespace != self.shared_sampler.physical_sample_namespace for item in self.coordinates):
            raise ValueError("all coordinates must use the shared physical sample namespace")
        if (tuple(sorted(self.look_sample_boundaries)) != self.look_sample_boundaries
                or len(set(self.look_sample_boundaries)) != len(self.look_sample_boundaries)
                or self.look_sample_boundaries[-1] != sample_count):
            raise ValueError("look boundaries must cover each planned physical sample exactly once")
        target_ids = {target.target_id for target in self.assessment.targets}
        if set(self.target_arm_ids) != target_ids or any(arm_id not in arm_ids for arm_id in self.target_arm_ids.values()):
            raise ValueError("each assessed target requires one declared arm")
        if set(self.source_denominator_required_by_target) - target_ids or set(self.source_denominators) - target_ids:
            raise ValueError("source denominator fields reference an unknown target")
        if sample_count * len(self.arms) > self.assessment.resources.max_events:
            raise ValueError("paired work expansion exceeds frozen event cap")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-campaign-work-spec-v1", self.primitive_bytes())


class CampaignExecutionOrderV1(StrictModel):
    """Prospective sample-major order for a matched multi-arm campaign."""

    schema_name: Literal["campaign_execution_order_v1"] = Field(alias="schema", serialization_alias="schema")
    rule: Literal["coordinate_point_namespace_sample_declared_arm_v1"]
    arm_order: tuple[str, ...] = Field(min_length=2, max_length=256)

    @field_validator("arm_order", mode="before")
    @classmethod
    def tuple_arm_order(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def complete_unique_arm_order(self) -> "CampaignExecutionOrderV1":
        if len(set(self.arm_order)) != len(self.arm_order) or any(not arm for arm in self.arm_order):
            raise ValueError("declared arm order requires unique nonempty arm IDs")
        return self


class OrderedCampaignWorkSpecV1(StrictModel):
    """Additive fixed/finite wrapper; historical work-spec bytes stay intact."""

    schema_name: Literal["ordered_campaign_work_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    campaign_work_spec: CampaignWorkSpecV1
    execution_order: CampaignExecutionOrderV1

    @model_validator(mode="after")
    def declared_arms_match_fixed_or_finite_work(self) -> "OrderedCampaignWorkSpecV1":
        declared = self.execution_order.arm_order
        actual = tuple(arm.arm_id for arm in self.campaign_work_spec.arms)
        if len(actual) != len(declared) or set(actual) != set(declared):
            raise ValueError("declared arm order must cover the exact frozen arm set")
        if not isinstance(self.campaign_work_spec.assessment.stopping, (FixedShotStoppingV1, FiniteLookStoppingV1)):
            raise ValueError("ordered multi-arm work requires fixed-shot or finite-look stopping")
        return self

    def normalized_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", by_alias=True)
        inner = payload["campaign_work_spec"]
        inner["arms"] = sorted(inner["arms"], key=lambda item: item["arm_id"])
        inner["coordinates"] = sorted(inner["coordinates"], key=lambda item: (
            item["cohort_id"], item["point_id"], item["sample_namespace"],
        ))
        for coordinate in inner["coordinates"]:
            coordinate["sample_ids"] = sorted(coordinate["sample_ids"])
        return payload

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.normalized_payload())

    def digest(self) -> str:
        return _digest("bp-registry-ordered-campaign-work-spec-v1", self.primitive_bytes())


class FailureCountWorkSpecV1(StrictModel):
    """Outcome-independent authorization for one canonical failure-count arm.

    The nested work specification retains the established manifest, sampler,
    coordinate, and lock grammar.  Restricting it to exactly one arm makes an
    ordinal a scientific shot rather than a completion-order observation.
    """

    schema_name: Literal["failure_count_work_spec_v1"] = Field(alias="schema", serialization_alias="schema")
    campaign_work_spec: CampaignWorkSpecV1
    policy: FailureCountPolicyV1

    @model_validator(mode="after")
    def one_arm_prospective_contract(self) -> "FailureCountWorkSpecV1":
        campaign = self.campaign_work_spec
        if len(campaign.arms) != 1:
            raise ValueError("failure-count canonical work requires exactly one declared arm")
        if campaign.assessment.stopping != self.policy:
            raise ValueError("failure-count work assessment must bind the prospective policy exactly")
        if campaign.assessment.resources.max_shots != self.policy.caps.max_shots:
            raise ValueError("failure-count work resources must bind the prospective policy caps")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def digest(self) -> str:
        return _digest("bp-registry-failure-count-work-spec-v1", self.primitive_bytes())


class MaterializedPhysicalSampleV1(StrictModel):
    """Immutable byte-level physical sample retained before either arm decodes."""

    schema_name: Literal["materialized_physical_sample_v1"] = Field(alias="schema", serialization_alias="schema")
    physical_sample_identity: str = Field(pattern=_SHA256)
    sample_seed_identity: str = Field(pattern=_SHA256)
    cohort_id: str = Field(min_length=1, max_length=256)
    point_id: str = Field(min_length=1, max_length=256)
    sample_namespace: str = Field(min_length=1, max_length=256)
    sample_id: int = Field(ge=0, le=_MAX_EVENTS)
    sampler_contract_sha256: str = Field(pattern=_SHA256)
    x_dtype: Literal["uint8"]
    x_shape: tuple[int, ...] = Field(min_length=1, max_length=2)
    x_bytes_b64: str
    z_dtype: Literal["uint8"]
    z_shape: tuple[int, ...] = Field(min_length=1, max_length=2)
    z_bytes_b64: str
    observations: dict[str, dict[str, Any]] = Field(min_length=1, max_length=8)
    physical_error_sha256: str = Field(pattern=_SHA256)
    materialized_sample_sha256: str = Field(pattern=_SHA256)

    @field_validator("x_shape", "z_shape", mode="before")
    @classmethod
    def tuple_shapes(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def byte_digests_bind_payload(self) -> "MaterializedPhysicalSampleV1":
        try:
            x_bytes, z_bytes = base64.b64decode(self.x_bytes_b64, validate=True), base64.b64decode(self.z_bytes_b64, validate=True)
        except Exception as error:
            raise ValueError("materialized sample has invalid base64 bytes") from error
        error_payload = canonical_json_bytes({"x": self.x_bytes_b64, "z": self.z_bytes_b64})
        if self.physical_error_sha256 != _digest("bp-registry-physical-error-v1", error_payload):
            raise ValueError("materialized sample physical error digest differs from bytes")
        unsigned = self.model_dump(mode="json", by_alias=True, exclude={"materialized_sample_sha256"})
        if self.materialized_sample_sha256 != _digest("bp-registry-materialized-sample-v1", canonical_json_bytes(unsigned)):
            raise ValueError("materialized sample digest differs from bytes")
        if not x_bytes or not z_bytes:
            raise ValueError("materialized error vectors must be nonempty")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))


class BinaryComponentTerminalV1(StrictModel):
    """D-08 terminal evidence for one marginal-only binary component."""

    component: Literal["X", "Z"]
    candidate: tuple[int, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    iterations: int = Field(ge=0, le=_MAX_EVENTS)
    work: dict[str, int]
    syndrome_sha256: str = Field(pattern=_SHA256)

    @field_validator("candidate", mode="before")
    @classmethod
    def binary_candidate(cls, value: Any) -> Any:
        if value is None:
            return value
        candidate = tuple(value)
        if not candidate or any(type(bit) is not int or bit not in (0, 1) for bit in candidate):
            raise ValueError("binary component candidate must be a nonempty binary vector")
        return candidate

    @field_validator("work")
    @classmethod
    def nonnegative_work(cls, value: dict[str, int]) -> dict[str, int]:
        if not value or any(not key or type(amount) is not int or amount < 0 for key, amount in value.items()):
            raise ValueError("component work must be a nonempty nonnegative integer mapping")
        return dict(sorted(value.items()))


class PauliMatchedArmV1(StrictModel):
    """One arm in a D-06 same-materialized-sample comparison."""

    arm_id: Literal["joint", "separate"]
    materialized_sample_sha256: str = Field(pattern=_SHA256)
    candidate_x: tuple[int, ...] | None = None
    candidate_z: tuple[int, ...] | None = None
    terminal_status: Literal[
        "exact", "stabilizer_equivalent", "wrong_logical_action", "invalid_syndrome",
        "no_proposal", "nonconvergence", "timeout", "postselected_rejection",
        "infrastructure_interruption",
    ]
    evaluation: dict[str, Any]
    work: dict[str, int]

    @field_validator("candidate_x", "candidate_z", mode="before")
    @classmethod
    def binary_recovery(cls, value: Any) -> Any:
        return BinaryComponentTerminalV1.binary_candidate(value)

    @field_validator("work")
    @classmethod
    def arm_work(cls, value: dict[str, int]) -> dict[str, int]:
        return BinaryComponentTerminalV1.nonnegative_work(value)


class PauliMatchedPairV1(StrictModel):
    """Complete D-05/D-06/D-08 evidence for one physical Pauli sample."""

    schema_name: Literal["pauli_matched_pair_v1"] = Field(alias="schema", serialization_alias="schema")
    decision_ids: tuple[Literal["D-05", "D-06", "D-08"], ...]
    physical_sample_identity: str = Field(pattern=_SHA256)
    physical_error_sha256: str = Field(pattern=_SHA256)
    materialized_sample_sha256: str = Field(pattern=_SHA256)
    joint: PauliMatchedArmV1
    separate: PauliMatchedArmV1
    components: tuple[BinaryComponentTerminalV1, BinaryComponentTerminalV1]
    record_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def complete_and_replayable_pair(self) -> "PauliMatchedPairV1":
        if self.decision_ids != ("D-05", "D-06", "D-08"):
            raise ValueError("matched pair must cite D-05, D-06, and D-08 in order")
        if self.joint.arm_id != "joint" or self.separate.arm_id != "separate":
            raise ValueError("matched pair requires exactly one joint and one separate arm")
        if (self.joint.materialized_sample_sha256 != self.materialized_sample_sha256
                or self.separate.materialized_sample_sha256 != self.materialized_sample_sha256):
            raise ValueError("both decoder arms must bind the same materialized Pauli sample")
        if tuple(item.component for item in self.components) != ("X", "Z"):
            raise ValueError("matched pair components must be ordered X then Z")
        unsigned = self.model_dump(mode="json", by_alias=True, exclude={"record_sha256"})
        expected = _digest("bp-registry-pauli-matched-pair-v1", canonical_json_bytes(unsigned))
        if self.record_sha256 != expected:
            raise ValueError("matched pair record digest differs from retained evidence")
        return self

    def primitive_bytes(self) -> bytes:
        return canonical_json_bytes(self.model_dump(mode="json", by_alias=True))

    def verify_replay(self) -> "PauliMatchedPairV1":
        return type(self).model_validate_json(self.primitive_bytes())


@dataclass(frozen=True, slots=True)
class CampaignPlanV1:
    """The one-unit frozen plan derived from a primitive campaign specification."""

    campaign_spec: CampaignSpecV1
    campaign_spec_digest: str
    unit_key: str
    shard_id: str
    campaign_plan_preimage: bytes
    campaign_plan_digest: str

    @property
    def campaign_spec_bytes(self) -> bytes:
        return self.campaign_spec.primitive_bytes()

    @property
    def physical_sample_identity(self) -> str:
        payload = canonical_json_bytes({
            "campaign_spec_digest": self.campaign_spec_digest,
            "cohort_id": self.campaign_spec.cohort_id,
            "point_id": self.campaign_spec.point_id,
            "sample_namespace": self.campaign_spec.sample_namespace,
            "sample_id": self.campaign_spec.sample_id,
        })
        return _digest("bp-registry-campaign-physical-sample-v1", payload)

    @property
    def decoder_randomness_identity(self) -> str:
        payload = canonical_json_bytes({
            "campaign_spec_digest": self.campaign_spec_digest,
            "cohort_id": self.campaign_spec.cohort_id,
            "point_id": self.campaign_spec.point_id,
            "sample_id": self.campaign_spec.sample_id,
            "arm_id": self.campaign_spec.arm_id,
            "decoder_seed_identity": self.campaign_spec.decoder_seed_identity,
        })
        return _digest("bp-registry-campaign-decoder-randomness-v1", payload)


def build_one_unit_plan(spec: CampaignSpecV1) -> CampaignPlanV1:
    """Derive one unit before hashing the unsigned plan that seals it."""
    spec_digest = spec.digest()
    coordinate = {
        "campaign_spec_digest": spec_digest,
        "cohort_id": spec.cohort_id,
        "point_id": spec.point_id,
        "sample_id": spec.sample_id,
        "arm_id": spec.arm_id,
    }
    unit_key = _digest("bp-registry-campaign-unit-v1", canonical_json_bytes(coordinate))
    shard_id = _digest("bp-registry-campaign-shard-v1", canonical_json_bytes({"unit_keys": [unit_key]}))
    unsigned_plan = {
        "schema": "campaign_plan_v1",
        "campaign_spec_digest": spec_digest,
        "unit_keys": [unit_key],
        "shards": [{"shard_id": shard_id, "unit_keys": [unit_key]}],
    }
    preimage = canonical_json_bytes(unsigned_plan)
    return CampaignPlanV1(
        campaign_spec=spec,
        campaign_spec_digest=spec_digest,
        unit_key=unit_key,
        shard_id=shard_id,
        campaign_plan_preimage=preimage,
        campaign_plan_digest=_digest("bp-registry-campaign-plan-v1", preimage),
    )
