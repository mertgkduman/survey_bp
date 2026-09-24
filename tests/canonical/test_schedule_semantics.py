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
        CanonicalLocalStepExecutor(_layer_api()[0](limits=(), parents={}), scope="replay"),
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
