#!/usr/bin/env python3
"""Read-only, offline HTML view of the verified BB72 CSS BP study."""

from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/studies/bb72-css-bp-v1.json"
EVIDENCE = ROOT / "data/results/bb72-css-bp-v1"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _configuration_ids(spec: dict) -> list[tuple[str, str, float, float | None]]:
    rows = []
    for family in spec["families"]:
        gammas = family["gamma"]
        parameter = "alpha" if "alpha" in family else "offset" if "offset" in family else None
        values = family[parameter] if parameter else [None]
        for value in values:
            for gamma in gammas:
                parts = [family["id"]]
                if parameter:
                    parts.append(f"{parameter[0]}{int(round(value * 1000)):04d}")
                parts.append(f"g{int(round(gamma * 1000)):04d}")
                rows.append(("-".join(parts), family["id"], gamma, value))
    return rows


def _selection_figure(spec: dict) -> go.Figure:
    rates = spec["channel"]["x_error_rates"]
    configs = _configuration_ids(spec)
    figure = make_subplots(rows=1, cols=len(rates), subplot_titles=[f"p={rate:.2f}" for rate in rates], shared_yaxes=True)
    for column, rate in enumerate(rates, 1):
        rate_id = f"p{int(round(rate * 1000)):03d}"
        for family in (item["id"] for item in spec["families"]):
            points = []
            for key, kind, gamma, other in configs:
                if kind != family:
                    continue
                root = EVIDENCE / "selection" / rate_id / key
                result = _read(root / "result.json")
                manifest = _read(root / "manifest.json")
                if result["final_row_count"] != spec["cohorts"]["selection"]["shots_per_rate"] or result["assessment_status"] != "not_assessed":
                    raise ValueError(f"selection arm is incomplete or mislabeled: {root}")
                if result["ledger_sha256"] != _digest(root / "events.jsonl") or manifest["run_id"] != result["run_id"]:
                    raise ValueError(f"selection ledger or manifest differs: {root}")
                outcomes = result["denominators"]
                failures = result["final_row_count"] - outcomes.get("exact", 0) - outcomes.get("stabilizer_equivalent", 0)
                points.append((gamma, failures, key, other))
            figure.add_trace(go.Scatter(
                x=[item[0] for item in points], y=[item[1] for item in points],
                customdata=[[item[2], item[3]] for item in points],
                name=family, legendgroup=family, showlegend=column == 1,
                mode="markers", marker={"size": 10},
                hovertemplate="%{customdata[0]}<br>γ=%{x}<br>failures=%{y}/128<extra></extra>",
            ), row=1, col=column)
    figure.update_xaxes(title_text="Fresh-message weight γ")
    figure.update_yaxes(title_text="Unconditional failures / 128", rangemode="tozero")
    figure.update_layout(title="Selection cohort: every prespecified parameter point", height=500)
    return figure


def _evaluation_figure(result: dict, spec: dict) -> go.Figure:
    summaries = result["shared_work_view"]["summaries"]
    selected = result["selected_configuration_ids"]
    ids = list(dict.fromkeys(["spa-g1000", *selected.values()]))
    figure = go.Figure()
    for key in ids:
        rates, values, plus, minus, labels = [], [], [], [], []
        for rate in spec["channel"]["x_error_rates"]:
            rate_id = f"p{int(round(rate * 1000)):03d}"
            row = summaries[rate_id][key]
            low, high = row["failure_interval_95"]
            rates.append(f"{rate:.2f}")
            values.append(row["failure_rate"])
            plus.append(high - row["failure_rate"])
            minus.append(row["failure_rate"] - low)
            labels.append(f"{row['failures']}/{row['shots']}")
        figure.add_trace(go.Scatter(
            x=rates, y=values, mode="lines+markers", name=key,
            error_y={"type": "data", "array": plus, "arrayminus": minus, "visible": True},
            customdata=labels,
            hovertemplate="%{fullData.name}<br>p=%{x}<br>failure=%{y:.3f} (%{customdata})<extra></extra>",
        ))
    figure.update_layout(title="Evaluation cohort: unconditional failure with exact 95% intervals", xaxis_title="X-error rate p", yaxis_title="Failure fraction", height=500)
    figure.update_yaxes(range=[0, 1])
    return figure


def _contrast_figure(result: dict) -> go.Figure:
    contrasts = result["shared_work_view"]["contrasts"]
    labels, newly, lost, assessments = [], [], [], []
    for key, row in sorted(contrasts.items()):
        labels.append(key)
        newly.append(row["newly_valid"])
        lost.append(-row["lost_valid"])
        assessments.append(row["assessment"])
    figure = go.Figure()
    figure.add_bar(x=labels, y=newly, name="Newly valid")
    figure.add_bar(x=labels, y=lost, name="Lost valid")
    figure.update_layout(title="Matched changes versus undamped SPA", xaxis_title="Rate / family", yaxis_title="Matched samples", barmode="relative", height=500)
    figure.update_traces(customdata=assessments, hovertemplate="%{x}<br>%{y} samples<br>%{customdata}<extra></extra>")
    return figure


def render() -> Path:
    spec = _read(DESIGN)
    result = _read(EVIDENCE / "result.json")
    lock_path = EVIDENCE / "selection-lock.json"
    if (result["design_sha256"] != _digest(DESIGN)
            or result["selection_lock_sha256"] != _digest(lock_path)
            or result["source_reproduction_assessment"] != "not_applicable"):
        raise ValueError("study result is not bound to the frozen design and selection lock")
    for relative, expected in result["evaluation_ledger_sha256"].items():
        if _digest(EVIDENCE / "evaluation" / relative / "events.jsonl") != expected:
            raise ValueError(f"evaluation ledger differs from the verified report: {relative}")
    selection = _selection_figure(spec)
    evaluation = _evaluation_figure(result, spec)
    contrast = _contrast_figure(result)
    source_rows = "\n".join(
        f"<tr><td>{escape(item['id'])}</td><td>{escape(item['bb72_css_status'])}</td><td>{escape(item['reason'])}</td></tr>"
        for item in result["source_settings_view"]
    )
    figures = [selection.to_html(full_html=False, include_plotlyjs=True),
               evaluation.to_html(full_html=False, include_plotlyjs=False),
               contrast.to_html(full_html=False, include_plotlyjs=False)]
    body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>BB72 CSS BP study</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1250px;margin:2rem auto;padding:0 1rem;color:#172033}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cbd5e1;padding:.5rem;text-align:left}}th{{background:#e8eef7}}
.note{{background:#f5f8fc;border-left:4px solid #4472a9;padding:1rem;margin:1.4rem 0}}</style></head><body>
<h1>BB72 CSS BP comparison v1</h1><p class="note">Controlled X-only code-capacity study on the source-pinned [[72,12,6]] BB72 code. Selection and evaluation use disjoint matched samples. All terminal outcomes count. These results do not reproduce the Bravyi circuit-level BP-OSD experiment or rank decoders across codes.</p>
<p><a href="REPORT.md">Verified report</a> · <a href="../../studies/bb72-css-bp-v1.json">Frozen design</a></p>
{figures[0]}{figures[1]}{figures[2]}
<h2>Source-settings view</h2><p>Published settings and source semantics are shown separately from the shared-work comparison. Their BB72 CSS status limits each claim.</p>
<table><thead><tr><th>Source</th><th>BB72 CSS status</th><th>Reason</th></tr></thead><tbody>{source_rows}</tbody></table>
<p class="note">The shared cap is 40 flooding sweeps or 8,640 messages per direction. Extra intervention work differs. Consult the report and per-arm ledgers for outcomes, work, and missing measurements.</p>
</body></html>"""
    target = EVIDENCE / "study.html"
    target.write_text(body, encoding="utf-8")
    return target


if __name__ == "__main__":
    print(render())
