"""Lifecycle coverage for ordered, failure-count stopped local campaigns."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
from argparse import Namespace

import pytest

from bp_registry.campaigns.contracts import FailureCountStoppingV1
from bp_registry.campaigns.planning import CampaignCoordinateV1, freeze_work_plan


def _public_fixture(tmp_path: Path, *, shots: int = 1, target_failures: int = 1, batch_size: int = 1) -> tuple[Path, Path]:
    from test_campaign_execution import ROOT, _single_arm_failure_count_work_spec_payload
    from bp_registry.campaigns.contracts import FailureCountWorkSpecV1
    from bp_registry.campaigns.planning import failure_count_plan_binding

    payload = _single_arm_failure_count_work_spec_payload()
    work = payload["campaign_work_spec"]
    policy = payload["policy"]
    work["coordinates"][0]["sample_ids"] = list(range(shots))
    work["look_sample_boundaries"] = [shots]
    work["assessment"]["resources"].update({
        "max_shots": shots, "max_batch_size": batch_size,
        "max_decoder_work": shots * policy["executable_limits"]["derived_work_per_unit"],
        "max_events": shots * policy["executable_limits"]["derived_events_per_unit"],
        "max_evidence_bytes": shots * policy["executable_limits"]["derived_evidence_bytes_per_unit"] + shots * policy["executable_limits"]["partial_receipt_reserve_bytes"],
        "max_storage_bytes": shots * policy["executable_limits"]["derived_storage_bytes_per_unit"] + shots * policy["executable_limits"]["partial_receipt_reserve_bytes"],
    })
    policy.update({"target_failures": target_failures, "batch_size": batch_size})
    policy["caps"].update({
        "max_shots": shots, "max_decoder_work": work["assessment"]["resources"]["max_decoder_work"],
        "max_events": work["assessment"]["resources"]["max_events"],
        "max_evidence_bytes": work["assessment"]["resources"]["max_evidence_bytes"],
        "max_storage_bytes": work["assessment"]["resources"]["max_storage_bytes"],
    })
    policy["batch_authorization"].update({
        "max_shots_per_batch": batch_size,
        "max_work_per_batch": batch_size * policy["executable_limits"]["derived_work_per_unit"],
        "max_events_per_batch": batch_size * policy["executable_limits"]["derived_events_per_unit"],
        "max_evidence_bytes_per_batch": batch_size * policy["executable_limits"]["derived_evidence_bytes_per_unit"] + policy["executable_limits"]["partial_receipt_reserve_bytes"],
        "max_storage_bytes_per_batch": batch_size * policy["executable_limits"]["derived_storage_bytes_per_unit"] + policy["executable_limits"]["partial_receipt_reserve_bytes"],
        "per_unit_timeout_ns": 10_000_000_000,
    })
    work["assessment"]["stopping"] = policy.copy()
    spec = FailureCountWorkSpecV1.model_validate(payload)
    binding = failure_count_plan_binding(spec.campaign_work_spec)
    payload["policy"]["campaign_plan_sha256"] = binding
    payload["campaign_work_spec"]["assessment"]["stopping"]["campaign_plan_sha256"] = binding
    document = tmp_path / "failure-count-campaign.json"
    document.write_text(json.dumps({"failure_count_work_spec": payload}), encoding="utf-8")
    return document, ROOT


def test_public_failure_count_cap_censor_has_no_interval_or_verdict(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path, target_failures=2)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert run["campaign_state"] == "cap_censored"
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[run["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    report = cli._assess(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root), output_root=str(tmp_path / "report")))["report"]
    assert report["terminal_state"] == "cap_censored"
    assert report["assessment_status"] == "inconclusive_cap_censored"
    assert report["terminal_failure_ordinal"] is None
    assert report["inverse_binomial_rate"] is None
    assert report["target_decision"]["verdict"] == "inconclusive"


def test_public_failure_count_resume_runs_only_next_batch(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path, shots=2, target_failures=2)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    first = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert first["campaign_state"] == "progress"
    first_merge = cli._merge(Namespace(plan=plan_path, receipt=[first["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge-first")))["artifact_path"]
    resume = cli._resume(Namespace(plan=plan_path, merge=first_merge, campaign_root=str(root)))
    assert resume["pending_ordinal"] == 2
    assert len(resume["exact_missing_set"]) == 1
    second = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert second["completed_shots"] == 2
    assert second["campaign_state"] in {"target_reached", "cap_censored"}
    assert len(list((tmp_path / "run" / "attempts").glob("*/attempt.json"))) == 2


def test_public_failure_count_authorized_tail_cost_excluded_from_inference(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path, shots=2, target_failures=1, batch_size=2)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert run["campaign_state"] == "target_reached"
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[run["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    report = cli._assess(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root), output_root=str(tmp_path / "report")))["report"]
    assert report["terminal_failure_ordinal"] == 1
    assert report["total_completed_shots"] == 2
    assert report["authorized_tail_ordinals"] == [2]
    assert report["inferential_failures"] == 1
    assert report["inferential_nonfailures"] == 0
    assert report["inverse_binomial_rate"]["inferential_trials"] == 1


def test_public_mid_unit_cap_retains_zero_credit_partial_then_censors(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path)
    payload = json.loads(document.read_text())
    spec = payload["failure_count_work_spec"]
    for policy in (spec["policy"], spec["campaign_work_spec"]["assessment"]["stopping"]):
        policy.update({"dispatch_mode": "interruptible_unit", "interruptible_evidence_bytes": 1,
                       "interruptible_storage_bytes": 1_000_000})
    document.write_text(json.dumps(payload), encoding="utf-8")
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    first = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert first["campaign_state"] == "progress"
    assert first["completed_shots"] == 0
    assert first["partial_attempt_sha256"] is not None
    first_merge = cli._merge(Namespace(plan=plan_path, receipt=[first["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge-first")))["artifact_path"]
    first_report = cli._assess(Namespace(plan=plan_path, merge=first_merge, campaign_root=str(root), output_root=str(tmp_path / "report-first")))["report"]
    assert first_report["assessment_status"] == "not_assessed"
    assert first_report["target_decision"] is None
    assert first_report["actual_resources"]["wall_ns"] is None
    assert first_report["actual_resources"]["wall_observation_status"] == "unavailable_for_byte_interruption"
    resume = cli._resume(Namespace(plan=plan_path, merge=first_merge, campaign_root=str(root)))
    assert resume["campaign_state"] == "cap_censored"
    assert resume["recovered_terminal_receipt"] is True
    assert resume["exact_missing_set"] == []
    second = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert second["campaign_state"] == "cap_censored"
    assert second["completed_shots"] == 0


def test_public_wall_overshoot_is_zero_credit_and_censors_on_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from bp_registry.campaigns import cli, failure_count_public

    document, root = _public_fixture(tmp_path)
    payload = json.loads(document.read_text())
    spec = payload["failure_count_work_spec"]
    for policy in (spec["policy"], spec["campaign_work_spec"]["assessment"]["stopping"]):
        policy.update({"dispatch_mode": "interruptible_unit", "interruptible_evidence_bytes": 3_000_000,
                       "interruptible_storage_bytes": 3_000_000})
        policy["batch_authorization"]["per_unit_timeout_ns"] = 1
    document.write_text(json.dumps(payload), encoding="utf-8")
    real_runner = failure_count_public.run_canonical_bounded_batch
    ticks = iter((0, 0, 0, 2, 3, 4, 5))
    monkeypatch.setattr(failure_count_public, "run_canonical_bounded_batch",
                        lambda *args, **kwargs: real_runner(*args, **kwargs, clock_ns=lambda: next(ticks)))
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    first = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert first["campaign_state"] == "progress"
    assert first["completed_shots"] == 0
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[first["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    resume = cli._resume(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root)))
    assert resume["campaign_state"] == "cap_censored"
    assert resume["exact_missing_set"] == []
    final_merge = cli._merge(Namespace(plan=plan_path, receipt=[str(tmp_path / "run" / "failure-count-cap-censor.json")], campaign_root=str(root), output_root=str(tmp_path / "merge-final")))["artifact_path"]
    report = cli._assess(Namespace(plan=plan_path, merge=final_merge, campaign_root=str(root), output_root=str(tmp_path / "report")))["report"]
    assert report["first_exhausted_cap"] == "wall"
    assert report["actual_resources"]["completed_shots"] == 0
    assert report["actual_resources"]["wall_ns"] > 0
    assert report["pending_interruption"]["overshoot_ns"] > 0


def test_public_failure_count_recovers_missing_target_receipt_without_rerun(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    first = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert first["campaign_state"] == "target_reached"
    terminal = tmp_path / "run" / "failure-count-target-stop.json"
    saved = terminal.read_bytes()
    terminal.unlink()
    attempt = next((tmp_path / "run" / "attempts").glob("*/attempt.json"))
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[str(attempt)], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    recovery = cli._resume(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root)))
    assert recovery["recovered_terminal_receipt"] is True
    assert recovery["needs_merge_refresh"] is True
    assert recovery["exact_missing_set"] == []
    second = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    assert terminal.read_bytes() == saved
    assert second["receipt_sha256"] == first["receipt_sha256"]
    assert len(list((tmp_path / "run" / "attempts").glob("*/attempt.json"))) == 1


def test_public_failure_count_plan_and_merge_reject_tampering(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path)
    altered = json.loads(document.read_text())
    altered["failure_count_work_spec"]["policy"]["campaign_plan_sha256"] = "0" * 64
    altered["failure_count_work_spec"]["campaign_work_spec"]["assessment"]["stopping"]["campaign_plan_sha256"] = "0" * 64
    document.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="bind the prospective work layout"):
        cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))
    document, root = _public_fixture(tmp_path)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[run["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    merge = json.loads(Path(merge_path).read_text())
    merge["actual_resources"]["decoder_work"] += 1
    Path(merge_path).write_text(json.dumps(merge), encoding="utf-8")
    with pytest.raises(ValueError, match="merge differs"):
        cli._resume(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root)))


def test_public_failure_count_tampered_target_tail_receipt_is_rejected(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path, shots=2, target_failures=1, batch_size=2)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    terminal = Path(run["receipt_path"])
    payload = json.loads(terminal.read_text())
    payload["terminal_receipt"]["authorized_tail_ordinals"] = []
    terminal.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="target receipt differs"):
        cli._merge(Namespace(plan=plan_path, receipt=[str(terminal)], campaign_root=str(root), output_root=str(tmp_path / "merge")))


def test_public_failure_count_plan_run_local_merge_resume_assess_verify(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path)
    planned = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))
    assert planned["publication_slurm_authorization"] == "deny"
    plan_path = planned["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    merged = cli._merge(Namespace(plan=plan_path, receipt=[run["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))
    resumed = cli._resume(Namespace(plan=plan_path, merge=merged["artifact_path"], campaign_root=str(root)))
    assessed = cli._assess(Namespace(plan=plan_path, merge=merged["artifact_path"], campaign_root=str(root), output_root=str(tmp_path / "report")))
    verified = cli._verify(Namespace(plan=plan_path, merge=merged["artifact_path"], report=assessed["artifact_path"], receipt=None, campaign_root=str(root)))
    assert verified["verified"] is True
    assert resumed["complete"] is True
    assert assessed["report"]["total_completed_shots"] == 1
    assert assessed["report"]["actual_resources"]["completed_shots"] == 1
    assert assessed["report"]["terminal_state"] in {"target_reached", "cap_censored"}
    assert cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")["receipt_sha256"] == run["receipt_sha256"]


def test_public_failure_count_report_rejects_tampered_cost(tmp_path: Path) -> None:
    from bp_registry.campaigns import cli

    document, root = _public_fixture(tmp_path)
    plan_path = cli._plan(Namespace(campaign=str(document), campaign_root=str(root), output_root=str(tmp_path / "plan")))["artifact_path"]
    run = cli._run(Namespace(plan=plan_path, campaign_root=str(root), output_root=str(tmp_path / "run")), route="local")
    merge_path = cli._merge(Namespace(plan=plan_path, receipt=[run["receipt_path"]], campaign_root=str(root), output_root=str(tmp_path / "merge")))["artifact_path"]
    report_path = cli._assess(Namespace(plan=plan_path, merge=merge_path, campaign_root=str(root), output_root=str(tmp_path / "report")))["artifact_path"]
    altered = json.loads(Path(report_path).read_text())
    altered["actual_resources"]["decoder_work"] += 1
    Path(report_path).write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="report differs"):
        cli._verify(Namespace(plan=plan_path, merge=merge_path, report=report_path, receipt=None, campaign_root=str(root)))


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
_INTERRUPT_ONCE: set[int] = set()


def _runner(unit: dict[str, object], staging: str) -> dict[str, object]:
    del staging
    ordinal = int(unit["sample_id"]) + 1
    _RUNS.append(ordinal)
    if ordinal in _INTERRUPT_ONCE:
        _INTERRUPT_ONCE.remove(ordinal)
        raise RuntimeError("injected worker interruption")
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


def test_interrupted_unit_retries_only_the_missing_frozen_key(tmp_path: Path) -> None:
    from bp_registry.campaigns.execution import dispatch_failure_count_batches

    global _FAILURES, _RUNS, _INTERRUPT_ONCE
    _FAILURES, _RUNS, _INTERRUPT_ONCE = {1, 2, 6}, [], {3}
    incomplete = dispatch_failure_count_batches(
        _plan(), output_root=tmp_path, workers=1, unit_runner=_runner, stopping=_stopping(),
    )
    assert incomplete["status"] == "incomplete"
    assert incomplete["resumable_unit_keys"] == [_plan().units[2].key]
    # The rest of the authorized batch remains retained; only its failed
    # ordinal is retried on resume.
    assert _RUNS == [1, 2, 3, 4, 5]
    completed = dispatch_failure_count_batches(
        _plan(), output_root=tmp_path, workers=1, unit_runner=_runner, stopping=_stopping(),
    )
    assert completed["receipt"]["terminal_failure_ordinal"] == 6
    assert _RUNS == [1, 2, 3, 4, 5, 3, 6, 7, 8, 9, 10]


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
