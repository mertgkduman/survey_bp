"""End-to-end proof for the canonical CSS tracer."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest


def test_checked_canonical_manifest_has_a_strict_public_preflight_contract():
    """The development fixture is a public immutable experiment, not a kernel shortcut."""
    from pathlib import Path

    from bp_registry.manifests import CanonicalExperimentV2, preflight

    manifest_path = Path("data/manifests/canonical-three-qubit-development.json")
    schema_path = Path("data/manifests/schema-canonical-v2.json")
    assert schema_path.exists()
    assert manifest_path.exists()
    assert json.loads(schema_path.read_text(encoding="utf-8")) == CanonicalExperimentV2.model_json_schema()

    resolved = preflight(manifest_path)
    assert isinstance(resolved.manifest, CanonicalExperimentV2)
    assert resolved.manifest.evidence.relation == "canonical_implemented"
    assert resolved.manifest.evidence.fixture == "development_fixture"
    assert resolved.manifest.evidence.assessment_status == "not_assessed"
    assert set(type(resolved.manifest.policies).model_fields) == {
        "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
    }


def test_public_canonical_command_reconstructs_verified_structural_evidence(tmp_path):
    from pathlib import Path

    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    output = tmp_path / "canonical-result"
    report = run_canonical(Path("data/manifests/canonical-three-qubit-development.json"), output)
    assert report["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    events = read_canonical_events(output / "events.jsonl")
    assert [event["kind"] for event in events].count("termination") == 2
    assert [event["kind"] for event in events].count("runtime") == 2
    assert [event["kind"] for event in events].count("missingness") == 2
    assert all(event["data"].get("evidence_relation") == "canonical_implemented" for event in events)


def test_checked_canonical_result_is_idempotent_and_honestly_labeled():
    from pathlib import Path

    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.ledger import read_canonical_events

    manifest = Path("data/manifests/canonical-three-qubit-development.json")
    output = Path("data/results/canonical-three-qubit-development")
    first = run_canonical(manifest, output)
    second = run_canonical(manifest, output)
    assert first["final_row_count"] == second["final_row_count"] == 2
    assert verify_run(output)["final_row_count"] == 2
    terminals = [event for event in read_canonical_events(output / "events.jsonl") if event["kind"] == "termination"]
    assert [event["shot_id"] for event in terminals] == [0, 1]
    assert all(event["data"]["assessment_status"] == "not_assessed" for event in terminals)


def _manifest(run_id: str = "canonical-tracer") -> dict[str, object]:
    def policy(role: str, kind: str) -> dict[str, object]:
        return {
            "kind": kind,
            "binding_id": f"{role}-v1",
            "state_lifetime": "attempt",
            "owned_state": [],
            "requires": [],
            "provides": [],
        }

    return {
        "schema_version": 2,
        "run_id": run_id,
        "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 8,
        "error_rate": 0.1,
        "policies": {
            "update": policy("update", "binary_spa"),
            "schedule": policy("schedule", "flooding"),
            "state_memory": policy("state-memory", "stateless"),
            "intervention": policy("intervention", "identity"),
            "stopping": policy("stopping", "syndrome_or_budget"),
            "selection": policy("selection", "stable_first"),
            "postprocessing": policy("postprocessing", "identity"),
        },
    }


def _inputs():
    from bp_registry.css import fixture_code
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    code = fixture_code()
    truth = np.array([1, 0, 0], dtype=np.uint8)
    return code, DecoderObservation("Z", (code.hz @ truth) % 2), HiddenTruth(truth, np.zeros(3, dtype=np.uint8))


def test_manifest_runs_project_owned_kernel_then_independent_evaluation(tmp_path, monkeypatch):
    from bp_registry.canonical.execution import run_canonical_shot

    code, observation, hidden = _inputs()
    monkeypatch.setattr("bp_registry.reference.decode", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("native")))
    result = run_canonical_shot(_manifest(), code=code, observation=observation, hidden_truth=hidden,
                                shot_id=0, ledger_path=tmp_path / "events.jsonl")
    rows = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert result.evaluation is not None
    assert result.termination == "completed"
    assert [row["kind"] for row in rows] == ["begin", "terminal"]
    assert rows[-1]["outcome"] == result.evaluation.outcome
    assert rows[-1]["selection_status"] == "frozen_decoder_visible_candidate"


def test_replay_is_idempotent_conflicts_rejected_and_single_owner_is_terminal(tmp_path):
    from bp_registry.canonical.execution import CanonicalConflictError, run_canonical_shot

    code, observation, hidden = _inputs()
    path = tmp_path / "events.jsonl"
    first = run_canonical_shot(_manifest(), code=code, observation=observation, hidden_truth=hidden, shot_id=0, ledger_path=path)
    second = run_canonical_shot(_manifest(), code=code, observation=observation, hidden_truth=hidden, shot_id=0, ledger_path=path)
    assert (first.run_id, first.shot_id, first.termination, first.evaluation) == (second.run_id, second.shot_id, second.termination, second.evaluation)
    assert np.array_equal(first.candidate, second.candidate)
    conflicting = _manifest()
    conflicting["max_iterations"] = 7
    with pytest.raises(CanonicalConflictError):
        run_canonical_shot(conflicting, code=code, observation=observation, hidden_truth=hidden, shot_id=0, ledger_path=path)

    concurrent_path = tmp_path / "concurrent.jsonl"
    def execute():
        return run_canonical_shot(_manifest("concurrent"), code=code, observation=observation, hidden_truth=hidden, shot_id=1, ledger_path=concurrent_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result() for future in [pool.submit(execute), pool.submit(execute)]]
    assert outcomes[0].termination == outcomes[1].termination == "completed"
    assert sum(json.loads(line)["kind"] == "terminal" for line in concurrent_path.read_text().splitlines()) == 1


def test_numerical_failure_is_terminal_and_skips_evaluation(tmp_path, monkeypatch):
    from bp_registry.canonical.execution import run_canonical_shot
    from bp_registry.canonical.kernel import BinarySpaKernel
    from bp_registry.canonical.numerics import NumericalFailure

    code, observation, hidden = _inputs()
    evaluated = False
    def fail(*_args, **_kwargs):
        raise NumericalFailure("nonfinite message")
    def evaluator(*_args, **_kwargs):
        nonlocal evaluated
        evaluated = True
    monkeypatch.setattr(BinarySpaKernel, "run", fail)
    result = run_canonical_shot(_manifest(), code=code, observation=observation, hidden_truth=hidden,
                                shot_id=0, ledger_path=tmp_path / "events.jsonl", evaluate=evaluator)
    assert result.termination == "numerical_failure"
    assert result.evaluation is None
    assert evaluated is False
