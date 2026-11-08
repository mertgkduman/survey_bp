"""Owned batch output and independent stored-run validation."""
from dataclasses import replace
import json
import numpy as np
import pytest
from bp_registry import cpu_batch
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.quaternary.problems import PauliCode
from bp_registry.resolution import STABLE_SPA_F64


def execute(family="binary", limit=3, stop=True, empty=False):
    h = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    s = np.array([[0, 0], [1, 0], [1, 1]], dtype=np.uint8)
    if empty:
        s = np.empty((0, 2), dtype=np.uint8)
    if family == "binary":
        graph = CompiledBinaryFlooding.from_check_matrix(h, policy=STABLE_SPA_F64)
        return graph, graph.run_batch(s, error_rate=.2, max_iterations=limit), {"error_rate": .2}
    graph = CompiledBp4Graph.from_code(PauliCode(checks=h), np.tile([.7, .1, .1, .1], (3, 1)), policy=STABLE_SPA_F64)
    return graph, graph.run_batch(s, max_iterations=limit, stop_on_convergence=stop), {}


@pytest.mark.parametrize("field", ("candidates", "iterations", "converged", "syndromes"))
def test_batch_arrays_cannot_reenable_writes(field):
    _, result, _ = execute()
    value = getattr(result, field)
    with pytest.raises(ValueError):
        value.setflags(write=True)
    with pytest.raises(ValueError):
        value.flat[0] = 0
    while isinstance(value.base, np.ndarray):
        value = value.base
        with pytest.raises(ValueError):
            value.setflags(write=True)


@pytest.mark.parametrize("field", ("candidates", "iterations", "converged", "syndromes", "evidence_json"))
def test_replacement_cannot_keep_stale_evidence(field):
    _, result, _ = execute()
    if field == "evidence_json":
        evidence = json.loads(result.evidence_json)
        evidence["max_iterations"] += 1
        value = json.dumps(evidence)
    else:
        value = getattr(result, field).copy()
        value.flat[-1] = not value.flat[-1] if value.dtype == bool else int(value.flat[-1]) ^ 1
    with pytest.raises(ValueError):
        replace(result, **{field: value})


@pytest.mark.parametrize("field,value", [
    ("candidates", np.zeros((1, 3), dtype=np.uint8)),
    ("candidates", np.full((3, 3), 2, dtype=np.uint8)),
    ("iterations", np.array([0., 1., 2.])),
    ("iterations", np.array([0, -1, 2])),
    ("converged", np.array([0, 1, 0])),
    ("syndromes", np.zeros((3, 1), dtype=np.uint8)),
    ("evidence_json", "{}"),
])
def test_direct_result_admission(field, value):
    _, result, _ = execute()
    fields = {name: getattr(result, name) for name in ("candidates", "iterations", "converged", "syndromes", "evidence_json")}
    fields[field] = value
    with pytest.raises(ValueError):
        cpu_batch.CpuBatchResult(**fields)


def test_constructor_owns_callers_buffers():
    _, result, _ = execute()
    arrays = [getattr(result, name).copy() for name in ("candidates", "iterations", "converged", "syndromes")]
    owned = cpu_batch.CpuBatchResult(*arrays, result.evidence_json)
    arrays[0][:] ^= 1
    np.testing.assert_array_equal(owned.candidates, result.candidates)


@pytest.mark.parametrize("family", ("binary", "pauli"))
@pytest.mark.parametrize("limit,stop,empty", ((0, True, False), (3, True, False), (3, False, False), (3, True, True)))
def test_stored_ledger_replays_candidate_validity_and_work(family, limit, stop, empty, tmp_path):
    graph, result, kwargs = execute(family, limit, stop, empty)
    path = tmp_path / "events.jsonl"
    result.write_ledger(path)
    assert cpu_batch.verify_cpu_batch_ledger(path, graph, **kwargs)["shots"] == len(result.candidates)


@pytest.mark.parametrize("field", ("candidate", "candidate_valid", "iterations", "syndrome", "work", "shot_index", "graph_prior_sha256", "termination"))
def test_stored_tampering_is_detected(field, tmp_path):
    graph, result, kwargs = execute()
    path = tmp_path / "events.jsonl"
    result.write_ledger(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    row = rows[-1]
    if field in ("candidate", "syndrome"):
        row[field][0] ^= 1
    elif field == "work":
        row[field]["bp_calls"] += 1
    elif field == "candidate_valid":
        row[field] = not row[field]
    elif field in ("iterations", "shot_index"):
        row[field] += 1
    else:
        row[field] = "forged"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError):
        cpu_batch.verify_cpu_batch_ledger(path, graph, **kwargs)


def test_failed_export_leaves_existing_ledger_unchanged(tmp_path, monkeypatch):
    _, result, _ = execute()
    path = tmp_path / "events.jsonl"
    path.write_text("existing evidence\n")
    original = cpu_batch.json.dumps
    def fail_row(value, **kwargs):
        if value.get("shot_index") == 1:
            raise ValueError("injected serialization failure")
        return original(value, **kwargs)
    monkeypatch.setattr(cpu_batch.json, "dumps", fail_row)
    with pytest.raises(ValueError, match="injected"):
        result.write_ledger(path)
    assert path.read_text() == "existing evidence\n"
    assert list(tmp_path.iterdir()) == [path]


def test_historical_v1_ledger_is_verified_without_rewriting(tmp_path):
    graph, result, kwargs = execute()
    path = tmp_path / "events.jsonl"
    result.write_ledger(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        for key in ("batch_size", "variable_count", "check_count", "result_binding_sha256"):
            del row[key]
        row["backend"] = "numba-cpu-batch-v1"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    before = path.read_bytes()
    assert cpu_batch.verify_cpu_batch_ledger(path, graph, **kwargs)["shots"] == 3
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="identity"):
        cpu_batch.verify_cpu_batch_ledger(path, graph, error_rate=.3)


def test_rebinding_a_false_result_does_not_bypass_replay(tmp_path):
    graph, result, kwargs = execute()
    candidates = result.candidates.copy()
    candidates[0, 0] ^= 1
    evidence = json.loads(result.evidence_json)
    evidence["result_binding_sha256"] = cpu_batch._result_binding((candidates, result.iterations, result.converged, result.syndromes), evidence)
    forged = cpu_batch.CpuBatchResult(candidates, result.iterations, result.converged, result.syndromes, json.dumps(evidence))
    path = tmp_path / "events.jsonl"
    forged.write_ledger(path)
    with pytest.raises(ValueError, match="replay"):
        cpu_batch.verify_cpu_batch_ledger(path, graph, **kwargs)
