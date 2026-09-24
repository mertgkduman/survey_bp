"""Leaf-only work attribution and qualified resource fact contracts."""

from __future__ import annotations

import importlib

import pytest


def _api():
    budgets = importlib.import_module("bp_registry.canonical.budgets")
    assert hasattr(budgets, "QualifiedIteration"), (
        "canonical work accounting requires schedule-qualified iteration evidence"
    )
    return budgets


def _tree(api):
    return api.BudgetTree(
        limits=(),
        parents={"search": "shot", "member": "search", "leg": "member", "branch": "leg", "attempt": "branch"},
    )


def test_work_vector_retains_each_atomic_category_and_explicit_zeroes():
    api = _api()
    zero = api.WorkVector.zero()
    assert zero.as_evidence() == {
        "check_to_variable_updates": 0,
        "variable_to_check_updates": 0,
        "belief_assemblies": 0,
        "candidate_constructions": 0,
        "convergence_checks": 0,
        "order_generation": 0,
        "order_selection": 0,
        "residual_precomputations": 0,
        "residual_differences": 0,
        "priority_maintenance": 0,
        "residual_priority_evaluations": 0,
        "bp_calls": 0,
        "candidate_checks": 0,
        "intervention_actions": 0,
        "branch_expansions": 0,
        "branch_prunes": 0,
        "relay_transfers": 0,
        "fallback_calls": 0,
    }
    assert api.WorkVector(branch_expansions=1, relay_transfers=2, fallback_calls=3).as_evidence()["branch_expansions"] == 1
    with pytest.raises(ValueError, match="nonnegative"):
        api.WorkVector(bp_calls=-1)


def test_unique_leaf_events_reduce_to_all_lineage_ancestors_without_reemission():
    api = _api()
    tree = _tree(api)
    leaves = (
        ("branch", "branch-leaf", api.WorkVector(branch_expansions=1, branch_prunes=1)),
        ("leg", "relay-leaf", api.WorkVector(relay_transfers=2)),
        ("attempt", "fallback-leaf", api.WorkVector(fallback_calls=3, intervention_actions=1)),
    )
    for scope, leaf_id, delta in leaves:
        reservation = tree.reserve(scope, delta, leaf_id=leaf_id)
        assert reservation is not None
        reservation.commit_once()

    expected = api.WorkVector(branch_expansions=1, branch_prunes=1, relay_transfers=2, fallback_calls=3, intervention_actions=1)
    assert tree.summary("shot") == expected
    assert tree.summary("search") == expected
    assert tree.summary("member") == expected
    assert tree.summary("leg") == expected
    assert tree.summary("branch") == api.WorkVector(branch_expansions=1, branch_prunes=1, fallback_calls=3, intervention_actions=1)
    assert {leaf_id for leaf_id, _scope, _delta in tree.leaf_events()} == {"branch-leaf", "relay-leaf", "fallback-leaf"}


def test_iteration_and_runtime_measurements_keep_unit_precision_and_missingness():
    api = _api()
    iteration = api.QualifiedIteration(4, schedule="flooding", atomic_unit="complete_old_to_new_sweep")
    assert iteration.as_evidence() == {
        "count": 4,
        "schedule": "flooding",
        "atomic_unit": "complete_old_to_new_sweep",
    }

    observed = api.Measurement.observed(123, method="time.monotonic_ns", scope="attempt", unit="ns", precision="1 ns")
    missing = api.Measurement.unavailable(method="not_supported", scope="backend", unit="bytes", precision="unknown", reason="device counter unavailable")
    context = api.RuntimeResourceFacts(
        wall_time=observed,
        process_cpu_time=api.Measurement.unavailable(method="not_collected", scope="attempt", unit="ns", precision="unknown", reason="profiling disabled"),
        peak_host_memory=missing,
        concurrency=api.Measurement.observed(1, method="configured", scope="process", unit="threads", precision="exact"),
        machine_environment=api.Measurement.observed("fixture", method="fixture", scope="host", unit="identity", precision="exact"),
        backend_device_time=api.Measurement.unavailable(method="not_applicable", scope="backend", unit="ns", precision="unknown", reason="CPU execution"),
        backend_device_memory=missing,
    )
    assert context.as_evidence()["peak_host_memory"]["value"] is None
    assert context.as_evidence()["peak_host_memory"]["unavailable_reason"] == "device counter unavailable"
    with pytest.raises(ValueError, match="reason"):
        api.Measurement(None, method="missing", scope="attempt", unit="ns", precision="unknown")


def test_schedule_terminal_evidence_preserves_dual_views_partial_progress_and_legacy_work():
    """Phase-3 terminals must never collapse local progress or work into one scalar."""
    api = _api()
    assert hasattr(api, "ScheduleTerminalEvidence"), (
        "schedule terminals require a versioned evidence model with dual budget views"
    )
    from bp_registry.canonical.verification import reconstruct_schedule_terminal

    legacy = {
        "check_to_variable_updates": 2,
        "variable_to_check_updates": 2,
        "belief_assemblies": 1,
        "residual_priority_evaluations": 0,
        "bp_calls": 1,
        "candidate_checks": 1,
        "intervention_actions": 0,
        "branch_expansions": 0,
        "branch_prunes": 0,
        "relay_transfers": 0,
        "fallback_calls": 0,
    }
    assert api.WorkVector.from_evidence(legacy, structural_event_version=2).as_evidence(structural_event_version=2) == legacy

    evidence = api.ScheduleTerminalEvidence(
        schedule="layered",
        source_iteration=api.QualifiedIteration(0, schedule="layered", atomic_unit="one_layer"),
        completed_traversals=0,
        local_cursor=(1,),
        stopping_adaptation="D-09 after layer",
        work=api.WorkVector(check_to_variable_updates=2, convergence_checks=1),
        setup_runtime=api.Measurement.unavailable(method="not_measured", scope="schedule_setup", unit="ns", precision="unknown", reason="fixture"),
        decode_runtime=api.Measurement.observed(9, method="fixture", scope="decode", unit="ns", precision="exact"),
        budget_views=(
            api.BudgetView.common_c2v_cap(2),
            api.BudgetView.schedule_iteration_limit(api.QualifiedIteration(1, schedule="layered", atomic_unit="one_layer")),
        ),
    ).as_evidence()
    reconstructed = reconstruct_schedule_terminal(evidence)
    assert reconstructed == evidence
    assert reconstructed["budget_views"][0]["work_vector"] == reconstructed["budget_views"][1]["work_vector"]
    assert reconstructed["completed_traversals"] == 0
