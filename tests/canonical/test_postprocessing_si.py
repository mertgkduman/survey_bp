"""Algebraic contracts for the canonical stabilizer-inactivation adaptation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def test_source_status_module_exists_as_the_closed_canonical_adaptation_seam():
    assert (Path(__file__).resolve().parents[2] / "src/bp_registry/canonical/postprocessing/si.py").is_file()


def _original():
    from bp_registry.canonical.problems import OriginalProblem

    return OriginalProblem(
        lineage_id="original-si",
        hx=np.asarray([[1, 1, 0, 0]], dtype=np.uint8),
        hz=np.asarray([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8),
        syndrome=np.asarray([0, 1], dtype=np.uint8),
    )


def test_source_status_keeps_faithful_si_non_runnable_with_all_blockers():
    from bp_registry.canonical.postprocessing.si import source_faithful_status

    status = source_faithful_status()
    assert status.disposition == "non_runnable"
    assert status.qualification == "source_faithful"
    assert status.blockers == (
        "equal_reliability_tie_rule_unknown",
        "gf2_solution_selection_unknown",
        "author_code_identity_unknown",
    )


def test_reliability_orders_stabilizers_by_absolute_posterior_then_id_and_reduces_immutably():
    from bp_registry.canonical.postprocessing.si import StabilizerInactivationSpec

    original = _original()
    before_hz = original.hz.copy()
    before_syndrome = original.syndrome.copy()
    spec = StabilizerInactivationSpec(max_inactivations=1)

    reduction = spec.reduce(original, np.asarray([-3.0, 1.0, -2.0, 2.0], dtype=np.float64))

    assert reduction.source_status.qualification == "canonical_adaptation"
    assert reduction.stabilizer_order == (0,)
    assert reduction.removed_qubits == (0, 1)
    assert reduction.removed_checks == (0,)
    assert reduction.working.column_map == (2, 3)
    assert reduction.working.row_map == (1,)
    np.testing.assert_array_equal(reduction.working.check_matrix, [[1, 1]])
    np.testing.assert_array_equal(reduction.working.syndrome, [1])
    np.testing.assert_array_equal(original.hz, before_hz)
    np.testing.assert_array_equal(original.syndrome, before_syndrome)


def test_reduction_rejects_incompatible_css_before_any_rerun():
    from bp_registry.canonical.postprocessing.si import StabilizerInactivationSpec
    from bp_registry.canonical.problems import OriginalProblem

    incompatible = OriginalProblem(
        lineage_id="original-si-incompatible",
        hx=np.asarray([[1, 0, 0]], dtype=np.uint8),
        hz=np.asarray([[1, 1, 0]], dtype=np.uint8),
        syndrome=np.asarray([0], dtype=np.uint8),
    )
    with pytest.raises(ValueError, match="commute"):
        StabilizerInactivationSpec(max_inactivations=1).reduce(
            incompatible, np.asarray([1.0, 2.0, 3.0], dtype=np.float64),
        )


def test_rerun_controller_is_a_method_owned_canonical_si_operation():
    from bp_registry.canonical.postprocessing.si import StabilizerInactivationSpec

    assert hasattr(StabilizerInactivationSpec, "run")


def test_rerun_solve_lift_and_original_validation_produce_a_qualified_candidate():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.postprocessing.si import StabilizerInactivationSpec

    result = StabilizerInactivationSpec(max_inactivations=1).run(
        _original(), np.asarray([-3.0, 1.0, -2.0, 2.0], dtype=np.float64),
        rerun=lambda working: np.asarray([1, 0], dtype=np.uint8),
        budgets=BudgetTree(limits=(), parents={}), scope="si",
    )

    assert result.status == "success"
    assert result.selected_candidate == (0, 0, 1, 0)
    assert result.trials[0].original_valid is True
    assert {leaf.stage for leaf in result.work} == {"ranking", "reduction", "rerun", "solve", "lift", "original_check"}
