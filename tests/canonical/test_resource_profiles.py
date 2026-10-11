"""Executable-profile declarations are derived, closed, and tamper evident."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _profile(path: str | Path):
    from bp_registry.runner import canonical_public_manifest_context, derive_canonical_executable_maxima

    return derive_canonical_executable_maxima(canonical_public_manifest_context(path))


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


def test_registered_profiles_cover_baseline_local_relay_phase5_and_v7(tmp_path):
    baseline = _profile("data/manifests/canonical-three-qubit-development.json")
    local = _profile("data/manifests/phase3-hsu-group-pilot.json")
    relay = _profile("data/manifests/phase4-memory-relay-b1.json")

    campaign = json.loads(Path("data/manifests/phase5-b1-calibration.json").read_text())
    assert isinstance(campaign["arm_manifests"], dict)
    phase5_path = tmp_path / "phase5.json"
    phase5_path.write_text(json.dumps(campaign["arm_manifests"]["guided_decimation"]))
    phase5 = _profile(phase5_path)

    v7_list_path = tmp_path / "v7-list.json"
    v7_list_path.write_text(json.dumps(_v7(vote=False)))
    v7_vote_path = tmp_path / "v7-vote.json"
    v7_vote_path.write_text(json.dumps(_v7(vote=True)))
    v7_list, v7_vote = _profile(v7_list_path), _profile(v7_vote_path)

    assert (baseline.route, local.route, relay.route, phase5.route) == (
        "baseline", "local:group_shuffled", "relay", "phase5",
    )
    assert (v7_list.route, v7_vote.route) == ("v7-list", "v7-vote")
    # Coordinate ballots are a distinct reachable V7 event class and cannot
    # silently inherit the list profile.
    assert v7_vote.max_ledger_events_per_unit > v7_list.max_ledger_events_per_unit
    for profile in (baseline, local, relay, phase5, v7_list, v7_vote):
        assert profile.derived_work_per_unit == profile.max_decoder_iterations * profile.work_per_iteration
        assert profile.derived_events_per_unit == profile.max_ledger_events_per_unit
        assert profile.derived_evidence_bytes_per_unit == (
            profile.max_ledger_events_per_unit * profile.serializer_bytes_per_event
            + profile.partial_receipt_reserve_bytes
        )
        assert profile.derived_storage_bytes_per_unit == (
            profile.artifact_storage_bytes_per_unit + profile.derived_evidence_bytes_per_unit
        )


def test_each_profile_field_and_digest_is_exactly_verified():
    from bp_registry.runner import verify_declared_executable_limits

    profile = _profile("data/manifests/canonical-three-qubit-development.json")
    pristine = profile.as_evidence()
    verify_declared_executable_limits(
        pristine, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
    )
    for field, value in pristine.items():
        altered = dict(pristine)
        altered[field] = ("0" * 64 if isinstance(value, str) else value - 1)
        with pytest.raises(ValueError, match=field):
            verify_declared_executable_limits(
                altered, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
            )
    missing = dict(pristine)
    missing.pop("derived_storage_bytes_per_unit")
    with pytest.raises(ValueError, match="extra or missing"):
        verify_declared_executable_limits(
            missing, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
        )
    extra = {**pristine, "untrusted_multiplier": 1}
    with pytest.raises(ValueError, match="extra or missing"):
        verify_declared_executable_limits(
            extra, expected_policy_binding=profile.policy_binding_sha256, derived=profile,
        )
    with pytest.raises(ValueError, match="policy_binding_sha256"):
        verify_declared_executable_limits(
            pristine, expected_policy_binding="0" * 64, derived=profile,
        )


def test_unregistered_postprocessor_route_fails_closed(tmp_path):
    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 8
    value["postprocessing_config"] = {"enabled": False}
    path = tmp_path / "unregistered-v8.json"
    path.write_text(json.dumps(value))

    with pytest.raises(ValueError, match="unregistered canonical manifest route"):
        _profile(path)
