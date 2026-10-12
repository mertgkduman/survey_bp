"""Shared-initial Relay/Beam evaluation, including corrected validation cost."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/studies/phase9-relay-beam-control-v2.json"


def _read_bound(path: str, digest: str) -> dict:
    target = ROOT / path
    assert target.is_file() and sha256(target.read_bytes()).hexdigest() == digest
    return json.loads(target.read_bytes())


def test_three_arm_family_shared_initial_receipt_and_complete_n() -> None:
    study = json.loads(STUDY.read_bytes())
    report = _read_bound(study["report_path"], study["report_sha256"])
    merged = _read_bound(study["merge_path"], study["merge_sha256"])
    assert study["frozen_bounded_n"] == study["completed_matched_n"] == 16
    assert study["arm_order"] == ["initial_bp", "relay", "beam"]
    assert study["primary_contrasts"] == [["initial_bp", "relay"], ["initial_bp", "beam"]]
    assert report["family"]["status"] == "complete"
    assert report["family"]["missing_unit_keys"] == []
    assert report["family"]["holm_result"]["frozen_family_size"] == 2
    assert len(report["cost_projections"]) == 16
    assert len(merged["verified_units"]) == 48
    run_root = ROOT / "data/results/phase9-controlled-evaluation-v2/relay_beam/run"
    shared = list((run_root / "shared").glob("*.json"))
    assert len(shared) == 16
    for item in report["cost_projections"]:
        assert len(item["shared_receipt_sha256"]) == 64
        assert len(item["projection"]["shared_component_sha256s"]) == 1
    by_sample = {}
    for path in (run_root / "units").glob("*.json"):
        receipt = json.loads(path.read_bytes())
        by_sample.setdefault(receipt["physical_sample_identity"], set()).add(receipt["shared_input_receipt_sha256"])
    assert len(by_sample) == 16 and all(len(digests) == 1 for digests in by_sample.values())


def test_replay_cost_corrects_no_candidate_original_check_and_limits_claim() -> None:
    study = json.loads(STUDY.read_bytes())
    old = json.loads((ROOT / study["supersedes"]).read_bytes())
    assert old["scientific_use"] is False
    assert old["claim_status"] == "diagnostic_superseded_cost_accounting"
    assert study["verified"] is True
    assert study["source_label"] == "controlled_canonical_adaptation"
    assert study["claim_status"] == "bounded_exploratory_no_superiority_claim"
    run_root = ROOT / "data/results/phase9-controlled-evaluation-v2/relay_beam/run"
    no_candidate = [json.loads(path.read_bytes()) for path in (run_root / "units").glob("*.json")
                    if json.loads(path.read_bytes())["candidate"] is None]
    assert len(no_candidate) == 1
    assert no_candidate[0]["validation_component"]["actual_work"]["original_checks"] == 0
    report = _read_bound(study["report_path"], study["report_sha256"])
    assert report["family"]["holm_result"]["verdict"] == "not_rejected"
    assert all(table["complete_pairs"] == 16 for table in report["family"]["paired_tables"].values())
