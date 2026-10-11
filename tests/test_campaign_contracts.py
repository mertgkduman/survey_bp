"""Adversarial coverage for frozen campaign assessment contracts."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError


def test_work_plan_distinguishes_accepted_physical_sample_namespaces() -> None:
    from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan

    coordinates = tuple(
        CampaignCoordinateV1(
            cohort_id="cohort", point_id="point", sample_namespace=namespace,
            sample_ids=(7,),
        )
        for namespace in ("source-a", "source-b")
    )
    plan = freeze_work_plan(
        campaign_spec_digest="a" * 64, coordinates=coordinates,
        arm_seed_identities={"bp": "seed"}, look_sample_boundaries=(2,),
        units_per_shard=1,
    )
    assert len(plan.units) == 2
    assert len(set(plan.unit_keys)) == 2
    assert len({unit.physical_sample_identity for unit in plan.units}) == 2


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
        "resources": {"max_shots": 100, "max_looks": 1, "max_batch_size": 20, "max_decoder_work": 10000, "max_events": 1000, "max_evidence_bytes": 1000000, "max_storage_bytes": 2000000},
    }


def _failure_count_payload() -> dict[str, object]:
    """A bounded Yao-style design with a realized target-th-failure receipt."""
    payload = _assessment_payload()
    payload.update(
        {
            "interval": {
                "method": "exact_inverse_binomial",
                "confidence_level": 0.95,
                "stopping_event": "decoder_logical_failure_v1",
                "target_failures": 100,
                "inferential_trials": 117,
                "inferential_prefix_sha256": _hash("b"),
                "authorized_tail_count": 3,
                "authorized_tail_sha256": _hash("c"),
            },
            "stopping": {
                "mode": "failure_count",
                "target_failures": 100,
                "batch_size": 20,
                "shot_order": "campaign_cohort_point_sample_ordinal_v1",
                "failure_event": "decoder_logical_failure_v1",
                "terminal_batch_authorization_sha256": _hash("d"),
                "cap_authorization_sha256": _hash("e"),
                "terminal_state": "target_reached",
                "terminal_failure_ordinal": 117,
                "cumulative_failures_before_terminal": 99,
                "cumulative_failures_at_terminal": 100,
                "authorized_tail_ordinals": [118, 119, 120],
            },
            "decision_rule": {
                "rule": "multiplicative_target_interval_containment_v1",
                "factor": 1.5,
            },
            "resources": {
                "max_shots": 200,
                "max_looks": 1,
                "max_batch_size": 20,
                "max_decoder_work": 10000,
                "max_events": 1000,
                "max_evidence_bytes": 1000000,
                "max_storage_bytes": 2000000,
            },
        }
    )
    return payload


def test_campaign_assessment_is_strict_and_digest_bound():
    from bp_registry.campaigns import contracts

    assert hasattr(contracts, "CampaignAssessmentV1"), "strict campaign assessment contract must be public"
    CampaignAssessmentV1 = contracts.CampaignAssessmentV1

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


def test_stopping_rejects_fixed_interim_look_and_unbounded_alpha_spending():
    from bp_registry.campaigns.contracts import CampaignAssessmentV1, CampaignSpecV1
    from test_campaign_execution import _spec_payload

    fixed_campaign = _spec_payload()
    fixed_campaign["assessment"] = _assessment_payload()
    fixed_campaign["final_look"] = 2
    with pytest.raises(ValidationError):
        CampaignSpecV1.model_validate(fixed_campaign)

    finite = _assessment_payload(mode="finite_look")
    finite["resources"]["max_looks"] = 2
    finite["stopping"]["alpha_allocations"] = [
        {"family_id": "primary", "target_id": "curve-p100", "look": 40, "alpha": 0.03},
        {"family_id": "primary", "target_id": "curve-p100", "look": 100, "alpha": 0.03},
    ]
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(finite)


def test_failure_count_stopping_binds_ordered_prefix_tail_and_censoring():
    from bp_registry.campaigns import contracts

    assert hasattr(contracts, "FailureCountStoppingV1"), "failure-count stopping must be a public strict contract"
    FailureCountStoppingV1 = contracts.FailureCountStoppingV1

    payload = _failure_count_payload()
    stopping = FailureCountStoppingV1.model_validate(payload["stopping"])
    assert stopping.mode == "failure_count"
    assert stopping.shot_order == "campaign_cohort_point_sample_ordinal_v1"
    assert stopping.terminal_failure_ordinal == 117
    assert stopping.cumulative_failures_before_terminal == 99
    assert stopping.cumulative_failures_at_terminal == 100
    assert stopping.authorized_tail_ordinals == (118, 119, 120)

    tail_outside_terminal_batch = copy.deepcopy(payload["stopping"])
    tail_outside_terminal_batch["authorized_tail_ordinals"] = [118, 121]
    with pytest.raises(ValidationError):
        FailureCountStoppingV1.model_validate(tail_outside_terminal_batch)

    outcome_dependent_order = copy.deepcopy(payload["stopping"])
    outcome_dependent_order["shot_order"] = "completion_order"
    with pytest.raises(ValidationError):
        FailureCountStoppingV1.model_validate(outcome_dependent_order)

    censored = copy.deepcopy(payload["stopping"])
    censored.update(
        {
            "terminal_state": "cap_censored",
            "terminal_failure_ordinal": None,
            "cumulative_failures_before_terminal": None,
            "cumulative_failures_at_terminal": 99,
            "authorized_tail_ordinals": [],
        }
    )
    assert FailureCountStoppingV1.model_validate(censored).terminal_state == "cap_censored"


def test_failure_count_assessment_requires_inverse_binomial_and_multiplicative_rule():
    from bp_registry.campaigns import contracts

    assert hasattr(contracts, "ExactInverseBinomialIntervalV1"), "inverse-binomial intervals must be explicit"
    assert hasattr(contracts, "MultiplicativeTargetRuleV1"), "multiplicative target rules must be explicit"
    CampaignAssessmentV1 = contracts.CampaignAssessmentV1

    payload = _failure_count_payload()
    assessment = CampaignAssessmentV1.model_validate(payload)
    assert assessment.interval.method == "exact_inverse_binomial"
    assert assessment.interval.inferential_trials == assessment.stopping.terminal_failure_ordinal
    assert assessment.interval.authorized_tail_count == len(assessment.stopping.authorized_tail_ordinals)
    assert assessment.decision_rule.factor == 1.5

    tail_as_trials = copy.deepcopy(payload)
    tail_as_trials["interval"]["inferential_trials"] = 120
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(tail_as_trials)

    bad_factor = copy.deepcopy(payload)
    bad_factor["decision_rule"]["factor"] = 1.0
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(bad_factor)

    fixed_with_inverse = _assessment_payload()
    fixed_with_inverse["interval"] = payload["interval"]
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(fixed_with_inverse)

    finite_with_inverse = _assessment_payload(mode="finite_look")
    finite_with_inverse["resources"]["max_looks"] = 2
    finite_with_inverse["stopping"]["alpha_allocations"] = [
        {"family_id": "primary", "target_id": "curve-p100", "look": 40, "alpha": 0.025},
        {"family_id": "primary", "target_id": "curve-p100", "look": 100, "alpha": 0.025},
    ]
    finite_with_inverse["interval"] = payload["interval"]
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(finite_with_inverse)

    censored = copy.deepcopy(payload)
    censored["stopping"].update(
        {
            "terminal_state": "cap_censored",
            "terminal_failure_ordinal": None,
            "cumulative_failures_before_terminal": None,
            "cumulative_failures_at_terminal": 99,
            "authorized_tail_ordinals": [],
        }
    )
    censored["interval"] = None
    assert CampaignAssessmentV1.model_validate(censored).interval is None


def test_outcome_denominator_matrix_is_total_and_interruption_stays_partial():
    from bp_registry.campaigns.contracts import CampaignAssessmentV1

    uncovered = _assessment_payload()
    uncovered["outcome_matrix"]["treatments"].pop()
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(uncovered)

    dropped_interruption = _assessment_payload()
    dropped_interruption["outcome_matrix"]["treatments"][-1] = {
        "terminal_status": "infrastructure_interruption",
        "all_shot": "failure",
        "conditional": "excluded",
    }
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(dropped_interruption)


def test_finite_look_requires_complete_declared_alpha_grid():
    from bp_registry.campaigns.contracts import CampaignAssessmentV1

    finite = _assessment_payload(mode="finite_look")
    finite["resources"]["max_looks"] = 2
    finite["stopping"]["alpha_allocations"] = [
        {"family_id": "primary", "target_id": "curve-p100", "look": 40, "alpha": 0.025},
        {"family_id": "primary", "target_id": "curve-p100", "look": 100, "alpha": 0.025},
    ]
    assert CampaignAssessmentV1.model_validate(finite).stopping.mode == "finite_look"

    finite["stopping"]["alpha_allocations"].pop()
    with pytest.raises(ValidationError):
        CampaignAssessmentV1.model_validate(finite)


def test_prospective_failure_count_has_no_terminal_facts_and_limits_are_derived():
    from bp_registry.campaigns.contracts import (
        FailureCountBatchAuthorizationV1,
        FailureCountCampaignCapsV1,
        FailureCountExecutableLimitReceiptV1,
        FailureCountPolicyV1,
        InverseBinomialProcedureV1,
        MultiplicativeTargetRuleV1,
    )

    limits = FailureCountExecutableLimitReceiptV1(
        schema="failure_count_executable_limit_receipt_v1",
        derivation_version="v1",
        manifest_dimensions_sha256="1" * 64,
        policy_binding_sha256="2" * 64,
        serializer_sha256="3" * 64,
        artifact_layout_sha256="4" * 64,
        verifier_sha256="5" * 64,
        max_decoder_iterations=10,
        work_per_iteration=4,
        max_ledger_events_per_unit=3,
        serializer_bytes_per_event=20,
        artifact_storage_bytes_per_unit=50,
        partial_receipt_reserve_bytes=100,
        derived_work_per_unit=40,
        derived_events_per_unit=3,
        derived_evidence_bytes_per_unit=160,
        derived_storage_bytes_per_unit=210,
    )
    authorization = FailureCountBatchAuthorizationV1(
        schema="failure_count_batch_authorization_v1",
        executable_limit_receipt_sha256=limits.digest(),
        policy_binding_sha256="2" * 64,
        max_local_workers=1,
        max_shots_per_batch=5,
        max_work_per_batch=200,
        max_events_per_batch=15,
        max_evidence_bytes_per_batch=900,
        max_storage_bytes_per_batch=1150,
        monotonic_clock="monotonic_ns_v1",
        per_unit_timeout_ns=1_000,
    )
    policy = FailureCountPolicyV1(
        schema="failure_count_policy_v1",
        policy_binding_sha256="2" * 64,
        campaign_plan_sha256="6" * 64,
        target_failures=2,
        batch_size=5,
        shot_order="campaign_cohort_point_sample_ordinal_v1",
        failure_event="decoder_logical_failure_v1",
        procedure=InverseBinomialProcedureV1(
            method="exact_inverse_binomial", confidence_level=0.95, sidedness="two_sided",
        ),
        multiplicative_rule=MultiplicativeTargetRuleV1(
            rule="multiplicative_target_interval_containment_v1", factor=1.5,
        ),
        caps=FailureCountCampaignCapsV1(
            max_shots=10, max_decoder_work=400, max_events=30,
            max_evidence_bytes=1700, max_storage_bytes=2200, max_wall_seconds=10.0,
        ),
        cap_precedence=("wall", "storage", "evidence", "events", "work", "shots"),
        executable_limits=limits,
        batch_authorization=authorization,
    )
    assert policy.target_failures == 2
    assert policy.executable_limits.derived_evidence_bytes_per_unit == 160
    assert "terminal_state" not in policy.model_dump()
    with pytest.raises(ValidationError, match="extra_forbidden"):
        FailureCountPolicyV1.model_validate({**policy.model_dump(by_alias=True), "terminal_state": "target_reached"})
    with pytest.raises(ValidationError, match="derived"):
        FailureCountExecutableLimitReceiptV1.model_validate(
            {**limits.model_dump(by_alias=True), "derived_work_per_unit": 39},
        )
    with pytest.raises(ValidationError, match="batch"):
        FailureCountPolicyV1.model_validate({
            **policy.model_dump(by_alias=True),
            "batch_authorization": {
                **authorization.model_dump(by_alias=True), "max_events_per_batch": 14,
            },
        })


def test_terminal_receipt_is_post_run_only_and_records_boundary_overshoot():
    from bp_registry.campaigns.contracts import FailureCountTerminalReceiptV1
    receipt = FailureCountTerminalReceiptV1(
        schema="failure_count_terminal_receipt_v1",
        policy_sha256="a" * 64, campaign_plan_sha256="6" * 64,
        executable_limit_receipt_sha256="b" * 64, batch_authorization_sha256="c" * 64,
        terminal_state="target_reached", terminal_failure_ordinal=8,
        cumulative_failures=2, total_completed_shots=10,
        inferential_prefix_sha256="d" * 64, authorized_tail_ordinals=(9, 10),
        authorized_tail_sha256="e" * 64,
        realized_decoder_work=40, realized_events=10,
        realized_evidence_bytes=300, realized_storage_bytes=500,
        wall_boundaries=((1_000, 1_025, 25),),
    )
    assert receipt.wall_boundaries[0][2] == 25
    assert receipt.terminal_failure_ordinal == 8
    with pytest.raises(ValidationError):
        FailureCountTerminalReceiptV1.model_validate(
            {**receipt.model_dump(by_alias=True), "terminal_state": "cap_censored"},
        )
    with pytest.raises(ValidationError):
        FailureCountTerminalReceiptV1.model_validate(
            {**receipt.model_dump(by_alias=True), "wall_boundaries": [(1_000, 999, 0)]},
        )
