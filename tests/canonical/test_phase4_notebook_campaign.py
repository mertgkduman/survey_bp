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


def test_real_inventory_is_read_only_and_preserves_current_nonterminal_states():
    campaign = _module()
    inventory = campaign.build_campaign_snapshots(ROOT)
    assert inventory["mode"] == "read_only_campaign_inventory"
    assert inventory["assessment"] == "not_assessed"
    assert inventory["summary"]["qualified_stages"] == []
    assert inventory["artifacts"]["calibration"]["status"] == "missing"
    assert inventory["artifacts"]["evaluation"]["status"] == "missing"
    assert inventory["artifacts"]["benchmark"]["execution_qualified"] is False
    assert inventory["artifacts"]["historical_author_agreement"]["execution_qualified"] is False


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


def test_campaign_root_requires_a_repository_shaped_root(tmp_path):
    campaign = _module()
    with pytest.raises(ValueError, match="campaign root"):
        campaign.build_campaign_snapshots(ROOT, campaign_root=tmp_path)


def test_active_benchmark_uses_report_digest_and_selected_rate_schema(tmp_path, monkeypatch):
    campaign = _module()
    report = {"schema_version": 1, "status": "completed", "codes": {"fixture-code": {"selected_rate": .03, "selection_status": "selected"}}}
    report["report_digest"] = campaign._json_digest(report)
    report_path = tmp_path / "data/results/phase4-memory-relay/active.json"; _write(report_path, report)
    caps = {"schema_version": 4, "benchmark_evidence": {"active_v4": {"path": "data/results/phase4-memory-relay/active.json", "byte_sha256": campaign._byte_sha(report_path), "report_digest": report["report_digest"]}}}
    caps["caps_digest"] = campaign._json_digest(caps)
    _write(tmp_path / "data/manifests/phase4-pilot-caps.json", caps)

    class Pilots:
        _digest = staticmethod(campaign._json_digest)

    monkeypatch.setattr(campaign, "_runners", lambda: (None, None, Pilots, None))
    snapshot = campaign._benchmark(tmp_path)
    assert snapshot["execution_qualified"] is True
    assert snapshot["tables"][0]["rows"][0]["error_rate"] == .03
    altered = dict(report); altered["benchmark_digest"] = report["report_digest"]
    _write(report_path, altered)
    assert campaign._benchmark(tmp_path)["execution_qualified"] is False
