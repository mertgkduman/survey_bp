"""Independent boundary oracle for the Phase 3 min-sum update contract."""

from __future__ import annotations

import importlib
import importlib.util

import numpy as np
import pytest


def _updates_module():
    """Import only after the assertion makes a missing implementation a valid RED."""
    spec = importlib.util.find_spec("bp_registry.canonical.updates")
    assert spec is not None, "Phase 3 must provide bp_registry.canonical.updates"
    return importlib.import_module("bp_registry.canonical.updates")


def test_min_sum_public_update_contract_exists():
    updates = _updates_module()
    assert hasattr(updates, "CheckUpdateRule")
    assert hasattr(updates, "MinSumUpdate")
    assert hasattr(updates, "UpdateRuleEvidence")


@pytest.mark.parametrize(
    ("incoming", "syndrome", "expected"),
    [
        (np.asarray([2.0, -3.0, 4.0]), 0, -2.0),
        (np.asarray([2.0, -3.0, 4.0]), 1, 2.0),
        (np.asarray([0.0, -0.5, 0.5]), 0, 0.0),
        (np.asarray([1.0, -1.0, 4.0]), 0, -1.0),
        (np.asarray([], dtype=np.float64), 0, 25.0),
        (np.asarray([], dtype=np.float64), 1, -25.0),
    ],
)
def test_min_sum_matches_hand_calculated_signed_minimum(incoming, syndrome, expected):
    update = _updates_module().MinSumUpdate()
    assert update.check_to_variable(incoming, syndrome=syndrome) == expected


def test_min_sum_saturates_only_after_formed_magnitude_and_rejects_nonfinite_input():
    update = _updates_module().MinSumUpdate()
    below = np.nextafter(25.0, 0.0)
    above = np.nextafter(25.0, np.inf)
    assert update.check_to_variable(np.asarray([below, above]), syndrome=0) == below
    assert update.check_to_variable(np.asarray([above, above]), syndrome=0) == 25.0
    with pytest.raises(Exception, match="nonfinite"):
        update.check_to_variable(np.asarray([np.inf]), syndrome=0)


def test_local_step_denial_preserves_every_owned_state_byte_for_byte():
    updates = _updates_module()
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree, WorkVector
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, LocalStepProposal, ScheduleProgress

    messages = np.asarray([1.0, -2.0], dtype=np.float64)
    progress = ScheduleProgress(iteration=0, local_steps=0, cursor=(0,), rng_state=("seed", 1))
    cache = {"residual": (0.5,)}
    tree = BudgetTree(
        limits=(BudgetLimit("attempt", "candidate_checks", 0),),
        parents={"attempt": "search", "search": "shot"},
    )
    proposal = LocalStepProposal(
        label="test-step",
        proposed_work=WorkVector(check_to_variable_updates=1, candidate_checks=1, convergence_checks=1),
        compute=lambda: np.asarray([9.0, 9.0]),
    )
    result = CanonicalLocalStepExecutor(tree, scope="attempt").execute(
        proposal,
        messages=messages,
        progress=progress,
        policy_state={"update": updates.MinSumUpdate()},
        cache=cache,
        is_converged=lambda _: False,
    )
    assert result.admitted is False
    np.testing.assert_array_equal(messages, np.asarray([1.0, -2.0]))
    assert progress == ScheduleProgress(iteration=0, local_steps=0, cursor=(0,), rng_state=("seed", 1))
    assert cache == {"residual": (0.5,)}


def test_normalized_min_sum_and_explicit_assignments_have_a_closed_graph_bound_contract():
    updates = _updates_module()

    scalar = updates.ParameterAssignment.model_validate({"shape": "scalar", "value": 0.8})
    checks = updates.ParameterAssignment.model_validate(
        {"shape": "check", "graph_sha256": "a" * 64, "values": [0.8, 0.8]}
    )
    edges = updates.ParameterAssignment.model_validate(
        {"shape": "edge", "graph_sha256": "a" * 64, "values": [0.8, 0.8, 0.8]}
    )

    np.testing.assert_array_equal(
        scalar.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0),
        checks.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0, edge_checks=(0, 1, 0)),
    )
    np.testing.assert_array_equal(
        scalar.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0),
        edges.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0),
    )
    update = updates.NormalizedMinSumUpdate(alpha=scalar)
    assert update.check_to_variable(np.asarray([2.0, -3.0]), syndrome=0) == -1.6
    assert update.evidence().kind == "normalized_min_sum"
    assert update.evidence().provenance == "conventional"


@pytest.mark.parametrize(
    "value",
    [
        {"shape": "scalar", "value": -0.1},
        {"shape": "scalar", "value": float("inf")},
        {"shape": "scalar", "value": 0.8, "values": [0.8]},
    ],
)
def test_explicit_normalization_assignments_reject_ambiguous_or_invalid_shapes(value):
    updates = _updates_module()
    with pytest.raises(ValueError):
        updates.ParameterAssignment.model_validate(value)


def test_graph_bound_assignment_rejects_a_different_immutable_graph():
    updates = _updates_module()
    assignment = updates.ParameterAssignment.model_validate(
        {"shape": "edge", "graph_sha256": "b" * 64, "values": [0.8, 0.8, 0.8]}
    )
    with pytest.raises(ValueError, match="graph_sha256"):
        assignment.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0)


def test_graph_bound_assignment_rejects_a_wrong_declared_length_before_broadcasting():
    updates = _updates_module()
    assignment = updates.ParameterAssignment.model_validate(
        {"shape": "check", "graph_sha256": "a" * 64, "values": [0.8]}
    )
    with pytest.raises(ValueError, match="check_count"):
        assignment.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0, edge_checks=(0, 1, 0))


@pytest.mark.parametrize(
    ("incoming", "syndrome", "beta", "expected"),
    [
        (np.asarray([2.0, -3.0]), 0, 0.0, -2.0),
        (np.asarray([2.0, -3.0]), 0, 2.0, -0.0),
        (np.asarray([np.nextafter(2.0, 0.0)]), 1, 2.0, 0.0),
        (np.asarray([np.nextafter(2.0, np.inf)]), 1, 2.0, -(np.nextafter(2.0, np.inf) - 2.0)),
        (np.asarray([30.0]), 0, 1.0, 25.0),
    ],
)
def test_offset_min_sum_matches_independent_float64_boundary_oracle(incoming, syndrome, beta, expected):
    updates = _updates_module()
    assignment = updates.ParameterAssignment.model_validate({"shape": "scalar", "value": beta})
    observed = updates.OffsetMinSumUpdate(beta=assignment).check_to_variable(incoming, syndrome=syndrome)
    assert observed == expected


@pytest.mark.parametrize("value", [
    {"shape": "scalar", "value": -0.1},
    {"shape": "scalar", "value": float("nan")},
    {"shape": "scalar", "value": float("inf")},
])
def test_offset_min_sum_rejects_invalid_beta_before_execution(value):
    updates = _updates_module()
    with pytest.raises(ValueError):
        updates.ParameterAssignment.model_validate(value)


def test_offset_min_sum_source_iteration_uses_schedule_iteration_not_local_step_count():
    updates = _updates_module()
    beta = updates.ParameterAssignment.model_validate(
        {"shape": "source_iteration", "values": [0.25, 1.5]}
    )
    update = updates.OffsetMinSumUpdate(beta=beta)
    assert update.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=0) == 1.75
    assert update.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=1) == 0.5
    with pytest.raises(ValueError, match="source_iteration"):
        update.check_to_variable(np.asarray([2.0]), syndrome=0, source_iteration=2)


def test_parameter_generation_replays_and_commits_only_after_admission():
    updates = _updates_module()

    class _Reservation:
        active = True

        def commit_once(self):
            self.active = False

        def rollback(self):
            self.active = False

    class _Budget:
        last_termination = {"reason": "denied"}

        def __init__(self, admit=True):
            self.admit = admit

        def reserve(self, *_args, **_kwargs):
            return _Reservation() if self.admit else None

    spec = updates.ParameterGeneratorSpec.model_validate({
        "shape": "edge", "graph_sha256": "a" * 64, "distribution": "uniform",
        "low": 0.0, "high": 1.0, "root_seed_identity": "b" * 64,
    })
    plan = updates.ParameterRefreshPlan(scope="source_iteration", generator=spec)
    initial = plan.initial_state(configuration_identity="cfg", attempt_identity="attempt:1")
    denied = plan.refresh(
        initial, boundary="source_iteration", source_iteration=0, graph_sha256="a" * 64,
        check_count=2, edge_count=3, budgets=_Budget(False), budget_scope="attempt",
    )
    assert not denied.admitted and denied.state == initial and denied.assignment is None
    first = plan.refresh(
        initial, boundary="source_iteration", source_iteration=0, graph_sha256="a" * 64,
        check_count=2, edge_count=3, budgets=_Budget(), budget_scope="attempt",
    )
    replay = plan.refresh(
        initial, boundary="source_iteration", source_iteration=0, graph_sha256="a" * 64,
        check_count=2, edge_count=3, budgets=_Budget(), budget_scope="attempt",
    )
    assert first.admitted and first.assignment == replay.assignment
    assert first.state == replay.state
    assert first.evidence["purpose"] == "parameter_assignment"
    assert first.evidence["resolved_assignment"] == first.assignment.model_dump(mode="json")
    with pytest.raises(ValueError, match="source_iteration"):
        plan.refresh(
            initial, boundary="local_unit", source_iteration=0, graph_sha256="a" * 64,
            check_count=2, edge_count=3, budgets=_Budget(), budget_scope="attempt",
        )
