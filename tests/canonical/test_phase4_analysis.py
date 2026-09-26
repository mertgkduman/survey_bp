"""Phase 4 denominators and paired outcomes on deliberately discordant shots."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bp_registry.phase4_analysis import exact_paired_binomial_p, summarize_matched_cohort, wilson_interval


def _shot(shot_id: int, first_cell: str, first_selected: bool, second_cell: str, second_selected: bool) -> dict[str, object]:
    sample = f"sample-{shot_id}"
    return {
        "shot_id": shot_id, "sample_identity": sample,
        "arms": {
            "first": {"status": "completed", "sample_identity": sample, "diagnostic_cell": first_cell, "selected": first_selected},
            "second": {"status": "completed", "sample_identity": sample, "diagnostic_cell": second_cell, "selected": second_selected},
        },
    }


def test_matched_cohort_keeps_invalid_correct_and_no_proposal_as_failures():
    shots = [
        _shot(0, "valid_correct", True, "valid_correct", True),
        _shot(1, "invalid_correct", False, "valid_correct", True),
        _shot(2, "no_proposal", False, "valid_wrong_logical", True),
        _shot(3, "valid_correct", True, "invalid_wrong_logical", False),
    ]
    summary = summarize_matched_cohort(shots, arm_names=("first", "second"))
    first, second = summary["arms"]["first"], summary["arms"]["second"]
    assert first["diagnostic_cells"] == {
        "valid_correct": 2, "valid_wrong_logical": 0, "invalid_correct": 1,
        "invalid_wrong_logical": 0, "no_proposal": 1,
    }
    assert first["all_shot_failure"]["failures"] == 2
    assert first["selected_valid_syndrome_logical_error"]["denominator"] == 2
    assert first["selected_valid_syndrome_logical_error"]["failures"] == 0
    assert second["all_shot_failure"]["failures"] == 2
    assert second["selected_valid_syndrome_logical_error"]["denominator"] == 3
    assert second["selected_valid_syndrome_logical_error"]["failures"] == 1
    assert summary["paired_success"]["first_only"] == 1
    assert summary["paired_success"]["second_only"] == 1
    assert summary["paired_success"]["exact_two_sided_p"] == 1.0


def test_paired_arithmetic_and_empty_conditional_denominator():
    assert exact_paired_binomial_p(0, 3) == .25
    assert exact_paired_binomial_p(0, 0) == 1.0
    assert wilson_interval(0, 0) is None
    summary = summarize_matched_cohort([_shot(0, "no_proposal", False, "valid_correct", True)], arm_names=("first", "second"))
    assert summary["arms"]["first"]["selected_valid_syndrome_logical_error"] == {
        "failures": 0, "denominator": 0, "estimate": None, "wilson_95": None,
    }
    assert summary["paired_success"]["exact_two_sided_p"] == 1.0


@pytest.mark.parametrize("change,match", [
    ("incomplete", "incomplete"),
    ("sample", "physical sample"),
    ("nonexistent_selection", "nonexistent proposal"),
    ("duplicate", "duplicate shot/sample identity"),
])
def test_matched_cohort_rejects_unverifiable_denominators(change: str, match: str):
    shots = [_shot(0, "valid_correct", True, "valid_correct", True)]
    if change == "incomplete":
        shots[0]["arms"]["first"]["status"] = "timeout"
    elif change == "sample":
        shots[0]["arms"]["first"]["sample_identity"] = "other"
    elif change == "nonexistent_selection":
        shots[0]["arms"]["first"]["diagnostic_cell"] = "no_proposal"
    else:
        shots.append(deepcopy(shots[0]))
    with pytest.raises(ValueError, match=match):
        summarize_matched_cohort(shots, arm_names=("first", "second"))
