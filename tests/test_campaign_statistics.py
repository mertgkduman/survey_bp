"""Regression tests for the campaign statistical decision boundary."""

from __future__ import annotations

import math
import importlib

import pytest
from scipy.stats import binomtest

from bp_registry.campaigns.contracts import (
    AssessmentFamilyV1,
    CampaignAssessmentV1,
    ExactIntervalV1,
    FiniteLookStoppingV1,
    LookAlphaAllocationV1,
    OutcomeMatrixV1,
    OutcomeTreatmentV1,
    ScientificResourceCapsV1,
    TargetReferenceV1,
)
_HASH = "a" * 64


def _statistics_api() -> object:
    try:
        return importlib.import_module("bp_registry.campaigns.statistics")
    except ModuleNotFoundError:
        return None


def _exact_binomial_rate(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None, "campaign statistics module must provide exact rates"
    return api.exact_binomial_rate(*args, **kwargs)


def _target_interval_decision(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None, "campaign statistics module must provide target decisions"
    return api.target_interval_decision(*args, **kwargs)


@pytest.mark.parametrize("shots", range(1, 8))
def test_binomial_matches_scipy_for_every_small_count(shots: int) -> None:
    for failures in range(shots + 1):
        result = _exact_binomial_rate(
            failures=failures,
            shots=shots,
            alpha=0.05,
            count_receipt_sha256=_HASH,
        )
        expected = binomtest(failures, shots).proportion_ci(
            confidence_level=0.95,
            method="exact",
        )
        assert result.failures == failures
        assert result.shots == shots
        assert result.estimate == failures / shots
        assert result.interval == pytest.approx((expected.low, expected.high))


def test_zero_failure_keeps_positive_upper_exact_bound() -> None:
    result = _exact_binomial_rate(
        failures=0, shots=10, alpha=0.05, count_receipt_sha256=_HASH,
    )
    assert result.estimate == 0.0
    assert result.interval[0] == 0.0
    assert 0.0 < result.interval[1] < 1.0


def test_all_failure_keeps_subunit_lower_exact_bound() -> None:
    result = _exact_binomial_rate(
        failures=10, shots=10, alpha=0.05, count_receipt_sha256=_HASH,
    )
    assert result.estimate == 1.0
    assert 0.0 < result.interval[0] < 1.0
    assert result.interval[1] == 1.0


@pytest.mark.parametrize("failures,shots", [(0, 0), (-1, 1), (2, 1), (True, 1), (1, True)])
def test_binomial_rejects_invalid_integer_counts(failures: int, shots: int) -> None:
    with pytest.raises(ValueError):
        _exact_binomial_rate(
            failures=failures, shots=shots, alpha=0.05, count_receipt_sha256=_HASH,
        )


def _target() -> TargetReferenceV1:
    return TargetReferenceV1(
        target_id="p050",
        target_receipt_sha256="b" * 64,
        lower=0.30,
        upper=0.40,
        absolute_tolerance=0.05,
    )


def _rate(failures: int, shots: int) -> object:
    return _exact_binomial_rate(
        failures=failures, shots=shots, alpha=0.05, count_receipt_sha256=_HASH,
    )


def test_target_decision_uses_containment_disjointness_and_overlap() -> None:
    target = _target()
    passed = _target_interval_decision(
        _rate(350, 1000), target, input_receipt_hashes={"target": "b" * 64},
    )
    failed = _target_interval_decision(
        _rate(0, 100), target, input_receipt_hashes={"target": "b" * 64},
    )
    inconclusive = _target_interval_decision(
        _rate(25, 100), target, input_receipt_hashes={"target": "b" * 64},
    )
    assert passed.verdict == "pass"
    assert failed.verdict == "fail"
    assert inconclusive.verdict == "inconclusive"
    assert passed.acceptable_interval == pytest.approx((0.25, 0.45))
    assert passed.rule_id == "target_interval_containment_v1"


def test_target_decision_clips_to_probability_domain_and_requires_source_n_when_declared() -> None:
    target = TargetReferenceV1(
        target_id="edge",
        target_receipt_sha256="b" * 64,
        lower=0.0,
        upper=0.02,
        absolute_tolerance=0.10,
    )
    result = _target_interval_decision(
        _rate(0, 100),
        target,
        input_receipt_hashes={"target": "b" * 64},
        source_denominator_required=True,
        source_denominator=None,
    )
    assert result.acceptable_interval == pytest.approx((0.0, 0.12))
    assert result.verdict == "inconclusive"
    assert result.reason == "missing_required_source_denominator"
    assert math.isfinite(result.computed_interval[1])


def _finite_assessment() -> CampaignAssessmentV1:
    target = TargetReferenceV1(
        target_id="p050",
        target_receipt_sha256="b" * 64,
        lower=0.0,
        upper=0.10,
        absolute_tolerance=0.15,
    )
    allocations = tuple(
        LookAlphaAllocationV1(family_id="family", target_id="p050", look=look, alpha=0.01)
        for look in (10, 20)
    )
    treatments = (
        OutcomeTreatmentV1(terminal_status="exact", all_shot="success", conditional="accepted"),
        OutcomeTreatmentV1(terminal_status="stabilizer_equivalent", all_shot="success", conditional="accepted"),
        OutcomeTreatmentV1(terminal_status="wrong_logical_action", all_shot="failure", conditional="accepted"),
        OutcomeTreatmentV1(terminal_status="invalid_syndrome", all_shot="failure", conditional="excluded"),
        OutcomeTreatmentV1(terminal_status="no_proposal", all_shot="failure", conditional="excluded"),
        OutcomeTreatmentV1(terminal_status="nonconvergence", all_shot="failure", conditional="excluded"),
        OutcomeTreatmentV1(terminal_status="timeout", all_shot="failure", conditional="excluded"),
        OutcomeTreatmentV1(terminal_status="postselected_rejection", all_shot="failure", conditional="excluded"),
        OutcomeTreatmentV1(terminal_status="infrastructure_interruption", all_shot="incomplete", conditional="incomplete"),
    )
    return CampaignAssessmentV1(
        schema="campaign_assessment_v1",
        targets=(target,),
        interval=ExactIntervalV1(method="exact_clopper_pearson", confidence_level=0.95),
        families=(AssessmentFamilyV1(family_id="family", alpha=0.05, member_target_ids=("p050",)),),
        stopping=FiniteLookStoppingV1(
            mode="finite_look",
            cumulative_looks=(10, 20),
            batch_sizes=(5, 5),
            minimum_terminal_shots=10,
            stop_rule="all_primary_decisions_resolved_or_maximum_reached",
            alpha_allocations=allocations,
        ),
        outcome_matrix=OutcomeMatrixV1(rule_id="all_shot_v1", treatments=treatments),
        decision_rule="target_interval_containment_v1",
        resources=ScientificResourceCapsV1(
            max_shots=20,
            max_looks=2,
            max_batch_size=5,
            max_decoder_work=100,
            max_events=100,
            max_evidence_bytes=10_000,
            max_storage_bytes=10_000,
        ),
    )


def _finite_look_assessment(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "finite_look_assessment"), (
        "campaign statistics module must provide finite-look assessment"
    )
    return api.finite_look_assessment(*args, **kwargs)


def _look(*, look: int, dispatched: int, realized: int, failures: int) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "FiniteLookObservationV1"), (
        "campaign statistics module must provide finite-look observations"
    )
    return api.FiniteLookObservationV1(
        look=look,
        dispatched_shots=dispatched,
        realized_shots=realized,
        failures_by_target={"p050": failures},
        count_receipt_sha256_by_target={"p050": _HASH},
    )


def test_finite_look_uses_declared_alpha_and_stops_only_after_a_completed_look() -> None:
    result = _finite_look_assessment(
        _finite_assessment(),
        observations=(
            _look(look=10, dispatched=10, realized=10, failures=0),
            _look(look=20, dispatched=20, realized=20, failures=0),
        ),
        input_receipt_hashes={"assessment": "c" * 64},
    )
    assert result.status == "complete"
    assert result.completed_looks == (10, 20)
    assert result.stop_reason == "all_primary_decisions_resolved"
    assert tuple(record.alpha_spent for record in result.look_records) == (0.01, 0.01)
    assert result.look_records[1].target_decisions["p050"].verdict == "pass"


def test_finite_look_retains_whole_completed_batch_overshoot() -> None:
    result = _finite_look_assessment(
        _finite_assessment(),
        observations=(_look(look=10, dispatched=15, realized=15, failures=0),),
        input_receipt_hashes={"assessment": "c" * 64},
    )
    record = result.look_records[0]
    assert result.status == "complete"
    assert record.planned_boundary == 10
    assert record.dispatched_shots == record.realized_shots == 15
    assert record.overshoot == 5


def test_finite_look_partial_batch_and_undeclared_peeking_are_inconclusive_or_rejected() -> None:
    partial = _finite_look_assessment(
        _finite_assessment(),
        observations=(_look(look=10, dispatched=15, realized=9, failures=0),),
        input_receipt_hashes={"assessment": "c" * 64},
    )
    assert partial.status == "inconclusive_partial_batch"
    assert partial.completed_looks == ()
    assert partial.stop_reason == "partial_batch"
    with pytest.raises(ValueError, match="declared"):
        _finite_look_assessment(
            _finite_assessment(),
            observations=(_look(look=15, dispatched=15, realized=15, failures=0),),
            input_receipt_hashes={"assessment": "c" * 64},
        )


def _paired_table(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "paired_outcome_table"), (
        "campaign statistics module must provide paired outcome tables"
    )
    return api.paired_outcome_table(*args, **kwargs)


def _paired_outcome(*, sample: str, arm: str, failure: bool) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "PairedArmOutcomeV1"), (
        "campaign statistics module must provide paired arm outcomes"
    )
    return api.PairedArmOutcomeV1(
        campaign_spec_digest="c" * 64,
        cohort_id="cohort",
        point_id="p050",
        sample_identity=sample,
        arm_id=arm,
        terminal_status="wrong_logical_action" if failure else "exact",
    )


@pytest.mark.parametrize("both_ok,first_only,second_only,both_failed", [
    (0, 0, 0, 1), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (1, 1, 1, 1),
])
def test_paired_table_exhaustively_retains_cells_marginals_and_exact_discordance(
    both_ok: int, first_only: int, second_only: int, both_failed: int,
) -> None:
    records: list[object] = []
    cells = ((0, 0, both_ok), (1, 0, first_only), (0, 1, second_only), (1, 1, both_failed))
    sample_index = 0
    for first_failure, second_failure, count in cells:
        for _ in range(count):
            sample = f"sample-{sample_index}"
            records.extend((
                _paired_outcome(sample=sample, arm="first", failure=bool(first_failure)),
                _paired_outcome(sample=sample, arm="second", failure=bool(second_failure)),
            ))
            sample_index += 1
    result = _paired_table(
        outcomes=tuple(records),
        arm_ids=("first", "second"),
        alpha=0.05,
        count_receipt_sha256=_HASH,
    )
    assert result.table == {
        "first_success_second_success": both_ok,
        "first_failure_second_success": first_only,
        "first_success_second_failure": second_only,
        "first_failure_second_failure": both_failed,
    }
    total = sum((both_ok, first_only, second_only, both_failed))
    assert result.complete_pairs == total
    assert result.first_failure_rate == pytest.approx((first_only + both_failed) / total)
    assert result.second_failure_rate == pytest.approx((second_only + both_failed) / total)
    discordant = first_only + second_only
    expected_p = 1.0 if discordant == 0 else binomtest(first_only, discordant, p=0.5).pvalue
    assert result.exact_discordance_p_value == pytest.approx(expected_p)
    assert result.risk_difference == pytest.approx((first_only - second_only) / total)
    assert result.risk_difference_interval[0] <= result.risk_difference <= result.risk_difference_interval[1]


def test_paired_table_rejects_tampered_or_partial_identity_and_keeps_zero_discordance_exact() -> None:
    complete = _paired_table(
        outcomes=(
            _paired_outcome(sample="shared", arm="first", failure=False),
            _paired_outcome(sample="shared", arm="second", failure=False),
        ),
        arm_ids=("first", "second"),
        alpha=0.05,
        count_receipt_sha256=_HASH,
    )
    assert complete.exact_discordance_p_value == 1.0
    with pytest.raises(ValueError, match="partial"):
        _paired_table(
            outcomes=(_paired_outcome(sample="only-first", arm="first", failure=False),),
            arm_ids=("first", "second"),
            alpha=0.05,
            count_receipt_sha256=_HASH,
        )
    with pytest.raises(ValueError, match="duplicate"):
        _paired_table(
            outcomes=(
                _paired_outcome(sample="shared", arm="first", failure=False),
                _paired_outcome(sample="shared", arm="first", failure=True),
                _paired_outcome(sample="shared", arm="second", failure=False),
            ),
            arm_ids=("first", "second"),
            alpha=0.05,
            count_receipt_sha256=_HASH,
        )


def _holm_family(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "holm_adjusted_family"), (
        "campaign statistics module must provide frozen-family Holm adjustment"
    )
    return api.holm_adjusted_family(*args, **kwargs)


def _holm_member(comparison_id: str, raw_p_value: float | None) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "HolmFamilyMemberV1"), (
        "campaign statistics module must provide Holm family member records"
    )
    return api.HolmFamilyMemberV1(comparison_id=comparison_id, raw_p_value=raw_p_value)


def test_holm_uses_the_frozen_full_family_for_unavailable_members() -> None:
    with_unavailable = _holm_family(
        family_id="frozen-family",
        alpha=0.05,
        members=(
            _holm_member("a", 0.01),
            _holm_member("b", None),
            _holm_member("c", 0.04),
        ),
    )
    explicit_sentinel = _holm_family(
        family_id="frozen-family",
        alpha=0.05,
        members=(
            _holm_member("a", 0.01),
            _holm_member("b", 1.0),
            _holm_member("c", 0.04),
        ),
    )
    unavailable = next(member for member in with_unavailable.members if member.comparison_id == "b")
    assert with_unavailable.frozen_family_size == 3
    assert with_unavailable.verdict == "inconclusive"
    assert unavailable.status == "unavailable"
    assert unavailable.conclusion == "inconclusive"
    assert unavailable.sentinel_p_value == unavailable.adjusted_p_value == 1.0
    for comparison_id in ("a", "c"):
        first = next(member for member in with_unavailable.members if member.comparison_id == comparison_id)
        second = next(member for member in explicit_sentinel.members if member.comparison_id == comparison_id)
        assert (first.rank, first.multiplier, first.adjusted_p_value) == (
            second.rank, second.multiplier, second.adjusted_p_value,
        )


def test_holm_orders_ties_by_id_and_applies_running_maximum() -> None:
    result = _holm_family(
        family_id="family",
        alpha=0.05,
        members=(
            _holm_member("z", 0.01),
            _holm_member("a", 0.01),
            _holm_member("later", 0.03),
        ),
    )
    assert [member.comparison_id for member in result.members] == ["a", "z", "later"]
    assert [member.rank for member in result.members] == [1, 2, 3]
    assert [member.multiplier for member in result.members] == [3, 2, 1]
    assert [member.adjusted_p_value for member in result.members] == pytest.approx([0.03, 0.03, 0.03])


def _denominator_summary(*args: object, **kwargs: object) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "outcome_denominator_summary"), (
        "campaign statistics module must provide outcome denominator summaries"
    )
    return api.outcome_denominator_summary(*args, **kwargs)


def _campaign_outcome(*, sample: str, status: str, work: int = 7) -> object:
    api = _statistics_api()
    assert api is not None and hasattr(api, "CampaignTerminalOutcomeV1"), (
        "campaign statistics module must provide terminal campaign outcomes"
    )
    return api.CampaignTerminalOutcomeV1(
        sample_identity=sample,
        arm_id="first",
        terminal_status=status,
        actual_work=work,
    )


def test_outcome_summary_exposes_all_shot_acceptance_and_conditional_denominators() -> None:
    summary = _denominator_summary(
        outcomes=(
            _campaign_outcome(sample="success", status="exact", work=2),
            _campaign_outcome(sample="timeout", status="timeout", work=3),
            _campaign_outcome(sample="wrong", status="wrong_logical_action", work=5),
            _campaign_outcome(sample="interrupted", status="infrastructure_interruption", work=11),
        ),
        arm_id="first",
        planned_samples=5,
        dispatched_samples=4,
        outcome_matrix=_finite_assessment().outcome_matrix,
        alpha=0.05,
        count_receipt_sha256=_HASH,
    )
    assert summary.planned_samples == 5
    assert summary.dispatched_samples == 4
    assert summary.terminal_samples == 3
    assert summary.incomplete_samples == 1
    assert summary.accepted_samples == summary.conditional_performance.shots == 2
    assert summary.all_shot_performance.failures == 2
    assert summary.all_shot_performance.shots == 3
    assert summary.conditional_performance.failures == 1
    assert summary.acceptance_probability.failures == 2
    assert summary.acceptance_probability.shots == 3
    assert summary.status_counts["timeout"] == 1
    assert summary.status_counts["infrastructure_interruption"] == 1
    assert summary.actual_work == 21


def test_outcome_summary_keeps_postselection_and_invalid_results_visible() -> None:
    summary = _denominator_summary(
        outcomes=(
            _campaign_outcome(sample="invalid", status="invalid_syndrome"),
            _campaign_outcome(sample="none", status="no_proposal"),
            _campaign_outcome(sample="nonconv", status="nonconvergence"),
            _campaign_outcome(sample="post", status="postselected_rejection"),
        ),
        arm_id="first",
        planned_samples=4,
        dispatched_samples=4,
        outcome_matrix=_finite_assessment().outcome_matrix,
        alpha=0.05,
        count_receipt_sha256=_HASH,
    )
    assert summary.all_shot_performance.failures == summary.all_shot_performance.shots == 4
    assert summary.accepted_samples == 0
    assert summary.conditional_performance is None
    assert summary.status_counts == {
        "invalid_syndrome": 1, "no_proposal": 1, "nonconvergence": 1,
        "postselected_rejection": 1,
    }


def test_incomplete_pair_summary_blocks_paired_inference_until_finalized() -> None:
    api = _statistics_api()
    assert api is not None and hasattr(api, "paired_completion_summary")
    summary = api.paired_completion_summary(
        outcomes=(
            _paired_outcome(sample="complete", arm="first", failure=False),
            _paired_outcome(sample="complete", arm="second", failure=True),
            _paired_outcome(sample="partial", arm="first", failure=False),
        ),
        arm_ids=("first", "second"),
    )
    assert summary.complete_pairs == 1
    assert summary.incomplete_pairs == 1
    assert summary.paired_inference_status == "inconclusive_incomplete_pairs"
    assert summary.missing_arms_by_sample == {"partial": ("second",)}
