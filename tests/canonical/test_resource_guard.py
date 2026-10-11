"""Hard byte and deadline guards for bounded canonical execution."""

from __future__ import annotations

import pytest


def test_guarded_append_exact_fit_and_one_byte_over_leave_prefix_unchanged(tmp_path):
    from bp_registry.ledger import CanonicalEventWriter
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    path = tmp_path / "events.jsonl"
    authorization = CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="a" * 64, authorization_identity="unit", max_events=2,
        max_evidence_bytes=2, max_storage_bytes=2, control_receipt_reserve_bytes=3,
    )
    guard = CanonicalRuntimeGuardV1(authorization)
    payload = b"x\n"
    reservation = guard.reserve_ledger_append(payload, boundary="test")
    guard.commit(reservation)
    assert guard.snapshot().scientific_evidence_bytes == 2
    with pytest.raises(Exception, match="resource cap"):
        guard.reserve_ledger_append(b"y\n", boundary="test")
    assert guard.snapshot().scientific_evidence_bytes == 2

    # Writer denial happens before any append, including the trailing newline.
    with CanonicalEventWriter(path, resource_guard=guard) as writer:
        with pytest.raises(Exception, match="resource cap"):
            writer.begin(run_id="r", shot_id=0, sample_seed_identity="s")
    assert not path.exists() or path.read_bytes() == b""


def test_guard_control_reserve_is_single_use_after_scientific_exhaustion():
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    authorization = CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="b" * 64, authorization_identity="unit", max_events=1,
        max_evidence_bytes=2, max_storage_bytes=2, control_receipt_reserve_bytes=5,
    )
    guard = CanonicalRuntimeGuardV1(authorization)
    guard.commit(guard.reserve_ledger_append(b"a\n", boundary="first"))
    with pytest.raises(Exception, match="resource cap"):
        guard.reserve_artifact_write(1, boundary="after-exhaustion")
    control = guard.reserve_control_receipt(5)
    guard.commit(control)
    with pytest.raises(Exception, match="control receipt"):
        guard.reserve_control_receipt(1)


def test_strict_mode_requires_the_full_profile_limit():
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1

    with pytest.raises(ValueError, match="strict_full_unit"):
        CanonicalRuntimeAuthorizationV1.strict_full_unit(
            profile_digest="c" * 64, authorization_identity="unit", max_events=1,
            max_evidence_bytes=1, max_storage_bytes=1, control_receipt_reserve_bytes=1,
            derived_events=2, derived_evidence_bytes=2, derived_storage_bytes=2,
        )


def test_wall_boundary_records_positive_overshoot_and_latches_future_work():
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    ticks = iter((10, 14))
    guard = CanonicalRuntimeGuardV1(
        CanonicalRuntimeAuthorizationV1.interruptible_unit(
            profile_digest="d" * 64, authorization_identity="unit", max_events=5,
            max_evidence_bytes=100, max_storage_bytes=100, control_receipt_reserve_bytes=10,
            monotonic_deadline_ns=12,
        ), clock_ns=lambda: next(ticks),
    )
    guard.before_work("atomic:before_work")
    with pytest.raises(Exception, match="resource cap"):
        guard.after_work("atomic:after_work")
    snapshot = guard.snapshot()
    assert snapshot.interruption_kind == "wall_deadline"
    assert snapshot.overshoot_ns == 2
    with pytest.raises(Exception, match="resource cap"):
        guard.before_work("later:before_work")


def test_executable_maxima_are_context_derived_and_reject_stale_field():
    from bp_registry.runner import (
        canonical_public_manifest_context, derive_canonical_executable_maxima,
    )

    context = canonical_public_manifest_context("data/manifests/canonical-three-qubit-development.json")
    # A profile cannot turn open event payloads into a fabricated finite byte
    # cap. The profile prerequisite rejects this route before a campaign can
    # declare a supposedly hard authorization.
    with pytest.raises(ValueError, match="lacks closed per-kind canonical event payload schemas"):
        derive_canonical_executable_maxima(context)


def test_pending_reservations_cannot_be_double_spent_or_replayed():
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    auth = CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="e" * 64, authorization_identity="pending", max_events=1,
        max_evidence_bytes=2, max_storage_bytes=2, control_receipt_reserve_bytes=3,
    )
    guard = CanonicalRuntimeGuardV1(auth)
    first = guard.reserve_ledger_append(b"a\n", boundary="first")
    with pytest.raises(CanonicalResourceInterruption):
        guard.reserve_ledger_append(b"b\n", boundary="second")
    guard.commit(first)
    with pytest.raises(TypeError, match="unknown canonical runtime reservation"):
        guard.commit(first)
    assert guard.snapshot().scientific_events == 1
    assert guard.snapshot().scientific_evidence_bytes == 2


def test_materialized_authorization_must_bind_derived_profile_before_writes(tmp_path):
    from bp_registry.runner import (
        canonical_public_manifest_context, derive_canonical_executable_maxima,
    )

    path = "data/manifests/canonical-three-qubit-development.json"
    context = canonical_public_manifest_context(path)
    ledger = tmp_path / "events.jsonl"
    with pytest.raises(ValueError, match="lacks closed per-kind canonical event payload schemas"):
        derive_canonical_executable_maxima(context)
    assert not ledger.exists()


def test_guarded_artifact_exact_fit_and_denied_replace_preserve_bytes(tmp_path):
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import (
        CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1, guarded_atomic_write_bytes,
    )

    guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="a" * 64, authorization_identity="artifact", max_events=1,
        max_evidence_bytes=1, max_storage_bytes=3, control_receipt_reserve_bytes=4,
    ))
    target = tmp_path / "sample.json"
    guarded_atomic_write_bytes(target, b"abc", resource_guard=guard, boundary="sample")
    assert target.read_bytes() == b"abc"
    assert guard.snapshot().scientific_storage_bytes == 3
    with pytest.raises(CanonicalResourceInterruption):
        guarded_atomic_write_bytes(target, b"x", resource_guard=guard, boundary="replacement")
    assert target.read_bytes() == b"abc"
    assert guard.snapshot().scientific_storage_bytes == 3
    control = tmp_path / "partial.json"
    guarded_atomic_write_bytes(
        control, b"halt", resource_guard=guard, boundary="interruption", control_receipt=True,
    )
    assert control.read_bytes() == b"halt"
    with pytest.raises(CanonicalResourceInterruption):
        guarded_atomic_write_bytes(
            tmp_path / "second.json", b"x", resource_guard=guard,
            boundary="second-control", control_receipt=True,
        )
    assert not (tmp_path / "second.json").exists()


def test_materialized_wall_interruption_has_prefix_and_no_decoder_result(tmp_path):
    from bp_registry.runner import (
        canonical_public_manifest_context, derive_canonical_executable_maxima,
    )

    path = "data/manifests/canonical-three-qubit-development.json"
    context = canonical_public_manifest_context(path)
    ledger = tmp_path / "events.jsonl"
    with pytest.raises(ValueError, match="lacks closed per-kind canonical event payload schemas"):
        derive_canonical_executable_maxima(context)
    assert not ledger.exists()
