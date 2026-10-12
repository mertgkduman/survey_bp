"""One-unit tracer coverage for the immutable campaign boundary."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
INNER_MANIFEST = "data/manifests/canonical-three-qubit-development.json"


def _campaign_api():
    """Keep the RED failure an assertion about the public campaign capability."""
    try:
        return importlib.import_module("bp_registry.campaigns")
    except ModuleNotFoundError:
        return None


def _spec_payload() -> dict[str, object]:
    manifest_bytes = (ROOT / INNER_MANIFEST).read_bytes()
    from bp_registry.manifests import manifest_digest, preflight

    manifest_namespace = manifest_digest(preflight(ROOT / INNER_MANIFEST).manifest)
    return {
        "schema": "campaign_spec_v1",
        "inner_manifest_path": INNER_MANIFEST,
        "inner_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "source_lock_sha256": "1" * 64,
        "environment_lock_sha256": "2" * 64,
        "cohort_id": "tracer",
        "point_id": "p100",
        "sample_namespace": manifest_namespace,
        "sample_id": 1,
        "arm_id": "identity",
        "decoder_seed_identity": "canonical-deterministic-no-local-randomness-v1",
        "final_look": 1,
        "alpha": 0.05,
        "outcome_rule": "all_terminal_shots_are_logical_failures",
        "max_events": 64,
        "max_evidence_bytes": 1_000_000,
    }


def test_tracer_runs_seals_verifies_and_reconstructs_zero_failure(tmp_path: Path):
    """A frozen one-shot CSS unit has replayable, exact all-shot evidence."""
    api = _campaign_api()
    assert api is not None, "campaign_spec_v1 tracer must provide the campaign package"

    spec = api.CampaignSpecV1.model_validate(_spec_payload())
    first = api.run_one_unit(spec, campaign_root=ROOT, output_root=tmp_path / "first", worker_label="local-a")
    second = api.run_one_unit(spec, campaign_root=ROOT, output_root=tmp_path / "second", worker_label="slurm-999")

    assert first["campaign_spec_digest"] == second["campaign_spec_digest"]
    assert first["campaign_plan_digest"] == second["campaign_plan_digest"]
    assert first["unit_key"] == second["unit_key"]
    assert first["physical_sample_identity"] == second["physical_sample_identity"]
    assert first["terminal_fact"] == second["terminal_fact"]
    assert "campaign_plan_digest" not in first["unit_key"]
    assert b"campaign_plan_digest" not in first["campaign_spec_bytes"]
    assert b"campaign_plan_digest" not in first["campaign_plan_preimage"]

    checked = api.verify_shard(first["receipt_path"], campaign_root=ROOT)
    report = api.reconstruct_fixed_shot(checked)
    assert report["completed"] == 1
    assert report["failures"] == 0
    assert report["interval"]["method"] == "exact"
    assert report["interval"]["upper"] > 0.0


def test_identity_is_acyclic_and_changes_only_with_scientific_primitives():
    """Executor labels never enter scientific identities, while source locks do."""
    api = _campaign_api()
    assert api is not None, "campaign_spec_v1 tracer must provide the campaign package"

    original = api.CampaignSpecV1.model_validate(_spec_payload())
    changed_payload = json.loads(json.dumps(_spec_payload()))
    changed_payload["source_lock_sha256"] = "3" * 64
    changed = api.CampaignSpecV1.model_validate(changed_payload)

    original_plan = api.build_one_unit_plan(original)
    changed_plan = api.build_one_unit_plan(changed)
    assert original_plan.campaign_spec_digest != changed_plan.campaign_spec_digest
    assert original_plan.unit_key != changed_plan.unit_key
    assert original_plan.campaign_plan_digest != changed_plan.campaign_plan_digest
    assert b"campaign_plan_digest" not in original_plan.campaign_spec_bytes
    assert b"campaign_plan_digest" not in original_plan.campaign_plan_preimage


def test_sample_identity_is_arm_and_worker_neutral_but_decoder_randomness_is_arm_scoped():
    """Matched arms retain bytes while decoder-local streams remain independent."""
    from bp_registry.campaigns.identity import (
        decoder_randomness_identity,
        physical_sample_identity,
    )

    scientific = "a" * 64
    sample = physical_sample_identity(
        campaign_spec_digest=scientific,
        cohort_id="bb144",
        point_id="p005",
        sample_namespace="shared-errors-v1",
        sample_id=7,
    )
    assert sample == physical_sample_identity(
        campaign_spec_digest=scientific,
        cohort_id="bb144",
        point_id="p005",
        sample_namespace="shared-errors-v1",
        sample_id=7,
    )
    left = decoder_randomness_identity(
        campaign_spec_digest=scientific, arm_id="spa", sample_id=7,
        decoder_seed_identity="spa-seed-v1",
    )
    right = decoder_randomness_identity(
        campaign_spec_digest=scientific, arm_id="ms", sample_id=7,
        decoder_seed_identity="ms-seed-v1",
    )
    assert left != right


def test_persisted_sample_receipt_rejects_tampered_bytes_before_decoder_use():
    """A non-reproducible backend gets one hash-bound artifact for all arms."""
    from bp_registry.campaigns.identity import (
        PersistedSampleReceiptV1,
        physical_sample_identity,
        verify_persisted_sample,
    )

    artifact = b"fixed physical error vector"
    sample = physical_sample_identity(
        campaign_spec_digest="a" * 64, cohort_id="bb144", point_id="p005",
        sample_namespace="shared-errors-v1", sample_id=7,
    )
    receipt = PersistedSampleReceiptV1(
        campaign_spec_digest="a" * 64, cohort_id="bb144", point_id="p005",
        sample_namespace="shared-errors-v1", sample_id=7,
        physical_sample_identity=sample, artifact_sha256=sha256(artifact).hexdigest(),
        artifact_bytes=len(artifact),
    )
    assert verify_persisted_sample(receipt, artifact) == artifact
    with pytest.raises(ValueError, match="digest"):
        verify_persisted_sample(receipt, b"X" + artifact[1:])


def test_public_campaign_facade_exports_work_plan() -> None:
    """The supported facade exposes the general paired-work contract."""
    api = _campaign_api()
    assert api is not None
    expected = {
        "CampaignWorkSpecV1",
        "MaterializedPhysicalSampleV1",
        "freeze_campaign_work_spec",
        "run_canonical_work_plan",
        "reconstruct_campaign_report",
        "verify_campaign_report",
        "verify_campaign_routes",
    }
    assert expected <= set(api.__all__)


def _paired_work_spec_payload() -> dict[str, object]:
    """One bounded physical error and two real canonical decoder calls."""
    from bp_registry.runner import canonical_public_manifest_context

    manifest = ROOT / INNER_MANIFEST
    context = canonical_public_manifest_context(manifest)
    public = context.manifest
    matrix = sha256(context.code.hx.tobytes(order="C") + b"\0" + context.code.hz.tobytes(order="C")).hexdigest()
    outcomes = [
        {"terminal_status": status, "all_shot": all_shot, "conditional": conditional}
        for status, all_shot, conditional in (
            ("exact", "success", "accepted"), ("stabilizer_equivalent", "success", "accepted"),
            ("wrong_logical_action", "failure", "accepted"), ("invalid_syndrome", "failure", "excluded"),
            ("no_proposal", "failure", "excluded"), ("nonconvergence", "failure", "excluded"),
            ("timeout", "failure", "excluded"), ("postselected_rejection", "failure", "excluded"),
            ("infrastructure_interruption", "incomplete", "incomplete"),
        )
    ]
    return {
        "schema": "campaign_work_spec_v1",
        "arms": [
            {"arm_id": "left", "manifest_path": INNER_MANIFEST, "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(), "decoder_seed_identity": public.randomness.decoder_seed_identity},
            {"arm_id": "right", "manifest_path": INNER_MANIFEST, "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(), "decoder_seed_identity": public.randomness.decoder_seed_identity},
        ],
        "shared_sampler": {
            "code_id": public.artifact.code_id, "artifact_raw_sha256": public.artifact.raw_sha256,
            "artifact_semantic_sha256": public.artifact.semantic_sha256, "matrix_sha256": matrix,
            "channel_family": "css_code_capacity_v1", "x_error_rate": public.error_rate, "z_error_rate": 0.0,
            "sampler_algorithm": "bp_registry_sample_shot_v1", "sampler_version": "v1",
            "physical_sample_namespace": public.randomness.physical_sample_identity or context.manifest_sha256,
            "physical_sample_seed": public.randomness.sample_seed,
        },
        "coordinates": [{"cohort_id": "paired", "point_id": "p100", "sample_namespace": public.randomness.physical_sample_identity or context.manifest_sha256, "sample_ids": [0]}],
        "look_sample_boundaries": [1], "units_per_shard": 2,
        "assessment": {
            "schema": "campaign_assessment_v1", "targets": [{"target_id": "p100", "target_receipt_sha256": "a" * 64, "lower": 0.0, "upper": 1.0, "absolute_tolerance": 0.0}],
            "interval": {"method": "exact_clopper_pearson", "confidence_level": 0.95},
            "families": [{"family_id": "paired-family", "alpha": 0.05, "member_target_ids": ["p100"]}],
            "stopping": {"mode": "fixed_shot", "final_shots": 1, "batch_size": 1},
            "outcome_matrix": {"rule_id": "all_shot_v1", "treatments": outcomes}, "decision_rule": "target_interval_containment_v1",
            "resources": {"max_shots": 1, "max_looks": 1, "max_batch_size": 1, "max_decoder_work": 1000, "max_events": 2, "max_evidence_bytes": 1_000_000, "max_storage_bytes": 1_000_000},
        },
        "source_lock_sha256": "b" * 64, "environment_lock_sha256": "c" * 64, "dependency_lock_sha256": "d" * 64,
        "target_arm_ids": {"p100": "left"}, "source_denominator_required_by_target": {}, "source_denominators": {},
    }


def test_paired_canonical_replays_identical_error_bytes(tmp_path: Path) -> None:
    api = _campaign_api()
    assert api is not None
    plan = api.freeze_campaign_work_spec(api.CampaignWorkSpecV1.model_validate(_paired_work_spec_payload()))
    result = api.run_canonical_work_plan(plan, campaign_root=ROOT, output_root=tmp_path)
    attempts = result["verified_attempts"]
    assert len(attempts) == 2
    assert attempts[0]["materialized_sample_sha256"] == attempts[1]["materialized_sample_sha256"]
    assert attempts[0]["physical_error_sha256"] == attempts[1]["physical_error_sha256"]
    assert plan.units[0].decoder_randomness_identity != plan.units[1].decoder_randomness_identity


def test_paired_canonical_rejects_equal_labels_with_different_material(tmp_path: Path) -> None:
    api = _campaign_api()
    assert api is not None
    payload = _paired_work_spec_payload()
    payload["shared_sampler"]["x_error_rate"] = 0.2  # type: ignore[index]
    plan = api.freeze_campaign_work_spec(api.CampaignWorkSpecV1.model_validate(payload))
    with pytest.raises(ValueError, match="incompatible"):
        api.run_canonical_work_plan(plan, campaign_root=ROOT, output_root=tmp_path)
    assert not list(tmp_path.iterdir())


def test_paired_canonical_rejects_attempt_or_ledger_tamper(tmp_path: Path) -> None:
    api = _campaign_api()
    assert api is not None
    plan = api.freeze_campaign_work_spec(api.CampaignWorkSpecV1.model_validate(_paired_work_spec_payload()))
    result = api.run_canonical_work_plan(plan, campaign_root=ROOT, output_root=tmp_path)
    tampered = dict(result["verified_attempts"][0])
    tampered["canonical_ledger_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="receipt bytes"):
        api.verify_canonical_attempt(record=tampered, plan=plan)


def _single_arm_failure_count_work_spec_payload() -> dict[str, object]:
    """A one-shot canonical adaptation with prospective failure-count caps."""
    from bp_registry.runner import canonical_public_manifest_context, derive_canonical_executable_maxima

    payload = _paired_work_spec_payload()
    payload["arms"] = [payload["arms"][0]]  # type: ignore[index]
    payload["units_per_shard"] = 1
    arm = payload["arms"][0]  # type: ignore[index]
    assert isinstance(arm, dict)
    derived = derive_canonical_executable_maxima(
        canonical_public_manifest_context(ROOT / str(arm["manifest_path"]))
    )
    limits = {"schema": "failure_count_executable_limit_receipt_v1", **derived.as_evidence()}
    batch_evidence = derived.derived_evidence_bytes_per_unit + derived.partial_receipt_reserve_bytes
    batch_storage = derived.derived_storage_bytes_per_unit + derived.partial_receipt_reserve_bytes
    resources = payload["assessment"]["resources"]  # type: ignore[index]
    resources.update({"max_shots": 1, "max_batch_size": 1, "max_events": derived.derived_events_per_unit,
                      "max_decoder_work": derived.derived_work_per_unit, "max_evidence_bytes": batch_evidence,
                      "max_storage_bytes": batch_storage})
    authorization = {
        "schema": "failure_count_batch_authorization_v1", "policy_binding_sha256": derived.policy_binding_sha256,
        "executable_limit_receipt_sha256": __import__("bp_registry.campaigns.contracts", fromlist=["FailureCountExecutableLimitReceiptV1"]).FailureCountExecutableLimitReceiptV1.model_validate(limits).digest(),
        "max_local_workers": 1, "max_shots_per_batch": 1, "max_work_per_batch": derived.derived_work_per_unit,
        "max_events_per_batch": derived.derived_events_per_unit, "max_evidence_bytes_per_batch": batch_evidence,
        "max_storage_bytes_per_batch": batch_storage, "monotonic_clock": "monotonic_ns_v1",
        "per_unit_timeout_ns": 1_000_000_000,
    }
    policy = {
        "schema": "failure_count_policy_v1", "policy_binding_sha256": derived.policy_binding_sha256,
        "campaign_plan_sha256": "6" * 64, "target_failures": 1, "batch_size": 1,
        "shot_order": "campaign_cohort_point_sample_ordinal_v1",
        "failure_event": "decoder_logical_failure_v1",
        "procedure": {"method": "exact_inverse_binomial", "confidence_level": 0.95, "sidedness": "two_sided"},
        "multiplicative_rule": {"rule": "multiplicative_target_interval_containment_v1", "factor": 1.5},
        "caps": {"max_shots": 1, "max_decoder_work": derived.derived_work_per_unit, "max_events": derived.derived_events_per_unit,
                 "max_evidence_bytes": batch_evidence, "max_storage_bytes": batch_storage, "max_wall_seconds": 60.0},
        "cap_precedence": ["wall", "storage", "evidence", "events", "work", "shots"],
        "executable_limits": limits, "batch_authorization": authorization,
    }
    payload["assessment"].update({  # type: ignore[index]
        "interval": None,
        "stopping": policy,
        "decision_rule": {"rule": "multiplicative_target_interval_containment_v1", "factor": 1.5},
    })
    return {"schema": "failure_count_work_spec_v1", "campaign_work_spec": payload, "policy": policy}


def _ordered_work_spec_payload() -> dict[str, object]:
    base = _paired_work_spec_payload()
    base["coordinates"] = [
        {"cohort_id": "zeta", "point_id": "p100", "sample_namespace": base["shared_sampler"]["physical_sample_namespace"], "sample_ids": [1]},
        {"cohort_id": "alpha", "point_id": "p100", "sample_namespace": base["shared_sampler"]["physical_sample_namespace"], "sample_ids": [0]},
    ]
    base["look_sample_boundaries"] = [2]
    base["units_per_shard"] = 1
    base["assessment"]["stopping"]["final_shots"] = 2
    base["assessment"]["resources"].update({"max_shots": 2, "max_batch_size": 2, "max_events": 4})
    return {"schema": "ordered_campaign_work_spec_v1", "campaign_work_spec": base,
            "execution_order": {"schema": "campaign_execution_order_v1",
                                "rule": "coordinate_point_namespace_sample_declared_arm_v1",
                                "arm_order": ["right", "left"]}}


def test_ordered_work_spec_freezes_declared_arm_order_and_group_ordinals() -> None:
    from bp_registry.campaigns.contracts import OrderedCampaignWorkSpecV1
    from bp_registry.campaigns.planning import freeze_ordered_campaign_work_spec

    spec = OrderedCampaignWorkSpecV1.model_validate(_ordered_work_spec_payload())
    plan = freeze_ordered_campaign_work_spec(spec)
    assert [unit.arm_id for unit in plan.units] == ["right", "left", "right", "left"]
    assert [unit.cohort_id for unit in plan.units] == ["alpha", "alpha", "zeta", "zeta"]
    preimage = json.loads(plan.campaign_plan_preimage)
    assert preimage["execution_order"]["arm_order"] == ["right", "left"]
    assert [group["group_ordinal"] for group in preimage["groups"]] == [1, 2]
    assert [entry["unit_ordinal"] for entry in preimage["units"]] == [1, 2, 3, 4]
    assert preimage["groups"][0]["unit_keys"] == [plan.units[0].key, plan.units[1].key]


def test_declared_arm_order_changes_identity_but_input_topology_permutation_does_not() -> None:
    from bp_registry.campaigns.contracts import CampaignWorkSpecV1, OrderedCampaignWorkSpecV1
    from bp_registry.campaigns.planning import freeze_campaign_work_spec, freeze_ordered_campaign_work_spec

    original = _ordered_work_spec_payload()
    historical = CampaignWorkSpecV1.model_validate(original["campaign_work_spec"])
    historical_bytes = historical.primitive_bytes()
    historical_plan_bytes = freeze_campaign_work_spec(historical).campaign_plan_preimage
    baseline = freeze_ordered_campaign_work_spec(OrderedCampaignWorkSpecV1.model_validate(original))
    permuted = json.loads(json.dumps(original))
    permuted["campaign_work_spec"]["arms"].reverse()
    permuted["campaign_work_spec"]["coordinates"].reverse()
    assert freeze_ordered_campaign_work_spec(OrderedCampaignWorkSpecV1.model_validate(permuted)).campaign_plan_preimage == baseline.campaign_plan_preimage
    reversed_order = json.loads(json.dumps(original))
    reversed_order["execution_order"]["arm_order"] = ["left", "right"]
    assert freeze_ordered_campaign_work_spec(OrderedCampaignWorkSpecV1.model_validate(reversed_order)).campaign_plan_digest != baseline.campaign_plan_digest
    assert historical.primitive_bytes() == historical_bytes
    assert freeze_campaign_work_spec(historical).campaign_plan_preimage == historical_plan_bytes
    assert [unit.arm_id for unit in freeze_campaign_work_spec(historical).units[:2]] == ["left", "right"]


@pytest.mark.parametrize("arms", (["left"], ["left", "left"], ["left", "unknown"], ["right", "left", "extra"]))
def test_ordered_work_spec_rejects_invalid_declared_arm_membership(arms: list[str]) -> None:
    from bp_registry.campaigns.contracts import OrderedCampaignWorkSpecV1

    payload = _ordered_work_spec_payload()
    payload["execution_order"]["arm_order"] = arms
    with pytest.raises(ValueError, match="arm"):
        OrderedCampaignWorkSpecV1.model_validate(payload)


def test_installed_ordered_campaign_inside_group_partial_resume_and_terminal(tmp_path: Path) -> None:
    document = tmp_path / "ordered.json"
    ordered = _ordered_work_spec_payload()
    coordinate = ordered["campaign_work_spec"]["coordinates"][0]
    coordinate["sample_ids"] = [1, 0]
    ordered["campaign_work_spec"]["coordinates"] = [coordinate]
    document.write_text(json.dumps({"ordered_campaign_work_spec": ordered}), encoding="utf-8")
    planned = _run_installed_campaign("plan", "--campaign", str(document), "--campaign-root", str(ROOT),
                                      "--output-root", str(tmp_path / "plan"))
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    frozen = json.loads(Path(plan_path).read_text())
    assert frozen["publication_slurm_authorization"] == "deny"
    assert frozen["execution_order"]["arm_order"] == ["right", "left"]
    run_root = tmp_path / "run"
    first = _run_installed_campaign("run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
                                    "--output-root", str(run_root), "--max-units", "1")
    assert first.returncode == 0, first.stdout
    first_path = json.loads(first.stdout)["artifact_path"]
    partial = _run_installed_campaign("merge", "--plan", plan_path, "--receipt", first_path,
                                      "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "partial"))
    assert partial.returncode == 0, partial.stdout
    partial_info = json.loads(partial.stdout)
    assert partial_info["complete"] is False
    assert partial_info["terminal_unit_keys"] == [frozen["units"][0]["unit_key"]]
    assert partial_info["missing_group_ordinals"] == [1, 2]
    partial_merge = partial_info["artifact_path"]
    verified = _run_installed_campaign("verify", "--plan", plan_path, "--merge", partial_merge,
                                       "--receipt", first_path, "--campaign-root", str(ROOT))
    assert verified.returncode == 0, verified.stdout
    assert json.loads(verified.stdout)["complete"] is False
    resumed = _run_installed_campaign("resume", "--plan", plan_path, "--merge", partial_merge,
                                      "--campaign-root", str(ROOT))
    assert resumed.returncode == 0, resumed.stdout
    assert json.loads(resumed.stdout)["exact_missing_set"] == [unit["unit_key"] for unit in frozen["units"][1:]]
    premature = _run_installed_campaign("assess", "--plan", plan_path, "--merge", partial_merge,
                                        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "premature"))
    assert premature.returncode != 0
    second = _run_installed_campaign("run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
                                     "--output-root", str(run_root))
    assert second.returncode == 0, second.stdout
    second_path = json.loads(second.stdout)["artifact_path"]
    assert len(json.loads(Path(second_path).read_text())["attempts"]) == 3
    terminal = _run_installed_campaign("merge", "--plan", plan_path, "--receipt", second_path,
                                       "--receipt", first_path, "--campaign-root", str(ROOT),
                                       "--output-root", str(tmp_path / "terminal"))
    assert terminal.returncode == 0, terminal.stdout
    terminal_info = json.loads(terminal.stdout)
    assert terminal_info["complete"] is True
    assessment = _run_installed_campaign("assess", "--plan", plan_path, "--merge", terminal_info["artifact_path"],
                                         "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "assessment"))
    assert assessment.returncode == 0, assessment.stdout
    checked = _run_installed_campaign("verify", "--plan", plan_path, "--merge", terminal_info["artifact_path"],
                                      "--report", json.loads(assessment.stdout)["artifact_path"],
                                      "--campaign-root", str(ROOT))
    assert checked.returncode == 0, checked.stdout
    noncanonical_merge = tmp_path / "noncanonical-ordered-merge.json"
    noncanonical_merge.write_text(json.dumps(json.loads(Path(terminal_info["artifact_path"]).read_text()), indent=2), encoding="utf-8")
    noncanonical = _run_installed_campaign("verify", "--plan", plan_path, "--merge", str(noncanonical_merge),
                                           "--receipt", first_path, "--campaign-root", str(ROOT))
    assert noncanonical.returncode != 0
    reordered = json.loads(Path(second_path).read_text())
    reordered["attempts"].reverse()
    forged = tmp_path / Path(second_path).name
    forged.write_text(json.dumps(reordered), encoding="utf-8")
    rejected = _run_installed_campaign("merge", "--plan", plan_path, "--receipt", first_path,
                                       "--receipt", str(forged), "--campaign-root", str(ROOT),
                                       "--output-root", str(tmp_path / "reordered"))
    assert rejected.returncode != 0
    duplicate = _run_installed_campaign("merge", "--plan", plan_path, "--receipt", first_path,
                                        "--receipt", first_path, "--campaign-root", str(ROOT),
                                        "--output-root", str(tmp_path / "duplicate"))
    assert duplicate.returncode != 0
    denied = _run_installed_campaign("run-shard", "--plan", plan_path, "--array-task-id", "0",
                                     "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "denied"))
    assert denied.returncode != 0


def test_ordered_tamper_rejects_changed_arm_sequence(tmp_path: Path) -> None:
    document = tmp_path / "ordered.json"
    document.write_text(json.dumps({"ordered_campaign_work_spec": _ordered_work_spec_payload()}), encoding="utf-8")
    planned = _run_installed_campaign("plan", "--campaign", str(document), "--campaign-root", str(ROOT),
                                      "--output-root", str(tmp_path / "plan"))
    assert planned.returncode == 0, planned.stdout
    original = json.loads(Path(json.loads(planned.stdout)["artifact_path"]).read_text())
    original["execution_order"]["arm_order"].reverse()
    tampered = tmp_path / "tampered-plan.json"
    tampered.write_text(json.dumps(original), encoding="utf-8")
    rejected = _run_installed_campaign("run-local", "--plan", str(tampered), "--campaign-root", str(ROOT),
                                       "--output-root", str(tmp_path / "run"))
    assert rejected.returncode != 0


def test_single_arm_work_spec_runs_one_verified_canonical_bounded_unit(tmp_path: Path) -> None:
    """A failure-count request runs only its frozen ordinal through canonical evidence."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch, verify_failure_count_partial_attempt
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    spec = FailureCountWorkSpecV1.model_validate(_single_arm_failure_count_work_spec_payload())
    plan = freeze_failure_count_work_spec(spec)
    result = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
    )
    assert result["ordinals"] == (1,)
    assert len(result["verified_attempts"]) == 1
    assert result["verified_attempts"][0]["unit_key"] == plan.units[0].key
    assert result["authorization_projection"]["dispatch_allowed"] is True


def test_failure_count_interruptible_policy_is_explicit_and_default_bytes_stay_strict() -> None:
    """Development interruption is frozen, while historical strict bytes do not drift."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1

    payload = _single_arm_failure_count_work_spec_payload()
    default = FailureCountWorkSpecV1.model_validate(payload)
    assert "dispatch_mode" not in default.policy.model_dump(mode="json", by_alias=True)
    policy = payload["policy"]
    assert isinstance(policy, dict)
    policy["dispatch_mode"] = "interruptible_unit"
    policy["batch_size"] = 2
    limits = policy["executable_limits"]
    assert isinstance(limits, dict)
    policy["interruptible_evidence_bytes"] = limits["derived_evidence_bytes_per_unit"]
    policy["interruptible_storage_bytes"] = limits["derived_storage_bytes_per_unit"]
    campaign = payload["campaign_work_spec"]
    assert isinstance(campaign, dict)
    assessment = campaign["assessment"]
    assert isinstance(assessment, dict)
    resources = assessment["resources"]
    assert isinstance(resources, dict)
    resources["max_batch_size"] = 2
    explicit = FailureCountWorkSpecV1.model_validate(payload)
    assert explicit.policy.dispatch_mode == "interruptible_unit"
    policy["caps"]["max_wall_seconds"] = 0.5
    with pytest.raises(ValueError, match="per-unit wall authorization exceeds"):
        FailureCountWorkSpecV1.model_validate(payload)


def test_bounded_batch_charges_sample_ledger_and_terminal_receipt_to_one_guard(tmp_path: Path) -> None:
    """Every durable unit artifact consumes the same per-unit authorization."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch, verify_failure_count_partial_attempt
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    plan = freeze_failure_count_work_spec(
        FailureCountWorkSpecV1.model_validate(_single_arm_failure_count_work_spec_payload())
    )
    result = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
    )
    snapshot = result["runtime_snapshots"][0]
    attempt = result["verified_attempts"][0]
    receipt = Path(attempt["canonical_ledger_path"]).parent / "attempt.json"
    assert snapshot.scientific_evidence_bytes == Path(attempt["canonical_ledger_path"]).stat().st_size
    assert snapshot.scientific_storage_bytes == (
        Path(attempt["canonical_ledger_path"]).stat().st_size
        + Path(attempt["materialized_sample_path"]).stat().st_size
        + receipt.stat().st_size
    )


def test_interruptible_unit_seals_an_immutable_zero_credit_partial_attempt(tmp_path: Path) -> None:
    """A denied ledger append preserves the exact pending ordinal without outcome credit."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch, verify_failure_count_partial_attempt
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    policy = payload["policy"]
    assert isinstance(policy, dict)
    policy.update({
        "dispatch_mode": "interruptible_unit", "interruptible_evidence_bytes": 1,
        "interruptible_storage_bytes": 1_000_000,
    })
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    result = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
    )
    partial = result["partial_attempt"]
    assert partial.interruption_kind == "interrupted_evidence"
    assert partial.completed_shot_credit == partial.failure_credit == 0
    receipt = Path(partial.canonical_ledger_path).parent / "partial-attempt.json"
    original = receipt.read_bytes()
    assert partial.consumed_control_receipt_bytes == len(original)
    assert not result["verified_attempts"]
    verify_failure_count_partial_attempt(
        record=partial, plan=plan, receipt_sha256=result["partial_attempt_sha256"],
    )
    censored = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
        parent_partial_receipt_sha256=result["partial_attempt_sha256"],
    )
    assert censored["terminal_receipt"].terminal_state == "cap_censored"
    assert censored["terminal_receipt"].total_completed_shots == 0
    assert censored["retained_partial_attempt_sha256"] == result["partial_attempt_sha256"]
    receipt.write_bytes(original.replace(b'"consumed_events":0', b'"consumed_events":1'))
    with pytest.raises(ValueError, match="differ from its hash"):
        verify_failure_count_partial_attempt(
            record=__import__("bp_registry.campaigns.contracts", fromlist=["FailureCountPartialAttemptV1"]).FailureCountPartialAttemptV1.model_validate_json(receipt.read_bytes()),
            plan=plan, receipt_sha256=result["partial_attempt_sha256"],
        )


def test_interruptible_storage_denial_seals_before_materialized_sample_write(tmp_path: Path) -> None:
    """A denied sample write leaves no scientific artifact and spends only control reserve."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch, verify_failure_count_partial_attempt
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    policy = payload["policy"]
    assert isinstance(policy, dict)
    policy.update({"dispatch_mode": "interruptible_unit", "interruptible_evidence_bytes": 1_000_000,
                   "interruptible_storage_bytes": 1})
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    result = run_canonical_bounded_batch(plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1)
    partial = result["partial_attempt"]
    assert partial.interruption_kind == "interrupted_storage"
    assert partial.materialized_sample_sha256 is None
    assert not Path(partial.materialized_sample_path).exists()
    assert partial.attempted_bytes is not None and partial.attempted_bytes > partial.consumed_storage_bytes
    verify_failure_count_partial_attempt(record=partial, plan=plan, receipt_sha256=result["partial_attempt_sha256"])


def test_interruptible_wall_partial_retains_positive_boundary_overshoot(tmp_path: Path) -> None:
    """The campaign records the guard's first inside-unit deadline observation."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    policy = payload["policy"]
    assert isinstance(policy, dict)
    policy.update({"dispatch_mode": "interruptible_unit", "interruptible_evidence_bytes": 3_000_000,
                   "interruptible_storage_bytes": 3_000_000})
    authorization = policy["batch_authorization"]
    assert isinstance(authorization, dict)
    authorization["per_unit_timeout_ns"] = 1
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    ticks = iter((0, 0, 0, 2, 3, 4, 5))
    result = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
        clock_ns=lambda: next(ticks),
    )
    partial = result["partial_attempt"]
    assert partial.interruption_kind == "interrupted_wall"
    assert partial.overshoot_ns is not None and partial.overshoot_ns > 0


def test_bounded_batch_charges_verified_prior_terminal_before_next_dispatch(tmp_path: Path) -> None:
    """One complete shot's actual bytes must reduce the next batch authorization."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    campaign = payload["campaign_work_spec"]
    policy = payload["policy"]
    assert isinstance(campaign, dict) and isinstance(policy, dict)
    campaign["coordinates"][0]["sample_ids"] = [0, 1]
    campaign["look_sample_boundaries"] = [2]
    campaign["assessment"]["resources"]["max_shots"] = 2
    policy["caps"]["max_shots"] = 2
    # The original byte caps admit one maximum-sized batch, but the first
    # terminal consumes positive bytes before the second batch is considered.
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    first = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
    )
    assert len(first["verified_attempts"]) == 1
    with pytest.raises(ValueError, match="hard resource cap: storage"):
        run_canonical_bounded_batch(
            plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=2, batch_size=1,
        )
    assert len(list((tmp_path / "attempts").glob("*/attempt.json"))) == 1


@pytest.mark.parametrize("selected_cap", ("work", "events", "evidence", "storage"))
def test_bounded_batch_checks_each_accumulated_hard_cap_before_dispatch(tmp_path: Path, selected_cap: str) -> None:
    """A spent first unit makes the next maximum fail one selected hard cap."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    campaign = payload["campaign_work_spec"]
    policy = payload["policy"]
    assert isinstance(campaign, dict) and isinstance(policy, dict)
    campaign["coordinates"][0]["sample_ids"] = [0, 1]
    campaign["look_sample_boundaries"] = [2]
    campaign["assessment"]["resources"]["max_shots"] = 2
    policy["caps"]["max_shots"] = 2
    names = {"work": "max_decoder_work", "events": "max_events",
             "evidence": "max_evidence_bytes", "storage": "max_storage_bytes"}
    for cap, name in names.items():
        if cap != selected_cap:
            policy["caps"][name] *= 2
        campaign["assessment"]["resources"][name] = policy["caps"][name]
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    run_canonical_bounded_batch(plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1)
    with pytest.raises(ValueError, match=f"hard resource cap: {selected_cap}"):
        run_canonical_bounded_batch(plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=2, batch_size=1)
    assert len(list((tmp_path / "attempts").glob("*/attempt.json"))) == 1


def test_bounded_cap_censor_after_terminal_and_wall_partial_replays_costs(tmp_path: Path) -> None:
    """A later partial retains the earlier terminal's denominator and wall evidence."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    def two_shot_payload() -> dict[str, object]:
        payload = _single_arm_failure_count_work_spec_payload()
        campaign = payload["campaign_work_spec"]
        policy = payload["policy"]
        assert isinstance(campaign, dict) and isinstance(policy, dict)
        campaign["coordinates"][0]["sample_ids"] = [0, 1]
        campaign["look_sample_boundaries"] = [2]
        campaign["assessment"]["resources"]["max_shots"] = 2
        policy["caps"]["max_shots"] = 2
        policy["target_failures"] = 2
        policy["dispatch_mode"] = "interruptible_unit"
        policy["interruptible_evidence_bytes"] = 3_000_000
        policy["interruptible_storage_bytes"] = 3_000_000
        limits = policy["executable_limits"]
        assert isinstance(limits, dict)
        policy["caps"]["max_decoder_work"] = 2 * limits["derived_work_per_unit"]
        policy["caps"]["max_events"] = 2 * limits["derived_events_per_unit"]
        policy["caps"]["max_evidence_bytes"] = 2 * limits["derived_evidence_bytes_per_unit"]
        policy["caps"]["max_storage_bytes"] = 2 * limits["derived_storage_bytes_per_unit"]
        campaign["assessment"]["resources"].update({
            "max_decoder_work": policy["caps"]["max_decoder_work"],
            "max_events": policy["caps"]["max_events"],
            "max_evidence_bytes": policy["caps"]["max_evidence_bytes"],
            "max_storage_bytes": policy["caps"]["max_storage_bytes"],
        })
        return payload

    trial = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(two_shot_payload()))
    measured = run_canonical_bounded_batch(
        trial, campaign_root=ROOT, output_root=tmp_path / "trial",
        first_ordinal=1, batch_size=1, clock_ns=lambda: 0,
    )["actual_resources"]["storage_bytes"]
    payload = two_shot_payload()
    policy = payload["policy"]
    campaign = payload["campaign_work_spec"]
    assert isinstance(policy, dict) and isinstance(campaign, dict)
    limits = policy["executable_limits"]
    assert isinstance(limits, dict)
    # One more maximum unit fits after the first terminal, but a partial's
    # measured storage makes a fresh retry unaffordable.
    policy["caps"]["max_storage_bytes"] = limits["derived_storage_bytes_per_unit"] + limits["partial_receipt_reserve_bytes"] + measured + 1_000
    campaign["assessment"]["resources"]["max_storage_bytes"] = policy["caps"]["max_storage_bytes"]
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    root = tmp_path / "retained"
    first = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=root, first_ordinal=1, batch_size=1,
        clock_ns=lambda: 0,
    )
    assert len(first["verified_attempts"]) == 1
    ticks = iter((0, 0, 0, 2_000_000_000, 2_000_000_001, 2_000_000_002))
    second = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=root, first_ordinal=2, batch_size=1,
        clock_ns=lambda: next(ticks),
    )
    assert second["partial_attempt"].interruption_kind == "interrupted_wall"
    censored = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=root, first_ordinal=2, batch_size=1,
        parent_partial_receipt_sha256=second["partial_attempt_sha256"],
    )
    terminal = censored["terminal_receipt"]
    assert terminal.terminal_state == "cap_censored"
    assert terminal.total_completed_shots == 1
    assert terminal.realized_storage_bytes >= first["actual_resources"]["storage_bytes"]
    assert len(terminal.wall_boundaries) == 1
    assert censored["retained_partial_attempt_sha256"] == second["partial_attempt_sha256"]
    censor_path = Path(censored["terminal_receipt_path"])
    retained = censor_path.read_bytes()
    assert sha256(retained).hexdigest() == censored["terminal_receipt_sha256"]
    assert censored["actual_resources"]["storage_bytes"] == terminal.realized_storage_bytes
    replay = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=root, first_ordinal=2, batch_size=1,
        parent_partial_receipt_sha256=second["partial_attempt_sha256"],
    )
    assert replay["terminal_receipt_sha256"] == censored["terminal_receipt_sha256"]
    with pytest.raises(ValueError, match="forbids further dispatch"):
        run_canonical_bounded_batch(
            plan, campaign_root=ROOT, output_root=root, first_ordinal=1, batch_size=1,
        )
    censor_path.write_bytes(retained.replace(b'"cap_censored"', b'"target_reached"'))
    with pytest.raises(ValueError, match="conflicts with verified evidence"):
        run_canonical_bounded_batch(
            plan, campaign_root=ROOT, output_root=root, first_ordinal=2, batch_size=1,
            parent_partial_receipt_sha256=second["partial_attempt_sha256"],
        )


def test_interruptible_wall_partial_retries_same_ordinal_under_remaining_budget(tmp_path: Path) -> None:
    """A fresh attempt can complete the same shot when its frozen caps still fit."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    campaign = payload["campaign_work_spec"]
    policy = payload["policy"]
    assert isinstance(campaign, dict) and isinstance(policy, dict)
    policy["dispatch_mode"] = "interruptible_unit"
    policy["interruptible_evidence_bytes"] = 3_000_000
    policy["interruptible_storage_bytes"] = 3_000_000
    for cap_name in ("max_decoder_work", "max_events", "max_evidence_bytes", "max_storage_bytes"):
        policy["caps"][cap_name] *= 2
        campaign["assessment"]["resources"][cap_name] = policy["caps"][cap_name]
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    ticks = iter((0, 0, 0, 2_000_000_000, 2_000_000_001, 2_000_000_002))
    first = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
        clock_ns=lambda: next(ticks),
    )
    assert first["partial_attempt"].interruption_kind == "interrupted_wall"
    resumed = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=1,
        parent_partial_receipt_sha256=first["partial_attempt_sha256"],
    )
    assert len(resumed["verified_attempts"]) == 1
    assert resumed["verified_attempts"][0]["unit_key"] == plan.units[0].key
    assert len(list((tmp_path / "attempts").glob("*/partial-attempt.json"))) == 1
    assert len(list((tmp_path / "attempts").glob("*/attempt.json"))) == 1
    terminal_path = next((tmp_path / "attempts").glob("*/attempt.json"))
    observation = json.loads(terminal_path.read_bytes())["attempt"]["resource_observation"]
    partial = first["partial_attempt"]
    assert resumed["actual_resources"]["storage_bytes"] == (
        partial.consumed_storage_bytes + partial.consumed_control_receipt_bytes
        + observation["scientific_storage_bytes"]
    )


def test_strict_batch_wall_boundary_censors_without_dispatching_tail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A boundary-observed wall cap keeps the completed prefix and leaves the rest undispatched."""
    import bp_registry.campaigns.execution as execution
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    payload = _single_arm_failure_count_work_spec_payload()
    campaign = payload["campaign_work_spec"]
    policy = payload["policy"]
    assert isinstance(campaign, dict) and isinstance(policy, dict)
    campaign["coordinates"][0]["sample_ids"] = [0, 1]
    campaign["look_sample_boundaries"] = [2]
    campaign["assessment"]["resources"].update({"max_shots": 2, "max_batch_size": 2})
    policy["target_failures"] = 2
    policy["batch_size"] = 2
    policy["caps"]["max_shots"] = 2
    policy["batch_authorization"]["max_shots_per_batch"] = 2
    for name, auth_name in (
        ("max_decoder_work", "max_work_per_batch"), ("max_events", "max_events_per_batch"),
        ("max_evidence_bytes", "max_evidence_bytes_per_batch"),
        ("max_storage_bytes", "max_storage_bytes_per_batch"),
    ):
        policy["caps"][name] *= 2
        campaign["assessment"]["resources"][name] = policy["caps"][name]
        policy["batch_authorization"][auth_name] = policy["caps"][name]
    plan = freeze_failure_count_work_spec(FailureCountWorkSpecV1.model_validate(payload))
    original = execution.run_canonical_materialized_one
    completed_first = False

    def finish_first_then_advance_clock(*args: object, **kwargs: object) -> object:
        nonlocal completed_first
        result = original(*args, **kwargs)
        completed_first = True
        return result

    monkeypatch.setattr(execution, "run_canonical_materialized_one", finish_first_then_advance_clock)
    result = execution.run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path, first_ordinal=1, batch_size=2,
        clock_ns=lambda: 2_000_000_000 if completed_first else 0,
    )
    assert result["terminal_receipt"].terminal_state == "cap_censored"
    assert result["terminal_receipt"].first_exhausted_cap == "wall"
    assert result["pending_ordinal"] == 2
    assert result["actual_resources"]["completed_shots"] == 1
    assert result["wall_boundaries"][0][2] > 0
    assert len(list((tmp_path / "attempts").glob("*/attempt.json"))) == 1


def test_canonical_bounded_batch_seals_actual_resources_and_rejects_noncontiguous_dispatch(tmp_path: Path) -> None:
    """The bounded adapter reports actual work and never expands an ordinal slice."""
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.execution import run_canonical_bounded_batch
    from bp_registry.campaigns.planning import freeze_failure_count_work_spec

    plan = freeze_failure_count_work_spec(
        FailureCountWorkSpecV1.model_validate(_single_arm_failure_count_work_spec_payload()),
    )
    result = run_canonical_bounded_batch(
        plan, campaign_root=ROOT, output_root=tmp_path / "bounded", first_ordinal=1, batch_size=1,
    )
    assert result["actual_resources"]["decoder_work"] >= 0
    with pytest.raises(ValueError, match="exact declared ordinal batch"):
        run_canonical_bounded_batch(
            plan, campaign_root=ROOT, output_root=tmp_path / "outside", first_ordinal=2, batch_size=1,
        )


def _planning_inputs():
    from bp_registry.campaigns.planning import CampaignCoordinateV1

    return (
        "a" * 64,
        (CampaignCoordinateV1(
            cohort_id="bb144", point_id="p005", sample_namespace="shared-errors-v1",
            sample_ids=(2, 7),
        ),),
        {"spa": "spa-seed-v1", "ms": "ms-seed-v1"},
    )


def test_unit_key_and_shard_plan_are_acyclic_complete_and_topology_invariant():
    """Scientific shards are fixed before a local or scheduler allocation exists."""
    from bp_registry.campaigns.planning import freeze_work_plan, validate_executor_allocation

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    permuted = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates,
        arm_seed_identities={"ms": "ms-seed-v1", "spa": "spa-seed-v1"},
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    assert plan.campaign_plan_digest == permuted.campaign_plan_digest
    assert plan.unit_keys == permuted.unit_keys
    assert len(plan.unit_keys) == 4
    assert len(set(plan.unit_keys)) == 4
    assert set(key for shard in plan.shards for key in shard.unit_keys) == set(plan.unit_keys)
    assert b"campaign_plan_digest" not in plan.campaign_plan_preimage
    assert set(plan.completed_prefix(1)).isdisjoint(plan.authorized_tail(1))
    assert set(plan.completed_prefix(1)) | set(plan.authorized_tail(1)) == set(plan.unit_keys)
    assert validate_executor_allocation(plan, {shard.shard_id: index for index, shard in enumerate(plan.shards)})
    with pytest.raises(ValueError, match="exactly"):
        validate_executor_allocation(plan, {plan.shards[0].shard_id: 0})


def test_shard_plan_rejects_duplicate_coordinates_and_excessive_bounds():
    """A campaign fails before materializing ambiguous or unbounded work."""
    from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan

    with pytest.raises(ValueError, match="unique"):
        CampaignCoordinateV1(
            cohort_id="bb144", point_id="p005", sample_namespace="shared-errors-v1",
            sample_ids=(7, 7),
        )
    digest, coordinates, arms = _planning_inputs()
    with pytest.raises(ValueError, match="max_total_units"):
        freeze_work_plan(
            campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
            look_sample_boundaries=(1, 2), units_per_shard=2, max_total_units=3,
        )


def _bounded_unit_runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    """Pickle-safe deterministic worker fixture for frozen campaign units."""
    del staging
    return {
        "terminal_fact": {
            "unit_key": unit["unit_key"],
            "termination": "converged",
            "outcome": "exact",
            "logical_failure": False,
        },
        "work_vector": {"bp_calls": 1},
        "persisted_sample_bytes": (
            "sample:" + str(unit["physical_sample_identity"])
        ).encode("ascii"),
    }


def _failing_unit_runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    if str(unit["arm_id"]) == "ms":
        raise RuntimeError("injected worker interruption")
    return _bounded_unit_runner(unit, staging)


def _mismatched_sample_runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    result = _bounded_unit_runner(unit, staging)
    result["persisted_sample_bytes"] = str(unit["arm_id"]).encode("ascii")
    return result


def test_local_matched_arms_reject_different_persisted_sample_bytes(tmp_path: Path):
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    with pytest.raises(ValueError, match="matched arms"):
        execute_local_work_plan(
            plan, output_root=tmp_path / "mismatched", workers=1,
            unit_runner=_mismatched_sample_runner,
        )


def test_local_workers_and_arm_order_preserve_frozen_scientific_evidence(tmp_path: Path):
    """Changing bounded pool topology cannot change frozen arm/sample facts."""
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    serial = execute_local_work_plan(
        plan, output_root=tmp_path / "serial", workers=1, unit_runner=_bounded_unit_runner,
    )
    parallel = execute_local_work_plan(
        plan, output_root=tmp_path / "parallel", workers=2, unit_runner=_bounded_unit_runner,
    )
    assert serial["scientific_records"] == parallel["scientific_records"]
    assert serial["terminal_unit_keys"] == plan.unit_keys
    assert parallel["observed_concurrency"] <= 2
    assert set(parallel["environment"]) <= {
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
    }
    assert all("unavailable_reason" in item for item in parallel["resource_observations"])


def test_local_worker_failure_seals_incomplete_and_retains_completed_units(tmp_path: Path):
    """An interrupted shard retains completed units and leaves only missing work resumable."""
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    result = execute_local_work_plan(
        plan, output_root=tmp_path / "interrupted", workers=2, unit_runner=_failing_unit_runner,
    )
    assert result["incomplete_unit_keys"]
    assert set(result["terminal_unit_keys"]).isdisjoint(result["incomplete_unit_keys"])
    sealed = {record["unit_key"] for record in result["records"]}
    assert sealed < set(plan.unit_keys)
    assert all(Path(record["receipt_path"]).is_file() for record in result["records"])


def _stop_after_first_complete_look(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
    inputs = sorted(str(record["unit_key"]) for record in terminal_records)
    return {
        "decision_input_hashes": [sha256("|".join(inputs).encode("ascii")).hexdigest()],
        "decision_result": {"look": look, "terminal_count": len(inputs)},
        "stop_reason": "all_primary_decisions_resolved",
        "should_stop": look == 1,
    }


def _never_stop(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
    decision = _stop_after_first_complete_look(look=look, terminal_records=terminal_records)
    decision["should_stop"] = False
    return decision


def test_retained_stop_rejects_changed_decision_before_next_look(tmp_path: Path):
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "retained-stop"
    dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    first_look_receipts = tuple(sorted(root.glob("unit-*/receipt.json")))
    with pytest.raises(ValueError, match="conflicts with reconstructed decision"):
        dispatch_finite_looks(
            plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
            decision_for_look=_never_stop,
        )
    assert tuple(sorted(root.glob("unit-*/receipt.json"))) == first_look_receipts


def test_finite_look_recovers_stop_receipt_before_any_later_dispatch(tmp_path: Path):
    """A post-decision crash recovers its exact receipt before the next look runs."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "finite-look"
    with pytest.raises(InterruptedError, match="after decision"):
        dispatch_finite_looks(
            plan, output_root=root, workers=2, unit_runner=_bounded_unit_runner,
            decision_for_look=_stop_after_first_complete_look, fault_after_decision=True,
        )
    first_look = set(plan.completed_prefix(1))
    assert {path.parent.name.removeprefix("unit-") for path in root.glob("unit-*/receipt.json")} == first_look
    merge_path = root / "look-1-merge-receipt.json"
    pre_crash_merge = merge_path.read_bytes()
    recovered = dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    assert recovered["recovered_stop_receipt"] is True
    assert recovered["authorized_undispatched_keys"] == plan.authorized_tail(1)
    assert {path.parent.name.removeprefix("unit-") for path in root.glob("unit-*/receipt.json")} == first_look
    assert (root / "look-stop-receipt.json").is_file()
    assert merge_path.read_bytes() == pre_crash_merge
    assert recovered["stop_receipt"]["merge_receipt_sha256"] == sha256(pre_crash_merge).hexdigest()


def test_finite_look_rejects_a_forged_retained_stop_tail(tmp_path: Path):
    """A retained receipt is checked against the complete frozen boundary again."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "forged-stop"
    dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    receipt_path = root / "look-stop-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["authorized_undispatched"] = []
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="conflicts"):
        dispatch_finite_looks(
            plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
            decision_for_look=_stop_after_first_complete_look,
        )


def test_finite_look_rejects_a_mutated_completed_merge(tmp_path: Path):
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    root = tmp_path / "mutated-merge"
    dispatch_finite_looks(
        plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
        decision_for_look=_stop_after_first_complete_look,
    )
    merge_path = root / "look-1-merge-receipt.json"
    merge_path.write_bytes(merge_path.read_bytes() + b" ")
    first_look_receipts = tuple(sorted(root.glob("unit-*/receipt.json")))
    with pytest.raises(ValueError, match="conflicts with reconstruction"):
        dispatch_finite_looks(
            plan, output_root=root, workers=1, unit_runner=_bounded_unit_runner,
            decision_for_look=_stop_after_first_complete_look,
        )
    assert tuple(sorted(root.glob("unit-*/receipt.json"))) == first_look_receipts


def test_finite_look_maximum_retains_all_realized_units(tmp_path: Path):
    """The maximum declared look stops only after all matched arm units finish."""
    from bp_registry.campaigns.execution import dispatch_finite_looks
    from bp_registry.campaigns.planning import freeze_work_plan

    def maximum(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
        return {
            "decision_input_hashes": [sha256(str(look).encode("ascii")).hexdigest()],
            "decision_result": {"look": look}, "stop_reason": "maximum_reached",
            "should_stop": look == 2,
        }

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    result = dispatch_finite_looks(
        plan, output_root=tmp_path / "maximum", workers=2, unit_runner=_bounded_unit_runner,
        decision_for_look=maximum,
    )
    assert result["stop_receipt"]["stop_reason"] == "maximum_reached"
    assert result["authorized_undispatched_keys"] == ()
    assert len(result["records"]) == len(plan.unit_keys)


def _slurm_api():
    """Keep Slurm transport RED evidence focused on the public adapter."""
    try:
        return importlib.import_module("bp_registry.campaigns.slurm")
    except ModuleNotFoundError:
        return None


def test_slurm_argv_and_array_selection_are_bounded_and_shell_free():
    """A scheduler can select one frozen shard without gaining planning authority."""
    api = _slurm_api()
    assert api is not None, "campaigns must provide the bounded Slurm adapter"

    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    allocation = api.SlurmAllocation(
        partition="research", qos="short", account="bp", wall_minutes=30,
        memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
    )
    argv = api.build_sbatch_argv(
        plan, allocation=allocation,
        allowed_values={"partition": {"research"}, "qos": {"short"}, "account": {"bp"}},
        entrypoint=("/usr/bin/python3", "-m", "bp_registry.campaigns.slurm_entry"),
    )
    assert argv == (
        "sbatch", "--array=0-1%1", "--cpus-per-task=1", "--mem=512M", "--time=30",
        "--partition=research", "--qos=short", "--account=bp", "--",
        "/usr/bin/python3", "-m", "bp_registry.campaigns.slurm_entry",
    )
    assert api.select_array_shard(plan, "1") == plan.shards[1]
    for invalid in (None, "", "-1", "2", "1;touch", " 1"):
        with pytest.raises(ValueError):
            api.select_array_shard(plan, invalid)
    with pytest.raises(ValueError, match="allowlist"):
        api.build_sbatch_argv(
            plan,
            allocation=api.SlurmAllocation(
                partition="unapproved", qos="short", account="bp", wall_minutes=30,
                memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
            ),
            allowed_values={"partition": {"research"}, "qos": {"short"}, "account": {"bp"}},
            entrypoint=("/usr/bin/python3",),
        )
    with pytest.raises(ValueError, match="scheduler identifier"):
        api.SlurmAllocation(
            partition="research;touch", qos="short", account="bp", wall_minutes=30,
            memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
        )
    with pytest.raises(ValueError, match="cpus_per_task"):
        api.SlurmAllocation(
            partition="research", qos="short", account="bp", wall_minutes=30,
            memory_mb=512, cpus_per_task=65, max_concurrent_tasks=1,
        )


def test_slurm_capability_parser_preserves_missing_accounting_as_unavailable():
    """Unknown site policy remains unavailable and cannot become a campaign default."""
    api = _slurm_api()
    assert api is not None, "campaigns must provide the bounded Slurm adapter"

    capabilities = api.parse_site_capabilities(
        scontrol_text="MaxArraySize=32 DefMemPerCPU=2048", sacct_text=None,
    )
    assert capabilities["max_array_size"] == {
        "value": 32, "unavailable_reason": None,
    }
    assert capabilities["default_memory_mb"] == {
        "value": 2048, "unavailable_reason": None,
    }
    assert capabilities["accounting_available"] == {
        "value": None, "unavailable_reason": "sacct output was not supplied",
    }

    verified = api.parse_site_capabilities(
        scontrol_text=None,
        sacct_text="JobIDRaw|State|Elapsed|AllocCPUS|\n42|COMPLETED|00:00:01|1|\n",
    )
    assert verified["accounting_available"] == {"value": True, "unavailable_reason": None}
    for malformed, reason in (
        ("", "sacct output was empty"),
        ("not an accounting record", "sacct output did not contain a bounded accounting record"),
        ("JobIDRaw|State|Elapsed|AllocCPUS\n42|COMPLETED|not-time|1\n", "sacct output contained a malformed accounting record"),
    ):
        unavailable = api.parse_site_capabilities(scontrol_text=None, sacct_text=malformed)
        assert unavailable["accounting_available"] == {"value": None, "unavailable_reason": reason}


def _slurm_allocation(api):
    return api.SlurmAllocation(
        partition="research", qos="short", account="bp", wall_minutes=30,
        memory_mb=512, cpus_per_task=1, max_concurrent_tasks=1,
    )


def _scheduler_observation(api, *, task_id: str, state: str = "COMPLETED"):
    return api.SchedulerObservation(
        job_id="81234", task_id=task_id, allocated_cpus=1, elapsed_seconds=2,
        state=state, exit_code=0 if state == "COMPLETED" else 1,
        accounting_available=None, accounting_unavailable_reason="sacct was unavailable",
        launch_overhead_seconds=1, shard_fixed_cost_seconds=1,
    )


def test_executor_equivalence_keeps_scheduler_receipts_out_of_scientific_results(tmp_path: Path):
    """Synthetic array delivery must reproduce local frozen science byte-for-byte."""
    api = _slurm_api()
    assert api is not None and hasattr(api, "execute_synthetic_slurm_array"), (
        "campaigns must execute frozen shards through the synthetic Slurm harness"
    )
    from bp_registry.campaigns.execution import execute_local_work_plan
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    local = execute_local_work_plan(
        plan, output_root=tmp_path / "local", workers=1, unit_runner=_bounded_unit_runner,
    )
    slurm = api.execute_synthetic_slurm_array(
        plan, output_root=tmp_path / "slurm", unit_runner=_bounded_unit_runner,
        allocation=_slurm_allocation(api),
        observations=tuple(_scheduler_observation(api, task_id=str(index)) for index in range(len(plan.shards))),
    )
    assert slurm["terminal_unit_keys"] == local["terminal_unit_keys"]
    assert slurm["scientific_records"] == local["scientific_records"]
    assert slurm["merge_receipt_sha256"] == api.scientific_records_digest(local["scientific_records"])
    assert all("scheduler" not in record for record in slurm["scientific_records"])
    assert all(receipt["executor_receipt"]["scheduler"]["accounting_available"] is None for receipt in slurm["task_receipts"])
    assert all(receipt["executor_receipt"]["scheduler"]["launch_overhead_seconds"] == 1 for receipt in slurm["task_receipts"])


def test_synthetic_slurm_rejects_cross_shard_sample_mismatch(tmp_path: Path):
    from bp_registry.campaigns.planning import freeze_work_plan
    from bp_registry.campaigns.slurm import execute_synthetic_slurm_array
    api = _slurm_api()
    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=1,
    )
    with pytest.raises(ValueError, match="matched arms"):
        execute_synthetic_slurm_array(
            plan, output_root=tmp_path / "slurm", unit_runner=_mismatched_sample_runner,
            allocation=_slurm_allocation(api),
            observations=tuple(_scheduler_observation(api, task_id=str(index)) for index in range(len(plan.shards))),
        )


def test_scheduler_receipt_preemption_cancellation_and_duplicate_delivery_are_incomplete(tmp_path: Path):
    """Scheduler outcomes retain observations and leave only their frozen units resumable."""
    api = _slurm_api()
    assert api is not None and hasattr(api, "execute_slurm_array_task"), (
        "campaigns must retain scheduler receipts for one frozen array task"
    )
    from bp_registry.campaigns.planning import freeze_work_plan

    digest, coordinates, arms = _planning_inputs()
    plan = freeze_work_plan(
        campaign_spec_digest=digest, coordinates=coordinates, arm_seed_identities=arms,
        look_sample_boundaries=(1, 2), units_per_shard=2,
    )
    for state in ("FAILED", "PREEMPTED", "CANCELLED"):
        receipt = api.execute_slurm_array_task(
            plan, array_task_id="0", output_root=tmp_path / state,
            unit_runner=_bounded_unit_runner, allocation=_slurm_allocation(api),
            observation=_scheduler_observation(api, task_id="0", state=state),
        )
        assert receipt["terminal_unit_keys"] == ()
        assert receipt["incomplete_unit_keys"] == plan.shards[0].unit_keys
        assert receipt["resume_unit_keys"] == plan.shards[0].unit_keys
        assert receipt["executor_receipt"]["scheduler"]["state"] == state
        assert receipt["executor_receipt"]["scheduler"]["accounting_available"] is None
    with pytest.raises(ValueError, match="duplicate"):
        api.execute_synthetic_slurm_array(
            plan, output_root=tmp_path / "duplicate", unit_runner=_bounded_unit_runner,
            allocation=_slurm_allocation(api),
            observations=(
                _scheduler_observation(api, task_id="0"),
                _scheduler_observation(api, task_id="0"),
            ),
        )


def _write_cli_campaign(path: Path) -> Path:
    payload = _spec_payload()
    target_sha256 = sha256((ROOT / INNER_MANIFEST).read_bytes()).hexdigest()
    payload["assessment"] = {
        "schema": "campaign_assessment_v1",
        "targets": [{
            "target_id": "tracer-target", "target_receipt_sha256": target_sha256,
            "lower": 0.0, "upper": 1.0, "absolute_tolerance": 0.0,
        }],
        "interval": {"method": "exact_clopper_pearson", "confidence_level": 0.95},
        "families": [{"family_id": "tracer-family", "alpha": 0.05, "member_target_ids": ["tracer-target"]}],
        "stopping": {"mode": "fixed_shot", "final_shots": 1, "batch_size": 1},
        "outcome_matrix": {
            "rule_id": "all_shot_v1",
            "treatments": [
                {"terminal_status": "exact", "all_shot": "success", "conditional": "accepted"},
                {"terminal_status": "stabilizer_equivalent", "all_shot": "success", "conditional": "accepted"},
                {"terminal_status": "wrong_logical_action", "all_shot": "failure", "conditional": "accepted"},
                {"terminal_status": "invalid_syndrome", "all_shot": "failure", "conditional": "excluded"},
                {"terminal_status": "no_proposal", "all_shot": "failure", "conditional": "excluded"},
                {"terminal_status": "nonconvergence", "all_shot": "failure", "conditional": "excluded"},
                {"terminal_status": "timeout", "all_shot": "failure", "conditional": "excluded"},
                {"terminal_status": "postselected_rejection", "all_shot": "failure", "conditional": "excluded"},
                {"terminal_status": "infrastructure_interruption", "all_shot": "incomplete", "conditional": "incomplete"},
            ],
        },
        "decision_rule": "target_interval_containment_v1",
        "resources": {
            "max_shots": 1, "max_looks": 1, "max_batch_size": 1,
            "max_decoder_work": 64, "max_events": 64,
            "max_evidence_bytes": 1_000_000, "max_storage_bytes": 1_000_000,
        },
    }
    path.write_text(json.dumps({
        "campaign_spec": payload,
        "target_receipts": {"tracer-target": INNER_MANIFEST},
    }, sort_keys=True), encoding="utf-8")
    return path


def _run_campaign_module(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "bp_registry.campaigns.cli", *arguments],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )


def _run_installed_campaign(*arguments: str) -> subprocess.CompletedProcess[str]:
    command = shutil.which("bp-registry-campaign", path=str(Path(sys.executable).parent))
    assert command is not None, "bp-registry-campaign must be installed into the active environment"
    return subprocess.run([command, *arguments], cwd=ROOT, text=True, capture_output=True, check=False)


def test_installed_paired_canonical_local_lifecycle(tmp_path: Path) -> None:
    """The installed command plans and executes the real paired local path."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_installed_campaign(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    run = _run_installed_campaign(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "run"),
    )
    assert run.returncode == 0, run.stdout
    result = json.loads(run.stdout)
    assert result["unit_count"] == 2
    assert (tmp_path / "run" / "samples").is_dir()
    verified = _run_installed_campaign(
        "verify", "--plan", plan_path, "--receipt", result["artifact_path"],
        "--campaign-root", str(ROOT),
    )
    assert verified.returncode == 0, verified.stdout
    merged = _run_installed_campaign(
        "merge", "--plan", plan_path, "--receipt", result["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "merge"),
    )
    assert merged.returncode == 0, merged.stdout
    merge_path = json.loads(merged.stdout)["artifact_path"]
    resumed = _run_installed_campaign("resume", "--plan", plan_path, "--merge", merge_path, "--campaign-root", str(ROOT))
    assert resumed.returncode == 0, resumed.stdout
    assert json.loads(resumed.stdout)["exact_missing_set"] == []
    assessed = _run_installed_campaign(
        "assess", "--plan", plan_path, "--merge", merge_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "assessment"),
    )
    assert assessed.returncode == 0, assessed.stdout


def test_installed_assess_emits_complete_campaign_report(tmp_path: Path) -> None:
    """The installed assessor publishes an immutable, complete paired report."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_installed_campaign(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    run = _run_installed_campaign(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "run"),
    )
    assert run.returncode == 0, run.stdout
    merged = _run_installed_campaign(
        "merge", "--plan", plan_path, "--receipt", json.loads(run.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "merge"),
    )
    assert merged.returncode == 0, merged.stdout
    assessed = _run_installed_campaign(
        "assess", "--plan", plan_path, "--merge", json.loads(merged.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "assessment"),
    )
    assert assessed.returncode == 0, assessed.stdout
    payload = json.loads(assessed.stdout)
    assert payload["report"]["schema"] == "campaign_report_v1"
    assert len(payload["report"]["report_sha256"]) == 64
    report_path = Path(payload["artifact_path"])
    assert report_path.name == "assessment.json"
    assert sha256(report_path.read_bytes()).hexdigest() == payload["artifact_sha256"]


def test_installed_report_verify_reconstructs_retained_report(tmp_path: Path) -> None:
    """The installed verifier replays report inputs instead of trusting JSON cache bytes."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_installed_campaign(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    run = _run_installed_campaign(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "run"),
    )
    merged = _run_installed_campaign(
        "merge", "--plan", plan_path, "--receipt", json.loads(run.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "merge"),
    )
    assessed = _run_installed_campaign(
        "assess", "--plan", plan_path, "--merge", json.loads(merged.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "assessment"),
    )
    assert assessed.returncode == 0, assessed.stdout
    assessment = json.loads(assessed.stdout)
    verified = _run_installed_campaign(
        "verify", "--report", assessment["artifact_path"], "--plan", plan_path,
        "--merge", json.loads(merged.stdout)["artifact_path"], "--campaign-root", str(ROOT),
    )
    assert verified.returncode == 0, verified.stdout
    assert json.loads(verified.stdout)["verified"] is True
    tampered = json.loads(Path(assessment["artifact_path"]).read_text(encoding="utf-8"))
    tampered["status"] = "inconclusive"
    tampered_path = tmp_path / "tampered-assessment.json"
    tampered_path.write_text(json.dumps(tampered, sort_keys=True) + "\n", encoding="utf-8")
    rejected = _run_installed_campaign(
        "verify", "--report", str(tampered_path), "--plan", plan_path,
        "--merge", json.loads(merged.stdout)["artifact_path"], "--campaign-root", str(ROOT),
    )
    assert rejected.returncode != 0


def test_installed_route_equivalence_verify_reconstructs_both_routes(tmp_path: Path) -> None:
    """Local and selected Slurm chains must be separately replayed before comparison."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_installed_campaign(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    local = _run_installed_campaign(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "local"),
    )
    assert local.returncode == 0, local.stdout
    allocation = tmp_path / "allocation.json"
    allocation.write_text(json.dumps({
        "partition": "research", "qos": "short", "account": "bp", "wall_minutes": 10,
        "memory_mb": 256, "cpus_per_task": 1, "max_concurrent_tasks": 1,
    }), encoding="utf-8")
    observation = tmp_path / "observation.json"
    observation.write_text(json.dumps({
        "job_id": "81234", "task_id": "0", "allocated_cpus": 1, "elapsed_seconds": 1,
        "state": "COMPLETED", "exit_code": 0, "accounting_available": None,
        "accounting_unavailable_reason": "sacct unavailable", "launch_overhead_seconds": 0,
        "shard_fixed_cost_seconds": 0,
    }), encoding="utf-8")
    slurm = _run_installed_campaign(
        "run-shard", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "slurm"), "--array-task-id", "0",
        "--allocation", str(allocation), "--scheduler-observation", str(observation),
    )
    assert slurm.returncode == 0, slurm.stdout
    local_merge = _run_installed_campaign(
        "merge", "--plan", plan_path, "--receipt", json.loads(local.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "local-merge"),
    )
    slurm_merge = _run_installed_campaign(
        "merge", "--plan", plan_path, "--receipt", json.loads(slurm.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "slurm-merge"),
    )
    assert local_merge.returncode == slurm_merge.returncode == 0
    local_assessment = _run_installed_campaign(
        "assess", "--plan", plan_path, "--merge", json.loads(local_merge.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "local-report"),
    )
    slurm_assessment = _run_installed_campaign(
        "assess", "--plan", plan_path, "--merge", json.loads(slurm_merge.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "slurm-report"),
    )
    assert local_assessment.returncode == slurm_assessment.returncode == 0
    receipt = _run_installed_campaign(
        "verify-routes", "--plan", plan_path,
        "--local-merge", json.loads(local_merge.stdout)["artifact_path"],
        "--local-report", json.loads(local_assessment.stdout)["artifact_path"],
        "--slurm-merge", json.loads(slurm_merge.stdout)["artifact_path"],
        "--slurm-report", json.loads(slurm_assessment.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--output", str(tmp_path / "route-equivalence.json"),
    )
    assert receipt.returncode == 0, receipt.stdout
    assert json.loads(receipt.stdout)["scientific_records_match"] is True


def test_paired_canonical_local_and_slurm_routes_match(tmp_path: Path) -> None:
    """A selected scheduler shard replays the same frozen canonical evidence."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_campaign_module(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    local = _run_campaign_module(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "local"),
    )
    assert local.returncode == 0, local.stdout
    allocation = tmp_path / "allocation.json"
    allocation.write_text(json.dumps({
        "partition": "research", "qos": "short", "account": "bp", "wall_minutes": 10,
        "memory_mb": 256, "cpus_per_task": 1, "max_concurrent_tasks": 1,
    }), encoding="utf-8")
    observation = tmp_path / "observation.json"
    observation.write_text(json.dumps({
        "job_id": "81234", "task_id": "0", "allocated_cpus": 1, "elapsed_seconds": 1,
        "state": "COMPLETED", "exit_code": 0, "accounting_available": None,
        "accounting_unavailable_reason": "sacct unavailable", "launch_overhead_seconds": 0,
        "shard_fixed_cost_seconds": 0,
    }), encoding="utf-8")
    shard = _run_campaign_module(
        "run-shard", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "slurm"), "--array-task-id", "0",
        "--allocation", str(allocation), "--scheduler-observation", str(observation),
    )
    assert shard.returncode == 0, shard.stdout
    local_payload, shard_payload = json.loads(local.stdout), json.loads(shard.stdout)
    assert shard_payload["executor_route"] == "slurm"
    assert shard_payload["terminal_unit_keys"] == local_payload["terminal_unit_keys"]
    assert shard_payload["materialized_sample_sha256s"] == local_payload["materialized_sample_sha256s"]
    assert shard_payload["physical_error_sha256s"] == local_payload["physical_error_sha256s"]


def test_paired_canonical_slurm_array_is_bounded(tmp_path: Path) -> None:
    """The public paired submission argv covers precisely the frozen shard tuple."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_campaign_module(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    allocation = tmp_path / "allocation.json"
    allocation.write_text(json.dumps({
        "partition": "research", "qos": "short", "account": "bp", "wall_minutes": 10,
        "memory_mb": 256, "cpus_per_task": 1, "max_concurrent_tasks": 1,
    }), encoding="utf-8")
    allowlists = tmp_path / "allowlists.json"
    allowlists.write_text(json.dumps({"partition": ["research"], "qos": ["short"], "account": ["bp"]}), encoding="utf-8")
    emitted = _run_campaign_module(
        "emit-slurm", "--plan", json.loads(planned.stdout)["artifact_path"],
        "--campaign-root", str(ROOT), "--allocation", str(allocation),
        "--site-allowlists", str(allowlists),
    )
    assert emitted.returncode == 0, emitted.stdout
    payload = json.loads(emitted.stdout)
    assert payload["shard_count"] == 1
    assert payload["sbatch_argv"][:2] == ["sbatch", "--array=0-0%1"]


def test_paired_canonical_mixed_route_merge_and_resume(tmp_path: Path) -> None:
    """Verified duplicate route delivery merges once and leaves no retry work."""
    document = tmp_path / "paired.json"
    document.write_text(json.dumps({"campaign_work_spec": _paired_work_spec_payload()}), encoding="utf-8")
    planned = _run_campaign_module(
        "plan", "--campaign", str(document), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "plan"),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = json.loads(planned.stdout)["artifact_path"]
    local = _run_campaign_module(
        "run-local", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "local"),
    )
    assert local.returncode == 0, local.stdout
    allocation = tmp_path / "allocation.json"
    allocation.write_text(json.dumps({
        "partition": "research", "qos": "short", "account": "bp", "wall_minutes": 10,
        "memory_mb": 256, "cpus_per_task": 1, "max_concurrent_tasks": 1,
    }), encoding="utf-8")
    observation = tmp_path / "observation.json"
    observation.write_text(json.dumps({
        "job_id": "81234", "task_id": "0", "allocated_cpus": 1, "elapsed_seconds": 1,
        "state": "COMPLETED", "exit_code": 0, "accounting_available": None,
        "accounting_unavailable_reason": "sacct unavailable", "launch_overhead_seconds": 0,
        "shard_fixed_cost_seconds": 0,
    }), encoding="utf-8")
    shard = _run_campaign_module(
        "run-shard", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "slurm"), "--array-task-id", "0",
        "--allocation", str(allocation), "--scheduler-observation", str(observation),
    )
    assert shard.returncode == 0, shard.stdout
    merged = _run_campaign_module(
        "merge", "--plan", plan_path, "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "merge"),
        "--receipt", json.loads(local.stdout)["artifact_path"],
        "--receipt", json.loads(shard.stdout)["artifact_path"],
    )
    assert merged.returncode == 0, merged.stdout
    merge_path = json.loads(merged.stdout)["artifact_path"]
    envelope = json.loads(Path(merge_path).read_text(encoding="utf-8"))
    assert envelope["canonical_merge"]["terminal_unit_keys"]
    assert len(envelope["materialized_samples_by_identity"]) == 1
    resumed = _run_campaign_module(
        "resume", "--plan", plan_path, "--merge", merge_path, "--campaign-root", str(ROOT),
    )
    assert resumed.returncode == 0, resumed.stdout
    assert json.loads(resumed.stdout)["exact_missing_set"] == []


@pytest.mark.parametrize("raw_profile", (
    '{"measured":NaN,"limit":1.0,"unit":"seconds"}',
    '{"measured":true,"limit":1.0,"unit":"seconds"}',
    '{"measured":0.5,"limit":Infinity,"unit":"seconds"}',
))
def test_cli_profile_gate_rejects_nonfinite_and_boolean_measurements(tmp_path: Path, raw_profile: str):
    """Profile budgets are finite numeric observations with strict JSON output."""
    profile = tmp_path / "profile.json"
    profile.write_text(raw_profile, encoding="utf-8")
    rejected = _run_campaign_module("profile-gate", "--profile", str(profile))
    assert rejected.returncode != 0
    error = json.loads(rejected.stdout)
    assert error["status"] == "error"
    assert "NaN" not in rejected.stdout and "Infinity" not in rejected.stdout

    profile.write_text('{"measured":0.5,"limit":1.0,"unit":"seconds"}', encoding="utf-8")
    accepted = _run_campaign_module("profile-gate", "--profile", str(profile))
    assert accepted.returncode == 0, accepted.stdout
    assert json.loads(accepted.stdout)["profile"]["measured"] == 0.5


def test_cli_preflight_and_plan_freeze_identity_before_any_execution(tmp_path: Path):
    """The public command rejects drift before it can write a run receipt."""
    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    output_root = tmp_path / "campaign-output"

    preflight = _run_campaign_module(
        "preflight", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(output_root),
    )

    assert preflight.returncode == 0, preflight.stderr
    payload = json.loads(preflight.stdout)
    assert payload["status"] == "ok"
    assert len(payload["campaign_spec_digest"]) == 64
    assert not output_root.exists()


def test_operational_gate_preflight_binds_both_paths_without_creating_evidence(tmp_path: Path):
    """The retained Phase 8 gate cannot switch a representative path at launch."""
    study = ROOT / "data/studies/phase8-operational-gate-v1.json"
    output_root = tmp_path / "operational-gate-output"

    accepted = _run_campaign_module(
        "preflight", "--campaign", str(study), "--campaign-root", str(ROOT),
        "--output-root", str(output_root),
    )

    assert accepted.returncode == 0, accepted.stdout
    assert json.loads(accepted.stdout)["sampling_performed"] is False
    assert not output_root.exists()

    drifted = json.loads(study.read_text(encoding="utf-8"))
    drifted["operational_gate"]["eligible_manifests"]["slow"][1] = "0" * 64
    drifted_path = tmp_path / "operational-gate-drifted.json"
    drifted_path.write_text(json.dumps(drifted), encoding="utf-8")
    rejected = _run_campaign_module(
        "preflight", "--campaign", str(drifted_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "must-not-exist"),
    )

    assert rejected.returncode != 0
    assert "operational_gate manifest SHA-256" in json.loads(rejected.stdout)["error"]


def test_paired_canonical_gate_definition_and_documented_lifecycle(tmp_path: Path) -> None:
    """The retained real gate freezes four compatible units before any sampling."""
    from bp_registry.campaigns.cli import _load_work_plan
    from bp_registry.manifests import preflight as preflight_manifest

    study_path = ROOT / "data/studies/phase8-paired-canonical-gate-v1.json"
    study = json.loads(study_path.read_text(encoding="utf-8"))
    assert set(study) == {"campaign_work_spec"}
    spec = study["campaign_work_spec"]
    assert spec["schema"] == "campaign_work_spec_v1"
    assert spec["coordinates"] == [{
        "cohort_id": "gross-bb-144", "point_id": "p050",
        "sample_namespace": "phase8-paired-bb144-canonical-gate-shared-physical-samples-v1",
        "sample_ids": [0, 1],
    }]
    assert spec["look_sample_boundaries"] == [2]
    assert spec["assessment"]["stopping"] == {"mode": "fixed_shot", "final_shots": 2, "batch_size": 2}
    assert spec["assessment"]["resources"]["max_events"] == 4
    assert spec["assessment"]["targets"][0]["target_id"] == "development_fixture-not_assessed-all-domain"
    assert spec["source_denominator_required_by_target"] == {"development_fixture-not_assessed-all-domain": False}
    assert spec["source_denominators"] == {"development_fixture-not_assessed-all-domain": None}

    arms = {item["arm_id"]: item for item in spec["arms"]}
    assert set(arms) == {"fast", "slow"}
    manifests = {}
    for arm_id, arm in arms.items():
        path = ROOT / arm["manifest_path"]
        assert sha256(path.read_bytes()).hexdigest() == arm["manifest_sha256"]
        manifests[arm_id] = preflight_manifest(path).manifest
        assert manifests[arm_id].budgets.max_shots == 2
        assert manifests[arm_id].randomness.decoder_seed_identity == arm["decoder_seed_identity"]
    assert manifests["fast"].randomness.decoder_seed_identity != manifests["slow"].randomness.decoder_seed_identity
    assert manifests["fast"].error_rate == manifests["slow"].error_rate == 0.05
    assert manifests["fast"].randomness.sample_seed == manifests["slow"].randomness.sample_seed == 317
    assert manifests["fast"].randomness.physical_sample_identity == manifests["slow"].randomness.physical_sample_identity
    assert manifests["fast"].randomness.sample_derivation == manifests["slow"].randomness.sample_derivation
    assert manifests["fast"].artifact.model_dump(mode="json") == manifests["slow"].artifact.model_dump(mode="json")

    preflight_root = tmp_path / "preflight-must-not-write"
    checked = _run_campaign_module(
        "preflight", "--campaign", str(study_path), "--campaign-root", str(ROOT),
        "--output-root", str(preflight_root),
    )
    assert checked.returncode == 0, checked.stdout
    response = json.loads(checked.stdout)
    assert response["sampling_performed"] is False
    assert response["campaign_plan_digest"]
    assert not preflight_root.exists()

    work_plan_path = ROOT / "data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json"
    _loaded_spec, work_plan, payload = _load_work_plan(str(work_plan_path), ROOT)
    assert payload["campaign_spec_digest"] == response["campaign_spec_digest"]
    assert len(work_plan.units) == 4 and len(work_plan.shards) == 2
    assert {(unit.sample_id, unit.arm_id) for unit in work_plan.units} == {
        (0, "fast"), (0, "slow"), (1, "fast"), (1, "slow"),
    }

    documentation = (ROOT / "docs/campaigns.md").read_text(encoding="utf-8")
    for verb in ("preflight", "plan", "run-local", "emit-slurm", "run-shard", "verify", "merge", "resume", "assess", "verify-routes"):
        assert f"bp-registry-campaign {verb}" in documentation
    assert "canonical event ledger fields and sampler-derived identity do not change" in documentation
    assert "campaign attempt receipt binds each immutable" in documentation
    assert "No real scheduler submission is authorized without measured site ceilings" in documentation
    assert "phase8-bb144-fast.json` / `phase8-bb144-slow.json" in documentation
    assert "different rates (`0.05` and `0.03`)" in documentation
    assert "never described as matched decoder evidence" in documentation


def test_retained_paired_canonical_gate_verifies(tmp_path: Path) -> None:
    """Replay both retained real routes and their shared physical sample bytes."""
    root = ROOT / "data/results/phase8-paired-canonical-gate-v1"
    plan = root / "campaign-work-plan.json"
    routes = (
        (root / "local" / "campaign-paired-merge.json", root / "assessment.json"),
        (root / "slurm-route" / "campaign-paired-merge.json", root / "slurm-route" / "assessment.json"),
    )
    samples: dict[int, bytes] = {}
    for merge_path, report_path in routes:
        checked = _run_installed_campaign(
            "verify", "--report", str(report_path), "--plan", str(plan),
            "--merge", str(merge_path), "--campaign-root", str(ROOT),
        )
        assert checked.returncode == 0, checked.stdout
        assert json.loads(checked.stdout)["verified"] is True
        merge = json.loads(merge_path.read_text(encoding="utf-8"))
        assert len(merge["verified_attempts"]) == 4
        for attempt in merge["verified_attempts"]:
            sample_id = json.loads(Path(attempt["materialized_sample_path"]).read_text())["sample_id"]
            material = Path(attempt["materialized_sample_path"]).read_bytes()
            assert samples.setdefault(sample_id, material) == material
            assert len(attempt["canonical_ledger_sha256"]) == 64
            assert len(attempt["physical_error_sha256"]) == 64
            assert attempt["terminal_fact"]["outcome"] == "nonconvergence"
            canonical_terminal = json.loads(Path(attempt["canonical_ledger_path"]).read_text().splitlines()[-1])
            assert canonical_terminal["data"]["outcome"] is None
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["merge_receipt_sha256"] == merge["canonical_merge"]["receipt_sha256"]
        point = report["point_reports"][0]
        assert point["planned_samples"] == 4 and point["terminal_samples"] == 4
        assert {item["arm_id"] for item in point["outcome_denominator_summaries"]} == {"fast", "slow"}
        assert all(item["acceptance_probability"]["denominator"] == 2 for item in point["outcome_denominator_summaries"])
        assert all(item["conditional_performance"] is None and item["conditional_unavailable_reason"] == "zero accepted samples"
                   for item in point["outcome_denominator_summaries"])
        assert point["work_and_resources"]["work_vectors"]
        assert point["outcome_treatment_table"]
    assert set(samples) == {0, 1}
    routes_checked = _run_installed_campaign(
        "verify-routes", "--plan", str(plan), "--local-merge", str(routes[0][0]),
        "--local-report", str(routes[0][1]), "--slurm-merge", str(routes[1][0]),
        "--slurm-report", str(routes[1][1]), "--campaign-root", str(ROOT),
        "--output", str(tmp_path / "route-check.json"),
    )
    assert routes_checked.returncode == 0, routes_checked.stdout
    assert json.loads(routes_checked.stdout)["scientific_records_match"] is True


def test_retained_paired_canonical_gate_rejects_tampering(tmp_path: Path) -> None:
    """Changed labels, sample bytes, and ledger bytes fail attempt replay."""
    from bp_registry.campaigns.cli import _load_work_plan
    from bp_registry.campaigns.execution import verify_canonical_attempt

    root = ROOT / "data/results/phase8-paired-canonical-gate-v1"
    _spec, plan, _payload = _load_work_plan(str(root / "campaign-work-plan.json"), ROOT)
    merge = json.loads((root / "local" / "campaign-paired-merge.json").read_text())
    original = merge["verified_attempts"][0]
    for field, value in (("unit_key", "wrong-unit"), ("physical_error_sha256", "0" * 64)):
        changed = {**original, field: value}
        with pytest.raises(ValueError):
            verify_canonical_attempt(record=changed, plan=plan)
    for field, source in (("materialized_sample_path", "materialized_sample_path"),
                          ("canonical_ledger_path", "canonical_ledger_path")):
        copied = tmp_path / Path(original[source]).name
        copied.write_bytes(Path(original[source]).read_bytes() + b" ")
        with pytest.raises(ValueError):
            verify_canonical_attempt(record={**original, field: str(copied)}, plan=plan)
    extra_receipt = root / "slurm-route" / "shard-0" / "paired-shard-run.json"
    altered_merge = dict(merge)
    altered_merge["attempt_artifacts"] = sorted(
        [*merge["attempt_artifacts"], {"path": str(extra_receipt),
                                     "sha256": sha256(extra_receipt.read_bytes()).hexdigest()}],
        key=lambda item: (item["path"], item["sha256"]),
    )
    altered_path = tmp_path / "unrelated-indexed-delivery.json"
    altered_path.write_text(json.dumps(altered_merge, sort_keys=True), encoding="utf-8")
    rejected = _run_installed_campaign(
        "verify", "--report", str(root / "assessment.json"),
        "--plan", str(root / "campaign-work-plan.json"),
        "--merge", str(altered_path), "--campaign-root", str(ROOT),
    )
    assert rejected.returncode != 0
    assert "attempts differ from indexed run receipts" in json.loads(rejected.stdout)["error"]


def test_operational_fixture_recovers_a_post_decision_crash_without_next_look(tmp_path: Path):
    """The bounded gate retains its stop-receipt recovery proof on disk."""
    study = ROOT / "data/studies/phase8-operational-gate-v1.json"
    output_root = tmp_path / "operational-fixture"
    completed = _run_campaign_module(
        "operational-fixture", "--campaign", str(study), "--campaign-root", str(ROOT),
        "--output-root", str(output_root),
    )

    assert completed.returncode == 0, completed.stdout
    response = json.loads(completed.stdout)
    assert response["recovered_stop_receipt"] is True
    receipt = json.loads((output_root / "finite-look-recovery.json").read_text(encoding="utf-8"))
    assert receipt["next_look_submissions"] == 0
    assert receipt["pre_crash_receipt_sha256s"] == receipt["post_crash_receipt_sha256s"]
    assert receipt["authorized_undispatched_keys"]


def test_operational_gate_verify_requires_retained_bounded_evidence() -> None:
    """The public Phase 8 verification entry point proves the retained gate."""
    result_root = ROOT / "data/results/phase8-operational-gate-v1"
    completed = _run_campaign_module(
        "verify", "--campaign", str(ROOT / "data/studies/phase8-operational-gate-v1.json"),
        "--campaign-root", str(ROOT), "--output", str(result_root),
    )

    assert completed.returncode == 0, completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["verified"] is True
    assert payload["production_authorization"] == "deny"
    assert payload["next_look_submissions"] == 0


def test_cli_lifecycle_uses_preserved_receipts_and_rejects_plan_drift(tmp_path: Path):
    """One bounded manifest reaches each lifecycle stage without mutable inputs."""
    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    planned_root = tmp_path / "planned"
    planned = _run_campaign_module(
        "plan", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(planned_root),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = planned_root / "campaign-plan.json"

    local = _run_campaign_module(
        "run-local", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "local"),
    )
    assert local.returncode == 0, local.stdout
    local_payload = json.loads(local.stdout)
    assert local_payload["executor_route"] == "local"

    verified = _run_campaign_module(
        "verify", "--receipt", local_payload["receipt_path"], "--campaign-root", str(ROOT),
    )
    assert verified.returncode == 0, verified.stdout
    assert json.loads(verified.stdout)["verified"] is True

    merged_root = tmp_path / "merged"
    merged = _run_campaign_module(
        "merge", "--receipt", local_payload["receipt_path"], "--campaign-root", str(ROOT),
        "--output-root", str(merged_root),
    )
    assert merged.returncode == 0, merged.stdout
    merge_path = merged_root / "campaign-merge.json"

    resumed = _run_campaign_module(
        "resume", "--plan", str(plan_path), "--merge", str(merge_path),
        "--campaign-root", str(ROOT),
    )
    assert resumed.returncode == 0, resumed.stdout
    assert json.loads(resumed.stdout)["exact_missing_set"] == []

    assessed = _run_campaign_module(
        "assess", "--merge", str(merge_path), "--campaign-root", str(ROOT),
    )
    assert assessed.returncode == 0, assessed.stdout
    assert json.loads(assessed.stdout)["assessment_status"] == "evidence_reconstructed"

    tampered = json.loads(merge_path.read_text(encoding="utf-8"))
    tampered["members"][0]["report"]["failures"] = 0
    tampered_path = tmp_path / "tampered-merge.json"
    tampered_path.write_text(json.dumps(tampered, sort_keys=True) + "\n", encoding="utf-8")
    rejected_resume = _run_campaign_module(
        "resume", "--plan", str(plan_path), "--merge", str(tampered_path),
        "--campaign-root", str(ROOT),
    )
    rejected_assess = _run_campaign_module(
        "assess", "--merge", str(tampered_path), "--campaign-root", str(ROOT),
    )
    assert rejected_resume.returncode != 0
    assert rejected_assess.returncode != 0
    assert "canonical reconstruction" in json.loads(rejected_assess.stdout)["error"]

    # Valid JSON with different raw bytes must also be rejected: consumers
    # rehash the retained receipt rather than trusting its merge counter.
    receipt_path = Path(json.loads(local.stdout)["receipt_path"])
    receipt_path.write_bytes(receipt_path.read_bytes() + b"\n")
    receipt_changed = _run_campaign_module(
        "resume", "--plan", str(plan_path), "--merge", str(merge_path),
        "--campaign-root", str(ROOT),
    )
    assert receipt_changed.returncode != 0
    assert "canonical reconstruction" in json.loads(receipt_changed.stdout)["error"]

    drifted = json.loads(plan_path.read_text(encoding="utf-8"))
    drifted["campaign_plan_digest"] = "0" * 64
    drifted_path = tmp_path / "drifted-plan.json"
    drifted_path.write_text(json.dumps(drifted), encoding="utf-8")
    rejected_root = tmp_path / "must-not-exist"
    rejected = _run_campaign_module(
        "run-local", "--plan", str(drifted_path), "--campaign-root", str(ROOT),
        "--output-root", str(rejected_root),
    )
    assert rejected.returncode != 0
    assert json.loads(rejected.stdout)["status"] == "error"
    assert not rejected_root.exists()


def test_one_unit_cli_uses_frozen_confidence_and_refuses_multi_shot_assessment(tmp_path: Path):
    """A tracer uses its frozen confidence level and cannot complete more shots."""
    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    document = json.loads(campaign.read_text(encoding="utf-8"))
    assessment = document["campaign_spec"]["assessment"]
    assessment["interval"]["confidence_level"] = 0.9
    campaign.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    plan_root = tmp_path / "one-shot-planned"
    planned = _run_campaign_module(
        "plan", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(plan_root),
    )
    assert planned.returncode == 0, planned.stdout
    local = _run_campaign_module(
        "run-local", "--plan", str(plan_root / "campaign-plan.json"),
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "one-shot-local"),
    )
    assert local.returncode == 0, local.stdout
    verified = _run_campaign_module(
        "verify", "--receipt", json.loads(local.stdout)["receipt_path"],
        "--campaign-root", str(ROOT),
    )
    assert verified.returncode == 0, verified.stdout
    assert json.loads(verified.stdout)["report"]["interval"]["confidence_level"] == 0.9

    assessment["stopping"] = {"mode": "fixed_shot", "final_shots": 2, "batch_size": 1}
    assessment["resources"]["max_shots"] = 2
    campaign.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    plan_root = tmp_path / "planned"
    planned = _run_campaign_module(
        "plan", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(plan_root),
    )
    assert planned.returncode == 0, planned.stdout
    local = _run_campaign_module(
        "run-local", "--plan", str(plan_root / "campaign-plan.json"),
        "--campaign-root", str(ROOT), "--output-root", str(tmp_path / "local"),
    )
    assert local.returncode == 0, local.stdout
    rejected = _run_campaign_module(
        "verify", "--receipt", json.loads(local.stdout)["receipt_path"],
        "--campaign-root", str(ROOT),
    )
    assert rejected.returncode != 0
    assert "final_shots other than one" in json.loads(rejected.stdout)["error"]


def test_cli_scheduler_route_emits_literal_argv_and_executes_one_frozen_shard(tmp_path: Path):
    """The scheduler path selects task zero from exactly the planned campaign."""
    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    plan_root = tmp_path / "planned"
    assert _run_campaign_module(
        "plan", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(plan_root),
    ).returncode == 0
    allocation = tmp_path / "allocation.json"
    allocation.write_text(json.dumps({
        "partition": "research", "qos": "short", "account": "bp", "wall_minutes": 10,
        "memory_mb": 256, "cpus_per_task": 1, "max_concurrent_tasks": 1,
    }), encoding="utf-8")
    allowlists = tmp_path / "allowlists.json"
    allowlists.write_text(json.dumps({"partition": ["research"], "qos": ["short"], "account": ["bp"]}), encoding="utf-8")
    plan_path = plan_root / "campaign-plan.json"
    emitted = _run_campaign_module(
        "emit-slurm", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--allocation", str(allocation), "--site-allowlists", str(allowlists),
    )
    assert emitted.returncode == 0, emitted.stdout
    assert json.loads(emitted.stdout)["sbatch_argv"][:2] == ["sbatch", "--array=0-0%1"]

    shard = _run_campaign_module(
        "run-shard", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "shard"), "--array-task-id", "0",
    )
    assert shard.returncode == 0, shard.stdout
    assert json.loads(shard.stdout)["executor_route"] == "slurm"
    malformed = _run_campaign_module(
        "run-shard", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "invalid-task"), "--array-task-id", "1;touch",
    )
    assert malformed.returncode != 0
    assert not (tmp_path / "invalid-task").exists()


def test_installed_cli_exposes_lifecycle_help_and_preserves_route_science(tmp_path: Path):
    """The installed command has every lifecycle verb and route-neutral science."""
    help_result = _run_installed_campaign("--help")
    assert help_result.returncode == 0, help_result.stderr
    for command in ("preflight", "plan", "run-local", "run-shard", "emit-slurm", "merge", "resume", "assess", "verify", "profile-gate", "site-capability"):
        assert command in help_result.stdout

    campaign = _write_cli_campaign(tmp_path / "campaign.json")
    plan_root = tmp_path / "planned"
    planned = _run_installed_campaign(
        "plan", "--campaign", str(campaign), "--campaign-root", str(ROOT),
        "--output-root", str(plan_root),
    )
    assert planned.returncode == 0, planned.stdout
    plan_path = plan_root / "campaign-plan.json"
    local = _run_installed_campaign(
        "run-local", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "local"),
    )
    shard = _run_installed_campaign(
        "run-shard", "--plan", str(plan_path), "--campaign-root", str(ROOT),
        "--output-root", str(tmp_path / "slurm"), "--array-task-id", "0",
    )
    assert local.returncode == shard.returncode == 0
    local_payload, shard_payload = json.loads(local.stdout), json.loads(shard.stdout)
    assert local_payload["terminal_fact"] == shard_payload["terminal_fact"]
    assert local_payload["unit_key"] == shard_payload["unit_key"]
    assert local_payload["executor_route"] != shard_payload["executor_route"]
