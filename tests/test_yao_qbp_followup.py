"""The B2 Q-BP follow-up is selected only after its independent ledger audit."""

from __future__ import annotations

import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd"
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("yao_non_osd_assess_qbp", ROOT / "assess.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(MODULE, "REPO", tmp_path)
    plan_path = tmp_path / "qbp-plan.json"
    monkeypatch.setattr(MODULE, "QBP_FOLLOWUP_PLAN", plan_path)
    runner = tmp_path / "fake_vanilla_run.py"
    runner.write_text("# pinned runner bytes\n")
    output = tmp_path / "results/qbp-followup-b2-p040-test"
    output.mkdir(parents=True)
    job = {"code": "b2", "p": .04, "seed": 123, "start_shot": 0,
           "fixed_shots": 1, "output": str(output.relative_to(tmp_path))}
    plan_path.write_text(json.dumps({"schema": "yao-completion-qbp-sparse-plan-v1",
                                     "runner": runner.name,
                                     "runner_sha256": sha256(runner.read_bytes()).hexdigest(),
                                     "jobs": [job]}))
    code_hash = json.loads((ROOT / "codes.json").read_text())["codes"]["b2"]["semantic_sha256"]
    source = MODULE.SOURCE["figures"]["8"]["curves"]["qbp"]["0.04000"]
    manifest = {"schema": "yao-vanilla-point-manifest-v1", "code": "b2",
                "physical_p": .04, "seed": 123, "start_shot": 0, "max_shots": 1,
                "stop_rule": "fixed_shard", "campaign_sha256": None,
                "source_qbp_rate": source, "code_semantic_sha256": code_hash,
                "decoder_specs": {"bp4_v2": {
                    "max_iterations": 100, "check_rule": "sum_product",
                    "message_resolution": "float64", "damping_old": 0.0,
                    "numerical_profile": "quaternary-bp4-f64-v2-undamped"}}}
    manifest_bytes = json.dumps(manifest).encode()
    (output / "manifest.json").write_bytes(manifest_bytes)
    record = {"type_i": False, "type_ii": False, "exact_success": True,
              "stabilizer_success": False, "iterations": [1], "elapsed_ns": 5}
    arms = {name: dict(record) for name in ("bp4_v1", "bp4_v2", "binary_v1", "binary_v2")}
    event = {"schema": "yao-vanilla-shot-v1", "shot": 0, "arms": arms}
    ledger = (json.dumps(event) + "\n").encode()
    (output / "events.jsonl").write_bytes(ledger)
    counts = {name: {"type_i": 0, "type_ii": 0, "exact_success": 1,
                     "stabilizer_success": 0, "iteration_sum": 1, "elapsed_ns_sum": 5}
              for name in arms}
    summary = {"schema": "yao-vanilla-point-summary-v1",
               "manifest_sha256": sha256(manifest_bytes).hexdigest(),
               "events_sha256": sha256(ledger).hexdigest(), "code": "b2",
               "physical_p": .04, "source_qbp_rate": source,
               "shots": 1, "start_shot": 0, "end_shot_exclusive": 1,
               "stop_reason": "fixed_shard_complete", "counts": counts}
    (output / "summary.json").write_text(json.dumps(summary))
    return output


def test_qbp_followup_verifies_and_extracts_bp4_v2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = _write_fixture(tmp_path, monkeypatch)
    result = MODULE.verified_qbp_followups()
    assert result[("b2", "qbp", "0.04000")]["shots"] == 1
    assert result[("b2", "qbp", "0.04000")]["evidence_tier"] == "qbp_followup"
    (output / "events.jsonl").write_text("corrupted\n")
    with pytest.raises(ValueError):
        MODULE.verified_qbp_followups()
