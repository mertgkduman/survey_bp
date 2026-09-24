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


def _attempt_canonical_intermediate_event(path: str, result: multiprocessing.queues.Queue) -> None:
    """Try to inject canonical evidence without the owning writer's handle."""

    from bp_registry.ledger import CanonicalEventWriter, ShotOwnershipError

    try:
        CanonicalEventWriter(path).event(
            run_id="canonical", shot_id=1, kind="attempt",
        )
    except ShotOwnershipError:
        result.put("ShotOwnershipError")
    else:
        result.put("appended")


def test_empty_journal_has_no_final_rows_or_denominators(tmp_path):
    from bp_registry.ledger import reconcile, summarize

    path = tmp_path / "events.jsonl"
    path.write_text("")
    assert reconcile(path) == []
    assert summarize(path)["total_final"] == 0


def test_begin_requires_replayable_sample_identity(tmp_path):
    from bp_registry.ledger import LedgerWriter

    with LedgerWriter(tmp_path / "events.jsonl") as writer:
        with pytest.raises(ValueError, match="sample_seed_identity"):
            writer.begin(run_id="r1", shot_id=1)


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


def test_native_metric_facts_round_trip_with_qualified_missingness(tmp_path):
    from bp_registry import ledger
    from bp_registry.canonical.metrics import MetricFact, unavailable_metric

    assert hasattr(ledger, "query_native_metric_facts"), (
        "ledger queries must expose typed native metric facts"
    )
    path = tmp_path / "events.jsonl"
    metrics = [
        MetricFact.observed(
            "native_iterations", 0, method="ldpc.BpDecoder.iter",
            scope="native_decoder_call", unit="native_iterations",
            qualification="public_sdk_counter",
        ),
        unavailable_metric(
            "native_edge_updates", method="ldpc.BpDecoder",
            scope="native_decoder_call", unit="edge_messages",
            qualification="opaque_native_internal",
            reason="ldpc.BpDecoder does not expose edge-update counts",
        ),
    ]
    with ledger.LedgerWriter(path) as writer:
        writer.begin(run_id="native", shot_id=1, sample_seed_identity="seed-native")
        writer.terminal(
            run_id="native", shot_id=1, termination="completed",
            native_metric_facts=[metric.as_evidence() for metric in metrics],
        )

    row = ledger.reconcile(path)[0]
    assert row["native_metric_facts"] == [metric.as_evidence() for metric in metrics]
    assert ledger.query_native_metric_facts(path) == [
        {"run_id": "native", "shot_id": 1, **metric.as_evidence()} for metric in metrics
    ]


def test_native_metric_summary_separates_availability_from_numeric_zero(tmp_path):
    from bp_registry import ledger
    from bp_registry.canonical.metrics import MetricFact, unavailable_metric

    path = tmp_path / "events.jsonl"
    metrics = [
        MetricFact.observed(
            "native_iterations", 0, method="ldpc.BpDecoder.iter",
            scope="native_decoder_call", unit="native_iterations",
            qualification="public_sdk_counter",
        ),
        unavailable_metric(
            "native_edge_updates", method="ldpc.BpDecoder",
            scope="native_decoder_call", unit="edge_messages",
            qualification="opaque_native_internal", reason="not exposed",
        ),
    ]
    with ledger.LedgerWriter(path) as writer:
        writer.begin(run_id="native", shot_id=2, sample_seed_identity="seed-native-2")
        writer.terminal(
            run_id="native", shot_id=2, termination="completed",
            native_metric_facts=[metric.as_evidence() for metric in metrics],
        )

    availability = ledger.summarize(path)["native_metric_availability"]
    assert availability["native_iterations"] == {"observed": 1, "unavailable": 0}
    assert availability["native_edge_updates"] == {"observed": 0, "unavailable": 1}


def test_reconciled_interruption_preserves_explicit_unavailable_native_metrics(tmp_path):
    from bp_registry import ledger

    path = tmp_path / "events.jsonl"
    with ledger.LedgerWriter(path) as writer:
        writer.begin(run_id="interrupted", shot_id=3, sample_seed_identity="seed-interrupted")

    repaired = ledger.reconcile(path)[0]
    facts = repaired["native_metric_facts"]
    assert {fact["metric"] for fact in facts} == {
        "native_iterations", "native_edge_updates", "native_control_flow_events",
    }
    assert all(fact["value"] is None for fact in facts)
    assert all(fact["unavailable_reason"] for fact in facts)


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


def test_legacy_manifest_never_opens_a_ledger(tmp_path, monkeypatch):
    import json

    from bp_registry import runner

    manifest = {
        "schema_version": 1, "run_id": "exception-ledger", "source_uri": "https://example.test/paper",
        "source_revision": "v1", "source_anchor": "table", "code_id": "project-three-qubit-css-fixture",
        "experiment_relation": "pilot_adaptation", "expected_output_status": "not_assessed",
        "x_error_rate": 0.1, "seed": 12, "max_iter": 10, "bp_method": "product_sum",
        "schedule": "parallel", "input_vector_type": "syndrome",
    }
    manifest_path, journal = tmp_path / "fixture.json", tmp_path / "events.jsonl"
    manifest_path.write_text(json.dumps(manifest))

    monkeypatch.setattr(runner.sampling, "sample_shot", lambda *_args, **_kwargs: pytest.fail("sampled"))
    with pytest.raises(ValueError, match="read-only"):
        runner.run_one(manifest_path, shot_id=4, ledger_path=journal)
    assert not journal.exists()


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


def test_canonical_intermediate_events_require_active_writer_ownership(tmp_path):
    from bp_registry.ledger import (
        CanonicalEventWriter,
        ShotOwnershipError,
        read_canonical_events,
    )

    path = tmp_path / "canonical-events.jsonl"
    with CanonicalEventWriter(path) as owner, CanonicalEventWriter(path) as intruder:
        owner.begin(run_id="canonical", shot_id=1, sample_seed_identity="seed-1")

        context = multiprocessing.get_context("spawn")
        result = context.Queue()
        process = context.Process(
            target=_attempt_canonical_intermediate_event,
            args=(str(path), result),
        )
        process.start()
        process.join(timeout=10)
        assert process.exitcode == 0
        assert result.get(timeout=1) == "ShotOwnershipError"

        for kind in (
            "attempt",
            "candidate",
            "selection",
            "work",
            "runtime",
            "missingness",
            "trace_link",
        ):
            with pytest.raises(ShotOwnershipError, match="not owned"):
                intruder.event(run_id="canonical", shot_id=1, kind=kind)
        with pytest.raises(ShotOwnershipError, match="not owned"):
            intruder.terminal(
                run_id="canonical", shot_id=1, termination="forged",
            )

        owner.event(run_id="canonical", shot_id=1, kind="attempt")
        owner.terminal(run_id="canonical", shot_id=1, termination="completed")

    assert [event["kind"] for event in read_canonical_events(path)] == [
        "shot_begin",
        "attempt",
        "termination",
    ]


def test_canonical_event_rejects_reserved_lifecycle_kinds(tmp_path):
    from bp_registry.ledger import CanonicalEventWriter, read_canonical_events

    path = tmp_path / "canonical-events.jsonl"
    with CanonicalEventWriter(path) as writer:
        writer.begin(run_id="canonical", shot_id=1, sample_seed_identity="seed-1")
        with pytest.raises(ValueError, match="reserved lifecycle"):
            writer.event(run_id="canonical", shot_id=1, kind="shot_begin")
        with pytest.raises(ValueError, match="reserved lifecycle"):
            writer.event(run_id="canonical", shot_id=1, kind="termination")

    assert [event["kind"] for event in read_canonical_events(path)] == ["shot_begin"]


def test_version_three_schedule_terminal_preserves_dual_budget_views_and_rejects_tampering(tmp_path):
    from bp_registry.canonical.budgets import BudgetView, Measurement, QualifiedIteration, ScheduleTerminalEvidence, WorkVector
    from bp_registry.canonical.verification import CanonicalStructuralVerificationError, reconstruct_schedule_terminal
    from bp_registry.ledger import CANONICAL_SCHEDULE_LEDGER_VERSION, CanonicalEventWriter, read_canonical_events

    source_unit = QualifiedIteration(0, schedule="layered", atomic_unit="one_layer")
    evidence = ScheduleTerminalEvidence(
        schedule="layered", source_iteration=source_unit, completed_traversals=0,
        local_cursor=(1,), stopping_adaptation="D-09 after layer",
        work=WorkVector(check_to_variable_updates=2, convergence_checks=1),
        setup_runtime=Measurement.unavailable(method="not_measured", scope="schedule_setup", unit="ns", precision="unknown", reason="fixture"),
        decode_runtime=Measurement.observed(7, method="fixture", scope="decode", unit="ns", precision="exact"),
        budget_views=(
            BudgetView.common_c2v_cap(2),
            BudgetView.schedule_iteration_limit(QualifiedIteration(1, schedule="layered", atomic_unit="one_layer")),
        ),
    ).as_evidence()
    path = tmp_path / "schedule-events.jsonl"
    deterministic = {
        "candidate": [0, 1],
        "policy_effects": {"update": "min_sum", "schedule": "layered"},
        "rng_identities": {"schedule_order": "sha256:" + "a" * 64},
    }
    with CanonicalEventWriter(path, structural_event_version=CANONICAL_SCHEDULE_LEDGER_VERSION) as writer:
        writer.begin(run_id="schedule", shot_id=1, sample_seed_identity="seed")
        writer.terminal(
            run_id="schedule", shot_id=1, termination="count_budget_exhausted",
            data={"schedule_terminal": evidence, "deterministic_facts": deterministic},
        )

    terminal = read_canonical_events(path)[-1]
    assert terminal["ledger_version"] == 3
    assert reconstruct_schedule_terminal(terminal["data"]["schedule_terminal"]) == evidence
    tampered = dict(evidence)
    tampered["completed_traversals"] = 1
    with pytest.raises(CanonicalStructuralVerificationError, match="progress facts are invalid"):
        reconstruct_schedule_terminal(tampered)


def test_version_three_schedule_verifier_reconstructs_deterministic_claims_after_rehashing(tmp_path):
    """A valid event hash cannot authenticate altered schedule semantics."""
    import bp_registry.canonical.verification as verification

    from bp_registry.canonical.budgets import BudgetView, Measurement, QualifiedIteration, ScheduleTerminalEvidence, WorkVector
    from bp_registry.canonical.verification import CanonicalStructuralVerificationError
    from bp_registry.ledger import CANONICAL_SCHEDULE_LEDGER_VERSION, CanonicalEventWriter, _canonical_event_id, read_canonical_events

    assert hasattr(verification, "validate_schedule_terminal_shot"), (
        "V3 schedule terminals require independent reconstruction rather than rehashed self-claims"
    )

    source_unit = QualifiedIteration(1, schedule="layered", atomic_unit="one_layer")
    terminal = ScheduleTerminalEvidence(
        schedule="layered", source_iteration=source_unit, completed_traversals=1,
        local_cursor=(1,), stopping_adaptation="D-09 after layer",
        work=WorkVector(check_to_variable_updates=2, convergence_checks=1),
        setup_runtime=Measurement.unavailable(method="not_measured", scope="schedule_setup", unit="ns", precision="unknown", reason="fixture"),
        decode_runtime=Measurement.observed(7, method="fixture", scope="decode", unit="ns", precision="exact"),
        budget_views=(
            BudgetView.common_c2v_cap(2),
            BudgetView.schedule_iteration_limit(QualifiedIteration(1, schedule="layered", atomic_unit="one_layer")),
        ),
    ).as_evidence()
    deterministic = {
        "candidate": [0, 1],
        "policy_effects": {"update": "min_sum", "schedule": "layered"},
        "rng_identities": {"schedule_order": "sha256:" + "a" * 64},
    }
    path = tmp_path / "schedule-events.jsonl"
    with CanonicalEventWriter(path, structural_event_version=CANONICAL_SCHEDULE_LEDGER_VERSION) as writer:
        writer.begin(run_id="schedule", shot_id=1, sample_seed_identity="seed")
        writer.terminal(
            run_id="schedule", shot_id=1, termination="count_budget_exhausted",
            data={"schedule_terminal": terminal, "deterministic_facts": deterministic},
        )

    events = read_canonical_events(path)
    assert verification.validate_schedule_terminal_shot(
        events,
        run_id="schedule",
        shot_id=1,
        expected_terminal=terminal,
        expected_deterministic_facts=deterministic,
    ) == events[-1]

    tampered_terminal = {**terminal, "completed_traversals": 0}
    tampered_event = {**events[-1], "data": {"schedule_terminal": tampered_terminal, "deterministic_facts": deterministic}}
    tampered_event["event_id"] = _canonical_event_id(tampered_event)
    with pytest.raises(CanonicalStructuralVerificationError, match="deterministic schedule terminal"):
        verification.validate_schedule_terminal_shot(
            [*events[:-1], tampered_event],
            run_id="schedule",
            shot_id=1,
            expected_terminal=terminal,
            expected_deterministic_facts=deterministic,
        )

    for tampered_facts in (
        {**deterministic, "candidate": [1, 0]},
        {**deterministic, "policy_effects": {"update": "offset_min_sum", "schedule": "layered"}},
        {**deterministic, "rng_identities": {"schedule_order": "sha256:" + "b" * 64}},
    ):
        tampered_event = {**events[-1], "data": {"schedule_terminal": terminal, "deterministic_facts": tampered_facts}}
        tampered_event["event_id"] = _canonical_event_id(tampered_event)
        with pytest.raises(CanonicalStructuralVerificationError, match="deterministic schedule terminal"):
            verification.validate_schedule_terminal_shot(
                [*events[:-1], tampered_event],
                run_id="schedule",
                shot_id=1,
                expected_terminal=terminal,
                expected_deterministic_facts=deterministic,
            )

    changed_decode = {**terminal["decode_runtime"], "value": 99}
    changed_measurement = {
        **terminal,
        "decode_runtime": changed_decode,
        "budget_views": [
            {**view, "decode_runtime": changed_decode}
            for view in terminal["budget_views"]
        ],
    }
    measured_event = {**events[-1], "data": {"schedule_terminal": changed_measurement, "deterministic_facts": deterministic}}
    measured_event["event_id"] = _canonical_event_id(measured_event)
    assert verification.validate_schedule_terminal_shot(
        [*events[:-1], measured_event],
        run_id="schedule",
        shot_id=1,
        expected_terminal=terminal,
        expected_deterministic_facts=deterministic,
    ) == measured_event
