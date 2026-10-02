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


def test_layered_local_unit_reserves_its_mandatory_convergence_check_before_mutation():
    """D-09 checks are part of, rather than subsequent to, local admission."""
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree, WorkVector
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.schedules import EdgeTable, LayeredSchedule

    assert "convergence_checks" in WorkVector.zero().as_evidence(), (
        "Phase 3 local schedules require a distinct, reservable convergence-check resource"
    )
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    schedule = LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=((0,), (1,)), provenance="explicit")
    messages = np.asarray([0.4, -0.2, 0.7, 1.3], dtype=np.float64)
    before = messages.copy()
    progress = ScheduleProgress(iteration=0, local_steps=0, cursor=(0,))
    proposal = schedule.propose_local_step(messages, np.asarray([0, 1], dtype=np.uint8), error_rate=0.1, progress=progress)
    assert proposal.proposed_work.convergence_checks == 1

    denied_tree = BudgetTree(limits=(BudgetLimit("attempt", "convergence_checks", 0),))
    denied = schedule.execute_local_step(
        CanonicalLocalStepExecutor(denied_tree, scope="attempt"), messages,
        np.asarray([0, 1], dtype=np.uint8), error_rate=0.1, progress=progress,
        is_converged=lambda _candidate: False,
    )
    assert not denied.admitted
    assert denied.progress == progress
    np.testing.assert_array_equal(messages, before)
    assert denied_tree.leaf_events() == ()

    admitted_tree = BudgetTree(limits=(BudgetLimit("attempt", "convergence_checks", 1),))
    admitted = schedule.execute_local_step(
        CanonicalLocalStepExecutor(admitted_tree, scope="attempt"), messages,
        np.asarray([0, 1], dtype=np.uint8), error_rate=0.1, progress=progress,
        is_converged=lambda _candidate: False,
    )
    assert admitted.admitted
    assert admitted.progress.local_steps == 1
    assert admitted.progress.cursor == (1,)
    assert admitted_tree.summary("attempt").convergence_checks == 1


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


def _two_check_local_execution_inputs(schedule: dict[str, object], *, max_iterations: int = 1):
    """A decoder-visible nonconverging fixture with two local checks."""
    from bp_registry.css import CssCode
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    def policy(role: str, kind: str) -> dict[str, object]:
        return {
            "kind": kind, "binding_id": f"{role}-v1", "state_lifetime": "attempt",
            "owned_state": [], "requires": [], "provides": [],
        }

    manifest = {
        "schema_version": 3, "run_id": "local-source-iteration-test",
        "numerical_profile": "cpu-float64-spa-v1", "max_iterations": max_iterations,
        # At p=1/2 all SPA messages remain zero, while the supplied nonzero
        # syndrome keeps the candidate outside the stopping condition.
        "error_rate": 0.5,
        "policies": {
            "update": policy("update", "binary_spa"),
            "schedule": schedule,
            "state_memory": policy("state-memory", "stateless"),
            "intervention": policy("intervention", "identity"),
            "stopping": policy("stopping", "syndrome_or_budget"),
            "selection": policy("selection", "stable_first"),
            "postprocessing": policy("postprocessing", "identity"),
        },
    }
    code = CssCode(
        hx=np.zeros((0, 4), dtype=np.uint8),
        hz=np.asarray([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8),
        lx=np.asarray([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8),
        lz=np.asarray([[1, 0, 0, 0], [0, 0, 1, 0]], dtype=np.uint8),
    ).validate()
    return (
        manifest, code, DecoderObservation("Z", np.asarray([1, 1], dtype=np.uint8)),
        HiddenTruth(np.asarray([1, 0, 1, 0], dtype=np.uint8), np.zeros(4, dtype=np.uint8)),
    )


@pytest.mark.parametrize(
    ("schedule", "expected_steps"),
    [
        ({"kind": "layered", "binding_id": "schedule-layered-v1", "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [], "partitions": [[0], [1]], "provenance": "explicit"}, 2),
        ({"kind": "check_node_serial", "binding_id": "schedule-check-node-serial-v1", "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": []}, 2),
        ({"kind": "variable_node_serial", "binding_id": "schedule-variable-node-serial-v1", "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": []}, 4),
        ({"kind": "residual", "binding_id": "schedule-residual-v1", "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": []}, 4),
    ],
)
def test_local_max_iterations_means_one_complete_source_traversal(tmp_path, schedule, expected_steps):
    """The public local executor must not stop after its first local unit."""
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.ledger import read_canonical_events
    from bp_registry.canonical.verification import PublicShotContext, _expected_local_attempt

    manifest, code, observation, hidden = _two_check_local_execution_inputs(schedule)
    ledger_path = tmp_path / "events.jsonl"
    result = run_canonical_structural_shot(
        manifest, code=code, observation=observation, hidden_truth=hidden,
        shot_id=0, ledger_path=ledger_path, sample_seed_identity="local-source-iteration-test",
        context={},
    )
    assert result.termination == "max_iterations"
    terminal = next(event["data"] for event in read_canonical_events(ledger_path) if event["kind"] == "termination")
    assert terminal["iterations"] == expected_steps
    assert terminal["schedule_terminal"]["completed_traversals"] == 1
    assert terminal["schedule_terminal"]["local_cursor"] == [0]

    replay = _expected_local_attempt(PublicShotContext(
        manifest_sha256="a" * 64, artifact_raw_sha256="b" * 64,
        artifact_semantic_sha256="c" * 64, compact_manifest=manifest,
        sample_seed_identity="local-source-iteration-test", run_id=manifest["run_id"],
        shot_id=0, check_type="Z", syndrome=(1, 1), code_id="two-check-test",
        evidence_relation="canonical_implemented", fixture="test",
        assessment_status="not_assessed", decoder_seed_identity="test",
        code=code, error_rate=0.5, max_iterations=1,
        schedule_kind=schedule["kind"],
    ))
    assert replay["iterations"] == expected_steps
    assert replay["progress"].iteration == 1
    assert replay["progress"].cursor == (0,)


@pytest.mark.parametrize("refresh_scope,expected_orders", [("configuration", 1), ("attempt", 1), ("sweep", 2)])
def test_randomized_execution_refreshes_at_its_declared_boundary(tmp_path, refresh_scope, expected_orders):
    """A sweep order is retained within a traversal and renewed only between sweeps."""
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.ledger import read_canonical_events

    schedule = {
        "kind": "randomized", "binding_id": "schedule-randomized-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "base_schedule": "layered", "refresh_scope": refresh_scope, "root_identity": "a" * 64,
        "partitions": [[0], [1]], "provenance": "explicit",
    }
    manifest, code, observation, hidden = _two_check_local_execution_inputs(schedule, max_iterations=2)
    ledger_path = tmp_path / "events.jsonl"
    result = run_canonical_structural_shot(
        manifest, code=code, observation=observation, hidden_truth=hidden,
        shot_id=0, ledger_path=ledger_path, sample_seed_identity="randomized-boundary-test",
        context={},
    )
    assert result.termination == "max_iterations"
    terminal = next(event["data"] for event in read_canonical_events(ledger_path) if event["kind"] == "termination")
    orders = terminal["schedule_evidence"]["randomized_traversal"]["realized_orders"]
    assert len(orders) == expected_orders
    assert terminal["iterations"] == 4


class _RecordingSpaKernel:
    """SPA delegate that exposes which C2V edges a local unit evaluated."""

    def __init__(self):
        from bp_registry.canonical.kernel import BinarySpaKernel

        self._delegate = BinarySpaKernel()
        self.profile = self._delegate.profile
        self.c2v_calls: list[tuple[int, int]] = []

    def prior(self, error_rate):
        return self._delegate.prior(error_rate)

    def check_message(self, incoming, syndrome, *, check_index=0, edge_index=0, source_iteration=0):
        self.c2v_calls.append((check_index, edge_index))
        return self._delegate.check_message(
            incoming, syndrome, check_index=check_index,
            edge_index=edge_index, source_iteration=source_iteration,
        )

    def assemble_beliefs(self, variable_count, edge_variables, messages, prior):
        return self._delegate.assemble_beliefs(variable_count, edge_variables, messages, prior)

    def variable_message(self, belief, check_message):
        return self._delegate.variable_message(belief, check_message)

    def candidate_from_beliefs(self, beliefs):
        return self._delegate.candidate_from_beliefs(beliefs)


@pytest.mark.parametrize(
    ("schedule_type", "first_edges", "second_edges"),
    [
        ("layered", ((0, 0), (0, 1)), ((1, 2), (1, 3))),
        ("check_node_serial", ((0, 0), (0, 1)), ((1, 2), (1, 3))),
        ("variable_node_serial", ((0, 0), (1, 2)), ((0, 1), (1, 3))),
    ],
)
def test_local_schedules_recompute_only_the_selected_c2v_edges_and_charge_them(schedule_type, first_edges, second_edges):
    """A later local unit must retain prior C2V state instead of re-evaluating it."""
    (
        _BudgetLimit,
        BudgetTree,
        CanonicalLocalStepExecutor,
        ScheduleProgress,
        _BinarySpaKernel,
        EdgeTable,
        CheckNodeSerialSchedule,
        VariableNodeSerialSchedule,
        _Registry,
    ) = _serial_api()
    table = EdgeTable.from_edges(2, 2, [(0, 0), (0, 1), (1, 0), (1, 1)])
    kernel = _RecordingSpaKernel()
    if schedule_type == "layered":
        from bp_registry.canonical.schedules import LayeredSchedule

        schedule = LayeredSchedule(table, kernel=kernel, partitions=((0,), (1,)), provenance="explicit")
    elif schedule_type == "check_node_serial":
        schedule = CheckNodeSerialSchedule(table, kernel=kernel)
    else:
        schedule = VariableNodeSerialSchedule(table, kernel=kernel)
    messages = np.asarray([1.5, -0.7, 0.2, 2.0], dtype=np.float64)
    syndrome = np.asarray([0, 1], dtype=np.uint8)
    executor = CanonicalLocalStepExecutor(BudgetTree(limits=(), parents={}), scope="attempt")

    first = schedule.execute_local_step(
        executor, messages, syndrome, error_rate=0.2,
        progress=ScheduleProgress(iteration=0, local_steps=0, cursor=(0,)),
        is_converged=lambda _candidate: False,
    )
    assert first.admitted
    assert tuple(kernel.c2v_calls) == first_edges
    assert first.proposed_work.check_to_variable_updates == len(first_edges)
    c2v_after_first = schedule._c2v.copy()

    second = schedule.execute_local_step(
        executor, messages, syndrome, error_rate=0.2, progress=first.progress,
        is_converged=lambda _candidate: False,
    )
    assert second.admitted
    assert tuple(kernel.c2v_calls) == first_edges + second_edges
    assert second.proposed_work.check_to_variable_updates == len(second_edges)
    unchanged = set(range(table.edge_count)).difference(edge for _check, edge in second_edges)
    for edge in unchanged:
        assert schedule._c2v[edge] == c2v_after_first[edge]


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
    assert variable.proposed_work.check_to_variable_updates == 2
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
