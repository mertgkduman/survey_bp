# Length74 paper values

Inspected original arXiv sources v1 (April2003), v2 (May2003), v3 (February2004),
all embedded PostScript/EPS figure inventories, and the current42-page PDF.
The journal DOI page was unavailable; the negative finding is scoped to the
inspected primary versions, rather than a claim about unprovided author data.
Reproducible archive/member SHA256s are in paper-evidence.json.

The current PDF's Figure11 (printed page27) shows the length74 parity-check
matrix and construction table. Figure16 (printed page34) is the **length274**
error-rate curve. Figure17 (printed page35) summarizes multiple codes at a fixed
error target. Thus no source-supported length74 block-error ordinates exist at
p=.010/.013/.020/.030/.040 in these versions. Each requested value is explicitly
null/not_reported in the evidence receipt. The historical source.json referred
to Figure15; current PDF confirms Figure16. Frozen old source files are retained.

One genuine length74 performance reference can be extracted from Figure17:
**marginal p approximately .006818**, at the paper's convention of quantum
block-error target1e-4, represented by constituent classical block error5e-5.
The marker at vector coordinate(3651,1574) is the length74 point; its vertical
quantum rate agrees with18/74. The logarithmic axis calibrates .001 at x1601
and .01 at x4060. This is a single threshold summary, not five curve points.
No interpolation or fitted model is reported as paper measurement.

Primary sources: https://arxiv.org/pdf/quant-ph/0304161v3 and
https://arxiv.org/src/quant-ph/0304161v1 (also v2/v3). Figure member:
figs/QSUMMARYUBNM.ps. Re-extract with extract_paper_evidence.py and the three
original source archives; no simulations are involved.
