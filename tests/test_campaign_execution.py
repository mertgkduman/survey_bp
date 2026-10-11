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
        verify_persisted_sample(receipt, artifact + b"!")
