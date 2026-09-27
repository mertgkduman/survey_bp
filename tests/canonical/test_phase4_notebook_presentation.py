"""Check denominators, uncertainty and qualified rendering, not styling internals."""
from __future__ import annotations

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from phase4_notebook_presentation import failure_points, failure_figure, table_html, display_campaign_stage
from bp_registry.phase4_analysis import wilson_interval


def _rows():
    return [{"code_id": "fixture-css-code", "arm": arm, "error_rate": rate,
             "failures": failures, "denominator": 16,
             "estimate": failures / 16, "wilson_95": wilson_interval(failures, 16)}
            for arm, rate, failures in [("baseline", .01, 0), ("baseline", .03, 4),
                                        ("memory", .01, 0), ("memory", .03, 2)]]


def test_failure_points_preserve_counts_and_empty_denominators():
    rows = _rows() + [{**_rows()[0], "failures": 0, "denominator": 0, "estimate": None}]
    points = failure_points(rows)
    assert len(points) == 4
    assert points[0]["estimate"] == 0
    assert points[0]["high"] > 0
    assert points[1]["denominator"] == 16
    assert failure_points([{"status": "incomplete", "error_rate": .03}]) == []
    with pytest.raises(ValueError, match="outcome counts"):
        failure_points([{**_rows()[0], "failures": 17}])
    with pytest.raises(ValueError, match="estimate"):
        failure_points([{**_rows()[0], "estimate": .2}])
    with pytest.raises(ValueError, match="uncertainty"):
        failure_points([{**_rows()[0], "wilson_95": [.1, .2]}])
    with pytest.raises(ValueError, match="duplicate"):
        failure_points([_rows()[0], _rows()[0]])
    configurations = failure_points([{**_rows()[0], "configuration_id": "a"},
                                     {**_rows()[0], "configuration_id": "b"}])
    assert [point["arm"] for point in configurations] == ["baseline / a", "baseline / b"]


def test_preview_is_bounded_escaped_and_missing_values_explicit():
    html = table_html({"title": "<script>", "columns": ["label", "runtime_seconds"],
                       "rows": [{"label": "<b>", "runtime_seconds": None}, {"label": "second"}]}, max_rows=1)
    assert "Showing 1 of 2" in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;" in html
    assert "unavailable" in html
    assert "second" not in html.split("<tbody>")[1]


def test_fixture_figure_labels_uncertainty_and_qualification(tmp_path):
    figure = failure_figure(_rows(), title="Controlled fixture view", fixture=True)
    assert figure is not None
    text = " ".join(item.get_text() for item in figure.texts)
    assert "Development fixture" in text
    assert "synthetic" in text
    assert "95% Wilson" in text
    assert "16" in text
    destination = tmp_path / "fixture.png"
    figure.savefig(destination, dpi=100)
    assert destination.stat().st_size > 1000
    plt.close(figure)
    assert failure_figure([], title="Missing evidence") is None


def test_unqualified_campaign_rows_never_become_figures(tmp_path):
    campaign = {"mode": "read_only_campaign_inventory", "artifacts": {
        "evaluation": {"status": "running", "execution_qualified": False}},
        "tables": [{"stage": "evaluation", "name": "Outcomes", "rows": _rows()}]}
    result = display_campaign_stage("evaluation", {}, campaign, figure_dir=tmp_path)
    assert result["figures"] == []
    assert list(tmp_path.iterdir()) == []
