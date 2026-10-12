"""Deterministic Phase 9 evidence closure without promoting source fidelity."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bp_registry.campaigns.evidence_index import _regular, build_phase9_css_evidence_index
from bp_registry.literature import qualify_phase9_source_inventory


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data/results/phase9-css-evidence-index-v1.json"


def test_reconstruct_fourteen_source_records_and_all_twenty_plan_coverage() -> None:
    assert build_phase9_css_evidence_index(ROOT) == INDEX.read_bytes()
    index = json.loads(INDEX.read_bytes())
    assert index["source_variant_count"] == len(index["source_variants"]) == 14
    assert [entry["plan"] for entry in index["coverage"]] == [f"09-{number:02d}" for number in range(1, 21)]
    assert all(entry["status"] == "complete" for entry in index["coverage"])
    assert all(entry["source_faithful"] is False for entry in index["source_variants"])
    assert all(entry["native_status"] == "identity_unverified" for entry in index["source_variants"])
    for item in index["coverage"]:
        assert (ROOT / item["plan_ref"]["path"]).is_file()
        assert (ROOT / item["summary_ref"]["path"]).is_file()
    assert index["coverage"][14]["summary_ref"]["sha256"] is None
    assert set(index["gap_closure"]) == {
        "plan_16_prospective_terminal", "plan_17_dynamic_cap", "plan_18_ordered_partial_terminal",
        "plan_19_typed_shared_input", "plan_20_guarded_serializer",
    }


def test_yao_ordered_stop_cap_censor_keeps_target_inconclusive() -> None:
    index = json.loads(INDEX.read_bytes())
    b1 = index["yao_b1"]
    assert b1["source_label"] == "canonical_adaptation"
    assert b1["target_failures"] == 100 and b1["completed_shots"] == 2
    assert b1["assessment_status"] == "inconclusive_cap_censored"
    assert b1["first_exhausted_cap"] == "wall"
    assert b1["terminal_failure_ordinal"] is None
    assert b1["inferential_prefix"] is None
    assert b1["inverse_binomial_interval"] is None
    assert b1["target_verdict"] == "inconclusive"
    selected = next(item for item in index["source_variants"] if item["identity"] == "yao:bpgd-t001")
    assert selected["canonical_assessment"]["status"] == "inconclusive_cap_censored"
    assert selected["source_faithful"] is False
    assert qualify_phase9_source_inventory(ROOT) == (ROOT / "literature_policies/qualification-phase9-v1.json").read_bytes()


def test_positive_n_shared_input_convergence_iterations_cost_and_phase_status() -> None:
    index = json.loads(INDEX.read_bytes())
    assert index["phase_status"] == "complete"
    assert index["eval03_complete"] is True
    assert index["completion_blockers"] == []
    assert [(item["family_id"], item["frozen_bounded_n"], item["completed_matched_n"]) for item in index["controls"]] == [
        ("schedule", 3, 3), ("relay_beam", 16, 16), ("mbbp_list_vote", 2, 2)]
    for item in index["controls"]:
        assert item["source_label"] == "controlled_canonical_adaptation"
        assert item["claim_status"] == "bounded_exploratory_no_superiority_claim"
        assert item["profiles"] and all(profile["sha256"] for profile in item["profiles"])
        assert item["typed_components"]["component_count"] > 0
        for field in ("convergence_status", "iterations", "runtime_ns", "peak_rss_bytes"):
            assert item["typed_components"]["field_status_counts"][field]
        assert item["holm_result"]["verdict"] == "not_rejected"
        assert item["publication_slurm_authorization"] == "deny"
    assert index["controls"][2]["typed_components"]["field_status_counts"]["iterations"]["unavailable"] == 4


def test_tamper_rejection_and_paper_records_guide_no_overclaim(tmp_path: Path) -> None:
    source = tmp_path / "receipt.json"
    source.write_text('{"status":"complete"}\n')
    with pytest.raises(ValueError, match="digest differs"):
        _regular(tmp_path.resolve(), "receipt.json", digest="0" * 64)
    guide = (ROOT / "docs/css-evaluation.md").read_text()
    assert "inconclusive_cap_censored" in guide
    assert "16/16" in guide and "3/3" in guide and "2/2" in guide
    assert "unavailable" in guide and "Publication Slurm authorization remains `deny`" in guide
    assert "run-shard" not in guide and "emit-slurm" not in guide
    for folder in ("yao-2024-guided-decimation", "bhatnagar-2026-impulse-decoding",
                   "rabeti-2026-multiple-bases-bp-list-decoding"):
        paper = (ROOT / "literature_policies" / folder / "paper_reproduction/PAPER.md").read_text()
        assert "phase9-css-evidence-index-v1.json" in paper
    assert sha256(INDEX.read_bytes()).hexdigest() == sha256(build_phase9_css_evidence_index(ROOT)).hexdigest()
