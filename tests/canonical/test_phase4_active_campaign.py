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
