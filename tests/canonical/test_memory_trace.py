"""Bounded observation coverage for ordinary-memory sweeps."""

from __future__ import annotations

import numpy as np
import pytest

from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.canonical.tracing import TracePlan, TraceSink


def _public_disordered_manifest(tmp_path, *, trace: bool, max_records: int = 16):
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    value = json.loads((root / "data/manifests/canonical-three-qubit-development.json").read_text())
    value.update(
        schema_version=4,
        run_id="public-memory-trace-fixture",
        memory={"bindings": [{
            "binding_id": "affine", "kind": "affine_prior", "target": "prior",
            "parameters": {"alpha": 0.5}, "order": 0, "history_owner": "trace:affine",
            "state_lifetime": "attempt", "advance_boundary": "source_iteration",
            "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation",
            "retain_history": False,
            "assignment": {
                "mode": "uniform", "low": 0.2, "high": 0.8,
                "root_seed_identity": "c" * 64,
                "refresh_boundary": "source_iteration", "rng_algorithm": "numpy.PCG64",
            },
        }]},
    )
    value["randomness"]["physical_sample_identity"] = "public-memory-trace-common-sample-v1"
    value["budgets"]["max_shots"] = 2
    for scope in ("shot", "search", "attempt"):
        value["budgets"][scope]["max_iterations"] = 2
    value["trace_plan"] = {
        "level": "full" if trace else "off", "relative_dir": "trace-sidecars",
        "max_records": max_records if trace else 0,
        "max_bytes": 16_384 if trace else 0,
        "label": "prespecified_campaign" if trace else "development_default",
    }
    path = tmp_path / ("trace-on.json" if trace else "trace-off.json")
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _memory():
    return MemoryCompositionSpec.model_validate({"bindings": [{
        "binding_id": "affine", "kind": "affine_prior", "target": "prior",
        "parameters": {"alpha": 0.5}, "order": 0, "history_owner": "history:affine",
        "state_lifetime": "attempt", "advance_boundary": "source_iteration",
        "refresh_boundary": "attempt_start", "source_status": "canonical_adaptation",
    }]})


def test_memory_trace_observes_only_committed_sweeps_and_candidate_origin(tmp_path):
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule

    sink = TraceSink(TracePlan(tmp_path, max_records=4, max_bytes=16_384))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink, trace_context={"configuration_identity": "arm", "decoder_identity": "shot"},
    )
    initial = schedule.initialize(0.1)
    proposal = schedule.sweep(initial, np.ones(1, dtype=np.uint8), error_rate=0.1)
    assert sink.finish().sidecar_path is None
    # A fresh sink is used because finalization intentionally closes an observer.
    sink = TraceSink(TracePlan(tmp_path, max_records=4, max_bytes=16_384))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink, trace_context={"configuration_identity": "arm", "decoder_identity": "shot"},
    )
    initial = schedule.initialize(0.1)
    proposal = schedule.sweep(initial, np.ones(1, dtype=np.uint8), error_rate=0.1)
    schedule.commit(proposal)
    schedule.observe_candidate(origin={"candidate_lineage_id": "candidate-0", "status": "diagnostic"}, candidate=proposal.candidate)
    result = sink.finish()
    document = TraceSink.load(tmp_path, result.sidecar_path, expected_sha256=result.sha256)
    assert [record["kind"] for record in document["records"]] == ["memory_sweep", "memory_candidate"]
    payload = document["records"][0]["payload"]
    assert "beliefs" in payload and "history_sha256" in payload and "history_values" in payload
    assert "posterior" in payload["history_values"]["affine"]
    assert "hidden_truth" not in str(document)


def test_memory_trace_caps_are_explicit_and_do_not_change_memory_execution(tmp_path):
    from bp_registry.canonical.memory_execution import MemoryFloodingSchedule

    sink = TraceSink(TracePlan(tmp_path, max_records=1, max_bytes=4_096))
    schedule = MemoryFloodingSchedule(
        EdgeTable.from_edges(1, 2, [(0, 0), (0, 1)]), kernel=BinarySpaKernel(), memory=_memory(),
        trace_sink=sink,
    )
    messages = schedule.initialize(0.1)
    for iteration in range(2):
        proposal = schedule.sweep(messages, np.ones(1, dtype=np.uint8), error_rate=0.1, source_iteration=iteration)
        schedule.commit(proposal)
        messages = proposal.new_v2c
    result = sink.finish()
    assert result.records == 1 and result.truncated and result.dropped_records == 1
    assert schedule.evidence()["committed_iterations"] == 2


def test_public_v4_trace_links_committed_memory_and_keeps_assignment_rng_observational(tmp_path):
    """Public trace configuration cannot perturb per-shot ordinary-memory draws."""
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.canonical.tracing import TraceSink
    from bp_registry.ledger import read_canonical_events

    untraced_manifest = _public_disordered_manifest(tmp_path, trace=False)
    traced_manifest = _public_disordered_manifest(tmp_path, trace=True)
    untraced_output, traced_output = tmp_path / "untraced", tmp_path / "traced"
    assert run_canonical(untraced_manifest, untraced_output)["final_row_count"] == 2
    assert run_canonical(traced_manifest, traced_output)["final_row_count"] == 2
    assert verify_run(traced_output)["final_row_count"] == 2

    plain = [event for event in read_canonical_events(untraced_output / "events.jsonl") if event["kind"] == "termination"]
    traced_events = read_canonical_events(traced_output / "events.jsonl")
    terminal = [event for event in traced_events if event["kind"] == "termination"]
    assert [event["data"]["memory_execution"] for event in plain] == [event["data"]["memory_execution"] for event in terminal]
    assert [event["data"].get("diagnostic_candidate") for event in plain] == [event["data"].get("diagnostic_candidate") for event in terminal]

    links = [event for event in traced_events if event["kind"] == "trace_link"]
    assert len(links) == 2
    assert all(event["data"]["status"] == "linked" for event in links)
    assert all(event["sidecar"]["truncated"] is False for event in links)
    documents = [TraceSink.load(traced_output, event["sidecar"]["path"], expected_sha256=event["sidecar"]["sha256"]) for event in links]
    first = documents[0]["records"][0]
    assert first["kind"] == "memory_sweep"
    assert "history_values" in first["payload"] and "assignment_evidence" in first["payload"]
    assert all(any(record["kind"] == "memory_candidate" for record in document["records"]) for document in documents)
    draws = [event["data"]["memory_execution"]["assignment_evidence"]["affine"]["replay_identity"] for event in terminal]
    assert draws[0] != draws[1]

    capped_manifest = _public_disordered_manifest(tmp_path, trace=True, max_records=1)
    capped_manifest = capped_manifest.rename(tmp_path / "trace-capped.json")
    capped_output = tmp_path / "capped"
    assert run_canonical(capped_manifest, capped_output)["final_row_count"] == 2
    capped_links = [event for event in read_canonical_events(capped_output / "events.jsonl") if event["kind"] == "trace_link"]
    assert all(event["sidecar"]["truncated"] is True and event["sidecar"]["dropped_records"] > 0 for event in capped_links)


@pytest.mark.parametrize("mutation", ["empty", "belief", "history", "candidate"])
def test_public_trace_rejects_rehashed_nonsemantic_memory_sidecars(tmp_path, mutation):
    """A hash-valid sidecar still has to equal an independent memory replay."""
    import copy
    import hashlib
    import json

    from bp_registry.canonical.verification import CanonicalStructuralVerificationError, validate_canonical_shot
    from bp_registry.cli import run_canonical
    from bp_registry.ledger import read_canonical_events
    from bp_registry.runner import canonical_public_shot_context

    manifest = _public_disordered_manifest(tmp_path, trace=True)
    output = tmp_path / "output"
    assert run_canonical(manifest, output)["final_row_count"] == 2
    events = read_canonical_events(output / "events.jsonl")
    trace = next(event for event in events if event["kind"] == "trace_link" and event["shot_id"] == 0)
    document = TraceSink.load(output, trace["sidecar"]["path"], expected_sha256=trace["sidecar"]["sha256"])
    changed = copy.deepcopy(document)
    if mutation == "empty":
        changed["records"] = []
    elif mutation == "belief":
        changed["records"][0]["payload"]["beliefs"]["typed_array"]["values"][0] += 1.0
    elif mutation == "history":
        changed["records"][0]["payload"]["history_sha256"]["affine"] = "0" * 64
    else:
        candidate = next(record for record in reversed(changed["records"]) if record["kind"] == "memory_candidate")
        candidate["payload"]["candidate"]["typed_array"]["values"][0] ^= 1
    encoded = json.dumps(changed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    relative = f"trace-sidecars/rehashed-{mutation}.json"
    (output / relative).write_bytes(encoded)
    altered = copy.deepcopy(events)
    altered_trace = next(event for event in altered if event["kind"] == "trace_link" and event["shot_id"] == 0)
    altered_trace["sidecar"] = {
        **altered_trace["sidecar"], "path": relative, "sha256": hashlib.sha256(encoded).hexdigest(),
        "records": len(changed["records"]), "bytes": len(encoded),
    }
    with pytest.raises(CanonicalStructuralVerificationError, match="trace differs"):
        validate_canonical_shot(
            altered, canonical_public_shot_context(manifest, shot_id=0), trace_root=output,
        )
