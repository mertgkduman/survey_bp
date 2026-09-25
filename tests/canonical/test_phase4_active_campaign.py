"""Focused contracts for the v4 active campaign driver."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _module():
    spec = importlib.util.spec_from_file_location("phase4_active_campaign", Path("scripts/run_phase4_active_campaign.py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_campaign_requires_both_active_core_repairs(tmp_path, monkeypatch):
    campaign = _module()
    monkeypatch.setattr(campaign.subprocess, "run", lambda *args, **kwargs: type("Result", (), {"stdout": "deadbeef\n", "returncode": 1})())
    try:
        campaign._core_identity(tmp_path)
    except RuntimeError as error:
        assert "both committed active-memory core repairs" in str(error)
    else:
        raise AssertionError("missing core repairs were accepted")


def test_campaign_report_is_immutable_and_retains_native_rerun_status(tmp_path, monkeypatch):
    campaign = _module()
    output = tmp_path / "report.json"
    output.write_text("{}", encoding="utf-8")
    try:
        campaign.run_campaign(root=tmp_path, output_path=output, job_id="1", campaign_id="active-test")
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing report was overwritten")


def test_later_activation_counts_only_later_legs():
    campaign = _module()
    assert campaign._later_activations({"attempts": [{"distinct_leg_indices": [0]}, {"distinct_leg_indices": [0, 1]}]}) == 1


def test_bounded_b1_selection_requires_activation_and_does_not_require_unbounded_scan():
    campaign = _module()
    complete = {"status": "completed", "active_memory_verified": True,
                "attempts": [{"distinct_leg_indices": [0]} for _ in range(32)]}
    bounded = {**complete, "attempts": [
        {"distinct_leg_indices": [0, 1]} if index < 2 else {"distinct_leg_indices": [0]}
        for index in range(32)
    ]}
    assert campaign._bounded_selected(bounded) is True
    assert campaign._bounded_selected(complete) is False
    incomplete_scan = {**complete, "status": "incomplete_canonical_arm"}
    code = {"rates": {"p0070": {"presets": {
        "canonical_default": {"baseline": {**complete, "arm": "baseline"},
                              "controlled_relay_31": {**incomplete_scan, "arm": "controlled_relay_31"},
                              "controlled_relay_31_bounded": {**bounded, "arm": "controlled_relay_31_bounded"}},
        "source_procedure": {"baseline": {**complete, "arm": "baseline"},
                             "controlled_relay_31": {**complete, "arm": "controlled_relay_31"}},
    }}}}
    assert campaign._selected_arms_complete("b1-ghp-882", .07, code) is True
    code["rates"]["p0070"]["presets"]["canonical_default"]["controlled_relay_31_bounded"] = {**complete, "arm": "controlled_relay_31_bounded"}
    assert campaign._selected_arms_complete("b1-ghp-882", .07, code) is True
    del code["rates"]["p0070"]["presets"]["source_procedure"]["baseline"]
    assert campaign._selected_arms_complete("b1-ghp-882", .07, code) is False
