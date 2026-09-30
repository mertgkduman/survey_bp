#!/usr/bin/env python3
"""Export the verified Phase 5 notebook as a self-contained offline HTML view."""

from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import sys

import nbformat
import plotly


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bp_registry.phase5_analysis import ARMS, load_verified_evidence, synchronized_figure  # noqa: E402
from scripts.phase5_notebook_support import shot_table_html  # noqa: E402


def export_html(executed: Path, html_path: Path, *, check: bool = False) -> Path:
    if plotly.__version__ != "7.1.0":
        raise ValueError("Phase 5 HTML requires the approved plotly==7.1.0 pin")
    notebook = nbformat.read(executed, as_version=4)
    nbformat.validate(notebook)
    evidence = notebook.metadata.get("phase5_evidence", {})
    source_notebook = ROOT / "notebooks/phase5-interventions-analysis.ipynb"
    if evidence.get("source_notebook_sha256") != sha256(source_notebook.read_bytes()).hexdigest():
        raise ValueError("executed notebook does not match the tracked source notebook")
    if evidence.get("assessment_status") != "not_assessed" or not evidence.get("source_root"):
        raise ValueError("executed notebook lacks qualified evidence metadata")
    if not any(cell.cell_type == "code" and cell.get("outputs") for cell in notebook.cells):
        raise ValueError("Phase 5 notebook has no executed results")
    dataset = load_verified_evidence(Path(evidence["source_root"]))
    if dataset.ledger_sha256 != evidence.get("ledger_sha256") or dataset.design_digest != evidence.get("design_digest"):
        raise ValueError("executed notebook evidence digest has drifted")
    figure = synchronized_figure(dataset)
    figure_html = figure.to_html(full_html=False, include_plotlyjs=True, div_id="phase5-interventions-figure")
    if re.search(r"<(?:script|link)\b[^>]+(?:src|href)\s*=\s*['\"]?https?://", figure_html, re.I):
        raise ValueError("Phase 5 figure export must not require a network asset")
    selected = dataset.shot(0)
    if len(selected) != len(ARMS):
        raise ValueError("Phase 5 export requires the complete initial matched shot")
    source_rows = []
    for row in selected:
        source_rows.append("<tr>" + "".join(
            f"<td>{escape(str(value))}</td>" for value in (
                row.arm, row.source_revision, row.variant, row.qualification,
                row.native_availability, row.assessment_status, row.manifest_sha256,
            )
        ) + "</tr>")
    evidence_reference = "../phase5-interventions/b1-mechanism-pilot/"
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'">
<title>Phase 5 B1 intervention evidence</title>
<style>body{font:15px/1.5 system-ui,sans-serif;max-width:1600px;margin:0 auto;padding:2rem;color:#17253b;background:#fff}h1,h2{line-height:1.2}p{max-width:88ch}table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border-bottom:1px solid #dce3eb;padding:.5rem;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#f2f6f8}tr.selected{background:#eaf5f3}code{overflow-wrap:anywhere}.note{padding:.8rem 1rem;background:#fff8e8;border-left:4px solid #997000}a{color:#006c76}</style></head><body>
<h1>Phase 5 B1 intervention evidence</h1>
<p class="note">This is a bounded <strong>pilot_adaptation</strong> mechanism inspection on B1 at p=0.07. All arms are <strong>not_assessed</strong> for curve agreement or superiority. Each of 16 matched physical samples has one baseline and six separate single-intervention arms.</p>
<p>Plotly version: <strong>7.1.0</strong>. Approved upstream release: <code>plotly/plotly.py v7.1.0 @ 243bfd0fa5c0a5c29a185e4034a1ab5b111695a5</code>. The figure and JavaScript are embedded for offline use.</p>
<h2>Matched shot 0</h2>
""" + shot_table_html(dataset, shot_id=0, selected_arm="guided_decimation") + """
<h2>Source and manifest identities</h2><table><thead><tr><th>Arm</th><th>Source revision</th><th>Variant</th><th>Qualification</th><th>Native availability</th><th>Assessment</th><th>Manifest SHA256</th></tr></thead><tbody>""" + "".join(source_rows) + """</tbody></table>
<h2>Synchronized mechanism panels</h2><p>Click an arm in the legend to toggle it in outcome, attempt, and work panels together. Baseline and guided decimation start visible; other arms start in the legend.</p>
""" + figure_html + """
<h2>Evidence and full drilldown</h2><p>The executed notebook retains every attempt, including failures, denials, invalid lifts, cap hits, and no-proposal branches. Evidence files remain read-only inputs to this report.</p>
<ul><li><a href=""" + '"' + escape(evidence_reference + "result.json", quote=True) + '"' + """>Matched result</a></li><li><a href=""" + '"' + escape(evidence_reference + "events.jsonl", quote=True) + '"' + """>Complete structural ledger</a></li><li><a href="phase5-interventions.ipynb">Executed full-attempt notebook</a></li></ul>
<p>Code ID: <code>b1-ghp-882</code>; design digest: <code>""" + escape(dataset.design_digest) + """</code>; ledger SHA256: <code>""" + escape(dataset.ledger_sha256) + """</code>.</p>
</body></html>"""
    if "legendonly" not in html or "togglegroup" not in html or "not_assessed" not in html:
        raise ValueError("Phase 5 HTML omitted required grouped visibility or assessment labels")
    if check and html_path.exists() and html_path.read_text(encoding="utf-8") != html:
        raise ValueError("Phase 5 HTML differs from a deterministic verified export")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executed", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(export_html(args.executed, args.html, check=args.check))


if __name__ == "__main__":
    main()
