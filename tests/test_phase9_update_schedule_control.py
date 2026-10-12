"""Frozen, bounded Phase 9 schedule comparison evidence."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/studies/phase9-update-schedule-control-v1.json"


def _bound(path: str, digest: str) -> dict:
    target = ROOT / path
    assert target.is_file() and sha256(target.read_bytes()).hexdigest() == digest
    return json.loads(target.read_bytes())


def test_one_factor_positive_n_matched_evidence_and_typed_costs() -> None:
    study = json.loads(STUDY.read_bytes())
    report = _bound(study["report_path"], study["report_sha256"])
    _bound(study["merge_path"], study["merge_sha256"])
    _bound(study["plan_path"], study["plan_sha256"])
    assert study["frozen_bounded_n"] == study["completed_matched_n"] == 3
    assert study["source_label"] == "controlled_canonical_adaptation"
    assert study["claim_status"] == "bounded_exploratory_no_superiority_claim"
    assert study["arm_order"] == ["spa_flooding", "spa_check_node_serial"]
    assert report["family"]["status"] == "complete"
    assert report["family"]["missing_unit_keys"] == []
    assert len(report["family"]["complete_sample_identities"]) == 3
    assert len(report["cost_projections"]) == 6
    assert {item["arm_id"] for item in report["cost_projections"]} == set(study["arm_order"])
    for item in report["cost_projections"]:
        component = item["component"]
        assert component["actual_work"]["bp_calls"] == 1
        assert component["runtime_ns"]["status"] == "observed"
        assert component["iterations"]["status"] in {"observed", "unavailable"}
        assert component["convergence_status"]["status"] in {"observed", "unavailable"}
        assert component["peak_rss_bytes"]["status"] in {"observed", "unavailable"}
        assert component["evidence_bytes"]["value"] > 0
    documents = [_bound(path, digest) for path, digest in zip(
        study["one_factor_manifest_paths"], study["one_factor_manifest_sha256"], strict=True)]
    assert [item["policies"]["schedule"]["kind"] for item in documents] == ["flooding", "check_node_serial"]
    for item in documents:
        item.pop("run_id")
        item["policies"].pop("schedule")
        item["randomness"].pop("decoder_seed_identity")
    assert documents[0] == documents[1]


def test_public_two_arm_assess_verify_keeps_denominators_and_diagnostic_separate() -> None:
    study = json.loads(STUDY.read_bytes())
    report = _bound(study["report_path"], study["report_sha256"])
    diagnostic = _bound(study["adapter_diagnostic_path"], study["adapter_diagnostic_sha256"])
    assert diagnostic["campaign_credit"] == 0
    assert diagnostic["termination"] == "count_budget_exhausted"
    assert study["verified"] and study["execution_complete"]
    assert report["family"]["paired_tables"]["spa_flooding-vs-spa_check_node_serial"]["complete_pairs"] == 3
    for arm in study["arm_order"]:
        views = report["denominator_views"][arm]
        assert views["all_shot"]["denominator"] == 3
        assert views["conditional_acceptance"]["denominator"] == 0
        assert views["conditional_acceptance"]["failure_rate"] is None
        assert views["acceptance_probability"]["probability"] == 0.0
    assert report["report_sha256"] == study["report_content_digest"]
