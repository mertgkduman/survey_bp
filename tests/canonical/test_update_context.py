"""Integration contracts for indexed updates, replay and atomic admission."""
import numpy as np
import pytest

from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
from bp_registry.canonical.execution import AtomicFloodingExecutor, CanonicalLocalStepExecutor, ScheduleProgress
from bp_registry.canonical.group_shuffled import HsuGroupSchedule
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule, LayeredSchedule, CheckNodeSerialSchedule, VariableNodeSerialSchedule
from bp_registry.canonical.updates import ParameterAssignment, NormalizedMinSumUpdate, OffsetMinSumUpdate

H = np.ones((2, 2), dtype=np.uint8)
S = np.array([0, 1], dtype=np.uint8)  # Inconsistent: force every source iteration.
TABLE = EdgeTable.from_check_matrix(H)
LOCAL = (LayeredSchedule, CheckNodeSerialSchedule, VariableNodeSerialSchedule)


class RecordingRule:
    def __init__(self, rule):
        self.rule, self.calls = rule, []

    def __getattr__(self, name):
        return getattr(self.rule, name)

    def check_to_variable(self, incoming, **context):
        self.calls.append(context)
        return self.rule.check_to_variable(incoming, **context)


def make_rule(kind):
    assignment = ParameterAssignment(shape="source_iteration", values=(.2, .8, .4))
    return NormalizedMinSumUpdate(alpha=assignment) if kind == "nms" else OffsetMinSumUpdate(beta=assignment)


def make_schedule(cls, kernel):
    kwargs = dict(partitions=((0,), (1,)), provenance="explicit") if cls is LayeredSchedule else {}
    return cls(TABLE, kernel=kernel, **kwargs)


@pytest.mark.parametrize("kind", ("nms", "oms"))
@pytest.mark.parametrize("entry", ("standalone", "atomic"))
def test_flooding_source_iterations(kind, entry):
    rule = RecordingRule(make_rule(kind))
    kernel = BinarySpaKernel(update_rule=rule)
    if entry == "standalone":
        kernel.run(H, S, error_rate=.2, max_iterations=3)
    else:
        AtomicFloodingExecutor(FloodingSchedule(TABLE, kernel=kernel), BudgetTree(limits=()), scope="attempt").run_attempt(np.ones(4), S, error_rate=.2, max_iterations=3)
    assert {c["source_iteration"] for c in rule.calls} == {0, 1, 2}


@pytest.mark.parametrize("kind", ("nms", "oms"))
@pytest.mark.parametrize("cls", LOCAL)
@pytest.mark.parametrize("cursor", (0, 1))
def test_local_context_and_actual_arithmetic(kind, cls, cursor):
    rule = RecordingRule(make_rule(kind))
    schedule = make_schedule(cls, BinarySpaKernel(update_rule=rule))
    original = np.array([1., 2., 3., 4.])
    schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), original.copy(), S, error_rate=.2,
        progress=ScheduleProgress(1, 77, (cursor,)), is_converged=lambda _: False)
    assert rule.calls and {c["source_iteration"] for c in rule.calls} == {1}
    for context in rule.calls:
        edge, check = context["edge_index"], context["check_index"]
        assert TABLE.edges[edge][0] == check
        other = 2 * check + (1 - TABLE.edges[edge][1])
        expected = make_rule(kind).check_to_variable(np.array([original[other]]), syndrome=int(S[check]), check_index=check, edge_index=edge, source_iteration=1)
        assert schedule._c2v[edge] == expected


@pytest.mark.parametrize("cls", LOCAL)
def test_exhausted_assignment_and_denied_step_are_atomic(cls):
    rule = RecordingRule(make_rule("nms"))
    schedule = make_schedule(cls, BinarySpaKernel(update_rule=rule))
    messages = np.array([1., 2., 3., 4.])
    before = messages.copy()
    tree = BudgetTree(limits=(BudgetLimit("attempt", "convergence_checks", 0),))
    result = schedule.execute_local_step(CanonicalLocalStepExecutor(tree, scope="attempt"), messages, S, error_rate=.2,
        progress=ScheduleProgress(3, 9, (0,)), is_converged=lambda _: False)
    assert not result.admitted and not rule.calls
    tree = BudgetTree(limits=())
    with pytest.raises(ValueError):
        schedule.execute_local_step(CanonicalLocalStepExecutor(tree, scope="attempt"), messages, S, error_rate=.2,
            progress=ScheduleProgress(3, 9, (0,)), is_converged=lambda _: False)
    np.testing.assert_array_equal(messages, before)
    np.testing.assert_array_equal(schedule._c2v, np.zeros(4))
    assert tree.leaf_events() == ()


@pytest.mark.parametrize("cls", LOCAL)
def test_explicit_legacy_replay(cls):
    rule = RecordingRule(make_rule("nms"))
    kernel = BinarySpaKernel(update_rule=rule, update_context_version="legacy-zero-v1")
    kernel.run(H, S, error_rate=.2, max_iterations=3)
    assert {c["source_iteration"] for c in rule.calls} == {0}
    rule.calls.clear()
    schedule = make_schedule(cls, kernel)
    schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), np.ones(4), S, error_rate=.2,
        progress=ScheduleProgress(1, 77, (0,)), is_converged=lambda _: False)
    assert {c["source_iteration"] for c in rule.calls} == {0}
    assert schedule.evidence()["update_context_version"] == "legacy-zero-v1"
    rule.calls.clear()
    AtomicFloodingExecutor(FloodingSchedule(TABLE, kernel=kernel), BudgetTree(limits=()), scope="attempt").run_attempt(np.ones(4), S, error_rate=.2, max_iterations=3)
    assert {c["source_iteration"] for c in rule.calls} == {0, 1, 2}


def test_unknown_context_version_rejected():
    with pytest.raises(ValueError, match="context"):
        BinarySpaKernel(update_context_version="guess")


@pytest.mark.parametrize("kind", ("nms", "oms"))
def test_source_qualified_group_schedule_rejects_unqualified_update_compositions(kind):
    with pytest.raises(ValueError, match="plain SPA"):
        HsuGroupSchedule(TABLE, kernel=BinarySpaKernel(update_rule=make_rule(kind)), root_identity="a" * 64, attempt_identity="attempt")


@pytest.mark.parametrize("cls", LOCAL)
def test_randomized_order_preserves_iteration_and_canonical_edge_ids(cls):
    from bp_registry.canonical.schedules import RandomizedTraversalPlan
    rule = RecordingRule(make_rule("nms"))
    schedule = make_schedule(cls, BinarySpaKernel(update_rule=rule))
    plan = RandomizedTraversalPlan(schedule, refresh_scope="sweep", root_identity="a" * 64)
    state = plan.initial_state(configuration_identity="configuration", attempt_identity="attempt")
    tree = BudgetTree(limits=())
    messages = np.array([1., 2., 3., 4.])
    for iteration in range(3):
        refresh = plan.refresh(state, boundary="sweep", budgets=tree, budget_scope="attempt")
        state = refresh.state
        for ordinal, cursor in enumerate(refresh.order):
            rule.calls.clear()
            schedule.execute_local_step(CanonicalLocalStepExecutor(tree, scope=f"step-{iteration}-{ordinal}"), messages, S, error_rate=.2,
                progress=ScheduleProgress(iteration, iteration * 2 + ordinal, (cursor,)), is_converged=lambda _: False)
            assert {c["source_iteration"] for c in rule.calls} == {iteration}
            assert all(TABLE.edges[c["edge_index"]][0] == c["check_index"] for c in rule.calls)


@pytest.mark.parametrize("cls", LOCAL)
@pytest.mark.parametrize("kind", ("nms", "oms"))
def test_resolved_per_edge_assignment_unchanged_across_iterations(cls, kind):
    assignment = ParameterAssignment(shape="edge", values=(.1, .2, .3, .4), graph_sha256=TABLE.graph_sha256)
    rule = NormalizedMinSumUpdate(alpha=assignment, resolved_alpha=assignment.values) if kind == "nms" else OffsetMinSumUpdate(beta=assignment, resolved_beta=assignment.values)
    outputs = []
    for iteration in (0, 2):
        schedule = make_schedule(cls, BinarySpaKernel(update_rule=rule))
        messages = np.array([1., 2., 3., 4.])
        schedule.execute_local_step(CanonicalLocalStepExecutor(BudgetTree(limits=()), scope="attempt"), messages, S, error_rate=.2,
            progress=ScheduleProgress(iteration, 99, (1,)), is_converged=lambda _: False)
        outputs.append(messages)
    np.testing.assert_array_equal(*outputs)
