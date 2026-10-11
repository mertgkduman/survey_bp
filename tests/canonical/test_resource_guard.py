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
    from bp_registry.canonical.budgets import WorkVector
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
        guard.after_work(
            "atomic:after_work", committed_work=WorkVector(bp_calls=1, check_to_variable_updates=3),
            leaf_id="attempt:0:sweep:0",
        )
    snapshot = guard.snapshot()
    assert snapshot.interruption_kind == "wall_deadline"
    assert snapshot.overshoot_ns == 2
    assert snapshot.committed_work.bp_calls == 1
    assert snapshot.committed_work.check_to_variable_updates == 3
    assert snapshot.last_work_leaf_id == "attempt:0:sweep:0"
    with pytest.raises(Exception, match="resource cap"):
        guard.before_work("later:before_work")


def test_executable_maxima_are_context_derived_and_reject_stale_field():
    from bp_registry.runner import (
        canonical_public_manifest_context, derive_canonical_executable_maxima,
        verify_declared_executable_limits,
    )

    context = canonical_public_manifest_context("data/manifests/canonical-three-qubit-development.json")
    maxima = derive_canonical_executable_maxima(context)
    declared = maxima.as_evidence()
    verify_declared_executable_limits(
        declared, expected_policy_binding=maxima.policy_binding_sha256, derived=maxima,
    )
    declared["derived_events_per_unit"] = maxima.derived_events_per_unit - 1
    with pytest.raises(ValueError, match="derived_events_per_unit"):
        verify_declared_executable_limits(
            declared, expected_policy_binding=maxima.policy_binding_sha256, derived=maxima,
        )


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
        CanonicalRuntimeAuthorizationV1, CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        canonical_public_manifest_context, derive_canonical_executable_maxima,
        run_canonical_materialized_one,
    )
    from bp_registry.sampling import sample_shot

    path = "data/manifests/canonical-three-qubit-development.json"
    context = canonical_public_manifest_context(path)
    derived = derive_canonical_executable_maxima(context)
    manifest = context.manifest
    anchor = manifest.randomness.physical_sample_identity or context.manifest_sha256
    sample = sample_shot(
        context.code, shot_id=0, seed=0, x_error_rate=manifest.error_rate,
        manifest_identity=anchor,
    )
    ledger = tmp_path / "events.jsonl"
    kwargs = dict(
        authorization_identity="bound-unit", max_events=derived.derived_events_per_unit,
        max_evidence_bytes=derived.derived_evidence_bytes_per_unit,
        max_storage_bytes=derived.derived_storage_bytes_per_unit,
        control_receipt_reserve_bytes=derived.partial_receipt_reserve_bytes,
        max_event_bytes=derived.serializer_bytes_per_event,
        max_artifact_bytes=CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
    )
    wrong = CanonicalRuntimeAuthorizationV1.interruptible_unit(profile_digest="0" * 64, **kwargs)
    with pytest.raises(ValueError, match="profile_digest"):
        run_canonical_materialized_one(
            path, sample=sample, materialized_sample_sha256="f" * 64,
            ledger_path=ledger, runtime_authorization=wrong,
        )
    assert not ledger.exists()
    too_small = CanonicalRuntimeAuthorizationV1(
        profile_digest=derived.digest, mode="strict_full_unit",
        **{**kwargs, "max_events": derived.derived_events_per_unit - 1},
    )
    with pytest.raises(ValueError, match="strict_full_unit"):
        run_canonical_materialized_one(
            path, sample=sample, materialized_sample_sha256="f" * 64,
            ledger_path=ledger, runtime_authorization=too_small,
        )
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


def test_engine_payload_ceiling_rejects_oversized_event_and_artifact_before_write(tmp_path):
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import (
        CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1, guarded_atomic_write_bytes,
    )

    event_guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="f" * 64, authorization_identity="event-ceiling", max_events=2,
        max_evidence_bytes=10, max_storage_bytes=10, control_receipt_reserve_bytes=4,
        max_event_bytes=2, max_artifact_bytes=3,
    ))
    event_guard.commit(event_guard.reserve_ledger_append(b"a\n", boundary="exact-event"))
    with pytest.raises(CanonicalResourceInterruption):
        event_guard.reserve_ledger_append(b"ab\n", boundary="oversize-event")
    snapshot = event_guard.snapshot()
    assert snapshot.interruption_kind == "unsupported_event_payload"
    assert snapshot.scientific_events == 1
    assert snapshot.scientific_evidence_bytes == 2

    artifact_guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="f" * 64, authorization_identity="artifact-ceiling", max_events=2,
        max_evidence_bytes=10, max_storage_bytes=10, control_receipt_reserve_bytes=4,
        max_event_bytes=2, max_artifact_bytes=3,
    ))
    target = tmp_path / "artifact.json"
    guarded_atomic_write_bytes(target, b"abc", resource_guard=artifact_guard, boundary="exact-artifact")
    with pytest.raises(CanonicalResourceInterruption):
        guarded_atomic_write_bytes(
            target, b"abcd", resource_guard=artifact_guard, boundary="oversize-artifact",
        )
    assert target.read_bytes() == b"abc"
    assert artifact_guard.snapshot().interruption_kind == "unsupported_artifact_payload"
    assert artifact_guard.snapshot().scientific_storage_bytes == 3


def test_writer_applies_framed_event_ceiling_before_append(tmp_path):
    from bp_registry.ledger import CanonicalEventWriter, CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    reference = tmp_path / "reference.jsonl"
    with CanonicalEventWriter(reference) as writer:
        writer.begin(run_id="r", shot_id=0, sample_seed_identity="s", note="payload")
    framed = reference.read_bytes()

    def guard(ceiling: int):
        return CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
            profile_digest="f" * 64, authorization_identity=f"event-{ceiling}",
            max_events=1, max_evidence_bytes=len(framed), max_storage_bytes=len(framed),
            control_receipt_reserve_bytes=4, max_event_bytes=ceiling,
        ))

    exact = tmp_path / "exact.jsonl"
    exact_guard = guard(len(framed))
    with CanonicalEventWriter(exact, resource_guard=exact_guard) as writer:
        writer.begin(run_id="r", shot_id=0, sample_seed_identity="s", note="payload")
    assert exact.read_bytes() == framed
    assert exact_guard.snapshot().scientific_evidence_bytes == len(framed)

    denied = tmp_path / "denied.jsonl"
    denied_guard = guard(len(framed) - 1)
    with pytest.raises(CanonicalResourceInterruption):
        with CanonicalEventWriter(denied, resource_guard=denied_guard) as writer:
            writer.begin(run_id="r", shot_id=0, sample_seed_identity="s", note="payload")
    assert not denied.exists() or denied.read_bytes() == b""
    assert denied_guard.snapshot().scientific_evidence_bytes == 0


def test_materialized_wall_interruption_has_prefix_and_no_decoder_result(tmp_path):
    import json

    from bp_registry.runner import (
        CanonicalRuntimeAuthorizationV1, CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        canonical_public_manifest_context, derive_canonical_executable_maxima,
        run_canonical_materialized_one,
    )
    from bp_registry.sampling import sample_shot

    path = "data/manifests/canonical-three-qubit-development.json"
    context = canonical_public_manifest_context(path)
    profile = derive_canonical_executable_maxima(context)
    manifest = context.manifest
    sample = sample_shot(
        context.code, shot_id=0, seed=0, x_error_rate=manifest.error_rate,
        manifest_identity=manifest.randomness.physical_sample_identity or context.manifest_sha256,
    )
    auth = CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest=profile.digest, authorization_identity="expired-unit",
        max_events=profile.derived_events_per_unit,
        max_evidence_bytes=profile.derived_evidence_bytes_per_unit,
        max_storage_bytes=profile.derived_storage_bytes_per_unit,
        control_receipt_reserve_bytes=profile.partial_receipt_reserve_bytes,
        max_event_bytes=profile.serializer_bytes_per_event,
        max_artifact_bytes=CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        monotonic_deadline_ns=0,
    )
    ledger = tmp_path / "events.jsonl"
    result = run_canonical_materialized_one(
        path, sample=sample, materialized_sample_sha256="f" * 64,
        ledger_path=ledger, runtime_authorization=auth,
    )
    assert result.status == "interrupted"
    assert result.terminal is None
    assert result.interruption is not None
    assert result.interruption.snapshot.interruption_kind == "wall_deadline"
    assert all(json.loads(line)["kind"] != "termination" for line in ledger.read_text().splitlines())


def test_strict_profile_authorizes_one_verified_materialized_terminal(tmp_path):
    from bp_registry.ledger import read_canonical_events
    from bp_registry.runner import (
        CanonicalRuntimeAuthorizationV1, CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        canonical_public_manifest_context, derive_canonical_executable_maxima,
        run_canonical_materialized_one,
    )
    from bp_registry.sampling import sample_shot

    path = "data/manifests/canonical-three-qubit-development.json"
    context = canonical_public_manifest_context(path)
    profile = derive_canonical_executable_maxima(context)
    manifest = context.manifest
    sample = sample_shot(
        context.code, shot_id=0, seed=0, x_error_rate=manifest.error_rate,
        manifest_identity=manifest.randomness.physical_sample_identity or context.manifest_sha256,
    )
    authorization = CanonicalRuntimeAuthorizationV1.strict_full_unit(
        profile_digest=profile.digest, authorization_identity="strict-unit",
        max_events=profile.derived_events_per_unit,
        max_evidence_bytes=profile.derived_evidence_bytes_per_unit,
        max_storage_bytes=profile.derived_storage_bytes_per_unit,
        control_receipt_reserve_bytes=profile.partial_receipt_reserve_bytes,
        max_event_bytes=profile.serializer_bytes_per_event,
        max_artifact_bytes=CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        derived_events=profile.derived_events_per_unit,
        derived_evidence_bytes=profile.derived_evidence_bytes_per_unit,
        derived_storage_bytes=profile.derived_storage_bytes_per_unit,
    )
    ledger = tmp_path / "events.jsonl"
    result = run_canonical_materialized_one(
        path, sample=sample, materialized_sample_sha256="f" * 64,
        ledger_path=ledger, runtime_authorization=authorization,
    )
    assert result.status == "terminal"
    assert result.interruption is None
    assert read_canonical_events(ledger)[-1]["kind"] == "termination"
