"""Researcher command: compute once, verify reuse, reject altered evidence."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib

import pytest

from bp_registry.study import _expanded_policies, ensure_study


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_policy_file_computes_then_reuses_verified_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = json.loads((ROOT / "examples/three-qubit-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(study))
    cache = tmp_path / "results"
    decoder = ROOT / "examples/three-qubit-decoder.toml"
    first = ensure_study(study_path, decoder, results_root=cache)
    assert first["status"] == "computed"
    assert first["verification"]["final_row_count"] == 2
    second = ensure_study(study_path, decoder, results_root=cache)
    assert second["status"] == "reused"
    assert second["cache_key"] == first["cache_key"]
    assert second["result"]["manifest_sha256"] == first["result"]["manifest_sha256"]
    json_decoder = tmp_path / "decoder.json"
    json_decoder.write_text(json.dumps(tomllib.loads(decoder.read_text())))
    third = ensure_study(study_path, json_decoder, results_root=cache)
    assert third["status"] == "reused" and third["cache_key"] == first["cache_key"]
    ledger = Path(first["output"]) / "events.jsonl"
    ledger.write_bytes(ledger.read_bytes() + b"tampered\n")
    with pytest.raises(ValueError):
        ensure_study(study_path, decoder, results_root=cache)


def test_schema5_and_schema6_policy_studies_accept_decoder_owned_controls(tmp_path: Path) -> None:
    """Schemas 5 and 6 are compiled without the study owning decoder controls."""
    sources = [
        ROOT / "data/manifests/phase5-b1-mechanism-pilot.json",
        ROOT / "data/manifests/phase5-b1-p005-damping-pilot-v2.json",
    ]
    for source_path, schema in zip(sources, (5, 6), strict=True):
        source = json.loads(source_path.read_text())
        study = dict(next(manifest for manifest in source["arm_manifests"].values()
                          if manifest["schema_version"] == schema))
        assert study["schema_version"] == schema
        decoder = {"schema_version": 1, "engine": "canonical_css", **study.pop("policies")}
        decoder["intervention"] = study.pop("intervention")
        decoder["intervention_limits"] = study.pop("intervention_limits")
        if schema == 6:
            decoder["memory"] = study.pop("memory")
        assert "intervention" not in study and "intervention_limits" not in study
        assert set(_expanded_policies(decoder, schema_version=schema)) == {
            "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
        }


def test_policy_file_rejects_unimplemented_composition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = json.loads((ROOT / "examples/three-qubit-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(study))
    policy = (ROOT / "examples/three-qubit-decoder.toml").read_text().replace(
        'kind = "binary_spa"', 'kind = "made_up_update"', 1,
    )
    decoder = tmp_path / "decoder.toml"
    decoder.write_text(policy)
    with pytest.raises(ValueError):
        ensure_study(study_path, decoder, results_root=tmp_path / "results")


def test_v4_memory_and_relay_are_read_from_decoder_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    source = json.loads((ROOT / "data/manifests/phase4-memory-relay-bb144.json").read_text())
    decoder_data = {"schema_version": 1, "engine": "canonical_css", **source.pop("policies"),
                    "memory": source.pop("memory"), "relay": source.pop("relay")}
    source["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "v4-study.json"
    decoder_path = tmp_path / "v4-decoder.json"
    study_path.write_text(json.dumps(source))
    decoder_path.write_text(json.dumps(decoder_data))
    first = ensure_study(study_path, decoder_path, results_root=tmp_path / "results")
    assert first["status"] == "computed"
    assert first["verification"]["final_row_count"] == 1
    assert ensure_study(study_path, decoder_path, results_root=tmp_path / "results")["status"] == "reused"


def test_commented_toml_memory_policy_changes_cache_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = json.loads((ROOT / "examples/three-qubit-memory-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "memory-study.json"
    study_path.write_text(json.dumps(study))
    original = (ROOT / "examples/three-qubit-damped-decoder.toml").read_text()
    decoder_path = tmp_path / "decoder.toml"
    decoder_path.write_text(original)
    first = ensure_study(study_path, decoder_path, results_root=tmp_path / "results")
    assert first["status"] == "computed"
    decoder_path.write_text(original.replace("gamma = 0.5", "gamma = 1.0"))
    second = ensure_study(study_path, decoder_path, results_root=tmp_path / "results")
    assert second["status"] == "computed"
    assert first["cache_key"] != second["cache_key"]


def test_published_bb72_arm_reuses_verified_package() -> None:
    result = ensure_study(ROOT / "data/studies/fair-beam-relay-css-v2.json",
                          ROOT / "examples/bb72-relay-decoder.toml")
    assert result["status"] == "reused"
    assert result["verification"]["package_files"] == 43
    assert result["result"]["p050"]["failures"] == 81
    assert result["result"]["p080"]["failures"] == 584
