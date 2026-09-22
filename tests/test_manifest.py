"""Contracts for strict executable manifests and immutable preflight."""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path

import pytest


def _artifact_payload() -> dict[str, object]:
    return {
        "format_version": 1,
        "hx": [[1, 1, 0]],
        "hz": [[0, 0, 1]],
        "lx": [[1, 0, 0]],
        "lz": [[1, 1, 0]],
    }


def _manifest(tmp_path: Path, **changes: object) -> dict[str, object]:
    root = tmp_path / "approved-artifacts"
    root.mkdir(exist_ok=True)
    artifact = root / "fixture.json"
    artifact.write_text(json.dumps(_artifact_payload(), separators=(",", ":")))
    raw = hashlib.sha256(artifact.read_bytes()).hexdigest()
    from bp_registry.artifacts import load_artifact
    from bp_registry.manifests import matrix_hashes

    loaded = load_artifact(root, artifact.name)
    semantic = loaded.semantic_sha256
    manifest: dict[str, object] = {
        "schema_version": 1,
        "run_id": "strict-fixture",
        "paper": {
            "uri": "https://arxiv.org/abs/2312.10950",
            "revision": "v2",
            "experiment_anchor": "Figure 2",
            "relation": "pilot_adaptation",
            "source_artifact_sha256": "a" * 64,
            "source_artifact_status": "verified",
        },
        "artifact": {
            "root": str(root),
            "path": artifact.name,
            "raw_sha256": raw,
            "semantic_sha256": semantic,
            "matrix_hashes": matrix_hashes(loaded.code),
            "format_version": 1,
            "code_id": "project-three-qubit-css-fixture",
        },
        "decoder": {
            "implementation": "ldpc",
            "version": version("ldpc"),
            "entry_point": "ldpc.BpDecoder",
            "bp_method": "product_sum",
            "schedule": "parallel",
            "input_vector_type": "syndrome",
            "parameter_names": [
                "error_rate", "max_iter", "bp_method", "schedule", "input_vector_type",
            ],
        },
        "noise": {"channel": "x_only_bit_flip", "x_error_rates": [0.0]},
        "seed_policy": {"root_seed": 12, "derivation": "sha256-manifest-shot-v1"},
        "budget": {
            "max_shots": 32,
            "max_iter": 10,
            "stopping_rule": "fixed_shots",
            "denominator_rule": "all_terminal_shots",
        },
        "environment": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "ldpc": version("ldpc"),
            "backend": "cpu",
        },
        "expected_output": {
            "status": "not_assessed",
            "reason": "Pilot has no prespecified curve criterion.",
            "values": [],
            "tolerance": None,
            "statistical_verdict": None,
        },
        "discrepancies": ["The project fixture is a pilot adaptation."],
    }
    manifest.update(changes)
    return manifest


def test_manifest_requires_complete_strict_provenance_and_round_trips_schema(tmp_path):
    from bp_registry.manifests import ManifestV1, parse_manifest

    value = _manifest(tmp_path)
    parsed = parse_manifest(value)
    assert isinstance(parsed, ManifestV1)
    assert parsed.model_dump(mode="json") == value
    schema = ManifestV1.model_json_schema()
    assert schema["additionalProperties"] is False
    assert ManifestV1.model_validate_json(parsed.model_dump_json()) == parsed

    missing = dict(value)
    missing.pop("environment")
    with pytest.raises(ValueError):
        parse_manifest(missing)
    with pytest.raises(ValueError):
        parse_manifest({**value, "unknown_key": "ignored"})
    with pytest.raises(ValueError):
        parse_manifest({**value, "schema_version": 2})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.01, 1.01, "0.1"])
def test_manifest_rejects_nonfinite_out_of_range_or_coerced_rates(tmp_path, value):
    from bp_registry.manifests import parse_manifest

    manifest = _manifest(tmp_path)
    manifest["noise"] = {"channel": "x_only_bit_flip", "x_error_rates": [value]}
    with pytest.raises(ValueError):
        parse_manifest(manifest)


@pytest.mark.parametrize("budget", [
    {"max_shots": 0, "max_iter": 10, "stopping_rule": "fixed_shots", "denominator_rule": "all_terminal_shots"},
    {"max_shots": 32, "max_iter": 0, "stopping_rule": "fixed_shots", "denominator_rule": "all_terminal_shots"},
    {"max_shots": 32, "max_iter": 100_001, "stopping_rule": "fixed_shots", "denominator_rule": "all_terminal_shots"},
])
def test_manifest_rejects_unbounded_or_invalid_compute_budgets(tmp_path, budget):
    from bp_registry.manifests import parse_manifest

    with pytest.raises(ValueError):
        parse_manifest(_manifest(tmp_path, budget=budget))


def test_not_assessed_requires_reason_and_cannot_claim_a_passing_verdict(tmp_path):
    from bp_registry.manifests import parse_manifest

    missing_reason = _manifest(tmp_path)
    missing_reason["expected_output"] = {
        "status": "not_assessed", "reason": "", "values": [], "tolerance": None,
        "statistical_verdict": None,
    }
    with pytest.raises(ValueError):
        parse_manifest(missing_reason)

    passing = _manifest(tmp_path)
    passing["expected_output"] = {
        "status": "not_assessed", "reason": "No curve.", "values": [], "tolerance": None,
        "statistical_verdict": "pass",
    }
    with pytest.raises(ValueError):
        parse_manifest(passing)


def test_preflight_confines_and_verifies_artifact_and_environment(tmp_path):
    from bp_registry.manifests import preflight

    resolved = preflight(_manifest(tmp_path))
    assert resolved.code.n == 3
    assert resolved.manifest.artifact.raw_sha256 == resolved.artifact.raw_sha256

    escaped = _manifest(tmp_path)
    escaped["artifact"] = {**escaped["artifact"], "path": "../fixture.json"}
    with pytest.raises(ValueError, match="escapes approved root"):
        preflight(escaped)

    changed = _manifest(tmp_path)
    changed["artifact"] = {**changed["artifact"], "raw_sha256": "0" * 64}
    with pytest.raises(ValueError, match="raw SHA-256"):
        preflight(changed)

    changed_matrix = _manifest(tmp_path)
    changed_matrix["artifact"] = {
        **changed_matrix["artifact"],
        "matrix_hashes": {**changed_matrix["artifact"]["matrix_hashes"], "hx_semantic_sha256": "0" * 64},
    }
    with pytest.raises(ValueError, match="Hx semantic SHA-256"):
        preflight(changed_matrix)

    wrong_environment = _manifest(tmp_path)
    wrong_environment["environment"] = {**wrong_environment["environment"], "ldpc": "0.0.0"}
    with pytest.raises(ValueError, match="environment"):
        preflight(wrong_environment)


def test_invalid_preflight_never_reaches_sampling_or_native_decode(tmp_path, monkeypatch):
    from bp_registry import runner

    calls: list[str] = []
    monkeypatch.setattr(runner.sampling, "sample_shot", lambda *args, **kwargs: calls.append("sample"))
    monkeypatch.setattr(runner.reference, "decode", lambda *args, **kwargs: calls.append("decode"))
    bad = _manifest(tmp_path)
    bad["paper"] = {**bad["paper"], "source_artifact_status": "unverified"}
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="source artifact"):
        runner.run_one(path, shot_id=0, ledger_path=tmp_path / "ledger.jsonl")
    assert calls == []


@pytest.mark.parametrize("mutation", [
    lambda manifest: manifest["artifact"].update({"path": "missing.json"}),
    lambda manifest: manifest["artifact"].update({"path": "../fixture.json"}),
    lambda manifest: manifest["artifact"].update({"semantic_sha256": "0" * 64}),
    lambda manifest: manifest["artifact"].update({"format_version": 2}),
])
def test_every_invalid_artifact_is_rejected_before_sampling_or_native_decode(
    tmp_path, monkeypatch, mutation
):
    from bp_registry import runner

    calls: list[str] = []
    monkeypatch.setattr(runner.sampling, "sample_shot", lambda *args, **kwargs: calls.append("sample"))
    monkeypatch.setattr(runner.reference, "decode", lambda *args, **kwargs: calls.append("decode"))
    manifest = _manifest(tmp_path)
    mutation(manifest)
    path = tmp_path / "invalid-artifact.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        runner.run_one(path, shot_id=0, ledger_path=tmp_path / "ledger.jsonl")
    assert calls == []


def test_runner_consumes_the_verified_resolved_experiment(tmp_path):
    from bp_registry.runner import run_one

    path = tmp_path / "complete.json"
    ledger = tmp_path / "ledger.jsonl"
    path.write_text(json.dumps(_manifest(tmp_path)))
    result = run_one(path, shot_id=2, ledger_path=ledger)
    events = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert result.shot_id == 2
    assert events[0]["kind"] == "begin"
    assert events[0]["decoder_config"]["error_rate"] == 0.0


def test_run_one_rejects_legacy_manifests(tmp_path):
    from bp_registry.runner import run_one

    legacy = {
        "schema_version": 1, "run_id": "legacy", "source_uri": "https://example.test/paper",
        "source_revision": "v1", "source_anchor": "table", "code_id": "project-three-qubit-css-fixture",
        "experiment_relation": "pilot_adaptation", "expected_output_status": "not_assessed",
        "x_error_rate": 0.0, "seed": 12, "max_iter": 10, "bp_method": "product_sum",
        "schedule": "parallel", "input_vector_type": "syndrome",
    }
    legacy_path = tmp_path / "legacy.json"
    legacy_ledger = tmp_path / "legacy-events.jsonl"
    legacy_path.write_text(json.dumps(legacy))
    with pytest.raises(ValueError, match="read-only"):
        run_one(legacy_path, shot_id=0, ledger_path=legacy_ledger)
    assert not legacy_ledger.exists()


def test_run_one_rejects_shots_outside_the_complete_manifest_budget(tmp_path):
    from bp_registry.runner import run_one

    manifest_path = tmp_path / "complete.json"
    ledger_path = tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(_manifest(tmp_path)))
    with pytest.raises(ValueError, match="outside the manifest budget"):
        run_one(manifest_path, shot_id=32, ledger_path=ledger_path)
    assert not ledger_path.exists()
