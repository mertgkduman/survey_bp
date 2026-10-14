"""Measured, fail-closed authorization for bounded campaign execution.

The gate records operational observations without treating them as decoder
semantics.  It accepts only verified, pre-outcome representative clean/profile
pairs and denies an authorization whenever evidence or site ceilings are absent.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Literal, Mapping

from bp_registry.canonical.profiling import ProfileMeasurement, ReplayLink, compare_semantics
from bp_registry.campaigns.contracts import CampaignAssessmentV1


_DIGEST_LENGTH = 64
_MAX_COUNT = (1 << 63) - 1
_FORBIDDEN_CONTEXT_PARTS = ("secret", "token", "password", "authorization", "cookie", "api_key")
_CEILING_FIELDS = (
    "max_cpu_time_ns", "max_wall_time_ns", "max_storage_bytes", "max_shard_bytes",
    "max_replay_time_ns", "max_peak_memory_bytes", "max_scheduler_cost_ns",
)


@dataclass(frozen=True, slots=True)
class Phase11DispatchProposalV1:
    """A review package that can describe a production request but never authorize it.

    The ordinary Phase 8 site and authorization types remain the source of
    capability semantics.  This wrapper adds Phase 11's two-code calibration,
    source-route, and precision receipts while hard-coding the separation
    between package preparation and the Plan 11-11 human decision.
    """

    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        receipt = self.payload.get("receipt")
        if not isinstance(receipt, Mapping) or receipt.get("decision") != "deny" or receipt.get("dispatch_token") is not None:
            raise ValueError("Phase 11 proposal must retain a default-deny receipt without a dispatch token")

    def as_evidence(self) -> dict[str, object]:
        return dict(self.payload)


@dataclass(frozen=True, slots=True)
class Phase11AuthorizationReceiptV1:
    """One sealed, digest-bound human decision about a Phase 11 package."""

    decision: Literal["allow", "deny"]
    reviewer: str
    reason: str
    recorded_at: str
    reviewed_package_sha256: str
    confirmed_ceilings_sha256: str
    account: str | None
    partition: str | None
    approved_manifest_sha256s: tuple[str, ...]
    denied_campaign_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    receipt_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.reviewer, str) or not self.reviewer.strip():
            raise ValueError("authorization reviewer must be a nonempty string")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("authorization reason must be a nonempty string")
        if not isinstance(self.recorded_at, str):
            raise ValueError("authorization recorded_at must be an ISO timestamp")
        try:
            datetime.fromisoformat(self.recorded_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("authorization recorded_at must be an ISO timestamp") from error
        for name in ("reviewed_package_sha256", "confirmed_ceilings_sha256", "receipt_sha256"):
            _require_digest(getattr(self, name), name=name)
        if any(value is not None and (not isinstance(value, str) or not value) for value in (self.account, self.partition)):
            raise ValueError("authorization account and partition must be explicit strings or unavailable")
        if (not self.denied_campaign_ids or any(not isinstance(item, str) or not item for item in self.denied_campaign_ids)
                or len(set(self.denied_campaign_ids)) != len(self.denied_campaign_ids)):
            raise ValueError("authorization denied campaign ids must be a unique nonempty set")
        if any(not isinstance(item, str) or not item for item in self.reasons):
            raise ValueError("authorization reasons must be nonempty strings")
        for digest in self.approved_manifest_sha256s:
            _require_digest(digest, name="approved manifest digest")

    def as_evidence(self) -> dict[str, object]:
        payload = {
            "schema": "phase11_authorization_receipt_v1", "decision": self.decision,
            "reviewer": self.reviewer, "reason": self.reason, "recorded_at": self.recorded_at,
            "reviewed_package_sha256": self.reviewed_package_sha256,
            "confirmed_ceilings_sha256": self.confirmed_ceilings_sha256,
            "account": self.account, "partition": self.partition,
            "approved_manifest_sha256s": list(self.approved_manifest_sha256s),
            "denied_campaign_ids": list(self.denied_campaign_ids), "reasons": list(self.reasons),
            "dispatch_token": None,
        }
        return {**payload, "receipt_sha256": self.receipt_sha256}


def _phase11_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve(strict=True)
    if root not in (path, *path.parents) or path.is_symlink() or not path.is_file():
        raise ValueError("Phase 11 package references a regular file beneath the project root")
    return path


def build_phase11_dispatch_package(root: Path) -> dict[str, object]:
    """Build the deterministic two-code package for the blocking human gate.

    It records present calibration and mathematical precision facts while
    making missing scheduler ceilings, allocation accounting, quota/cost, and
    source eligibility explicit.  No installed scheduler client can change the
    receipt because client discovery is not capacity evidence.
    """
    root = root.resolve(strict=True)
    from .controlled_execution import preflight_phase11_controlled_design
    from .sizing import calibrate_paired_sweep_design

    calibration_rows: list[dict[str, object]] = []
    for code_id, relative in (
        ("GB46", "data/studies/phase11-gb46-joint-separate.json"),
        ("BB72", "data/studies/phase11-bb72-joint-separate.json"),
    ):
        manifest = _phase11_path(root, relative)
        raw = manifest.read_bytes()
        preflight = preflight_phase11_controlled_design(root=root, design_path=manifest)
        if preflight["code_id"] != code_id:
            raise ValueError("Phase 11 calibration manifest code identity differs from its proposal row")
        calibration_rows.append({
            "code_id": code_id, "manifest_path": relative, "manifest_sha256": sha256(raw).hexdigest(),
            "code_artifact_sha256": preflight["code_artifact_sha256"],
            "code_provenance_sha256": preflight.get("code_provenance_sha256"),
            "bounded_evidence_status": "qualified_public_calibration_lifecycle",
            "runtime_work_status": "typed_native_units_and_wall_boundary_required_for_dispatch",
        })
    design_path = _phase11_path(root, "data/studies/phase11-fixed-marginal-design.json")
    design = json.loads(design_path.read_bytes())
    sizing = calibrate_paired_sweep_design(
        design_path=str(design_path), pilot_evidence_identity=design["sizing"]["pilot_evidence_identity"],
    )
    reasons = [
        "missing_site_ceiling:max_cpu_time_ns", "missing_site_ceiling:max_wall_time_ns",
        "missing_site_ceiling:max_storage_bytes", "missing_site_ceiling:max_shard_bytes",
        "missing_site_ceiling:max_replay_time_ns", "missing_site_ceiling:max_peak_memory_bytes",
        "missing_site_ceiling:max_scheduler_cost_ns", "missing_accounting_partition_evidence",
        "missing_quota_or_cost_evidence", "source_route_ineligible", "missing_persisted_calibration_profile",
    ]
    payload: dict[str, object] = {
        "schema": "phase11_dispatch_proposal_v1", "proposal_id": "phase11-two-code-production-v1",
        "calibrations": calibration_rows,
        "requested_campaigns": [
            {"campaign_id": "gb46-controlled", "lane": "controlled", "code_id": "GB46", "pairs_per_point": sizing.proposed_pairs_per_point, "source_eligible": False},
            {"campaign_id": "bb72-controlled", "lane": "controlled", "code_id": "BB72", "pairs_per_point": sizing.proposed_pairs_per_point, "source_eligible": False},
            {"campaign_id": "gb46-source", "lane": "source", "code_id": "GB46", "pairs_per_point": None, "source_eligible": False},
            {"campaign_id": "bb72-source", "lane": "source", "code_id": "BB72", "pairs_per_point": None, "source_eligible": False},
        ],
        "precision_feasibility": {"status": sizing.paired_sizing.status, "required_pairs_per_point": sizing.proposed_pairs_per_point,
                                  "cap_pairs_per_point": sizing.capped_pairs_per_point, "receipt_sha256": sizing.receipt_sha256},
        "site_capability": {"installed_slurm_clients": False, **{field: None for field in _CEILING_FIELDS}},
        "accounting_partition": {"status": "unavailable", "account": None, "partition": None},
        "quota_cost": {"status": "unavailable", "allocation": None, "cost_estimate": None},
        "forecast": {"status": "blocked_no_persisted_profile", "predicted_memory_bytes": None,
                     "predicted_wall_time_ns": None, "predicted_typed_work": None},
        "receipt": {"decision": "deny", "dispatch_token": None, "reasons": reasons,
                    "authorization_contract": "AuthorizationReceiptV1 decision literal retained; Plan 11-11 human gate required for allow"},
    }
    payload["package_sha256"] = _digest({key: value for key, value in payload.items() if key != "package_sha256"})
    return Phase11DispatchProposalV1(payload).as_evidence()


def _phase11_receipt_preimage(receipt: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in receipt.items() if key != "receipt_sha256"}


def _validate_phase11_authorization_receipt(expected: Mapping[str, object], receipt: Mapping[str, object]) -> None:
    """Validate a sealed decision against the immutable package it reviewed."""
    if receipt.get("schema") != "phase11_authorization_receipt_v1":
        raise ValueError("Phase 11 authorization receipt schema is invalid")
    decision = receipt.get("decision")
    if decision not in {"allow", "deny"} or receipt.get("dispatch_token") is not None:
        raise ValueError("Phase 11 authorization receipt cannot contain a dispatch token")
    candidate = Phase11AuthorizationReceiptV1(
        decision=decision, reviewer=receipt.get("reviewer"), reason=receipt.get("reason"),
        recorded_at=receipt.get("recorded_at"), reviewed_package_sha256=receipt.get("reviewed_package_sha256"),
        confirmed_ceilings_sha256=receipt.get("confirmed_ceilings_sha256"), account=receipt.get("account"),
        partition=receipt.get("partition"), approved_manifest_sha256s=tuple(receipt.get("approved_manifest_sha256s", ())),
        denied_campaign_ids=tuple(receipt.get("denied_campaign_ids", ())), reasons=tuple(receipt.get("reasons", ())),
        receipt_sha256=receipt.get("receipt_sha256"),
    )
    if candidate.reviewed_package_sha256 != expected["package_sha256"]:
        raise ValueError("Phase 11 authorization receipt reviewed package digest is stale")
    if candidate.confirmed_ceilings_sha256 != _digest(expected["site_capability"]):
        raise ValueError("Phase 11 authorization receipt ceiling digest is stale")
    if candidate.receipt_sha256 != _digest(_phase11_receipt_preimage(receipt)):
        raise ValueError("Phase 11 authorization receipt digest differs from its sealed evidence")
    campaign_ids = {campaign["campaign_id"] for campaign in expected["requested_campaigns"]}
    if set(candidate.denied_campaign_ids) - campaign_ids:
        raise ValueError("Phase 11 authorization receipt names an unknown campaign")
    manifests = {row["manifest_sha256"] for row in expected["calibrations"]}
    if set(candidate.approved_manifest_sha256s) - manifests:
        raise ValueError("Phase 11 authorization receipt names an unknown manifest")
    eligible = _phase11_eligible_manifest_digests(expected)
    if candidate.decision == "allow":
        if not candidate.approved_manifest_sha256s or set(candidate.approved_manifest_sha256s) - eligible:
            raise ValueError("Phase 11 authorization receipt cannot allow an ineligible manifest")
        accounting = expected["accounting_partition"]
        if (not isinstance(accounting, Mapping) or candidate.account != accounting.get("account")
                or candidate.partition != accounting.get("partition")):
            raise ValueError("Phase 11 authorization receipt account or partition differs from reviewed evidence")
        manifest_for_code = {row["code_id"]: row["manifest_sha256"] for row in expected["calibrations"]}
        expected_denied = {
            campaign["campaign_id"] for campaign in expected["requested_campaigns"]
            if manifest_for_code[campaign["code_id"]] not in candidate.approved_manifest_sha256s
        }
        if set(candidate.denied_campaign_ids) != expected_denied:
            raise ValueError("Phase 11 authorization receipt denies an incorrect campaign set")
    elif set(candidate.denied_campaign_ids) != campaign_ids or candidate.approved_manifest_sha256s:
        raise ValueError("Phase 11 denial must retain every campaign and no approved manifest")


def validate_phase11_dispatch_package(root: Path, package: Mapping[str, object]) -> None:
    """Reject stale packages and validate either default or sealed deny evidence."""
    if not isinstance(package, Mapping):
        raise ValueError("Phase 11 dispatch package must be a mapping")
    expected = build_phase11_dispatch_package(root)
    if package == expected:
        return
    receipt = package.get("receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("Phase 11 dispatch receipt must be a mapping")
    baseline = dict(package)
    baseline["receipt"] = expected["receipt"]
    if baseline != expected:
        raise ValueError("Phase 11 dispatch package differs from its frozen evidence")
    if receipt.get("schema") != "phase11_authorization_receipt_v1":
        if receipt.get("decision") != "deny" or receipt.get("dispatch_token") is not None:
            raise ValueError("Phase 11 dispatch receipt must remain deny without a dispatch token")
        raise ValueError("Phase 11 dispatch package has an unsealed authorization receipt")
    _validate_phase11_authorization_receipt(expected, receipt)


def _phase11_receipt_reasons(package: Mapping[str, object]) -> list[str]:
    default = package["receipt"]
    if not isinstance(default, Mapping):
        raise ValueError("Phase 11 package has no default receipt")
    reasons = default.get("reasons")
    if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
        raise ValueError("Phase 11 package has invalid default denial reasons")
    return list(reasons)


def _phase11_eligible_manifest_digests(package: Mapping[str, object]) -> set[str]:
    """Return the manifest allowlist only when every linked gate is present."""
    site = package.get("site_capability")
    accounting = package.get("accounting_partition")
    quota = package.get("quota_cost")
    forecast = package.get("forecast")
    precision = package.get("precision_feasibility")
    calibrations = package.get("calibrations")
    requested = package.get("requested_campaigns")
    if not all(isinstance(value, Mapping) for value in (site, accounting, quota, forecast, precision)):
        return set()
    if not isinstance(calibrations, list) or not isinstance(requested, list):
        return set()
    if (precision.get("status") != "powered" or accounting.get("status") != "available"
            or quota.get("status") != "available" or forecast.get("status") != "available"):
        return set()
    if (not isinstance(accounting.get("account"), str) or not accounting["account"]
            or not isinstance(accounting.get("partition"), str) or not accounting["partition"]):
        return set()
    if any(type(site.get(field)) is not int or site[field] <= 0 for field in _CEILING_FIELDS):
        return set()
    if any(type(forecast.get(field)) is not int or forecast[field] < 0 for field in (
        "predicted_memory_bytes", "predicted_wall_time_ns", "predicted_typed_work",
    )):
        return set()
    if quota.get("allocation") is None or quota.get("cost_estimate") is None:
        return set()
    rows = {
        row.get("code_id"): row.get("manifest_sha256") for row in calibrations
        if isinstance(row, Mapping) and isinstance(row.get("code_id"), str) and isinstance(row.get("manifest_sha256"), str)
    }
    if len(rows) != len(calibrations):
        return set()
    eligible_codes = {
        campaign.get("code_id") for campaign in requested
        if isinstance(campaign, Mapping) and campaign.get("source_eligible") is True
    }
    if {campaign.get("code_id") for campaign in requested if isinstance(campaign, Mapping)} != eligible_codes:
        return set()
    return {rows[code_id] for code_id in eligible_codes if code_id in rows}


def materialize_phase11_authorization_receipt(
    root: Path, package_path: Path, *, decision: str, reviewer: str | None, reason: str | None,
    reviewed_package_sha256: str | None, confirmed_ceilings_sha256: str | None,
    account: str | None, partition: str | None, approved_manifest_sha256s: tuple[str, ...],
) -> dict[str, object]:
    """Seal a reviewed decision and atomically replace only the authorization package.

    The current package is revalidated before use.  If it is stale or malformed,
    the known default-deny package replaces it with an explicit failed-input reason.
    This makes an interrupted or invalid resume fail closed without dispatching work.
    """
    root = root.resolve(strict=True)
    package_path = package_path.resolve()
    if package_path.is_symlink() or not package_path.is_file():
        raise ValueError("authorization package must be a regular file")
    expected = build_phase11_dispatch_package(root)
    input_reasons: list[str] = []
    try:
        current = json.loads(package_path.read_bytes())
        validate_phase11_dispatch_package(root, current)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        input_reasons.append(f"authorization_input_unverified:{type(error).__name__}")
    package = dict(expected)
    reasons = _phase11_receipt_reasons(expected) + input_reasons
    requested_manifests = tuple(approved_manifest_sha256s)
    if decision not in {"authorize_exact_manifests", "preserve_deny"}:
        reasons.append("authorization_request_invalid_decision")
    if not isinstance(reviewer, str) or not reviewer.strip():
        reasons.append("authorization_request_missing_reviewer")
        reviewer = "unattributed"
    if not isinstance(reason, str) or not reason.strip():
        reasons.append("authorization_request_missing_reason")
        reason = "No reviewer reason was supplied; authorization remains denied."
    if reviewed_package_sha256 != expected["package_sha256"]:
        reasons.append("authorization_request_stale_package_digest")
    ceiling_digest = _digest(expected["site_capability"])
    if confirmed_ceilings_sha256 is not None and confirmed_ceilings_sha256 != ceiling_digest:
        reasons.append("authorization_request_stale_ceiling_digest")
    known_manifests = {row["manifest_sha256"] for row in expected["calibrations"]}
    if len(set(requested_manifests)) != len(requested_manifests):
        reasons.append("authorization_request_duplicate_manifest")
    if set(requested_manifests) - known_manifests:
        reasons.append("authorization_request_unknown_manifest")
    if decision == "authorize_exact_manifests":
        if not requested_manifests:
            reasons.append("authorization_request_empty_allowlist")
        if confirmed_ceilings_sha256 is None:
            reasons.append("authorization_request_missing_ceiling_digest")
    if decision == "preserve_deny":
        requested_manifests = ()
    site_accounting = expected["accounting_partition"]
    if not isinstance(site_accounting, Mapping):
        raise ValueError("Phase 11 package has invalid accounting evidence")
    eligible_manifests = _phase11_eligible_manifest_digests(expected)
    if decision == "authorize_exact_manifests" and set(requested_manifests) - eligible_manifests:
        reasons.append("authorization_request_ineligible_manifest")
    if decision == "authorize_exact_manifests" and (
        account != site_accounting.get("account") or partition != site_accounting.get("partition")
    ):
        reasons.append("authorization_request_accounting_mismatch")
    allow = (
        decision == "authorize_exact_manifests" and bool(requested_manifests)
        and not reasons and set(requested_manifests) <= eligible_manifests
    )
    manifest_for_code = {row["code_id"]: row["manifest_sha256"] for row in expected["calibrations"]}
    denied_campaign_ids = sorted(
        campaign["campaign_id"] for campaign in expected["requested_campaigns"]
        if not allow or manifest_for_code[campaign["code_id"]] not in requested_manifests
    )
    receipt_payload: dict[str, object] = {
        "schema": "phase11_authorization_receipt_v1", "decision": "allow" if allow else "deny", "reviewer": reviewer,
        "reason": reason, "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reviewed_package_sha256": expected["package_sha256"], "confirmed_ceilings_sha256": ceiling_digest,
        "account": site_accounting.get("account"), "partition": site_accounting.get("partition"),
        "approved_manifest_sha256s": sorted(requested_manifests) if allow else [],
        "denied_campaign_ids": denied_campaign_ids,
        "reasons": sorted(set(reasons)) if reasons else ["human_reviewed_exact_manifest_allow"], "dispatch_token": None,
    }
    receipt_payload["receipt_sha256"] = _digest(_phase11_receipt_preimage(receipt_payload))
    sealed = Phase11AuthorizationReceiptV1(
        decision=receipt_payload["decision"], reviewer=receipt_payload["reviewer"], reason=receipt_payload["reason"],
        recorded_at=receipt_payload["recorded_at"], reviewed_package_sha256=receipt_payload["reviewed_package_sha256"],
        confirmed_ceilings_sha256=receipt_payload["confirmed_ceilings_sha256"], account=receipt_payload["account"],
        partition=receipt_payload["partition"], approved_manifest_sha256s=tuple(receipt_payload["approved_manifest_sha256s"]),
        denied_campaign_ids=tuple(receipt_payload["denied_campaign_ids"]), reasons=tuple(receipt_payload["reasons"]),
        receipt_sha256=receipt_payload["receipt_sha256"],
    )
    package["receipt"] = sealed.as_evidence()
    _write_phase11_package_atomic(package_path, package)
    reloaded = json.loads(package_path.read_bytes())
    validate_phase11_dispatch_package(root, reloaded)
    return reloaded


def _write_phase11_package_atomic(path: Path, package: Mapping[str, object]) -> None:
    """Publish one fully-written receipt package without exposing partial JSON."""
    payload = json.dumps(package, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".phase11-authorization-", delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _require_digest(value: str, *, name: str) -> None:
    if not isinstance(value, str) or len(value) != _DIGEST_LENGTH or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def _nonnegative(value: int, *, name: str, positive: bool = False) -> None:
    if type(value) is not int or value < (1 if positive else 0) or value > _MAX_COUNT:
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be a bounded {qualifier} integer")


def _sum_bounded(values: tuple[int, ...] | list[int], *, name: str) -> int:
    total = 0
    for value in values:
        _nonnegative(value, name=name)
        if value > _MAX_COUNT - total:
            raise ValueError(f"{name} exceeds bounded arithmetic")
        total += value
    return total


def _multiply_bounded(left: int, right: int, *, name: str) -> int:
    _nonnegative(left, name=name)
    _nonnegative(right, name=name)
    if left and right > _MAX_COUNT // left:
        raise ValueError(f"{name} exceeds bounded arithmetic")
    return left * right


def _integer_mapping(value: Mapping[str, int], *, name: str, allow_empty: bool = False) -> Mapping[str, int]:
    parsed = dict(value)
    if (not allow_empty and not parsed) or any(not isinstance(key, str) or not key or type(item) is not int or item < 0 for key, item in parsed.items()):
        raise ValueError(f"{name} must be a mapping of names to nonnegative integers")
    return MappingProxyType(dict(sorted(parsed.items())))


def _measurement_value(profile: ProfileMeasurement, field: str) -> int | None:
    fact = getattr(profile.runtime, field)
    if fact.value is None:
        return None
    if type(fact.value) is not int or fact.value < 0 or fact.value > _MAX_COUNT:
        raise ValueError(f"profile {field} must be an observed nonnegative integer")
    return fact.value


@dataclass(frozen=True, slots=True)
class OperationalEvidenceV1:
    """One verified pre-outcome clean/profile pair and its retained costs."""

    campaign_spec_digest: str
    campaign_plan_digest: str
    assessment_digest: str
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
            "campaign_spec_digest", "campaign_plan_digest", "assessment_digest",
            "shard_receipt_sha256", "merge_receipt_sha256",
            "replay_receipt_sha256", "profile_receipt_sha256",
        ):
            _require_digest(getattr(self, name), name=name)
        if not all(type(item) is bool and item for item in (self.verified_shard, self.verified_merge, self.verified_replay)):
            raise ValueError("operational evidence requires verified shard, merge, and replay receipts")
        if not isinstance(self.replay_link, ReplayLink) or not isinstance(self.profile, ProfileMeasurement):
            raise ValueError("operational evidence requires typed replay and profile facts")
        if self.path_class not in {"fast", "slow"}:
            raise ValueError("representative evidence path class must be fast or slow")
        if self.replay_link.cohort.stratum != self.path_class:
            raise ValueError("representative path class differs from prespecified cohort stratum")
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
    assessment_digest: str
    merge_receipt_sha256: str
    shard_receipt_sha256s: tuple[str, ...]
    replay_receipt_sha256s: tuple[str, ...]
    profile_receipt_sha256s: tuple[str, ...]
    sample_count: int
    fast_path_samples: int
    slow_path_samples: int
    inclusion_probability: float
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

    @property
    def decoder_ns_per_event(self) -> float | None:
        return None if self.event_count == 0 else self.decoder_wall_time_ns / self.event_count

    @property
    def ledger_bytes_per_event(self) -> float | None:
        return None if self.event_count == 0 else self.ledger_bytes / self.event_count

    @property
    def sidecar_bytes_per_event(self) -> float | None:
        return None if self.event_count == 0 else self.sidecar_bytes / self.event_count

    def as_evidence(self) -> dict[str, object]:
        return {field.name: getattr(self, field.name) for field in fields(self)} | {
            "memory_available": self.memory_available,
            "decoder_shots_per_second": self.decoder_shots_per_second,
            "replay_shots_per_second": self.replay_shots_per_second,
            "decoder_ns_per_event": self.decoder_ns_per_event,
            "ledger_bytes_per_event": self.ledger_bytes_per_event,
            "sidecar_bytes_per_event": self.sidecar_bytes_per_event,
        }


def aggregate_representative_evidence(records: tuple[OperationalEvidenceV1, ...]) -> RepresentativeProfileAggregateV1:
    """Aggregate only verified, paired samples covering both eligible path strata."""
    if not isinstance(records, tuple) or not records:
        raise ValueError("representative evidence requires a nonempty immutable tuple")
    if any(not isinstance(record, OperationalEvidenceV1) for record in records):
        raise ValueError("representative evidence records must be typed")
    first = records[0]
    if any(
        (record.campaign_spec_digest, record.campaign_plan_digest, record.assessment_digest, record.merge_receipt_sha256)
        != (first.campaign_spec_digest, first.campaign_plan_digest, first.assessment_digest, first.merge_receipt_sha256)
        for record in records
    ):
        raise ValueError("representative evidence must bind one verified campaign and merge receipt")
    samples = {record.replay_link.sample_identity for record in records}
    paths = {record.path_class for record in records}
    if len(samples) < 2 or paths != {"fast", "slow"}:
        raise ValueError("representative evidence requires multiple physical samples and fast/slow eligible paths")
    if len(samples) != len(records):
        raise ValueError("representative evidence cannot count one physical sample more than once")
    receipt_tuples = {
        (record.shard_receipt_sha256, record.replay_receipt_sha256, record.profile_receipt_sha256)
        for record in records
    }
    if len(receipt_tuples) != len(records):
        raise ValueError("representative evidence contains duplicate receipt tuples")
    probabilities = {record.replay_link.cohort.inclusion_probability for record in records}
    if len(probabilities) != 1:
        raise ValueError("representative projection requires one common inclusion probability")
    inclusion_probability = probabilities.pop()
    assert isinstance(inclusion_probability, float)
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
        "campaign_spec_digest": first.campaign_spec_digest,
        "campaign_plan_digest": first.campaign_plan_digest,
        "assessment_digest": first.assessment_digest,
        "merge_receipt_sha256": first.merge_receipt_sha256,
        "records": [
            {
                "shard": record.shard_receipt_sha256, "replay": record.replay_receipt_sha256,
                "profile": record.profile_receipt_sha256, "sample": record.replay_link.sample_identity,
                "path_class": record.path_class,
                "inclusion_probability": record.replay_link.cohort.inclusion_probability,
            }
            for record in records
        ]
    }
    total_events = _sum_bounded([record.event_count for record in records], name="event_count")
    if total_events == 0:
        missing.add("event_count")
    return RepresentativeProfileAggregateV1(
        campaign_spec_digest=first.campaign_spec_digest,
        campaign_plan_digest=first.campaign_plan_digest,
        assessment_digest=first.assessment_digest,
        merge_receipt_sha256=first.merge_receipt_sha256,
        shard_receipt_sha256s=tuple(sorted({record.shard_receipt_sha256 for record in records})),
        replay_receipt_sha256s=tuple(sorted({record.replay_receipt_sha256 for record in records})),
        profile_receipt_sha256s=tuple(sorted({record.profile_receipt_sha256 for record in records})),
        sample_count=len(records), fast_path_samples=sum(record.path_class == "fast" for record in records),
        slow_path_samples=sum(record.path_class == "slow" for record in records),
        inclusion_probability=inclusion_probability,
        event_count=total_events,
        decoder_wall_time_ns=_sum_bounded(decoder_wall, name="decoder_wall_time_ns"),
        decoder_cpu_time_ns=_sum_bounded(decoder_cpu, name="decoder_cpu_time_ns"),
        replay_wall_time_ns=_sum_bounded([record.replay_wall_time_ns for record in records], name="replay_wall_time_ns"),
        ledger_bytes=_sum_bounded([record.ledger_bytes for record in records], name="ledger_bytes"),
        sidecar_bytes=_sum_bounded([record.sidecar_bytes for record in records], name="sidecar_bytes"),
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
        projected = (value * self.numerator + self.denominator - 1) // self.denominator
        if projected > _MAX_COUNT:
            raise ValueError("projected value exceeds bounded arithmetic")
        return projected

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
    assessment: CampaignAssessmentV1
    operational_allocation: Mapping[str, int]

    @property
    def scientific_caps(self) -> Mapping[str, int]:
        return MappingProxyType(self.assessment.resources.model_dump(mode="python"))

    def __post_init__(self) -> None:
        _require_digest(self.campaign_spec_digest, name="campaign_spec_digest")
        _require_digest(self.campaign_plan_digest, name="campaign_plan_digest")
        _nonnegative(self.total_shots, name="total_shots", positive=True)
        _nonnegative(self.max_shard_shots, name="max_shard_shots", positive=True)
        if self.max_shard_shots > self.total_shots:
            raise ValueError("maximum shard shots cannot exceed total shots")
        if not isinstance(self.assessment, CampaignAssessmentV1):
            raise ValueError("proposal requires a frozen typed campaign assessment")
        if self.total_shots > self.assessment.resources.max_shots:
            raise ValueError("requested shots exceed assessment scientific cap")
        if self.max_shard_shots > self.assessment.resources.max_batch_size:
            raise ValueError("requested shard shots exceed assessment batch cap")
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
        "assessment_digest": proposal.assessment.digest(),
        "scientific_caps": dict(proposal.scientific_caps),
    })


@dataclass(frozen=True, slots=True)
class AuthorizationReceiptV1:
    """Digest-bound authorization outcome and every reason supporting it."""

    decision: Literal["allow", "deny"]
    reasons: tuple[str, ...]
    scientific_identity: str
    assessment_digest: str
    scientific_caps: Mapping[str, int]
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
            "assessment_digest": self.assessment_digest, "scientific_caps": dict(self.scientific_caps),
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
    _nonnegative(total, name="sample total")
    _nonnegative(count, name="sample count", positive=True)
    return (total + count - 1) // count


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
    if aggregate.assessment_digest != proposal.assessment.digest():
        raise ValueError("proposal assessment does not match frozen profiling evidence")
    bytes_per_sample = _per_sample(_sum_bounded([aggregate.ledger_bytes, aggregate.sidecar_bytes], name="storage bytes"), aggregate.sample_count)
    scheduler_unit_cost = _sum_bounded([aggregate.scheduler_launch_overhead_ns, aggregate.shard_fixed_cost_ns], name="scheduler cost")
    projections: dict[str, int | None] = {
        "max_cpu_time_ns": safety_factor.apply(_multiply_bounded(_per_sample(aggregate.decoder_cpu_time_ns, aggregate.sample_count), proposal.total_shots, name="cpu projection")),
        "max_wall_time_ns": safety_factor.apply(_multiply_bounded(_per_sample(aggregate.decoder_wall_time_ns, aggregate.sample_count), proposal.total_shots, name="wall projection")),
        "max_storage_bytes": safety_factor.apply(_multiply_bounded(bytes_per_sample, proposal.total_shots, name="storage projection")),
        "max_shard_bytes": safety_factor.apply(_multiply_bounded(bytes_per_sample, proposal.max_shard_shots, name="shard storage projection")),
        "max_replay_time_ns": safety_factor.apply(_multiply_bounded(_per_sample(aggregate.replay_wall_time_ns, aggregate.sample_count), proposal.total_shots, name="replay projection")),
        "max_peak_memory_bytes": None if aggregate.peak_host_memory_bytes is None else safety_factor.apply(aggregate.peak_host_memory_bytes),
        "max_scheduler_cost_ns": safety_factor.apply(_multiply_bounded(scheduler_unit_cost, _per_sample(proposal.total_shots, proposal.max_shard_shots), name="scheduler projection")),
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
        "assessment_digest": proposal.assessment.digest(), "scientific_caps": dict(proposal.scientific_caps),
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
        assessment_digest=proposal.assessment.digest(), scientific_caps=proposal.scientific_caps,
        operational_allocation=proposal.operational_allocation, campaign_spec_digest=proposal.campaign_spec_digest,
        campaign_plan_digest=proposal.campaign_plan_digest, gate_evidence_sha256=aggregate.evidence_sha256,
        merge_receipt_sha256=aggregate.merge_receipt_sha256, site_capability_sha256=site.site_capability_sha256,
        shard_receipt_sha256s=aggregate.shard_receipt_sha256s,
        replay_receipt_sha256s=aggregate.replay_receipt_sha256s,
        profile_receipt_sha256s=aggregate.profile_receipt_sha256s,
        safety_factor=safety_factor, projections=MappingProxyType(projections), receipt_sha256=_digest(preimage),
    )
