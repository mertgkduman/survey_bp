"""Source-lifecycle oracle tests for the pinned Huang--Ueng sRBP schedule."""

from __future__ import annotations

import importlib
import importlib.util

import numpy as np
import pytest


def _irregular_fixture():
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    # c0 has degree three, while the other checks make dependency cones irregular.
    table = EdgeTable.from_edges(3, 5, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 4)])
    return table, BinarySpaKernel(), np.asarray([2.0, 3.0, 4.0, 1.5, 1.0, 2.5, 0.5]), np.zeros(7), np.zeros(3, dtype=np.uint8)


def _reference_lifecycle_step(table, kernel, v2c, c2v, cache, syndrome, *, error_rate):
    """Independent full-cache source oracle; it never globally refreshes values."""
    from bp_registry.canonical.updates import MinSumUpdate

    edges = table.edges
    check_edges = tuple(tuple(i for i, (c, _v) in enumerate(edges) if c == current) for current in range(table.check_count))
    variable_edges = tuple(tuple(i for i, (_c, v) in enumerate(edges) if v == current) for current in range(table.variable_count))
    predictor = MinSumUpdate(profile=kernel.profile)
    selected = 0
    for index in range(1, table.edge_count):
        if cache[index] > cache[selected]:
            selected = index
    check, variable = edges[selected]
    next_v2c = np.array(v2c, dtype=np.float64, copy=True)
    next_c2v = np.array(c2v, dtype=np.float64, copy=True)
    incoming = next_v2c[[other for other in check_edges[check] if other != selected]]
    next_c2v[selected] = kernel.check_message(incoming, int(syndrome[check]))
    beliefs = kernel.assemble_beliefs(table.variable_count, tuple(v for _c, v in edges), next_c2v, kernel.prior(error_rate))
    for index in variable_edges[variable]:
        if index != selected:
            next_v2c[index] = kernel.variable_message(float(beliefs[variable]), float(next_c2v[index]))
    next_cache = np.array(cache, dtype=np.float64, copy=True)
    next_cache[selected] = 0.0
    for v2c_index in variable_edges[variable]:
        changed_check, _ = edges[v2c_index]
        if changed_check == check:
            continue
        for index in check_edges[changed_check]:
            if edges[index][1] == variable:
                continue
            prediction = predictor.check_to_variable(
                next_v2c[[other for other in check_edges[changed_check] if other != index]], syndrome=int(syndrome[changed_check]),
            )
            next_cache[index] = abs(prediction - next_c2v[index])
    return selected, next_v2c, next_c2v, next_cache


def _residual_module():
    """Make the absent Phase 3 policy a deliberate, assertion-based RED."""
    spec = importlib.util.find_spec("bp_registry.canonical.residual")
    assert spec is not None, "Phase 3 must provide bp_registry.canonical.residual"
    return importlib.import_module("bp_registry.canonical.residual")


def test_tracer_residual_schedule_contract_is_closed_to_conventional_srbp():
    residual = _residual_module()
    assert hasattr(residual, "SyndromeResidualSchedule")
    assert hasattr(residual, "ResidualCache")
    assert hasattr(residual, "ResidualSelection")
    assert residual.SyndromeResidualSchedule.policy_name == "huang_ueng_conventional_srbp"
    assert residual.SyndromeResidualSchedule.tie_rule == "canonical_edge_order"
    assert residual.SyndromeResidualSchedule.stopping_adaptation == "D-09 after residual-selected local unit"


def test_tracer_initializes_full_pool_selects_first_tie_and_reserves_one_local_unit():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    residual = _residual_module()
    table = EdgeTable.from_edges(2, 2, [(1, 1), (0, 1), (1, 0), (0, 0)])
    schedule = residual.SyndromeResidualSchedule(table, kernel=BinarySpaKernel())
    v2c = np.asarray([1.0, 1.0, 1.0, 1.0])
    c2v = np.asarray([0.0, 0.0, 0.0, 0.0])
    setup_tree = BudgetTree(limits=())
    cache = schedule.initialize(v2c, c2v, np.asarray([0, 0]), error_rate=0.1, budgets=setup_tree, scope="attempt")

    assert cache.values.shape == (4,)
    assert cache.setup_work.residual_precomputations == 4
    assert cache.setup_work.residual_differences == 4
    assert setup_tree.summary("attempt").residual_priority_evaluations == 8
    proposal = schedule.propose_local_step(v2c, c2v, cache, np.asarray([0, 0]), error_rate=0.1)
    assert proposal.selection.index == 0
    assert proposal.selection.comparisons == 3
    assert proposal.local_step.proposed_work.candidate_checks == 1
    assert proposal.decode_work.priority_comparisons == 3

    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"),
        proposal,
        v2c=v2c,
        c2v=c2v,
        cache=cache,
        progress=ScheduleProgress(iteration=0, local_steps=0),
        is_converged=lambda _candidate: False,
    )
    assert result.admitted is True
    assert result.selection.edge == (0, 0)
    assert result.progress.local_steps == 1
    assert result.progress.iteration == 0
    assert result.cache.values[result.selection.index] == 0.0
    assert result.candidate.shape == (2,)


def test_setup_budget_denial_precedes_all_full_pool_residual_calculation():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    residual = _residual_module()
    table = EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)])
    schedule = residual.SyndromeResidualSchedule(table, kernel=BinarySpaKernel())
    v2c = np.asarray([1.0, 2.0])
    c2v = np.asarray([0.0, 0.0])
    tree = BudgetTree(limits=(BudgetLimit("attempt", "residual_priority_evaluations", 0),))

    with pytest.raises(residual.ResidualSetupBudgetDenied):
        schedule.initialize(v2c, c2v, np.asarray([0]), error_rate=0.1, budgets=tree, scope="attempt")
    np.testing.assert_array_equal(v2c, np.asarray([1.0, 2.0]))
    np.testing.assert_array_equal(c2v, np.asarray([0.0, 0.0]))
    assert tree.leaf_events() == ()


def test_source_lifecycle_matches_independent_full_cache_oracle_and_preserves_selected_zero():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress

    residual = _residual_module()
    table, kernel, v2c, c2v, syndrome = _irregular_fixture()
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    selected, expected_v2c, expected_c2v, expected_cache = _reference_lifecycle_step(
        table, kernel, v2c, c2v, cache.values, syndrome, error_rate=0.1,
    )
    stateless_selected_residual = abs(schedule._prediction(v2c, syndrome, selected) - expected_c2v[selected])
    assert stateless_selected_residual > 0.0  # MS prediction and SPA commit deliberately differ.

    proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1)
    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), proposal,
        v2c=v2c, c2v=c2v, cache=cache, progress=ScheduleProgress(0, 0), is_converged=lambda _candidate: False,
    )
    assert result.selection.index == selected
    np.testing.assert_allclose(v2c, expected_v2c)
    np.testing.assert_allclose(result.c2v, expected_c2v)
    np.testing.assert_allclose(result.cache.values, expected_cache)
    assert result.cache.values[selected] == 0.0
    assert proposal.decode_work.priority_comparisons == table.edge_count - 1
    assert proposal.decode_work.residual_precomputations == len(proposal.invalidated_indices)
    assert proposal.decode_work.residual_differences == len(proposal.invalidated_indices)


def test_selected_residual_remains_zero_until_a_later_dependency_update_invalidates_it():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress

    residual = _residual_module()
    table, kernel, v2c, c2v, syndrome = _irregular_fixture()
    # Keep c0/v0 first, then make c2/v1 the next source-cache selection.
    v2c[6] = 8.0
    c2v[0] = -0.3
    c2v[4] = 4.7
    c2v[5] = 5.2
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    executor = CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt")

    first = schedule.execute_local_step(
        executor, schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1),
        v2c=v2c, c2v=c2v, cache=cache, progress=ScheduleProgress(0, 0), is_converged=lambda _candidate: False,
    )
    assert first.selection.index == 0
    assert first.cache.values[0] == 0.0
    stateless = abs(schedule._prediction(v2c, syndrome, 0) - first.c2v[0])
    assert stateless > 0.0

    second_proposal = schedule.propose_local_step(v2c, first.c2v, first.cache, syndrome, error_rate=0.1)
    assert second_proposal.selection.index == 5
    assert 0 in second_proposal.invalidated_indices
    second = schedule.execute_local_step(
        executor, second_proposal,
        v2c=v2c, c2v=first.c2v, cache=first.cache, progress=first.progress, is_converged=lambda _candidate: False,
    )
    assert second.cache.values[0] > 0.0


@pytest.mark.parametrize(
    "edges",
    [
        [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
        [(0, 0), (0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 3)],
    ],
)
def test_small_irregular_graphs_match_the_independent_source_lifecycle_oracle(edges):
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable

    residual = _residual_module()
    table = EdgeTable.from_edges(3, 4, edges)
    rng = np.random.default_rng(20260924 + table.edge_count)
    v2c = rng.uniform(0.2, 4.0, size=table.edge_count)
    c2v = rng.uniform(-1.0, 1.0, size=table.edge_count)
    syndrome = np.asarray([0, 1, 0], dtype=np.uint8)
    kernel = BinarySpaKernel()
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    selected, expected_v2c, expected_c2v, expected_cache = _reference_lifecycle_step(
        table, kernel, v2c, c2v, cache.values, syndrome, error_rate=0.1,
    )
    proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1)
    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), proposal,
        v2c=v2c, c2v=c2v, cache=cache, progress=ScheduleProgress(0, 0), is_converged=lambda _candidate: False,
    )
    assert result.selection.index == selected
    np.testing.assert_allclose(v2c, expected_v2c)
    np.testing.assert_allclose(result.c2v, expected_c2v)
    np.testing.assert_allclose(result.cache.values, expected_cache)


def test_denied_local_bundle_preserves_messages_cache_progress_and_budget_leaves():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress

    residual = _residual_module()
    table, kernel, v2c, c2v, syndrome = _irregular_fixture()
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    before_v2c, before_c2v, before_cache = v2c.copy(), c2v.copy(), cache.values.copy()
    proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1)
    tree = BudgetTree(limits=(BudgetLimit("attempt", "candidate_checks", 0),))
    progress = ScheduleProgress(0, 0, cursor=(0,), rng_state=("schedule", 7))

    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(tree, scope="attempt"), proposal,
        v2c=v2c, c2v=c2v, cache=cache, progress=progress, is_converged=lambda _candidate: False,
    )
    assert result.admitted is False
    assert result.progress == progress
    np.testing.assert_array_equal(v2c, before_v2c)
    np.testing.assert_array_equal(result.c2v, before_c2v)
    np.testing.assert_array_equal(result.cache.values, before_cache)
    assert tree.leaf_events() == ()


def test_e_selections_form_one_source_iteration_without_rounding_partial_progress():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress

    residual = _residual_module()
    table, kernel, v2c, c2v, syndrome = _irregular_fixture()
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    executor = CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt")
    progress = ScheduleProgress(0, 0)
    reference_v2c = v2c.copy()
    reference_c2v = c2v.copy()
    reference_cache = cache.values.copy()
    for expected_steps in range(1, table.edge_count + 1):
        expected_selected, reference_v2c, reference_c2v, reference_cache = _reference_lifecycle_step(
            table, kernel, reference_v2c, reference_c2v, reference_cache, syndrome, error_rate=0.1,
        )
        proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1)
        result = schedule.execute_local_step(
            executor, proposal, v2c=v2c, c2v=c2v, cache=cache, progress=progress, is_converged=lambda _candidate: False,
        )
        cache, c2v, progress = result.cache, result.c2v, result.progress
        assert result.selection.index == expected_selected
        np.testing.assert_allclose(v2c, reference_v2c)
        np.testing.assert_allclose(c2v, reference_c2v)
        np.testing.assert_allclose(cache.values, reference_cache)
        assert progress.local_steps == expected_steps
        assert progress.iteration == expected_steps // table.edge_count
        assert progress.cursor == (expected_steps % table.edge_count,)


def test_exception_during_candidate_assembly_rolls_back_messages_cache_and_leaves(monkeypatch):
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress

    residual = _residual_module()
    table, kernel, v2c, c2v, syndrome = _irregular_fixture()
    schedule = residual.SyndromeResidualSchedule(table, kernel=kernel)
    cache = schedule.initialize(v2c, c2v, syndrome, error_rate=0.1)
    before_v2c, before_c2v, before_cache = v2c.copy(), c2v.copy(), cache.values.copy()
    proposal = schedule.propose_local_step(v2c, c2v, cache, syndrome, error_rate=0.1)
    monkeypatch.setattr(kernel, "assemble_beliefs", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected")))
    tree = BudgetTree(limits=())

    with pytest.raises(RuntimeError, match="injected"):
        schedule.execute_local_step(
            CanonicalLocalStepExecutor(tree, scope="attempt"), proposal,
            v2c=v2c, c2v=c2v, cache=cache, progress=ScheduleProgress(0, 0), is_converged=lambda _candidate: False,
        )
    np.testing.assert_array_equal(v2c, before_v2c)
    np.testing.assert_array_equal(c2v, before_c2v)
    np.testing.assert_array_equal(cache.values, before_cache)
    assert tree.leaf_events() == ()
