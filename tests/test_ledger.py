"""Shot accounting must survive failures, replay, and process interruption."""

from __future__ import annotations

import multiprocessing

import pytest


def _hold_shot(path: str, ready: multiprocessing.synchronize.Event,
               release: multiprocessing.synchronize.Event) -> None:
    """Own a shot in a child process, then exit without a terminal event."""

    from bp_registry.ledger import LedgerWriter

    with LedgerWriter(path) as writer:
        writer.begin(run_id="active", shot_id=7, sample_seed_identity="seed-active")
        ready.set()
        release.wait(timeout=10)


def test_empty_journal_has_no_final_rows_or_denominators(tmp_path):
    from bp_registry.ledger import reconcile, summarize

    path = tmp_path / "events.jsonl"
    path.write_text("")
    assert reconcile(path) == []
    assert summarize(path)["total_final"] == 0


def test_terminal_row_is_durable_and_summary_counts_only_final_rows(tmp_path):
    from bp_registry.ledger import LedgerWriter, reconcile, summarize

    path = tmp_path / "events.jsonl"
    with LedgerWriter(path) as writer:
        writer.begin(run_id="r1", shot_id=1, sample_seed_identity="seed-1")
        writer.terminal(
            run_id="r1", shot_id=1, termination="completed", native_converged=False,
            outcome="logical_failure", postselection="none", selected_output="native_bp",
        )

    rows = reconcile(path)
    assert len(rows) == 1
    assert rows[0]["ledger_version"] == 1
    assert rows[0]["termination"] == "completed"
    summary = summarize(path)
    assert summary["total_final"] == 1
    assert summary["nonconverged"] == 1
    assert summary["interrupted"] == 0
    assert summary["postselected"] == 0
    assert summary["outcomes"] == {"logical_failure": 1}


def test_duplicate_or_out_of_order_events_are_rejected_without_double_counting(tmp_path):
    from bp_registry.ledger import LedgerWriter, reconcile

    path = tmp_path / "events.jsonl"
    with LedgerWriter(path) as writer:
        with pytest.raises(ValueError, match="begin"):
            writer.terminal(run_id="r1", shot_id=1, termination="completed")
        writer.begin(run_id="r1", shot_id=1, sample_seed_identity="seed-1")
        writer.terminal(run_id="r1", shot_id=1, termination="completed")
        writer.terminal(run_id="r1", shot_id=1, termination="completed")

    with LedgerWriter(path) as second:
        with pytest.raises(ValueError, match="already has a terminal"):
            second.begin(run_id="r1", shot_id=1, sample_seed_identity="seed-1")
    assert len(reconcile(path)) == 1


def test_active_owner_stays_pending_then_dead_owner_is_repaired_once(tmp_path):
    from bp_registry.ledger import reconcile

    path = tmp_path / "events.jsonl"
    context = multiprocessing.get_context("spawn")
    ready, release = context.Event(), context.Event()
    process = context.Process(target=_hold_shot, args=(str(path), ready, release))
    process.start()
    try:
        assert ready.wait(timeout=10)
        assert reconcile(path) == []
    finally:
        release.set()
        process.join(timeout=10)
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)

    rows = reconcile(path)
    assert len(rows) == 1
    repaired = rows[0]
    assert repaired["termination"] == "interrupted"
    assert repaired["termination_inference"] == "reconciled_after_owner_release"
    assert repaired["observed_termination"] is False
    assert repaired["native_iterations"] is None
    assert repaired["native_internals_unavailable_reason"]
    assert reconcile(path) == rows
