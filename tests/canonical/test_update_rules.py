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
        proposed_work=WorkVector(check_to_variable_updates=1, candidate_checks=1),
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
        checks.resolve(graph_sha256="a" * 64, check_count=2, edge_count=3, source_iteration=0),
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
        {"shape": "check", "graph_sha256": "a" * 64, "values": [0.8]},
        {"shape": "edge", "graph_sha256": "b" * 64, "values": [0.8, 0.8, 0.8]},
        {"shape": "scalar", "value": 0.8, "values": [0.8]},
    ],
)
def test_explicit_normalization_assignments_reject_ambiguous_or_invalid_shapes(value):
    updates = _updates_module()
    with pytest.raises(ValueError):
        updates.ParameterAssignment.model_validate(value)
