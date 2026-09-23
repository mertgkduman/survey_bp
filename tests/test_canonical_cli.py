"""End-to-end proof for the canonical CSS tracer."""

from __future__ import annotations

import json
import os
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
    assert [event["data"]["outcome"] for event in terminals] == ["logical_failure", "exact"]
    assert all(event["data"]["selection_status"] == "frozen_decoder_visible_candidate" for event in terminals)
    assert all(event["data"]["assessment_status"] == "not_assessed" for event in terminals)
    assert len([event for event in events if event["kind"] == "runtime"]) == 2
    assert all(
        event["data"]["profile"]["runtime"]["backend_device_time"]["value"] is None
        for event in events if event["kind"] == "runtime"
    )


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
    assert all(event["data"]["profile"]["enabled"] is True for event in events if event["kind"] == "runtime")
    assert all(event["data"].get("evidence_relation") == "canonical_implemented" for event in events)


def test_public_replay_rejects_same_run_changed_full_manifest_before_result(tmp_path):
    """A full-manifest change must not reuse a same-run structural terminal."""
    from bp_registry.canonical.execution import CanonicalConflictError
    from bp_registry.cli import run_canonical
    from bp_registry.runner import run_canonical_one
    from bp_registry.sampling import sample_shot
    from bp_registry.manifests import manifest_digest, preflight

    output = tmp_path / "canonical-result"
    ledger_path = output / "events.jsonl"
    run_canonical(CANONICAL_MANIFEST, output)
    changed = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    changed["evidence"]["procedure"] = "same baseline with a distinct documented procedure"
    changed_path = tmp_path / "changed-procedure.json"
    changed_path.write_text(json.dumps(changed), encoding="utf-8")

    original = preflight(CANONICAL_MANIFEST)
    altered = preflight(changed_path)
    assert np.array_equal(
        sample_shot(original.code, manifest_identity=manifest_digest(original.manifest), seed=original.manifest.randomness.sample_seed, shot_id=0, x_error_rate=original.manifest.error_rate).observation.syndrome,
        sample_shot(altered.code, manifest_identity=manifest_digest(altered.manifest), seed=altered.manifest.randomness.sample_seed, shot_id=0, x_error_rate=altered.manifest.error_rate).observation.syndrome,
    )
    before_result = (output / "result.json").read_bytes()
    with pytest.raises(CanonicalConflictError, match="conflicting canonical content"):
        run_canonical_one(changed_path, shot_id=0, ledger_path=ledger_path)
    with pytest.raises(CanonicalConflictError, match="conflicting canonical content"):
        run_canonical(changed_path, output)
    assert (output / "result.json").read_bytes() == before_result


def test_public_execution_identity_binds_manifest_code_sample_and_shot():
    from bp_registry.canonical.verification import public_execution_identity

    common = {
        "manifest_sha256": "m" * 64,
        "artifact_raw_sha256": "r" * 64,
        "artifact_semantic_sha256": "s" * 64,
        "compact_manifest": {"schema_version": 2, "run_id": "run"},
        "sample_seed_identity": "seed" * 16,
        "run_id": "run",
        "shot_id": 0,
        "check_type": "Z",
        "syndrome": [0, 1],
    }
    identity = public_execution_identity(**common)
    assert identity.startswith("sha256:")
    for field, changed in (("manifest_sha256", "x" * 64), ("artifact_raw_sha256", "y" * 64),
                           ("sample_seed_identity", "other"), ("shot_id", 1)):
        altered = dict(common)
        altered[field] = changed
        assert public_execution_identity(**altered) != identity


def _rewrite_rehashed_canonical_ledger(output: Path, mutate):
    """Apply an attacker-style semantic edit while retaining generic event hashes."""
    from hashlib import sha256

    from bp_registry.ledger import _canonical_event_id

    ledger_path = output / "events.jsonl"
    events = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    mutate(events)
    for event in events:
        event["event_id"] = _canonical_event_id(event)
    ledger_path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")
    result_path = output / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["ledger_sha256"] = sha256(ledger_path.read_bytes()).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("label", "mutate", "message"),
    [
        (
            "work",
            lambda events: next(event for event in events if event["kind"] == "termination")["data"]["work_vector"].__setitem__("bp_calls", 0),
            "work_vector",
        ),
        (
            "policy",
            lambda events: next(event for event in events if event["kind"] == "termination")["data"]["policy_effects"]["update"].__setitem__("effect", "identity_only"),
            "policy_effects",
        ),
    ],
)
def test_verify_run_rejects_rehashed_work_and_policy_tampering(tmp_path, label, mutate, message):
    from bp_registry.cli import run_canonical, verify_run

    output = tmp_path / label
    run_canonical(CANONICAL_MANIFEST, output)
    _rewrite_rehashed_canonical_ledger(output, mutate)
    with pytest.raises(ValueError, match=message):
        verify_run(output)


@pytest.mark.parametrize(
    ("label", "mutate", "message"),
    [
        (
            "sample",
            lambda events: next(event for event in events if event["kind"] == "shot_begin").__setitem__("sample_seed_identity", "tampered-sample"),
            "sample identity",
        ),
        (
            "lineage",
            lambda events: next(event for event in events if event["kind"] == "selection")["data"].__setitem__("candidate_lineage_id", "candidate-tampered"),
            "candidate_lineage_id",
        ),
        (
            "profile",
            lambda events: next(event for event in events if event["kind"] == "runtime")["data"]["profile"]["runtime"]["wall_time"].__setitem__("method", "untrusted"),
            "profile",
        ),
        (
            "trace",
            lambda events: next(event for event in events if event["kind"] == "runtime").__setitem__("sidecar", {"path": "trace.json", "sha256": "0" * 64}),
            "trace",
        ),
    ],
)
def test_verify_run_rejects_rehashed_structural_provenance_tampering(tmp_path, label, mutate, message):
    from bp_registry.cli import run_canonical, verify_run

    output = tmp_path / label
    run_canonical(CANONICAL_MANIFEST, output)
    _rewrite_rehashed_canonical_ledger(output, mutate)
    with pytest.raises(ValueError, match=message):
        verify_run(output)


def test_verify_run_rederives_budget_and_numerical_terminal_semantics(tmp_path, monkeypatch):
    from bp_registry.canonical.numerics import NumericalFailure
    from bp_registry.cli import run_canonical, verify_run
    from bp_registry.runner import run_canonical_one
    from bp_registry.canonical.schedules import FloodingSchedule

    budget_manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    budget_manifest["budgets"]["attempt"]["work_limits"]["check_to_variable_updates"] = 0
    budget_path = tmp_path / "cap.json"
    budget_path.write_text(json.dumps(budget_manifest), encoding="utf-8")
    budget_output = tmp_path / "cap-output"
    assert run_canonical(budget_path, budget_output)["final_row_count"] == 2
    assert verify_run(budget_output)["final_row_count"] == 2

    numerical_output = tmp_path / "numerical-output"
    original_sweep = FloodingSchedule.sweep
    monkeypatch.setattr(FloodingSchedule, "sweep", lambda *_args, **_kwargs: (_ for _ in ()).throw(NumericalFailure("transient nonfinite")))
    assert run_canonical_one(CANONICAL_MANIFEST, shot_id=0, ledger_path=numerical_output / "events.jsonl").termination == "numerical_failure"
    monkeypatch.setattr(FloodingSchedule, "sweep", original_sweep)
    report = run_canonical(CANONICAL_MANIFEST, numerical_output)
    assert verify_run(numerical_output)["final_row_count"] == report["final_row_count"] == 2
    numerical = next(event["data"] for event in __import__("bp_registry.ledger", fromlist=["read_canonical_events"]).read_canonical_events(numerical_output / "events.jsonl") if event["kind"] == "termination" and event["termination"] == "numerical_failure")
    assert numerical["verification_status"] == "not_independently_reproduced_numerical_failure"


def test_public_profile_plan_emits_typed_attempt_evidence(tmp_path):
    from bp_registry.ledger import read_canonical_events
    from bp_registry.runner import run_canonical_one

    ledger_path = tmp_path / "events.jsonl"
    run_canonical_one(CANONICAL_MANIFEST, shot_id=0, ledger_path=ledger_path)
    events = read_canonical_events(ledger_path)
    runtime = next(event["data"] for event in events if event["kind"] == "runtime")
    terminal = next(event["data"] for event in events if event["kind"] == "termination")

    profile = runtime["profile"]
    assert profile["enabled"] is True
    assert profile["level"] == "low_overhead"
    assert profile["runtime"]["wall_time"]["value"] is not None
    assert profile["runtime"]["backend_device_time"]["value"] is None
    assert profile["adapter_overhead"]["value"] is not None
    assert terminal["profile"] == profile

    disabled_manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text())
    disabled_manifest["profile_plan"]["enabled"] = False
    disabled_path = tmp_path / "disabled.json"
    disabled_path.write_text(json.dumps(disabled_manifest), encoding="utf-8")
    run_canonical_one(disabled_path, shot_id=0, ledger_path=tmp_path / "disabled-events.jsonl")
    disabled_events = read_canonical_events(tmp_path / "disabled-events.jsonl")
    disabled_profile = next(event["data"]["profile"] for event in disabled_events if event["kind"] == "runtime")
    assert disabled_profile["enabled"] is False
    assert disabled_profile["runtime"]["wall_time"]["value"] is None
    assert disabled_profile["runtime"]["wall_time"]["method"] == "not_collected"


def test_enabled_public_trace_plan_is_rejected_before_ledger(tmp_path):
    from bp_registry.runner import preflight_canonical, run_canonical_one

    manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text())
    manifest["trace_plan"]["level"] = "full"
    manifest["trace_plan"]["max_records"] = 1
    manifest["trace_plan"]["max_bytes"] = 1024
    manifest_path = tmp_path / "trace-enabled.json"
    ledger_path = tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="canonical trace plan.*off"):
        preflight_canonical(manifest_path)
    with pytest.raises(ValueError, match="canonical trace plan.*off"):
        run_canonical_one(manifest_path, shot_id=0, ledger_path=ledger_path)
    assert ledger_path.exists() is False


@pytest.mark.parametrize(
    "change",
    [
        {"level": "representative"},
        {"cohort": "representative"},
        {"cohort": "diagnostic"},
    ],
)
def test_public_preflight_rejects_unbounded_profile_cohorts_before_ledger(tmp_path, change):
    """Public Phase 2 profiling remains bounded until it has a cohort quota."""
    from bp_registry.runner import preflight_canonical, run_canonical_one

    manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    manifest["profile_plan"].update(change)
    manifest_path = tmp_path / "unbounded-profile.json"
    ledger_path = tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="profile plan.*clean.*low_overhead"):
        preflight_canonical(manifest_path)
    with pytest.raises(ValueError, match="profile plan.*clean.*low_overhead"):
        run_canonical_one(manifest_path, shot_id=0, ledger_path=ledger_path)
    assert ledger_path.exists() is False


def test_canonical_preflight_and_run_do_not_import_ldpc(tmp_path):
    script = """
import builtins
_real_import = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == 'ldpc' or name.startswith('ldpc.'):
        raise ImportError('ldpc deliberately unavailable')
    return _real_import(name, *args, **kwargs)
builtins.__import__ = blocked
from bp_registry.runner import preflight_canonical, run_canonical_one, run_one
from pathlib import Path
root = Path(__import__('os').environ['BP_REGISTRY_ROOT'])
output = Path(__import__('os').environ['BP_REGISTRY_OUTPUT'])
manifest = root / 'data/manifests/canonical-three-qubit-development.json'
assert preflight_canonical(manifest)['run_id'] == 'canonical-three-qubit-development'
assert run_canonical_one(manifest, shot_id=0, ledger_path=output / 'canonical-events.jsonl').termination == 'completed'
try:
    run_one(root / 'data/manifests/project-three-qubit-fixture.json', shot_id=0, ledger_path=output / 'native-events.jsonl')
except ImportError as error:
    assert 'ldpc deliberately unavailable' in str(error)
else:
    raise AssertionError('native reference path did not import ldpc')
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=REPOSITORY_ROOT, text=True, capture_output=True,
        env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT / "src"), "OMP_NUM_THREADS": "1", "BP_REGISTRY_ROOT": str(REPOSITORY_ROOT), "BP_REGISTRY_OUTPUT": str(tmp_path)},
    )
    assert completed.returncode == 0, completed.stderr


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
    work_limit_ref = scope_schema["work_limits"]["$ref"].removeprefix("#/$defs/")
    assert set(schema["$defs"][work_limit_ref]["properties"]) == expected_resources

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


def test_public_canonical_work_counts_one_bp_call_per_attempt(tmp_path):
    from bp_registry.ledger import read_canonical_events
    from bp_registry.runner import run_canonical_one

    ledger_path = tmp_path / "events.jsonl"
    result = run_canonical_one(CANONICAL_MANIFEST, shot_id=0, ledger_path=ledger_path)
    assert result.termination == "completed"
    events = read_canonical_events(ledger_path)
    work = next(event["data"]["work_vector"] for event in events if event["kind"] == "work")
    terminal = next(event["data"] for event in events if event["kind"] == "termination")
    assert work == terminal["work_vector"]
    assert work["bp_calls"] == 1


def test_public_cap_below_one_sweep_emits_scoped_denial(tmp_path):
    from bp_registry.ledger import read_canonical_events
    from bp_registry.runner import run_canonical_one

    manifest = json.loads((REPOSITORY_ROOT / CANONICAL_MANIFEST).read_text(encoding="utf-8"))
    manifest["budgets"]["attempt"]["work_limits"]["check_to_variable_updates"] = 0
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = run_canonical_one(manifest_path, shot_id=0, ledger_path=tmp_path / "events.jsonl")
    assert result.termination == "count_budget_exhausted"
    terminal = next(event["data"] for event in read_canonical_events(tmp_path / "events.jsonl") if event["kind"] == "termination")
    assert terminal["budget_termination"]["binding_scope"] == "attempt"
    assert terminal["budget_termination"]["resource"] == "check_to_variable_updates"
