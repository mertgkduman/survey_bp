"""Build the compact, vector-typeset v1/v2 comparison in HTML and PDF."""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs/decoder-numerics-v1-v2.html"
PDF = ROOT / "docs/decoder-numerics-v1-v2.pdf"

CLIP = r"$\mathcal{C}_{K}(x)=\max(-K,\min(K,x))$"
PARAMETERS = r"$\mathrm{v1}:K=25,\qquad\mathrm{v2}:\epsilon=10^{-10},\quad d=0.1$"
CHECK_V1 = (
    r"$a\boxplus b=2\operatorname{atanh}[\tanh(a/2)\tanh(b/2)]$",
    r"$R_{c\to v}=(-1)^{s_c}\mathcal{B}_{K}(r_{\partial c\setminus v})$",
)
CHECK_V2 = (
    r"$q_{cv}=(-1)^{s_c}\prod_{u\in\partial c\setminus v}\tanh(r_{u\to c}/2)$",
    r"$R_{c\to v}=2\operatorname{atanh}[\mathcal{C}_{1-\epsilon}(q_{cv})]$",
)


@dataclass(frozen=True)
class Comparison:
    title: str
    subtitle: str
    belief_v1: str
    belief_v2: str
    message_v1: tuple[str, ...]
    message_v2: tuple[str, ...]
    note_v1: str
    note_v2: str


COMPARISONS = (
    Comparison(
        title="Binary sum-product BP",
        subtitle="Binary log-likelihood ratio under a depolarizing CSS marginal prior.",
        belief_v1=r"$B_v=\mathcal{C}_{K}\!\left(\lambda_v+\sum_{c\in\partial v}R_{c\to v}\right)$",
        belief_v2=r"$B_v=\lambda_v+\sum_{c\in\partial v}R_{c\to v}$",
        message_v1=(r"$m_{v\to c}^{\mathrm{new}}=\mathcal{C}_{K}(B_v-R_{c\to v})$",),
        message_v2=(r"$m_{v\to c}^{\mathrm{new}}=d\,m_{v\to c}^{\mathrm{old}}+(1-d)(B_v-R_{c\to v})$",),
        note_v1="Clip the prior and each message to magnitude 25. No damping.",
        note_v2="Keep finite LLRs unclipped. Dampen only the outgoing variable message.",
    ),
    Comparison(
        title="Four-state BP4",
        subtitle="Pauli states X, Y, Z; A indicates anticommutation. Edges carry commute/anticommute LLRs.",
        belief_v1=r"$B_v^a=\mathcal{C}_{K}\!\left(\lambda_v^a+\sum_{c\in\partial v}A_{cv}^aR_{c\to v}\right)$",
        belief_v2=r"$B_v^a=\lambda_v^a+\sum_{c\in\partial v}A_{cv}^aR_{c\to v}$",
        message_v1=(r"$m_{v\to c}^{a,\mathrm{new}}=\mathcal{C}_{K}(B_v^a-A_{cv}^aR_{c\to v})$",),
        message_v2=(
            r"$u_{v\to c}^a=B_v^a-A_{cv}^aR_{c\to v}$",
            r"$m_{v\to c}^{a,\mathrm{new}}=d\,m_{v\to c}^{a,\mathrm{old}}+(1-d)u_{v\to c}^a$",
        ),
        note_v1="Clip the prior, edge projection, and messages. Ties favor X, then Y, then Z; an initial candidate may stop.",
        note_v2="No global clip. Strict decision: I, then X, then Z, else Y. Complete one sweep before stopping.",
    ),
)


def _svg_math(expression: str) -> str:
    """Return self-contained vector math, with no browser-side dependency."""
    output = BytesIO()
    math_to_image(
        expression, output, format="svg", dpi=180,
        prop=FontProperties(family="STIXGeneral", size=18), color="#17222e",
    )
    source = "data:image/svg+xml;base64," + b64encode(output.getvalue()).decode("ascii")
    return f'<img src="{source}" alt="{escape(expression)}">'


def _html_cell(title: str, check: tuple[str, ...], belief: str,
               message: tuple[str, ...], note: str) -> str:
    check_math = "".join(f'<div class="equation">{_svg_math(eq)}</div>' for eq in check)
    message_math = "".join(f'<div class="equation">{_svg_math(eq)}</div>' for eq in message)
    return (
        f'<div class="column"><h3>{escape(title)}</h3>'
        f'<div class="step"><h4>Check update</h4>{check_math}</div>'
        f'<div class="step"><h4>Posterior</h4><div class="equation">{_svg_math(belief)}</div></div>'
        f'<div class="step"><h4>Outgoing message</h4>{message_math}</div>'
        f'<p class="note">{escape(note)}</p></div>'
    )


def build_html() -> None:
    blocks = []
    for item in COMPARISONS:
        blocks.append(
            f'<section><h2>{escape(item.title)}</h2><p class="subtitle">{escape(item.subtitle)}</p>'
            '<div class="pair">'
            + _html_cell("v1", CHECK_V1, item.belief_v1, item.message_v1, item.note_v1)
            + _html_cell("v2", CHECK_V2, item.belief_v2, item.message_v2, item.note_v2)
            + '</div></section>'
        )
    document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canonical BP numerical profiles: v1 and v2</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#fff;color:#17222e;font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1080px;margin:40px auto;padding:0 24px}h1{font-size:28px;letter-spacing:-.025em;margin:0 0 8px}
.notation{display:flex;align-items:center;gap:15px;flex-wrap:wrap;color:#4a5867;margin:0 0 30px}.notation img{height:24px;width:auto}
section{margin:0 0 34px}h2{font-size:21px;margin:0 0 3px}.subtitle{margin:0 0 13px;color:#4a5867}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}.column{border:1px solid #ccd5dd;border-radius:8px;padding:17px 18px 13px;min-width:0}
.column:nth-child(2){border-color:#8aafb1}.column h3{font-size:17px;margin:0 0 12px;color:#164f55}
.step{border-top:1px solid #e4e9ed;padding:10px 0}.step h4{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#5b6876;margin:0 0 7px}
.equation{overflow-x:auto;margin:4px 0}.equation img{display:block;max-width:none;height:auto;width:auto}.note{border-top:1px solid #e4e9ed;padding-top:10px;margin:3px 0 0;color:#465563;font-size:13px}
@media(max-width:760px){main{margin:22px auto;padding:0 15px}.pair{grid-template-columns:1fr}.column{padding:15px}}
@media print{main{max-width:none;margin:0;padding:0}section{break-inside:avoid}.column{padding:10px}.equation img{max-width:100%}}
</style></head><body><main>
<h1>Canonical BP: v1 and v2</h1>
<p class="notation">''' + _svg_math(PARAMETERS) + '''<span>The v1 check operator is ordered box-plus, clipped after each pair.</span>''' + _svg_math(CLIP) + '''</p>
''' + "\n".join(blocks) + '''
</main></body></html>
'''
    HTML.write_text(document, encoding="utf-8")


def _pdf_equation(fig: plt.Figure, x: float, y: float, expression: str) -> None:
    fig.text(x, y, expression, fontsize=13, color="#17222e", va="center")


def _pdf_column(fig: plt.Figure, x: float, version: str, check: tuple[str, ...],
                belief: str, message: tuple[str, ...], note: str) -> None:
    fig.add_artist(Rectangle((x, .115), .44, .655, transform=fig.transFigure,
                             facecolor="white", edgecolor="#ccd5dd", linewidth=.8))
    fig.text(x + .018, .735, version, fontsize=16, weight="bold", color="#164f55")
    for label, y in (("CHECK UPDATE", .675), ("POSTERIOR", .47), ("OUTGOING MESSAGE", .31)):
        fig.text(x + .018, y, label, fontsize=9, weight="bold", color="#5b6876")
    _pdf_equation(fig, x + .018, .625, check[0])
    _pdf_equation(fig, x + .018, .563, check[1])
    _pdf_equation(fig, x + .018, .415, belief)
    for index, equation in enumerate(message):
        _pdf_equation(fig, x + .018, .255 - .045 * index, equation)
    fig.text(x + .018, .17, fill(note, 68), fontsize=9.6,
             color="#465563", va="top", linespacing=1.25)


def build_pdf() -> None:
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "pdf.fonttype": 42})
    with PdfPages(PDF, metadata={"Title": "Canonical BP: v1 and v2",
                                 "Author": "survey_bp", "CreationDate": None, "ModDate": None}) as pages:
        for item in COMPARISONS:
            fig = plt.figure(figsize=(11.7, 8.3), facecolor="white")
            fig.text(.05, .93, item.title, fontsize=23, weight="bold", color="#17222e")
            fig.text(.05, .883, item.subtitle, fontsize=11, color="#4a5867")
            fig.text(.05, .835, PARAMETERS, fontsize=12, color="#4a5867")
            fig.text(.365, .835, "v1 check: ordered box-plus, clipped after each pair.",
                     fontsize=10, color="#4a5867")
            _pdf_equation(fig, .05, .792, CLIP)
            _pdf_column(fig, .05, "v1", CHECK_V1, item.belief_v1, item.message_v1, item.note_v1)
            _pdf_column(fig, .51, "v2", CHECK_V2, item.belief_v2, item.message_v2, item.note_v2)
            pages.savefig(fig)
            plt.close(fig)


if __name__ == "__main__":
    build_html()
    build_pdf()
    print(HTML)
    print(PDF)
