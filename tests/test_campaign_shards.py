"""Adversarial contracts for immutable campaign shard evidence."""

from __future__ import annotations

from hashlib import sha256
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


def _work_plan():
    from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan

    return freeze_work_plan(
        campaign_spec_digest="b" * 64,
        coordinates=(CampaignCoordinateV1(
            cohort_id="cohort", point_id="point", sample_namespace="samples", sample_ids=(0, 1),
        ),),
        arm_seed_identities={"bp": "seed"}, look_sample_boundaries=(1, 2), units_per_shard=1,
    )


def _verified_attempt(*, unit_key: str, plan_digest: str, attempt_id: str, state: str,
                      terminal: str | None = None, parent: str | None = None) -> dict[str, object]:
    attempt = _attempt(attempt_id=attempt_id, state=state, parent=parent)
    attempt["unit_key"] = unit_key
    attempt["campaign_plan_digest"] = plan_digest
    item: dict[str, object] = {
        "attempt": attempt,
        "receipt_sha256": sha256(attempt_id.encode()).hexdigest(),
        "validation_status": "verified",
        "replay_status": "verified",
    }
    if terminal is not None:
        item["terminal_bytes_sha256"] = sha256(terminal.encode()).hexdigest()
        item["terminal_fact"] = {
            "unit_key": unit_key, "termination": "converged", "outcome": terminal,
            "logical_failure": terminal == "failure",
        }
        item["events"] = [{"event_id": f"event-{attempt_id}"}]
    return item


def test_merge_accepts_interrupted_retry_once_and_is_input_order_independent() -> None:
    from bp_registry.campaigns.shards import merge_verified_attempts

    plan = _work_plan()
    first, second = plan.unit_keys
    completed = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="a", state="sealed_terminal", terminal="exact",
    )
    interrupted = _verified_attempt(
        unit_key=second, plan_digest=plan.campaign_plan_digest, attempt_id="b", state="sealed_interrupted",
    )
    retried = _verified_attempt(
        unit_key=second, plan_digest=plan.campaign_plan_digest, attempt_id="c", state="sealed_terminal",
        terminal="failure", parent="b",
    )
    merged = merge_verified_attempts(plan=plan, verified_attempts=(completed, interrupted, retried))
    reordered = merge_verified_attempts(plan=plan, verified_attempts=(retried, completed, interrupted))
    assert merged["terminal_unit_keys"] == list(plan.unit_keys)
    assert merged["missing_unit_keys"] == []
    assert merged["receipt_bytes"] == reordered["receipt_bytes"]


def test_merge_rejects_terminal_conflicts_and_validates_authorized_tail() -> None:
    from bp_registry.campaigns.shards import merge_verified_attempts

    plan = _work_plan()
    first, second = plan.unit_keys
    first_terminal = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="a", state="sealed_terminal", terminal="exact",
    )
    conflicting = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="b", state="sealed_terminal", terminal="failure",
    )
    with pytest.raises(ValueError, match="conflicting"):
        merge_verified_attempts(plan=plan, verified_attempts=(first_terminal, conflicting))

    stop = {
        "schema": "campaign_look_stop_receipt_v1", "campaign_plan_digest": plan.campaign_plan_digest,
        "completed_look": 1, "decision_input_hashes": ["c" * 64], "decision_result": {"status": "pass"},
        "stop_reason": "all_primary_decisions_resolved", "realized_count": 1, "overshoot_count": 0,
        "authorized_undispatched": list(plan.authorized_tail(1)),
    }
    merged = merge_verified_attempts(plan=plan, verified_attempts=(first_terminal,), look_stop_receipt=stop)
    assert merged["authorized_undispatched_keys"] == [second]
    assert merged["missing_unit_keys"] == []

    stop["authorized_undispatched"] = []
    with pytest.raises(ValueError, match="tail"):
        merge_verified_attempts(plan=plan, verified_attempts=(first_terminal,), look_stop_receipt=stop)
