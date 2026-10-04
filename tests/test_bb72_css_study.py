"""Study-design gates for the source-pinned BB72 CSS comparison."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from scripts import run_bb72_css_study as study
from bp_registry.manifests import preflight


def test_grid_and_disjoint_sample_namespaces():
    spec = study.design()
    configs = study.configurations(spec)
    assert len(configs) == 17
    assert {item["family"] for item in configs} == {"spa", "ms", "nms", "oms", "bpgd", "bpsf"}
    for rate in spec["channel"]["x_error_rates"]:
        selection = [study.make_manifest(spec, config, "selection", rate) for config in configs]
        identities = {item["randomness"]["physical_sample_identity"] for item in selection}
        assert len(identities) == 1
        assert {item["artifact"]["raw_sha256"] for item in selection} == {spec["artifact"]["raw_sha256"]}
        assert {item["budgets"]["max_shots"] for item in selection} == {128}
        assert {item["budgets"]["shot"]["work_limits"]["check_to_variable_updates"] for item in selection} == {8640}
        evaluation = study.make_manifest(spec, configs[0], "evaluation", rate)
        assert evaluation["randomness"]["physical_sample_identity"] not in identities
        assert evaluation["budgets"]["max_shots"] == 512


def test_damped_bpgd_and_bpsf_have_explicit_adaptation_identity():
    spec = study.design()
    configs = study.configurations(spec)
    for family in ("bpgd", "bpsf"):
        config = next(item for item in configs if item["family"] == family and item["gamma"] == 0.5)
        manifest = study.make_manifest(spec, config, "selection", 0.05)
        resolved = preflight(manifest).manifest
        assert resolved.schema_version == 6
        assert resolved.memory.bindings[0].parameters["gamma"] == 0.5
        assert resolved.evidence.assessment_status == "not_assessed"
        assert resolved.intervention.qualification != "source_faithful"


def test_selection_rule_counts_unavailable_and_uses_work_then_stable_tie():
    spec = study.design()
    configs = [item for item in study.configurations(spec) if item["family"] == "spa"]
    def row(outcome: str, updates: int):
        return {"outcome": outcome, "work_vector": {"check_to_variable_updates": updates}}
    rows = {
        configs[0]["id"]: [row("exact", 30), row("outcome_unavailable", 30)],
        configs[1]["id"]: [row("exact", 10), row("logical_failure", 10)],
        configs[2]["id"]: [row("exact", 1), row("exact", 1)],
    }
    assert study.choose_configuration(rows, configs) == configs[2]["id"]
    rows[configs[2]["id"]][1]["outcome"] = "invalid_syndrome"
    assert study.choose_configuration(rows, configs) == configs[2]["id"]
    rows.pop(configs[2]["id"])
    with pytest.raises(ValueError, match="incomplete"):
        study.choose_configuration(rows, configs)


def test_paired_contrast_and_holm_are_deterministic():
    def row(sample: str, outcome: str):
        return {"sample_identity": sample, "outcome": outcome}
    baseline = {0: row("a", "outcome_unavailable"), 1: row("b", "exact"), 2: row("c", "exact")}
    variant = {0: row("a", "exact"), 1: row("b", "outcome_unavailable"), 2: row("c", "exact")}
    comparison = study._contrast(baseline, variant)
    assert comparison["newly_valid"] == comparison["lost_valid"] == 1
    assert comparison["failure_rate_difference_vs_reference"] == 0
    assert study._holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    variant[0]["sample_identity"] = "wrong"
    with pytest.raises(ValueError, match="mismatched"):
        study._contrast(baseline, variant)


def test_design_rejects_changed_cohort_identity(tmp_path, monkeypatch):
    altered = deepcopy(study.design())
    altered["cohorts"]["evaluation"]["identity_prefix"] = altered["cohorts"]["selection"]["identity_prefix"]
    path = tmp_path / "design.json"
    path.write_text(json.dumps(altered))
    monkeypatch.setattr(study, "DESIGN", path)
    with pytest.raises(ValueError, match="not separated"):
        study.design()
