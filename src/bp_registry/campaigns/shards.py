"""Immutable campaign-shard publication, validation, and one-look reduction."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping

from scipy.stats import binomtest

from ..canonical.verification import validate_canonical_shot
from ..ledger import read_canonical_events_bytes
from ..runner import canonical_public_shot_context
from .contracts import CampaignSpecV1, build_one_unit_plan, canonical_json_bytes


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_sealed_shard(*, staging: Path, destination: Path) -> None:
    """Atomically publish a fully fsynced private shard on its destination FS."""
    for path in staging.iterdir():
        if path.is_file():
            _fsync_file(path)
    _fsync_directory(staging)
    os.replace(staging, destination)
    _fsync_directory(destination.parent)


def _read_regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("sealed shard files must be regular non-symlink files")
    return path.read_bytes()


def _resolve_manifest(campaign_root: Path, spec: CampaignSpecV1) -> Path:
    root = campaign_root.resolve(strict=True)
    path = root
    for part in Path(spec.inner_manifest_path).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("inner manifest may not be a symlink")
    resolved = path.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise ValueError("inner manifest escapes campaign root")
    if sha256(_read_regular_bytes(path)).hexdigest() != spec.inner_manifest_sha256:
        raise ValueError("inner manifest digest differs from frozen campaign specification")
    return path


def _terminal_fact(events: list[dict[str, Any]], *, unit_key: str) -> dict[str, Any]:
    terminal = next(event for event in events if event["kind"] == "termination")
    outcome = terminal["data"].get("outcome")
    logical_failure = outcome not in {"exact", "stabilizer_equivalent"}
    return {
        "unit_key": unit_key,
        "termination": terminal["termination"],
        "outcome": outcome,
        "logical_failure": logical_failure,
    }


def seal_receipt(*, path: Path, receipt: Mapping[str, Any]) -> None:
    """Write compact receipt bytes once; callers publish its directory atomically."""
    payload = canonical_json_bytes(dict(receipt)) + b"\n"
    path.write_bytes(payload)
    _fsync_file(path)


def verify_shard(receipt_path: str | Path, *, campaign_root: str | Path) -> dict[str, Any]:
    """Revalidate one sealed byte snapshot before reporting any terminal outcome."""
    receipt_file = Path(receipt_path)
    receipt_bytes = _read_regular_bytes(receipt_file)
    try:
        receipt = json.loads(receipt_bytes)
    except json.JSONDecodeError as error:
        raise ValueError("sealed shard receipt is not JSON") from error
    if not isinstance(receipt, dict) or receipt.get("schema") != "campaign_shard_receipt_v1":
        raise ValueError("unsupported shard receipt")
    spec = CampaignSpecV1.model_validate(receipt.get("campaign_spec"))
    manifest = _resolve_manifest(Path(campaign_root), spec)
    plan = build_one_unit_plan(spec)
    expected = {
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "unit_key": plan.unit_key,
        "shard_id": plan.shard_id,
        "physical_sample_identity": plan.physical_sample_identity,
        "decoder_randomness_identity": plan.decoder_randomness_identity,
    }
    if any(receipt.get(name) != value for name, value in expected.items()):
        raise ValueError("sealed shard receipt differs from the frozen campaign plan")
    ledger = _read_regular_bytes(receipt_file.parent / "events.jsonl")
    if len(ledger) != receipt.get("ledger_bytes") or sha256(ledger).hexdigest() != receipt.get("ledger_sha256"):
        raise ValueError("sealed shard ledger receipt mismatch")
    if len(ledger) > spec.max_evidence_bytes:
        raise ValueError("sealed shard exceeds campaign evidence bound")
    events = read_canonical_events_bytes(ledger)
    if len(events) > spec.max_events:
        raise ValueError("sealed shard exceeds campaign event bound")
    context = canonical_public_shot_context(manifest, shot_id=spec.sample_id)
    validate_canonical_shot(events, context)
    if context.decoder_seed_identity != spec.decoder_seed_identity:
        raise ValueError("inner manifest decoder randomness differs from campaign specification")
    manifest_namespace = context.manifest_sha256
    from ..manifests import preflight
    parsed = preflight(manifest).manifest
    manifest_namespace = parsed.randomness.physical_sample_identity or manifest_namespace
    if manifest_namespace != spec.sample_namespace:
        raise ValueError("inner manifest physical sample namespace differs from campaign specification")
    terminal_fact = _terminal_fact(events, unit_key=receipt["unit_key"])
    if receipt.get("terminal_fact") != terminal_fact:
        raise ValueError("sealed shard terminal fact differs from immutable ledger")
    return {**receipt, "events": events, "terminal_fact": terminal_fact}


def reconstruct_fixed_shot(verified_shard: Mapping[str, Any]) -> dict[str, Any]:
    """Compute the declared one-look all-shot rate from a verified terminal only."""
    terminal = verified_shard.get("terminal_fact")
    if not isinstance(terminal, Mapping) or not isinstance(terminal.get("logical_failure"), bool):
        raise ValueError("verified shard has no all-shot terminal outcome")
    failures, completed = int(terminal["logical_failure"]), 1
    interval = binomtest(failures, completed).proportion_ci(confidence_level=0.95, method="exact")
    return {
        "campaign_spec_digest": verified_shard["campaign_spec_digest"],
        "campaign_plan_digest": verified_shard["campaign_plan_digest"],
        "completed": completed,
        "failures": failures,
        "estimate": failures / completed,
        "interval": {
            "method": "exact",
            "confidence_level": 0.95,
            "lower": float(interval.low),
            "upper": float(interval.high),
        },
        "status": "fixed_shot_complete",
    }
