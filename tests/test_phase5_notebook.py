"""Read-only Phase 5 notebook, grouped Plotly, and escaped shot inspection."""

from __future__ import annotations

import json

import pytest

from bp_registry.phase5_analysis import ARMS, AttemptRow, Phase5Dataset, ShotArmRow, WORK_FIELDS, synchronized_figure
from scripts.phase5_notebook_support import attempt_details_html, shot_table_html


def _dataset() -> Phase5Dataset:
    work = {field: 0 for field in WORK_FIELDS}
    rows = tuple(ShotArmRow(
        0, "fixed-sample-identity", arm, "manifest-digest", "b1-ghp-882",
        "source<test>", "variant<test>", "controlled_css_adaptation", "unverified",
        "not_assessed", "outcome_unavailable", "count_budget_exhausted", None,
        "null", None, 1 if arm == "impulse" else 0, json.dumps(work),
    ) for arm in ARMS)
    attempts = (AttemptRow(0, "impulse", 0, "invalid_original_candidate",
                           json.dumps({"target_index": 2, "reset_rule": "fresh_per_coordinate",
                                       "lifted_candidate": None, "original_valid": False,
                                       "termination": "invalid_original_candidate"}),
                           "controlled_css_adaptation"),)
    return Phase5Dataset(rows, attempts, "ledger-digest", "design-digest", "source-root", "not_assessed")


def test_phase5_shot_first_candidate_origin_original_validation_and_work():
    dataset = _dataset()
    html = shot_table_html(dataset, shot_id=0, selected_arm="impulse")
    assert "fixed-sample-identity" in html
    assert "pilot_adaptation" in html and "not_assessed" in html
    assert "impulse" in html and "identity" in html
    assert "C2V work" in html and "Selected origin" in html
    assert html.count("<tr") == 8


def test_phase5_attempt_rows_retain_invalid_and_no_proposal():
    html = attempt_details_html(_dataset(), shot_id=0)
    assert "invalid_original_candidate" in html
    assert "fresh_per_coordinate" in html
    assert "original_valid" in html
    assert "No intervention attempt was proposed" in html
    assert html.count("<details>") == 1


def test_phase5_synchronized_legend_visibility_and_work_panels():
    dataset = _dataset()
    before = tuple(dataset.rows)
    figure = synchronized_figure(dataset, selected_arm="impulse")
    assert figure.layout.legend.groupclick == "togglegroup"
    assert len(figure.data) == 3 * len(ARMS)
    for index, arm in enumerate(ARMS):
        group = figure.data[3 * index:3 * index + 3]
        assert all(trace.legendgroup == arm for trace in group)
        assert all(trace.visible == (True if arm in {"identity", "impulse"} else "legendonly") for trace in group)
        assert group[0].showlegend is True
        assert group[1].showlegend is False and group[2].showlegend is False
    assert "not_assessed" in figure.layout.title.text
    assert dataset.rows == before


def test_phase5_notebook_text_is_escaped_and_loader_is_confined(tmp_path):
    from bp_registry.phase5_analysis import load_verified_evidence

    html = shot_table_html(_dataset(), shot_id=0, selected_arm="impulse")
    assert "<script>" not in html
    assert "source&lt;test&gt;" in html and "variant&lt;test&gt;" in html
    assert "source<test>" not in html
    detail = attempt_details_html(_dataset(), shot_id=0)
    assert "<details>" in detail
    with pytest.raises((ValueError, FileNotFoundError)):
        load_verified_evidence(tmp_path)


def test_phase5_plotly_exact_approved_pin_and_notebook_structure():
    import plotly
    import nbformat
    from pathlib import Path

    assert plotly.__version__ == "7.1.0"
    notebook = nbformat.read(Path(__file__).resolve().parents[1] / "notebooks/phase5-interventions-analysis.ipynb", as_version=4)
    sections = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "markdown")
    assert all(section in sections for section in ("## tl;dr", "## Context & methods", "## Data", "## Results", "## Takeaways"))
    assert "not_assessed" in sections
    assert len([cell for cell in notebook.cells if "phase5_parameters" in cell.metadata.get("tags", ())]) == 1


def test_phase5_guide_public_commands_source_limits_and_claim_limits():
    from pathlib import Path

    guide = (Path(__file__).resolve().parents[1] / "docs/phase5-interventions.md").read_text(encoding="utf-8")
    for text in (
        "bp_registry.cli preflight", "bp_registry.cli canonical", "verify-canonical-shot",
        "verify-run", "--preflight-entitlement --calibrate --freeze-caps --self-audit",
        "--evaluate", "test_phase5_code_fixtures.py", "validate_intervention_design.py --check",
        "execute_phase5_notebook.py", "preview_phase5_notebook.py", "plotly==7.1.0",
        "algorithm_interpretation", "controlled_css_adaptation", "mechanism_only_adaptation",
        "not_assessed", "pilot_adaptation", "exact distance is unknown",
        "negative-infinite-LLR", "exact-zero", "16 BPGD rounds", "t_cap=8",
    ):
        assert text in guide
    assert "one baseline and six" in guide.lower() or "one identity baseline and six" in guide.lower()
