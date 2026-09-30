"""Focused, schema-faithful tests for read-only Phase 4 campaign adapters."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from bp_registry.phase4_analysis import wilson_interval


ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("phase4_notebook_campaign", ROOT / "scripts" / "phase4_notebook_campaign.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_real_cancellation_inventory_preserves_interrupted_receipts_without_a_result():
    campaign = _module()
    cancellation = campaign._cancelled_production(ROOT)
    assert cancellation is not None
    assert cancellation["counts"] == {"completed": 159, "incomplete_interrupted": 1}
    snapshots = {stage: campaign._cancelled_stage(stage, cancellation)
                 for stage in ("evaluation", "factorial", "native", "traces")}
    assert all(item["status"] == "cancelled_before_completion" and not item["execution_qualified"]
               for item in snapshots.values())
    row = snapshots["evaluation"]["tables"][0]["rows"][0]
    assert row["completed_attempt_receipts"] == 159
    assert row["interrupted_attempt_receipts"] == 1
    assert row["performance_denominator"] is None
    assert all(not item["tables"] for stage, item in snapshots.items() if stage != "evaluation")


def test_cancelled_receipt_tampering_rejected_before_display(tmp_path):
    campaign = _module()
    receipt = tmp_path / "data/results/phase4-memory-relay/evaluation/b1-ghp-882/baseline/attempts.json"
    _write(receipt, [{"status": "completed"}, {"status": "incomplete_interrupted"}])
    relative = str(receipt.relative_to(tmp_path))
    inventory = {"decision": "comprehensive_phase4_experiment_cancelled_by_user_as_premature",
                 "entries": {"interrupted_b1_baseline": {"path": relative, "sha256": campaign._byte_sha(receipt),
                                                         "attempts": {"completed": 1, "incomplete_interrupted": 1}}}}
    for key, path in {"fresh_evaluation": "evaluation/result.json",
                      "fresh_native_pairs": "evaluation/native-pairs/result.json",
                      "factorial": "factorial/result.json"}.items():
        inventory["entries"][key] = {"path": "data/results/phase4-memory-relay/" + path,
                                      "status": "unavailable_cancelled_before_completion"}
    _write(tmp_path / "data/evidence/phase4-retained-evidence-inventory.json", inventory)
    _write(tmp_path / ".planning/async-jobs/04-13-production-v1.json",
           {"plan_id": "04-13", "status": "cancelled", "terminal_details": {
               "automatic_resume_disabled": True, "retained_attempts_path": relative,
               "retained_attempts_sha256": campaign._byte_sha(receipt),
               "retained_attempt_status_counts": {"completed": 1, "incomplete_interrupted": 1}}})
    assert campaign._cancelled_production(tmp_path)["counts"]["completed"] == 1
    _write(receipt, [{"status": "completed"}, {"status": "completed"}])
    with pytest.raises(ValueError, match="receipt bytes"):
        campaign._cancelled_production(tmp_path)
    inventory["entries"]["interrupted_b1_baseline"]["path"] = "../outside/attempts.json"
    _write(tmp_path / "data/evidence/phase4-retained-evidence-inventory.json", inventory)
    with pytest.raises(ValueError, match="receipt path"):
        campaign._cancelled_production(tmp_path)


def test_baseline_view_relabels_retained_benchmark_snapshot_without_mutation():
    campaign = _module()
    benchmark = {
        "stage": "benchmark",
        "status": "completed",
        "execution_qualified": True,
        "tables": [{
            "stage": "benchmark",
            "name": "active_benchmark",
            "title": "active benchmark",
            "columns": ["stage", "code_id", "arm", "error_rate"],
            "rows": [{"stage": "benchmark", "code_id": "b1-ghp-882", "arm": "controlled_relay_31", "error_rate": 0.07}],
        }],
    }

    baseline = campaign._baseline_diagnostic_view(benchmark)

    assert benchmark["tables"][0]["stage"] == "benchmark"
    assert benchmark["tables"][0]["rows"][0]["stage"] == "benchmark"
    assert baseline["stage"] == "baseline"
    assert baseline["execution_qualified"] is False
    assert baseline["tables"][0]["stage"] == "baseline"
    assert baseline["tables"][0]["name"] == "retained_active_benchmark_baseline_diagnostic"
    assert baseline["tables"][0]["rows"][0]["stage"] == "baseline"


def test_fabricated_completed_calibration_does_not_qualify_from_a_terminal_label(tmp_path, monkeypatch):
    campaign = _module()
    path = tmp_path / "data/results/phase4-memory-relay/calibration/result.json"
    # These are real calibration result field names, but no producer plan/cap
    # verifier is available for the fabricated bytes.
    _write(path, {"schema_version": 1, "status": "completed", "calibration_digest": "a" * 64,
                  "caps_sha256": "b" * 64, "calibration_input": {}, "result_digest": "c" * 64,
                  "evaluation_namespace_accessed": False, "codes": {}})

    class Evaluation:
        @staticmethod
        def verified_calibration_inputs(**_kwargs):
            raise ValueError("terminal calibration result digest does not verify")

    monkeypatch.setattr(campaign, "_runners", lambda: (Evaluation, None, None, None))
    snapshot = campaign._calibration_or_selection(tmp_path, "calibration")
    assert snapshot["status"] == "completed"  # raw producer status remains exact
    assert snapshot["execution_qualified"] is False
    assert "digest" in snapshot["reason"]


def test_fixture_tables_are_explicitly_synthetic_and_contain_plot_accounting_rows():
    campaign = _module()
    fixture = campaign.build_campaign_snapshots(ROOT, development_fixture=True)
    assert fixture["mode"] == "development_fixture"
    assert all(item["status"] == "development_fixture_not_assessed" for item in fixture["artifacts"].values())
    assert all(item["execution_qualified"] is False for item in fixture["artifacts"].values())
    rows = [row for table in fixture["tables"] for row in table["rows"]]
    assert rows and all(row["denominator"] == 7 and row["wilson_95"] == wilson_interval(1, 7) for row in rows)


def test_failure_rows_retain_denominators_wilson_and_runtime_scope_without_filling_missing_values():
    campaign = _module()
    payload = {"aggregate": {"by_cell": {"code/visible/arm": {
        "all_shot_failure": {"failures": 2, "denominator": 7, "estimate": 2 / 7, "wilson_95": [0.08, 0.64]},
        "runtime_seconds": {"p95": 3.2}, "resource_maxrss_kib": {"missing": 1},
    }}}}
    row = campaign._failure_rows("factorial", payload)[0]
    assert row["failures"] == 2 and row["denominator"] == 7
    assert row["wilson_95"] == [0.08, 0.64]
    assert row["runtime_scope"] == "public cell boundary"


def test_evaluation_rows_use_the_producer_all_shot_failure_summary():
    campaign = _module()
    payload = {"codes": {"fixture-code": {"baseline": {"error_rate": .03, "summary": {
        "all_shot_failure": {"failures": 1, "denominator": 7, "estimate": 1 / 7,
                             "wilson_95": wilson_interval(1, 7)}}}}}}
    row = campaign._failure_rows("evaluation", payload)[0]
    assert row["failures"] == 1
    assert row["denominator"] == 7
    assert row["wilson_95"] == wilson_interval(1, 7)


def test_campaign_root_requires_a_repository_shaped_root(tmp_path):
    campaign = _module()
    with pytest.raises(ValueError, match="campaign root"):
        campaign.build_campaign_snapshots(ROOT, campaign_root=tmp_path)


def test_active_benchmark_uses_report_digest_and_selected_rate_schema(tmp_path, monkeypatch):
    campaign = _module()
    report = {"schema_version": 1, "status": "completed", "codes": {"fixture-code": {
        "selected_rate": .03, "selection_status": "selected", "rates": {"p0030": {
            "error_rate": .03, "presets": {"canonical_default": {"controlled_relay_31": {
                "public_command_wall_seconds": {"p95": 1.0}, "raw_work": {"availability": "observed"},
                "termination_counts": {"completed": 1}, "active_memory_verified": True}}}}}}}}
    report["report_digest"] = campaign._json_digest(report)
    report_path = tmp_path / "data/results/phase4-memory-relay/active.json"; _write(report_path, report)
    caps = {"schema_version": 4, "benchmark_evidence": {"active_v4": {"path": "data/results/phase4-memory-relay/active.json", "byte_sha256": campaign._byte_sha(report_path), "report_digest": report["report_digest"]}}}
    caps["caps_digest"] = campaign._json_digest(caps)
    _write(tmp_path / "data/manifests/phase4-pilot-caps.json", caps)

    class Pilots:
        _digest = staticmethod(campaign._json_digest)

    monkeypatch.setattr(campaign, "_runners", lambda: (None, None, Pilots, None))
    snapshot = campaign._benchmark(tmp_path)
    assert snapshot["execution_qualified"] is False
    assert "provenance" in snapshot["reason"]
    assert snapshot["tables"][0]["rows"][0]["error_rate"] == .03
    altered = dict(report); altered["benchmark_digest"] = report["report_digest"]
    _write(report_path, altered)
    assert campaign._benchmark(tmp_path)["execution_qualified"] is False


def test_active_benchmark_rejects_duplicate_shots_before_accepting_arm_aggregates(tmp_path):
    campaign = _module()
    arm_root = tmp_path / "artifacts/fixture-code/p0030/canonical_default/controlled-relay-31"
    manifest = arm_root / "manifest.json"
    _write(manifest, {"fixture": "manifest", "error_rate": .03})
    (arm_root / "run").mkdir(parents=True)
    (arm_root / "run/events.jsonl").write_text("", encoding="utf-8")
    attempts = [{"shot_id": 0, "status": "completed"} for _ in range(32)]
    _write(arm_root / "attempts.json", attempts)
    report = {
        "artifact_root": "artifacts", "core_commits": ["core"], "author_source_pin": "pin",
        "codes": {"fixture-code": {"rates": {"p0030": {"error_rate": .03, "presets": {
            "canonical_default": {"controlled_relay_31": {
                "status": "completed", "active_memory_verified": True, "attempts": attempts,
                "manifest_sha256": campaign._json_digest({"fixture": "manifest", "error_rate": .03}),
            }},
        }}}}},
    }
    with pytest.raises(ValueError, match="exactly once"):
        campaign._verify_active_benchmark(tmp_path, report)


def test_inventory_proof_cache_reuses_current_ledger_once_and_rejects_changed_bytes(tmp_path, monkeypatch):
    campaign = _module()
    ledger = tmp_path / "events.jsonl"
    ledger.write_text("first", encoding="utf-8")
    calls = []
    import bp_registry.ledger as ledger_module

    def read_once(snapshot):
        calls.append(snapshot)
        return [{"run_id": "run", "shot_id": 0}, {"run_id": "run", "shot_id": 1}]

    monkeypatch.setattr(ledger_module, "read_canonical_events_bytes", read_once)
    cache = campaign._InventoryProofCache()
    first_key, first = cache.events(ledger)
    second_key, second = cache.events(ledger)
    assert first_key == second_key and first is second and calls == [b"first"]
    ledger.write_text("changed", encoding="utf-8")
    changed_key, changed = cache.events(ledger)
    assert changed_key != first_key and changed == first and calls == [b"first", b"changed"]


def test_inventory_proof_cache_uses_an_immutable_ledger_snapshot_during_replace(tmp_path, monkeypatch):
    campaign = _module()
    ledger = tmp_path / "events.jsonl"
    ledger.write_text("before", encoding="utf-8")
    import bp_registry.ledger as ledger_module

    def replace_during_parse(snapshot):
        ledger.write_text("after", encoding="utf-8")
        return [{"snapshot_bytes": snapshot.decode("utf-8")}]

    monkeypatch.setattr(ledger_module, "read_canonical_events_bytes", replace_during_parse)
    key, events = campaign._InventoryProofCache().events(ledger)
    assert key[1] != campaign._byte_sha(tmp_path / "events.jsonl")
    assert events == [{"snapshot_bytes": "before"}]


def test_inventory_context_base_uses_one_exact_manifest_buffer_per_current_bytes(tmp_path, monkeypatch):
    campaign = _module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text("first", encoding="utf-8")
    import bp_registry.runner as runner
    calls = []

    class Base:
        def __init__(self, marker): self.marker = marker
        def shot_context(self, shot_id): return {"marker": self.marker, "shot_id": shot_id}

    def build(path, *, manifest_bytes=None):
        calls.append((Path(path), manifest_bytes))
        return Base(manifest_bytes)

    monkeypatch.setattr(runner, "canonical_public_manifest_context", build)
    cache = campaign._InventoryProofCache()
    assert cache.context(manifest, 0)["marker"] == b"first"
    assert cache.context(manifest, 1)["marker"] == b"first"
    manifest.write_text("second", encoding="utf-8")
    assert cache.context(manifest, 0)["marker"] == b"second"
    assert [item[1] for item in calls] == [b"first", b"second"]
