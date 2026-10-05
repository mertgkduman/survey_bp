"""Read-only regression lock for the sealed Phase 6 fair-leg campaign."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

import bp_registry.study as study_module
from bp_registry.study import ensure_study


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/studies/fair-beam-relay-css-v2.json"
RESULTS = ROOT / "data/results/fair-beam-relay-css-v2"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as source:
        yield from (json.loads(line) for line in source)


def test_phase6_published_package_is_verified_and_reused_without_campaign_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_launch(*args, **kwargs):
        raise AssertionError("a sealed campaign must never be relaunched by evidence verification")

    monkeypatch.setattr(study_module.subprocess, "run", fail_if_launch)
    result = ensure_study(STUDY, ROOT / "examples/bb72-beam-decoder.toml")

    assert result["status"] == "reused"
    assert result["verification"] == {
        "package_files": 43,
        "assessment_status": "controlled_evaluation_complete",
    }
    assert result["method"] == "beam"


def test_phase6_fair_design_locks_matched_bp_damping_legs_work_and_cohorts() -> None:
    design = _read(STUDY)

    assert design["source_status"] == "controlled_css_adaptation"
    assert design["damping_gammas"] == [1.0, 0.5]
    assert design["common_controls"] == {
        "initial_iterations": 20,
        "max_extra_units": 8,
        "max_extra_c2v_updates": 8640,
        "beam_width": 2,
        "beam_rounds": 4,
        "solution_limit": 1,
        "relay_gamma_low": -0.24,
        "relay_gamma_high": 0.66,
        "relay_seed": "fair-beam-relay-css-v2-disordered",
    }
    assert design["cohorts"]["selection"]["sample_seed"] != design["cohorts"]["evaluation"]["sample_seed"]
    assert "disjoint" in " ".join(design["limitations"])


def test_phase6_published_ledgers_keep_matched_initial_state_and_terminal_units() -> None:
    pruned = denied = False
    for row in _rows(RESULTS / "selection/p050/i05/events.jsonl.gz"):
        for arm in row["arms"].values():
            assert arm["beam"]["initial"] == arm["relay"]["initial"] == arm["initial"]
            assert arm["beam"]["source_status"] == arm["relay"]["source_status"] == "controlled_css_adaptation"
            assert arm["beam"]["source_profile"] == "paper_v2_masked_min_sum_css_adaptation"
            assert arm["relay"]["source_profile"] == "relay_v022_disordered_memory_after_shared_bp_css_adaptation"
            assert arm["beam"]["total_work"]["original_checks"] >= 1
            assert arm["relay"]["total_work"]["original_checks"] >= 1
            pruned |= any(unit["status"] == "pruned" for unit in arm["beam"]["units"])
    for row in _rows(RESULTS / "selection/p050/i10/events.jsonl.gz"):
        denied |= any(
            unit["status"] == "denied"
            for arm in row["arms"].values()
            for method in ("beam", "relay")
            for unit in arm[method]["units"]
        )
    assert pruned is True
    assert denied is True


def test_phase5_visual_review_remains_an_explicit_open_dependency() -> None:
    verification = (ROOT / ".planning/phases/05-guided-and-perturbative-bp-interventions/05-VERIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "remaining checkpoint" in verification
    assert "visual notebook/HTML walkthrough" in verification
