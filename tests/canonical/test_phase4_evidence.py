"""Phase 4 ledger, identity, trace, and notebook evidence targets."""

from __future__ import annotations

from copy import deepcopy
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


def test_phase4_reconstruction_rejects_leaf_lineage_mismatches_even_when_totals_match(tmp_path):
    """A valid aggregate cannot conceal work assigned to the wrong Relay leg."""
    from bp_registry.canonical.verification import CanonicalStructuralVerificationError, reconstruct_relay_work
    from bp_registry.ledger import read_canonical_events

    path = tmp_path / "lineage-mismatch.jsonl"
    _phase4_events(path)
    events = deepcopy(read_canonical_events(path))
    work = next(event["data"] for event in events if event["kind"] == "work")
    work["relay_legs"] = [
        {"index": 0, "lineage_id": "attempt:3:leg:0"},
        {"index": 1, "lineage_id": "attempt:3:leg:1"},
    ]
    next(leaf for leaf in work["relay_work_leaves"] if leaf["kind"] == "leg")["lineage_id"] = "attempt:3:leg:1"

    with pytest.raises(CanonicalStructuralVerificationError, match="leg work leaf"):
        reconstruct_relay_work(events)


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
            expected_scope = "all_children_to_date" if arm_name == "native_v022" else "attempt"
            assert arm["resource_measurements"]["scope"] == expected_scope
        assert code["arms"]["baseline"]["sample_identities"] == code["arms"]["canonical_relay_31"]["sample_identities"] == code["arms"]["native_v022"]["sample_identities"]
        assert code["arms"]["canonical_relay_31"]["relay"]["total_leg_limit"] == 31
        assert code["arms"]["canonical_relay_31"]["raw_work"]["per_leg_totals"]
        assert code["arms"]["native_v022"]["raw_work"]["availability"] == "unavailable"
        assert code["arms"]["native_v022"]["source_identity"]["author_commit"] == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"


def test_benchmark_per_shot_public_identity_matches_native_observation(tmp_path):
    """Selected-shot canonical evidence and native input share one physical observation."""
    runner = _phase4_runner_module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text(encoding="utf-8"))
    manifest = runner._benchmark_manifest(base, arm="canonical_relay_31")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    shot_id = 7

    native_observation = runner._json_command(Path("."), "canonical-observation", str(manifest_path), "--shot", str(shot_id))
    runner._json_command(Path("."), "canonical", str(manifest_path), "--output", str(tmp_path / "run"), "--shot", str(shot_id))
    runner._json_command(Path("."), "verify-canonical-shot", str(manifest_path), str(tmp_path / "run"), "--shot", str(shot_id))
    attempts, _ = runner._canonical_attempts(tmp_path / "run", expected_shots=32)

    assert attempts[shot_id]["sample_identity"] == native_observation["sample_identity"]
    assert attempts[shot_id]["terminal"]
    assert all(attempt["sample_identity"] is None for attempt in attempts[:shot_id])


def test_benchmark_timeout_without_a_ledger_is_retained_as_each_incomplete_shot(tmp_path, monkeypatch):
    """A public CLI timeout cannot erase an unstarted shot from the 32-shot denominator."""
    runner = _phase4_runner_module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text(encoding="utf-8"))

    def timeout(_root, *arguments, **_kwargs):
        if arguments[0] == "preflight":
            return {"run_id": "bounded", "shot_budget": 32}
        raise subprocess.TimeoutExpired(arguments, 300)

    import subprocess
    monkeypatch.setattr(runner, "_json_command", timeout)
    arm = runner._run_canonical_benchmark_arm(repository_root=Path("."), base=base, arm="baseline", output=tmp_path / "baseline")

    assert arm["status"] == "incomplete_canonical_arm"
    assert [attempt["shot_id"] for attempt in arm["attempts"]] == list(range(32))
    assert {attempt["status"] for attempt in arm["attempts"]} == {"incomplete_canonical_shot"}


def test_representative_v3_manifest_and_native_settings_are_fixed():
    """D-22 representative work uses the declared 80/60/one-solution controls."""
    runner = _phase4_runner_module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text(encoding="utf-8"))
    baseline = runner._benchmark_manifest(base, arm="baseline")["relay"]
    relay = runner._benchmark_manifest(base, arm="canonical_relay_31")["relay"]
    assert baseline["total_leg_limit"] == 1
    assert baseline["legs"] == [{"max_iterations": 80}]
    assert relay["total_leg_limit"] == 31
    assert relay["solution_limit"] == 1
    assert relay["legs"][0]["max_iterations"] == 80
    assert all(leg["max_iterations"] == 60 for leg in relay["legs"][1:])
    assert runner._NATIVE_TIMEOUT_SECONDS == 900
    import inspect
    native_source = inspect.getsource(runner._run_native)
    assert '"num_sets": 30' in native_source
    assert '"stopping_criterion": "nconv"' in native_source
    assert '"stop_nconv": 1' in native_source


def test_rate_amendment_uses_a_distinct_matched_namespace():
    """A harder-rate probe cannot alias retained p=.03 physical samples."""
    runner = _phase4_runner_module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text(encoding="utf-8"))
    p03 = runner._benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=0.03)
    p05_canonical = runner._benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=0.05)
    p05_native = runner._benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=0.05)

    assert p03["error_rate"] == 0.03
    assert p05_canonical["error_rate"] == 0.05
    assert p03["randomness"]["physical_sample_identity"] != p05_canonical["randomness"]["physical_sample_identity"]
    assert p05_canonical["randomness"]["physical_sample_identity"].endswith("benchmark-p0050")
    assert p05_canonical["randomness"]["physical_sample_identity"] == p05_native["randomness"]["physical_sample_identity"]


def test_b1_p07_bounded_probe_has_a_fixed_three_leg_work_envelope():
    """The p=.07 adaptation caps public work before the 900-second outer boundary."""
    runner = _phase4_runner_module()
    base = json.loads(Path("data/manifests/phase4-memory-relay-b1.json").read_text(encoding="utf-8"))
    bounded = runner._benchmark_manifest(
        base, arm="canonical_relay_31", central_error_rate=0.07,
        work_limit_override=runner._B1_P07_BOUNDED_THREE_LEG_WORK_LIMITS,
        namespace_suffix="-bounded-three-leg-v1", sample_namespace_suffix="",
    )
    unbounded = runner._benchmark_manifest(base, arm="canonical_relay_31", central_error_rate=0.07)

    assert bounded["relay"]["total_leg_limit"] == 31
    assert bounded["relay"]["first_leg_iteration_limit"] == 80
    assert bounded["relay"]["later_leg_iteration_limit"] == 60
    assert bounded["relay"]["solution_limit"] == 1
    assert bounded["run_id"] != unbounded["run_id"]
    assert bounded["randomness"]["physical_sample_identity"] == unbounded["randomness"]["physical_sample_identity"]
    assert bounded["randomness"]["physical_sample_identity"].endswith("benchmark-p0070")
    for scope_name in ("shot", "search", "attempt"):
        assert bounded["budgets"][scope_name]["work_limits"] == {
            "belief_assemblies": 176400, "candidate_checks": 176400,
            "check_to_variable_updates": 529200, "variable_to_check_updates": 529200,
            "residual_priority_evaluations": 0, "bp_calls": 3, "relay_transfers": 2,
            "branch_expansions": 0, "branch_prunes": 0, "fallback_calls": 0,
            "intervention_actions": 0,
        }


def test_frozen_v3_caps_are_numeric_separate_and_executable():
    """D-23 freezes measured one-worker caps before calibration can rank a setting."""
    caps = json.loads(Path("data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8"))
    amendment = json.loads(Path("data/evidence/phase4-pilot-design-amendment-v3.json").read_text(encoding="utf-8"))
    allocation = caps["allocation"]
    categories = allocation["categories"]

    assert caps["status"] == "frozen_pre_calibration"
    assert amendment["calibration_outcomes_inspected"] is False
    assert caps["entitlement"]["worker_count"] == 1
    assert caps["entitlement"]["concurrency_proof"]["status"] == "not_proven"
    assert sum(item["wall_seconds_max"] for item in categories.values()) <= allocation["allocatable_wall_seconds_after_margin"]
    assert sum(item["planned_total_wall_seconds"] for item in categories.values()) <= allocation["allocatable_wall_seconds_after_margin"]
    assert categories["calibration"]["planned_total_wall_seconds"] <= categories["calibration"]["wall_seconds_max"]
    assert categories["evaluation"]["planned_total_wall_seconds"] <= categories["evaluation"]["wall_seconds_max"]
    assert caps["evaluation"]["fresh_matched_samples_per_arm"] == 448
    assert caps["stop_rules"]["no_silent_extension"]
    assert caps["stop_rules"]["no_rank_chasing"]
    assert caps["factorial"]["shots_per_arm_rate_code"] == 7
    assert len(caps["factorial"]["arms"]) == 14
    assert categories["fixture_trace"]["planned_total_wall_seconds"] <= categories["fixture_trace"]["wall_seconds_max"]

    namespaces = set()
    expected_counts = {"gross-bb-144": 54, "b1-ghp-882": 20, "hgp-gallager-3-4-seed-20260923": 14}
    for code_id, code in caps["codes"].items():
        assert code["coarse_candidate_count"] == expected_counts[code_id]
        assert len(code["coarse_candidates"]) == expected_counts[code_id]
        assert code["calibration_shots_per_configuration"] == 32
        assert code["evaluation_shots_per_arm"] == 448
        assert code["canonical_public_boundary_seconds"] == 900
        assert code["refinement_candidate_count_per_preset"] == 1
        assert len(code["per_shot_work_cap"]) == 11
        namespaces.update((code["calibration_namespace"], code["evaluation_namespace"], code["native_namespace"], code["fixture_trace_namespace"]))
    assert len(namespaces) == 12
    assert caps["codes"]["b1-ghp-882"]["per_shot_work_cap"]["bp_calls"] == 3


def test_calibration_plan_is_complete_disjoint_and_keeps_controlled_adaptation_labels():
    """D-22 derives every finite cell before any calibration outcome is read."""
    runner = _phase4_runner_module()
    caps = json.loads(Path("data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8"))

    plan = runner.calibration_plan(Path("."), caps)

    assert plan["calibration_digest"] == runner._digest(plan["calibration_input"])
    assert plan["evaluation_namespaces"] == sorted(
        code["evaluation_namespace"] for code in caps["codes"].values()
    )
    assert set(plan["calibration_namespaces"]).isdisjoint(plan["evaluation_namespaces"])
    expected = sum(
        2 * (code["coarse_candidate_count"] + code["refinement_candidate_count_per_preset"])
        for code in caps["codes"].values()
    )
    assert len(plan["cells"]) == expected
    assert {cell["relay"]["fidelity_status"] for cell in plan["cells"]} == {"controlled_component_adaptation"}
    assert {cell["relay"]["total_leg_limit"] for cell in plan["cells"]} == {31}
    assert {cell["relay"]["first_leg_iteration_limit"] for cell in plan["cells"]} == {80}
    assert {cell["relay"]["later_leg_iteration_limit"] for cell in plan["cells"]} == {60}
    assert {cell["relay"]["solution_limit"] for cell in plan["cells"]} == {1}
    assert any(cell["candidate"]["later_low"] < 0 for cell in plan["cells"])
    assert any(cell["candidate"]["later_high"] > 1 for cell in plan["cells"])
    first = plan["cells"][0]
    same_code = next(cell for cell in plan["cells"] if cell["code_id"] == first["code_id"] and cell["candidate"]["id"] != first["candidate"]["id"])
    amendment_path = "data/evidence/phase4-pilot-design-amendment-v4-active-memory.json"
    manifest_a = runner._calibration_manifest(json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text()), first, amendment_path=amendment_path, amendment_sha256="b" * 64)
    manifest_b = runner._calibration_manifest(json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text()), same_code, amendment_path=amendment_path, amendment_sha256="b" * 64)
    assert manifest_a["relay"]["memory_tuning"]["seed_identity"] == manifest_b["relay"]["memory_tuning"]["seed_identity"]
    source = next(cell for cell in plan["cells"] if cell["code_id"] == "gross-bb-144" and cell["preset_key"] == "source_procedure")
    canonical = next(cell for cell in plan["cells"] if cell["code_id"] == "gross-bb-144" and cell["preset_key"] == "canonical_default")
    source_manifest = runner._calibration_manifest(json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text()), source, amendment_path=amendment_path, amendment_sha256="b" * 64)
    canonical_manifest = runner._calibration_manifest(json.loads(Path("data/manifests/phase4-memory-relay-bb144.json").read_text()), canonical, amendment_path=amendment_path, amendment_sha256="b" * 64)
    assert source_manifest["policies"]["update"]["kind"] == "min_sum"
    assert source_manifest["numerical_profile"] == source_manifest["relay"]["numerical_profile"] == "cpu-float64-min-sum-v1"
    assert canonical_manifest["policies"]["update"]["kind"] == "binary_spa"
    assert canonical_manifest["numerical_profile"] == canonical_manifest["relay"]["numerical_profile"] == "cpu-float64-spa-v1"
    assert any(source.startswith(f"{amendment_path}#sha256:") for source in source_manifest["evidence"]["sources"])


def test_selection_rule_is_deterministic_and_never_reads_evaluation_data(tmp_path):
    """Selection uses only eligible calibration rows and reports finite precision."""
    runner = _phase4_runner_module()
    calibration = {
        "calibration_digest": "a" * 64,
        "codes": {
            "code-a": {
                "presets": {
                    "source": {"configurations": [
                        {"configuration_id": "b", "candidate": {"id": "shared"}, "logical_failure": {"estimate": 0.25, "wilson_95": [0.1, 0.5], "eligible": True}, "work": {"mean_c2v": 9, "mean_total": 12}},
                        {"configuration_id": "a", "candidate": {"id": "local"}, "logical_failure": {"estimate": 0.25, "wilson_95": [0.1, 0.5], "eligible": True}, "work": {"mean_c2v": 8, "mean_total": 99}},
                    ]},
                    "canonical": {"configurations": [
                        {"configuration_id": "c", "candidate": {"id": "shared"}, "logical_failure": {"estimate": None, "wilson_95": None, "eligible": False}, "work": {"mean_c2v": None, "mean_total": None}},
                    ]},
                }
            }
        },
        "evaluation": {"forbidden": "must not be consulted"},
    }
    selected = runner.select_calibration_settings(calibration)

    assert selected["calibration_digest"] == "a" * 64
    assert selected["codes"]["code-a"]["presets"]["source"]["configuration_id"] == "a"
    assert selected["codes"]["code-a"]["presets"]["canonical"]["status"] == "inconclusive"
    assert selected["codes"]["code-a"]["shared_memory_settings"]["status"] == "inconclusive"
    assert selected["selection_input_fields"] == ["calibration.codes"]


def test_selection_tie_break_uses_work_only_for_overlapping_wilson_intervals():
    runner = _phase4_runner_module()
    calibration = {
        "calibration_digest": "c" * 64,
        "codes": {"code-a": {"presets": {"source": {"configurations": [
            {"configuration_id": "lowest", "candidate": {"id": "x"}, "logical_failure": {"estimate": 0.10, "wilson_95": [0.01, 0.40], "eligible": True}, "work": {"mean_c2v": 9, "mean_total": 9}},
            {"configuration_id": "overlap", "candidate": {"id": "y"}, "logical_failure": {"estimate": 0.20, "wilson_95": [0.05, 0.45], "eligible": True}, "work": {"mean_c2v": 1, "mean_total": 1}},
            {"configuration_id": "separate", "candidate": {"id": "z"}, "logical_failure": {"estimate": 0.30, "wilson_95": [0.50, 0.60], "eligible": True}, "work": {"mean_c2v": 0, "mean_total": 0}},
        ]}}}}}
    selected = runner.select_calibration_settings(calibration)
    assert selected["codes"]["code-a"]["presets"]["source"]["configuration_id"] == "overlap"


def test_shared_selection_retains_zero_work_as_lower_than_positive_work():
    runner = _phase4_runner_module()
    def row(candidate_id: str, c2v: int) -> dict[str, object]:
        return {"configuration_id": candidate_id, "candidate": {"id": candidate_id},
                "logical_failure": {"estimate": .2, "wilson_95": [.1, .3], "eligible": True},
                "work": {"mean_c2v": c2v, "mean_total": c2v}}
    calibration = {"calibration_digest": "d" * 64, "codes": {"code-a": {"presets": {
        "source": {"configurations": [row("zero", 0), row("positive", 1)]},
        "canonical": {"configurations": [row("zero", 0), row("positive", 1)]},
    }}}}
    selected = runner.select_calibration_settings(calibration)
    assert selected["codes"]["code-a"]["shared_memory_settings"]["candidate_id"] == "zero"


def test_live_freeze_entitlement_uses_running_slurm_remaining_wall_and_rejects_stale_ceiling(monkeypatch):
    runner = _phase4_runner_module()
    record = (
        "JobId=42 JobState=RUNNING TimeLimit=1-00:00:00 RunTime=01:00:00 "
        "EndTime=2026-09-26T00:00:00 NumTasks=1"
    )
    monkeypatch.setattr(runner.subprocess, "run", lambda *_args, **_kwargs: type("Result", (), {
        "returncode": 0, "stdout": record, "stderr": "",
    })())
    live = runner._live_freeze_entitlement("42", ceiling_seconds=3_600)
    assert live["verified_remaining_wall_seconds"] == 82_800
    assert live["remaining_wall_seconds"] == 3_600
    assert live["one_worker"] == {"omp_num_threads": 1, "workers": 1}
    with pytest.raises(ValueError, match="exceeds verified"):
        runner._live_freeze_entitlement("42", ceiling_seconds=82_801)
    stopped = record.replace("JobState=RUNNING", "JobState=COMPLETED")
    monkeypatch.setattr(runner.subprocess, "run", lambda *_args, **_kwargs: type("Result", (), {
        "returncode": 0, "stdout": stopped, "stderr": "",
    })())
    with pytest.raises(RuntimeError, match="requires RUNNING"):
        runner._live_freeze_entitlement("42")


def test_active_v4_cap_builder_requires_terminal_verified_benchmark_and_derives_new_identity(tmp_path):
    """The active-memory timing amendment cannot reuse the pre-active V3 cap."""
    runner = _phase4_runner_module()
    prior = json.loads(Path("data/manifests/phase4-pilot-caps.json").read_text(encoding="utf-8"))

    def arm(*, elapsed: float, work: int) -> dict[str, object]:
        vector = {key: 0 for key in runner._ACTIVE_V4_WORK_VECTOR_KEYS}
        vector.update({"check_to_variable_updates": work, "variable_to_check_updates": work,
                       "bp_calls": 3, "relay_transfers": 2})
        return {"status": "completed", "active_memory_verified": True, "attempts": [
            {"status": "completed", "shot_id": shot, "public_boundary": {"elapsed_seconds": elapsed + shot / 100.0},
             "work_vector": {**vector, "check_to_variable_updates": work + shot, "variable_to_check_updates": work + shot}}
            for shot in range(32)
        ]}

    codes = {}
    for code_id, rate in (("gross-bb-144", .03), ("b1-ghp-882", .07), ("hgp-gallager-3-4-seed-20260923", .03)):
        key = f"p{rate:.3f}".replace(".", "")
        canonical = {"baseline": arm(elapsed=4.0, work=20), "controlled_relay_31": arm(elapsed=5.0, work=30)}
        if code_id == "b1-ghp-882":
            canonical["controlled_relay_31"] = {"status": "incomplete_canonical_arm", "active_memory_verified": False, "attempts": []}
            canonical["controlled_relay_31_bounded"] = arm(elapsed=8.0, work=40)
        codes[code_id] = {"selected_rate": rate, "selection_status": "selected", "rates": {key: {"presets": {
            "source_procedure": {"baseline": arm(elapsed=3.0, work=10), "controlled_relay_31": arm(elapsed=6.0, work=35)},
            "canonical_default": canonical,
        }}}}
    report = {"status": "completed",
              "author_source_pin": "relay-v0.2.2@14cb31a18f9b9d7d099791b793e35b8a2951f8f3",
              "core_commits": ["6e6ad03", "660049a", "1f8f1c2"], "codes": codes}
    report["report_digest"] = runner._digest(report)
    entitlement = {"job_id": "55938300", "remaining_wall_seconds": 3_000_000,
                   "one_worker": {"omp_num_threads": 1, "workers": 1}}

    built = runner.build_active_v4_caps(
        report, entitlement, prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
        prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64,
    )

    caps, amendment = built["caps"], built["amendment"]
    assert caps["status"] == "frozen_pre_calibration"
    assert caps["supersedes"]["prior_status"] == "superseded_pre_active_memory"
    assert amendment["calibration_outcomes_inspected"] is False
    assert caps["allocation"]["fraction_sum"] == 1.0
    assert sum(item["wall_seconds_max"] for item in caps["allocation"]["categories"].values()) <= caps["allocation"]["allocatable_wall_seconds_after_margin"]
    assert caps["codes"]["b1-ghp-882"]["central_error_rate"] == .07
    assert caps["codes"]["b1-ghp-882"]["canonical_public_boundary_seconds"] == 900
    assert caps["codes"]["gross-bb-144"]["per_shot_work_cap"]["check_to_variable_updates"] == 812160
    assert caps["codes"]["b1-ghp-882"]["per_shot_work_cap"]["check_to_variable_updates"] == 529200
    assert caps["codes"]["b1-ghp-882"]["active_v4_benchmark"]["observed_work_max"]["check_to_variable_updates"] < 529200
    assert set(caps["codes"]["gross-bb-144"]["per_shot_work_cap"]) == runner._ACTIVE_V4_WORK_VECTOR_KEYS
    assert caps["codes"]["gross-bb-144"]["timing_model"]["source"].startswith("active-V4")
    assert "historical_pre_active_memory_timing_model" in caps["codes"]["gross-bb-144"]
    assert caps["codes"]["gross-bb-144"]["calibration_namespace"].endswith("-v4-active-calibration")
    assert all(item["planned_total_wall_seconds"] > 0 for item in caps["allocation"]["categories"].values())
    assert caps["benchmark_evidence"]["active_v4"]["byte_sha256"] == "a" * 64
    assert "fresh_matched_samples_per_arm" not in caps["evaluation"]
    assert caps["evaluation"]["fresh_matched_samples_per_arm_by_code"] == caps["allocation_plan"]["evaluation"]["shots_per_code"]
    assert "shots_per_arm_rate_code" not in caps["factorial"]
    assert caps["factorial"]["shots_per_arm_rate_code_by_code"] == caps["allocation_plan"]["fixture_trace"]["factorial_shots_per_arm_rate_code"]
    assert caps["caps_digest"] == runner._digest({key: value for key, value in caps.items() if key != "caps_digest"})

    report_path = tmp_path / "data/results/active-v4.json"
    prior_path = tmp_path / "data/manifests/phase4-pilot-caps.json"
    amendment_path = tmp_path / "data/evidence/phase4-pilot-design-amendment-v4-active-memory.json"
    report_path.parent.mkdir(parents=True)
    prior_path.parent.mkdir(parents=True)
    report_path.write_bytes(runner._canonical_json_bytes(report))
    prior_path.write_bytes(runner._canonical_json_bytes(prior))
    published = runner.publish_active_v4_caps(
        repository_root=tmp_path, report_path=report_path, prior_caps_path=prior_path,
        caps_output_path=prior_path, amendment_output_path=amendment_path, live_entitlement=entitlement,
    )
    snapshot = tmp_path / "data/manifests/phase4-pilot-caps-v3-pre-active-memory.json"
    assert snapshot.read_bytes() == runner._canonical_json_bytes(prior)
    assert published["amendment_byte_sha256"] == hashlib.sha256(amendment_path.read_bytes()).hexdigest()
    assert runner.calibration_plan(tmp_path, json.loads(prior_path.read_text()))["calibration_digest"]

    tampered_report = deepcopy(report)
    tampered_report["unbound_change"] = True
    with pytest.raises(ValueError, match="digest-bound benchmark"):
        runner.build_active_v4_caps(tampered_report, entitlement, prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
                                    prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64)
    inconsistent_b1 = deepcopy(report)
    inconsistent_b1["codes"]["b1-ghp-882"]["rates"]["p0070"]["presets"]["source_procedure"]["controlled_relay_31"]["attempts"][0]["work_vector"]["bp_calls"] = 4
    inconsistent_b1["report_digest"] = runner._digest({key: value for key, value in inconsistent_b1.items() if key != "report_digest"})
    with pytest.raises(ValueError, match="consistently three-leg"):
        runner.build_active_v4_caps(inconsistent_b1, entitlement, prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
                                    prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64)
    tampered_prior = deepcopy(prior)
    tampered_prior["unbound_change"] = True
    with pytest.raises(ValueError, match="preserved frozen V3"):
        runner.build_active_v4_caps(report, entitlement, tampered_prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
                                    prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64)

    report["status"] = "final_inconclusive"
    with pytest.raises(ValueError, match="terminal completed"):
        runner.build_active_v4_caps(report, entitlement, prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
                                    prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64)
    report["status"] = "completed"
    report["codes"]["gross-bb-144"]["rates"]["p0030"]["presets"]["source_procedure"]["baseline"]["attempts"] = []
    report["report_digest"] = runner._digest({key: value for key, value in report.items() if key != "report_digest"})
    with pytest.raises(ValueError, match="complete verified active arm"):
        runner.build_active_v4_caps(report, entitlement, prior, report_path="data/results/active-v4.json", report_sha256="a" * 64,
                                    prior_caps_path="data/manifests/phase4-pilot-caps.json", prior_caps_sha256="b" * 64)


def test_calibration_runner_retains_verified_attempts_and_is_idempotent(tmp_path, monkeypatch):
    """A resumed finite cell cannot duplicate public events or re-run a terminal shot."""
    runner = _phase4_runner_module()
    real_caps = json.loads(Path("data/manifests/phase4-pilot-caps.json").read_text())
    code = deepcopy(real_caps["codes"]["gross-bb-144"])
    code["coarse_candidates"] = [code["coarse_candidates"][0]]
    code["coarse_candidate_count"] = 1
    code["refinement_candidates"] = []
    code["refinement_candidate_count_per_preset"] = 0
    code["calibration_shots_per_configuration"] = 1
    caps = deepcopy(real_caps)
    caps["codes"] = {"gross-bb-144": code}
    caps["allocation"]["categories"]["calibration"]["wall_seconds_max"] = 2_000.0
    caps_path = tmp_path / "caps.json"
    caps_path.write_text(json.dumps(caps), encoding="utf-8")
    calls = {"canonical": 0}

    def public(_root, *args, **_kwargs):
        if args[0] == "preflight":
            return {"status": "ok"}
        if args[0] == "canonical":
            calls["canonical"] += 1
            manifest = json.loads(Path(args[1]).read_text())
            output = Path(args[args.index("--output") + 1])
            shot = int(args[args.index("--shot") + 1])
            output.mkdir(parents=True, exist_ok=True)
            events = [
                {"event_id": f"begin-{manifest['run_id']}-{shot}", "kind": "shot_begin", "shot_id": shot, "sample_seed_identity": f"sample-{shot}"},
                {"event_id": f"terminal-{manifest['run_id']}-{shot}", "kind": "termination", "shot_id": shot, "termination": "completed", "data": {"outcome": "exact", "work_vector": {"check_to_variable_updates": 2, "variable_to_check_updates": 2}}},
            ]
            with (output / "events.jsonl").open("a", encoding="utf-8") as handle:
                for event in events:
                    handle.write(json.dumps(event) + "\n")
            return {"status": "ran"}
        if args[0] == "verify-canonical-shot":
            return {"status": "verified"}
        raise AssertionError(args)

    monkeypatch.setattr(runner, "_json_command", public)
    first = runner.run_calibration(repository_root=Path("."), caps_path=caps_path, output_root=tmp_path / "calibration")
    second = runner.run_calibration(repository_root=Path("."), caps_path=caps_path, output_root=tmp_path / "calibration")
    assert first["status"] == second["status"] == "completed"
    assert calls["canonical"] == 2  # one shot for each named controlled preset
    lines = (tmp_path / "calibration" / "events.jsonl").read_text().splitlines()
    assert len(lines) == len({json.loads(line)["event_id"] for line in lines})
    for preset in second["codes"]["gross-bb-144"]["presets"].values():
        assert preset["configurations"][0]["logical_failure"]["eligible"] is True
