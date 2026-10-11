"""Route inventories and explicit guarded resource-profile declarations."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _context(path: str | Path):
    from bp_registry.runner import canonical_public_manifest_context

    return canonical_public_manifest_context(path)


def _route_inventory(context: object) -> tuple[str, int, int, dict[str, int]]:
    from bp_registry.canonical.schedules import EdgeTable
    from bp_registry.runner import _registered_canonical_route, _route_dimensions

    manifest = context.manifest
    route, _ = _registered_canonical_route(manifest)
    iterations, work, inventory = _route_dimensions(
        manifest, EdgeTable.from_check_matrix(context.code.hz), route,
    )
    return route, iterations, work, inventory


def _v7(*, vote: bool) -> dict[str, object]:
    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 7
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    policies = value["policies"]
    assert isinstance(policies, dict)
    policies["update"].update({"kind": "normalized_min_sum", "parameter_assignment": {"shape": "scalar", "value": 0.875}})
    policies["schedule"].update({"kind": "check_node_serial"})
    policies["state_memory"].update({"kind": "identity"})
    value["ensemble"] = {
        "kind": "mbbp_ld", "source_status": "canonical_adaptation", "member_state": "independent",
        "max_iterations": 8, "max_member_c2v_updates": 100, "max_total_members": 2,
        "no_member_terminal": "no_member_converged_zero_return",
        "bases": [
            {"member_id": "member-0", "local_ordinal": 0, "partition_identity": "p0",
             "permutation_identity": "q0", "transform_kind": "one_hot_original_check_rows",
             "redundant_transforms": [[1]]},
            {"member_id": "member-1", "local_ordinal": 1, "partition_identity": "p1",
             "permutation_identity": "q1", "transform_kind": "one_hot_original_check_rows",
             "redundant_transforms": [[1]]},
        ],
    }
    value["list_selection"] = {"kind": "frequency_over_weight_plus_one", "tie_rule": "local_ordinal_then_lineage"}
    if vote:
        value["vote"] = {"object": "correction_bits", "electorate_rule": "admitted_members",
                         "aggregation": "coordinate_majority", "tie_bit": 1}
    return value


def _phase5_guided(tmp_path: Path, *, damped: bool = False) -> Path:
    campaign = json.loads(Path("data/manifests/phase5-b1-p005-damping-pilot-v2.json").read_text())
    assert isinstance(campaign["arm_manifests"], dict)
    path = tmp_path / ("phase6-yao-guided.json" if damped else "phase5-guided.json")
    path.write_text(json.dumps(campaign["arm_manifests"]["guided_decimation__damped" if damped else "guided_decimation"]))
    return path


def test_registered_route_event_inventory_counts_actual_emission_families(tmp_path):
    baseline = _route_inventory(_context("data/manifests/canonical-three-qubit-development.json"))
    local = _route_inventory(_context("data/manifests/phase3-hsu-group-pilot.json"))
    relay = _route_inventory(_context("data/manifests/phase4-memory-relay-b1.json"))
    phase5 = _route_inventory(_context(_phase5_guided(tmp_path)))

    v7_list_path = tmp_path / "v7-list.json"
    v7_list_path.write_text(json.dumps(_v7(vote=False)))
    v7_vote_path = tmp_path / "v7-vote.json"
    v7_vote_path.write_text(json.dumps(_v7(vote=True)))
    v7_list, v7_vote = _route_inventory(_context(v7_list_path)), _route_inventory(_context(v7_vote_path))

    assert baseline[0] == "baseline" and sum(baseline[3].values()) == 8
    assert local[0] == "local:group_shuffled" and sum(local[3].values()) == 8
    assert relay[0] == "relay" and relay[3]["relay_transfer"] == 1
    assert phase5[0] == "phase5:guided_decimation"
    assert phase5[3]["transform"] == phase5[3]["attempt"] == phase5[3]["lift"] == 16
    assert phase5[3]["original_check"] == 17
    assert v7_list[0] == "v7-list" and v7_list[3]["work_leaf"] > 2
    assert v7_vote[0] == "v7-vote" and v7_vote[3]["vote_ballot"] == 2
    assert v7_vote[3]["vote_exclusion"] == 2
    assert v7_vote[3]["vote_aggregate"] == 1


def test_registered_route_profiles_bind_versioned_guarded_ceilings(tmp_path):
    from bp_registry.ledger import CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1, canonical_serializer_descriptor
    from bp_registry.runner import (
        CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1,
        derive_canonical_executable_maxima,
    )

    v7_list_path = tmp_path / "v7-list.json"
    v7_list_path.write_text(json.dumps(_v7(vote=False)))
    v7_vote_path = tmp_path / "v7-vote.json"
    v7_vote_path.write_text(json.dumps(_v7(vote=True)))
    contexts = [
        _context("data/manifests/canonical-three-qubit-development.json"),
        _context("data/manifests/phase3-hsu-group-pilot.json"),
        _context("data/manifests/phase4-memory-relay-b1.json"),
        _context(_phase5_guided(tmp_path)), _context(_phase5_guided(tmp_path, damped=True)),
        _context(v7_list_path), _context(v7_vote_path),
    ]
    routes = [derive_canonical_executable_maxima(context) for context in contexts]

    assert [profile.route for profile in routes] == [
        "baseline", "local:group_shuffled", "relay", "phase5:guided_decimation",
        "phase5:guided_decimation", "v7-list", "v7-vote",
    ]
    assert all(profile.serializer_bytes_per_event == CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1 for profile in routes)
    assert all(profile.artifact_storage_bytes_per_unit == 2 * CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1 for profile in routes)
    assert all(profile.partial_receipt_reserve_bytes == CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1 for profile in routes)
    assert all(profile.derived_evidence_bytes_per_unit == (
        profile.max_ledger_events_per_unit * CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1
        + CANONICAL_GUARDED_CONTROL_RECEIPT_BYTE_CEILING_V1
    ) for profile in routes)
    assert all(profile.derived_storage_bytes_per_unit == (
        profile.artifact_storage_bytes_per_unit + profile.derived_evidence_bytes_per_unit
    ) for profile in routes)
    descriptor = canonical_serializer_descriptor(structural_event_version=2)
    assert descriptor["guarded_event_ceiling"] == {
        "schema": "canonical-guarded-event-ceiling-v1",
        "max_framed_bytes": CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1,
        "enforcement": "runtime_guard.reserve_ledger_append.exact_framed_bytes",
    }


def test_declaration_verifier_rejects_each_stale_or_understated_plan16_field():
    from bp_registry.campaigns.contracts import FailureCountExecutableLimitReceiptV1
    from bp_registry.runner import derive_canonical_executable_maxima, verify_declared_executable_limits

    profile = derive_canonical_executable_maxima(_context("data/manifests/canonical-three-qubit-development.json"))
    declared = profile.as_evidence()
    receipt = FailureCountExecutableLimitReceiptV1.model_validate({
        "schema": "failure_count_executable_limit_receipt_v1", **declared,
    })
    assert receipt.derived_storage_bytes_per_unit == profile.derived_storage_bytes_per_unit
    verify_declared_executable_limits(
        declared, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
    )
    for field, value in declared.items():
        altered = dict(declared)
        altered[field] = ("0" * 64 if isinstance(value, str) else value - 1)
        with pytest.raises(ValueError, match=field):
            verify_declared_executable_limits(
                altered, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
            )
    with pytest.raises(ValueError, match="extra or missing"):
        verify_declared_executable_limits(
            {**declared, "untrusted_multiplier": 1},
            expected_policy_binding=profile.policy_binding_sha256, derived=profile,
        )


def test_serializer_bound_accepts_exact_fit_and_denies_before_writer_mutation(tmp_path):
    from bp_registry.ledger import CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1, CanonicalEventWriter, CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    ceiling = CANONICAL_GUARDED_EVENT_BYTE_CEILING_V1
    guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="a" * 64, authorization_identity="profile-ceiling", max_events=2,
        max_evidence_bytes=ceiling, max_storage_bytes=ceiling,
        control_receipt_reserve_bytes=1, max_event_bytes=ceiling,
    ))
    exact = guard.reserve_ledger_append(b"x" * (ceiling - 1) + b"\n", boundary="exact")
    guard.commit(exact)
    assert guard.snapshot().scientific_evidence_bytes == ceiling

    path = tmp_path / "events.jsonl"
    over_guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="b" * 64, authorization_identity="profile-ceiling-over", max_events=2,
        max_evidence_bytes=ceiling + 1, max_storage_bytes=ceiling + 1,
        control_receipt_reserve_bytes=1, max_event_bytes=ceiling,
    ))
    with CanonicalEventWriter(path, resource_guard=over_guard) as writer:
        with pytest.raises(CanonicalResourceInterruption, match="resource cap"):
            writer.begin(run_id="r", shot_id=0, sample_seed_identity="s", payload="x" * ceiling)
    snapshot = over_guard.snapshot()
    assert snapshot.interruption_kind == "unsupported_event_payload"
    assert snapshot.scientific_events == snapshot.scientific_evidence_bytes == snapshot.scientific_storage_bytes == 0
    assert not path.exists() or path.read_bytes() == b""


def test_artifact_layout_trace_larger_than_registered_ceiling_fails_closed():
    from bp_registry.runner import (
        CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1,
        _artifact_layout_bytes,
    )

    manifest = SimpleNamespace(trace_plan=SimpleNamespace(
        level="full", max_bytes=CANONICAL_GUARDED_ARTIFACT_BYTE_CEILING_V1 + 1,
    ))
    with pytest.raises(ValueError, match="trace plan exceeds"):
        _artifact_layout_bytes(manifest, table=None)

def test_unregistered_beam_route_fails_closed(tmp_path):
    from bp_registry.runner import derive_canonical_executable_maxima

    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 8
    value["postprocessing_config"] = {"enabled": False}
    path = tmp_path / "unregistered-v8.json"
    path.write_text(json.dumps(value))

    with pytest.raises(ValueError, match="unregistered canonical manifest route"):
        derive_canonical_executable_maxima(_context(path))
