"""Atomic local-step execution for the admitted Phase 4 memory operands."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.schedules import EdgeTable


def _composition(*kinds: str) -> MemoryCompositionSpec:
    target = {
        "pdbp_field_mix": "belief", "pdprime_delta_mix": "belief",
        "posterior_momentum": "posterior", "v2c_damping": "v2c",
    }
    parameters = {
        "pdbp_field_mix": {"gamma": 0.25}, "pdprime_delta_mix": {"gamma": 0.5},
        "posterior_momentum": {"alpha": 0.5, "gamma": 0.5}, "v2c_damping": {"gamma": 0.5},
    }
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
    beliefs = controller.transform_beliefs(np.asarray([5.0, 3.0]), np.asarray([2.0, -1.0]))
    messages = controller.transform_v2c(np.asarray([7.0, -6.0]))
    np.testing.assert_allclose(beliefs, [4.0, 2.0])
    np.testing.assert_allclose(messages, [5.0, -4.0])
    proposal = controller.proposal()
    assert controller.evidence() == before
    controller.commit(proposal)
    assert controller.evidence()["committed_local_updates"] == 1


def test_local_pdprime_uses_matched_c2v_statistic_and_momentum_keeps_distinct_histories():
    from bp_registry.canonical.compatibility import validate_memory_compatibility
    from bp_registry.canonical.memory_execution import LocalMemoryExecution

    memory = _composition("pdprime_delta_mix", "posterior_momentum", "posterior_momentum")
    assert validate_memory_compatibility(memory, update_rule="binary_spa", schedule="check_node_serial").admitted
    controller = LocalMemoryExecution(EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), memory=memory)
    controller.initialize(error_rate=0.1, initial_v2c=np.asarray([0.0, 0.0]), initial_beliefs=np.asarray([1.0, -1.0]))
    controller.begin_step()
    # PD-prime sees the actual complete C2V vector, reduced as [2, -1], then
    # each momentum binding owns an independent posterior/velocity history.
    beliefs = controller.transform_beliefs(np.asarray([5.0, 3.0]), np.asarray([2.0, -1.0]))
    np.testing.assert_allclose(beliefs, [1.0625, -1.03125])
    proposal = controller.proposal()
    controller.commit(proposal)
    evidence = controller.evidence()
    assert evidence["memory_element_updates"] == {
        "pdprime_delta_mix-0": 4,
        "posterior_momentum-1": 4,
        "posterior_momentum-2": 4,
    }
    assert evidence["memory_c2v_reduction_additions"] == 2
    assert len(set(evidence["history_sha256"].values())) == 3


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


@pytest.mark.parametrize("schedule_kind", ["layered", "check_node_serial", "variable_node_serial"])
def test_public_local_pdprime_and_momentum_replay_for_each_exact_schedule(tmp_path, schedule_kind):
    from bp_registry.cli import run_canonical, verify_run

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 4, "run_id": f"canonical-{schedule_kind}-pdprime-momentum"})
    schedule = {
        "kind": schedule_kind, "binding_id": f"schedule-{schedule_kind}-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
    }
    if schedule_kind == "layered":
        schedule.update({"partitions": [[0]], "provenance": "explicit"})
    manifest["policies"]["schedule"] = schedule
    manifest["memory"] = _composition("pdprime_delta_mix", "posterior_momentum", "posterior_momentum").model_dump(mode="json")
    path = tmp_path / f"{schedule_kind}.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / schedule_kind
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2


def _public_local_trace_manifest(tmp_path, *, trace: bool, max_records: int = 16):
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 4, "run_id": "canonical-layered-local-trace"})
    manifest["randomness"]["physical_sample_identity"] = "local-trace-common-sample-v1"
    manifest["policies"]["schedule"] = {
        "kind": "layered", "binding_id": "schedule-layered-local-trace-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "partitions": [[0]], "provenance": "explicit",
    }
    manifest["memory"] = _composition("pdprime_delta_mix", "posterior_momentum").model_dump(mode="json")
    manifest["trace_plan"] = {
        "level": "full" if trace else "off", "relative_dir": "trace-sidecars",
        "max_records": max_records if trace else 0, "max_bytes": 16_384 if trace else 0,
        "label": "prespecified_campaign" if trace else "development_default",
    }
    path = tmp_path / ("local-trace-on.json" if trace else "local-trace-off.json")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_public_local_trace_is_observational_linked_and_capped(tmp_path):
    from bp_registry.canonical.tracing import TraceSink
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    off = _public_local_trace_manifest(tmp_path, trace=False)
    on = _public_local_trace_manifest(tmp_path, trace=True)
    off_output, on_output = tmp_path / "off", tmp_path / "on"
    assert run_canonical(off, off_output)["final_row_count"] == 2
    assert run_canonical(on, on_output)["final_row_count"] == 2
    assert verify_run(on_output)["final_row_count"] == 2
    off_terminal = [event["data"] for event in read_canonical_events(off_output / "events.jsonl") if event["kind"] == "termination"]
    on_events = read_canonical_events(on_output / "events.jsonl")
    on_terminal = [event["data"] for event in on_events if event["kind"] == "termination"]
    assert [data["memory_execution"] for data in off_terminal] == [data["memory_execution"] for data in on_terminal]
    links = [event for event in on_events if event["kind"] == "trace_link"]
    assert len(links) == 2 and all(event["data"]["status"] == "linked" for event in links)
    documents = [TraceSink.load(on_output, event["sidecar"]["path"], expected_sha256=event["sidecar"]["sha256"]) for event in links]
    assert all(document["records"][0]["kind"] == "memory_local_update" for document in documents)
    assert all(any(record["kind"] == "memory_candidate" for record in document["records"]) for document in documents)
    assert "hidden_truth" not in str(documents)

    capped = _public_local_trace_manifest(tmp_path, trace=True, max_records=1).rename(tmp_path / "local-trace-capped.json")
    capped_output = tmp_path / "capped"
    assert run_canonical(capped, capped_output)["final_row_count"] == 2
    capped_links = [event for event in read_canonical_events(capped_output / "events.jsonl") if event["kind"] == "trace_link"]
    assert all(event["sidecar"]["truncated"] and event["sidecar"]["dropped_records"] > 0 for event in capped_links)


def test_local_pdprime_numerical_failure_discards_uncommitted_histories(tmp_path, monkeypatch):
    from bp_registry.canonical.memory import PDPrimeDeltaMix
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    original = PDPrimeDeltaMix.propose

    def fail(*_args, **_kwargs):
        raise NumericalFailure("local-pdprime-injected")

    monkeypatch.setattr(PDPrimeDeltaMix, "propose", fail)
    path = _public_local_trace_manifest(tmp_path, trace=False)
    output = tmp_path / "numerical"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    terminals = [event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination"]
    assert all(data["memory_execution"]["committed_local_updates"] == 0 for data in terminals)
    monkeypatch.setattr(PDPrimeDeltaMix, "propose", original)
