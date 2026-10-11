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


def test_merge_rejects_different_persisted_sample_hashes_across_arms() -> None:
    from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan
    from bp_registry.campaigns.shards import merge_verified_attempts

    plan = freeze_work_plan(
        campaign_spec_digest="b" * 64,
        coordinates=(CampaignCoordinateV1(
            cohort_id="cohort", point_id="point", sample_namespace="samples", sample_ids=(0,),
        ),),
        arm_seed_identities={"fast": "seed-fast", "slow": "seed-slow"},
        look_sample_boundaries=(1,), units_per_shard=1,
    )
    records = []
    for index, unit in enumerate(plan.units):
        record = _verified_attempt(
            unit_key=unit.key, plan_digest=plan.campaign_plan_digest,
            attempt_id=f"arm-{index}", state="sealed_terminal", terminal="exact",
        )
        record["persisted_sample_sha256"] = sha256(f"sample-{index}".encode()).hexdigest()
        records.append(record)
    with pytest.raises(ValueError, match="matched arms"):
        merge_verified_attempts(plan=plan, verified_attempts=records)


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


def test_merge_records_byte_identical_terminal_retries_without_double_counting() -> None:
    from bp_registry.campaigns.shards import merge_verified_attempts

    plan = _work_plan()
    first, second = plan.unit_keys
    interrupted = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="a", state="sealed_interrupted",
    )
    retry_a = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="b", state="sealed_terminal",
        terminal="exact", parent="a",
    )
    retry_b = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="c", state="sealed_terminal",
        terminal="exact", parent="a",
    )
    merged = merge_verified_attempts(plan=plan, verified_attempts=(retry_b, interrupted, retry_a))
    assert merged["terminal_unit_keys"] == [first]
    assert merged["redundant_attempt_receipt_hashes"] == [max(retry_a["receipt_sha256"], retry_b["receipt_sha256"])]
    assert merged["missing_unit_keys"] == [second]


def _resume_identity(plan, *, source: str = "1" * 64, environment: str = "2" * 64,
                     dependency: str = "3" * 64) -> dict[str, str]:
    """Frozen facts that must match before any prior evidence is reusable."""
    return {
        "campaign_spec_digest": plan.campaign_spec_digest,
        "campaign_plan_digest": plan.campaign_plan_digest,
        "source_lock_sha256": source,
        "environment_lock_sha256": environment,
        "dependency_lock_sha256": dependency,
        "sample_namespace_digest": "4" * 64,
        "stopping_rule_digest": "5" * 64,
        "assessment_digest": "6" * 64,
    }


def _stopping_decision(*, look: int, terminal_records: tuple[dict[str, object], ...]) -> dict[str, object]:
    assert look == 1
    assert len(terminal_records) == 1
    return {
        "decision_input_hashes": ["7" * 64],
        "decision_result": {"status": "pass"},
        "stop_reason": "all_primary_decisions_resolved",
        "should_stop": True,
    }


def test_resume_recovers_stop_receipt_before_set_subtraction_without_mutating_evidence() -> None:
    """The post-decision/pre-publication crash cannot dispatch the next look."""
    from bp_registry.campaigns.shards import derive_resume_plan

    plan = _work_plan()
    first, second = plan.unit_keys
    completed = _verified_attempt(
        unit_key=first, plan_digest=plan.campaign_plan_digest, attempt_id="a",
        state="sealed_terminal", terminal="exact",
    )
    original = (completed["receipt_sha256"], completed["terminal_bytes_sha256"])
    resumed = derive_resume_plan(
        plan=plan, verified_attempts=(completed,), scientific_identity=_resume_identity(plan),
        decision_for_look=_stopping_decision,
    )
    assert resumed["recovered_look_stop_receipts"]
    assert resumed["authorized_undispatched_keys"] == [second]
    assert resumed["resumable_unit_keys"] == []
    assert resumed["attempt_plans"] == []
    assert (completed["receipt_sha256"], completed["terminal_bytes_sha256"]) == original


def test_resume_rejects_scientific_drift_but_not_executor_observation() -> None:
    """Allocation can move; every frozen scientific or dependency fact cannot."""
    from bp_registry.campaigns.shards import derive_resume_plan

    plan = _work_plan()
    identity = _resume_identity(plan)
    with pytest.raises(ValueError, match="identity"):
        derive_resume_plan(
            plan=plan, verified_attempts=(), scientific_identity={**identity, "source_lock_sha256": "a" * 64},
            prior_scientific_identity=identity, decision_for_look=_stopping_decision,
        )
    accepted = derive_resume_plan(
        plan=plan, verified_attempts=(), scientific_identity=identity,
        prior_scientific_identity=identity,
        executor_allocation={"worker_count": 1},
        prior_executor_allocation={"worker_count": 32},
        decision_for_look=_stopping_decision,
    )
    assert accepted["resumable_unit_keys"] == list(plan.unit_keys)


def test_resume_rejects_stop_receipt_for_an_undeclared_partial_look() -> None:
    """A forged future receipt cannot turn incomplete work into an authorized tail."""
    from bp_registry.campaigns.shards import derive_resume_plan

    plan = _work_plan()
    forged = {
        "schema": "campaign_look_stop_receipt_v1", "campaign_plan_digest": plan.campaign_plan_digest,
        "completed_look": 2, "decision_input_hashes": ["c" * 64], "decision_result": {"status": "pass"},
        "stop_reason": "all_primary_decisions_resolved", "realized_count": 0, "overshoot_count": 0,
        "authorized_undispatched": [],
    }
    with pytest.raises(ValueError, match="stop receipt|undeclared|complete"):
        derive_resume_plan(
            plan=plan, verified_attempts=(), scientific_identity=_resume_identity(plan),
            look_stop_receipts=(forged,), decision_for_look=_stopping_decision,
        )
