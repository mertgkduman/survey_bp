"""Lifecycle coverage for ordered, failure-count stopped local campaigns."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from bp_registry.campaigns.contracts import FailureCountStoppingV1
from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan


def _plan(shots: int = 10):
    return freeze_work_plan(
        campaign_spec_digest="a" * 64,
        coordinates=(CampaignCoordinateV1(
            cohort_id="failure", point_id="p010", sample_namespace="ordered-v1",
            sample_ids=tuple(range(shots)),
        ),),
        arm_seed_identities={"bp": "deterministic-v1"},
        look_sample_boundaries=(shots,), units_per_shard=5,
    )


def _stopping(target: int = 3, batch: int = 5) -> FailureCountStoppingV1:
    # The terminal fields are replaced by the controller's sealed observation.
    return FailureCountStoppingV1(
        mode="failure_count", target_failures=target, batch_size=batch,
        shot_order="campaign_cohort_point_sample_ordinal_v1",
        failure_event="decoder_logical_failure_v1",
        terminal_batch_authorization_sha256="b" * 64,
        cap_authorization_sha256="c" * 64,
        terminal_state="cap_censored", cumulative_failures_at_terminal=0,
    )


_FAILURES: set[int] = set()
_RUNS: list[int] = []


def _runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    del staging
    ordinal = int(unit["sample_id"]) + 1
    _RUNS.append(ordinal)
    failure = ordinal in _FAILURES
    return {
        "terminal_fact": {
            "unit_key": unit["unit_key"], "termination": "converged",
            "outcome": "wrong_logical_action" if failure else "exact",
            "logical_failure": failure,
        },
        "work_vector": {"bp_calls": 1},
        "persisted_sample_bytes": f"sample:{unit['physical_sample_identity']}".encode("ascii"),
    }


@pytest.mark.parametrize(
    ("failures", "expected_terminal", "expected_tail"),
    (
        ({1, 2, 6}, 6, (7, 8, 9, 10)),
        ({1, 2, 8}, 8, (9, 10)),
        ({1, 2, 10}, 10, ()),
    ),
)
def test_tracer_ordered_stop_seals_exact_prefix_and_terminal_batch_tail(
    tmp_path: Path, failures: set[int], expected_terminal: int, expected_tail: tuple[int, ...],
) -> None:
    from bp_registry.campaigns.execution import dispatch_failure_count_batches, verify_failure_count_receipt

    global _FAILURES, _RUNS
    _FAILURES, _RUNS = failures, []
    result = dispatch_failure_count_batches(
        _plan(), output_root=tmp_path, workers=1, unit_runner=_runner, stopping=_stopping(),
    )

    receipt = result["receipt"]
    assert receipt["terminal_state"] == "target_reached"
    assert receipt["terminal_failure_ordinal"] == expected_terminal
    assert tuple(receipt["authorized_tail_ordinals"]) == expected_tail
    assert receipt["inferential_prefix_count"] == expected_terminal
    assert receipt["total_completed_shots"] == 10
    assert _RUNS == list(range(1, 11))
    assert verify_failure_count_receipt(plan=_plan(), output_root=tmp_path) == receipt


def test_censor_is_inconclusive_and_resume_rebuilds_missing_stop_without_rerun(tmp_path: Path) -> None:
    from bp_registry.campaigns.execution import dispatch_failure_count_batches, verify_failure_count_receipt

    global _FAILURES, _RUNS
    _FAILURES, _RUNS = {2, 4}, []
    with pytest.raises(InterruptedError, match="after terminal merge"):
        dispatch_failure_count_batches(
            _plan(), output_root=tmp_path / "recovery", workers=1, unit_runner=_runner,
            stopping=_stopping(), fault_after_terminal_merge=True,
        )
    before = list(_RUNS)
    recovered = dispatch_failure_count_batches(
        _plan(), output_root=tmp_path / "recovery", workers=1, unit_runner=_runner, stopping=_stopping(),
    )
    assert recovered["recovered_receipt"] is True
    assert _RUNS == before
    assert verify_failure_count_receipt(plan=_plan(), output_root=tmp_path / "recovery") == recovered["receipt"]

    _FAILURES, _RUNS = {1, 2}, []
    censored = dispatch_failure_count_batches(
        _plan(), output_root=tmp_path / "censored", workers=1, unit_runner=_runner,
        stopping=_stopping(), max_shots=5,
    )["receipt"]
    assert censored["terminal_state"] == "cap_censored"
    assert censored["assessment_status"] == "inconclusive_cap_censored"
    assert "verdict" not in censored
    assert censored["total_completed_shots"] == 5


def test_replay_rejects_tampered_order_tail_or_resource_receipt(tmp_path: Path) -> None:
    from bp_registry.campaigns.execution import dispatch_failure_count_batches, verify_failure_count_receipt

    global _FAILURES, _RUNS
    _FAILURES, _RUNS = {1, 2, 8}, []
    dispatch_failure_count_batches(
        _plan(), output_root=tmp_path, workers=1, unit_runner=_runner, stopping=_stopping(),
    )
    receipt_path = tmp_path / "failure-count-receipt.json"
    raw = receipt_path.read_bytes()
    receipt_path.write_bytes(raw.replace(b'"total_completed_shots":10', b'"total_completed_shots":9'))
    with pytest.raises(ValueError, match="differs from sealed evidence"):
        verify_failure_count_receipt(plan=_plan(), output_root=tmp_path)
    receipt_path.write_bytes(raw)
    assert sha256(raw).hexdigest()
