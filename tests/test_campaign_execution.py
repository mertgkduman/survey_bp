"""One-unit tracer coverage for the immutable campaign boundary."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path

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
