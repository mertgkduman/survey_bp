"""Behavioral contracts for the persisted canonical policy composition."""

from __future__ import annotations

import json

import pytest

from bp_registry.canonical import contracts


ROLES = (
    "update",
    "schedule",
    "state_memory",
    "intervention",
    "stopping",
    "selection",
    "postprocessing",
)


def composition_payload() -> dict[str, object]:
    return {
        role: {
            "kind": "identity",
            "binding_id": f"{role}-identity",
            "state_lifetime": "attempt",
            "owned_state": [],
            "requires": [],
            "provides": [],
        }
        for role in ROLES
    }


def manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 2,
        "run_id": "canonical-contract-fixture",
        "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 3,
        "error_rate": 0.1,
        "policies": composition_payload(),
    }


def test_complete_composition_is_explicit_frozen_and_deterministic():
    parsed = contracts.parse_canonical_manifest(manifest_payload())

    assert tuple(parsed.policies.model_dump(mode="json")) == ROLES
    assert parsed.policies.update.binding_id == "update-identity"
    assert parsed.model_dump_json() == contracts.parse_canonical_manifest(
        json.loads(parsed.model_dump_json())
    ).model_dump_json()


def test_missing_role_unknown_kind_and_persisted_extras_fail_closed():
    missing = manifest_payload()
    missing["policies"].pop("postprocessing")
    with pytest.raises(ValueError):
        contracts.parse_canonical_manifest(missing)

    unknown = manifest_payload()
    unknown["policies"]["update"]["kind"] = "untrusted.module:callable"
    with pytest.raises(ValueError, match="known policy kind"):
        contracts.parse_canonical_manifest(unknown)

    extra = manifest_payload()
    extra["policies"]["selection"]["callable"] = "eval"
    with pytest.raises(ValueError):
        contracts.parse_canonical_manifest(extra)


def test_duplicate_binding_capability_ownership_and_invalid_hook_are_rejected():
    duplicate = manifest_payload()
    duplicate["policies"]["schedule"]["binding_id"] = "update-identity"
    with pytest.raises(ValueError, match="binding_id"):
        contracts.parse_canonical_manifest(duplicate)

    overlap = manifest_payload()
    overlap["policies"]["update"]["owned_state"] = ["messages"]
    overlap["policies"]["schedule"]["owned_state"] = ["messages"]
    with pytest.raises(ValueError, match="owned state"):
        contracts.parse_canonical_manifest(overlap)

    unsupported = manifest_payload()
    unsupported["policies"]["schedule"]["hook"] = "message"
    with pytest.raises(ValueError, match="hook"):
        contracts.parse_canonical_manifest(unsupported)


def test_resolved_composition_is_closed_and_exposes_typed_contracts():
    parsed = contracts.parse_canonical_manifest(manifest_payload())

    assert hasattr(contracts, "PolicyRole")
    assert hasattr(contracts, "PolicyBinding")
    assert hasattr(contracts, "validate_composition")
    resolved = contracts.validate_composition(parsed.policies)
    assert tuple(binding.role.value for binding in resolved.bindings) == ROLES
    assert resolved.semantic_identity == contracts.validate_composition(parsed.policies).semantic_identity


def test_lifecycle_owns_policy_state_and_rejects_unauthorized_decisions():
    from bp_registry.canonical import execution

    parsed = contracts.parse_canonical_manifest(manifest_payload())
    resolved = contracts.validate_composition(parsed.policies)

    assert hasattr(execution, "PolicyRuntime")
    assert hasattr(contracts, "PolicyDecision")
    runtime = execution.PolicyRuntime(resolved)
    visited = runtime.traverse_lifecycle()
    assert tuple(event.hook.value for event in visited) == (
        "shot", "search", "member", "leg", "branch", "attempt", "iteration", "message",
    )

    first = runtime.private_state("update-identity", sibling_id="member-a")
    second = runtime.private_state("update-identity", sibling_id="member-b")
    assert first is not second
    with pytest.raises(ValueError, match="does not own"):
        runtime.apply_decision(
            contracts.PolicyDecision(
                binding_id="schedule-identity", hook="iteration", action="state_update",
                state_updates={"foreign": 1},
            )
        )


def test_search_relationship_topology_and_relay_transfer_are_typed_separately():
    assert hasattr(contracts, "SearchRelationship")
    assert hasattr(contracts, "ExecutionTopology")
    assert hasattr(contracts, "RelayPayload")

    plan = contracts.SearchPlan(
        relationship="relayed", topology="sequential", budget_scope="search",
        relay_payload={"kind": "canonical-relay-v1", "values": [1, 0]},
    )
    assert plan.relationship.value == "relayed"
    assert plan.topology.value == "sequential"
    with pytest.raises(ValueError, match="relay payload"):
        contracts.SearchPlan(
            relationship="independent", topology="concurrent", budget_scope="search",
            relay_payload={"kind": "canonical-relay-v1", "values": [1]},
        )


def test_resolved_bindings_carry_complete_adjacent_evidence():
    resolved = contracts.validate_composition(
        contracts.parse_canonical_manifest(manifest_payload()).policies
    )
    assert all(binding.evidence.invariants for binding in resolved.bindings)
    assert all(binding.evidence.procedure or binding.evidence.source_anchors for binding in resolved.bindings)


def test_v3_generated_assignment_requires_closed_generator_and_refresh_models():
    generated = contracts.PolicySpecV3.model_validate({
        "kind": "offset_min_sum", "binding_id": "update-oms-generator", "state_lifetime": "attempt",
        "owned_state": [], "requires": [], "provides": [],
        "parameter_generator": {
            "shape": "check", "graph_sha256": "a" * 64, "distribution": "uniform",
            "low": 0.0, "high": 1.0, "root_seed_identity": "b" * 64,
        },
        "parameter_refresh": {"scope": "attempt"},
    })
    assert generated.parameter_generator is not None
    assert generated.parameter_refresh is not None
    with pytest.raises(ValueError, match="parameter_generator"):
        contracts.PolicySpecV3.model_validate({
            "kind": "offset_min_sum", "binding_id": "update-oms-invalid", "state_lifetime": "attempt",
            "owned_state": [], "requires": [], "provides": [],
            "parameter_refresh": {"scope": "attempt"},
        })
