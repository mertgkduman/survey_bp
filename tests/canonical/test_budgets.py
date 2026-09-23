"""Hierarchical budget and atomic flooding execution contracts."""

from __future__ import annotations

import importlib
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest


def _api():
    assert importlib.util.find_spec("bp_registry.canonical.budgets") is not None, (
        "canonical execution requires a budgets module with reserve-before-work controls"
    )
    budgets = importlib.import_module("bp_registry.canonical.budgets")
    execution = importlib.import_module("bp_registry.canonical.execution")
    return budgets, execution


def _tree(api, *, limit: int):
    BudgetLimit, BudgetTree, WorkVector = api.BudgetLimit, api.BudgetTree, api.WorkVector
    resource = "check_to_variable_updates"
    return BudgetTree(
        limits=(
            BudgetLimit("shot", resource, limit),
            BudgetLimit("search", resource, limit),
            BudgetLimit("member", resource, limit),
            BudgetLimit("attempt", resource, limit),
        ),
        parents={"search": "shot", "member": "search", "attempt": "member"},
    ), WorkVector(check_to_variable_updates=limit)


def test_reservation_checks_every_ancestor_and_names_the_binding_limit():
    budgets, _execution = _api()
    tree, work = _tree(budgets, limit=2)

    accepted = tree.reserve("attempt", work, leaf_id="leaf-accepted")
    accepted.commit_once()
    rejected = tree.reserve("attempt", budgets.WorkVector(check_to_variable_updates=1), leaf_id="leaf-rejected")

    assert rejected is None
    termination = tree.last_termination
    assert termination is not None
    assert termination.binding_scope == "attempt"
    assert termination.resource == "check_to_variable_updates"
    assert termination.configured_limit == 2
    assert termination.consumed_amount == 2
    assert termination.reason == "count_budget_exhausted"
    assert tree.summary("shot") == work


def test_tighter_root_limit_rejects_before_sweep_work_even_when_attempt_allows_it():
    budgets, _execution = _api()
    resource = "check_to_variable_updates"
    tree = budgets.BudgetTree(
        limits=(
            budgets.BudgetLimit("shot", resource, 1),
            budgets.BudgetLimit("search", resource, 3),
            budgets.BudgetLimit("member", resource, 3),
            budgets.BudgetLimit("attempt", resource, 3),
        ),
        parents={"search": "shot", "member": "search", "attempt": "member"},
    )
    assert tree.reserve("attempt", budgets.WorkVector(check_to_variable_updates=2), leaf_id="root-bound") is None
    assert tree.last_termination is not None
    assert tree.last_termination.binding_scope == "shot"
    assert tree.last_termination.configured_limit == 1
    assert tree.summary("shot") == budgets.WorkVector.zero()


def test_exact_limit_commits_once_and_rollback_leaves_no_work_or_state():
    budgets, _execution = _api()
    tree, work = _tree(budgets, limit=2)
    reservation = tree.reserve("attempt", work, leaf_id="leaf-once")
    assert reservation is not None
    reservation.rollback()
    assert tree.summary("shot") == budgets.WorkVector.zero()

    retry = tree.reserve("attempt", work, leaf_id="leaf-once")
    assert retry is not None
    retry.commit_once()
    with pytest.raises(RuntimeError, match="already finalized"):
        retry.commit_once()
    assert tree.summary("attempt") == work


def test_concurrent_reservations_never_oversubscribe_a_shared_ancestor():
    budgets, _execution = _api()
    tree, work = _tree(budgets, limit=1)

    def reserve(index: int):
        return tree.reserve("attempt", work, leaf_id=f"leaf-{index}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations = list(pool.map(reserve, range(2)))
    accepted = [reservation for reservation in reservations if reservation is not None]
    assert len(accepted) == 1
    accepted[0].commit_once()
    assert tree.summary("shot") == work


def test_wall_clock_stops_after_inflight_sweep_at_next_declared_boundary():
    budgets, execution = _api()
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule

    ticks = iter((0, 3, 12))
    clock = lambda: next(ticks)
    tree, _work = _tree(budgets, limit=100)
    schedule = FloodingSchedule(EdgeTable.from_edges(1, 1, [(0, 0)]), kernel=BinarySpaKernel())
    runner = execution.AtomicFloodingExecutor(
        schedule, tree, scope="attempt", wall_clock=budgets.WallClockLimit(10, clock=clock)
    )

    result = runner.run_attempt(np.array([0.0]), np.array([0], dtype=np.uint8), error_rate=0.2, max_iterations=2)

    assert result.termination is not None
    assert result.termination.reason == "wall_clock_deadline"
    assert result.termination.boundary_kind == "candidate_selection_boundary"
    assert result.termination.observed_elapsed_ns == 12
    assert result.termination.overshoot_ns == 2
    assert result.iterations == 1
    assert tree.summary("shot").check_to_variable_updates == 1


def test_sweep_exception_rolls_back_reservation_without_changing_message_state():
    budgets, execution = _api()
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule

    tree, _work = _tree(budgets, limit=100)
    schedule = FloodingSchedule(EdgeTable.from_edges(1, 1, [(0, 0)]), kernel=BinarySpaKernel())
    runner = execution.AtomicFloodingExecutor(schedule, tree, scope="attempt")
    old_v2c = np.array([0.4])

    with pytest.raises(ValueError, match="syndrome"):
        runner.run_attempt(old_v2c, np.array([2]), error_rate=0.2, max_iterations=1)
    np.testing.assert_allclose(old_v2c, [0.4])
    assert tree.summary("shot") == budgets.WorkVector.zero()
