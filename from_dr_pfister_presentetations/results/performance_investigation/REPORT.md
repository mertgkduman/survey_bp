# BP4 performance investigation

**2026-10-26 follow-up:** The [reference comparison and matched numerical
ablations](REFERENCE_GAP_AUDIT.md) identify global `±25` clipping in the
canonical float64 profile as a major cause of local B1/double-Gross
nonconvergence. A reference-style, unclipped float64 diagnostic failed 0/200
B1 and 1/1000 double-Gross shots on matched errors; this is an implementation
of the supplied reference description, not a direct package replay. The
source-presentation fidelity questions below remain open.

## Question and verdict

The presentation's BP4 curves for B1 and double-Gross are far better than our
slide-like Q8 adaptation. That gap is real in matched local trials, but it is
**not evidence of a general error in the canonical floating point BP4
recurrence**. On an independent published code-capacity benchmark, the
canonical compiled decoder and the paper authors' C++ BP4 give identical
success and syndrome-validity outcomes on all 10,000 identical errors. The
public Python canonical kernel and the compiled kernel also return identical
corrections on 100 other matched errors. On the published toric code, BP4
substantially outperforms the local binary OMS baseline.

The unresolved issue is source fidelity on the two presentation codes. The
presentation does not supply its check matrices, executable BP4 kernel,
quantization order, damping target, or raw shot data. Our Q8 adaptation chooses
those omitted details explicitly; its failures cannot be assigned to one
specific omitted detail. Tuning the BP4 prior and damping greatly improves the
local outcome, yet the performance remains far from the supplied curves.

## Protocol

All local experiments sample independent code-capacity depolarizing errors
with `P(I)=1-p` and `P(X)=P(Y)=P(Z)=p/3`. The same generated errors are sent to
every decoder within a run, and runs with the same code, seed, `p`, and shot
count use identical error vectors (checked by per-shot SHA-256 when compared).
The independent evaluator counts either an unmatched syndrome or a nontrivial
logical residual as a failure. All B1 and double-Gross arms have `T=1000`;
the literature toric experiment has `T=25`. Binary OMS uses separate X and Z
graphs with the explicitly recorded local settings. The four-state Q8 adapter
uses round-to-even quantization after each public message, signed range
`±127/s`, flooding unless otherwise labeled, and variable-to-check damping.
Those are implementation choices, not confirmed details of the presentation.

The B1/double-Gross screens were exploratory. We chose a promising double-Gross
policy from 80 common errors, tested several variants on a distinct 1,000-error
set, then froze `s=4, d=0.2, p₀=0.2` for a further 3,000-error confirmation.
B1's 40-error screen selected `s=4, p₀=0.2, d∈{0.3,0.4}` for a fresh 300-error
confirmation. The confirmation set alone is used to assess whether the chosen
policy beats binary BP; the screen is not counted as independent evidence.

## Presentation-code results

The double-Gross confirmation at physical `p=0.08`, 3,000 paired errors:

| Decoder | Failures | LER | Exact 95% interval | Mean iterations |
|---|---:|---:|---:|---:|
| Binary OMS | 100/3000 | 0.0333 | 0.0272–0.0404 | 28.9 equivalent X+Z pairs |
| Q8 BP4, slide-like `s=4,d=0.1,p₀=p` | 185/3000 | 0.0617 | 0.0533–0.0709 | 66.5 |
| Q8 BP4, screened `s=4,d=0.2,p₀=0.2` | 79/3000 | 0.0263 | 0.0209–0.0327 | 32.2 |

The optimized BP4 rescued 69 binary failures and lost 48 binary successes;
the two-sided exact paired p-value is 0.064. This confirmation supports a
large improvement over the slide-like local BP4 policy. It does not resolve a
BP4-versus-binary difference at the conventional 5% level. The supplied slide
has tuned BP4 LER 0.00077 at this `p`, about 34 times lower than the optimized
local rate and about 80 times lower than the slide-like local rate. The slide
binary rate 0.03153 is close to the local binary confirmation rate.

B1 confirmation at physical `p=0.10`, 300 new paired errors:

| Decoder | Failures | LER | Exact 95% interval | Mean iterations |
|---|---:|---:|---:|---:|
| Binary OMS | 13/300 | 0.0433 | 0.0233–0.0730 | 51.2 equivalent X+Z pairs |
| Q8 BP4, slide-like `s=4,d=0.1,p₀=p` | 113/300 | 0.3767 | 0.3216–0.4342 | 381.8 |
| Q8 BP4, screened `s=4,d=0.3,p₀=0.2` | 52/300 | 0.1733 | 0.1322–0.2210 | 182.5 |
| Q8 BP4, screened `s=4,d=0.4,p₀=0.2` | 42/300 | 0.1400 | 0.1028–0.1845 | 150.6 |

The best screened B1 arm rescued 9 binary failures and lost 38 binary
successes (two-sided exact paired p=0.0000249). It still fails about 438 times
as often as the supplied slide's tuned BP4 rate 0.00032. The slide binary
rate 0.04571 is close to the local binary rate. The initial 200-error transfer
test on another seed gave binary 10/200, slide-like Q8 BP4 72/200, and
`s=4,d=0.2,p₀=0.2` BP4 32/200. The small B1 screen showed that `d=0.3`
and `0.4` were promising relative to `d=0.2`, while `p₀=0.4` and Q8 scale 2
were disastrous (40/40 failures each). These are screen observations, not
general tuning advice.

The canonical compiled **floating point** BP4 kernel was also run on the
identical 300 B1 errors, with `T=1000` and its default numerical clip `±25`:
it failed 202/300 when initialized at `p₀=0.1`, and 145/300 at `p₀=0.2`.
Thus the B1 gap is present without Q8 quantization; the improved Q8 result
reflects a code-specific numerical/policy sweet spot rather than restoration
of an otherwise good floating point B1 curve. This is a performance finding,
not evidence that the floating point recurrence violates BP4 equations: its
independent toric replay agrees exactly with the authors' implementation.

Across the B1 and double-Gross local runs, nearly all BP4 failures are
nonconvergence to a syndrome-valid correction. The gross confirmation had
zero valid-syndrome logical failures in either BP4 arm; binary had three.
That identifies the immediate failure mode but not its sole cause.

### Check-row representation

The local double-Gross construction has 144 X-check rows and 144
Z-check rows, with rank 138 in each half. We kept the first independent rows
of each half and replayed the exact same 1,000 errors as the all-row holdout.
The binary failure count rose from 35 to 74; the slide-like Q8 BP4 count rose
from 55 to 78; and the screened `s=4,d=0.2,p₀=0.2` BP4 count rose from 21 to
36. Removing these 12 dependent checks therefore worsened both families on
this code. The original presentation's row selection is unknown, but this
simple full-rank transformation does not close its BP4 gap.

For B1 the local graph has 441 X-check and 441 Z-check rows, each of rank 429.
On the first 100 errors of the 200-error transfer set, independent-row
selection increased binary failures from 5 to 10, vanilla Q8 BP4 failures
from 70 to 80, slide-like tuned BP4 failures from 37 to 46, and the
`s=4,d=0.2,p₀=0.2` BP4 failures from 9 to 18. The same errors were verified
by their SHA-256 hashes. A prior 200-shot independent-row attempt was
terminated externally before a complete result; its empty ledger and exit
status are retained as failed-run evidence. The completed 100-shot retry is
the reported row-basis comparison. These row-selection probes are diagnostics,
not a search over all Tanner graph transformations.

## Independent literature control

[Miao et al., IEEE Access 2025, Fig. 8](https://publikationen.bibliothek.kit.edu/1000179617/157326592)
evaluate plain flooding BP4 on toric codes under code-capacity depolarizing
noise. Their distributed [C++ implementation](https://github.com/kit-cel/Quantum-Neural-BP4-demo)
and full-rank `[[32,2,4]]` toric matrix are pinned in
[`external/miao_2025/`](../../external/miao_2025/README.md). We used the
paper's 25 iterations and default decoder initialization `epsilon₀=0.1`,
physical `p=0.075`, and 10,000 new errors. A replay hook sets each error in
the native C++ decoder without changing its BP or evaluator logic.

| Decoder | Failures / 10,000 | Invalid syndrome | Valid-syndrome logical |
|---|---:|---:|---:|
| Native authors' C++ plain BP4 | 1,591 | 1,412 | 179 |
| Canonical compiled float64 BP4, source-like clip `±60` | 1,591 | 1,412 | 179 |
| Canonical compiled float64 BP4, default clip `±25` | 1,591 | 1,412 | 179 |
| Local Q8 BP4, `s=4,d=0` | 1,644 | 1,482 | 162 |
| Local binary OMS | 3,617 | 3,489 | 128 |

The native C++ and the canonical source-like BP4 agree on *every one* of the
10,000 success and syndrome-validity flags, not just the totals. Their LER is
0.1591, with exact 95% binomial interval about 0.1520–0.1664. The local
binary baseline is 0.3617. The paper's BP2 curve is from a separately sampled
independent-XZ channel and re-scaled by `2/3`, so we use it only for
qualitative context; the matched binary numbers above are our own comparison.
The paper provides a plot and a 300-frame-error stopping rule, not raw counts
for this exact point. Our 10,000-shot native replay is the stronger executable
cross-check, not a claim of exact figure reproduction.

This agrees with the literature's more limited conclusion: BP4 can exploit
Pauli correlation, but plain BP4 is sensitive to graph cycles and degeneracy.
[Kuo and Lai, npj Quantum Information 2022](https://doi.org/10.1038/s41534-022-00623-2)
report poor conventional BP4 performance on some highly degenerate codes and
improvements from memory BP4. Thus a universal BP4-over-BP2 guarantee is not
established by the literature.

## Evidence and remaining boundary

- `events.jsonl` in every run records shot ID, error SHA-256, outcome, syndrome
  validity, iterations, and elapsed time. `summary.json` pins settings, seed,
  counts, and a SHA-256 digest of the complete ledger.
- `analyze_bp4_performance.py` independently recounts every ledger, checks
  paired error hashes, verifies all 10,000 native outcomes, and writes
  [`audited_rates.csv`](audited_rates.csv),
  [`paired_comparisons.csv`](paired_comparisons.csv), and
  [`confirmation_comparison.png`](confirmation_comparison.png).
- The exact Pauli commutation/check update was previously checked against a
  four-state parity oracle (192 cases), and the canonical Python/compiled
  kernels returned identical candidates on 100 toric errors. These checks
  target different layers; none prove every Q8 numerical convention matches
  the presentation.

The defensible finding is that the canonical BP4 recurrence is sound on an
independent published code and that Q8 policy/graph choices have large effects
on the two presentation codes. The presentation reproduction remains open
until its precise matrix and implementation details or raw decoder outputs
become available. Treat the recorded presentation curves and local adaptation
as distinct evidence, and retain the failed and inconclusive runs.
