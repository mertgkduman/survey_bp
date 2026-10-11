"""Adversarial contracts for immutable campaign shard evidence."""

from __future__ import annotations

from pathlib import Path

import pytest


def _attempt(*, attempt_id: str, state: str, parent: str | None = None) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": "campaign_attempt_receipt_v1",
        "attempt_id": attempt_id,
        "unit_key": "unit-a",
        "campaign_plan_digest": "a" * 64,
        "lifecycle": ["planned", "running", state],
        "state": state,
    }
    if parent is not None:
        receipt["parent_attempt_receipt"] = parent
    return receipt


def test_seal_rejects_reopening_and_attempt_lineage_is_immutable(tmp_path: Path) -> None:
    """Only a sealed interrupted parent may have one terminal child attempt."""
    from bp_registry.campaigns.shards import publish_sealed_shard, validate_attempt_lineage

    staging = tmp_path / "staging"
    staging.mkdir(mode=0o700)
    (staging / "receipt.json").write_text("{}", encoding="utf-8")
    destination = tmp_path / "shard"
    publish_sealed_shard(staging=staging, destination=destination)
    with pytest.raises(ValueError, match="already exists"):
        publish_sealed_shard(staging=tmp_path / "missing", destination=destination)

    interrupted = _attempt(attempt_id="attempt-1", state="sealed_interrupted")
    terminal = _attempt(
        attempt_id="attempt-2", state="sealed_terminal", parent="attempt-1",
    )
    assert validate_attempt_lineage((interrupted, terminal))["terminal_attempt_ids"] == ("attempt-2",)

    cyclic = _attempt(attempt_id="attempt-1", state="sealed_interrupted", parent="attempt-2")
    with pytest.raises(ValueError, match="cycle|parent"):
        validate_attempt_lineage((cyclic, terminal))


def test_seal_rejects_non_private_or_non_regular_staging_products(tmp_path: Path) -> None:
    from bp_registry.campaigns.shards import publish_sealed_shard

    staging = tmp_path / "staging"
    staging.mkdir(mode=0o755)
    (staging / "receipt.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="private"):
        publish_sealed_shard(staging=staging, destination=tmp_path / "shard")
