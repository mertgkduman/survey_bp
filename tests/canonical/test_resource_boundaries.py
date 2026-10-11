"""Boundary-observed interruption regressions for canonical engine routes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


def _authorization(*, deadline_ns: int):
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1

    return CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="d" * 64,
        authorization_identity="boundary-fixture",
        max_events=100,
        max_evidence_bytes=100_000,
        max_storage_bytes=100_000,
        control_receipt_reserve_bytes=100,
        monotonic_deadline_ns=deadline_ns,
    )


def _v7_manifest() -> dict[str, object]:
    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 7
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    policies = value["policies"]
    assert isinstance(policies, dict)
    policies["update"].update({"kind": "normalized_min_sum", "parameter_assignment": {"shape": "scalar", "value": 0.875}})
    policies["schedule"].update({"kind": "check_node_serial"})
    policies["state_memory"].update({"kind": "identity"})
    value["ensemble"] = {
        "kind": "mbbp_ld", "source_status": "canonical_adaptation", "member_state": "independent",
        "max_iterations": 8, "max_member_c2v_updates": 100, "max_total_members": 2,
        "no_member_terminal": "no_member_converged_zero_return",
        "bases": [
            {"member_id": "member-0", "local_ordinal": 0, "partition_identity": "p0",
             "permutation_identity": "q0", "transform_kind": "one_hot_original_check_rows",
             "redundant_transforms": [[1]]},
            {"member_id": "member-1", "local_ordinal": 1, "partition_identity": "p1",
             "permutation_identity": "q1", "transform_kind": "one_hot_original_check_rows",
             "redundant_transforms": [[1]]},
        ],
    }
    value["list_selection"] = {"kind": "frequency_over_weight_plus_one", "tie_rule": "local_ordinal_then_lineage"}
    return value


def test_mbbp_inside_local_step_crossing_latches_before_later_member() -> None:
    from bp_registry.canonical.mbbp import MbbpBasis, MbbpController, MbbpSpec
    from bp_registry.canonical.problems import OriginalProblem
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeGuardV1

    original = OriginalProblem(
        "boundary-original", np.zeros((1, 3), dtype=np.uint8),
        np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8), np.asarray([1, 0], dtype=np.uint8),
    )
    bases = (
        MbbpBasis("first", 0, "p0", "q0", ((1, 1),)),
        MbbpBasis("later", 1, "p1", "q1", ((1, 0),)),
    )
    # before_member, before_step, then after the indivisible local step.
    ticks = iter((10, 11, 14))
    guard = CanonicalRuntimeGuardV1(_authorization(deadline_ns=12), clock_ns=lambda: next(ticks))

    def observe(boundary: str) -> None:
        if boundary.endswith(("before_member", "before_work")):
            guard.before_work(boundary)
        else:
            guard.after_work(boundary)

    with pytest.raises(CanonicalResourceInterruption):
        MbbpController(MbbpSpec(bases, max_iterations=2)).run(
            original, error_rate=0.1, boundary_observer=observe,
        )
    snapshot = guard.snapshot()
    assert snapshot.boundary == "mbbp:first:0:0:after_work"
    assert snapshot.overshoot_ns == 2
    assert guard.interrupted
    with pytest.raises(CanonicalResourceInterruption):
        guard.before_work("mbbp:later:before_member")


def test_phase5_inside_sweep_crossing_latches_before_later_phase5_work() -> None:
    from bp_registry.canonical.budgets import BudgetTree
    from bp_registry.canonical.contracts import Phase5InterventionContract
    from bp_registry.canonical.phase5 import execute_phase5_controller
    from bp_registry.canonical.problems import OriginalProblem
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeGuardV1

    spec = Phase5InterventionContract.model_validate({
        "kind": "identity", "lift_rule": "identity", "native_availability": "not_applicable",
        "operator": "identity", "preserved_fields": [], "qualification": "canonical_implemented",
        "reset_rule": "not_applicable", "selection": "stable_first",
        "source_revision": "project:canonical-baseline", "stream_status": "not_applicable",
        "trigger": "attempt_start", "unresolved": [], "variant": "identity_baseline_v1",
    })
    original = OriginalProblem(
        "phase5-boundary", np.zeros((1, 3), dtype=np.uint8),
        np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8), np.asarray([1, 0], dtype=np.uint8),
    )
    ticks = iter((10, 14))
    guard = CanonicalRuntimeGuardV1(_authorization(deadline_ns=12), clock_ns=lambda: next(ticks))
    budget = BudgetTree(limits=(), parents={"search": "shot", "attempt": "search"})

    def observe(boundary: str) -> None:
        if boundary.endswith(":before_work"):
            guard.before_work(boundary)
        else:
            guard.after_work(boundary)

    with pytest.raises(CanonicalResourceInterruption):
        execute_phase5_controller(
            spec, original, error_rate=0.1, budgets=budget, max_iterations=3,
            owner_identity="phase5-boundary", boundary_observer=observe,
        )
    snapshot = guard.snapshot()
    assert snapshot.boundary == "phase5:phase5-boundary:baseline:sweep:0:after_work"
    assert snapshot.overshoot_ns == 2
    assert len(budget.leaf_events()) == 1


def test_v7_interrupt_keeps_open_prefix_and_skips_projection_and_terminal(tmp_path) -> None:
    from bp_registry.canonical.execution import run_phase6_structural_shot
    from bp_registry.css import fixture_code
    from bp_registry.ledger import CanonicalResourceInterruption, CanonicalEventWriter
    from bp_registry.runner import CanonicalRuntimeGuardV1
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    value = _v7_manifest()
    code = fixture_code()
    syndrome = np.zeros(code.hz.shape[0], dtype=np.uint8)
    # Begin writer does not observe time.  The clock crosses only after the
    # first local member step, before any electorate projection can occur.
    ticks = iter((10, 11, 14))
    guard = CanonicalRuntimeGuardV1(_authorization(deadline_ns=12), clock_ns=lambda: next(ticks))
    path = tmp_path / "events.jsonl"

    with pytest.raises(CanonicalResourceInterruption):
        run_phase6_structural_shot(
            value, code=code, observation=DecoderObservation("Z", syndrome),
            hidden_truth=HiddenTruth(np.zeros(code.n, dtype=np.uint8), np.zeros(code.n, dtype=np.uint8)),
            shot_id=0, ledger_path=path, sample_seed_identity="seed", context={}, resource_guard=guard,
        )
    prefix = [json.loads(line) for line in path.read_text().splitlines()]
    assert [event["kind"] for event in prefix] == ["shot_begin"]
    assert guard.snapshot().boundary == "mbbp:member-0:0:0:after_work"
    assert guard.snapshot().overshoot_ns == 2

    # Context-manager unwind releases the writer's ownership before the caller
    # writes its separate interruption receipt.
    with CanonicalEventWriter(path, structural_event_version=6):
        pass
