"""Build the standalone side-by-side HTML and PDF numerical-profile guide."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import fill

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs/decoder-numerics-v1-v2.html"
PDF = ROOT / "docs/decoder-numerics-v1-v2.pdf"

SECTIONS = (
    {
        "title": "Four-state BP4",
        "shared": "Both use I=0, X=1, Y=2, Z=3 and three identity-referenced LLRs u^a=log[P(I)/P(a)]. Each edge projects four Pauli weights to one commute/anticommute LLR r. A_cv(a)=1 when Pauli a anticommutes with that edge label.",
        "rows": (
            ("Prior and edge projection",
             "lambda^a=log[P(I)/P(a)], then clip to [-25,25]. The commute/anticommute log-mass projection clips intermediate and final values.",
             "lambda^a and the commute/anticommute projection retain finite float64 values without global clipping."),
            ("Check-to-variable",
             "R_c->v=(-1)^s boxplus_{u != v} r_u->c. Fold neighbors in edge order and clip each pairwise result and final R to [-25,25].",
             "R_c->v=2 atanh[(-1)^s product_{u != v} tanh(r_u->c/2)]. If the product reaches +/-1 exactly, replace it with +/- (1-1e-10). No default hard check cap."),
            ("Posterior",
             "B_v^a=clip25(lambda_v^a + sum_c A_cv(a) R_c->v). Clipping may erase information before the extrinsic subtraction.",
             "B_v^a=lambda_v^a + sum_c A_cv(a) R_c->v. Preserve the full finite float64 posterior."),
            ("Outgoing variable message",
             "u_v->c^a=clip25(B_v^a - A_cv(a) R_c->v). There is no built-in damping.",
             "proposal=B_v^a - A_cv(a) R_c->v; u_new=0.1 u_old + 0.9 proposal. Damping applies to V2C only."),
            ("Hard decision",
             "Choose I if all three LLRs are positive; otherwise choose the minimum LLR, resolving nonidentity ties X, then Y, then Z.",
             "Strict ladder: choose I if it strictly wins; else X if it strictly beats Y and Z; else Z if it strictly beats X and Y; otherwise Y."),
            ("Stopping",
             "An all-identity correction can return at iteration zero when its syndrome matches.",
             "Complete at least one flooding iteration, then return the first syndrome-matching candidate."),
        ),
        "source": "src/bp_registry/quaternary/numerics.py; src/bp_registry/quaternary/compiled.py",
    },
    {
        "title": "Binary SPA",
        "shared": "For each CSS component, q=2 p0/3 under a depolarizing decoder prior p0 and lambda=log[(1-q)/q]. The physical sampling probability p may differ from p0. Both versions use the same parity syndrome and hard decision: bit 1 iff posterior LLR is negative.",
        "rows": (
            ("Prior",
             "lambda=log(1-q)-log(q), clipped to [-25,25].",
             "lambda=log[(1-q)/q], retained as finite float64 without global clipping."),
            ("Check-to-variable",
             "R_c->v=(-1)^s boxplus_{u != v} r_u->c; clip pairwise folds and final R to [-25,25]. A degree-one check returns +/-25.",
             "R_c->v=2 atanh[(-1)^s product_{u != v} tanh(r_u->c/2)]. Exact +/-1 products move to +/- (1-1e-10); no default hard cap."),
            ("Posterior",
             "B_v=clip25(lambda_v + sum_c R_c->v).",
             "B_v=lambda_v + sum_c R_c->v, without global clipping."),
            ("Outgoing variable message",
             "r_v->c=clip25(B_v-R_c->v). There is no built-in damping.",
             "proposal=B_v-R_c->v; r_new=0.1 r_old + 0.9 proposal. Damping applies to V2C only."),
            ("Hard decision and stopping",
             "Bit 1 iff B_v<0; exact zero chooses 0. Stop after the first completed syndrome-matching iteration.",
             "Same hard decision and stopping rule as v1."),
            ("Scope",
             "Historical public manifests explicitly select cpu-float64-spa-v1; min-sum has a separate v1 profile.",
             "New plain SPA schema 9 defaults to cpu-float64-spa-v2. This is SPA, not the presentation's Q8 offset min-sum decoder."),
        ),
        "source": "src/bp_registry/canonical/numerics.py; src/bp_registry/canonical/compiled.py",
    },
)


def build_html() -> None:
    sections = []
    for section in SECTIONS:
        cards = []
        for label, v1, v2 in section["rows"]:
            cards.append(
                f'<div class="row-label">{escape(label)}</div>'
                f'<div class="cell v1">{escape(v1)}</div>'
                f'<div class="cell v2">{escape(v2)}</div>'
            )
        sections.append(
            f'<section><div class="section-heading"><h2>{escape(section["title"])}</h2>'
            f'<p>{escape(section["shared"])}</p></div>'
            '<div class="comparison"><div class="corner">Update step</div>'
            '<div class="column-head v1-head">v1 <small>frozen legacy</small></div>'
            '<div class="column-head v2-head">v2 <small>default for new plain BP</small></div>'
            + "".join(cards) + '</div>'
            f'<p class="source">Implementation: {escape(section["source"])}</p></section>'
        )
    document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canonical BP numerical profiles: v1 and v2</title>
<style>
:root{color-scheme:light;--ink:#172434;--muted:#536579;--line:#d7e0e8;--paper:#fff;--v1:#f2f4f7;--v2:#eaf5f4;--accent:#087e76}
*{box-sizing:border-box}body{margin:0;background:#edf2f5;color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1260px;margin:auto;padding:38px 28px 60px}header{background:#153448;color:#fff;padding:30px 34px;border-radius:16px;margin-bottom:25px}
h1{font-size:31px;line-height:1.15;margin:0 0 10px}header p{margin:0;max-width:900px;color:#deedf0}
.key{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}.key span{background:#ffffff20;padding:6px 11px;border-radius:100px;font-size:13px}
section{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:24px 26px;margin:22px 0;box-shadow:0 3px 12px #1734480b}
h2{font-size:24px;margin:0 0 5px}.section-heading p{margin:0 0 18px;color:var(--muted)}
.comparison{display:grid;grid-template-columns:170px minmax(0,1fr) minmax(0,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.comparison>div{padding:12px 15px;background:#fff}.comparison .corner{background:#e9eef3;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em}
.comparison .column-head{font-size:19px;font-weight:800}.column-head small{display:block;font-size:12px;font-weight:500;color:var(--muted)}
.comparison .v1-head,.comparison .v1{background:var(--v1)}.comparison .v2-head,.comparison .v2{background:var(--v2)}
.comparison .v2-head{color:#075e57}.row-label{font-size:13px;font-weight:750;color:#334b60}.cell{font-size:13px;line-height:1.48;overflow-wrap:anywhere}
.source{margin:14px 1px 0;color:var(--muted);font-size:11px}.note{background:#fff;border-left:5px solid var(--accent);padding:15px 20px;border-radius:8px;color:#344b60}
footer{color:var(--muted);font-size:12px;margin-top:22px}
@media(max-width:750px){main{padding:16px}.comparison{grid-template-columns:92px minmax(0,1fr) minmax(0,1fr)}.comparison>div{padding:9px}.cell{font-size:11px}}
@media print{@page{size:A4 landscape;margin:12mm}body{background:#fff;font-size:11px}main{padding:0}header{border-radius:0;margin-bottom:8mm;padding:15px 20px}section{break-inside:avoid;box-shadow:none;margin:0 0 5mm;padding:9px 12px;border-radius:0}.section-heading p{margin-bottom:8px}.comparison>div{padding:6px 8px}.cell{font-size:9px}.source{font-size:8px}footer{display:none}}
</style></head><body><main><header><h1>Canonical BP: numerical v1 and v2</h1>
<p>Side-by-side update rules for the project-owned float64 BP4 and binary sum-product kernels. V2 is the default for new plain BP construction; explicitly versioned historical evidence keeps its original v1 meaning.</p>
<div class="key"><span>Same Tanner graph and syndrome</span><span>Different numerical recurrence</span><span>Q8 and min-sum are separate policies</span></div></header>
''' + "\n".join(sections) + '''<aside class="note"><strong>Why clipping matters.</strong> If a raw posterior is 40 and a check contributes 20, v1 clips first and sends 25-20=5; v2 forms the extrinsic proposal 40-20=20 before damping. The two states can therefore follow different trajectories even with identical errors and priors.</aside>
<footer>Versioned public routes: binary schema 9 selects float64 SPA v2; quaternary_experiment_v3 selects float64 BP4 v2. Older manifest versions and saved results remain pinned for replay. Generated from scripts/build_decoder_profile_comparison.py.</footer>
</main></body></html>'''
    HTML.write_text(document + "\n", encoding="utf-8")


def build_pdf() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    with PdfPages(PDF, metadata={"Title": "Canonical BP numerical profiles: v1 and v2",
                                 "Author": "survey_bp", "CreationDate": None, "ModDate": None}) as pages:
        for section in SECTIONS:
            fig = plt.figure(figsize=(11.7, 8.3), facecolor="#ffffff")
            fig.text(.045, .955, f"Canonical BP  /  {section['title']}", fontsize=20, weight="bold", color="#172434")
            fig.text(.045, .907, fill(section["shared"], 146), fontsize=9.3, color="#536579", va="top", linespacing=1.4)
            left, right, width = .045, .525, .43
            for x, title, color, head in ((left, "v1  |  frozen legacy", "#f2f4f7", "#566475"),
                                           (right, "v2  |  new plain BP default", "#eaf5f4", "#087e76")):
                fig.add_artist(FancyBboxPatch((x, .08), width, .735,
                    boxstyle="round,pad=0.012,rounding_size=0.012", transform=fig.transFigure,
                    facecolor=color, edgecolor="#d7e0e8", linewidth=1))
                fig.text(x+.018, .785, title, fontsize=12, color=head, weight="bold")
            for index, (label, v1, v2) in enumerate(section["rows"]):
                y = .738 - index*.112
                for x, body in ((left, v1), (right, v2)):
                    fig.text(x+.018, y, label.upper(), fontsize=8, weight="bold", color="#334b60", va="top")
                    fig.text(x+.018, y-.025, fill(body, 67), fontsize=8.3, color="#172434", va="top", linespacing=1.28)
            fig.text(.045, .042, f"Implementation: {section['source']}", fontsize=7.5, color="#536579")
            fig.text(.955, .042, "v2 changes clipping, damping and (for BP4) ties", ha="right", fontsize=7.5, color="#536579")
            pages.savefig(fig)
            plt.close(fig)


if __name__ == "__main__":
    build_html()
    build_pdf()
    print(HTML)
    print(PDF)
