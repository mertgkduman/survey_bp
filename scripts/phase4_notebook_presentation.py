"""Portable, qualified tables and figures for the Phase 4 walkthrough."""
from __future__ import annotations

from html import escape
from hashlib import sha256
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from bp_registry.phase4_analysis import wilson_interval

COLORS = ("#2563a6", "#b56819", "#61722f", "#8a4774", "#434b56")
MARKERS = ("o", "s", "^", "D", "v")


def _format(value: Any) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.6g}" if isfinite(value) else "unavailable"
    return str(value)


def table_html(table: Mapping[str, Any], *, max_rows: int = 30, max_cell_chars: int = 512) -> str:
    """Bound the preview while retaining its explicit full-row denominator."""
    if max_rows < 1 or max_cell_chars < 32:
        raise ValueError("table preview must retain at least one row")
    rows = list(table.get("rows", []))
    columns = list(table.get("columns", [])) or list(dict.fromkeys(key for row in rows for key in row))
    title = escape(str(table.get("title", table.get("name", "Evidence"))))
    header = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    def cell(value: Any) -> str:
        text = _format(value)
        if len(text) > max_cell_chars:
            text = text[:max_cell_chars] + " … [value preview; full value in retained artifact]"
        return escape(text)
    body = "".join("<tr>" + "".join(f"<td>{cell(row.get(column))}</td>" for column in columns) + "</tr>"
                   for row in rows[:max_rows])
    return (f"<h4>{title}</h4><p>Showing {min(len(rows), max_rows)} of {len(rows)} retained rows; "
            "unavailable values remain explicit.</p>"
            '<div style="overflow-x:auto"><table style="border-collapse:collapse; width:100%">'
            f"<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>")


def failure_points(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Use the declared failure denominator; never replace incompletes by zeros."""
    points = []
    for row in rows:
        metric = row.get("all_shot_failure", row)
        if not isinstance(metric, Mapping) or "failures" not in metric or "denominator" not in metric:
            continue
        failures, denominator = metric["failures"], metric["denominator"]
        if type(failures) is not int or type(denominator) is not int or not 0 <= failures <= denominator:
            raise ValueError("failure figure requires integer, consistent outcome counts")
        if denominator == 0:
            continue
        rate = row.get("error_rate")
        if not isinstance(rate, (float, int)) or isinstance(rate, bool) or not isfinite(rate) or not 0 <= rate <= 1:
            continue
        if not row.get("code_id") or not row.get("arm", row.get("arm_id")):
            continue
        estimate = failures / denominator
        declared = metric.get("estimate")
        if declared is not None and (type(declared) not in (float, int) or not isfinite(declared) or abs(declared - estimate) > 1e-12):
            raise ValueError("failure estimate disagrees with its retained denominator")
        interval = metric.get("wilson_95")
        if interval is None:
            interval = wilson_interval(failures, denominator)
        if not isinstance(interval, (list, tuple)) or len(interval) != 2:
            raise ValueError("failure figure requires declared 95% Wilson bounds")
        low, high = interval
        expected = wilson_interval(failures, denominator)
        if any(type(v) not in (float, int) or not isfinite(v) for v in interval) or any(abs(a - b) > 1e-10 for a, b in zip(interval, expected)):
            raise ValueError("failure uncertainty does not match 95% Wilson outcome counts")
        arm = str(row.get("arm", row.get("arm_id")))
        if row.get("configuration_id") is not None:
            arm += " / " + str(row["configuration_id"])
        points.append({"code_id": str(row["code_id"]), "arm": arm,
                       "error_rate": float(rate), "failures": failures, "denominator": denominator,
                       "estimate": estimate, "low": low, "high": high})
    identities = [(p["code_id"], p["arm"], p["error_rate"]) for p in points]
    if len(identities) != len(set(identities)):
        raise ValueError("failure figure contains duplicate code/arm/rate populations")
    return points


def failure_figure(rows: Sequence[Mapping[str, Any]], *, title: str, fixture: bool = False):
    """Faceted within-code comparisons with denominator-bearing intervals."""
    points = failure_points(rows)
    if not points:
        return None
    codes = sorted({p["code_id"] for p in points})
    arms = sorted({p["arm"] for p in points})
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
                         "axes.labelsize": 11, "figure.facecolor": "white", "axes.spines.top": False,
                         "axes.spines.right": False}):
        groups = [arms[start:start + 5] for start in range(0, len(arms), 5)]
        panels = [(code, group) for code in codes for group in groups]
        figure, axes = plt.subplots(len(panels), 1, figsize=(9, 3.5 * len(panels)), squeeze=False,
                                    layout="constrained")
        for index, (code, group) in enumerate(panels):
            axis = axes[index, 0]
            for arm in group:
                arm_index = arms.index(arm)
                selected = sorted([p for p in points if p["code_id"] == code and p["arm"] == arm], key=lambda p: p["error_rate"])
                if not selected:
                    continue
                axis.errorbar([p["error_rate"] for p in selected], [p["estimate"] for p in selected],
                              yerr=[[max(0., p["estimate"] - p["low"]) for p in selected],
                                    [max(0., p["high"] - p["estimate"]) for p in selected]],
                              fmt=MARKERS[(arm_index // len(COLORS)) % len(MARKERS)], linestyle="none", capsize=3,
                              color=COLORS[arm_index % len(COLORS)], markersize=5, linewidth=1.2,
                              label=arm)
            axis.set_title(code + (f" — arms {groups.index(group) + 1}/{len(groups)}" if len(groups) > 1 else ""))
            axis.set_xlabel("Physical error probability")
            axis.set_ylabel("All-shot failure probability")
            axis.xaxis.set_major_formatter(PercentFormatter(1.0))
            axis.yaxis.set_major_formatter(PercentFormatter(1.0))
            axis.set_ylim(0, min(1., max(.05, 1.12 * max(p["high"] for p in points))))
            axis.grid(axis="y", color="#e5e7eb", linewidth=.7)
            axis.legend(loc="upper left", bbox_to_anchor=(1, 1), frameon=False, fontsize=10)
        qualification = "Development fixture — synthetic validation records" if fixture else "CSS pilot adaptation — not_assessed"
        figure.suptitle(f"{title}\n{qualification}", fontsize=13)
        counts = sorted({p["denominator"] for p in points})
        figure.supxlabel("95% Wilson intervals; retained denominator(s): " + ", ".join(map(str, counts)), fontsize=10)
    return figure


def stage_tables(campaign: Mapping[str, Any], stage: str) -> list[Mapping[str, Any]]:
    return [table for table in campaign.get("tables", []) if table.get("stage") == stage]


def presentation_views(campaign: Mapping[str, Any]) -> dict[str, Any]:
    """Derive separate display sections from already qualified originating stages."""
    result = {**campaign, "artifacts": dict(campaign.get("artifacts", {})),
              "tables": list(campaign.get("tables", []))}
    fixture = campaign.get("mode") == "development_fixture"
    for stage, sources in (("cross_code", ("evaluation", "factorial")),
                           ("work_runtime_resources", ("benchmark", "calibration", "evaluation", "factorial", "native"))):
        accepted = [source for source in sources
                    if fixture or campaign.get("artifacts", {}).get(source, {}).get("execution_qualified") is True]
        tables = []
        for source in accepted:
            for original in stage_tables(campaign, source):
                table = {**original, "stage": stage, "name": f"{stage}_{original.get('name', source)}",
                         "title": f"{source}: {original.get('title', 'Retained evidence')}"}
                if stage == "work_runtime_resources":
                    columns = ["source_stage", "code_id", "arm", "configuration_id", "error_rate", "runtime_scope",
                               "runtime_tails", "public_elapsed_seconds", "work_vectors", "raw_work", "resource_tails"]
                    table["columns"] = columns
                    table["rows"] = [{"source_stage": source, **{key: row.get(key) for key in columns[1:]}}
                                     for row in original.get("rows", [])]
                tables.append(table)
        result["artifacts"][stage] = {
            "stage": stage, "status": "development_fixture_not_assessed" if fixture else
            "derived_from_verified_campaigns" if accepted else "missing_verified_origins",
            "execution_qualified": bool(accepted) and not fixture,
            "reason": "Each source keeps its own sample population and measurement boundary; no pooled ranking.",
            "producer": {source: campaign.get("artifacts", {}).get(source, {}).get("producer", {}) for source in accepted},
        }
        result["tables"].extend(tables)
    return result


def equation_check_table() -> dict[str, Any]:
    """Run deterministic primitive examples without drawing physical samples."""
    import numpy as np
    from bp_registry.canonical.memory import AffinePriorMemory, PDBPFieldMix, PDPrimeDeltaMix, PosteriorMomentum, V2CDamping

    base, old, fresh = np.array([2., -1.]), np.array([4., 1.]), np.array([-2., 3.])
    momentum = PosteriorMomentum("example-momentum", alpha=.5, gamma=.25)
    cases = [
        ("affine prior", "(1-alpha) base + alpha previous", {"alpha": .25},
         AffinePriorMemory("example-affine", alpha=.25).propose(base, old).prior, [2.5, -.5]),
        ("V2C damping", "(1-gamma) old + gamma fresh", {"gamma": .25},
         V2CDamping("example-damping", gamma=.25).propose(old, fresh, boundary="source_iteration").value, [2.5, 1.5]),
        ("PDBP", "(1-gamma) fresh + gamma old", {"gamma": .25},
         PDBPFieldMix("example-pdbp", gamma=.25).propose(old, fresh, boundary="source_iteration").value, [-.5, 2.5]),
        ("PD-prime", "old + (1-gamma) sum(fresh C2V - old C2V)", {"gamma": .25},
         PDPrimeDeltaMix("example-pdprime", gamma=.25).propose(
             old, np.array([[.5, -.5]]), np.array([[1.5, .5]]), boundary="source_iteration").value, [4.75, 1.75]),
        ("posterior momentum", "g = gamma g_old + (1-gamma)(Q_old - fresh); Q = Q_old - alpha g",
         {"alpha": .5, "gamma": .25, "old_velocity": [0., 0.]},
         momentum.propose(momentum.initial_state(old), fresh, boundary="source_iteration").posterior, [1.75, 1.75]),
    ]
    rows = []
    for name, equation, parameters, observed, expected in cases:
        np.testing.assert_allclose(observed, expected, rtol=0, atol=1e-12)
        rows.append({"primitive": name, "equation": equation, "parameters": parameters,
                     "base": base.tolist(), "old": old.tolist(), "fresh": fresh.tolist(),
                     "observed": observed.tolist(), "expected": expected, "check": "passed"})
    return {"stage": "equations", "name": "deterministic_primitive_examples",
            "title": "Deterministic equation examples — no campaign sampling",
            "columns": ["primitive", "equation", "parameters", "observed", "expected", "check"], "rows": rows}


def display_campaign_stage(stage: str, cached: Mapping[str, Any], campaign: Mapping[str, Any], *,
                           figure_dir: Path | None = None) -> dict[str, Any]:
    """Render a stage without treating a historical or missing artifact as a run."""
    from IPython.display import HTML, Image, display

    snapshot = campaign.get("artifacts", {}).get(stage, cached)
    fixture = campaign.get("mode") == "development_fixture"
    equation_fixture = snapshot.get("kind") == "deterministic_equation_fixture"
    qualification = ("Deterministic equation fixtures / not_assessed" if equation_fixture else
                     "development_fixture / not_assessed" if fixture else
                     "CSS pilot adaptation / not_assessed" if snapshot.get("execution_qualified") is True else
                     "Unqualified artifact metadata / not_assessed")
    display(HTML(f"<p><strong>{escape(stage)}:</strong> {escape(str(snapshot.get('status', 'missing')))}"
                 f"<br>{escape(qualification)}<br>{escape(str(snapshot.get('reason', '')))}</p>"))
    producer = snapshot.get("producer", {})
    if producer:
        display(HTML(f"<p>Source: {escape(str(producer))}</p>"))
    tables = stage_tables(campaign, stage)
    for table in tables:
        display(HTML(table_html(table)))
    can_plot = fixture or snapshot.get("execution_qualified") is True
    figures = []
    if can_plot:
        for table_index, table in enumerate(tables):
            figure = failure_figure(table.get("rows", []), title=str(table.get("title", table.get("name", stage))), fixture=fixture)
            if figure is not None:
                denominators = sorted({point["denominator"] for point in failure_points(table.get("rows", []))})
                display(HTML("<p>95% Wilson intervals; retained denominator(s): " +
                             ", ".join(map(str, denominators)) + ".</p>"))
                buffer = BytesIO()
                figure.savefig(buffer, format="png", dpi=150, facecolor="white")
                png = buffer.getvalue()
                if figure_dir is not None:
                    figure_dir.mkdir(parents=True, exist_ok=True)
                    content_identity = sha256(json.dumps({
                        "table": table, "fixture": fixture,
                        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                    }, sort_keys=True, allow_nan=False).encode()).hexdigest()[:20]
                    path = figure_dir / f"{stage}-{table_index}-{content_identity}.png"
                    if not path.exists():
                        with path.open("xb") as handle:
                            handle.write(png)
                    figures.append(str(path))
                display(Image(data=png))
                plt.close(figure)
    elif tables and not equation_fixture:
        display(HTML("<p>Quantitative figures await verified originating execution; retained rows keep their source status.</p>"))
    result = {"stage": stage, "status": snapshot.get("status", "missing"), "tables": len(tables), "figures": figures,
              "development_fixture": fixture, "execution_qualified": snapshot.get("execution_qualified") is True}
    if stage == "native" and "historical_author_agreement" in campaign.get("artifacts", {}):
        result["auxiliary_views"] = [display_campaign_stage("historical_author_agreement", {}, campaign,
                                                          figure_dir=figure_dir)]
    return result
