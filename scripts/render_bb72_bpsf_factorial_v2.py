#!/usr/bin/env python3
"""Render a self-contained HTML view from verified BB72 BP-SF v2 results."""

from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "data/studies/bb72-bpsf-factorial-v2.json"
EVIDENCE = ROOT / "data/results/bb72-bpsf-factorial-v2"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def render() -> Path:
    design = _read(DESIGN)
    result = _read(EVIDENCE / "result.json")
    if result["design_sha256"] != _digest(DESIGN) or result["source_reproduction_assessment"] != "not_applicable":
        raise ValueError("result differs from frozen controlled design")
    for relative, expected in result["evaluation_ledger_sha256"].items():
        if _digest(EVIDENCE / relative / "events.jsonl") != expected:
            raise ValueError(f"ledger differs from verified report: {relative}")
    summaries = result["summaries"]
    figure = make_subplots(rows=1, cols=2, subplot_titles=("p=0.05", "p=0.08"), shared_yaxes=True)
    for column, rate in enumerate(("p050", "p080"), 1):
        for kernel in ("spa", "ms"):
            for gamma in ("g1000", "g0500"):
                keys = [f"{kernel}-{gamma}-{mode}" for mode in ("bp20", "bp40", "bpsf20plus4x5")]
                rows = [summaries[rate][key] for key in keys]
                figure.add_trace(go.Scatter(
                    x=["BP 20", "BP 40", "BP-SF"],
                    y=[row["failure_rate"] for row in rows],
                    error_y={"type": "data", "symmetric": False,
                             "array": [row["failure_interval_95"][1] - row["failure_rate"] for row in rows],
                             "arrayminus": [row["failure_rate"] - row["failure_interval_95"][0] for row in rows]},
                    name=f"{kernel.upper()} γ={int(gamma[1:])/1000:g}",
                    legendgroup=f"{kernel}-{gamma}", showlegend=column == 1,
                    mode="lines+markers", customdata=[f"{row['failures']}/{row['shots']}" for row in rows],
                    hovertemplate="%{fullData.name}<br>%{x}<br>failure=%{y:.3f} (%{customdata})<extra></extra>",
                ), row=1, col=column)
    figure.update_yaxes(range=[0, 1], title_text="Unconditional failure fraction")
    figure.update_layout(title="Independent BB72 BP-SF factorial: exact 95% intervals", height=530)
    costs = go.Figure()
    for rate in ("p050", "p080"):
        for key, row in summaries[rate].items():
            costs.add_trace(go.Scatter(
                x=[row["mean_work_vector"]["check_to_variable_updates"]],
                y=[row["failure_rate"]], mode="markers",
                marker={"size": 11, "symbol": "diamond" if "bpsf" in key else "circle"},
                name=f"{rate}/{key}",
                hovertemplate="%{fullData.name}<br>C2V=%{x:.1f}<br>failure=%{y:.3f}<extra></extra>",
            ))
    costs.update_layout(title="Failure versus mean BP message work", xaxis_title="Mean C2V updates per shot",
                        yaxis_title="Unconditional failure fraction", height=600)
    contrasts = result["primary_contrasts"]
    rows = "\n".join(
        f"<tr><td>{escape(key)}</td><td>{item['newly_valid']}</td><td>{item['lost_valid']}</td>"
        f"<td>{item['failure_rate_difference']:+.3f}</td><td>{item['holm_adjusted_p']:.4g}</td>"
        f"<td>{escape(item['assessment'])}</td></tr>"
        for key, item in sorted(contrasts.items())
    )
    source_rows = "\n".join(
        f"<tr><td>{escape(item['id'])}</td><td>{escape(item['status'])}</td><td>{escape(item['reason'])}</td></tr>"
        for item in result["source_settings_view"]
    )
    content = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>BB72 BP-SF factorial v2</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1250px;margin:2rem auto;padding:0 1rem;color:#172033}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cbd5e1;padding:.5rem;text-align:left}}th{{background:#e8eef7}}
.note{{background:#f5f8fc;border-left:4px solid #4472a9;padding:1rem;margin:1.4rem 0}}</style></head><body>
<h1>BB72 BP-SF factorial v2</h1><p class="note">Independent X-only CSS evaluation on the source-pinned BB72 code. All terminal shots count. Runtime is observed serial execution; it is not the source decoder's parallel latency. No source-curve reproduction is claimed.</p>
<p><a href="REPORT.md">Statistical report</a> · <a href="../../studies/bb72-bpsf-factorial-v2.json">Frozen design</a></p>
{figure.to_html(full_html=False, include_plotlyjs=True)}
{costs.to_html(full_html=False, include_plotlyjs=False)}
<h2>Prespecified p=0.08 paired contrasts</h2><table><thead><tr><th>Contrast</th><th>Newly valid</th><th>Lost valid</th><th>Failure difference</th><th>Holm p</th><th>Assessment</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Source status</h2><table><thead><tr><th>Variant</th><th>Status</th><th>Reason</th></tr></thead><tbody>{source_rows}</tbody></table>
<p class="note">The common 40-sweep and 8,640-message caps do not equate non-message work. See the complete per-arm work vectors and qualified runtime scopes in <code>result.json</code>.</p>
</body></html>"""
    target = EVIDENCE / "study.html"
    encoded = content.encode()
    if target.exists() and target.read_bytes() != encoded:
        raise ValueError("existing offline view differs from verified report")
    target.write_bytes(encoded)
    return target


if __name__ == "__main__":
    print(render())
