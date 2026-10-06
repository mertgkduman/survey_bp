"""Contracts for the Phase 7 ordered Tanner forest CSS adaptation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

def test_otf_exposes_a_named_css_adaptation_contract():
    assert (Path(__file__).resolve().parents[2] / "src/bp_registry/canonical/postprocessing/otf.py").is_file()


def _original(matrix=((1, 1, 0), (1, 1, 1)), syndrome=None):
    from bp_registry.canonical.problems import OriginalProblem

    return OriginalProblem("original-otf", np.zeros((0, len(matrix[0])), dtype=np.uint8),
                           np.asarray(matrix, dtype=np.uint8),
                           np.zeros(len(matrix), dtype=np.uint8) if syndrome is None else np.asarray(syndrome, dtype=np.uint8))


def test_probability_conversion_orders_descending_error_probability_then_original_id():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    forest = OrderedTannerForestSpec().build(_original(), np.asarray([0.0, 0.0, 2.0]))

    assert forest.ordered_columns == (0, 1, 2)
    assert forest.probabilities[0] == pytest.approx(0.5)
    assert forest.probabilities[2] == pytest.approx(1.0 / (1.0 + np.exp(2.0)))


def test_ordered_union_find_returns_an_acyclic_maximal_forest_with_rejections():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    forest = OrderedTannerForestSpec().build(_original(), np.asarray([-4.0, -3.0, 3.0]))

    assert forest.source_status.qualification == "canonical_css_adaptation"
    assert forest.accepted_columns == (0, 2)
    assert forest.cycle_rejected_columns == (1,)
    assert forest.is_acyclic() is True
    assert forest.is_ordered_maximal() is True
    assert forest.working.column_map == (0, 2)
    assert {entry.stage for entry in forest.work} == {"sort", "union_find_probe", "accepted_column"}


def test_duplicate_ids_and_disconnected_columns_are_rejected_deterministically():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    with pytest.raises(ValueError, match="unique"):
        OrderedTannerForestSpec(column_ids=(0, 0, 2))
    with pytest.raises(ValueError, match="degree-zero"):
        OrderedTannerForestSpec().build(_original(((1, 0),)), np.asarray([1.0, 1.0]))


def test_accepted_column_cap_retains_the_ordered_denial_evidence():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    forest = OrderedTannerForestSpec(max_accepted_columns=1).build(_original(), np.asarray([-4.0, -3.0, 3.0]))

    assert forest.status == "capped"
    assert forest.accepted_columns == (0,)
    assert forest.cap_denied_columns == (1, 2)
    assert forest.is_acyclic() is True
    assert forest.is_ordered_maximal() is False


def test_otf_rerun_is_a_method_owned_same_kernel_operation():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    assert hasattr(OrderedTannerForestSpec, "run")


def test_forest_bp_rerun_lifts_omitted_columns_as_zero_and_validates_original_syndrome():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    seen = []
    result = OrderedTannerForestSpec().run(
        _original(syndrome=(1, 1)), np.asarray([-4.0, -3.0, 3.0]),
        rerun=lambda working: (seen.append((working.column_map, working.check_matrix.copy())) or np.asarray([1, 0], dtype=np.uint8)),
        budgets=BudgetTree(limits=(), parents={}), scope="otf",
    )

    assert seen[0][0] == (0, 2)
    np.testing.assert_array_equal(seen[0][1], [[1, 0], [1, 1]])
    assert result.status == "success"
    assert result.forest_candidate == (1, 0)
    assert result.lifted_candidate == result.selected_candidate == (1, 0, 0)
    assert result.original_valid is True
    assert {entry.stage for entry in result.work} == {"sort", "union_find_probe", "accepted_column", "forest_bp", "lift", "original_check"}


@pytest.mark.parametrize(
    ("rerun", "status"),
    [
        (lambda working: np.asarray([2, 0], dtype=np.uint8), "invalid_rerun_candidate"),
        (lambda working: np.asarray([0, 0], dtype=np.uint8), "forest_syndrome_invalid"),
    ],
)
def test_invalid_or_nonconverged_forest_outputs_stay_unsuccessful(rerun, status):
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    result = OrderedTannerForestSpec().run(
        _original(syndrome=(1, 1)), np.asarray([-4.0, -3.0, 3.0]), rerun=rerun,
        budgets=BudgetTree(limits=(), parents={}), scope="otf",
    )

    assert result.status == status
    assert result.selected_candidate is None
    assert result.original_valid is False
    assert any(entry.stage == "forest_bp" for entry in result.work)


def test_valid_candidate_remains_eligible_when_the_declared_forest_cap_terminates_the_call():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    result = OrderedTannerForestSpec(max_accepted_columns=1).run(
        _original(syndrome=(1, 1)), np.asarray([-4.0, -3.0, 3.0]),
        rerun=lambda working: np.asarray([1], dtype=np.uint8), budgets=BudgetTree(limits=(), parents={}), scope="otf",
    )

    assert result.status == "success_capped"
    assert result.termination == "count_budget_exhausted"
    assert result.construction.status == "capped"
    assert result.selected_candidate == (1, 0, 0)


def test_budget_denial_retains_graph_work_without_claiming_an_otf_success():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec

    result = OrderedTannerForestSpec().run(
        _original(syndrome=(1, 1)), np.asarray([-4.0, -3.0, 3.0]),
        rerun=lambda working: np.asarray([1, 0], dtype=np.uint8),
        budgets=BudgetTree(limits=(BudgetLimit("otf", "bp_calls", 0),), parents={}), scope="otf",
    )

    assert result.status == "capped"
    assert result.selected_candidate is None
    assert {entry.stage for entry in result.work} == {"sort", "union_find_probe", "accepted_column"}


def test_circuit_source_status_stays_non_runnable_while_the_css_adaptation_has_no_detector_input():
    from bp_registry.canonical.postprocessing.otf import OrderedTannerForestSpec, source_faithful_status

    status = source_faithful_status()
    assert status.disposition == "non_runnable"
    assert status.qualification == "source_faithful"
    assert "detector" in " ".join(status.blockers)
    assert OrderedTannerForestSpec.build.__annotations__.get("original") is not None


def test_otf_postprocessor_uses_the_generic_one_shot_controller_protocol():
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.canonical.postprocessing import FailedAttemptSnapshot, PostprocessingController
    from bp_registry.canonical.postprocessing.otf import OtfPostprocessor, OrderedTannerForestSpec
    from bp_registry.canonical.problems import WorkingProblem

    original = _original(syndrome=(1, 1))
    working = WorkingProblem(
        "working-otf", original,
        LineageEdge("identity", LineageId("original", original.lineage_id), LineageId("working", "working-otf")),
    )
    snapshot = FailedAttemptSnapshot(
        "otf-failed-attempt", working, np.zeros(3, dtype=np.uint8), np.asarray([-4.0, -3.0, 3.0]),
        original_residual_weight=2, original_channel_nll=1.0, declared_attempt_ordinal=0,
    )

    result = PostprocessingController(
        OtfPostprocessor(OrderedTannerForestSpec(), rerun=lambda forest: np.asarray([1, 0], dtype=np.uint8)),
    ).execute((snapshot,), bp_succeeded=False)

    assert result.status == "success"
    assert result.candidate == (1, 0, 0)
    assert result.native_calls == 1
