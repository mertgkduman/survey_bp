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


def _relay_manifest():
    from bp_registry.canonical.contracts import CanonicalManifestV4

    return CanonicalManifestV4.model_validate({
        "schema_version": 4, "run_id": "relay-boundary", "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 2, "error_rate": 0.1,
        "policies": {
            "update": {"kind": "binary_spa", "binding_id": "update", "state_lifetime": "message"},
            "schedule": {"kind": "flooding", "binding_id": "schedule", "state_lifetime": "iteration"},
            "state_memory": {"kind": "identity", "binding_id": "memory", "state_lifetime": "leg"},
            "intervention": {"kind": "identity", "binding_id": "intervention", "state_lifetime": "search"},
            "stopping": {"kind": "syndrome_or_budget", "binding_id": "stopping", "state_lifetime": "iteration"},
            "selection": {"kind": "stable_first", "binding_id": "selection", "state_lifetime": "attempt"},
            "postprocessing": {"kind": "identity", "binding_id": "post", "state_lifetime": "attempt"},
        },
        "memory_bindings": [{
            "binding_id": "relay-prior", "kind": "affine_prior", "target": "prior",
            "order": 0, "alpha": 0.5, "state_lifetime": "leg",
        }],
        "relay": {"total_leg_limit": 2, "legs": [{"max_iterations": 2}, {"max_iterations": 2}]},
    })


def _work_controls() -> dict[str, object]:
    from bp_registry.canonical.budgets import WorkVector

    return {"work_limits": {
        scope: {resource: 100 for resource in WorkVector.zero().as_evidence(structural_event_version=2)}
        for scope in ("shot", "search", "attempt")
    }}


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


def test_relay_inside_sweep_crossing_latches_before_later_leg_or_projection(tmp_path) -> None:
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.css import fixture_code
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeGuardV1
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    code = fixture_code()
    hidden_x = np.asarray([1, 0, 0], dtype=np.uint8)
    ticks = iter((10, 11, 14))
    guard = CanonicalRuntimeGuardV1(_authorization(deadline_ns=12), clock_ns=lambda: next(ticks))
    path = tmp_path / "relay.jsonl"

    with pytest.raises(CanonicalResourceInterruption):
        run_canonical_structural_shot(
            _relay_manifest(), code=code, observation=DecoderObservation("Z", code.hz @ hidden_x % 2),
            hidden_truth=HiddenTruth(hidden_x, np.zeros(code.n, dtype=np.uint8)), shot_id=0,
            ledger_path=path, sample_seed_identity="relay-seed", context={}, execution_controls=_work_controls(),
            resource_guard=guard,
        )
    prefix = [json.loads(line) for line in path.read_text().splitlines()]
    assert [event["kind"] for event in prefix] == ["shot_begin", "attempt"]
    assert guard.snapshot().boundary.endswith(":leg:0:sweep:1:after_work")
    assert guard.snapshot().overshoot_ns == 2


def test_trace_sidecar_reserves_exact_bytes_before_creating_file(tmp_path) -> None:
    from bp_registry.canonical.tracing import TracePlan, TraceSink
    from bp_registry.ledger import CanonicalResourceInterruption
    from bp_registry.runner import CanonicalRuntimeAuthorizationV1, CanonicalRuntimeGuardV1

    plan = TracePlan(root=tmp_path, max_records=2, max_bytes=4_096)
    baseline = TraceSink(plan)
    baseline.observe(kind="edge", iteration=0, payload={"message": [1, 0]})
    bytes_required = baseline.finish().bytes_written
    for path in tmp_path.glob("trace-sidecars/*.json"):
        path.unlink()

    exact_guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="e" * 64, authorization_identity="trace-exact", max_events=1,
        max_evidence_bytes=1, max_storage_bytes=bytes_required, control_receipt_reserve_bytes=1,
    ))
    exact = TraceSink(plan, resource_guard=exact_guard)
    exact.observe(kind="edge", iteration=0, payload={"message": [1, 0]})
    assert exact.finish().bytes_written == bytes_required
    assert exact_guard.snapshot().scientific_storage_bytes == bytes_required

    for path in tmp_path.glob("trace-sidecars/*.json"):
        path.unlink()
    denied_guard = CanonicalRuntimeGuardV1(CanonicalRuntimeAuthorizationV1.interruptible_unit(
        profile_digest="f" * 64, authorization_identity="trace-over", max_events=1,
        max_evidence_bytes=1, max_storage_bytes=bytes_required - 1, control_receipt_reserve_bytes=1,
    ))
    denied = TraceSink(plan, resource_guard=denied_guard)
    denied.observe(kind="edge", iteration=0, payload={"message": [1, 0]})
    with pytest.raises(CanonicalResourceInterruption):
        denied.finish()
    assert list(tmp_path.glob("trace-sidecars/*.json")) == []
    assert denied_guard.snapshot().scientific_storage_bytes == 0


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
