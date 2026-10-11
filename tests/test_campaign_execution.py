"""One-unit tracer coverage for the immutable campaign boundary."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path


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
    return {
        "schema": "campaign_spec_v1",
        "inner_manifest_path": INNER_MANIFEST,
        "inner_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "source_lock_sha256": "1" * 64,
        "environment_lock_sha256": "2" * 64,
        "cohort_id": "tracer",
        "point_id": "p100",
        "sample_namespace": sha256(manifest_bytes).hexdigest(),
        "sample_id": 0,
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
    assert "campaign_plan_digest" not in first["campaign_spec_bytes"]
    assert "campaign_plan_digest" not in first["campaign_plan_preimage"]

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
    assert "campaign_plan_digest" not in original_plan.campaign_spec_bytes
    assert "campaign_plan_digest" not in original_plan.campaign_plan_preimage
