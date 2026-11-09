"""Atomic local-step execution for the admitted Phase 4 memory operands."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.schedules import EdgeTable


def _composition(*kinds: str, assignment: dict[str, object] | None = None) -> MemoryCompositionSpec:
    target = {
        "affine_prior": "prior",
        "pdbp_field_mix": "belief", "pdprime_delta_mix": "belief",
        "posterior_momentum": "posterior", "v2c_damping": "v2c",
    }
    parameters = {
        "affine_prior": {"alpha": 0.5},
        "pdbp_field_mix": {"gamma": 0.25}, "pdprime_delta_mix": {"gamma": 0.5},
        "posterior_momentum": {"alpha": 0.5, "gamma": 0.5}, "v2c_damping": {"gamma": 0.5},
    }
    return MemoryCompositionSpec.model_validate({"bindings": [
        {
            "binding_id": f"{kind}-{index}", "kind": kind, "target": target[kind],
            "parameters": parameters[kind], "order": index,
            "history_owner": f"history:{kind}-{index}", "state_lifetime": "attempt",
            "advance_boundary": "source_iteration" if kind == "affine_prior" else "local_update",
            "refresh_boundary": "attempt_start",
            "source_status": "canonical_adaptation",
            **({"assignment": assignment} if kind == "affine_prior" and assignment is not None else {}),
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


@pytest.mark.parametrize("schedule", ["layered", "check_node_serial", "variable_node_serial"])
@pytest.mark.parametrize("disordered", [False, True])
def test_local_pdprime_rejects_changing_prior_before_execution(schedule, disordered):
    from bp_registry.canonical.compatibility import validate_memory_compatibility
    from bp_registry.canonical.memory_execution import validate_single_attempt_memory, LocalMemoryExecution
    from bp_registry.canonical.policy_decoder import BinaryPolicy

    assignment = (dict(mode="uniform", low=.2, high=.8, root_seed_identity="f" * 64,
                       refresh_boundary="source_iteration", rng_algorithm="numpy.PCG64")
                  if disordered else None)
    memory = _composition("affine_prior", "pdprime_delta_mix", assignment=assignment)
    decision = validate_memory_compatibility(memory, update_rule="binary_spa", schedule=schedule)
    assert not decision.admitted and "pdprime_requires_fixed_prior" in decision.reason
    for construct in (
        lambda: validate_single_attempt_memory(memory, schedule=schedule),
        lambda: LocalMemoryExecution(EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), memory=memory),
        lambda: BinaryPolicy(schedule=schedule, memory=memory,
                             partitions=((0,),) if schedule == "layered" else None),
    ):
        with pytest.raises(ValueError, match="pdprime_requires_fixed_prior"):
            construct()


@pytest.mark.parametrize("schedule", ["layered", "check_node_serial", "variable_node_serial"])
def test_local_fixed_prior_pdprime_still_executes_and_replays(schedule):
    from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder

    decoder = BinaryPolicyDecoder(np.ones((2, 3), dtype=np.uint8), BinaryPolicy(
        schedule=schedule, memory=_composition("pdprime_delta_mix", "posterior_momentum", "v2c_damping"),
        max_iterations=3, partitions=((0,), (1,)) if schedule == "layered" else None))
    result = decoder.decode([0, 1], prior_llrs=[.8, -1.3, 2.])
    assert not result.converged
    assert result.ledger["execution"]["memory"]["committed_local_updates"] > 0
    assert decoder.verify_ledger(result.ledger_json)


def test_local_saturates_pdprime_history_before_the_next_unit_and_trace(tmp_path):
    from bp_registry.canonical.memory_execution import LocalMemoryExecution
    from bp_registry.canonical.tracing import TracePlan, TraceSink

    memory = MemoryCompositionSpec.model_validate({"bindings": [{
        "binding_id": "pdprime", "kind": "pdprime_delta_mix", "target": "belief",
        "parameters": {"gamma": 0.0}, "order": 0, "history_owner": "history:pdprime",
        "state_lifetime": "attempt", "advance_boundary": "local_update",
        "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation",
    }]})
    sink = TraceSink(TracePlan(tmp_path, max_records=4, max_bytes=16_384))
    controller = LocalMemoryExecution(
        EdgeTable.from_edges(1, 1, [(0, 0)]), memory=memory, trace_sink=sink,
        trace_context={"configuration_identity": "local-saturation", "decoder_identity": "shot-0"},
    )
    controller.initialize(error_rate=0.1, initial_v2c=np.asarray([0.0]), initial_beliefs=np.asarray([25.0]))
    for _ in range(2):
        controller.begin_step()
        np.testing.assert_allclose(
            controller.transform_beliefs(np.asarray([0.0]), np.asarray([25.0])), [25.0],
        )
        controller.commit(controller.proposal())
    result = controller.trace_result()
    assert result is not None and result.records == 2
    document = TraceSink.load(tmp_path, result.sidecar_path, expected_sha256=result.sha256)
    records = document["records"]
    assert [record["kind"] for record in records] == ["memory_local_update", "memory_local_update"]
    assert all(record["payload"]["beliefs"]["typed_array"]["values"] == [25.0] for record in records)
    assert all(record["payload"]["history_values"]["pdprime"]["field"]["typed_array"]["values"] == [25.0] for record in records)


def test_local_disordered_affine_prior_stages_rng_and_history_only_for_complete_traversals():
    from bp_registry.canonical.memory_execution import LocalMemoryExecution

    assignment = {
        "mode": "uniform", "low": 0.2, "high": 0.8,
        "root_seed_identity": "d" * 64, "refresh_boundary": "source_iteration",
        "rng_algorithm": "numpy.PCG64",
    }
    controller = LocalMemoryExecution(
        EdgeTable.from_edges(1, 1, [(0, 0)]),
        memory=_composition("affine_prior", "affine_prior", assignment=assignment),
        execution_context={"configuration_identity": "configuration", "decoder_identity": "decoder-shot-0"},
    )
    controller.initialize(error_rate=0.1, initial_v2c=np.asarray([0.0]), initial_beliefs=np.asarray([2.0]))
    before = controller.evidence()
    np.testing.assert_allclose(controller.begin_source_iteration(), [2.0])
    # An incomplete traversal neither advances PCG64 state nor leaks an
    # assignment record into terminal evidence.
    controller.abort_source_iteration()
    assert controller.evidence() == before
    np.testing.assert_allclose(controller.begin_source_iteration(), [2.0])
    controller.begin_step()
    controller.transform_beliefs(np.asarray([6.0]), np.asarray([0.0]))
    controller.commit(controller.proposal())
    controller.complete_source_iteration()
    evidence = controller.evidence()
    assert evidence["committed_source_iterations"] == 1
    assert controller.evidence()["memory_element_updates"] == {"affine_prior-0": 1, "affine_prior-1": 1}
    assignments = evidence["assignment_evidence"]
    assert set(assignments) == {"affine_prior-0", "affine_prior-1"}
    assert {item["algorithm"] for item in assignments.values()} == {"numpy.PCG64"}
    assert {item["replay_identity"] for item in assignments.values()} == {"decoder-shot-0:source_iteration:0"}
    staged = controller.begin_source_iteration()
    controller.abort_source_iteration()
    np.testing.assert_allclose(controller.begin_source_iteration(), staged)
    controller.abort_source_iteration()
    assert controller.evidence() == evidence


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


def test_public_local_memory_replays_the_declared_min_sum_kernel(tmp_path):
    """V5 local replay must not silently substitute the SPA default kernel."""
    from bp_registry.cli import run_canonical, verify_run

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({
        "schema_version": 4, "run_id": "canonical-layered-local-memory-min-sum",
        "numerical_profile": "cpu-float64-min-sum-v1",
    })
    manifest["policies"]["update"]["kind"] = "min_sum"
    manifest["policies"]["schedule"] = {
        "kind": "layered", "binding_id": "schedule-layered-min-sum-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "partitions": [[0]], "provenance": "explicit",
    }
    manifest["memory"] = _composition("pdbp_field_mix", "v2c_damping").model_dump(mode="json")
    path = tmp_path / "local-memory-min-sum.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2


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


@pytest.mark.parametrize("schedule_kind", ["layered", "check_node_serial", "variable_node_serial"])
def test_public_local_ordered_affine_prior_replays_for_each_deterministic_schedule(tmp_path, schedule_kind):
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 4, "run_id": f"canonical-{schedule_kind}-local-affine"})
    schedule = {
        "kind": schedule_kind, "binding_id": f"schedule-{schedule_kind}-local-affine-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
    }
    if schedule_kind == "layered":
        schedule.update({"partitions": [[0]], "provenance": "explicit"})
    manifest["policies"]["schedule"] = schedule
    manifest["memory"] = _composition("affine_prior", "affine_prior", "pdbp_field_mix", "v2c_damping").model_dump(mode="json")
    path = tmp_path / f"{schedule_kind}-affine.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / schedule_kind
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    terminals = [event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination"]
    assert all(
        data["memory_execution"]["committed_source_iterations"] <= data["memory_execution"]["committed_local_updates"]
        for data in terminals
    )
    assert all("assignment_evidence" not in data["memory_execution"] for data in terminals)


@pytest.mark.parametrize("schedule_kind", ["layered", "check_node_serial", "variable_node_serial"])
def test_public_local_disordered_affine_prior_has_trace_neutral_pcg64_replay(tmp_path, schedule_kind):
    """Public local memory binds draws to the decoder, never a trace or truth."""
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.canonical.tracing import TraceSink
    from bp_registry.ledger import read_canonical_events

    root = Path(__file__).resolve().parents[2]
    base = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    base.update({"schema_version": 4, "run_id": f"canonical-{schedule_kind}-local-disordered"})
    schedule = {
        "kind": schedule_kind, "binding_id": f"schedule-{schedule_kind}-local-disordered-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
    }
    if schedule_kind == "layered":
        schedule.update({"partitions": [[0]], "provenance": "explicit"})
    base["policies"]["schedule"] = schedule
    base["memory"] = _composition(
        "affine_prior", "pdbp_field_mix", "v2c_damping",
        assignment={
            "mode": "uniform", "low": 0.2, "high": 0.8,
            "root_seed_identity": "e" * 64, "refresh_boundary": "source_iteration",
            "rng_algorithm": "numpy.PCG64",
        },
    ).model_dump(mode="json")
    base["randomness"]["physical_sample_identity"] = f"local-disordered-{schedule_kind}-sample"
    off, on = tmp_path / f"{schedule_kind}-off.json", tmp_path / f"{schedule_kind}-on.json"
    for path, level in ((off, "off"), (on, "full")):
        manifest = json.loads(json.dumps(base))
        manifest["trace_plan"] = {
            "level": level, "relative_dir": "trace-sidecars",
            "max_records": 16 if level == "full" else 0,
            "max_bytes": 16_384 if level == "full" else 0,
            "label": "prespecified_campaign" if level == "full" else "development_default",
        }
        path.write_text(json.dumps(manifest), encoding="utf-8")
    off_output, on_output = tmp_path / f"{schedule_kind}-off", tmp_path / f"{schedule_kind}-on"
    assert run_canonical(off, off_output)["final_row_count"] == 2
    assert run_canonical(on, on_output)["final_row_count"] == 2
    assert verify_run(on_output)["final_row_count"] == 2
    off_terminal = [event["data"] for event in read_canonical_events(off_output / "events.jsonl") if event["kind"] == "termination"]
    on_terminal = [event["data"] for event in read_canonical_events(on_output / "events.jsonl") if event["kind"] == "termination"]
    assert [item["memory_execution"] for item in off_terminal] == [item["memory_execution"] for item in on_terminal]
    for item in on_terminal:
        memory = item["memory_execution"]
        if memory["committed_source_iterations"]:
            assert memory["assignment_evidence"]["affine_prior-0"]["algorithm"] == "numpy.PCG64"
        else:
            assert "assignment_evidence" not in memory
    links = [event for event in read_canonical_events(on_output / "events.jsonl") if event["kind"] == "trace_link"]
    documents = [
        TraceSink.load(on_output, event["sidecar"]["path"], expected_sha256=event["sidecar"]["sha256"])
        for event in links
    ]
    # The trace exposes only decoder identities; no physical truth enters a
    # local assignment or its PCG64 replay key.
    decoder_ids = {document["records"][0]["payload"]["decoder_identity"] for document in documents}
    assert len(decoder_ids) == 2
    assert "hidden_truth" not in str(documents)


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


def test_public_local_affine_trace_observes_only_completed_source_histories(tmp_path):
    from bp_registry.canonical.tracing import TraceSink
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    off, on = _public_local_trace_manifest(tmp_path, trace=False), _public_local_trace_manifest(tmp_path, trace=True)
    for path in (off, on):
        value = json.loads(path.read_text())
        value["memory"] = _composition("affine_prior", "pdbp_field_mix", "v2c_damping").model_dump(mode="json")
        path.write_text(json.dumps(value), encoding="utf-8")
    off_output, on_output = tmp_path / "affine-off", tmp_path / "affine-on"
    assert run_canonical(off, off_output)["final_row_count"] == 2
    assert run_canonical(on, on_output)["final_row_count"] == 2
    assert verify_run(on_output)["final_row_count"] == 2
    plain = [event["data"]["memory_execution"] for event in read_canonical_events(off_output / "events.jsonl") if event["kind"] == "termination"]
    linked = read_canonical_events(on_output / "events.jsonl")
    assert plain == [event["data"]["memory_execution"] for event in linked if event["kind"] == "termination"]
    links = [event for event in linked if event["kind"] == "trace_link"]
    documents = [TraceSink.load(on_output, event["sidecar"]["path"], expected_sha256=event["sidecar"]["sha256"]) for event in links]
    assert all(any(record["kind"] == "memory_source_iteration" for record in document["records"]) for document in documents)


def test_local_field_numerical_failure_discards_uncommitted_prior_histories(tmp_path, monkeypatch):
    from bp_registry.canonical.memory import PDBPFieldMix
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    original = PDBPFieldMix.propose

    def fail(*_args, **_kwargs):
        raise NumericalFailure("local-pdbp-injected")

    monkeypatch.setattr(PDBPFieldMix, "propose", fail)
    path = _public_local_trace_manifest(tmp_path, trace=False)
    manifest = json.loads(path.read_text())
    manifest["memory"] = _composition(
        "affine_prior", "pdbp_field_mix",
        assignment={
            "mode": "uniform", "low": 0.2, "high": 0.8,
            "root_seed_identity": "f" * 64, "refresh_boundary": "source_iteration",
            "rng_algorithm": "numpy.PCG64",
        },
    ).model_dump(mode="json")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "numerical"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    terminals = [event["data"] for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination"]
    assert all(data["memory_execution"]["committed_local_updates"] == 0 for data in terminals)
    assert all(data["memory_execution"]["committed_source_iterations"] == 0 for data in terminals)
    assert all("assignment_evidence" not in data["memory_execution"] for data in terminals)
    monkeypatch.setattr(PDBPFieldMix, "propose", original)


def test_public_v3_local_numerical_failure_replays_its_empty_schedule_prefix(tmp_path, monkeypatch):
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.cli import run_canonical, verify_run

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 3, "run_id": "canonical-v3-local-numerical"})
    manifest.pop("memory", None)
    manifest["policies"]["schedule"] = {
        "kind": "layered", "binding_id": "schedule-layered-v3-numerical-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "partitions": [[0]], "provenance": "explicit",
    }
    path = tmp_path / "v3-local-numerical.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    def fail(*_args, **_kwargs):
        raise NumericalFailure("v3-local-injected")

    monkeypatch.setattr(BinarySpaKernel, "check_message", fail)
    output = tmp_path / "output"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2


def test_public_v3_local_numerical_failure_replays_an_admitted_prefix(tmp_path, monkeypatch):
    """A failure in the second unit retains and verifies the first local commit."""
    from dataclasses import replace
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.canonical.schedules import LayeredSchedule
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest.update({"schema_version": 3, "run_id": "canonical-v3-local-numerical-prefix"})
    manifest["policies"]["schedule"] = {
        "kind": "layered", "binding_id": "schedule-layered-v3-numerical-prefix-v1",
        "state_lifetime": "iteration", "owned_state": [], "requires": [], "provides": [],
        "partitions": [[0]], "provenance": "explicit",
    }
    path = tmp_path / "v3-local-numerical-prefix.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    original = LayeredSchedule.execute_local_step
    calls = 0

    def fail_after_first(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise NumericalFailure("v3-local-after-first-commit")
        # Keep the actual first commit but make its candidate unavailable so
        # the execution reaches the next local unit before the injected fault.
        return replace(original(self, *args, **kwargs), candidate=None)

    monkeypatch.setattr(LayeredSchedule, "execute_local_step", fail_after_first)
    output = tmp_path / "output"
    assert run_canonical(path, output)["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    events = read_canonical_events(output / "events.jsonl")
    failed_shot = next(event["shot_id"] for event in events if event["kind"] == "termination" and event["termination"] == "numerical_failure")
    work = next(event["data"] for event in events if event["kind"] == "work" and event["shot_id"] == failed_shot)
    assert work["qualified_iterations"]["count"] == 1
