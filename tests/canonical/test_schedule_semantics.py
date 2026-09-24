"""Executable local-unit contracts for canonical schedule policies."""

from __future__ import annotations

import numpy as np
import pytest


def _layer_api():
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, LayeredSchedule

    return BudgetTree, CanonicalLocalStepExecutor, ScheduleProgress, BinarySpaKernel, EdgeTable, LayeredSchedule


def _layer_executor():
    BudgetTree, CanonicalLocalStepExecutor, ScheduleProgress, BinarySpaKernel, EdgeTable, LayeredSchedule = _layer_api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    schedule = LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=((0,), (1,)), provenance="explicit")
    return CanonicalLocalStepExecutor(BudgetTree(limits=(), parents={}), scope="attempt"), ScheduleProgress, schedule


def test_layered_schedule_commits_one_conflict_free_layer_before_later_layer_reads_it():
    import bp_registry.canonical.schedules as schedules

    assert hasattr(schedules, "LayeredSchedule"), (
        "LayeredSchedule must provide the source-qualified local-layer production API"
    )
    executor, ScheduleProgress, schedule = _layer_executor()
    messages = np.asarray([1.5, -0.7, 0.2, 2.0], dtype=np.float64)
    original = messages.copy()
    syndrome = np.asarray([0, 1], dtype=np.uint8)

    first = schedule.execute_local_step(
        executor,
        messages,
        syndrome,
        error_rate=0.2,
        progress=ScheduleProgress(iteration=0, local_steps=0, cursor=(0,)),
        is_converged=lambda _candidate: False,
    )
    assert first.admitted
    assert first.progress.cursor == (1,)
    assert first.proposed_work.candidate_checks == 1
    assert not np.array_equal(messages, original)

    second = schedule.execute_local_step(
        executor,
        messages,
        syndrome,
        error_rate=0.2,
        progress=first.progress,
        is_converged=lambda _candidate: False,
    )
    assert second.admitted
    assert second.progress.cursor == (2,)
    # Re-running layer 1 from the original snapshot produces a different result:
    # layer 2 is required to observe layer 1's committed V2C values.
    replay_messages = original.copy()
    standalone = schedule.execute_local_step(
        type(executor)(_layer_api()[0](limits=(), parents={}), scope="replay"),
        replay_messages,
        syndrome,
        error_rate=0.2,
        progress=ScheduleProgress(iteration=0, local_steps=0, cursor=(1,)),
        is_converged=lambda _candidate: False,
    )
    assert standalone.admitted
    assert not np.allclose(messages, replay_messages)
    assert second.candidate.shape == (2,)


@pytest.mark.parametrize(
    "partitions,match",
    [
        (None, "partitions"),
        ((), "at least one layer"),
        (((),), "must not be empty"),
        (((2,),), "unknown check"),
        (((0,),), "cover every check"),
        (((0, 1),), "conflicting"),
    ],
)
def test_layered_schedule_rejects_invalid_partitions_before_execution(partitions, match):
    _BudgetTree, _Executor, _Progress, BinarySpaKernel, EdgeTable, LayeredSchedule = _layer_api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    with pytest.raises(ValueError, match=match):
        LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=partitions, provenance="explicit")


def test_layered_schedule_records_repeated_t_cover_membership_and_structural_graph_identity():
    _BudgetTree, _Executor, _Progress, BinarySpaKernel, EdgeTable, LayeredSchedule = _layer_api()
    table = EdgeTable.from_edges(2, 3, [(0, 0), (1, 1), (1, 2)])
    schedule = LayeredSchedule(
        table,
        kernel=BinarySpaKernel(),
        partitions=((0,), (1,), (0,)),
        provenance="source_explicit",
    )
    evidence = schedule.evidence()
    assert evidence["provenance"] == "source_explicit"
    assert evidence["realized_order"] == (0, 1, 0)
    assert evidence["membership_multiplicity"] == ((0, 2), (1, 1))
    assert evidence["graph_identity"] == (2, 3, ((0, 0), (1, 1), (1, 2)))
    with pytest.raises(ValueError, match="text"):
        LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=(("0",), (1,)), provenance="explicit")


def _serial_api():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import (
        CheckNodeSerialSchedule,
        EdgeTable,
        ScheduleAttemptRegistry,
        VariableNodeSerialSchedule,
    )

    return (
        BudgetLimit,
        BudgetTree,
        CanonicalLocalStepExecutor,
        ScheduleProgress,
        BinarySpaKernel,
        EdgeTable,
        CheckNodeSerialSchedule,
        VariableNodeSerialSchedule,
        ScheduleAttemptRegistry,
    )


def test_check_node_serial_updates_a_check_then_refreshes_affected_variables():
    import bp_registry.canonical.schedules as schedules

    assert hasattr(schedules, "CheckNodeSerialSchedule"), (
        "CheckNodeSerialSchedule must expose the SCNS local-unit production API"
    )
    (
        _BudgetLimit,
        BudgetTree,
        CanonicalLocalStepExecutor,
        ScheduleProgress,
        BinarySpaKernel,
        EdgeTable,
        CheckNodeSerialSchedule,
        VariableNodeSerialSchedule,
        _Registry,
    ) = _serial_api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    initial = np.asarray([1.5, -0.7, 0.2, 2.0], dtype=np.float64)
    syndrome = np.asarray([0, 1], dtype=np.uint8)
    executor = CanonicalLocalStepExecutor(BudgetTree(limits=(), parents={}), scope="attempt")
    check_messages = initial.copy()
    check = CheckNodeSerialSchedule(table, kernel=BinarySpaKernel()).execute_local_step(
        executor, check_messages, syndrome, error_rate=0.2,
        progress=ScheduleProgress(iteration=0, local_steps=0, cursor=(0,)),
        is_converged=lambda _candidate: False,
    )
    assert check.admitted and check.progress.cursor == (1,)
    assert check.proposed_work.check_to_variable_updates == 2
    assert check.proposed_work.variable_to_check_updates == 4
    assert CheckNodeSerialSchedule(table, kernel=BinarySpaKernel()).evidence()["atomic_unit"] == "one_check_all_c2v_then_affected_v2c"

    variable_messages = initial.copy()
    variable = VariableNodeSerialSchedule(table, kernel=BinarySpaKernel()).execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=(), parents={}), scope="variable"),
        variable_messages, syndrome, error_rate=0.2,
        progress=ScheduleProgress(iteration=0, local_steps=0, cursor=(0,)),
        is_converged=lambda _candidate: False,
    )
    assert variable.admitted and variable.progress.cursor == (1,)
    assert variable.proposed_work.check_to_variable_updates == 0
    assert variable.proposed_work.variable_to_check_updates == 2
    assert not np.allclose(check_messages, variable_messages)


def test_serial_schedule_denial_retry_and_duplicate_shot_identity_do_not_share_or_double_commit():
    (
        BudgetLimit,
        BudgetTree,
        CanonicalLocalStepExecutor,
        ScheduleProgress,
        BinarySpaKernel,
        EdgeTable,
        CheckNodeSerialSchedule,
        _VariableNodeSerialSchedule,
        Registry,
    ) = _serial_api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    schedule = CheckNodeSerialSchedule(table, kernel=BinarySpaKernel())
    messages = np.asarray([1.5, -0.7, 0.2, 2.0], dtype=np.float64)
    before = messages.copy()
    progress = ScheduleProgress(iteration=0, local_steps=0, cursor=(0,))
    denied = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=(BudgetLimit("attempt", "candidate_checks", 0),), parents={}), scope="attempt"),
        messages, np.asarray([0, 1], dtype=np.uint8), error_rate=0.2, progress=progress,
        is_converged=lambda _candidate: False,
    )
    assert not denied.admitted
    np.testing.assert_array_equal(messages, before)
    assert denied.progress == progress

    registry = Registry()
    registry.claim("shot:17")
    with pytest.raises(ValueError, match="duplicate"):
        registry.claim("shot:17")
    assert registry.claim("shot:18") == "shot:18"


def test_randomized_traversal_replays_exact_order_at_declared_refresh_boundaries():
    import bp_registry.canonical.schedules as schedules

    assert hasattr(schedules, "RandomizedTraversalPlan"), (
        "RandomizedTraversalPlan must provide replayable schedule-order identity"
    )
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, LayeredSchedule, RandomizedTraversalPlan

    table = EdgeTable.from_edges(2, 3, [(0, 0), (1, 1), (1, 2)])
    base = LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=((0,), (1,)), provenance="explicit")
    for scope, boundary in (("configuration", "configuration"), ("attempt", "attempt"), ("sweep", "sweep")):
        plan = RandomizedTraversalPlan(base, refresh_scope=scope, root_identity="a" * 64)
        initial = plan.initial_state(configuration_identity="cfg", attempt_identity="shot:4")
        first = plan.refresh(initial, boundary=boundary, budgets=BudgetTree(limits=(), parents={}), budget_scope="attempt")
        replay = plan.refresh(initial, boundary=boundary, budgets=BudgetTree(limits=(), parents={}), budget_scope="attempt")
        assert first.admitted and replay.admitted
        assert first.order == replay.order
        assert first.state.realized_orders == (first.order,)
        assert first.state.derived_identity == replay.state.derived_identity


def test_randomized_refresh_denial_preserves_rng_order_and_physical_sample_identity(small_css_checks, monkeypatch):
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, LayeredSchedule, RandomizedTraversalPlan
    from bp_registry.css import CssCode
    from bp_registry.sampling import sample_shot

    table = EdgeTable.from_edges(2, 3, [(0, 0), (1, 1), (1, 2)])
    base = LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=((0,), (1,)), provenance="explicit")
    plan = RandomizedTraversalPlan(base, refresh_scope="sweep", root_identity="a" * 64)
    initial = plan.initial_state(configuration_identity="cfg", attempt_identity="shot:4")
    denied_tree = BudgetTree(limits=(), parents={})
    monkeypatch.setattr(denied_tree, "reserve", lambda *_args, **_kwargs: None)
    denied = plan.refresh(initial, boundary="sweep", budgets=denied_tree, budget_scope="attempt")
    assert not denied.admitted
    assert denied.state == initial
    assert denied.order is None

    hx, hz = small_css_checks
    code = CssCode(hx=hx, hz=hz)
    baseline = sample_shot(code, manifest_identity="b" * 64, shot_id=4, seed=11, x_error_rate=0.4)
    changed_order_policy = RandomizedTraversalPlan(base, refresh_scope="sweep", root_identity="c" * 64)
    assert changed_order_policy.initial_state(configuration_identity="cfg", attempt_identity="shot:4").derived_identity != initial.derived_identity
    matched = sample_shot(code, manifest_identity="b" * 64, shot_id=4, seed=999, x_error_rate=0.4)
    assert baseline.sample_identity == matched.sample_identity
    np.testing.assert_array_equal(baseline.hidden_x, matched.hidden_x)
