"""Adversarial coverage for frozen campaign assessment contracts."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError


def _hash(char: str) -> str:
    return char * 64


def _outcomes() -> list[dict[str, str]]:
    return [
        {"terminal_status": "exact", "all_shot": "success", "conditional": "accepted"},
        {"terminal_status": "stabilizer_equivalent", "all_shot": "success", "conditional": "accepted"},
        {"terminal_status": "wrong_logical_action", "all_shot": "failure", "conditional": "accepted"},
        {"terminal_status": "invalid_syndrome", "all_shot": "failure", "conditional": "excluded"},
        {"terminal_status": "no_proposal", "all_shot": "failure", "conditional": "excluded"},
        {"terminal_status": "nonconvergence", "all_shot": "failure", "conditional": "excluded"},
        {"terminal_status": "timeout", "all_shot": "failure", "conditional": "excluded"},
        {"terminal_status": "postselected_rejection", "all_shot": "failure", "conditional": "excluded"},
        {"terminal_status": "infrastructure_interruption", "all_shot": "incomplete", "conditional": "incomplete"},
    ]


def _assessment_payload(*, mode: str = "fixed_shot") -> dict[str, object]:
    stopping: dict[str, object]
    if mode == "fixed_shot":
        stopping = {"mode": mode, "final_shots": 100, "batch_size": 20}
    else:
        stopping = {
            "mode": mode,
            "cumulative_looks": [40, 100],
            "batch_sizes": [20, 20],
            "minimum_terminal_shots": 40,
            "stop_rule": "all_primary_decisions_resolved_or_maximum_reached",
        }
    return {
        "schema": "campaign_assessment_v1",
        "targets": [{"target_id": "curve-p100", "target_receipt_sha256": _hash("a"), "lower": 0.01, "upper": 0.03, "absolute_tolerance": 0.01}],
        "interval": {"method": "exact_clopper_pearson", "confidence_level": 0.95},
        "families": [{"family_id": "primary", "alpha": 0.05, "member_target_ids": ["curve-p100"]}],
        "stopping": stopping,
        "outcome_matrix": {"rule_id": "all_shot_v1", "treatments": _outcomes()},
        "decision_rule": "target_interval_containment_v1",
        "resources": {"max_shots": 100, "max_looks": 2, "max_batch_size": 20, "max_decoder_work": 10000, "max_events": 1000, "max_evidence_bytes": 1000000, "max_storage_bytes": 2000000},
    }


def test_campaign_assessment_is_strict_and_digest_bound():
    from bp_registry.campaigns.contracts import CampaignAssessmentV1

    payload = _assessment_payload()
    first = CampaignAssessmentV1.model_validate(payload)
    assert first.digest() == CampaignAssessmentV1.model_validate(copy.deepcopy(payload)).digest()

    missing = copy.deepcopy(payload)
    del missing["targets"]
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(missing)

    extra = copy.deepcopy(payload)
    extra["worker_count"] = 64
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(extra)

    drifted = copy.deepcopy(payload)
    drifted["targets"][0]["absolute_tolerance"] = 0.02
    assert CampaignAssessmentV1.model_validate(drifted).digest() != first.digest()


def test_campaign_identity_binds_assessment_but_excludes_executor_observation():
    from bp_registry.campaigns.contracts import CampaignSpecV1
    from test_campaign_execution import _spec_payload

    payload = _spec_payload()
    payload["assessment"] = _assessment_payload()
    first = CampaignSpecV1.model_validate(payload)
    changed = copy.deepcopy(payload)
    changed["assessment"]["resources"]["max_storage_bytes"] = 3000000
    assert CampaignSpecV1.model_validate(changed).digest() != first.digest()

    with pytest.raises(ValidationError):
        CampaignSpecV1.model_validate({**payload, "executor_allocation": {"worker_count": 16}})


def test_campaign_rejects_identity_drift_and_nonfinite_resource_values():
    from bp_registry.campaigns.contracts import CampaignSpecV1, CampaignAssessmentV1
    from test_campaign_execution import _spec_payload

    payload = _spec_payload()
    payload["assessment"] = _assessment_payload()
    bad_hash = copy.deepcopy(payload)
    bad_hash["source_lock_sha256"] = "not-a-digest"
    with pytest.raises(ValidationError):
        CampaignSpecV1.model_validate(bad_hash)

    bad_resource = _assessment_payload()
    bad_resource["resources"]["max_decoder_work"] = float("inf")
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(bad_resource)
