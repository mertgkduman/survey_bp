"""Measured, fail-closed authorization for bounded campaign execution.

The gate records operational observations without treating them as decoder
semantics.  It accepts only verified, pre-outcome representative clean/profile
pairs and denies an authorization whenever evidence or site ceilings are absent.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
from math import ceil
from types import MappingProxyType
from typing import Literal, Mapping

from bp_registry.canonical.profiling import ProfileMeasurement, ReplayLink, compare_semantics


_DIGEST_LENGTH = 64
_FORBIDDEN_CONTEXT_PARTS = ("secret", "token", "password", "authorization", "cookie", "api_key")
_CEILING_FIELDS = (
    "max_cpu_time_ns", "max_wall_time_ns", "max_storage_bytes", "max_shard_bytes",
    "max_replay_time_ns", "max_peak_memory_bytes", "max_scheduler_cost_ns",
)


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _require_digest(value: str, *, name: str) -> None:
    if not isinstance(value, str) or len(value) != _DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def _nonnegative(value: int, *, name: str, positive: bool = False) -> None:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be a {qualifier} integer")


def _integer_mapping(value: Mapping[str, int], *, name: str, allow_empty: bool = False) -> Mapping[str, int]:
    parsed = dict(value)
    if (not allow_empty and not parsed) or any(not isinstance(key, str) or not key or type(item) is not int or item < 0 for key, item in parsed.items()):
        raise ValueError(f"{name} must be a mapping of names to nonnegative integers")
    return MappingProxyType(dict(sorted(parsed.items())))


def _measurement_value(profile: ProfileMeasurement, field: str) -> int | None:
    fact = getattr(profile.runtime, field)
    if fact.value is None:
        return None
    if type(fact.value) is not int or fact.value < 0:
        raise ValueError(f"profile {field} must be an observed nonnegative integer")
    return fact.value


@dataclass(frozen=True, slots=True)
class OperationalEvidenceV1:
    """One verified pre-outcome clean/profile pair and its retained costs."""

    campaign_spec_digest: str
    campaign_plan_digest: str
    shard_receipt_sha256: str
    merge_receipt_sha256: str
    replay_receipt_sha256: str
    profile_receipt_sha256: str
    verified_shard: bool
    verified_merge: bool
    verified_replay: bool
    replay_link: ReplayLink
    profile: ProfileMeasurement
    clean_semantics: Mapping[str, object]
    profiled_semantics: Mapping[str, object]
    path_class: Literal["fast", "slow"]
    event_count: int
    ledger_bytes: int
    sidecar_bytes: int
    replay_wall_time_ns: int
    scheduler_launch_overhead_ns: int
    shard_fixed_cost_ns: int
    allocation: Mapping[str, int]

    def __post_init__(self) -> None:
        for name in (
            "campaign_spec_digest", "campaign_plan_digest", "shard_receipt_sha256", "merge_receipt_sha256",
            "replay_receipt_sha256", "profile_receipt_sha256",
        ):
            _require_digest(getattr(self, name), name=name)
        if not all(type(item) is bool and item for item in (self.verified_shard, self.verified_merge, self.verified_replay)):
            raise ValueError("operational evidence requires verified shard, merge, and replay receipts")
        if not isinstance(self.replay_link, ReplayLink) or not isinstance(self.profile, ProfileMeasurement):
            raise ValueError("operational evidence requires typed replay and profile facts")
        if self.path_class not in {"fast", "slow"}:
            raise ValueError("representative evidence path class must be fast or slow")
        if not self.replay_link.cohort.population_estimate_eligible:
            raise ValueError("representative evidence must be selected before outcome")
        agreement = compare_semantics(self.clean_semantics, self.profiled_semantics)
        if not agreement.agrees or not self.replay_link.semantic_agreement.agrees:
            raise ValueError("semantic disagreement cannot enter an operational projection")
        if agreement != self.replay_link.semantic_agreement:
            raise ValueError("replay semantic agreement does not bind supplied semantics")
        if self.profile.level != "representative" or not self.profile.enabled:
            raise ValueError("operational evidence requires an enabled representative profile")
        if any(part in key.lower() for key in self.profile.raw_context for part in _FORBIDDEN_CONTEXT_PARTS):
            raise ValueError("profile raw context contains a secret-bearing field")
        for name in (
            "event_count", "ledger_bytes", "sidecar_bytes", "replay_wall_time_ns",
            "scheduler_launch_overhead_ns", "shard_fixed_cost_ns",
        ):
            _nonnegative(getattr(self, name), name=name, positive=name == "replay_wall_time_ns")
        object.__setattr__(self, "allocation", _integer_mapping(self.allocation, name="allocation"))


@dataclass(frozen=True, slots=True)
class RepresentativeProfileAggregateV1:
    """Aggregate measurements with explicit sample counts and missingness."""

    campaign_spec_digest: str
    campaign_plan_digest: str
    merge_receipt_sha256: str
    shard_receipt_sha256s: tuple[str, ...]
    replay_receipt_sha256s: tuple[str, ...]
    profile_receipt_sha256s: tuple[str, ...]
    sample_count: int
    fast_path_samples: int
    slow_path_samples: int
    event_count: int
    decoder_wall_time_ns: int
    decoder_cpu_time_ns: int
    replay_wall_time_ns: int
    ledger_bytes: int
    sidecar_bytes: int
    scheduler_launch_overhead_ns: int
    shard_fixed_cost_ns: int
    peak_host_memory_bytes: int | None
    missing_measurements: tuple[str, ...]
    evidence_sha256: str

    @property
    def memory_available(self) -> bool:
        return self.peak_host_memory_bytes is not None

    @property
    def decoder_shots_per_second(self) -> float:
        return self.sample_count * 1_000_000_000 / self.decoder_wall_time_ns

    @property
    def replay_shots_per_second(self) -> float:
        return self.sample_count * 1_000_000_000 / self.replay_wall_time_ns

    def as_evidence(self) -> dict[str, object]:
        return {field.name: getattr(self, field.name) for field in fields(self)} | {
            "memory_available": self.memory_available,
            "decoder_shots_per_second": self.decoder_shots_per_second,
            "replay_shots_per_second": self.replay_shots_per_second,
        }


def aggregate_representative_evidence(records: tuple[OperationalEvidenceV1, ...]) -> RepresentativeProfileAggregateV1:
    """Aggregate only verified, paired samples covering both eligible path strata."""
    if not isinstance(records, tuple) or not records:
        raise ValueError("representative evidence requires a nonempty immutable tuple")
    if any(not isinstance(record, OperationalEvidenceV1) for record in records):
        raise ValueError("representative evidence records must be typed")
    first = records[0]
    if any(
        (record.campaign_spec_digest, record.campaign_plan_digest, record.merge_receipt_sha256)
        != (first.campaign_spec_digest, first.campaign_plan_digest, first.merge_receipt_sha256)
        for record in records
    ):
        raise ValueError("representative evidence must bind one verified campaign and merge receipt")
    samples = {record.replay_link.sample_identity for record in records}
    paths = {record.path_class for record in records}
    if len(samples) < 2 or paths != {"fast", "slow"}:
        raise ValueError("representative evidence requires multiple physical samples and fast/slow eligible paths")
    decoder_wall = [_measurement_value(record.profile, "wall_time") for record in records]
    decoder_cpu = [_measurement_value(record.profile, "process_cpu_time") for record in records]
    missing = set()
    if any(value is None for value in decoder_wall):
        missing.add("decoder_wall_time")
    if any(value is None for value in decoder_cpu):
        missing.add("decoder_cpu_time")
    peak_memory = [_measurement_value(record.profile, "peak_host_memory") for record in records]
    if any(value is None for value in peak_memory):
        missing.add("peak_host_memory")
    if missing - {"peak_host_memory"}:
        raise ValueError("required throughput measurement is unavailable")
    assert all(value is not None for value in decoder_wall + decoder_cpu)
    payload = {
        "records": [
            {
                "shard": record.shard_receipt_sha256, "replay": record.replay_receipt_sha256,
                "profile": record.profile_receipt_sha256, "sample": record.replay_link.sample_identity,
            }
            for record in records
        ]
    }
    return RepresentativeProfileAggregateV1(
        campaign_spec_digest=first.campaign_spec_digest,
        campaign_plan_digest=first.campaign_plan_digest,
        merge_receipt_sha256=first.merge_receipt_sha256,
        shard_receipt_sha256s=tuple(sorted({record.shard_receipt_sha256 for record in records})),
        replay_receipt_sha256s=tuple(sorted({record.replay_receipt_sha256 for record in records})),
        profile_receipt_sha256s=tuple(sorted({record.profile_receipt_sha256 for record in records})),
        sample_count=len(records), fast_path_samples=sum(record.path_class == "fast" for record in records),
        slow_path_samples=sum(record.path_class == "slow" for record in records),
        event_count=sum(record.event_count for record in records),
        decoder_wall_time_ns=sum(decoder_wall), decoder_cpu_time_ns=sum(decoder_cpu),
        replay_wall_time_ns=sum(record.replay_wall_time_ns for record in records),
        ledger_bytes=sum(record.ledger_bytes for record in records), sidecar_bytes=sum(record.sidecar_bytes for record in records),
        scheduler_launch_overhead_ns=max(record.scheduler_launch_overhead_ns for record in records),
        shard_fixed_cost_ns=max(record.shard_fixed_cost_ns for record in records),
        peak_host_memory_bytes=None if any(value is None for value in peak_memory) else max(peak_memory),
        missing_measurements=tuple(sorted(missing)), evidence_sha256=_digest(payload),
    )


@dataclass(frozen=True, slots=True)
class SafetyFactorV1:
    """Frozen rational safety margin, avoiding unbounded floating arithmetic."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        _nonnegative(self.numerator, name="safety numerator", positive=True)
        _nonnegative(self.denominator, name="safety denominator", positive=True)
        if self.numerator < self.denominator:
            raise ValueError("safety factor cannot be below one")

    def apply(self, value: int) -> int:
        _nonnegative(value, name="projected value")
        return ceil(value * self.numerator / self.denominator)

    def as_evidence(self) -> dict[str, int]:
        return {"numerator": self.numerator, "denominator": self.denominator}


@dataclass(frozen=True, slots=True)
class SiteCapabilityV1:
    """Declared site ceilings; omitted facts deliberately produce a denial."""

    site_capability_sha256: str
    max_cpu_time_ns: int | None
    max_wall_time_ns: int | None
    max_storage_bytes: int | None
    max_shard_bytes: int | None
    max_replay_time_ns: int | None
    max_peak_memory_bytes: int | None
    max_scheduler_cost_ns: int | None

    def __post_init__(self) -> None:
        _require_digest(self.site_capability_sha256, name="site_capability_sha256")
        for name in _CEILING_FIELDS:
            value = getattr(self, name)
            if value is not None:
                _nonnegative(value, name=name, positive=True)

    def as_evidence(self) -> dict[str, object]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class ProposedCampaignV1:
    """Scientific caps plus separate executor allocation observations."""

    campaign_spec_digest: str
    campaign_plan_digest: str
    total_shots: int
    max_shard_shots: int
    scientific_caps: Mapping[str, int]
    operational_allocation: Mapping[str, int]

    def __post_init__(self) -> None:
        _require_digest(self.campaign_spec_digest, name="campaign_spec_digest")
        _require_digest(self.campaign_plan_digest, name="campaign_plan_digest")
        _nonnegative(self.total_shots, name="total_shots", positive=True)
        _nonnegative(self.max_shard_shots, name="max_shard_shots", positive=True)
        if self.max_shard_shots > self.total_shots:
            raise ValueError("maximum shard shots cannot exceed total shots")
        object.__setattr__(self, "scientific_caps", _integer_mapping(self.scientific_caps, name="scientific_caps"))
        object.__setattr__(self, "operational_allocation", _integer_mapping(self.operational_allocation, name="operational_allocation"))


def scientific_authorization_identity(proposal: ProposedCampaignV1) -> str:
    """Hash only scientific inputs; changing worker topology cannot change it."""
    if not isinstance(proposal, ProposedCampaignV1):
        raise ValueError("scientific identity requires a typed campaign proposal")
    return _digest({
        "campaign_spec_digest": proposal.campaign_spec_digest,
        "campaign_plan_digest": proposal.campaign_plan_digest,
        "total_shots": proposal.total_shots,
        "max_shard_shots": proposal.max_shard_shots,
        "scientific_caps": dict(proposal.scientific_caps),
    })


@dataclass(frozen=True, slots=True)
class AuthorizationReceiptV1:
    """Digest-bound authorization outcome and every reason supporting it."""

    decision: Literal["allow", "deny"]
    reasons: tuple[str, ...]
    scientific_identity: str
    operational_allocation: Mapping[str, int]
    campaign_spec_digest: str
    campaign_plan_digest: str
    gate_evidence_sha256: str
    merge_receipt_sha256: str
    shard_receipt_sha256s: tuple[str, ...]
    replay_receipt_sha256s: tuple[str, ...]
    profile_receipt_sha256s: tuple[str, ...]
    site_capability_sha256: str
    safety_factor: SafetyFactorV1
    projections: Mapping[str, int | None]
    receipt_sha256: str

    def as_evidence(self) -> dict[str, object]:
        return {
            "decision": self.decision, "reasons": list(self.reasons), "scientific_identity": self.scientific_identity,
            "operational_allocation": dict(self.operational_allocation), "campaign_spec_digest": self.campaign_spec_digest,
            "campaign_plan_digest": self.campaign_plan_digest, "gate_evidence_sha256": self.gate_evidence_sha256,
            "merge_receipt_sha256": self.merge_receipt_sha256, "site_capability_sha256": self.site_capability_sha256,
            "shard_receipt_sha256s": list(self.shard_receipt_sha256s),
            "replay_receipt_sha256s": list(self.replay_receipt_sha256s),
            "profile_receipt_sha256s": list(self.profile_receipt_sha256s),
            "safety_factor": self.safety_factor.as_evidence(), "projections": dict(self.projections),
            "receipt_sha256": self.receipt_sha256,
        }


def _per_sample(total: int, count: int) -> int:
    return ceil(total / count)


def authorize_campaign(*, aggregate: RepresentativeProfileAggregateV1, proposal: ProposedCampaignV1,
                       site: SiteCapabilityV1, safety_factor: SafetyFactorV1) -> AuthorizationReceiptV1:
    """Project a proposal from measured facts and deny if any required fact is absent."""
    if not all(isinstance(item, expected) for item, expected in (
        (aggregate, RepresentativeProfileAggregateV1), (proposal, ProposedCampaignV1),
        (site, SiteCapabilityV1), (safety_factor, SafetyFactorV1),
    )):
        raise ValueError("authorization requires typed aggregate, proposal, site, and safety factor")
    if (aggregate.campaign_spec_digest, aggregate.campaign_plan_digest) != (proposal.campaign_spec_digest, proposal.campaign_plan_digest):
        raise ValueError("proposal identity does not match profiling evidence")
    projections: dict[str, int | None] = {
        "max_cpu_time_ns": safety_factor.apply(_per_sample(aggregate.decoder_cpu_time_ns, aggregate.sample_count) * proposal.total_shots),
        "max_wall_time_ns": safety_factor.apply(_per_sample(aggregate.decoder_wall_time_ns, aggregate.sample_count) * proposal.total_shots),
        "max_storage_bytes": safety_factor.apply(_per_sample(aggregate.ledger_bytes + aggregate.sidecar_bytes, aggregate.sample_count) * proposal.total_shots),
        "max_shard_bytes": safety_factor.apply(_per_sample(aggregate.ledger_bytes + aggregate.sidecar_bytes, aggregate.sample_count) * proposal.max_shard_shots),
        "max_replay_time_ns": safety_factor.apply(_per_sample(aggregate.replay_wall_time_ns, aggregate.sample_count) * proposal.total_shots),
        "max_peak_memory_bytes": None if aggregate.peak_host_memory_bytes is None else safety_factor.apply(aggregate.peak_host_memory_bytes),
        "max_scheduler_cost_ns": safety_factor.apply((aggregate.scheduler_launch_overhead_ns + aggregate.shard_fixed_cost_ns) * ceil(proposal.total_shots / proposal.max_shard_shots)),
    }
    reasons = [f"missing_measurement:{item}" for item in aggregate.missing_measurements]
    for field in _CEILING_FIELDS:
        ceiling = getattr(site, field)
        projection = projections[field]
        if ceiling is None:
            reasons.append(f"missing_site_ceiling:{field}")
        elif projection is None:
            reasons.append(f"missing_projection:{field}")
        elif projection > ceiling:
            reasons.append(f"ceiling_exceeded:{field}")
    reasons = sorted(set(reasons))
    preimage = {
        "decision": "allow" if not reasons else "deny", "reasons": reasons,
        "scientific_identity": scientific_authorization_identity(proposal),
        "operational_allocation": dict(proposal.operational_allocation),
        "campaign_spec_digest": proposal.campaign_spec_digest, "campaign_plan_digest": proposal.campaign_plan_digest,
        "gate_evidence_sha256": aggregate.evidence_sha256, "merge_receipt_sha256": aggregate.merge_receipt_sha256,
        "shard_receipt_sha256s": aggregate.shard_receipt_sha256s,
        "replay_receipt_sha256s": aggregate.replay_receipt_sha256s,
        "profile_receipt_sha256s": aggregate.profile_receipt_sha256s,
        "site_capability_sha256": site.site_capability_sha256, "safety_factor": safety_factor.as_evidence(),
        "projections": projections,
    }
    return AuthorizationReceiptV1(
        decision=preimage["decision"], reasons=tuple(reasons), scientific_identity=preimage["scientific_identity"],
        operational_allocation=proposal.operational_allocation, campaign_spec_digest=proposal.campaign_spec_digest,
        campaign_plan_digest=proposal.campaign_plan_digest, gate_evidence_sha256=aggregate.evidence_sha256,
        merge_receipt_sha256=aggregate.merge_receipt_sha256, site_capability_sha256=site.site_capability_sha256,
        shard_receipt_sha256s=aggregate.shard_receipt_sha256s,
        replay_receipt_sha256s=aggregate.replay_receipt_sha256s,
        profile_receipt_sha256s=aggregate.profile_receipt_sha256s,
        safety_factor=safety_factor, projections=MappingProxyType(projections), receipt_sha256=_digest(preimage),
    )
