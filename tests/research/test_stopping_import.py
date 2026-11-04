"""Opt-in stopping and local-result import remain honest and portable."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from bp_registry.research.contracts import validate_experiment
from bp_registry.research.results import normalize_result_directory, persistent_import
from bp_registry.research.runner import run_experiment


def specimen() -> dict:
    return {"schema": "research-experiment-v1", "id": "stopping-import-fixture",
        "problem": {"kind": "css_code_capacity", "code": {"kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[0, 0, 1]], "lx": [[1, 0, 0]], "lz": [[1, 1, 0]]}},
        "channel": {"kind": "depolarizing"},
        "decoder": {"family": "binary_css", "implementation": "compiled", "variant": "plain", "rule": "sum_product", "numerical_profile": "binary-spa-flooding-f64-v2", "policy": None, "schedule": "flooding", "stop_on_convergence": True},
        "rate_points": [{"physical_p": .1, "decoder_p0": .1}], "sampling": {"seed": 9, "shot_start": 0, "shots": 3},
        "budgets": {"max_shots": 3, "max_iterations": 2},
        "provenance": {"relation": "development_fixture", "source_spec_id": None, "notes": None}}


def rehash_bound_files(result: Path) -> None:
    manifest_path = result / "result-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"] = {name: sha256((result / name).read_bytes()).hexdigest() for name in manifest["files"]}
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))


def test_absent_stopping_preserves_frozen_sampling_shape() -> None:
    assert validate_experiment(specimen())["sampling"] == {"seed": 9, "shot_start": 0, "shots": 3}
    invalid = specimen(); invalid["sampling"]["stop_failures"] = 0
    with pytest.raises(ValueError, match="positive"):
        validate_experiment(invalid)


def test_failure_stopping_terminates_rate_and_withholds_fixed_n_interval(tmp_path: Path, monkeypatch) -> None:
    from bp_registry.research import runner
    value = specimen(); value["sampling"]["stop_failures"] = 1
    monkeypatch.setattr(runner, "evaluate_candidate", lambda *args, **kwargs: SimpleNamespace(outcome="invalid_syndrome", logical_action_agrees=False))
    summary = run_experiment(value, output=tmp_path / "adaptive")
    row = summary["rows"][0]
    assert row["n"] == row["failures"] == row["type_i"] == 1
    assert row["sampling_mode"] == "adaptive_stopping"
    assert row["sampling_termination_reason"] == "stop_failures"
    assert (row["ci_low"], row["ci_high"], row["ci_method"]) == (None, None, "unavailable_optional_stopping")


def test_circuit_rejects_code_capacity_type_stopping_before_adapter_import() -> None:
    value = specimen()
    value.update({"problem": {"kind": "circuit", "circuit": {"kind": "inline_stim", "text": "R 0\nM 0\nOBSERVABLE_INCLUDE(0) rec[-1]"}, "dem": {"decompose_errors": False}}, "channel": {"kind": "embedded_circuit"}, "decoder": {"family": "circuit_dem_bp", "implementation": "canonical_sinter", "rule": "spa", "numerical_profile": "binary-spa-flooding-f64-v1", "schedule": "flooding", "max_iterations": 1, "tie_break": "zero"}, "rate_points": [{"label": "embedded"}]})
    value["sampling"]["stop_type_i"] = 1
    with pytest.raises(ValueError, match="type-I/type-II"):
        validate_experiment(value)


def test_circuit_timing_declaration_matches_per_shot_adapter_path(tmp_path: Path) -> None:
    pytest.importorskip("stim"); pytest.importorskip("sinter")
    value = specimen()
    value.update({"problem": {"kind": "circuit", "circuit": {"kind": "inline_stim", "text": "R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]"}, "dem": {"decompose_errors": False}}, "channel": {"kind": "embedded_circuit"}, "decoder": {"family": "circuit_dem_bp", "implementation": "canonical_sinter", "rule": "spa", "numerical_profile": "binary-spa-flooding-f64-v1", "schedule": "flooding", "max_iterations": 2, "tie_break": "zero"}, "rate_points": [{"label": "embedded"}]})
    value["sampling"]["shots"] = 1; value["budgets"]["max_shots"] = 1
    summary = run_experiment(value, output=tmp_path / "circuit")
    assert "batch-amortized" not in summary["timing_note"]
    assert summary["timing_boundaries"]["decode_seconds"].startswith("per retained shot")
    event = json.loads((tmp_path / "circuit/events.jsonl").read_text())
    assert event["end_to_end_seconds"] >= event["decode_seconds"]


def test_normalized_import_validates_ledger_and_refuses_collision(tmp_path: Path) -> None:
    result = tmp_path / "result"
    run_experiment(specimen(), output=result)
    entry = normalize_result_directory(result)
    assert entry["schema"] == "research-catalog-extension-v1"
    assert entry["import_manifest"]["result_file_hashes"]
    assert entry["decoders"][0]["configuration"]["experiment"] == specimen()
    assert (result / "catalog-entry.json").is_file()
    root = tmp_path / "repository"
    (root / "research/catalog").mkdir(parents=True)
    (root / "research/catalog/sources.json").write_text(json.dumps({"schema_version": 1, "papers": [], "study_paths": []}))
    stored = persistent_import(root, result)
    assert stored.is_file()
    assert json.loads((root / "research/catalog/sources.json").read_text())["normalized_catalogs"] == [stored.relative_to(root).as_posix()]
    with pytest.raises(FileExistsError, match="collision"):
        persistent_import(root, result)
    (result / "events.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        normalize_result_directory(result)


def test_two_local_runs_with_same_kernel_have_distinct_decoder_records(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    run_experiment(specimen(), output=first)
    changed = specimen(); changed["sampling"]["seed"] = 10
    run_experiment(changed, output=second)
    root = tmp_path / "repository"
    (root / "research/catalog").mkdir(parents=True)
    (root / "research/catalog/sources.json").write_text(json.dumps({"schema_version": 1, "papers": [], "study_paths": []}))
    one, two = persistent_import(root, first), persistent_import(root, second)
    assert one != two
    entries = [json.loads(path.read_text()) for path in (root / "research/imported").glob("*.json")]
    assert len({entry["decoders"][0]["decoder_id"] for entry in entries}) == 2


@pytest.mark.parametrize("mutation, message", [("rate", "canonical ledger aggregation"), ("ci", "canonical ledger aggregation"), ("configuration", "configuration identity"), ("identity", "experiment identity"), ("provenance", "provenance"), ("effective", "implementation provenance")])
def test_rehashed_semantic_tampering_is_not_accepted(tmp_path: Path, mutation: str, message: str) -> None:
    result = tmp_path / mutation
    run_experiment(specimen(), output=result)
    if mutation in {"rate", "ci"}:
        summary_path = result / "summary.json"; summary = json.loads(summary_path.read_text())
        if mutation == "rate": summary["rows"][0]["failure_rate"] = .777
        else: summary["rows"][0]["ci_low"], summary["rows"][0]["ci_high"] = .9, .1
        summary_path.write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    elif mutation == "configuration":
        for name in ("run-manifest.json", "summary.json"):
            path = result / name; payload = json.loads(path.read_text()); payload["configuration_sha256"] = "0" * 64; path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    elif mutation == "identity":
        for name in ("run-manifest.json", "status.json", "summary.json", "result-manifest.json"):
            path = result / name; payload = json.loads(path.read_text()); payload["experiment_id"] = "f" * 64; path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    elif mutation == "provenance":
        path = result / "summary.json"; payload = json.loads(path.read_text()); payload["provenance"] = {"forged": True}; path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        path = result / "effective-spec.json"; payload = json.loads(path.read_text()); payload["implementation_sha256"] = "0" * 64; path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    rehash_bound_files(result)
    with pytest.raises(ValueError, match=message):
        normalize_result_directory(result)


def test_explicit_channel_series_uses_decoder_prior_as_x(tmp_path: Path) -> None:
    value = specimen()
    value["channel"] = {"kind": "explicit", "probabilities": [.8, .2, 0, 0]}
    value["rate_points"] = [{"decoder_p0": .1}, {"decoder_p0": .2}]
    value["sampling"]["shots"] = 1; value["budgets"]["max_shots"] = 2
    result = tmp_path / "explicit"
    run_experiment(value, output=result)
    points = normalize_result_directory(result)["result_series"][0]["points"]
    assert [point["x"] for point in points] == [.1, .2]
    assert {point["x_semantics"] for point in points} == {"decoder_prior_probability"}


@pytest.mark.parametrize("mutation, message", [("shot_start", "shot ids"), ("family", "family"), ("iterations", "iterations"), ("duration", "duration"), ("csv", "summary.csv")])
def test_rehashed_malformed_event_or_csv_is_rejected(tmp_path: Path, mutation: str, message: str) -> None:
    result = tmp_path / mutation
    run_experiment(specimen(), output=result)
    if mutation == "csv":
        with (result / "summary.csv").open("a") as stream:
            stream.write("garbage\n")
    else:
        path = result / "events.jsonl"; events = [json.loads(line) for line in path.read_text().splitlines()]; event = events[0]
        if mutation == "shot_start": event["shot_id"] = 999
        elif mutation == "family": event["family"] = "bp4"
        elif mutation == "iterations": event["iterations"]["x"] = -1
        else: event["decode_seconds"] = -1
        path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in events) + "\n")
    rehash_bound_files(result)
    with pytest.raises(ValueError, match=message):
        normalize_result_directory(result)
