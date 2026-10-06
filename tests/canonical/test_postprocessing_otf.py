"""Contracts for the Phase 7 ordered Tanner forest CSS adaptation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

def test_otf_exposes_a_named_css_adaptation_contract():
    assert (Path(__file__).resolve().parents[2] / "src/bp_registry/canonical/postprocessing/otf.py").is_file()


def _original(matrix=((1, 1, 0), (1, 1, 1))):
    from bp_registry.canonical.problems import OriginalProblem

    return OriginalProblem("original-otf", np.zeros((0, len(matrix[0])), dtype=np.uint8),
                           np.asarray(matrix, dtype=np.uint8), np.zeros(len(matrix), dtype=np.uint8))


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
