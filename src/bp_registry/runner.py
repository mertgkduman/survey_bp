"""One-shot source-linked tracer for the project CSS smoke fixture."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Literal, Mapping

from .ledger import canonical_serializer_descriptor, CanonicalResourceInterruption, Writer, read_canonical_events
from .canonical.metrics import unavailable_metric
from .canonical.budgets import WorkVector
from .canonical.execution import run_canonical_structural_shot
from .canonical.verification import PublicShotContext
from .canonical.numerics import MIN_SUM_CPU_F64, REFERENCE_CPU_F64
from .canonical.schedules import EdgeTable
from .canonical.contracts import validate_composition
from .manifests import (
    CanonicalExperimentV2,
    CanonicalExperimentV3,
    CanonicalExperimentV4,
    CanonicalExperimentV5,
    CanonicalExperimentV6,
    CanonicalExperimentV7,
    CanonicalExperimentV8,
    ManifestV1,
    QuaternaryExperimentV1,
    QuaternaryExperimentV2,
    executable_canonical_policy_effects,
    manifest_digest,
    preflight,
    preflight_manifest_bytes,
    validate_executable_canonical_baseline,
)
from . import evaluator, sampling
from .quaternary.execution import TracerPauliProblem, _css_from_public_problem, run_quaternary_asced, run_quaternary_mbp4, run_quaternary_qbpgd, run_quaternary_scalar, run_quaternary_tracer, verify_quaternary_tracer
from .quaternary.compatibility import resolve_quaternary_composition


def _native_reference():
    """Load the optional native adapter only for explicit native execution."""
    from . import reference

    return reference


def __getattr__(name: str):
    """Retain lazy compatibility for callers using runner.reference."""
    if name == "reference":
        return _native_reference()
    raise AttributeError(name)


@dataclass(frozen=True)
class ShotResult:
    run_id: str
    shot_id: int
    outcome: str
    converged: bool
    iterations: int


def _unavailable_native_metric_facts(stage: str) -> list[dict[str, int | float | str | None]]:
    """Retain missing native instrumentation after an unsuccessful terminal."""
    reason = f"native instrumentation unavailable because {stage} raised before a native result was retained"
    return [
        unavailable_metric(
            metric, method="runner.run_one", scope="native_decoder_call", unit=unit,
            qualification="terminal_not_observed", reason=reason,
        ).as_evidence()
        for metric, unit in (
            ("native_iterations", "native_iterations"),
            ("native_edge_updates", "edge_messages"),
            ("native_control_flow_events", "events"),
        )
    ]


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SELECTED_PROVENANCE = _REPOSITORY_ROOT / "data/artifacts/selected-css.provenance.json"

# Versioned hard ceilings for guarded canonical artifact and interruption
# writes. These are protocol limits, not claims about natural payload maxima.
CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1 = 262_144
CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1 = 32_768


@dataclass(frozen=True, slots=True)
class CanonicalRuntimeAuthorizationV1:
    """Prospective hard limits for exactly one canonical unit.

    Scientific evidence and storage limits exclude the one-time control
    reserve.  This prevents a partial execution from spending the bytes needed
    to make its interruption durable.
    """

    profile_digest: str
    authorization_identity: str
    mode: Literal["strict_full_unit", "interruptible_unit"]
    max_events: int
    max_evidence_bytes: int
    max_storage_bytes: int
    control_receipt_reserve_bytes: int
    monotonic_deadline_ns: int | None = None
    max_event_bytes: int | None = None
    max_artifact_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"strict_full_unit", "interruptible_unit"}:
            raise ValueError("runtime authorization mode is not registered")
        if (not isinstance(self.profile_digest, str) or len(self.profile_digest) != 64
                or not isinstance(self.authorization_identity, str) or not self.authorization_identity):
            raise ValueError("runtime authorization requires stable digest and identity")
        if any(type(value) is not int or value < 1 for value in (
            self.max_events, self.max_evidence_bytes, self.max_storage_bytes,
            self.control_receipt_reserve_bytes,
        )):
            raise ValueError("runtime authorization limits must be positive integers")
        if self.monotonic_deadline_ns is not None and (type(self.monotonic_deadline_ns) is not int or self.monotonic_deadline_ns < 0):
            raise ValueError("monotonic deadline must be a nonnegative integer or absent")
        if any(value is not None and (type(value) is not int or value < 1) for value in (
            self.max_event_bytes, self.max_artifact_bytes,
        )):
            raise ValueError("guarded payload ceilings must be positive integers or absent")

    @classmethod
    def strict_full_unit(cls, *, derived_events: int, derived_evidence_bytes: int,
                         derived_storage_bytes: int, **kwargs: object) -> "CanonicalRuntimeAuthorizationV1":
        authorization = cls(mode="strict_full_unit", **kwargs)  # type: ignore[arg-type]
        reserve = authorization.control_receipt_reserve_bytes
        if (authorization.max_events < derived_events
                or authorization.max_evidence_bytes < derived_evidence_bytes - reserve
                or authorization.max_storage_bytes < derived_storage_bytes - reserve):
            raise ValueError("strict_full_unit authorization must fit every derived maximum")
        return authorization

    @classmethod
    def interruptible_unit(cls, **kwargs: object) -> "CanonicalRuntimeAuthorizationV1":
        return cls(mode="interruptible_unit", **kwargs)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class CanonicalRuntimeSnapshotV1:
    profile_digest: str
    authorization_identity: str
    scientific_events: int
    scientific_evidence_bytes: int
    scientific_storage_bytes: int
    control_receipt_bytes: int
    interruption_kind: str | None
    boundary: str | None
    attempted_bytes: int | None
    deadline_ns: int | None
    before_ns: int | None
    after_ns: int | None
    overshoot_ns: int | None
    committed_work: WorkVector
    last_work_leaf_id: str | None


@dataclass(frozen=True, slots=True)
class _RuntimeReservation:
    kind: Literal["ledger", "artifact", "control"]
    events: int
    evidence_bytes: int
    storage_bytes: int
    control_bytes: int


class CanonicalRuntimeGuardV1:
    """Mutable one-unit guard with pre-mutation reservations and a permanent latch."""

    def __init__(self, authorization: CanonicalRuntimeAuthorizationV1, *, clock_ns: Callable[[], int] = time.monotonic_ns) -> None:
        self.authorization = authorization
        self._clock_ns = clock_ns
        self._events = self._evidence = self._storage = self._control = 0
        self._latched = False
        self._interruption_kind: str | None = None
        self._boundary: str | None = None
        self._attempted_bytes: int | None = None
        self._before_ns: int | None = None
        self._after_ns: int | None = None
        self._pending_before: dict[str, int] = {}
        self._pending_reservations: dict[int, _RuntimeReservation] = {}
        self._committed_work = WorkVector.zero()
        self._last_work_leaf_id: str | None = None

    def snapshot(self) -> CanonicalRuntimeSnapshotV1:
        deadline = self.authorization.monotonic_deadline_ns
        return CanonicalRuntimeSnapshotV1(
            self.authorization.profile_digest, self.authorization.authorization_identity,
            self._events, self._evidence, self._storage, self._control,
            self._interruption_kind, self._boundary, self._attempted_bytes,
            deadline, self._before_ns, self._after_ns,
            None if deadline is None or self._after_ns is None else max(0, self._after_ns - deadline),
            self._committed_work, self._last_work_leaf_id,
        )

    @property
    def interrupted(self) -> bool:
        return self._latched

    def _interrupt(self, kind: str, *, boundary: str, attempted_bytes: int | None = None,
                   before_ns: int | None = None, after_ns: int | None = None) -> None:
        if not self._latched:
            self._latched = True
            self._interruption_kind = kind
            self._boundary = boundary
            self._attempted_bytes = attempted_bytes
            self._before_ns = before_ns
            self._after_ns = after_ns
        raise CanonicalResourceInterruption("canonical resource cap denied mutation", snapshot=self.snapshot())

    def _scientific_reservation(self, *, kind: Literal["ledger", "artifact"], events: int,
                                evidence: int, storage: int, boundary: str) -> _RuntimeReservation:
        if self._latched:
            self._interrupt("already_interrupted", boundary=boundary)
        pending_events = sum(item.events for item in self._pending_reservations.values())
        pending_evidence = sum(item.evidence_bytes for item in self._pending_reservations.values())
        pending_storage = sum(item.storage_bytes for item in self._pending_reservations.values())
        if self._events + pending_events + events > self.authorization.max_events:
            self._interrupt("events", boundary=boundary, attempted_bytes=events)
        if self._evidence + pending_evidence + evidence > self.authorization.max_evidence_bytes:
            self._interrupt("evidence_bytes", boundary=boundary, attempted_bytes=evidence)
        if self._storage + pending_storage + storage > self.authorization.max_storage_bytes:
            self._interrupt("storage_bytes", boundary=boundary, attempted_bytes=storage)
        return _RuntimeReservation(kind, events, evidence, storage, 0)

    def reserve_ledger_append(self, payload: bytes, *, boundary: str) -> _RuntimeReservation:
        if not isinstance(payload, bytes) or not payload.endswith(b"\n"):
            raise ValueError("ledger reservation requires exact framed bytes")
        if self.authorization.max_event_bytes is not None and len(payload) > self.authorization.max_event_bytes:
            self._interrupt("unsupported_event_payload", boundary=boundary, attempted_bytes=len(payload))
        reservation = self._scientific_reservation(kind="ledger", events=1, evidence=len(payload), storage=len(payload), boundary=boundary)
        self._pending_reservations[id(reservation)] = reservation
        return reservation

    def reserve_artifact_write(self, byte_count: int, *, boundary: str) -> _RuntimeReservation:
        if type(byte_count) is not int or byte_count < 0:
            raise ValueError("artifact reservation requires a nonnegative exact byte count")
        if self.authorization.max_artifact_bytes is not None and byte_count > self.authorization.max_artifact_bytes:
            self._interrupt("unsupported_artifact_payload", boundary=boundary, attempted_bytes=byte_count)
        reservation = self._scientific_reservation(kind="artifact", events=0, evidence=0, storage=byte_count, boundary=boundary)
        self._pending_reservations[id(reservation)] = reservation
        return reservation

    def reserve_control_receipt(self, byte_count: int) -> _RuntimeReservation:
        if type(byte_count) is not int or byte_count < 1:
            raise ValueError("control receipt requires a positive exact byte count")
        if not self._latched:
            raise CanonicalResourceInterruption("control receipt is available only after interruption", snapshot=self.snapshot())
        if (self._control or any(item.kind == "control" for item in self._pending_reservations.values())
                or byte_count > self.authorization.control_receipt_reserve_bytes):
            raise CanonicalResourceInterruption("control receipt reserve is single use", snapshot=self.snapshot())
        reservation = _RuntimeReservation("control", 0, 0, 0, byte_count)
        self._pending_reservations[id(reservation)] = reservation
        return reservation

    def commit(self, reservation: object) -> None:
        if (not isinstance(reservation, _RuntimeReservation)
                or self._pending_reservations.pop(id(reservation), None) is not reservation):
            raise TypeError("unknown canonical runtime reservation")
        self._events += reservation.events
        self._evidence += reservation.evidence_bytes
        self._storage += reservation.storage_bytes
        self._control += reservation.control_bytes

    def release(self, reservation: object) -> None:
        if (not isinstance(reservation, _RuntimeReservation)
                or self._pending_reservations.pop(id(reservation), None) is not reservation):
            raise TypeError("unknown canonical runtime reservation")
        # Reservations are only committed after durable I/O succeeds; release
        # therefore intentionally leaves accounting unchanged.

    def before_work(self, boundary: str) -> None:
        if self._latched:
            self._interrupt("already_interrupted", boundary=boundary)
        now = self._clock_ns()
        deadline = self.authorization.monotonic_deadline_ns
        if deadline is not None and now >= deadline:
            self._interrupt("wall_deadline", boundary=boundary, before_ns=now, after_ns=now)
        self._pending_before[boundary] = now

    def record_work(self, committed_work: WorkVector, *, leaf_id: str) -> None:
        """Retain the producer's committed total before an interruption can latch."""
        if self._latched:
            self._interrupt("already_interrupted", boundary=leaf_id)
        if not isinstance(committed_work, WorkVector):
            raise TypeError("committed canonical work requires a WorkVector")
        if not isinstance(leaf_id, str) or not leaf_id:
            raise ValueError("committed canonical work requires a leaf identity")
        before = self._committed_work.as_evidence(structural_event_version=4)
        after = committed_work.as_evidence(structural_event_version=4)
        if any(after[name] < count for name, count in before.items()):
            raise ValueError("committed canonical work cannot decrease")
        self._committed_work = committed_work
        self._last_work_leaf_id = leaf_id

    def after_work(self, boundary: str, *, committed_work: WorkVector | None = None,
                   leaf_id: str | None = None) -> None:
        if self._latched:
            self._interrupt("already_interrupted", boundary=boundary)
        if committed_work is not None:
            self.record_work(committed_work, leaf_id=leaf_id or boundary)
        now = self._clock_ns()
        deadline = self.authorization.monotonic_deadline_ns
        before = self._pending_before.pop(boundary, now)
        if deadline is not None and now >= deadline:
            self._interrupt("wall_deadline", boundary=boundary, before_ns=before, after_ns=now)


def _canonical_digest(domain: str, value: object) -> str:
    return sha256(domain.encode("ascii") + b"\0" + json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CanonicalExecutableMaximaV1:
    """Independent one-unit maximum derived from a closed public route registry."""

    derivation_version: Literal["v1"]
    route: str
    manifest_dimensions_sha256: str
    policy_binding_sha256: str
    serializer_sha256: str
    artifact_layout_sha256: str
    verifier_sha256: str
    max_decoder_iterations: int
    work_per_iteration: int
    max_ledger_events_per_unit: int
    serializer_bytes_per_event: int
    artifact_storage_bytes_per_unit: int
    partial_receipt_reserve_bytes: int
    derived_work_per_unit: int
    derived_events_per_unit: int
    derived_evidence_bytes_per_unit: int
    derived_storage_bytes_per_unit: int

    def as_evidence(self) -> dict[str, object]:
        # This is intentionally the exact Plan 09-16
        # FailureCountExecutableLimitReceiptV1 declaration surface.  ``route``
        # is retained as engine-local explanatory metadata, not a campaign
        # receipt field; admitting it here would make a valid Plan 09-16
        # declaration fail the required exact-field check.
        return {
            "derivation_version": self.derivation_version,
            "manifest_dimensions_sha256": self.manifest_dimensions_sha256,
            "policy_binding_sha256": self.policy_binding_sha256,
            "serializer_sha256": self.serializer_sha256, "artifact_layout_sha256": self.artifact_layout_sha256,
            "verifier_sha256": self.verifier_sha256, "max_decoder_iterations": self.max_decoder_iterations,
            "work_per_iteration": self.work_per_iteration, "max_ledger_events_per_unit": self.max_ledger_events_per_unit,
            "serializer_bytes_per_event": self.serializer_bytes_per_event,
            "artifact_storage_bytes_per_unit": self.artifact_storage_bytes_per_unit,
            "partial_receipt_reserve_bytes": self.partial_receipt_reserve_bytes,
            "derived_work_per_unit": self.derived_work_per_unit, "derived_events_per_unit": self.derived_events_per_unit,
            "derived_evidence_bytes_per_unit": self.derived_evidence_bytes_per_unit,
            "derived_storage_bytes_per_unit": self.derived_storage_bytes_per_unit,
        }

    @property
    def digest(self) -> str:
        return _canonical_digest("bp-registry-canonical-executable-maxima-v1", self.as_evidence())


_REGISTERED_LOCAL_SCHEDULES = frozenset({
    "layered", "check_node_serial", "variable_node_serial", "residual",
    "randomized", "group_shuffled",
})


def _registered_canonical_route(manifest: object) -> tuple[str, int]:
    """Resolve a route only when its executable emission grammar is known.

    This is intentionally a closed registry.  In particular, Phase 7's
    optional postprocessor and the controlled fair-Beam controller have no
    registered guarded structural grammar yet, so they cannot inherit a
    baseline profile by accident.
    """
    if isinstance(manifest, CanonicalExperimentV8):
        raise ValueError("unregistered canonical manifest route")
    if isinstance(manifest, CanonicalExperimentV7):
        return ("v7-vote" if manifest.vote is not None else "v7-list", 6)
    if isinstance(manifest, CanonicalExperimentV6):
        return f"phase5:{manifest.intervention.kind}", 5
    if isinstance(manifest, CanonicalExperimentV5):
        return f"phase5:{manifest.intervention.kind}", 5
    if isinstance(manifest, CanonicalExperimentV4) and manifest.relay is not None:
        return "relay", 4
    if isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4)):
        schedule = manifest.policies.schedule.kind
        if schedule == "flooding":
            return "baseline", 2
        if schedule in _REGISTERED_LOCAL_SCHEDULES:
            return f"local:{schedule}", 3
    raise ValueError("unregistered canonical manifest route")


def _checked_product(left: int, right: int, *, name: str) -> int:
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        raise ValueError(f"{name} requires nonnegative integer factors")
    result = left * right
    if result > (2**63 - 1):
        raise ValueError(f"{name} exceeds the executable counter range")
    return result


def _route_dimensions(manifest: object, table: EdgeTable, route: str) -> tuple[int, int, dict[str, int]]:
    """Return named route quantities from validated manifest and code facts."""
    core_sweep_work = 2 * table.edge_count + table.variable_count + table.check_count
    iterations = getattr(manifest, "budgets").attempt.max_iterations
    if route.startswith("local:"):
        # Normal completion is the largest mutually reachable branch.  A
        # numerical-failure branch adds ``missingness`` but omits candidate and
        # selection, so it has two fewer events.
        return iterations, core_sweep_work, {
            "shot_begin": 1, "attempt": 1, "runtime": 1, "candidate": 1,
            "selection": 1, "trace_link": 1, "work": 1, "termination": 1,
        }
    if route == "baseline":
        return iterations, core_sweep_work, {
            "shot_begin": 1, "attempt": 1, "runtime": 1, "candidate": 1,
            "selection": 1, "trace_link": 1, "work": 1, "termination": 1,
        }
    if route == "relay":
        legs = manifest.relay.total_leg_limit
        return _checked_product(iterations, legs, name="relay iteration units"), core_sweep_work, {
            "shot_begin": 1, "attempt": 1, "relay_transfer": max(0, legs - 1),
            "work": 1, "candidate": 1, "selection": 1, "termination": 1,
        }
    if route.startswith("phase5:"):
        kind = route.removeprefix("phase5:")
        spec = manifest.intervention
        attempts = {
            "identity": iterations,
            "guided_decimation": spec.round_limit,
            "impulse": spec.attempt_cap,
            "freezing": spec.retry_cap,
            "syndrome_flip": spec.test_cap,
            "sign_flip": 1,
        }.get(kind)
        if kind == "restart_belief":
            attempts = _checked_product(spec.eta, spec.t_cap, name="restart attempts")
        if attempts is None:
            raise ValueError(f"unregistered Phase 5 intervention route {kind!r}")
        # `_run_phase5_structural_shot` emits one header intervention, then
        # transform/attempt/lift and at most one original-check per projected
        # controller attempt.  Only Restart exposes branch rows, bounded by
        # eta; all other controllers expose no branch row.
        branches = spec.eta if kind == "restart_belief" else 0
        named = {
            "shot_begin": 1, "intervention": 1, "branch": branches,
            "transform": attempts, "attempt": attempts, "lift": attempts,
            # ``phase5_attempt_events`` emits an original_check for every
            # valid projected attempt; a selected candidate emits one final
            # original-space check as well.
            "original_check": attempts + 1,
            "candidate": 1, "selection": 1,
            "work": 1, "evaluation": 1, "runtime": 1, "termination": 1,
        }
        return _checked_product(iterations, manifest.intervention_limits.max_total_attempts,
                                name="phase5 iteration units"), core_sweep_work, named
    if route in {"v7-list", "v7-vote"}:
        members = len(manifest.ensemble.bases)
        local_steps = min(_checked_product(iterations, table.check_count, name="MBBP local steps"),
                          manifest.ensemble.max_member_c2v_updates)
        work_leaves = _checked_product(members, local_steps + 1, name="MBBP work leaves")
        if route == "v7-vote":
            # A ballot contains every coordinate, hence there is one ballot
            # event per admitted member, rather than one event per bit.
            return _checked_product(iterations, members, name="MBBP iteration units"), core_sweep_work, {
                "shot_begin": 1, "basis": members, "member": members,
                # ``phase6_events`` emits an exclusion for every member
                # that is not admitted before the electorate/ballot branch.
                "vote_exclusion": members, "vote_electorate": 1,
                "vote_ballot": members, "vote_aggregate": 1,
                "vote_validation": 1,
                "work_leaf": work_leaves, "evaluation": 1, "termination": 1,
            }
        return _checked_product(iterations, members, name="MBBP iteration units"), core_sweep_work, {
            "shot_begin": 1, "basis": members, "member": members,
            "candidate_origin": members, "duplicate_group": members,
            "selection": 1, "original_check": 1, "work_leaf": work_leaves,
            "evaluation": 1, "termination": 1,
        }
    raise ValueError(f"unregistered canonical route {route!r}")


def _profile_event_template(*, ledger_version: int, route: str, manifest: object, table: EdgeTable) -> dict[str, object]:
    """Return the guarded serializer rule instead of inventing event payloads.

    Canonical event payload schemas intentionally remain open.  Profiles bind a
    versioned hard framed-byte ceiling that the guarded writer enforces after
    exact serialization and before mutation; it is not a measured natural
    maximum.  Route and structural version remain digest inputs so a later
    grammar change cannot reuse this authorization silently.
    """
    del manifest, table
    serializer = canonical_serializer_descriptor(structural_event_version=ledger_version)
    ceiling = serializer.get("guarded_event_ceiling")
    if not isinstance(ceiling, dict) or type(ceiling.get("max_framed_bytes")) is not int:
        raise ValueError("canonical serializer lacks a versioned guarded event ceiling")
    return {"route": route, "ledger_version": ledger_version, **ceiling}


def _artifact_layout_bytes(manifest: object, table: EdgeTable) -> tuple[int, dict[str, object]]:
    """Derive declared non-ledger artifact ceilings for one guarded unit.

    The two regular artifacts (materialized sample and engine result) are each
    capped by the runtime guard.  A selected trace sidecar is a third bounded
    artifact.  Plan 09-17 owns passing its concrete artifact writes through
    that guard; profiles reject a trace configuration above the frozen
    per-artifact ceiling until that route has a distinct registered rule.
    """
    del table
    trace = getattr(manifest, "trace_plan", None)
    trace_bytes = 0
    if trace is not None and getattr(trace, "level", "off") != "off":
        trace_bytes = getattr(trace, "max_bytes", None)
        if type(trace_bytes) is not int or trace_bytes < 0:
            raise ValueError("canonical trace plan lacks a bounded byte ceiling")
    if trace_bytes > CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1:
        raise ValueError("canonical trace plan exceeds the registered guarded artifact ceiling")
    layout: dict[str, object] = {
        "schema": "canonical-nonledger-artifact-ceilings-v1",
        "sample_bytes": CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        "result_bytes": CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        "trace_sidecar_bytes": trace_bytes,
        "per_artifact_ceiling_bytes": CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        "enforcement": "runtime_guard.reserve_artifact_write.exact_bytes",
        "campaign_integration": "plan-09-17",
    }
    return (
        _checked_product(2, CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1, name="regular artifact ceilings")
        + trace_bytes,
        layout,
    )


def _neutral_interruption_reserve(manifest: object) -> int:
    """Return the frozen caller-control receipt reserve, independent of a run."""
    del manifest
    return CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1


def _interruption_control_descriptor() -> dict[str, object]:
    """Describe the dedicated interruption receipt budget bound into profiles."""
    return {
        "schema": "canonical-interruption-control-receipt-ceiling-v1",
        "max_bytes": CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1,
        "enforcement": "runtime_guard.reserve_control_receipt.exact_bytes",
        "campaign_validation": "plan-09-17",
    }

def derive_canonical_executable_maxima(context: "CanonicalPublicManifestContext") -> CanonicalExecutableMaximaV1:
    """Derive a conservative, digest-bound maximum without campaign declarations.

    This public boundary consumes only a preflight context.  Unsupported
    compact schemas and policy routes fail before sampling or ledger creation.
    """
    if not isinstance(context, CanonicalPublicManifestContext):
        raise TypeError("executable maxima require a validated public manifest context")
    manifest = context.manifest
    route, ledger_version = _registered_canonical_route(manifest)
    code = context.code
    table = EdgeTable.from_check_matrix(code.hz)
    iterations, work_per_iteration, event_inventory = _route_dimensions(manifest, table, route)
    events = sum(event_inventory.values())
    serializer = canonical_serializer_descriptor(structural_event_version=ledger_version)
    ceiling = _profile_event_template(
        ledger_version=ledger_version, route=route, manifest=manifest, table=table,
    )
    serializer_bytes = ceiling["max_framed_bytes"]
    assert type(serializer_bytes) is int
    control_reserve = _neutral_interruption_reserve(manifest)
    control_descriptor = _interruption_control_descriptor()
    artifact_bytes, artifact_layout = _artifact_layout_bytes(manifest, table)
    evidence = _checked_product(events, serializer_bytes, name="derived evidence") + control_reserve
    storage = artifact_bytes + evidence
    if evidence > 2**63 - 1 or storage > 2**63 - 1:
        raise ValueError("derived canonical byte maxima exceed the executable counter range")
    dimensions = {"manifest_sha256": context.manifest_sha256, "schema": manifest.schema_version, "route": route,
                  "n": code.n, "checks": table.check_count, "edges": table.edge_count,
                  "iterations": iterations, "event_inventory": event_inventory, "trace": context.trace_plan}
    return CanonicalExecutableMaximaV1(
        "v1", route, _canonical_digest("canonical-manifest-dimensions-v1", dimensions),
        _canonical_digest("canonical-policy-binding-v1", {"identity": context.composition_identity, "effects": context.policy_effects}),
        _canonical_digest("canonical-serializer-v1", {"descriptor": serializer, "route_ceiling": ceiling}),
        _canonical_digest("canonical-artifact-layout-v1", artifact_layout),
        _canonical_digest("canonical-verifier-v1", {"public_context": "v1", "route": route,
                                                      "inventory": event_inventory,
                                                      "control_receipt": control_descriptor}),
        iterations, work_per_iteration, events, serializer_bytes, artifact_bytes, control_reserve,
        _checked_product(iterations, work_per_iteration, name="derived decoder work"), events, evidence, storage,
    )


def verify_declared_executable_limits(
    declared: Mapping[str, object], *, expected_policy_binding: str, derived: CanonicalExecutableMaximaV1,
) -> None:
    """Reject any declaration which differs from the independently derived profile."""
    if not isinstance(declared, Mapping):
        raise TypeError("declared executable limits must be a mapping")
    expected = derived.as_evidence()
    if expected_policy_binding != derived.policy_binding_sha256:
        raise ValueError("policy_binding_sha256 differs from the expected binding")
    if set(declared) != set(expected):
        raise ValueError("declared executable limits have extra or missing fields")
    for key, value in expected.items():
        if declared[key] != value:
            raise ValueError(f"declared executable limit mismatch: {key}")


def guarded_atomic_write_bytes(
    path: str | Path, payload: bytes, *, resource_guard: CanonicalRuntimeGuardV1,
    boundary: str, control_receipt: bool = False,
) -> None:
    """Replace one caller-owned artifact only after an exact-byte reservation.

    The temporary sibling preserves the repository's atomic-write discipline;
    failed replacement releases the uncommitted reservation and cannot charge
    bytes that never became durable evidence.
    """
    if not isinstance(payload, bytes):
        raise TypeError("guarded artifact payload must be bytes")
    reservation = (resource_guard.reserve_control_receipt(len(payload)) if control_receipt
                   else resource_guard.reserve_artifact_write(len(payload), boundary=boundary))
    target = Path(path)
    temporary = target.with_name(f".{target.name}.canonical-guard.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except BaseException:
        resource_guard.release(reservation)
        if temporary.exists():
            temporary.unlink()
        raise
    resource_guard.commit(reservation)


def preflight_pilot(manifest_path: str | Path) -> dict[str, Any]:
    """Resolve the one Phase 1 selected-artifact pilot before native execution."""

    manifest = preflight(manifest_path).manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("selected artifact pilot requires a complete ManifestV1")
    provenance = json.loads(_SELECTED_PROVENANCE.read_text(encoding="utf-8"))
    artifact = provenance["artifact"]
    source = provenance["source"]
    expected_path = _REPOSITORY_ROOT / artifact["path"]
    actual_path = (Path(manifest.artifact.root) / manifest.artifact.path).resolve()
    if (
        manifest.run_id != "gross-bb144-pilot"
        or manifest.artifact.code_id != provenance["code_id"]
        or actual_path != expected_path.resolve()
        or manifest.artifact.raw_sha256 != artifact["raw_sha256"]
        or manifest.artifact.semantic_sha256 != artifact["semantic_sha256"]
        or manifest.paper.uri != "https://arxiv.org/html/2606.18240v1"
        or manifest.paper.revision != "v1"
        or manifest.implementation.repository_uri != source["repository"]
        or manifest.implementation.revision != source["revision"]
        or manifest.implementation.source_path != source["source_file"]
        or manifest.implementation.source_artifact_sha256 != source["source_file_sha256"]
    ):
        raise ValueError("manifest is not bound to the selected artifact provenance")
    if manifest.paper.relation != "pilot_adaptation":
        raise ValueError("selected artifact run must remain a pilot_adaptation")
    if manifest.expected_output.status != "not_assessed":
        raise ValueError("selected artifact run must remain not_assessed")
    report = {
        "run_id": manifest.run_id,
        "code_id": manifest.artifact.code_id,
        "relation": manifest.paper.relation,
        "assessment_status": manifest.expected_output.status,
        "assessment_reason": manifest.expected_output.reason,
        "paper_revision": manifest.paper.revision,
        "paper_uri": manifest.paper.uri,
        "implementation_revision": manifest.implementation.revision,
        "implementation_uri": manifest.implementation.repository_uri,
        "artifact_raw_sha256": manifest.artifact.raw_sha256,
        "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
        "shot_budget": manifest.budget.max_shots,
        "max_iter": manifest.budget.max_iter,
    }
    return report


def preflight_canonical(manifest_path: str | Path) -> dict[str, Any]:
    """Resolve all canonical external facts before sampling or durable evidence."""
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV7, CanonicalExperimentV8)):
        raise ValueError("canonical execution requires a strict public canonical manifest")
    composition = validate_composition(manifest.policies) if isinstance(manifest, (CanonicalExperimentV5, CanonicalExperimentV7)) else validate_executable_canonical_baseline(manifest.policies)
    report = {
        "run_id": manifest.run_id,
        "code_id": manifest.artifact.code_id,
        "manifest_sha256": manifest_digest(manifest),
        "numerical_profile": manifest.numerical_profile,
        "resolved_numerical_profile": (MIN_SUM_CPU_F64 if manifest.numerical_profile == "cpu-float64-min-sum-v1" else REFERENCE_CPU_F64).as_evidence(),
        "policies": manifest.policies.model_dump(mode="json", exclude_none=True),
        "policy_identity": composition.semantic_identity,
        "policy_effects": _canonical_policy_effects(manifest, resolved.code),
        "shot_budget": manifest.budgets.max_shots,
        "max_iterations": manifest.budgets.attempt.max_iterations,
        "work_limits": {
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        "relation": manifest.evidence.relation,
        "fixture": manifest.evidence.fixture,
        "assessment_status": manifest.evidence.assessment_status,
        "profile_plan": manifest.profile_plan.model_dump(mode="json"),
        "trace_plan": manifest.trace_plan.model_dump(mode="json"),
    }
    if isinstance(manifest, CanonicalExperimentV5):
        report["intervention"] = {
            "specification": manifest.intervention.model_dump(mode="json", exclude_none=True),
            "limits": manifest.intervention_limits.model_dump(mode="json"),
            "compact_contract_version": 7 if isinstance(manifest, CanonicalExperimentV6) else 6,
            "ledger_version": 5,
        }
        if isinstance(manifest, CanonicalExperimentV6):
            report["memory"] = manifest.memory.model_dump(mode="json")
    elif isinstance(manifest, CanonicalExperimentV7):
        report["ensemble"] = manifest.ensemble.model_dump(mode="json")
        report["list_selection"] = manifest.list_selection.model_dump(mode="json")
        report["vote"] = None if manifest.vote is None else manifest.vote.model_dump(mode="json")
        report["ledger_version"] = 6
    elif isinstance(manifest, CanonicalExperimentV4):
        report["memory"] = {
            "bindings": [binding.model_dump(mode="json") for binding in manifest.memory.bindings],
            "compatibility": {"admitted": True, "reason": None},
        }
        if manifest.relay is None:
            report["memory"]["execution"] = (
                {
                    "compact_contract_version": 5,
                    "mode": "ordered_single_attempt_flooding",
                    "commit_boundary": "complete_double_buffered_sweep",
                    "operand_order": ["prior", "belief_or_posterior", "v2c"],
                }
                if manifest.policies.schedule.kind == "flooding" else
                {
                    "compact_contract_version": 5,
                    "mode": "ordered_attempt_local_update",
                    "commit_boundary": "admitted_local_unit_after_convergence_check",
                    "operand_order": ["complete_fresh_belief", "affected_fresh_v2c"],
                }
            )
        if manifest.relay is not None:
            tuning = manifest.relay.memory_tuning
            report["relay"] = {
                "specification": manifest.relay.model_dump(mode="json"),
                "memory_execution": (
                    {"mode": "legacy_transfer_affine", "active_each_source_iteration": False}
                    if tuning is None else
                    {
                        "mode": "dynamic_affine_prior_each_source_iteration",
                        "active_each_source_iteration": True,
                        "source_semantics": "trmue/relay@v0.2.2: relay.rs:183-203; min_sum.rs:406-448",
                        "first_leg_gamma": tuning.first_leg_gamma,
                        "later_leg_center": tuning.later_leg_center,
                        "later_leg_width": tuning.later_leg_width,
                        "later_leg_low": tuning.later_leg_low,
                        "later_leg_high": tuning.later_leg_high,
                        "seed_identity": tuning.seed_identity,
                        "rng_algorithm": tuning.rng_algorithm,
                        "refresh": tuning.refresh,
                    }
                ),
            }
    return report


def preflight_quaternary(manifest_path: str | Path) -> dict[str, Any]:
    """Validate the distinct four-state public tracer before sampling."""
    manifest = preflight(manifest_path).manifest
    if not isinstance(manifest, (QuaternaryExperimentV1, QuaternaryExperimentV2)):
        raise ValueError("quaternary execution requires a quaternary experiment manifest")
    report = {
        "run_id": manifest.run_id,
        "manifest_sha256": manifest_digest(manifest),
        "shot_budget": 1,
        "pauli_encoding": "I=0,X=1,Y=2,Z=3",
        "max_iterations": manifest.max_iterations,
        "max_work": manifest.max_work,
        "relation": manifest.evidence.relation,
        "fixture": manifest.evidence.fixture,
        "assessment_status": manifest.evidence.assessment_status,
    }
    if isinstance(manifest, QuaternaryExperimentV2):
        intervention = manifest.composition.intervention
        is_asced = intervention is not None and intervention.kind in {"asced", "asced_overcomplete"}
        if is_asced:
            _css_from_public_problem(TracerPauliProblem(manifest.problem.checks, manifest.problem.syndrome))
        resolved = resolve_quaternary_composition(manifest.composition, problem_kind="css" if is_asced else "general_pauli")
        report["shot_budget"] = manifest.shot_budget
        report["composition"] = resolved.model_dump(mode="json")
    return report


def run_quaternary(manifest_path: str | Path, output: str | Path, *, shot_id: int | None = None) -> dict[str, Any]:
    """Run the single bounded joint-Pauli tracer through the public path."""
    report = preflight_quaternary(manifest_path)
    manifest = preflight(manifest_path).manifest
    if not isinstance(manifest, (QuaternaryExperimentV1, QuaternaryExperimentV2)):
        raise ValueError("quaternary execution requires a quaternary experiment manifest")
    if shot_id not in (None, 0) or (isinstance(manifest, QuaternaryExperimentV2) and (shot_id or 0) >= manifest.shot_budget):
        raise ValueError("quaternary shot ID is outside the manifest budget")
    output_path = Path(output)
    persisted_manifest = output_path / "manifest.json"
    if isinstance(manifest_path, (str, Path)):
        manifest_reference = str(Path(manifest_path))
    else:
        output_path.mkdir(parents=True, exist_ok=True)
        persisted_manifest.write_text(json.dumps(manifest.model_dump(mode="json"), sort_keys=True) + "\n", encoding="utf-8")
        manifest_reference = str(persisted_manifest)
    qbpgd = isinstance(manifest, QuaternaryExperimentV2) and manifest.composition.intervention is not None and manifest.composition.intervention.kind == "qbpgd"
    mbp4 = isinstance(manifest, QuaternaryExperimentV2) and manifest.composition.kernel is not None and manifest.composition.kernel.kind == "qbp_mbp4_fixed_alpha"
    asced = isinstance(manifest, QuaternaryExperimentV2) and manifest.composition.intervention is not None and manifest.composition.intervention.kind in {"asced", "asced_overcomplete"}
    scalar_public = isinstance(manifest, QuaternaryExperimentV2) and not qbpgd and not mbp4 and not asced
    if asced:
        result: Any = run_quaternary_asced(manifest, output_path, resolved_composition=report["composition"], shot_id=0)
    elif qbpgd:
        result: Any = run_quaternary_qbpgd(manifest, output_path, resolved_composition=report["composition"], shot_id=0)
    elif mbp4:
        result = run_quaternary_mbp4(manifest, output_path, resolved_composition=report["composition"], shot_id=0)
    elif scalar_public:
        result = run_quaternary_scalar(manifest, output_path, resolved_composition=report["composition"], shot_id=0)
    else:
        result = run_quaternary_tracer(manifest, output_path, shot_id=0)
    ledger_path = output_path / "events.jsonl"
    public = {
        **report, "output": str(output_path), "final_row_count": 1,
        "termination": result["termination"] if (qbpgd or mbp4 or asced or scalar_public) else result.termination,
        "outcome": result["outcome"] if (qbpgd or mbp4 or asced or scalar_public) else result.outcome,
        "ledger_sha256": sha256(ledger_path.read_bytes()).hexdigest(),
        "manifest_path": manifest_reference, "ledger_path": str(ledger_path),
        "statistical_claim": "not_assessed; development fixture, not a source-curve reproduction or performance result",
    }
    if qbpgd or mbp4 or asced or scalar_public:
        public.update({
            "run_fidelity": result["run_fidelity"], "component_fidelity": result["component_fidelity"],
            "component_ids": result["component_ids"], "interpretation_ids": result["interpretation_ids"],
            "source_author_code_identity": result["source_author_code_identity"],
            "work": result["work"], "adaptation_reasons": report["composition"]["adaptation_reasons"],
        })
    (output_path / "result.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return public


def verify_quaternary_run(output: str | Path) -> dict[str, Any]:
    """Verify result identity and exact replay for a joint-Pauli tracer output."""
    output_path = Path(output)
    result = json.loads((output_path / "result.json").read_text(encoding="utf-8"))
    if result.get("assessment_status") != "not_assessed" or result.get("statistical_claim", "").find("not_assessed") < 0:
        raise ValueError("quaternary result must remain not_assessed")
    manifest_path = Path(result["manifest_path"])
    report = preflight_quaternary(manifest_path)
    if result.get("manifest_sha256") != report["manifest_sha256"] or result.get("ledger_sha256") != sha256((output_path / "events.jsonl").read_bytes()).hexdigest():
        raise ValueError("quaternary result identity differs from immutable evidence")
    manifest = preflight(manifest_path).manifest
    if isinstance(manifest, QuaternaryExperimentV2):
        scratch = output_path / ".public-v2-replay"
        run_quaternary(manifest_path, scratch, shot_id=0)
        expected = (scratch / "events.jsonl").read_bytes()
        actual = (output_path / "events.jsonl").read_bytes()
        for child in scratch.iterdir():
            child.unlink()
        scratch.rmdir()
        if actual != expected:
            raise ValueError("quaternary public ledger differs from deterministic replay")
        replay = {"run_id": manifest.run_id, "shot_id": 0, "verified": True}
    else:
        replay = verify_quaternary_tracer(manifest, output_path, shot_id=0)
    return {**report, "output": str(output_path), "final_row_count": 1, **replay}


def _without_none(value: object) -> object:
    """Canonical V4 kernel contracts reject fields that the public V3 model leaves null."""
    if isinstance(value, dict):
        return {key: _without_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_without_none(item) for item in value]
    return value


def _canonical_kernel_manifest(manifest: CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV7) -> dict[str, object]:
    """Project-owned kernel receives only its compact execution policy contract."""
    if isinstance(manifest, CanonicalExperimentV8):
        return {
            "schema_version": 3, "run_id": manifest.run_id,
            "numerical_profile": manifest.numerical_profile,
            "max_iterations": manifest.budgets.attempt.max_iterations,
            "error_rate": manifest.error_rate,
            "policies": manifest.policies.model_dump(mode="json"),
            "postprocessing_config": manifest.postprocessing_config.model_dump(mode="json"),
        }
    if isinstance(manifest, CanonicalExperimentV7):
        return manifest.model_dump(mode="json")
    if isinstance(manifest, CanonicalExperimentV5):
        compact = {
            "schema_version": 7 if isinstance(manifest, CanonicalExperimentV6) else 6,
            "run_id": manifest.run_id,
            "numerical_profile": manifest.numerical_profile,
            "max_iterations": manifest.budgets.attempt.max_iterations,
            "error_rate": manifest.error_rate,
            "policies": _without_none(manifest.policies.model_dump(mode="json")),
            "intervention": manifest.intervention.model_dump(mode="json", exclude_none=True),
        }
        if isinstance(manifest, CanonicalExperimentV6):
            compact["memory"] = manifest.memory.model_dump(mode="json")
        return compact
    compact: dict[str, object] = {
        "schema_version": 3 if isinstance(manifest, CanonicalExperimentV4) else manifest.schema_version,
        "run_id": manifest.run_id,
        "numerical_profile": manifest.numerical_profile,
        "max_iterations": manifest.budgets.attempt.max_iterations,
        "error_rate": manifest.error_rate,
        # V2/V3 identity is part of retained public evidence. Preserve its
        # historical null-bearing compact representation exactly.
        "policies": manifest.policies.model_dump(mode="json"),
    }
    if isinstance(manifest, CanonicalExperimentV4) and manifest.relay is None:
        compact.update({
            "schema_version": 5,
            "memory": manifest.memory.model_dump(mode="json"),
        })
    if isinstance(manifest, CanonicalExperimentV4) and manifest.relay is not None:
        compact.update({
            "schema_version": 4,
            "policies": _without_none(manifest.policies.model_dump(mode="json")),
            "memory_bindings": [
                {
                    "binding_id": binding.binding_id,
                    "kind": binding.kind,
                    "target": binding.target,
                    "order": binding.order,
                    "alpha": binding.parameters["alpha"],
                    "state_lifetime": binding.state_lifetime,
                }
                for binding in manifest.memory.bindings
            ],
            "relay": manifest.relay.model_dump(mode="json"),
        })
    return compact


def _canonical_policy_effects(manifest: CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV7, code) -> dict[str, dict[str, Any]]:
    """Bind declared NMS assignments to the code's canonical edge identities once."""
    if isinstance(manifest, (CanonicalExperimentV5, CanonicalExperimentV7)):
        effects: dict[str, dict[str, Any]] = {
            binding.role.value: {
                "binding_id": binding.binding_id,
                "effect": "active" if binding.role.value in {"update", "schedule", "intervention", "stopping", "selection"} else "identity_only",
            }
            for binding in validate_composition(manifest.policies).bindings
        }
    else:
        effects = executable_canonical_policy_effects(manifest.policies)
    assignment = getattr(manifest.policies.update, "parameter_assignment", None)
    generation = None
    if assignment is None and isinstance(manifest, CanonicalExperimentV3) and manifest.policies.update.parameter_generator is not None:
        from .canonical.updates import resolve_generated_configuration_assignment

        table = EdgeTable.from_check_matrix(code.hz)
        assignment, generation = resolve_generated_configuration_assignment(
            manifest.policies.update.model_dump(mode="json"), _canonical_kernel_manifest(manifest),
            graph_sha256=table.graph_sha256, check_count=table.check_count,
            edge_count=table.edge_count,
        )
    if assignment is not None:
        table = EdgeTable.from_check_matrix(code.hz)
        resolved = assignment.resolve(
            graph_sha256=table.graph_sha256, check_count=table.check_count, edge_count=table.edge_count,
            source_iteration=0, edge_checks=tuple(check for check, _variable in table.edges),
        )
        effects["update"] = {
            **effects["update"], "parameter_assignment": assignment.as_evidence(resolved),
            **({"parameter_generation": generation} if generation is not None else {}),
        }
    return effects


def _canonical_execution_controls(manifest: CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV7, code) -> dict[str, object]:
    """Keep preflighted public limits and handler classifications beside the compact kernel input."""
    controls: dict[str, object] = {
        "work_limits": {
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        "policy_effects": _canonical_policy_effects(manifest, code),
        "profile_plan": manifest.profile_plan.model_dump(mode="json"),
    }
    if isinstance(manifest, CanonicalExperimentV5):
        controls["phase5_work_caps"] = dict(manifest.intervention_limits.work_caps)
        controls["phase5_max_runtime_seconds"] = manifest.intervention_limits.max_runtime_seconds
    # Trace-off V2/V3/Relay ledgers predate this control.  Omit an inert plan
    # so their execution identity and replayed evidence remain historical.
    if manifest.trace_plan.level != "off":
        controls["trace_plan"] = manifest.trace_plan.model_dump(mode="json")
    return controls


@dataclass(frozen=True, slots=True)
class CanonicalPublicManifestContext:
    """Immutable preflight facts from which each public shot is freshly sampled."""

    _manifest: CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV7
    _code: Any
    manifest_sha256: str
    _compact_manifest: dict[str, object]
    composition_identity: str
    _policy_effects: dict[str, dict[str, Any]]
    _work_limits: dict[str, dict[str, int]]
    _profile_plan: dict[str, object]
    _trace_plan: dict[str, object] | None
    _phase5_limits: dict[str, object] | None = None

    @property
    def manifest(self) -> CanonicalExperimentV2 | CanonicalExperimentV3 | CanonicalExperimentV4 | CanonicalExperimentV5 | CanonicalExperimentV7:
        """Return a detached manifest view of the preflight snapshot."""
        return self._manifest.model_copy(deep=True)

    @property
    def code(self) -> Any:
        """Return a detached code view; matrix mutation cannot poison later shots."""
        return deepcopy(self._code)

    @property
    def compact_manifest(self) -> dict[str, object]:
        return deepcopy(self._compact_manifest)

    @property
    def policy_effects(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._policy_effects)

    @property
    def work_limits(self) -> dict[str, dict[str, int]]:
        return deepcopy(self._work_limits)

    @property
    def profile_plan(self) -> dict[str, object]:
        return deepcopy(self._profile_plan)

    @property
    def trace_plan(self) -> dict[str, object] | None:
        return deepcopy(self._trace_plan)

    def shot_context(self, shot_id: int) -> PublicShotContext:
        """Derive one independent public context with the exact pinned sample rule."""
        manifest = self._manifest
        if type(shot_id) is not int or not 0 <= shot_id < manifest.budgets.max_shots:
            raise ValueError("shot_id is outside the canonical manifest budget")
        sample = sampling.sample_shot(
            self._code, manifest_identity=manifest.randomness.physical_sample_identity or self.manifest_sha256,
            seed=manifest.randomness.sample_seed,
            shot_id=shot_id, x_error_rate=manifest.error_rate,
        )
        return PublicShotContext(
            manifest_sha256=self.manifest_sha256,
            artifact_raw_sha256=manifest.artifact.raw_sha256,
            artifact_semantic_sha256=manifest.artifact.semantic_sha256,
            compact_manifest=deepcopy(self._compact_manifest),
            sample_seed_identity=sample.sample_identity,
            run_id=manifest.run_id,
            shot_id=shot_id,
            check_type=sample.observation.check_type,
            syndrome=tuple(int(value) for value in sample.observation.syndrome.tolist()),
            code_id=manifest.artifact.code_id,
            evidence_relation=manifest.evidence.relation,
            fixture=manifest.evidence.fixture,
            assessment_status=manifest.evidence.assessment_status,
            decoder_seed_identity=manifest.randomness.decoder_seed_identity,
            code=deepcopy(self._code),
            hidden_truth=sample.hidden,
            error_rate=manifest.error_rate,
            max_iterations=manifest.budgets.attempt.max_iterations,
            work_limits=deepcopy(self._work_limits),
            composition_identity=self.composition_identity,
            policy_effects=deepcopy(self._policy_effects),
            profile_plan=deepcopy(self._profile_plan),
            trace_plan=deepcopy(self._trace_plan),
            phase5_limits=deepcopy(self._phase5_limits),
            update_kind=manifest.policies.update.kind,
            schedule_kind=manifest.policies.schedule.kind,
        )


def canonical_public_manifest_context(
    manifest_path: str | Path, *, manifest_bytes: bytes | None = None,
) -> CanonicalPublicManifestContext:
    """Preflight immutable public manifest facts once; this function never samples."""
    resolved = (preflight(manifest_path) if manifest_bytes is None
                else preflight_manifest_bytes(manifest_path, manifest_bytes))
    manifest = resolved.manifest
    if not isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV7, CanonicalExperimentV8)):
        raise ValueError("canonical execution requires a strict public canonical manifest")
    composition = validate_composition(manifest.policies) if isinstance(manifest, (CanonicalExperimentV5, CanonicalExperimentV7)) else validate_executable_canonical_baseline(manifest.policies)
    return CanonicalPublicManifestContext(
        _manifest=manifest,
        _code=resolved.code,
        manifest_sha256=manifest_digest(manifest),
        _compact_manifest=_canonical_kernel_manifest(manifest),
        composition_identity=composition.semantic_identity,
        _policy_effects=_canonical_policy_effects(manifest, resolved.code),
        _work_limits={
            scope: getattr(manifest.budgets, scope).work_limits.as_evidence()
            for scope in ("shot", "search", "attempt")
        },
        _profile_plan=manifest.profile_plan.model_dump(mode="json"),
        _trace_plan=(manifest.trace_plan.model_dump(mode="json")
                    if manifest.trace_plan.level != "off" else None),
        _phase5_limits=(manifest.intervention_limits.model_dump(mode="json")
                        if isinstance(manifest, CanonicalExperimentV5) else None),
    )


def canonical_public_shot_context(manifest_path: str | Path, *, shot_id: int) -> PublicShotContext:
    """Resolve a deterministic public shot without opening a durable ledger."""
    return canonical_public_manifest_context(manifest_path).shot_context(shot_id)


@dataclass(frozen=True, slots=True)
class CanonicalMaterializedInterruptionV1:
    """Zero-credit partial attempt evidence, deliberately without decoder outcome facts."""

    schema: Literal["canonical_materialized_interruption_v1"]
    ledger_path: str
    ledger_sha256: str | None
    snapshot: CanonicalRuntimeSnapshotV1


@dataclass(frozen=True, slots=True)
class CanonicalMaterializedRunV1:
    status: Literal["terminal", "interrupted"]
    terminal: Any | None = None
    interruption: CanonicalMaterializedInterruptionV1 | None = None

    def __post_init__(self) -> None:
        if (self.status == "terminal") != (self.terminal is not None):
            raise ValueError("materialized terminal wrapper requires only a terminal result")
        if (self.status == "interrupted") != (self.interruption is not None):
            raise ValueError("materialized interruption wrapper requires only interruption evidence")


def run_canonical_materialized_one(
    manifest_path: str | Path, *, sample: sampling.ShotSample,
    materialized_sample_sha256: str, ledger_path: str | Path,
    manifest_bytes: bytes | None = None,
    runtime_authorization: CanonicalRuntimeAuthorizationV1 | None = None,
):
    """Run one verified caller-supplied physical sample without resampling.

    The supplied sample is evaluator-owned: policy execution receives only its
    decoder observation through ``run_canonical_structural_shot``.  This seam
    deliberately does not use ``shot_context`` because that convenience method
    samples a fresh error for every manifest.
    """
    if not isinstance(sample, sampling.ShotSample):
        raise ValueError("materialized canonical execution requires a ShotSample")
    if not isinstance(materialized_sample_sha256, str) or len(materialized_sample_sha256) != 64:
        raise ValueError("materialized sample requires a SHA-256 identity")
    public = canonical_public_manifest_context(manifest_path, manifest_bytes=manifest_bytes)
    manifest = public.manifest
    if runtime_authorization is not None:
        derived = derive_canonical_executable_maxima(public)
        if runtime_authorization.profile_digest != derived.digest:
            raise ValueError("runtime authorization profile_digest differs from executable route")
        if runtime_authorization.max_event_bytes != derived.serializer_bytes_per_event:
            raise ValueError("runtime authorization event ceiling differs from executable route")
        if runtime_authorization.max_artifact_bytes != CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1:
            raise ValueError("runtime authorization artifact ceiling differs from executable route")
        if runtime_authorization.control_receipt_reserve_bytes < derived.partial_receipt_reserve_bytes:
            raise ValueError("runtime authorization control receipt reserve is smaller than derived")
        if runtime_authorization.mode == "strict_full_unit" and (
            runtime_authorization.max_events < derived.derived_events_per_unit
            or runtime_authorization.max_evidence_bytes < (
                derived.derived_evidence_bytes_per_unit - derived.partial_receipt_reserve_bytes
            )
            or runtime_authorization.max_storage_bytes < (
                derived.derived_storage_bytes_per_unit - derived.partial_receipt_reserve_bytes
            )
        ):
            raise ValueError("strict_full_unit runtime authorization is below derived maxima")
    if not 0 <= sample.shot_id < manifest.budgets.max_shots:
        raise ValueError("materialized sample shot ID is outside the canonical manifest budget")
    anchor = manifest.randomness.physical_sample_identity or public.manifest_sha256
    expected_identity = sha256(
        f"bp-registry-sample-v1\0{anchor}\0{sample.shot_id}".encode()
    ).hexdigest()
    if sample.sample_identity != expected_identity:
        raise ValueError("materialized sample identity differs from the pinned sampler contract")
    code = public.code
    if sample.hidden.x.dtype.name != "uint8" or sample.hidden.z.dtype.name != "uint8":
        raise ValueError("materialized error vectors must be uint8")
    if sample.hidden.x.shape != (code.n,) or sample.hidden.z.shape != (code.n,):
        raise ValueError("materialized error vectors differ from the pinned code size")
    expected_z = ((code.hz.astype("int64") @ sample.hidden.x) % 2).astype("uint8")
    expected_x = ((code.hx.astype("int64") @ sample.hidden.z) % 2).astype("uint8")
    if (set(sample.observations) != {"X", "Z"}
            or sample.observation.check_type != "Z"
            or sample.observation.syndrome.dtype.name != "uint8"
            or not (sample.observation.syndrome == expected_z).all()
            or not (sample.observations["Z"].syndrome == expected_z).all()
            or not (sample.observations["X"].syndrome == expected_x).all()):
        raise ValueError("materialized sample observations differ from recomputed syndromes")
    verification_context = PublicShotContext(
        manifest_sha256=public.manifest_sha256,
        artifact_raw_sha256=manifest.artifact.raw_sha256,
        artifact_semantic_sha256=manifest.artifact.semantic_sha256,
        compact_manifest=public.compact_manifest,
        sample_seed_identity=sample.sample_identity,
        run_id=manifest.run_id, shot_id=sample.shot_id,
        check_type=sample.observation.check_type,
        syndrome=tuple(int(value) for value in sample.observation.syndrome.tolist()),
        code_id=manifest.artifact.code_id, evidence_relation=manifest.evidence.relation,
        fixture=manifest.evidence.fixture, assessment_status=manifest.evidence.assessment_status,
        decoder_seed_identity=manifest.randomness.decoder_seed_identity, code=code,
        hidden_truth=sample.hidden, error_rate=manifest.error_rate,
        max_iterations=manifest.budgets.attempt.max_iterations, work_limits=public.work_limits,
        composition_identity=public.composition_identity, policy_effects=public.policy_effects,
        profile_plan=public.profile_plan, trace_plan=public.trace_plan,
        phase5_limits=public._phase5_limits, update_kind=manifest.policies.update.kind,
        schedule_kind=manifest.policies.schedule.kind,
    )
    guard = None if runtime_authorization is None else CanonicalRuntimeGuardV1(runtime_authorization)
    try:
        result = run_canonical_structural_shot(
            public.compact_manifest, code=code, observation=sample.observation,
            hidden_truth=sample.hidden, shot_id=sample.shot_id, ledger_path=ledger_path,
            sample_seed_identity=sample.sample_identity, verification_context=verification_context,
            execution_controls=_canonical_execution_controls(manifest, code),
            memory_execution_context=verification_context.memory_execution_context,
            resource_guard=guard,
            context={
                "manifest_sha256": public.manifest_sha256,
                "artifact_raw_sha256": manifest.artifact.raw_sha256,
                "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
                "code_id": manifest.artifact.code_id, "evidence_relation": manifest.evidence.relation,
                "fixture": manifest.evidence.fixture, "assessment_status": manifest.evidence.assessment_status,
                "decoder_seed_identity": manifest.randomness.decoder_seed_identity,
                "composition_identity": public.composition_identity,
                "execution_identity": verification_context.execution_identity,
            },
        )
    except CanonicalResourceInterruption as error:
        if runtime_authorization is None or not isinstance(error.snapshot, CanonicalRuntimeSnapshotV1):
            raise
        ledger = Path(ledger_path)
        return CanonicalMaterializedRunV1(
            "interrupted", interruption=CanonicalMaterializedInterruptionV1(
                "canonical_materialized_interruption_v1", str(ledger),
                None if not ledger.exists() else sha256(ledger.read_bytes()).hexdigest(), error.snapshot,
            ),
        )
    return result if runtime_authorization is None else CanonicalMaterializedRunV1("terminal", terminal=result)


def run_canonical_one(manifest_path: str | Path, *, shot_id: int, ledger_path: str | Path):
    """Sample outside the engine, then evaluate only a frozen original-space candidate."""
    verification_context = canonical_public_shot_context(manifest_path, shot_id=shot_id)
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    assert isinstance(manifest, (CanonicalExperimentV2, CanonicalExperimentV3, CanonicalExperimentV4, CanonicalExperimentV5, CanonicalExperimentV7, CanonicalExperimentV8))
    digest = verification_context.manifest_sha256
    sample = sampling.sample_shot(
        resolved.code, manifest_identity=manifest.randomness.physical_sample_identity or digest,
        seed=manifest.randomness.sample_seed,
        shot_id=shot_id, x_error_rate=manifest.error_rate,
    )
    composition = validate_composition(manifest.policies) if isinstance(manifest, (CanonicalExperimentV5, CanonicalExperimentV7)) else validate_executable_canonical_baseline(manifest.policies)
    compact_manifest = _canonical_kernel_manifest(manifest)
    return run_canonical_structural_shot(
        compact_manifest, code=resolved.code, observation=sample.observation,
        hidden_truth=sample.hidden, shot_id=shot_id, ledger_path=ledger_path,
        sample_seed_identity=sample.sample_identity,
        verification_context=verification_context,
        execution_controls=_canonical_execution_controls(manifest, resolved.code),
        memory_execution_context=verification_context.memory_execution_context,
        context={
            "manifest_sha256": digest,
            "artifact_raw_sha256": manifest.artifact.raw_sha256,
            "artifact_semantic_sha256": manifest.artifact.semantic_sha256,
            "code_id": manifest.artifact.code_id,
            "evidence_relation": manifest.evidence.relation,
            "fixture": manifest.evidence.fixture,
            "assessment_status": manifest.evidence.assessment_status,
            "decoder_seed_identity": manifest.randomness.decoder_seed_identity,
            "composition_identity": composition.semantic_identity,
            "execution_identity": verification_context.execution_identity,
        },
    )


def canonical_terminal_rows(ledger_path: str | Path, run_id: str) -> list[dict[str, Any]]:
    """Return only terminal structural evidence for one canonical run."""
    return sorted(
        (event for event in read_canonical_events(ledger_path)
         if event["run_id"] == run_id and event["kind"] == "termination"),
        key=lambda event: event["shot_id"],
    )


def run_one(manifest_path: str | Path, *, shot_id: int, ledger_path: str | Path) -> ShotResult:
    resolved = preflight(manifest_path)
    manifest = resolved.manifest
    if not isinstance(manifest, ManifestV1):
        raise ValueError("legacy manifests are read-only and cannot execute")
    if not 0 <= shot_id < manifest.budget.max_shots:
        raise ValueError("shot_id is outside the manifest budget")
    code = resolved.code
    digest = manifest_digest(manifest)
    source_uri = manifest.implementation.repository_uri
    source_revision = manifest.implementation.revision
    source_anchor = manifest.implementation.source_path
    code_id = manifest.artifact.code_id
    experiment_relation = manifest.paper.relation
    expected_output_status = manifest.expected_output.status
    x_error_rate = manifest.noise.x_error_rates[0]
    seed = manifest.seed_policy.root_seed
    max_iter = manifest.budget.max_iter
    bp_method = manifest.decoder.bp_method
    schedule = manifest.decoder.schedule
    input_vector_type = manifest.decoder.input_vector_type
    decoder_version = manifest.decoder.version
    artifact_raw_sha256 = manifest.artifact.raw_sha256
    artifact_semantic_sha256 = manifest.artifact.semantic_sha256
    artifact_path = str(Path(manifest.artifact.root) / manifest.artifact.path)
    common = {
        "manifest_sha256": digest,
        "source_uri": source_uri,
        "source_revision": source_revision,
        "source_anchor": source_anchor,
        "paper_uri": manifest.paper.uri,
        "paper_revision": manifest.paper.revision,
        "paper_anchor": manifest.paper.experiment_anchor,
        "implementation_source_artifact_sha256": manifest.implementation.source_artifact_sha256,
        "code_id": code_id,
        "experiment_relation": experiment_relation,
        "expected_output_status": expected_output_status,
        "decoder_config": {
            "bp_method": bp_method,
            "schedule": schedule,
            "input_vector_type": input_vector_type,
            "error_rate": x_error_rate,
            "max_iter": max_iter,
        },
        "decoder_version": decoder_version,
        "artifact_raw_sha256": artifact_raw_sha256,
        "artifact_semantic_sha256": artifact_semantic_sha256,
        "artifact_path": artifact_path,
    }
    sample_seed_identity = sha256(
        f"bp-registry-sample-v1\0{digest}\0{shot_id}".encode()
    ).hexdigest()
    with Writer(ledger_path) as ledger:
        ledger.begin(
            run_id=manifest.run_id, shot_id=shot_id,
            sample_seed_identity=sample_seed_identity, **common,
        )
        stage = "sampling"
        try:
            sample = sampling.sample_shot(
                code, manifest_identity=digest, seed=seed, shot_id=shot_id,
                x_error_rate=x_error_rate,
            )
            stage = "decoding"
            native = _native_reference().decode(
                code.hz, sample.observation.syndrome, error_rate=x_error_rate,
                max_iter=max_iter, bp_method=bp_method,
                schedule=schedule, input_vector_type=input_vector_type,
            )
            stage = "evaluation"
            evaluation = evaluator.evaluate_candidate(
                code, true_x=sample.hidden.x, true_z=sample.hidden.z,
                candidate_x=native.candidate,
            )
            ledger.terminal(
                run_id=manifest.run_id, shot_id=shot_id, **common,
                termination="completed", observation_check_type="Z",
                syndrome=sample.observation.syndrome.tolist(), sample_identity=sample.sample_identity,
                hidden_x=sample.hidden.x.tolist(), hidden_z=sample.hidden.z.tolist(),
                candidate=native.candidate.tolist(), native_converged=native.converged,
                native_iterations=native.iterations, native_edge_updates=None,
                native_metric_facts=[fact.as_evidence() for fact in native.metric_facts],
                native_edge_updates_missing_reason=native.edge_updates_missing_reason,
                native_internals_unavailable_reason=native.edge_updates_missing_reason,
                outcome=evaluation.outcome, logical_action_agrees=evaluation.logical_action_agrees,
                selected_output=native.candidate.tolist(), selection_status="native_bp_candidate",
                postselection="none", postselection_status="not_requested",
            )
            return ShotResult(
                manifest.run_id, shot_id, evaluation.outcome, native.converged, native.iterations
            )
        except Exception as exc:
            ledger.terminal(
                run_id=manifest.run_id, shot_id=shot_id, **common,
                termination="exception", exception_stage=stage,
                exception_type=type(exc).__name__, exception_message=str(exc),
                native_converged=None, native_iterations=None, native_edge_updates=None,
                native_metric_facts=_unavailable_native_metric_facts(stage),
                native_internals_unavailable_reason=(
                    f"native internals unavailable because {stage} raised before terminal evaluation"
                ),
                outcome=None, outcome_unavailable_reason=(
                    f"independent outcome unavailable because {stage} raised"
                ),
                selected_output=None, selection_status="unavailable_due_to_exception",
                postselection="unavailable",
            )
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--shot-id", type=int, default=0)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    result = run_one(args.manifest, shot_id=args.shot_id, ledger_path=args.ledger)
    print(f"{result.run_id} shot={result.shot_id} outcome={result.outcome} ",
          f"native_converged={result.converged} native_iterations={result.iterations}")


if __name__ == "__main__":
    main()
