"""List and vote outcomes consume one retained MBBP electorate per sample."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/studies/phase9-mbbp-list-vote-control-v1.json"


def _bound(path: str, digest: str) -> dict:
    target = ROOT / path
    assert target.is_file() and sha256(target.read_bytes()).hexdigest() == digest
    return json.loads(target.read_bytes())


def test_shared_mbbp_member_set_list_vote_matched_evidence() -> None:
    study = json.loads(STUDY.read_bytes())
    report = _bound(study["report_path"], study["report_sha256"])
    merged = _bound(study["merge_path"], study["merge_sha256"])
    assert study["frozen_bounded_n"] == study["completed_matched_n"] == 2
    assert study["arm_order"] == ["list", "vote"]
    assert study["primary_contrasts"] == [["list", "vote"]]
    assert report["family"]["status"] == "complete"
    assert report["family"]["missing_unit_keys"] == []
    assert report["family"]["paired_tables"]["list-vs-vote"]["complete_pairs"] == 2
    assert len(merged["verified_units"]) == 4
    run_root = ROOT / "data/results/phase9-controlled-evaluation-v1/mbbp_list_vote/run"
    shared = list((run_root / "shared").glob("*.json"))
    assert len(shared) == 2
    for path in shared:
        receipt = json.loads(path.read_bytes())
        assert len(receipt["member_ids"]) == len(receipt["components"]) == 2
        assert len(set(receipt["member_ids"])) == 2
        assert all(component["role"] == "mbbp_member" for component in receipt["components"])
        assert all(component["iterations"]["status"] == "unavailable" and
                   component["iterations"]["reason"] for component in receipt["components"])
    for projection in report["cost_projections"]:
        assert len(projection["projection"]["shared_component_sha256s"]) == 2
        assert len(projection["projection"]["incremental_component_sha256s"]) == 2
        assert len(projection["projection"]["validation_component_sha256s"]) == 2
    by_sample = {}
    for path in (run_root / "units").glob("*.json"):
        arm = json.loads(path.read_bytes())
        by_sample.setdefault(arm["physical_sample_identity"], set()).add(arm["shared_input_receipt_sha256"])
    assert len(by_sample) == 2 and all(len(digests) == 1 for digests in by_sample.values())


def test_public_shared_mbbp_assess_verify_claim_remains_bounded() -> None:
    study = json.loads(STUDY.read_bytes())
    report = _bound(study["report_path"], study["report_sha256"])
    assert study["verified"] and study["execution_complete"]
    assert study["source_label"] == "controlled_canonical_adaptation"
    assert study["claim_status"] == "bounded_exploratory_no_superiority_claim"
    assert report["report_sha256"] == study["report_content_digest"]
    assert report["family"]["holm_result"]["frozen_family_size"] == 1
    assert report["family"]["holm_result"]["verdict"] == "not_rejected"
