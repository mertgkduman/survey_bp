"""Phase 6 list selection is explicit, stable, and original-problem gated."""

from __future__ import annotations

import json

import numpy as np
import pytest

from bp_registry.canonical.list_selection import (
    ListCandidate, ListSelectionSpec, select_candidate_list,
)
from bp_registry.canonical.problems import OriginalProblem


def _original() -> OriginalProblem:
    return OriginalProblem(
        "original-list-selection-fixture",
        np.zeros((1, 3), dtype=np.uint8),
        np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
        np.asarray([1, 0], dtype=np.uint8),
    )


def _item(
    candidate_id: str, order: int, bits: tuple[int, ...] | None, *,
    score: float | None = None, eligible: bool = True,
) -> ListCandidate:
    return ListCandidate(candidate_id, f"member-{candidate_id}", order, bits, eligible,
                         "fixture:controller_converged", score)


def test_original_invalid_candidate_cannot_win_even_with_better_score():
    original = _original()
    policy = ListSelectionSpec("declared_score", "fixture:controller_score", "minimize", "generation_order")
    rows = (
        _item("invalid", 0, (0, 0, 0), score=-10.0),
        _item("valid", 1, (1, 0, 0), score=2.0),
    )
    result = select_candidate_list(original, rows, spec=policy)
    assert result.selected_id == "valid"
    assert result.selected_origin == "member-valid"
    assert result.selected_bits == (1, 0, 0)
    assert result.assessments[0].rejection_reason == "original_syndrome_mismatch"
    assert result.assessments[0].score == -10.0
    assert result.assessments[0].bits == (0, 0, 0)
    assert original.hz.flags.writeable is False


def test_ties_and_arrival_order_use_the_declared_rule():
    rows = (
        _item("z", 0, (1, 0, 0), score=3.0),
        _item("a", 1, (0, 1, 1), score=3.0),
    )
    order_policy = ListSelectionSpec("declared_score", "fixture:controller_score", "minimize", "generation_order")
    id_policy = ListSelectionSpec("declared_score", "fixture:controller_score", "minimize", "candidate_id")
    for arrival in (rows, tuple(reversed(rows))):
        by_order = select_candidate_list(_original(), arrival, spec=order_policy)
        by_id = select_candidate_list(_original(), arrival, spec=id_policy)
        assert by_order.selected_id == "z"
        assert by_id.selected_id == "a"
        assert [item.candidate_id for item in by_order.assessments] == ["z", "a"]
        assert json.loads(json.dumps(by_order.as_evidence()))["selected_origin"] == "member-z"


def test_unavailable_declared_ineligible_and_wrong_shape_are_retained():
    result = select_candidate_list(_original(), (
        _item("missing", 0, None),
        _item("ineligible", 1, (1, 0, 0), eligible=False),
        _item("short", 2, (1, 0)),
    ), spec=ListSelectionSpec("hamming_weight", "original_hamming_weight", "minimize", "generation_order"))
    assert result.selected_id is None
    assert [row.rejection_reason for row in result.assessments] == [
        "candidate_unavailable", "declared_ineligible", "original_shape_mismatch",
    ]
    assert result.as_evidence()["selection_status"] == "no_eligible_candidate"
    assert len(result.as_evidence()["candidates"]) == 3


def test_score_policy_requires_an_explicit_finite_input():
    original = _original()
    result = select_candidate_list(original, (_item("unscored", 0, (1, 0, 0)),),
                                   spec=ListSelectionSpec("declared_score", "fixture:controller_score", "maximize", "candidate_id"))
    assert result.selected_id is None
    assert result.assessments[0].rejection_reason == "missing_declared_score"
    with pytest.raises(ValueError, match="finite"):
        _item("nan", 0, (1, 0, 0), score=float("nan"))
    with pytest.raises(ValueError, match="unused declared scores"):
        select_candidate_list(original, (_item("scored", 0, (1, 0, 0), score=1.0),),
                              spec=ListSelectionSpec("hamming_weight", "original_hamming_weight", "minimize", "generation_order"))
    with pytest.raises(ValueError, match="unique"):
        select_candidate_list(original, (_item("duplicate", 0, (1, 0, 0)), _item("duplicate", 1, (1, 0, 0))),
                              spec=ListSelectionSpec("hamming_weight", "original_hamming_weight", "minimize", "generation_order"))


def test_hamming_weight_is_computed_from_original_coordinate_bits():
    result = select_candidate_list(_original(), (
        _item("heavy", 0, (0, 1, 1)),
        _item("light", 1, (1, 0, 0)),
    ), spec=ListSelectionSpec("hamming_weight", "original_hamming_weight", "minimize", "generation_order"))
    assert result.selected_id == "light"
    assert [row.score for row in result.assessments] == [2, 1]


def test_declared_maximization_keeps_all_scores_and_origins():
    result = select_candidate_list(_original(), (
        _item("low", 0, (1, 0, 0), score=1.0),
        _item("high", 1, (0, 1, 1), score=2.0),
    ), spec=ListSelectionSpec("declared_score", "fixture:controller_score", "maximize", "generation_order"))
    evidence = result.as_evidence()
    assert evidence["selected_id"] == "high"
    assert evidence["selected_origin"] == "member-high"
    assert evidence["score_basis"] == "fixture:controller_score"
    assert [row["score"] for row in evidence["candidates"]] == [1.0, 2.0]
