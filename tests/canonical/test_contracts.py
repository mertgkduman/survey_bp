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
