"""Audited route inventories and fail-closed executable-profile declarations."""

from __future__ import annotations

import json
from pathlib import Path

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


def test_registered_route_event_inventory_counts_actual_emission_families(tmp_path):
    baseline = _route_inventory(_context("data/manifests/canonical-three-qubit-development.json"))
    local = _route_inventory(_context("data/manifests/phase3-hsu-group-pilot.json"))
    relay = _route_inventory(_context("data/manifests/phase4-memory-relay-b1.json"))

    campaign = json.loads(Path("data/manifests/phase5-b1-calibration.json").read_text())
    assert isinstance(campaign["arm_manifests"], dict)
    phase5_path = tmp_path / "phase5-guided.json"
    phase5_path.write_text(json.dumps(campaign["arm_manifests"]["guided_decimation"]))
    phase5 = _route_inventory(_context(phase5_path))

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
    assert phase5[3]["attempt_original_check"] == 16
    # MBBP work leaves are emitted for every completed local-member step plus
    # its original check. Vote ballots are one event per admitted member,
    # each carrying the whole coordinate vector.
    assert v7_list[0] == "v7-list" and v7_list[3]["work_leaf"] > 2
    assert v7_vote[0] == "v7-vote" and v7_vote[3]["vote_ballot"] == 2
    assert v7_vote[3]["vote_aggregate"] == 1


@pytest.mark.parametrize("path", [
    "data/manifests/canonical-three-qubit-development.json",
    "data/manifests/phase3-hsu-group-pilot.json",
    "data/manifests/phase4-memory-relay-b1.json",
])
def test_serializer_bound_fails_closed_until_event_payload_schemas_are_bounded(path):
    from bp_registry.runner import derive_canonical_executable_maxima

    with pytest.raises(ValueError, match="lacks closed per-kind canonical event payload schemas"):
        derive_canonical_executable_maxima(_context(path))


def _declared_profile():
    from bp_registry.runner import CanonicalExecutableMaximaV1

    return CanonicalExecutableMaximaV1(
        "v1", "fixture", "1" * 64, "2" * 64, "3" * 64, "4" * 64, "5" * 64,
        2, 3, 5, 7, 11, 13, 6, 5, 48, 59,
    )


def test_declaration_verifier_rejects_stale_and_understated_plan16_receipt_fields():
    from bp_registry.campaigns.contracts import FailureCountExecutableLimitReceiptV1
    from bp_registry.runner import verify_declared_executable_limits

    profile = _declared_profile()
    declared = profile.as_evidence()
    receipt = FailureCountExecutableLimitReceiptV1.model_validate({
        "schema": "failure_count_executable_limit_receipt_v1", **declared,
    })
    assert receipt.derived_storage_bytes_per_unit == 59
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


def test_artifact_layout_and_control_reserve_fail_closed_without_bounded_schemas():
    from bp_registry.canonical.schedules import EdgeTable
    from bp_registry.runner import _artifact_layout_bytes, _neutral_interruption_reserve

    context = _context("data/manifests/canonical-three-qubit-development.json")
    with pytest.raises(ValueError, match="closed materialized-sample and engine-result artifact layout"):
        _artifact_layout_bytes(context.manifest, EdgeTable.from_check_matrix(context.code.hz))
    with pytest.raises(ValueError, match="bounded interruption-control receipt schema"):
        _neutral_interruption_reserve(context.manifest)


def test_unregistered_beam_route_fails_closed(tmp_path):
    from bp_registry.runner import derive_canonical_executable_maxima

    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 8
    value["postprocessing_config"] = {"enabled": False}
    path = tmp_path / "unregistered-v8.json"
    path.write_text(json.dumps(value))

    with pytest.raises(ValueError, match="unregistered canonical manifest route"):
        derive_canonical_executable_maxima(_context(path))
