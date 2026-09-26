"""Independent checks for the matched author/native timing derivative."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import summarize_phase4_author_runtime as runtime


def _retained_pair_fixture(root: Path) -> Path:
    native_environment = root / "native-stage" / "venv"
    native_origin = native_environment / "lib" / "site-packages" / "relay_bp" / "__init__.py"
    report = {
        "status": "completed", "author_source_pin": runtime.AUTHOR_PIN,
        "look_shots": 2, "native_environment_path": str(native_environment),
        "native_module_origin": str(native_origin),
        "codes": {"code-a": {
            "complete_pairs": 2, "incomplete_pair_shot_ids": [],
            "paired_success_table": {
                "canonical_0_native_0": 0, "canonical_0_native_1": 1,
                "canonical_1_native_0": 0, "canonical_1_native_1": 1,
            },
            "disagreement": {"exact_candidate": {"count": 1}},
            "executed_gamma_digests_checked": 1,
        }},
    }
    report["result_digest"] = runtime._digest(report)
    root.mkdir(parents=True)
    (root / "result.json").write_text(json.dumps(report), encoding="utf-8")
    for shot_id in range(2):
        record = {
            "code_id": "code-a", "shot_id": shot_id,
            "executed_gamma_digests_checked": 1 if shot_id == 0 else 0,
            "canonical": {
                "status": "completed", "sample_identity": f"sample-{shot_id}",
                "diagnostic_cell": "valid_correct" if shot_id == 0 else "valid_wrong_logical",
                "diagnostic_candidate_sha256": "same" if shot_id == 0 else "canonical-only",
                "public_boundary": {"elapsed_seconds": 4.0 if shot_id == 0 else 6.0},
            },
            "native": {
                "status": "completed", "sample_identity": f"sample-{shot_id}",
                "diagnostic_cell": "valid_correct", "diagnostic_candidate_sha256": "same",
                "native_module_origin": str(native_origin),
                "runtime_seconds": 2.0 if shot_id == 0 else 3.0,
            },
        }
        shot_root = root / "code-a" / f"shot-{shot_id:04d}"
        shot_root.mkdir(parents=True)
        (shot_root / "result.json").write_text(json.dumps(record), encoding="utf-8")
    return root


def test_author_runtime_requires_all_matched_pairs_and_preserves_timing_scopes(tmp_path):
    root = _retained_pair_fixture(tmp_path / "agreement")
    summary = runtime.summarize_author_runtime(root)
    pair = summary["codes"]["code-a"]
    assert pair["paired_shots"] == 2
    assert pair["canonical_public_seconds"]["median"] == 5.0
    assert pair["native_pipeline_seconds"]["median"] == 2.5
    assert pair["paired_canonical_over_native_ratio"]["median"] == 2.0
    assert pair["canonical_slower_pairs"] == 2
    assert pair["exact_candidate_disagreements"] == 1
    assert "unequal" in summary["claim_limit"]
    assert summary["summary_digest"] == runtime._digest({k: v for k, v in summary.items() if k != "summary_digest"})
    written = runtime.write_summary(root)
    assert written.read_bytes() == runtime.write_summary(root).read_bytes()
    assert json.loads(written.read_text())["summary_digest"] == summary["summary_digest"]


def test_author_runtime_rejects_sample_drift_without_dropping_shot(tmp_path):
    root = _retained_pair_fixture(tmp_path / "agreement")
    shot_path = root / "code-a" / "shot-0001" / "result.json"
    shot = json.loads(shot_path.read_text())
    shot["native"]["sample_identity"] = "different-sample"
    shot_path.write_text(json.dumps(shot), encoding="utf-8")
    with pytest.raises(ValueError, match="physical sample identity"):
        runtime.summarize_author_runtime(root)


def test_author_runtime_rejects_report_or_pair_omission(tmp_path):
    root = _retained_pair_fixture(tmp_path / "agreement")
    (root / "code-a" / "shot-0001" / "result.json").unlink()
    with pytest.raises(FileNotFoundError):
        runtime.summarize_author_runtime(root)
    report_path = root / "result.json"
    report = json.loads(report_path.read_text())
    report["look_shots"] = 3
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="digest does not verify"):
        runtime.summarize_author_runtime(root)
