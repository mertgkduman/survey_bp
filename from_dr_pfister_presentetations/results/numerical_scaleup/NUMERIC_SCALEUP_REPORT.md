# Float64 BP numerical scale-up

## Question and experimental boundary

The project's frozen BP4 float64 v1 profile clips priors, edge projections,
check messages, posteriors, and variable messages at ±25. We screened the
reference-style direct tanh-product check, stable box-plus with several final
check caps, and a truly uncapped box-plus check. We applied the analogous
policies to binary SPA. The screen used paired errors on B1 at physical
depolarizing `p=0.10` (200 shots, seed 20261101) and double-Gross at `p=0.08`
(1,000 shots, seed 20261031). Policy selection preceded new-seed holdouts.

All B1 and double-Gross holdouts use decoder `p0=p`, perfect syndromes,
`T=1000`, and identical sampled four-Pauli errors across arms within a run.
For binary decoding, each component's prior is `2p0/3`. A block fails when
the correction either misses the syndrome (Type I) or matches the syndrome
but leaves a nontrivial logical residual (Type II). Stabilizer-equivalent
corrections count as successes. Binary work is `(X iterations + Z iterations)/2`.
The CSV files `points.csv` and `pairs.csv` are derived from SHA-256 checked
per-shot ledgers; intervals are exact two-sided 95% binomial intervals and
paired p-values are exact conditional McNemar tests.

The initial BP4 screens made the cap distinction visible before holdout:

| Screen policy | B1 failures / 200 | double-Gross failures / 1,000 |
|---|---:|---:|
| direct product, ε=1e-10, d=0 | 0 | 1 |
| direct product, ε=1e-12, d=0 | 0 | 1 |
| box-plus, check cap 25, d=0 | 0 | 1 |
| box-plus, check cap 50, d=0 | 0 | 1 |
| box-plus, truly no check cap, d=0 | 19 | 17 |
| direct product, ε=1e-10, d=0.1 | 0 | 0 |
| box-plus, no cap, d=0.1 | 0 | 2 |
| frozen float64 BP4 v1 | 155 | 116 |
| slide-knob Q8 BP4 | 72 | 55 |

A follow-up screen of box-plus cap 100, 1,000, and 1,000,000 at `d=0`
gave 1, 1, and 2 failures on the same 1,000 double-Gross shots. Cap 25
and 50 with `d=0.1` each gave zero. The later holdouts, rather than these
small selection screens, determine the reported performance estimates.

## Held-out BP4 results

| Code, physical p | Policy | Failures / N | LER | Mean BP4 work |
|---|---|---:|---:|---:|
| B1, 0.10 | product, ε=1e-10, V2C d=0.1 | 8 / 20,000 | 0.00040 | 12.08 |
| B1, 0.10 | product, ε=1e-10, d=0 | 19 / 20,000 | 0.00095 | 31.89 |
| B1, 0.10 | box-plus, final check cap 25, d=0.1 | 12 / 20,000 | 0.00060 | 12.25 |
| B1, 0.10 | box-plus, no check cap, d=0.1 | 46 / 20,000 | 0.00230 | 13.73 |
| B1, 0.12 | selected product, d=0.1 | 35 / 5,000 | 0.00700 | 27.21 |
| double-Gross, 0.08 | selected product, d=0.1 | 15 / 20,000 | 0.00075 | 6.86 |
| double-Gross, 0.08 | box-plus, cap 25, d=0.1 | 17 / 20,000 | 0.00085 | 6.83 |
| double-Gross, 0.08 | box-plus, no cap, d=0.1 | 48 / 20,000 | 0.00240 | 8.12 |
| double-Gross, 0.10 | selected product, d=0.1 | 75 / 5,000 | 0.01500 | 25.04 |
| double-Gross, 0.10 | box-plus, cap 25, d=0.1 | 77 / 5,000 | 0.01540 | 24.92 |
| double-Gross, 0.10 | box-plus, no cap, d=0.1 | 99 / 5,000 | 0.01980 | 28.59 |

The selected BP4 product check has **no hard check cap**. It moves a product
to `sign(product)*(1-1e-10)` only if floating point arithmetic reaches
exactly ±1 before `atanh`; it does not clamp merely near unity. There is no
global clip on prior, posterior, or V2C. The hard decision uses the strict
I, X, Z, else Y ladder. Damping weights the *old V2C message* by 0.1.
This exact-unity condition was caught during production qualification: an
earlier attempted v2 implementation clamped all products near unity and
diverged from the measured experimental recurrence. It was corrected before
promotion.

The presentation's tuned BP4 points are B1 `0.00032` at `p=0.10`,
double-Gross `0.00077` at `p=0.08`, and double-Gross `0.01505` at `p=0.10`.
The selected local estimates (0.00040, 0.00075, 0.01500) are close, and the
presentation values lie within the corresponding local exact 95% intervals.
Mean work 12.08 on B1 and 6.86 on double-Gross is also close to the slide's
roughly 12 and 6.7 BP4 iterations. At B1 `p=0.12`, however, the local
estimate `0.00700` (95% interval `0.00488–0.00972`) is below the slide's
`0.0112`. This is a **partial curve match**, not a source-faithful Q8
reproduction; the presentation used signed Q8 messages with scale 4, while
this selected policy is float64.

The selected BP4 arm's failures split into Type I / Type II as follows:
B1 `p=0.10`: 8/0; B1 `p=0.12`: 35/0; double-Gross `p=0.08`: 14/1;
double-Gross `p=0.10`: 73/2. The binary SPA v2 split is 94/0 on B1 and
218/3 on double-Gross. All rates in the tables are block logical error rates
with every attempted shot in the denominator.

The selected arm's work tail remains visible in the ledgers: B1 `p=0.10`
has p99/p99.9 about 48/99 iterations; double-Gross `p=0.08` has 28/267;
B1 `p=0.12` has 342/1000. These percentiles describe only the sampled
shots; rarer events are outside their resolution.
On paired B1 `p=0.10` errors, damping changed the selected product check
from 19 to 8 failures (17 rescues, 6 losses; exact p=0.0347), reduced mean
work from 31.89 to 12.08 iterations, and reduced p99 work from 259 to 48.

On double-Gross `p=0.08`, the uncapped box-plus variant lost all 33 shots
discordant with the selected product variant (exact paired p=2.33e-10).
On B1 `p=0.10`, the uncapped variant had 39 losses and one rescue
(p=7.46e-11).
The cap-25 box-plus variant differed by only three rescues and one loss
(p=0.625). The screen also showed that truly uncapped undamped box-plus was
worse than capped updates on both codes. Removing all check safeguards is
therefore not the winning numerical policy here.

## Held-out binary comparison

| Code, physical p | Binary decoder | Failures / N | Mean BP4-equivalent work |
|---|---|---:|---:|
| B1, 0.10 | float64 SPA v2 product, V2C d=0.1 | 94 / 2,000 | 43.77 |
| B1, 0.10 | float64 SPA v1, global ±25 | 158 / 2,000 | 98.79 |
| B1, 0.10 | tuned Q8 OMS | 91 / 2,000 | 49.49 |
| double-Gross, 0.08 | float64 SPA v2 product, V2C d=0.1 | 221 / 5,000 | 31.62 |
| double-Gross, 0.08 | float64 SPA v1, global ±25 | 262 / 5,000 | 41.88 |
| double-Gross, 0.08 | tuned Q8 OMS | 158 / 5,000 | 28.87 |

On paired double-Gross errors, binary SPA v2 rescued 50 v1 failures and lost
9 v1 successes (p=5.26e-8). On B1 it rescued 71 and lost 7
(p=1.93e-14). The tuned Q8 OMS remains better on double-Gross: it rescued
68 SPA-v2 failures and lost 5 SPA-v2 successes (p=3.42e-15). On B1 the
SPA-v2 versus Q8 OMS difference is unresolved (15 rescues, 18 losses,
p=0.728). The presentation's tuned binary values, `0.04571` on B1 and
`0.03153` on double-Gross, are close to local Q8 OMS (`0.0455`, `0.0316`).

## Independent small-code control and limitations

On a toric `[[32,2,4]]` code at physical `p=0.075`, decoder `p0=0.10`, and
`T=25`, BP4 v2 with V2C damping had 1,489/10,000 failures; frozen v1 had
1,560/10,000. There were 119 paired rescues and 48 losses (p=3.83e-8).
Undamped v2 and v1 both had 1,560 failures on these shots, so this control
supports the damping choice but does not isolate a clipping benefit on that
code.

The slide omits raw trial counts for ordinary curve points, Q8 rounding order,
and precise damping target. The local slide-Q8 BP4 policy remains far above
the shown BP4 curves; near agreement from float64 must not be presented as
verification of the slide's Q8 implementation. Exact-zero decoder priors
remain unsupported by the canonical LLR API, though all tested depolarizing
priors are strictly positive. Per-shot elapsed times are retained, but their
values are machine and implementation dependent and are not compared with
the presentation's timing baseline.

## Promotion and reproducibility

`quaternary-bp4-f64-v2` is now the default of direct canonical scalar BP4 and
its compiled graph, using the selected float64 recurrence. The frozen
`quaternary-bp4-f64-v1` profile remains explicitly selectable; existing public
v1 manifest execution and replay paths are pinned to it. Binary
`binary-spa-flooding-f64-v2` is an explicitly selectable canonical SPA profile
for direct one-shot and compiled execution. Existing public binary policy sessions
keep their frozen v1 default, and tuned Q8 OMS remains a separate check rule.

Rebuild the derived tables and plot with
`PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/analyze_numeric_scaleup.py`.
Run the algebraic and experimental qualification with
`PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/verify_numeric_sweep.py`.
Raw configurations, event ledgers, and SHA-256 summaries are in this folder;
the figure is `bp4_heldout_vs_presentation.png` (also PDF).

### Verification record

The promoted compiled kernels reproduced every retained iteration and outcome
field for all selected held-out arms: 50,000 BP4 shots (B1 20,000 at `p=.10`,
B1 5,000 at `p=.12`, double-Gross 20,000 at `p=.08`, and double-Gross 5,000
at `p=.10`) and 7,000 binary SPA shots (B1 2,000 and double-Gross 5,000).
`verify_numeric_sweep.py`, `verify_spike.py`, and the ledger audit in
`analyze_numeric_scaleup.py` passed. With `OMP_NUM_THREADS=1`, the canonical
test suite passed 754 tests with one skip, excluding two unrelated modules
that require `/tmp/phase11-mbp4.pdf` and
`/tmp/phase10-asced-native/source/quantum_asced`, which are unavailable in
this workspace. The focused new BP4/binary numerical tests passed 29/29.
