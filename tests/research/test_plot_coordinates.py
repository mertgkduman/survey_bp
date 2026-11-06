"""Scientific plot projections preserve measurements and channel semantics."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="plot-coordinate contract checks require Node",
)


def _plot_contract(script: str) -> object:
    program = """
global.window = globalThis;
require('./web/research/plot-data.js');
const result = (() => {
%s
})();
process.stdout.write(JSON.stringify(result));
""" % script
    return json.loads(
        subprocess.check_output(["node", "-e", program], cwd=ROOT, text=True)
    )


def test_mixed_depolarizing_and_x_only_uses_component_axis_and_transforms_only_depolarizing() -> None:
    result = _plot_contract(
        """
const dep = {channel_kind: 'depolarizing', points: [{x: 0.09, y: 0.01}]};
const bit = {channel_kind: 'x_only', points: [{x: 0.06, y: 0.02}]};
const mode = ResearchPlot.axis([dep, bit]);
return {
  mode,
  depolarizingX: ResearchPlot.coordinate(dep, dep.points[0], mode),
  xOnlyX: ResearchPlot.coordinate(bit, bit.points[0], mode),
  depolarizingY: dep.points[0].y,
  xOnlyY: bit.points[0].y,
};
"""
    )
    assert result == {
        "mode": "bit_flip",
        "depolarizingX": pytest.approx(0.06),
        "xOnlyX": pytest.approx(0.06),
        "depolarizingY": 0.01,
        "xOnlyY": 0.02,
    }


def test_pure_depolarizing_plot_retains_physical_probability() -> None:
    result = _plot_contract(
        """
const first = {channel_kind: 'depolarizing', points: [{x: 0.06}]};
const second = {channel_kind: 'depolarizing', points: [{x: 0.12}]};
const mode = ResearchPlot.axis([first, second]);
return {
  mode,
  coordinates: [
    ResearchPlot.coordinate(first, first.points[0], mode),
    ResearchPlot.coordinate(second, second.points[0], mode),
  ],
};
"""
    )
    assert result == {"mode": "physical", "coordinates": [0.06, 0.12]}


def test_zero_failure_upper_limits_split_line_even_when_bound_has_positive_y() -> None:
    result = _plot_contract(
        """
const points = [
  {x: 1, y: 0.1, failures: 2, ci_high: 0.2},
  {x: 2, y: 0.03, failures: 0, ci_high: 0.03},
  {x: 3, y: 0.2, failures: 4, ci_high: 0.3},
  {x: 4, y: 0.04, status: 'upper 95% bound', is_rate_estimate: false},
  {x: 5, y: 0.25, failures: 5, ci_high: 0.35},
];
return {
  boundFlags: points.map(ResearchPlot.upperBound),
  path: ResearchPlot.linePath(points, p => p.x, p => p.y),
};
"""
    )
    assert result["boundFlags"] == [False, True, False, True, False]
    assert result["path"] == "M1,0.1 M3,0.2 M5,0.25"
    assert "L" not in result["path"]


def test_plot_projection_never_mutates_retained_measurements() -> None:
    result = _plot_contract(
        """
const series = {
  channel_kind: 'depolarizing',
  points: [
    {x: 0.09, y: 0.012, n: 1000, failures: 12, ci_low: 0.006, ci_high: 0.021},
    {x: 0.12, y: 0.03, n: 1000, failures: 30, ci_low: 0.021, ci_high: 0.043},
  ],
};
const before = JSON.stringify(series);
ResearchPlot.coordinate(series, series.points[0], 'bit_flip');
ResearchPlot.linePath(series.points, p => ResearchPlot.coordinate(series, p, 'bit_flip'), p => p.y);
return {unchanged: before === JSON.stringify(series), points: series.points};
"""
    )
    assert result["unchanged"] is True
    assert result["points"] == [
        {
            "x": 0.09,
            "y": 0.012,
            "n": 1000,
            "failures": 12,
            "ci_low": 0.006,
            "ci_high": 0.021,
        },
        {
            "x": 0.12,
            "y": 0.03,
            "n": 1000,
            "failures": 30,
            "ci_low": 0.021,
            "ci_high": 0.043,
        },
    ]


def test_explicit_unknown_and_circuit_coordinates_are_never_converted() -> None:
    result = _plot_contract(
        """
const dep = {channel_kind: 'depolarizing', points: [{x: 0.09}]};
const bit = {channel_kind: 'x_only', points: [{x: 0.06}]};
const explicit = {channel_kind: 'explicit', points: [{x: 0.17}]};
const circuit = {channel_kind: 'embedded_circuit', points: [{x: 4}]};
const unknown = {channel_kind: 'custom_unknown', points: [{x: 0.42}]};
const all = [dep, bit, explicit, circuit, unknown];
const mode = ResearchPlot.axis(all);
return {
  mode,
  coordinates: [explicit, circuit, unknown].map(s =>
    ResearchPlot.coordinate(s, s.points[0], mode)),
  forcedCoordinates: [explicit, circuit, unknown].map(s =>
    ResearchPlot.coordinate(s, s.points[0], 'bit_flip')),
};
"""
    )
    assert result == {
        "mode": "bit_flip",
        "coordinates": [0.17, 4, 0.42],
        "forcedCoordinates": [0.17, 4, 0.42],
    }
