"""Source-construction and replay checks for Hsu's overlapping groups."""

import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetLimit, BudgetTree, WorkVector
from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
from bp_registry.canonical.group_shuffled import HsuGroupPlan, HsuGroupSchedule, groups_from_order
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable


def test_hsu_construction_matches_paper_worked_example():
    assert groups_from_order((0, 1, 2, 3), check_count=4) == ((0, 1), (1, 2), (2, 3))


def test_hsu_construction_replay_covers_and_counts_repeated_checks():
    plan = HsuGroupPlan(6, "a" * 64)
    first = plan.traversal(attempt_identity="run:shot:0", iteration=0)
    assert first == plan.traversal(attempt_identity="run:shot:0", iteration=0)
    assert first != plan.traversal(attempt_identity="run:shot:0", iteration=1)
    assert len(first.groups) == 5
    assert first.groups == tuple(zip(first.order[:-1], first.order[1:]))
    assert sorted(first.order) == list(range(6))
    assert dict(first.evidence()["membership_multiplicity"]) == {
        check: (1 if check in (first.order[0], first.order[-1]) else 2)
        for check in first.order
    }


@pytest.mark.parametrize("order,count", [((0,), 1), ((0, 0), 2), ((0, 2), 2), ((True, 1), 2), ((0, "1"), 2)])
def test_hsu_construction_rejects_invalid_order(order, count):
    with pytest.raises(ValueError):
        groups_from_order(order, check_count=count)


def test_hsu_replay_rejects_invalid_identity_and_iteration():
    with pytest.raises(ValueError):
        HsuGroupPlan(3, "not-a-digest")
    with pytest.raises(ValueError):
        HsuGroupPlan(3, "a" * 64).traversal(attempt_identity="x", iteration=-1)


def _small_schedule():
    # Every adjacent pair has a shared variable; unlike a conflict-free layer.
    table = EdgeTable.from_check_matrix(np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]], dtype=np.uint8))
    return HsuGroupSchedule(table, kernel=BinarySpaKernel(), root_identity="a" * 64, attempt_identity="test:attempt:0")


def test_hsu_shared_variable_group_uses_frozen_v2c_then_commits_affected_refresh():
    schedule = _small_schedule()
    budgets = BudgetTree(limits=[], parents={"search": "shot", "attempt": "search"})
    progress = ScheduleProgress(0, 0, (0,))
    assert schedule.refresh_order(progress, budgets=budgets)[0]
    group = schedule._selected_group(progress)
    kernel = BinarySpaKernel()
    messages = np.full(schedule.edge_table.edge_count, kernel.prior(0.1))
    frozen = messages.copy()
    syndrome = np.array([1, 0, 1], dtype=np.uint8)
    expected_messages, expected_candidate, expected_c2v = schedule._compute_group(frozen, syndrome, error_rate=0.1, group=group)
    result = schedule.execute_local_step(CanonicalLocalStepExecutor(budgets, scope="attempt"), messages, syndrome, error_rate=0.1, progress=progress, is_converged=lambda candidate: False)
    assert result.admitted and result.progress.cursor == (1,)
    np.testing.assert_allclose(messages, expected_messages)
    np.testing.assert_array_equal(result.candidate, expected_candidate)
    np.testing.assert_allclose(schedule._c2v, expected_c2v)
    assert set(schedule.edge_table.edges[index][1] for check in group for index in schedule._check_edges[check]) == {0, 1, 2}
    work = budgets.summary("attempt")
    assert work.check_to_variable_updates == 4
    assert work.variable_to_check_updates == 6
    assert work.order_generation == 3 and work.order_selection == 1
    assert work.convergence_checks == work.candidate_checks == 1


def test_hsu_group_budget_denial_rolls_back_messages_c2v_and_cursor():
    schedule = _small_schedule()
    budgets = BudgetTree(limits=[BudgetLimit("attempt", "check_to_variable_updates", 3)], parents={"search": "shot", "attempt": "search"})
    progress = ScheduleProgress(0, 0, (0,))
    assert schedule.refresh_order(progress, budgets=budgets)[0]
    messages = np.full(schedule.edge_table.edge_count, BinarySpaKernel().prior(0.1))
    before = messages.copy()
    step = schedule.execute_local_step(CanonicalLocalStepExecutor(budgets, scope="attempt"), messages, np.array([1, 0, 1], dtype=np.uint8), error_rate=0.1, progress=progress, is_converged=lambda _: False)
    assert not step.admitted and step.progress == progress
    np.testing.assert_array_equal(messages, before)
    np.testing.assert_array_equal(schedule._c2v, np.zeros(schedule.edge_table.edge_count))
    assert budgets.summary("attempt") == WorkVector(order_generation=3)
