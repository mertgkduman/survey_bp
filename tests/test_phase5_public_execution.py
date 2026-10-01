"""Public Phase 5 source qualification and manifest-boundary fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _public_v5(kind: str = "identity") -> dict[str, object]:
    from bp_registry.canonical.budgets import WorkVector

    manifest = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    manifest["schema_version"] = 5
    manifest["run_id"] = f"phase5-public-{kind}"
    manifest["memory"] = None
    manifest["relay"] = None
    manifest["policies"]["state_memory"]["kind"] = "identity"
    manifest["policies"]["intervention"]["kind"] = kind
    for scope in ("shot", "search", "attempt"):
        manifest["budgets"][scope]["work_limits"] = {
            name: 10000 for name in WorkVector.zero().as_evidence(structural_event_version=2)
        }
    caps = {name: 10000 for name in WorkVector.zero().as_evidence(structural_event_version=4)}
    manifest["intervention_limits"] = {
        "max_total_attempts": 16, "max_total_actions": 16,
        "max_runtime_seconds": 10.0, "max_trace_records": 0,
        "max_trace_bytes": 0, "work_caps": caps,
    }
    common = {
        "kind": kind, "native_availability": "not_applicable",
        "trigger": "attempt_start", "operator": "identity", "selection": "stable_first",
        "lift_rule": "identity", "reset_rule": "not_applicable",
        "preserved_fields": [], "unresolved": [], "stream_status": "not_applicable",
    }
    arm = {
        "identity": {"variant": "identity_baseline_v1", "source_revision": "project:canonical-baseline", "qualification": "canonical_implemented"},
        "guided_decimation": {
            "variant": "algorithm1_v2_interpretation", "source_revision": "arxiv:2312.10950v2",
            "qualification": "algorithm_interpretation", "native_availability": "unverified",
            "trigger": "failed_bp_round", "operator": "finite_prior_bias",
            "selection": "max_abs_reliability", "lift_rule": "identity",
            "reset_rule": "continue_messages", "preserved_fields": ["graph", "syndrome", "messages"],
            "unresolved": ["zero_sign", "final_round"],
            "finite_bias_magnitude": 25.0, "zero_rule": "positive_prior_for_zero_posterior",
            "final_round_rule": "return_after_last_fixation", "round_limit": 2, "sweeps_per_round": 1,
        },
        "impulse": {
            "variant": "impulse_exact_shortening_css_v1", "source_revision": "arxiv:2606.18240v1",
            "qualification": "controlled_css_adaptation", "native_availability": "unverified",
            "trigger": "baseline_invalid", "operator": "exact_shortening",
            "selection": "minimum_original_weight", "lift_rule": "restore_fixed",
            "reset_rule": "fresh_per_coordinate", "preserved_fields": ["original_graph", "original_syndrome"],
            "unresolved": ["source_infinite_llr_trajectory"],
            "realization": "exact_shortening", "baseline_sweeps": 1, "attempt_sweeps": 1, "attempt_cap": 2,
        },
        "freezing": {
            "variant": "freezing_binary_css_controlled_v1", "source_revision": "arxiv:0801.1241",
            "qualification": "controlled_css_adaptation", "native_availability": "unverified",
            "trigger": "frustrated_check", "operator": "temporary_zero_freeze",
            "selection": "first_valid", "lift_rule": "restore_fixed",
            "reset_rule": "fresh_structural_branch_then_release_to_original",
            "preserved_fields": ["original_graph", "original_syndrome"], "unresolved": ["quaternary_to_binary"],
            "stream_status": "derived_decoder_stream", "period_sweeps": 1,
            "lifetime_sweeps": 1, "retry_cap": 2, "root_seed": "phase5-decoder-seed",
        },
        "syndrome_flip": {
            "variant": "bpsf_stable_order_css_v1", "source_revision": "arxiv:2507.00254v1",
            "qualification": "controlled_css_adaptation",
            "native_availability": "repository_revision_verified_in_phase_research",
            "source_code_commit": "0417d33fc2ffb3b442d0397bb09954fc1c6c3938",
            "trigger": "baseline_invalid_after_oscillation_count", "operator": "syndrome_xor_test_vector",
            "selection": "first_declared_valid", "lift_rule": "xor_test_vector",
            "reset_rule": "fresh_per_test", "preserved_fields": ["original_graph", "original_syndrome"],
            "unresolved": ["unseeded_source_sampling"], "stream_status": "derived_decoder_stream",
            "baseline_sweeps": 2, "attempt_sweeps": 1, "top_k": 2,
            "max_weight": 1, "test_cap": 2, "root_seed": "phase5-decoder-seed",
        },
        "sign_flip": {
            "variant": "bsfbp_sign_only_controlled_adaptation", "source_revision": "doi:10.1109/TQE.2023.3279379",
            "qualification": "bsfbp_sign_only_controlled_adaptation", "native_availability": "unverified",
            "trigger": "failed_normalized_min_sum_trunk", "operator": "posterior_sign_flip",
            "selection": "global_mismatched_check_target", "lift_rule": "identity",
            "reset_rule": "continue_messages_at_next_sweep",
            "preserved_fields": ["prior", "v2c", "c2v"], "unresolved": ["compound_branch_omitted"],
            "alpha": 0.8, "trunk_sweeps": 1, "continuation_sweeps": 1,
        },
    }[kind]
    manifest["intervention"] = {**common, **arm}
    if kind == "sign_flip":
        manifest["numerical_profile"] = "cpu-float64-min-sum-v1"
        manifest["policies"]["update"]["kind"] = "normalized_min_sum"
        manifest["policies"]["update"]["parameter_assignment"] = {"shape": "scalar", "value": 0.8}
    return manifest


def _public_v5_b1_restart() -> dict[str, object]:
    manifest = _public_v5()
    source = json.loads((ROOT / "data/manifests/phase3-pilot-b1.json").read_text())
    manifest["run_id"] = "phase5-public-b1-restart"
    manifest["intervention_limits"]["max_total_actions"] = 32
    manifest["artifact"] = source["artifact"]
    manifest["evidence"] = source["evidence"]
    manifest["policies"]["intervention"]["kind"] = "restart_belief"
    manifest["intervention"] = {
        "kind": "restart_belief", "variant": "restart_belief_b1_tcap8_mechanism_v1",
        "source_revision": "arxiv:2511.13281v1", "qualification": "mechanism_only_adaptation",
        "native_availability": "repository_revision_verified_in_phase_research",
        "source_code_commit": "275535ec981763166c8549d91959dc6e371ec4b1",
        "trigger": "root_bp_failure", "operator": "inserted_error_residual_restart",
        "selection": "strict_lower_weight", "lift_rule": "xor_inserted_error",
        "reset_rule": "fresh_per_residual", "preserved_fields": ["inserted_error"],
        "unresolved": ["exact_b1_distance"], "stream_status": "not_applicable",
        "preset": "b1_tcap8_mechanism", "code_id": "b1-ghp-882", "eta": 2,
        "t_cap": 8, "root_sweeps": 1, "residual_sweeps": 2,
    }
    return manifest


def test_canonical_v5_and_compact_v6_public_baseline_roundtrip(tmp_path):
    from bp_registry.manifests import CanonicalExperimentV5, parse_manifest, preflight
    from bp_registry.runner import _canonical_kernel_manifest, preflight_canonical
    from bp_registry.canonical.contracts import CanonicalManifestV6, parse_canonical_manifest

    manifest = _public_v5()
    parsed = parse_manifest(manifest)
    assert isinstance(parsed, CanonicalExperimentV5)
    assert parse_manifest(parsed.model_dump(mode="json")) == parsed
    assert preflight(manifest).manifest == parsed
    compact = _canonical_kernel_manifest(parsed)
    assert compact["schema_version"] == 6
    assert isinstance(parse_canonical_manifest(compact), CanonicalManifestV6)
    saved = tmp_path / "public-v5.json"
    saved.write_text(json.dumps(manifest), encoding="utf-8")
    assert preflight_canonical(saved)["intervention"]["ledger_version"] == 5


def test_intervention_preflight_rejects_unsupported_kernel_before_artifact(monkeypatch):
    from bp_registry.manifests import preflight

    manifest = _public_v5("guided_decimation")
    manifest["policies"]["update"]["kind"] = "normalized_min_sum"
    monkeypatch.setattr("bp_registry.manifests.load_artifact", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("artifact opened")))
    with pytest.raises(ValueError, match="normalized_min_sum|incompatible"):
        preflight(manifest)


@pytest.mark.parametrize("field,value", [
    ("variant", "source_faithful_native"),
    ("operator", "arbitrary_python"),
    ("native_availability", "observed_native_agreement"),
    ("finite_bias_magnitude", float("inf")),
])
def test_intervention_preflight_rejects_false_source_or_nonfinite_before_artifact(monkeypatch, field, value):
    from bp_registry.manifests import preflight

    manifest = _public_v5("guided_decimation")
    manifest["intervention"][field] = value
    monkeypatch.setattr("bp_registry.manifests.load_artifact", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("artifact opened")))
    with pytest.raises(ValueError):
        preflight(manifest)


@pytest.mark.parametrize("kind", ["guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip"])
def test_intervention_preflight_accepts_each_qualified_small_fixture_arm(kind):
    from bp_registry.manifests import CanonicalExperimentV5, preflight
    from bp_registry.canonical.contracts import CanonicalManifestV6, parse_canonical_manifest
    from bp_registry.runner import _canonical_kernel_manifest

    manifest = _public_v5(kind)
    resolved = preflight(manifest)
    assert isinstance(resolved.manifest, CanonicalExperimentV5)
    assert isinstance(parse_canonical_manifest(_canonical_kernel_manifest(resolved.manifest)), CanonicalManifestV6)


def test_intervention_preflight_b1_restart_requires_pinned_artifact_and_unknown_distance():
    from bp_registry.manifests import CanonicalExperimentV5, preflight

    manifest = _public_v5_b1_restart()
    assert isinstance(preflight(manifest).manifest, CanonicalExperimentV5)
    invalid = json.loads(json.dumps(manifest))
    invalid["intervention"]["preset"] = "source_exact_distance"
    invalid["intervention"]["exact_distance"] = 18
    with pytest.raises(ValueError, match="distance|variant"):
        preflight(invalid)
    invalid = json.loads(json.dumps(manifest))
    invalid["artifact"]["raw_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="pinned artifact"):
        preflight(invalid)


def test_source_decisions_qualification_native_availability_restart_distance():
    record = json.loads((ROOT / "docs/evidence/phase5-source-decisions.json").read_text(encoding="utf-8"))
    assert record["schema_version"] == 1
    assert record["recorded_date"] == "2026-09-30"
    assert set(record["arms"]) == {
        "bpgd", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief",
    }
    required = {
        "paper_revision", "source_url", "procedure_anchor", "kernel_family", "trigger",
        "target_and_order", "changed_state", "preserved_state", "reset_rule", "lift_rule",
        "native_repository", "native_commit", "native_availability", "qualification", "source_revision",
        "unresolved", "canonical_identity",
    }
    for arm in record["arms"].values():
        assert required <= set(arm)
        assert arm["unresolved"] is not None
        assert arm["qualification"] in {
            "algorithm_interpretation", "controlled_css_adaptation", "mechanism_only_adaptation",
            "bsfbp_sign_only_controlled_adaptation",
        }
        if arm["source_revision"].startswith("arxiv:") and "v" in arm["source_revision"]:
            assert arm["source_url"].endswith(arm["source_revision"].split(":", 1)[1])
    pilot = json.loads((ROOT / "data/manifests/phase5-b1-mechanism-pilot.json").read_text(encoding="utf-8"))
    for key, arm in record["arms"].items():
        sealed = pilot["arm_manifests"]["guided_decimation" if key == "bpgd" else key]["intervention"]
        assert arm["canonical_identity"] == sealed["variant"]
        assert arm["source_revision"] == sealed["source_revision"]
        assert arm["qualification"] == sealed["qualification"]
        assert arm["native_availability"] == sealed["native_availability"]
    assert record["arms"]["bpgd"]["canonical_identity"] == "algorithm1_v2_interpretation"
    assert record["arms"]["impulse"]["native_availability"] == "unverified"
    assert record["arms"]["impulse"]["source_procedure"]["operator"] == "unchanged_graph_negative_infinite_llr"
    assert record["arms"]["impulse"]["canonical_adaptation"]["operator"] == "exact_structural_shortening"
    assert record["arms"]["bpgd"]["native_availability"] == "unverified"
    assert record["arms"]["sign_flip"]["native_availability"] == "unverified"
    assert record["arms"]["syndrome_flip"]["native_commit"] == "0417d33fc2ffb3b442d0397bb09954fc1c6c3938"
    assert record["arms"]["restart_belief"]["native_commit"] == "275535ec981763166c8549d91959dc6e371ec4b1"
    restart = record["arms"]["restart_belief"]
    assert restart["b1_distance"] == {"status": "source_bounded", "lower": 18, "upper": 24}
    assert restart["b1_t_cap"] == 8
    assert restart["qualification"] == "mechanism_only_adaptation"


@pytest.mark.parametrize("kind", ["identity", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip"])
def test_phase5_public_execution_and_replay_each_small_arm(tmp_path, kind):
    from bp_registry.cli import run_canonical, verify_canonical_shot
    from bp_registry.ledger import read_canonical_events

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_public_v5(kind)), encoding="utf-8")
    output = tmp_path / "output"
    report = run_canonical(manifest_path, output, shot_id=0)
    assert report["shot_id"] == 0
    events = read_canonical_events(output / "events.jsonl")
    assert all(row["ledger_version"] == 5 for row in events)
    assert events[1]["data"]["identity"]["intervention_kind"] == kind
    assert verify_canonical_shot(manifest_path, output, shot_id=0)["termination"] == events[-1]["termination"]


def test_phase5_public_execution_b1_restart_replay(tmp_path):
    from bp_registry.cli import run_canonical, verify_canonical_shot
    from bp_registry.ledger import read_canonical_events

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_public_v5_b1_restart()), encoding="utf-8")
    output = tmp_path / "output"
    run_canonical(manifest_path, output, shot_id=0)
    events = read_canonical_events(output / "events.jsonl")
    assert events[1]["data"]["identity"]["intervention_kind"] == "restart_belief"
    assert verify_canonical_shot(manifest_path, output, shot_id=0)["termination"] == events[-1]["termination"]


@pytest.mark.parametrize("mutation", ["qualification", "missing_attempt", "duplicate_leaf", "candidate"])
def test_phase5_replay_rejects_rehashed_semantic_tamper(tmp_path, mutation):
    from bp_registry.cli import run_canonical, verify_canonical_shot
    from bp_registry.ledger import _canonical_event_id

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_public_v5("identity")), encoding="utf-8")
    output = tmp_path / "output"
    run_canonical(manifest_path, output, shot_id=0)
    ledger = output / "events.jsonl"
    events = [json.loads(line) for line in ledger.read_text().splitlines()]
    if mutation == "qualification":
        events[1]["data"]["identity"]["qualification"] = "source_faithful"
    elif mutation == "missing_attempt":
        events = [event for event in events if event["kind"] != "attempt"]
    elif mutation == "duplicate_leaf":
        work = next(event for event in events if event["kind"] == "work")
        work["data"]["payload"]["leaves"].append(dict(work["data"]["payload"]["leaves"][0]))
    else:
        terminal = events[-1]
        terminal["data"]["payload"]["candidate"] = [1, 1, 1]
    for event in events:
        event["event_id"] = _canonical_event_id(event)
    ledger.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events))
    with pytest.raises(ValueError):
        verify_canonical_shot(manifest_path, output, shot_id=0)


def test_phase5_calibration_manifest_b1_identity_seven_arms_finite_caps_and_disjoint_samples():
    from scripts.run_phase5_pilot import ARMS, CALIBRATION, _evaluation_projection, _stage

    design = _stage(CALIBRATION, stage="calibration")
    assert tuple(design["arm_order"]) == ARMS
    assert design["shot_ids"] == list(range(4))
    assert design["error_rate"] == 0.07
    assert {design["arm_manifests"][arm]["randomness"]["physical_sample_identity"] for arm in ARMS} == {
        design["physical_sample_identity"]
    }
    for arm in ARMS:
        manifest = design["arm_manifests"][arm]
        assert manifest["artifact"]["code_id"] == "b1-ghp-882"
        assert manifest["artifact"]["raw_sha256"] == "3b3fb669daf18cb294049c2c20a457a2da997ad1a7da9f0667171d3b48eb38a6"
        assert manifest["evidence"]["relation"] == "pilot_adaptation"
        assert manifest["evidence"]["assessment_status"] == "not_assessed"
        assert manifest["environment"]["omp_num_threads"] == 1
        limits = manifest["intervention_limits"]
        assert limits["max_runtime_seconds"] == 300.0
        assert limits["max_trace_records"] == 512
        assert limits["max_total_attempts"] == 64
        assert limits["max_total_actions"] == 128
        assert all(0 <= count <= 300000 for count in limits["work_caps"].values())
    assert design["arm_manifests"]["guided_decimation"]["intervention"]["round_limit"] == 16
    assert design["arm_manifests"]["guided_decimation"]["intervention"]["sweeps_per_round"] == 10
    assert design["arm_manifests"]["impulse"]["intervention"]["attempt_cap"] == 8
    assert design["arm_manifests"]["freezing"]["intervention"]["retry_cap"] == 8
    assert design["arm_manifests"]["syndrome_flip"]["intervention"]["top_k"] == 8
    assert design["arm_manifests"]["syndrome_flip"]["intervention"]["max_weight"] == 1
    assert design["arm_manifests"]["restart_belief"]["intervention"]["eta"] == 8
    assert design["arm_manifests"]["restart_belief"]["intervention"]["t_cap"] == 8
    assert design["arm_manifests"]["restart_belief"]["intervention"]["residual_sweeps"] == 10
    evaluation = _evaluation_projection(design)
    assert evaluation["shot_ids"] == list(range(16))
    assert evaluation["physical_sample_identity"] != design["physical_sample_identity"]
    assert all(design["arm_manifests"][arm]["intervention_limits"] == evaluation["arm_manifests"][arm]["intervention_limits"] for arm in ARMS)


def test_phase5_evaluation_rejected_without_entitlement_or_cap_freeze(tmp_path, monkeypatch):
    import scripts.run_phase5_pilot as pilot

    monkeypatch.setattr(pilot, "FREEZE", tmp_path / "missing-freeze.json")
    monkeypatch.setattr(pilot, "ENTITLEMENT", tmp_path / "missing-entitlement.json")
    monkeypatch.setattr(pilot, "EVALUATION_OUTPUT", tmp_path / "evaluation")
    with pytest.raises(FileNotFoundError):
        pilot.evaluate()
    assert not (tmp_path / "evaluation").exists()


def test_phase5_cap_freeze_self_audit_rejects_digest_mismatch(tmp_path, monkeypatch):
    import scripts.run_phase5_pilot as pilot

    frozen = tmp_path / "freeze.json"
    evaluation = tmp_path / "evaluation.json"
    frozen.write_text(json.dumps({"evaluation_design_digest": "0" * 64}), encoding="utf-8")
    evaluation.write_text(json.dumps({"cap_freeze_digest": "1" * 64}), encoding="utf-8")
    monkeypatch.setattr(pilot, "FREEZE", frozen)
    monkeypatch.setattr(pilot, "EVALUATION", evaluation)
    with pytest.raises(ValueError, match="digests do not agree"):
        pilot.self_audit()


@pytest.mark.parametrize("mutation", (
    "entitlement_digest", "cap_freeze_digest", "evaluation_manifest_digest",
    "frozen_cap", "qualification", "availability", "arm_membership", "sample_identity",
))
def test_phase5_evaluation_preflight_rejects_frozen_prerequisite_tamper_without_output(
    tmp_path, monkeypatch, mutation,
):
    """A changed seal or scientific control must fail before opening output."""
    import scripts.run_phase5_pilot as pilot

    calibration = pilot._read(pilot.CALIBRATION)
    entitlement = pilot._read(pilot.ENTITLEMENT)
    freeze = pilot._read(pilot.FREEZE)
    evaluation = pilot._read(pilot.EVALUATION)
    entitlement_path = tmp_path / "entitlement.json"
    freeze_path = tmp_path / "freeze.json"
    evaluation_path = tmp_path / "evaluation.json"
    output = tmp_path / "evaluation-output"
    if mutation == "entitlement_digest":
        entitlement["purpose"] = "tampered"
    elif mutation == "cap_freeze_digest":
        freeze["caps_source"] = "outcome-conditioned"
    elif mutation == "evaluation_manifest_digest":
        evaluation["shot_ids"] = list(range(15))
    elif mutation == "frozen_cap":
        evaluation["arm_manifests"]["impulse"]["intervention_limits"]["max_total_actions"] += 1
    elif mutation == "qualification":
        evaluation["arm_manifests"]["guided_decimation"]["intervention"]["qualification"] = "source_faithful"
    elif mutation == "availability":
        evaluation["arm_manifests"]["restart_belief"]["intervention"]["native_availability"] = "available"
    elif mutation == "arm_membership":
        evaluation["arm_order"].pop()
    elif mutation == "sample_identity":
        evaluation["physical_sample_identity"] = calibration["physical_sample_identity"]
    entitlement_path.write_bytes(
        json.dumps(entitlement).encode("utf-8") if mutation == "entitlement_digest" else pilot.ENTITLEMENT.read_bytes()
    )
    freeze_path.write_bytes(
        json.dumps(freeze).encode("utf-8") if mutation == "cap_freeze_digest" else pilot.FREEZE.read_bytes()
    )
    evaluation_path.write_bytes(
        json.dumps(evaluation).encode("utf-8") if mutation not in {"entitlement_digest", "cap_freeze_digest"}
        else pilot.EVALUATION.read_bytes()
    )
    monkeypatch.setattr(pilot, "ENTITLEMENT", entitlement_path)
    monkeypatch.setattr(pilot, "FREEZE", freeze_path)
    monkeypatch.setattr(pilot, "EVALUATION", evaluation_path)
    monkeypatch.setattr(pilot, "EVALUATION_OUTPUT", output)
    # The calibration's already checked identity and objective summary are fixed.
    # This isolates each seal mutation from the expensive B1 policy preflight.
    monkeypatch.setattr(pilot, "_stage", lambda _path, *, stage: calibration if stage == "calibration" else evaluation)
    monkeypatch.setattr(pilot, "_calibration_objective_summary", lambda _design: freeze["calibration_objective_summary"])
    with pytest.raises(ValueError):
        pilot.evaluate()
    assert not output.exists()


def test_phase5_public_verify_run_accepts_relative_reference_to_absolute_result_path(tmp_path):
    """The public verifier must accept either spelling of the same saved output."""
    from bp_registry.cli import run_canonical, verify_run

    manifest = _public_v5("identity")
    manifest["run_id"] = "phase5-relative-verify-regression"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    run_canonical(path, output)
    relative_output = Path(os.path.relpath(output, ROOT))
    report = verify_run(relative_output)
    assert report["final_row_count"] == manifest["budgets"]["max_shots"]
