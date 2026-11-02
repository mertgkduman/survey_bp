"""Compute-only handoff preserves the frozen two-rate result contract."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_reconcile_independent_rate_reports(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "phase4_ler_reconcile_test", ROOT / "scripts/reconcile_phase4_low_noise_ler_parallel.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_job_present", lambda _job_id: False)
    serial, parallel, combined = (tmp_path / name for name in ("serial", "parallel", "combined"))
    serial.mkdir()
    parallel.mkdir()
    arms = {name: {"precision_met": True} for name, _, _ in module.original.ARMS}
    (serial / "identity.json").write_text(json.dumps({"design_byte_sha256": "frozen"}))
    (parallel / "identity.json").write_text(json.dumps({"design_byte_sha256": "frozen"}))
    (serial / "progress.json").write_text(json.dumps({"rates": {
        "p0060": {"error_rate": 0.06, "look_shots": 1024, "precision_met": True, "arms": arms}}}))
    (parallel / "result.json").write_text(json.dumps({
        "rate": 0.05, "look_shots": 2048, "precision_met": True,
        "design_byte_sha256": "frozen", "arms": arms}))
    result = module.run(serial_root=serial, parallel_root=parallel, output_root=combined,
                        serial_job_id="serial", parallel_job_id="parallel")
    assert result["status"] == "completed_precision"
    assert result["rates"]["p0060"]["look_shots"] == 1024
    assert result["rates"]["p0050"]["look_shots"] == 2048
    assert (combined / "result.json").exists()
    assert (combined / "handoff.json").exists()
