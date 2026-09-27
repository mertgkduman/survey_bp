"""Atomic local-step execution for the admitted Phase 4 memory operands."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.schedules import EdgeTable


def _composition(*kinds: str) -> MemoryCompositionSpec:
    target = {"pdbp_field_mix": "belief", "v2c_damping": "v2c"}
    parameters = {"pdbp_field_mix": {"gamma": 0.25}, "v2c_damping": {"gamma": 0.5}}
    return MemoryCompositionSpec.model_validate({"bindings": [
        {
            "binding_id": f"{kind}-{index}", "kind": kind, "target": target[kind],
            "parameters": parameters[kind], "order": index,
            "history_owner": f"history:{kind}-{index}", "state_lifetime": "attempt",
            "advance_boundary": "local_update", "refresh_boundary": "attempt_start",
            "source_status": "canonical_adaptation",
        }
        for index, kind in enumerate(kinds)
    ]})


def test_local_memory_uses_full_belief_then_v2c_operands_and_commits_once():
    from bp_registry.canonical.compatibility import validate_memory_compatibility
    from bp_registry.canonical.memory_execution import LocalMemoryExecution

    memory = _composition("pdbp_field_mix", "v2c_damping")
    assert validate_memory_compatibility(memory, update_rule="binary_spa", schedule="layered").admitted
    controller = LocalMemoryExecution(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), memory=memory,
    )
    controller.initialize(error_rate=0.1, initial_v2c=np.asarray([3.0, -2.0]), initial_beliefs=np.asarray([1.0, -1.0]))
    before = controller.evidence()
    controller.begin_step()
    beliefs = controller.transform_beliefs(np.asarray([5.0, 3.0]))
    messages = controller.transform_v2c(np.asarray([7.0, -6.0]))
    np.testing.assert_allclose(beliefs, [4.0, 2.0])
    np.testing.assert_allclose(messages, [5.0, -4.0])
    proposal = controller.proposal()
    assert controller.evidence() == before
    controller.commit(proposal)
    assert controller.evidence()["committed_local_updates"] == 1


def test_local_memory_rejects_order_and_preserves_history_on_abandoned_step():
    from bp_registry.canonical.memory_execution import LocalMemoryExecution

    with np.testing.assert_raises_regex(ValueError, "belief_then_v2c"):
        LocalMemoryExecution(EdgeTable.from_edges(1, 1, [(0, 0)]), memory=_composition("v2c_damping", "pdbp_field_mix"))
    controller = LocalMemoryExecution(EdgeTable.from_edges(1, 1, [(0, 0)]), memory=_composition("v2c_damping"))
    controller.initialize(error_rate=0.1, initial_v2c=np.asarray([1.0]), initial_beliefs=np.asarray([2.0]))
    before = controller.evidence()
    controller.begin_step()
    controller.transform_v2c(np.asarray([4.0]))
    controller.discard()
    assert controller.evidence() == before


def test_local_memory_budget_denial_rolls_back_the_pending_history():
    from bp_registry.canonical.budgets import BudgetLimit, BudgetTree
    from bp_registry.canonical.execution import CanonicalLocalStepExecutor, ScheduleProgress
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.memory_execution import LocalMemoryExecution
    from bp_registry.canonical.schedules import LayeredSchedule

    table = EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)])
    schedule = LayeredSchedule(table, kernel=BinarySpaKernel(), partitions=((0,),), provenance="explicit")
    controller = LocalMemoryExecution(table, memory=_composition("pdbp_field_mix", "v2c_damping"))
    messages = schedule.kernel.prior(0.1) * np.ones(table.edge_count)
    controller.initialize(error_rate=0.1, initial_v2c=messages, initial_beliefs=np.full(table.variable_count, schedule.kernel.prior(0.1)))
    before = controller.evidence()
    controller.begin_step()
    result = schedule.execute_local_step(
        CanonicalLocalStepExecutor(BudgetTree(limits=(BudgetLimit("attempt", "belief_assemblies", 0),), parents={}), scope="attempt"),
        messages, np.ones(1, dtype=np.uint8), error_rate=0.1, progress=ScheduleProgress(0, 0, (0,)),
        is_converged=lambda _candidate: False,
        transform_beliefs=controller.transform_beliefs, transform_v2c=controller.transform_v2c,
    )
    assert result.admitted is False
    controller.discard()
    assert controller.evidence() == before


def test_public_layered_memory_preflights_runs_and_replays(tmp_path):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.manifests import preflight

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 4, "run_id": "canonical-layered-local-memory"})
    manifest["policies"]["schedule"] = {
        "kind": "layered", "binding_id": "schedule-layered-explicit-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "partitions": [[0]], "provenance": "explicit",
    }
    manifest["memory"] = _composition("pdbp_field_mix", "v2c_damping").model_dump(mode="json")
    path = tmp_path / "local-memory.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert preflight(path).manifest.memory.bindings[0].advance_boundary.value == "local_update"
    output = tmp_path / "output"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    from bp_registry.ledger import read_canonical_events
    terminal = next(event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination")
    assert terminal["memory_execution"]["mode"] == "ordered_attempt_local_update"
    assert terminal["memory_execution"]["committed_local_updates"] == terminal["iterations"]
