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
    assert "C2V work" in html and "Selected origin" in html and "Selected candidate" in html
    assert html.count("<tr") == 8


def test_phase5_attempt_rows_retain_invalid_and_no_proposal():
    html = attempt_details_html(_dataset(), shot_id=0)
    assert "invalid_original_candidate" in html
    assert "fresh_per_coordinate" in html
    assert "original_valid" in html
    assert "No intervention attempt was proposed" in html
    assert html.count("<details>") == 1


def test_phase5_baseline_sweeps_are_visible_without_being_counted_as_interventions():
    base = _dataset()
    baseline_sweep = AttemptRow(0, "identity", 0, "continued", json.dumps({"index": 0}), "identity")
    dataset = Phase5Dataset(base.rows, (baseline_sweep, *base.attempts), base.ledger_sha256,
                            base.design_digest, base.source_root, base.assessment_status)
    detail = attempt_details_html(dataset, shot_id=0)
    table = shot_table_html(dataset, shot_id=0, selected_arm="impulse")
    assert "identity — 1 baseline sweep records" in detail
    assert "identity sweep 0" in detail
    assert "Intervention attempts" in table
    assert dataset.shot(0)[0].attempt_count == 0


def test_phase5_retained_baseline_keeps_sweeps_but_has_zero_intervention_attempts():
    from pathlib import Path
    from bp_registry.phase5_analysis import load_verified_evidence

    root = Path(__file__).resolve().parents[1]
    dataset = load_verified_evidence(root / "data/results/phase5-interventions/b1-mechanism-pilot")
    assert all(row.attempt_count == 0 for row in dataset.rows if row.arm == "identity")
    assert dataset.attempts_for(0, "identity")


def test_phase5_loader_accepts_sealed_v2_calibration_identities():
    from pathlib import Path
    from bp_registry.phase5_analysis import load_verified_evidence

    root = Path(__file__).resolve().parents[1]
    dataset = load_verified_evidence(root / "data/results/phase5-interventions/b1-calibration")
    assert len(dataset.rows) == 4 * len(ARMS)
    assert len({row.sample_identity for row in dataset.rows}) == 4


def test_phase5_attempt_drilldown_keeps_every_terminal_class():
    base = _dataset()
    statuses = (
        "failed", "contradictory_empty_check", "invalid_original_candidate",
        "count_budget_exhausted", "unavailable", "no_proposal",
    )
    attempts = tuple(AttemptRow(
        0, "impulse", index, status,
        json.dumps({"order": index, "termination": status, "original_valid": False}),
        "controlled_css_adaptation",
    ) for index, status in enumerate(statuses))
    dataset = Phase5Dataset(base.rows, attempts, base.ledger_sha256, base.design_digest, base.source_root, base.assessment_status)
    html = attempt_details_html(dataset, shot_id=0)
    assert html.count("<details>") == len(statuses)
    assert all(status in html for status in statuses)


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
    assert "manifest-digest" in figure.data[0].hovertemplate
    assert "fixed-sample-identity" in figure.data[1].customdata
    assert dataset.rows == before


def test_phase5_notebook_text_is_escaped_and_loader_is_confined(tmp_path):
    from bp_registry.phase5_analysis import load_verified_evidence

    html = shot_table_html(_dataset(), shot_id=0, selected_arm="impulse")
    assert "<script>" not in html
    assert "source&lt;test&gt;" in html and "variant&lt;test&gt;" in html
    assert "source<test>" not in html
    figure_html = synchronized_figure(_dataset()).to_html(full_html=False, include_plotlyjs=False)
    assert "variant<test>" not in figure_html
    assert "variant&lt;test&gt;" in figure_html or "variant\\u0026lt;test\\u0026gt;" in figure_html
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


def test_phase5_standalone_html_escaped_offline_grouped_and_no_mutation(tmp_path, monkeypatch):
    from hashlib import sha256
    from pathlib import Path
    import nbformat
    import scripts.preview_phase5_notebook as preview

    dataset = _dataset()
    before = tuple(dataset.rows)
    monkeypatch.setattr(preview, "load_verified_evidence", lambda _path: dataset)
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_code_cell("print('done')", outputs=[nbformat.v4.new_output("stream", name="stdout", text="done")]),
    ])
    source = Path(__file__).resolve().parents[1] / "notebooks/phase5-interventions-analysis.ipynb"
    notebook.metadata["phase5_evidence"] = {
        "source_notebook_sha256": sha256(source.read_bytes()).hexdigest(),
        "assessment_status": "not_assessed", "source_root": str(tmp_path),
        "ledger_sha256": dataset.ledger_sha256, "design_digest": dataset.design_digest,
    }
    executed = tmp_path / "executed.ipynb"
    nbformat.write(notebook, executed)
    destination = tmp_path / "phase5.html"
    preview.export_html(executed, destination, check=True)
    html = destination.read_text(encoding="utf-8")
    assert "plotly.js" in html.lower() or "Plotly.newPlot" in html
    import re
    assert not re.search(r"<(?:script|link)\b[^>]+(?:src|href)\s*=\s*['\"]?https?://", html, re.I)
    assert "togglegroup" in html and "legendonly" in html
    assert "variant&lt;test&gt;" in html and "variant<test>" not in html
    assert "manifest-digest" in html and "not_assessed" in html
    assert "events.jsonl" in html and "phase5-interventions.ipynb" in html
    assert dataset.rows == before
    preview.export_html(executed, destination, check=True)


def test_phase5_html_rejects_untrusted_executed_notebook_identity(tmp_path):
    import nbformat
    import scripts.preview_phase5_notebook as preview

    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_code_cell("print('untrusted')", outputs=[nbformat.v4.new_output("stream", name="stdout", text="untrusted")]),
    ])
    notebook.metadata["phase5_evidence"] = {
        "source_notebook_sha256": "0" * 64, "assessment_status": "not_assessed",
        "source_root": str(tmp_path), "ledger_sha256": "x", "design_digest": "y",
    }
    executed = tmp_path / "tampered.ipynb"
    nbformat.write(notebook, executed)
    with pytest.raises(ValueError, match="tracked source notebook"):
        preview.export_html(executed, tmp_path / "report.html", check=True)
