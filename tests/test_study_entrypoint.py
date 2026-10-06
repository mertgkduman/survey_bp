"""Researcher command: compute once, verify reuse, reject altered evidence."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tomllib

import pytest

from bp_registry.study import _expanded_policies, ensure_study


ROOT = Path(__file__).resolve().parents[1]


def test_native_bp_osd_study_arm_identity_resolver_is_explicit():
    """Native composite arms must use a separate public study path."""
    from bp_registry import study

    assert hasattr(study, "resolve_native_composite_arm")


@pytest.mark.parametrize(
    ("engine", "method_controls"),
    (
        ("native_bp_osd", {"osd_method": "OSD_0", "osd_order": 0}),
        ("native_bp_lsd", {
            "lsd_method": "LSD_0", "lsd_order": 0, "bits_per_step": 1,
            "always_run_lsd": False,
        }),
    ),
)
def test_native_composite_study_arms_share_matched_samples_and_keep_disjoint_cache_identity(
    tmp_path: Path, engine: str, method_controls: dict[str, object],
):
    from bp_registry.sampling import sample_shot

    study = json.loads((ROOT / "examples/three-qubit-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(study))
    decoder = {
        "schema_version": 1, "engine": engine, "provider": "quantumgizmos", "package": "ldpc",
        "version": "2.4.1", "max_iter": 1, "bp_method": "product_sum", "schedule": "parallel",
        "input_vector_type": "syndrome", **method_controls,
    }
    decoder_path = tmp_path / f"{engine}.json"
    decoder_path.write_text(json.dumps(decoder))
    cache = tmp_path / "results"

    first = ensure_study(study_path, decoder_path, results_root=cache)
    second = ensure_study(study_path, decoder_path, results_root=cache)
    assert first["status"] == "computed"
    assert second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]
    assert first["result"]["identity_kind"] == "native_composite_reference"
    assert first["result"]["engine"] == engine
    assert {row["native_composite_identity"]["kind"] for row in first["result"]["rows"]} == {
        "native_composite_reference"
    }
    expected = sample_shot(
        __import__("bp_registry.artifacts", fromlist=["load_artifact"]).load_artifact(
            study["artifact"]["root"], study["artifact"]["path"],
            expected_raw_sha256=study["artifact"]["raw_sha256"],
            expected_semantic_sha256=study["artifact"]["semantic_sha256"],
        ).code,
        shot_id=0, seed=study["randomness"]["sample_seed"], x_error_rate=study["error_rate"],
        manifest_identity=study["randomness"]["physical_sample_identity"],
    )
    assert first["result"]["rows"][0]["sample_identity"] == expected.sample_identity
    assert "bp_only" not in first["result"]["rows"][0]
    assert "fallback" not in first["result"]["rows"][0]


def test_native_bp_lsd_study_arm_rejects_runtime_override_and_pin_drift(tmp_path: Path):
    from bp_registry.study import resolve_native_composite_arm

    controls = {
        "schema_version": 1, "engine": "native_bp_lsd", "provider": "quantumgizmos", "package": "ldpc",
        "version": "2.4.1", "max_iter": 1, "bp_method": "product_sum", "schedule": "parallel",
        "input_vector_type": "syndrome", "lsd_method": "LSD_0", "lsd_order": 0,
        "bits_per_step": 1, "always_run_lsd": False,
    }
    with pytest.raises(ValueError, match="complete explicit"):
        resolve_native_composite_arm({**controls, "runtime_override": "canonical"})
    with pytest.raises(ValueError, match="ldpc==2.4.1"):
        resolve_native_composite_arm({**controls, "version": "0.0.0"})


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


def test_canonical_study_cache_reuses_after_directory_move(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Published study packages must not depend on the producer's output path."""
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = json.loads((ROOT / "examples/three-qubit-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(study))
    decoder = ROOT / "examples/three-qubit-decoder.toml"
    original = tmp_path / "original-cache"
    moved = tmp_path / "moved-cache"
    first = ensure_study(study_path, decoder, results_root=original)
    assert first["status"] == "computed"
    receipt = json.loads((Path(first["output"]) / "request-receipts" /
                          f'{first["request_receipt"]}.json').read_text())
    assert receipt["source_path"] == "examples/three-qubit-decoder.toml"
    result = first["result"]
    assert result["manifest_path"] == "manifest.json"
    assert result["ledger_path"] == "events.jsonl"
    shutil.move(original, moved)
    second = ensure_study(study_path, decoder, results_root=moved)
    assert second["status"] == "reused"
    assert second["cache_key"] == first["cache_key"]
    assert second["request_receipt"] == first["request_receipt"]
    assert second["result"] == first["result"]


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


def test_symbolic_literature_round_limit_uses_validated_b1_artifact_without_running_it() -> None:
    """B1 supplies n=882 to identity resolution; this is not a simulation."""
    from bp_registry.study import _validated_artifact_block_length

    source = json.loads((ROOT / "data/manifests/phase3-pilot-b1.json").read_text())
    source["artifact"]["root"] = str(ROOT / "data/artifacts")
    assert _validated_artifact_block_length(source) == 882
