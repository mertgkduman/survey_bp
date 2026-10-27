"""Build a one-page, vector-typeset comparison of the two BP profiles."""

from __future__ import annotations

from base64 import b64encode
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

NOTATION = (
    r"$\operatorname{clip}_{L}(x)=\max(-L,\min(L,x)),"
    r"\qquad\epsilon=10^{-10},\qquad d=0.1$"
)
CHI = r"$\chi_{cv}(a)=1$"
EQUATIONS = (
    (
        "Sum-product check",
        (
            r"$a\boxplus b=2\operatorname{atanh}[\tanh(a/2)\tanh(b/2)]$",
            r"$\hat m_{c\to v}^{(t+1)}=(-1)^{s_c}"
            r"\underset{v'\in\partial c\setminus v}{\boxplus_{25}}\,m_{v'\to c}^{(t)}$",
        ),
        (
            r"$q_{cv}^{(t)}=(-1)^{s_c}\prod_{v'\in\partial c\setminus v}"
            r"\tanh(m_{v'\to c}^{(t)}/2)$",
            r"$\hat m_{c\to v}^{(t+1)}=2\operatorname{atanh}"
            r"[\operatorname{clip}_{1-\epsilon}(q_{cv}^{(t)})]$",
        ),
    ),
    (
        "Binary variable",
        (
            r"$m_v^{(t+1)}=\operatorname{clip}_{25}"
            r"(\lambda_v+\sum_{c\in\partial v}\hat m_{c\to v}^{(t+1)})$",
            r"$m_{v\to c}^{(t+1)}=\operatorname{clip}_{25}"
            r"(m_v^{(t+1)}-\hat m_{c\to v}^{(t+1)})$",
        ),
        (
            r"$m_v^{(t+1)}=\lambda_v+\sum_{c\in\partial v}"
            r"\hat m_{c\to v}^{(t+1)}$",
            r"$m_{v\to c}^{(t+1)}=d\,m_{v\to c}^{(t)}+(1-d)"
            r"(m_v^{(t+1)}-\hat m_{c\to v}^{(t+1)})$",
        ),
    ),
    (
        "BP4 variable",
        (
            r"$m_v^{a,(t+1)}=\operatorname{clip}_{25}"
            r"(\lambda_v^a+\sum_{c\in\partial v}\chi_{cv}(a)"
            r"\hat m_{c\to v}^{(t+1)})$",
            r"$m_{v\to c}^{a,(t+1)}=\operatorname{clip}_{25}"
            r"(m_v^{a,(t+1)}-\chi_{cv}(a)\hat m_{c\to v}^{(t+1)})$",
        ),
        (
            r"$m_v^{a,(t+1)}=\lambda_v^a+\sum_{c\in\partial v}"
            r"\chi_{cv}(a)\hat m_{c\to v}^{(t+1)}$",
            r"$m_{v\to c}^{a,(t+1)}=d\,m_{v\to c}^{a,(t)}+(1-d)"
            r"(m_v^{a,(t+1)}-\chi_{cv}(a)\hat m_{c\to v}^{(t+1)})$",
        ),
    ),
)

NOTES = (
    "The subscript 25 on box-plus means an ordered fold with inputs and each pairwise result clipped to magnitude 25. BP4 may stop at iteration zero; nonidentity ties favor X, then Y, then Z.",
    "Only the check product is clamped at magnitude 1 - epsilon. Finite priors and messages have no global clip. BP4 completes one sweep before stopping and uses the strict I, X, Z, else Y decision rule.",
)


def _svg(expression: str) -> str:
    output = BytesIO()
    math_to_image(
        expression, output, format="svg", dpi=180,
        prop=FontProperties(family="STIXGeneral", size=14.5), color="#182633",
    )
    source = "data:image/svg+xml;base64," + b64encode(output.getvalue()).decode("ascii")
    return f'<img src="{source}" alt="{escape(expression)}">'


def build_html() -> None:
    columns = []
    for index, version in enumerate(("v1", "v2")):
        groups = []
        for label, left, right in EQUATIONS:
            equations = left if index == 0 else right
            math = "".join(f'<div class="equation">{_svg(eq)}</div>' for eq in equations)
            groups.append(f'<section><h3>{escape(label)}</h3>{math}</section>')
        columns.append(
            f'<div class="column"><h2>{version}</h2>' + "".join(groups)
            + f'<p class="note">{escape(NOTES[index])}</p></div>'
        )
    document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canonical BP: v1 and v2</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#fff;color:#182633;font:14px/1.42 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1120px;margin:28px auto;padding:0 24px}h1{font-size:27px;margin:0 0 6px}p{margin:0}
.intro{color:#4b5a69;margin:0 0 11px}.notation{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:0 0 20px;color:#4b5a69}
.notation img{height:23px;width:auto}.inline-math{display:inline-block;vertical-align:middle;height:19px;width:auto}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}.column{border:1px solid #cbd5dd;border-radius:7px;padding:14px 17px;min-width:0}
.column:nth-child(2){border-color:#8daeb1}h2{font-size:18px;color:#15545a;margin:0 0 9px}
section{border-top:1px solid #e5eaee;padding:9px 0}h3{font-size:11px;letter-spacing:.065em;text-transform:uppercase;color:#566775;margin:0 0 6px}
.equation{overflow-x:auto;margin:4px 0}.equation img{display:block;max-width:100%;height:auto;width:auto}
.note{border-top:1px solid #e5eaee;padding-top:10px;color:#4b5a69;font-size:12px}
.footer{color:#4b5a69;font-size:12px;margin-top:11px}
@media(max-width:780px){main{margin:20px auto;padding:0 14px}.pair{grid-template-columns:1fr}.column{padding:13px}}
@media print{main{max-width:none;margin:0;padding:0}.column{break-inside:avoid}}
</style></head><body><main>
<h1>Canonical BP: v1 and v2</h1>
<p class="intro">Flooding sum-product for binary BP and four-state BP4. BP4 check inputs are commute/anticommute projections of Pauli messages.</p>
<p class="notation">''' + _svg(NOTATION) + '''<span>For BP4, ''' + _svg(CHI).replace('<img ', '<img class="inline-math" ', 1) + ''' when Pauli a anticommutes with the check label at v.</span></p>
<div class="pair">''' + "".join(columns) + '''</div>
<p class="footer">Binary hard decision: error bit 1 when the posterior LLR is negative; exact zero selects 0.</p>
</main></body></html>
'''
    HTML.write_text(document, encoding="utf-8")


def build_pdf() -> None:
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "pdf.fonttype": 42})
    with PdfPages(PDF, metadata={"Title": "Canonical BP: v1 and v2",
                                 "Author": "survey_bp", "CreationDate": None, "ModDate": None}) as pages:
        fig = plt.figure(figsize=(11.7, 8.3), facecolor="white")
        fig.text(.05, .944, "Canonical BP: v1 and v2", fontsize=23, weight="bold", color="#182633")
        fig.text(.05, .900, "Flooding sum-product for binary BP and four-state BP4.", fontsize=10.5, color="#4b5a69")
        fig.text(.05, .864, NOTATION, fontsize=12.5, color="#182633")
        fig.text(.05, .833, "BP4 check inputs are commute/anticommute projections;", fontsize=9.4, color="#4b5a69")
        fig.text(.505, .833, CHI + " when a anticommutes with the local check Pauli.", fontsize=9.4, color="#4b5a69")
        for index, (x, version) in enumerate(((.05, "v1"), (.51, "v2"))):
            fig.add_artist(Rectangle((x, .105), .44, .695, transform=fig.transFigure,
                                     facecolor="white", edgecolor="#cbd5dd", linewidth=.8))
            fig.text(x + .018, .764, version, fontsize=17, weight="bold", color="#15545a")
            for (label, left, right), label_y, first_y, second_y in zip(
                EQUATIONS, (.711, .518, .350), (.670, .478, .310), (.622, .428, .252), strict=True,
            ):
                first, second = (left if index == 0 else right)
                fig.text(x + .018, label_y, label.upper(), fontsize=8.5, weight="bold", color="#566775")
                fig.text(x + .018, first_y, first, fontsize=12.5, color="#182633", va="center")
                fig.text(x + .018, second_y, second, fontsize=12.5, color="#182633", va="center")
            fig.text(x + .018, .186, fill(NOTES[index], 74), fontsize=9.2,
                     color="#4b5a69", va="top", linespacing=1.25)
        fig.text(.05, .065, "Binary decision: bit 1 iff posterior LLR < 0; exact zero selects 0.",
                 fontsize=9.2, color="#4b5a69")
        pages.savefig(fig)
        plt.close(fig)


if __name__ == "__main__":
    build_html()
    build_pdf()
    print(HTML)
    print(PDF)
