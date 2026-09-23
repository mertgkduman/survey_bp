"""End-to-end proof for the canonical CSS tracer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MANIFEST = "data/manifests/canonical-three-qubit-development.json"


def test_documented_tutorial(tmp_path):
    """The public tutorial is executable from the approved environment, without fetching dependencies."""
    import bp_registry

    tutorial = (REPOSITORY_ROOT / "docs/canonical-engine.md").read_text(encoding="utf-8")
    assert ".venv/bin/python -m pip install --no-deps -e ." in tutorial
    assert "approved `.venv`" in tutorial
    assert Path(bp_registry.__file__).resolve().is_relative_to(REPOSITORY_ROOT / "src")

    output = tmp_path / "canonical-three-qubit-development"
    commands = [
        [sys.executable, "-m", "bp_registry.cli", "preflight", CANONICAL_MANIFEST],
        [sys.executable, "-m", "bp_registry.cli", "canonical", CANONICAL_MANIFEST, "--output", str(output)],
        [sys.executable, "-m", "bp_registry.cli", "reconcile", str(output / "events.jsonl")],
        [sys.executable, "-m", "bp_registry.cli", "verify-run", str(output)],
    ]
    reports = [
        json.loads(subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=True).stdout)
        for command in commands
    ]
    checked = json.loads((REPOSITORY_ROOT / "data/results/canonical-three-qubit-development/result.json").read_text())
    assert reports[0]["numerical_profile"] == "cpu-float64-spa-v1"
    assert reports[0]["resolved_numerical_profile"]["profile_id"] == "binary-spa-flooding-f64-v1"
    assert set(reports[0]["policies"]) == {
        "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
    }
    assert reports[0]["policy_identity"] == checked["policy_identity"]
    assert reports[1]["final_row_count"] == reports[2]["final_rows"] == reports[3]["final_row_count"] == 2

    from bp_registry.ledger import read_canonical_events

    events = read_canonical_events(output / "events.jsonl")
    terminals = [event for event in events if event["kind"] == "termination"]
    assert [event["data"]["outcome"] for event in terminals] == ["exact", "exact"]
    assert all(event["data"]["selection_status"] == "frozen_decoder_visible_candidate" for event in terminals)
    assert all(event["data"]["assessment_status"] == "not_assessed" for event in terminals)
    assert len([event for event in events if event["kind"] == "runtime"]) == 2
    assert len([event for event in events if event["kind"] == "missingness"]) == 2


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


def test_public_preflight_rejects_nonbaseline_executable_bindings(tmp_path):
    """Only the implemented Phase 2 baseline may cross the public boundary."""
    from bp_registry.manifests import preflight
    from bp_registry.runner import preflight_canonical

    baseline = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    admitted = preflight_canonical(REPOSITORY_ROOT / CANONICAL_MANIFEST)
    assert admitted["policy_effects"] == {
        "update": {"binding_id": "update-binary-spa-v1", "effect": "active"},
        "schedule": {"binding_id": "schedule-flooding-v1", "effect": "active"},
        "state_memory": {"binding_id": "state-memory-stateless-v1", "effect": "identity_only"},
        "intervention": {"binding_id": "intervention-identity-v1", "effect": "identity_only"},
        "stopping": {"binding_id": "stopping-syndrome-budget-v1", "effect": "active"},
        "selection": {"binding_id": "selection-stable-first-v1", "effect": "active"},
        "postprocessing": {"binding_id": "postprocessing-identity-v1", "effect": "identity_only"},
    }

    for role, replacement in (("update", "identity"), ("schedule", "identity"),
                              ("stopping", "identity"), ("selection", "identity")):
        altered = json.loads(json.dumps(baseline))
        altered["policies"][role]["kind"] = replacement
        with pytest.raises(ValueError, match="executable canonical baseline"):
            preflight(altered)

    all_identity = json.loads(json.dumps(baseline))
    for role in all_identity["policies"]:
        all_identity["policies"][role]["kind"] = "identity"
    with pytest.raises(ValueError, match="executable canonical baseline"):
        preflight(all_identity)


def test_public_budget_schema_uses_exact_work_resources():
    """Persisted caps must name every WorkVector resource without a scalar proxy."""
    from pydantic import ValidationError

    from bp_registry.canonical.budgets import WorkVector
    from bp_registry.manifests import CanonicalExperimentV2

    manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    expected_resources = set(WorkVector.zero().as_evidence())
    schema = CanonicalExperimentV2.model_json_schema()
    scope_schema = schema["$defs"]["CanonicalBudgetScopeV2"]["properties"]
    assert "max_work_units" not in scope_schema
    assert set(scope_schema["work_limits"]["properties"]) == expected_resources

    for scope in ("shot", "search", "attempt"):
        assert set(manifest["budgets"][scope]["work_limits"]) == expected_resources

    missing = json.loads(json.dumps(manifest))
    del missing["budgets"]["attempt"]["work_limits"]["bp_calls"]
    with pytest.raises(ValidationError):
        CanonicalExperimentV2.model_validate(missing)

    extra = json.loads(json.dumps(manifest))
    extra["budgets"]["attempt"]["work_limits"]["universal_work"] = 1
    with pytest.raises(ValidationError):
        CanonicalExperimentV2.model_validate(extra)

    boolean_limit = json.loads(json.dumps(manifest))
    boolean_limit["budgets"]["attempt"]["work_limits"]["bp_calls"] = True
    with pytest.raises(ValidationError):
        CanonicalExperimentV2.model_validate(boolean_limit)

    expanding_child = json.loads(json.dumps(manifest))
    expanding_child["budgets"]["attempt"]["work_limits"]["bp_calls"] = (
        expanding_child["budgets"]["search"]["work_limits"]["bp_calls"] + 1
    )
    with pytest.raises(ValidationError):
        CanonicalExperimentV2.model_validate(expanding_child)
