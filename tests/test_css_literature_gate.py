"""The three-paper B1 gate is finite, qualified, and replayable."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from bp_registry.literature import parse_literature_policy
from bp_registry.manifests import _resolved_artifact_root
from bp_registry.study import _concretize_multi_decoder_study
from scripts.run_css_literature_gate import (
    QUALIFICATION, ROOT, SELECTED, _study, qualification_inventory, verify,
)


STUDY = ROOT / "data/studies/css-literature-b1-gate-v1.json"
RESULTS = ROOT / "data/results/css-literature-gate-v1"


def test_gate_design_pins_b1_artifact_samples_denominator_and_caps() -> None:
    study = _study(STUDY)
    assert study["artifact"]["code_id"] == "b1-ghp-882"
    assert study["budgets"]["max_shots"] == 2
    assert study["budgets"]["denominator_rule"] == "all_terminal_shots"
    assert study["error_rate"] == 0.000001
    assert study["evidence"]["assessment_status"] == "not_assessed"
    assert study["evidence"]["relation"] == "pilot_adaptation"
    assert all(study["budgets"][scope]["max_iterations"] == 100 for scope in ("shot", "search", "attempt"))


def test_all_fourteen_source_dispositions_are_frozen_and_not_source_faithful() -> None:
    inventory = qualification_inventory(STUDY)
    assert inventory == json.loads(QUALIFICATION.read_text())
    rows = inventory["records"]
    assert len(rows) == 14
    assert {family: sum(row["family"] == family for row in rows) for family in ("yao", "bhatnagar", "rabeti")} == {
        "yao": 10, "bhatnagar": 3, "rabeti": 1,
    }
    assert all(row["source_execution_status"] == "not_runnable" and not row["source_faithful"] for row in rows)
    assert all(row["source_revision"] and row["source_sha256"] and row["qualification"] and row["blockers"] for row in rows)
    for family, _folder, variant in SELECTED:
        row = next(item for item in rows if item["family"] == family and item["variant_id"] == variant)
        assert row["execution_status"] == "runnable_canonical_adaptation"
        assert row["runnable_counterpart"] is not None


def test_one_study_compiles_to_strict_intervention_and_ensemble_schemas() -> None:
    assert Path(_resolved_artifact_root("repo:data/artifacts")) == ROOT / "data/artifacts"
    with pytest.raises(ValueError, match="non-traversing"):
        _resolved_artifact_root("repo:../outside")
    for family, folder, variant in SELECTED:
        policy = parse_literature_policy(ROOT / "literature_policies" / folder / f"{variant}.toml")
        decoder = policy.decoder_projection(code_block_length=882, code_check_count=441)
        study = json.loads(STUDY.read_text())
        study["artifact"]["root"] = str((STUDY.parent / study["artifact"]["root"]).resolve())
        _concretize_multi_decoder_study(study, decoder)
        assert study["schema_version"] == (7 if family == "rabeti" else 5)
        assert study["numerical_profile"] == (
            "cpu-float64-min-sum-v1" if family == "rabeti" else "cpu-float64-spa-v1"
        )
        assert study["artifact"]["root"] == "repo:data/artifacts"
        assert "numerical_profiles" not in study
    bad = json.loads(STUDY.read_text())
    bad["numerical_profiles"]["binary_spa"] = "wrong"
    with pytest.raises(ValueError, match="numerical profiles"):
        _concretize_multi_decoder_study(bad, decoder)


def test_gate_package_replays_all_three_and_rejects_result_tamper(tmp_path: Path) -> None:
    assert verify(STUDY, RESULTS)["status"] == "verified"
    copied = tmp_path / "gate"
    shutil.copytree(RESULTS, copied)
    index = json.loads((copied / "evidence-index.json").read_text())
    yao_result = copied / index["entries"]["yao"]["output"] / "result.json"
    content = json.loads(yao_result.read_text())
    content["assessment_status"] = "source_faithful"
    yao_result.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        verify(STUDY, copied)


def test_gate_documentation_keeps_claim_limits_and_phase5_review_visible() -> None:
    guide = (ROOT / "docs/css-literature-gate.md").read_text()
    assert "not_assessed" in guide and "pilot_adaptation" in guide
    assert "Phase 5" in guide and "human" in guide
    assert "fair-beam-relay-css-v2" in guide
    for _family, folder, variant in SELECTED:
        assert f"{folder}/{variant}.toml" in guide
