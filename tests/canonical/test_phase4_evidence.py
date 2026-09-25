"""Phase 4 ledger, identity, trace, and notebook evidence targets."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


def _artifact_qualification_module():
    path = Path("scripts/qualify_phase4_artifacts.py")
    assert path.is_file(), "Phase 4 needs an exact artifact qualification command"
    spec = importlib.util.spec_from_file_location("qualify_phase4_artifacts", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_b1_identity_reconciliation_measures_source_and_classifies_inventory_staleness(tmp_path):
    """B1 is admitted only after source reconstruction identifies the stale record."""
    module = _artifact_qualification_module()

    report = module.qualify_phase4_artifacts(Path("."), output_path=tmp_path / "resolution.json")

    b1 = report["b1"]
    assert b1["disposition"] == "inventory_stale"
    assert b1["source"]["revision"] == "v3"
    assert b1["reconstructed"]["raw_sha256"] == b1["records"]["artifact_v3"]["raw_sha256"]
    assert b1["reconstructed"]["semantic_sha256"] == b1["records"]["phase3_manifest"]["semantic_sha256"]
    assert b1["reconstructed"]["semantic_sha256"] == b1["records"]["inventory"]["semantic_sha256"]
    assert b1["reconstructed"]["semantic_sha256"] != b1["records"]["inventory_before_repair"]["semantic_sha256"]
    assert b1["matrix_logical_identity_match"] is True
    assert json.loads((tmp_path / "resolution.json").read_text(encoding="utf-8")) == report


def test_b1_identity_gate_read_only_qualifies_bb144_and_hgp(tmp_path):
    """The supporting artifacts are measured but cannot be promoted by family labels."""
    report = _artifact_qualification_module().qualify_phase4_artifacts(
        Path("."), output_path=tmp_path / "resolution.json"
    )

    assert report["supporting_qualifications"]["gross-bb-144"]["all_identities_match"] is True
    assert report["supporting_qualifications"]["hgp-gallager-3-4-seed-20260923"]["all_identities_match"] is True
    assert report["supporting_qualifications"]["hgp-gallager-3-4-seed-20260923"]["author_instance"] is False


def test_b1_inventory_only_repair_preserves_v3_and_preflights_resolved_phase4_manifest():
    """An inventory typo must bind Phase 4 to the frozen, source-matched v3 artifact."""
    from bp_registry.manifests import preflight

    resolution = json.loads(Path("data/evidence/phase4-b1-identity-resolution.json").read_text(encoding="utf-8"))
    inventory = json.loads(Path("data/evidence/code-inventory.json").read_text(encoding="utf-8"))
    phase4_path = Path("data/manifests/phase4-memory-relay-b1.json")
    v3_artifact = Path("data/artifacts/b1-panteleev-kalachev-v3.npz")
    v3_metadata = Path("data/artifacts/b1-panteleev-kalachev-v3.json")
    phase3_manifest = Path("data/manifests/phase3-pilot-b1.json")

    assert phase4_path.is_file(), "Phase 4 needs a resolved B1 manifest before dependent pilots run"
    phase4 = json.loads(phase4_path.read_text(encoding="utf-8"))
    b1_inventory = next(item for item in inventory["candidates"] if item["code_id"] == "b1-ghp-882")
    measured = resolution["b1"]["reconstructed"]
    assert resolution["b1"]["disposition"] == "inventory_stale"
    assert v3_artifact.is_file() and v3_metadata.is_file() and phase3_manifest.is_file()
    assert not Path("data/artifacts/b1-panteleev-kalachev-v4.npz").exists()
    assert b1_inventory["matrix_identity"]["artifact_semantic_sha256"] == measured["semantic_sha256"]
    assert phase4["artifact"]["path"] == "b1-panteleev-kalachev-v3.npz"
    assert phase4["artifact"]["raw_sha256"] == measured["raw_sha256"]
    assert phase4["artifact"]["matrix_hashes"] == measured["matrix_hashes"]
    assert preflight(phase4_path).artifact is not None


def test_b1_versioned_repair_historical_preserved_resolved_gate_regeneration():
    """The required repair gate remains selected by the plan-level verification command."""
    test_b1_inventory_only_repair_preserves_v3_and_preflights_resolved_phase4_manifest()


def _canonical_json_sha256(value: object) -> str:
    """Return the content digest used to bind the frozen pilot-design record."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_phase4_pilot_design_prespecifies_focused_factorial_and_noise_grid():
    """D-24/D-25 pilot choices exist before sampling or calibration evidence."""
    design_path = Path("data/evidence/phase4-pilot-design.json")
    assert design_path.is_file(), "Phase 4 needs a retained presampling pilot design"
    design = json.loads(design_path.read_text(encoding="utf-8"))

    assert design["schema_version"] == 1
    assert design["status"] == "frozen_before_sampling"
    assert design["calibration_outcomes_inspected"] is False
    assert design["amendment_policy"] == {
        "permitted_only_after": "retained_baseline_scan_before_calibration",
        "preserve_prior_design": True,
        "require_versioned_reason": True,
    }
    assert set(design["codes"]) == {"gross-bb-144", "b1-ghp-882", "hgp-gallager-3-4-seed-20260923"}
    assert {arm["kind"] for arm in design["factorial_arms"]} >= {
        "common_baseline", "memory_family", "two_policy_interaction", "relay_component_ablation",
    }
    assert len(design["selected_two_policy_interactions"]) == 3
    assert {grid["region"] for grid in design["noise_grid"]} == {"easy", "visible_bp_failures", "harder"}
    assert {configuration["name"] for configuration in design["configurations"]} == {
        "source_procedure", "canonical_procedure", "controlled_matched",
    }


def test_phase4_pilot_manifests_gate_identity_presets_and_matched_samples():
    """Each code binds the same frozen design while preserving source qualifications."""
    design_path = Path("data/evidence/phase4-pilot-design.json")
    assert design_path.is_file(), "pilot-design evidence must exist before manifests are admitted"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    design_digest = _canonical_json_sha256(design)
    manifest_paths = {
        "gross-bb-144": Path("data/manifests/phase4-memory-relay-bb144.json"),
        "b1-ghp-882": Path("data/manifests/phase4-memory-relay-b1.json"),
        "hgp-gallager-3-4-seed-20260923": Path("data/manifests/phase4-memory-relay-hgp.json"),
    }
    manifests = {}
    for code_id, path in manifest_paths.items():
        assert path.is_file(), f"{code_id} needs an identity-gated Phase 4 pilot manifest"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifests[code_id] = manifest
        assert manifest["schema_version"] == 4
        assert manifest["artifact"]["code_id"] == code_id
        assert manifest["artifact"]["matrix_hashes"]
        assert f"phase4-pilot-design.json#sha256:{design_digest}" in manifest["evidence"]["sources"]
        assert manifest["randomness"]["physical_sample_identity"] == design["codes"][code_id]["sample_namespace"]
        assert "source_procedure" in manifest["evidence"]["procedure"]
        assert "controlled_matched" in manifest["evidence"]["procedure"]

    b1 = manifests["b1-ghp-882"]
    resolution = json.loads(Path("data/evidence/phase4-b1-identity-resolution.json").read_text(encoding="utf-8"))
    resolution_digest = _canonical_json_sha256(resolution)
    assert resolution["b1"]["disposition"] == "inventory_stale"
    assert b1["artifact"]["semantic_sha256"] == resolution["b1"]["reconstructed"]["semantic_sha256"]
    assert f"phase4-b1-identity-resolution.json#sha256:{resolution_digest}" in b1["evidence"]["sources"]
    assert resolution["b1"]["reconstructed"]["semantic_sha256"] in b1["evidence"]["sources"]

    hgp = manifests["hgp-gallager-3-4-seed-20260923"]
    assert hgp["evidence"]["relation"] == "pilot_adaptation"
    assert "generated" in " ".join(hgp["evidence"]["discrepancies"]).lower()
    assert "paper-exact" in " ".join(hgp["evidence"]["discrepancies"]).lower()


def test_phase4_validation_declares_all_five_wave_zero_test_targets():
    validation = Path(".planning/phases/04-memory-policies-and-relay-bp/04-VALIDATION.md").read_text(encoding="utf-8")
    for target in (
        "test_memory_policies.py", "test_memory_composition.py", "test_relay.py",
        "test_relay_differential.py", "test_phase4_evidence.py",
    ):
        assert target in validation


@pytest.mark.skip(reason="B1 semantic digest reconciliation and bounded notebook artifacts are Wave 1 evidence work.")
def test_notebook_stage_reuse_requires_matching_manifest_source_policy_and_sample_identities():
    """Reserved evidence target; missing external artifacts must remain explicit rather than fabricated."""


def _phase4_events(path: Path) -> None:
    from bp_registry.canonical.budgets import WorkVector
    from bp_registry.ledger import CanonicalEventWriter

    work = WorkVector(bp_calls=1, candidate_checks=1, relay_transfers=1).as_evidence(structural_event_version=2)
    with CanonicalEventWriter(path, structural_event_version=4) as ledger:
        ledger.begin(run_id="phase4-evidence", shot_id=3, sample_seed_identity="sample-3", schema_version=4)
        ledger.event(run_id="phase4-evidence", shot_id=3, kind="attempt", data={"attempt_lineage_id": "attempt:3"})
        ledger.event(run_id="phase4-evidence", shot_id=3, kind="relay_transfer", data={
            "representation": "llr_log_p0_over_p1", "vector_length": 3,
            "producer_leg_lineage_id": "attempt:3:leg:0", "numerical_profile": "cpu-float64-spa-v1",
            "clipping_evidence": "finite", "digest": "a" * 64, "relay_leaf_id": "transfer:3:1",
        })
        ledger.event(run_id="phase4-evidence", shot_id=3, kind="work", data={
            "work_vector": work,
            "relay_work_leaves": [
                {"kind": "leg", "leg_index": 0, "lineage_id": "attempt:3:leg:0", "leaf_id": "leg:3:0", "work_vector": WorkVector(bp_calls=1).as_evidence(structural_event_version=2)},
                {"kind": "transfer", "leg_index": 1, "lineage_id": "attempt:3:leg:0", "leaf_id": "transfer:3:1", "work_vector": WorkVector(relay_transfers=1).as_evidence(structural_event_version=2)},
                {"kind": "candidate", "leg_index": 1, "lineage_id": "attempt:3:leg:1", "leaf_id": "candidate:3:1", "work_vector": WorkVector(candidate_checks=1).as_evidence(structural_event_version=2)},
            ],
        })
        ledger.event(run_id="phase4-evidence", shot_id=3, kind="candidate", data={"candidate_lineage_id": "candidate:3:1", "candidate": [0, 1, 0]})
        ledger.event(run_id="phase4-evidence", shot_id=3, kind="selection", data={"candidate_lineage_id": "candidate:3:1", "selection_status": "frozen"})
        ledger.terminal(run_id="phase4-evidence", shot_id=3, termination="completed", data={"candidate_lineage_id": "candidate:3:1", "work_vector": work})


def test_phase4_ledger_reconstructs_transfer_candidates_selection_and_leaf_work(tmp_path):
    """V4 terminal facts reduce from unique leaves and retain visible Relay ancestry."""
    from bp_registry.canonical.verification import reconstruct_relay_work, validate_phase4_shot

    path = tmp_path / "phase4.jsonl"
    _phase4_events(path)

    result = validate_phase4_shot(path, run_id="phase4-evidence", shot_id=3, trace_root=tmp_path)
    assert result["selection"]["candidate_lineage_id"] == "candidate:3:1"
    assert result["transfers"][0]["producer_leg_lineage_id"] == "attempt:3:leg:0"
    assert reconstruct_relay_work(result["events"])["relay_transfers"] == 1


def test_phase4_validation_rejects_tampered_sidecars_and_keeps_unavailable_facts_typed(tmp_path):
    """Trace hashes and unavailable values remain evidence, never inferred measurements."""
    from bp_registry.canonical.tracing import TracePlan, TraceSink
    from bp_registry.canonical.verification import validate_phase4_shot
    from bp_registry.ledger import CanonicalEventWriter

    sink = TraceSink(TracePlan(root=tmp_path, max_records=2, max_bytes=500))
    sink.observe(kind="relay_history", payload={"leg": 1, "history": "reset"})
    link = sink.finish().ledger_link()
    assert link is not None
    path = tmp_path / "tampered.jsonl"
    with CanonicalEventWriter(path, structural_event_version=4) as ledger:
        ledger.begin(run_id="phase4-trace", shot_id=0, sample_seed_identity="sample", schema_version=4)
        ledger.event(run_id="phase4-trace", shot_id=0, kind="missingness", data={"field": "native_iterations", "value": None, "reason": "native adapter does not expose it"})
        ledger.event(run_id="phase4-trace", shot_id=0, kind="trace_link", data={"trace_kind": "relay_history"}, sidecar=link)
        ledger.terminal(run_id="phase4-trace", shot_id=0, termination="completed", data={"work_vector": {"check_to_variable_updates": 0, "variable_to_check_updates": 0, "belief_assemblies": 0, "residual_priority_evaluations": 0, "bp_calls": 0, "candidate_checks": 0, "intervention_actions": 0, "branch_expansions": 0, "branch_prunes": 0, "relay_transfers": 0, "fallback_calls": 0}})
    sidecar = tmp_path / link["path"]
    sidecar.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256|sidecar"):
        validate_phase4_shot(path, run_id="phase4-trace", shot_id=0, trace_root=tmp_path)


def _phase4_runner_module():
    path = Path("scripts/run_phase4_pilots.py")
    assert path.is_file(), "Phase 4 needs one staged public-boundary runner"
    spec = importlib.util.spec_from_file_location("run_phase4_pilots", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stage_identity_separates_native_and_canonical_matching_arms(tmp_path):
    """Matched samples never collapse source procedure, canonical, and native identities."""
    runner = _phase4_runner_module()
    manifest = Path("data/manifests/phase4-memory-relay-bb144.json")

    source = runner.stage_identity(
        repository_root=Path("."), manifest_path=manifest, stage="trace", arm="source_procedure",
    )
    canonical = runner.stage_identity(
        repository_root=Path("."), manifest_path=manifest, stage="trace", arm="canonical_default",
    )
    native = runner.stage_identity(
        repository_root=Path("."), manifest_path=manifest, stage="trace", arm="native_v022",
    )

    assert source["sample_identity"] == canonical["sample_identity"] == native["sample_identity"]
    assert source["stage_identity"] != canonical["stage_identity"] != native["stage_identity"]
    assert native["source_identity"]["author_commit"] == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
    assert native["translation_identity"] != canonical["translation_identity"]


def test_runner_tracer_uses_public_canonical_boundaries_and_retains_native_unavailability(tmp_path, monkeypatch):
    """The BB-144 tracer public-preflights, runs, and verifies both canonical Relay arms."""
    runner = _phase4_runner_module()
    calls: list[tuple[str, ...]] = []

    def public_boundary(_root, *arguments):
        calls.append(tuple(arguments))
        command = arguments[0]
        if command == "preflight":
            return {"run_id": "stub", "policy_identity": "policy", "shot_budget": 1}
        if command == "canonical":
            output = Path(arguments[arguments.index("--output") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "result.json").write_text("{}", encoding="utf-8")
            return {"output": str(output), "final_row_count": 1}
        if command == "verify-run":
            return {"output": arguments[1], "final_row_count": 1, "verified_at": "test"}
        if command == "canonical-observation":
            return {
                "sample_identity": "actual-sample",
                "sample_namespace": "phase4-memory-relay-bb144-matched-physical-samples-v1",
                "check_matrix": [[1, 0], [0, 1]], "syndrome": [0, 1],
                "error_priors": [0.03, 0.03], "decoder_seed": 0, "hidden_truth": "not_exposed",
            }
        raise AssertionError(arguments)

    monkeypatch.setattr(runner, "_json_command", public_boundary)
    monkeypatch.setattr(runner, "_run_native", lambda **_kwargs: {
        "status": "native_unavailable", "reason": "isolated exact-author source intentionally unavailable in unit test",
    })

    report = runner.run_stage(
        repository_root=Path("."),
        manifest_path=Path("data/manifests/phase4-memory-relay-bb144.json"),
        stage="trace", output_root=tmp_path,
    )

    assert [arm["arm"] for arm in report["arms"]] == ["source_procedure", "canonical_default", "native_v022"]
    assert all(arm["identity"]["sample_identity"] == report["sample_namespace"] for arm in report["arms"])
    assert report["arms"][-1]["status"] == "native_unavailable"
    assert {call[0] for call in calls} == {"preflight", "canonical", "verify-run", "canonical-observation"}
    assert not hasattr(runner, "run_canonical")


def test_stage_reuse_requires_full_identity_and_preserves_mismatched_or_interrupted_evidence(tmp_path, monkeypatch):
    """Reuse is exact; stale and incomplete stage outputs remain visible beside a new result."""
    runner = _phase4_runner_module()
    monkeypatch.setattr(runner, "_json_command", lambda _root, *arguments: (
        {"run_id": "stub", "policy_identity": "policy", "shot_budget": 1}
        if arguments[0] == "preflight" else (
            {"sample_identity": "actual-sample", "sample_namespace": "phase4-memory-relay-bb144-matched-physical-samples-v1", "check_matrix": [[1]], "syndrome": [0], "error_priors": [0.03], "decoder_seed": 0, "hidden_truth": "not_exposed"}
            if arguments[0] == "canonical-observation" else {"output": arguments[-1], "final_row_count": 1, "verified_at": "test"}
        )
    ))
    monkeypatch.setattr(runner, "_run_native", lambda **_kwargs: {"status": "completed", "candidate": [0], "success": True})
    manifest = Path("data/manifests/phase4-memory-relay-bb144.json")

    first = runner.run_stage(repository_root=Path("."), manifest_path=manifest, stage="benchmark", output_root=tmp_path)
    reused = runner.run_stage(repository_root=Path("."), manifest_path=manifest, stage="benchmark", output_root=tmp_path)
    stage_file = Path(first["stage_record"])
    stale = json.loads(stage_file.read_text(encoding="utf-8"))
    stale["identity"]["arms"][0]["environment_identity"]["runner_python"] = "mismatch"
    stage_file.write_text(json.dumps(stale), encoding="utf-8")
    refreshed = runner.run_stage(repository_root=Path("."), manifest_path=manifest, stage="benchmark", output_root=tmp_path)

    assert reused["reused"] is True
    assert refreshed["reused"] is False
    assert any(path.name.startswith("mismatch-") for path in stage_file.parent.iterdir())


def test_public_verify_executes_phase4_relay_through_cli(tmp_path):
    """The public V4 path retains relay controls through preflight, run, and verification."""
    import os
    import subprocess
    import sys

    manifest = Path("data/manifests/phase4-memory-relay-bb144.json")
    output = tmp_path / "relay-public"
    environment = {**os.environ, "OMP_NUM_THREADS": "1", "PYTHONPATH": str(Path("src").resolve())}
    for arguments in (
        ["preflight", str(manifest)],
        ["canonical", str(manifest), "--output", str(output)],
        ["verify-run", str(output)],
    ):
        completed = subprocess.run([sys.executable, "-m", "bp_registry.cli", *arguments], text=True, capture_output=True, env=environment)
        assert completed.returncode == 0, completed.stderr or completed.stdout
    events = (output / "events.jsonl").read_text(encoding="utf-8")
    assert '"relay_transfer"' in events


def test_interrupted_stage_is_retained_without_a_silent_same_identity_retry(tmp_path, monkeypatch):
    """Finite native failures remain visible and require a new identified stage to retry."""
    runner = _phase4_runner_module()
    calls = {"native": 0}

    def public_boundary(_root, *arguments):
        if arguments[0] == "preflight":
            return {"run_id": "stub", "shot_budget": 1}
        if arguments[0] == "canonical-observation":
            return {"sample_identity": "actual-sample", "sample_namespace": "phase4-memory-relay-bb144-matched-physical-samples-v1", "check_matrix": [[1]], "syndrome": [0], "error_priors": [0.03], "decoder_seed": 0, "hidden_truth": "not_exposed"}
        return {"output": arguments[-1], "final_row_count": 1, "verified_at": "test"}

    def unavailable(**_kwargs):
        calls["native"] += 1
        return {"status": "native_unavailable", "reason": "bounded test interruption"}

    monkeypatch.setattr(runner, "_json_command", public_boundary)
    monkeypatch.setattr(runner, "_run_native", unavailable)
    kwargs = {"repository_root": Path("."), "manifest_path": Path("data/manifests/phase4-memory-relay-bb144.json"), "stage": "native", "output_root": tmp_path}
    first = runner.run_stage(**kwargs)
    retained = runner.run_stage(**kwargs)

    assert first["status"] == retained["status"] == "incomplete_native_unavailable"
    assert retained["reused"] is False
    assert retained["retry_requires_new_stage_identity"] is True
    assert calls["native"] == 1


def test_three_codes_share_relay_stage_identity_protocol():
    """BB-144, B1, and HGP expose the same bounded Relay stage contract."""
    runner = _phase4_runner_module()
    manifests = [
        Path("data/manifests/phase4-memory-relay-bb144.json"),
        Path("data/manifests/phase4-memory-relay-b1.json"),
        Path("data/manifests/phase4-memory-relay-hgp.json"),
    ]
    for manifest in manifests:
        value = json.loads(manifest.read_text(encoding="utf-8"))
        assert value["relay"]["total_leg_limit"] == 2
        assert value["budgets"]["attempt"]["work_limits"]["relay_transfers"] == 1
        for stage in ("benchmark", "calibration", "evaluation", "factorial", "native", "trace"):
            identity = runner.stage_identity(repository_root=Path("."), manifest_path=manifest, stage=stage, arm="native_v022")
            assert identity["source_identity"]["author_commit"] == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"


def test_phase4_benchmark_retains_entitlement_and_thirty_two_identified_shots():
    """D-23 records only the scheduler allocation and every bounded benchmark attempt."""
    benchmark_path = Path("data/results/phase4-memory-relay/benchmark.json")
    assert benchmark_path.is_file(), "D-23 requires retained measured benchmark evidence"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))

    entitlement = benchmark["entitlement"]
    assert entitlement["scheduler"] == "slurm"
    assert entitlement["allocation"] == {
        "account": "pfisterlab", "partition": "common", "cpus": 2,
        "tasks": 1, "cpus_per_task": 2, "memory": "8G", "nodes": 1,
        "time_limit": "30-00:00:00",
    }
    assert "node_capacity" not in entitlement
    assert benchmark["sample_count_per_arm"] == 32
    assert set(benchmark["codes"]) == {
        "gross-bb-144", "b1-ghp-882", "hgp-gallager-3-4-seed-20260923",
    }
    for code_id, code in benchmark["codes"].items():
        assert code["central_error_rate"] == 0.03, code_id
        assert set(code["arms"]) == {"baseline", "canonical_relay_31", "native_v022"}
        for arm_name, arm in code["arms"].items():
            assert arm["shot_ids"] == list(range(32)), (code_id, arm_name)
            assert len(arm["attempts"]) == 32
            assert arm["runtime_seconds"]["count"] == 32
            assert arm["resource_measurements"]["scope"] == "attempt"
        assert code["arms"]["canonical_relay_31"]["relay"]["total_leg_limit"] == 31
        assert code["arms"]["canonical_relay_31"]["raw_work"]["per_leg_totals"]
        assert code["arms"]["native_v022"]["raw_work"]["availability"] == "unavailable"
        assert code["arms"]["native_v022"]["source_identity"]["author_commit"] == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
