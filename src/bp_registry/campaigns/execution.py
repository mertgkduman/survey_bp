"""Local execution of one frozen campaign unit through the existing runner."""

from __future__ import annotations

from hashlib import sha256
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..runner import canonical_public_shot_context, run_canonical_one
from .contracts import CampaignSpecV1, build_one_unit_plan
from .shards import _resolve_manifest, _terminal_fact, publish_sealed_shard, seal_receipt


def run_one_unit(
    spec: CampaignSpecV1,
    *,
    campaign_root: str | Path,
    output_root: str | Path,
    worker_label: str,
) -> dict[str, Any]:
    """Run exactly the frozen unit; worker_label is retained only as observation."""
    if not isinstance(worker_label, str) or not worker_label:
        raise ValueError("worker_label must be a nonempty observational label")
    plan = build_one_unit_plan(spec)
    root = Path(campaign_root)
    manifest = _resolve_manifest(root, spec)
    context = canonical_public_shot_context(manifest, shot_id=spec.sample_id)
    if context.decoder_seed_identity != spec.decoder_seed_identity:
        raise ValueError("inner manifest decoder randomness differs from campaign specification")
    destination_root = Path(output_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / f"shard-{plan.shard_id}"
    if destination.exists():
        raise ValueError("sealed campaign shard already exists and cannot be reopened")
    staging = Path(tempfile.mkdtemp(prefix=".campaign-stage-", dir=destination_root))
    try:
        ledger_path = staging / "events.jsonl"
        run_canonical_one(manifest, shot_id=spec.sample_id, ledger_path=ledger_path)
        ledger = ledger_path.read_bytes()
        from ..ledger import read_canonical_events_bytes
        events = read_canonical_events_bytes(ledger)
        terminal_fact = _terminal_fact(events, unit_key=plan.unit_key)
        receipt = {
            "schema": "campaign_shard_receipt_v1",
            "campaign_spec": spec.model_dump(mode="json", by_alias=True),
            "campaign_spec_digest": plan.campaign_spec_digest,
            "campaign_plan_digest": plan.campaign_plan_digest,
            "unit_key": plan.unit_key,
            "shard_id": plan.shard_id,
            "physical_sample_identity": plan.physical_sample_identity,
            "canonical_sample_identity": context.sample_seed_identity,
            "decoder_randomness_identity": plan.decoder_randomness_identity,
            "ledger_sha256": sha256(ledger).hexdigest(),
            "ledger_bytes": len(ledger),
            "terminal_fact": terminal_fact,
            "executor_observation": {"worker_label": worker_label},
        }
        receipt_path = staging / "receipt.json"
        seal_receipt(path=receipt_path, receipt=receipt)
        publish_sealed_shard(staging=staging, destination=destination)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    receipt_path = destination / "receipt.json"
    return {
        **receipt,
        "receipt_path": str(receipt_path),
        "campaign_spec_bytes": plan.campaign_spec_bytes,
        "campaign_plan_preimage": plan.campaign_plan_preimage,
    }
