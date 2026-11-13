# Retrospective iteration-cutoff inference

The pinned MacKay v3 primary paper, PDF and TeX do not supply a numeric cutoff.
The user explicitly authorized inferring one from curve alignment. This folder
retains a retrospective calibration, not fresh source-reproduction evidence.

For the length-274 source unicycle arm, test per-hypothesis cutoffs
2/3/5/10/20/25/50/100/200/500/1000 against the five measured source ordinates.
Read the original ordered ledgers and verify their full SHA-256 digests.

A branch's first valid candidate is fixed once convergence occurs. When the
full-budget selected candidate equals the transmitted classical word, its
true-extra-bit branch's first convergence time determines exact success at
any smaller cap. At/after that time, the same candidate wins among a subset of
the original eligible candidates. Before that time, neither the un-converged
true branch nor the opposite-extra-bit branch can return that exact word.
For full nonconvergence, neither branch converges at any smaller cap. Other
original errors can change selection, so both branch candidates are replayed
with at most 1,000 iterations. A skipped competitor is replayed only when
needed to distinguish detected from undetected errors before the correct
branch's first convergence. No 88,200-iteration run is performed.

This yields exact classical outcome counts on the retained bank for the tested
caps. It does not produce fresh random samples. The original bank stopped at
20 large-budget quantum failures, so projected estimates are descriptive;
original stopping intervals cannot be transferred to the projected counts.
Original raw ledgers, manifests and outcomes are untouched. Only 148 short
branch replays were required, at caps <=1,000.

The equal-rate sum of squared log relative total-error discrepancies is smallest
at 100 (0.0351), followed by 50 (0.0868), then 200 (0.1823). These differences
are not a confidence interval for the historical cap; 50–100 is a plausible
range among tested values. The detected/undetected split at 100 is also roughly
balanced as in the source. Source ordinates are approximate vector extractions,
without original author sample counts. Numerical conventions and row ordering
could also affect alignment.

At 100 per hypothesis, retrospective classical rates are:

| X rate | Projected | Paper approximate |
| --- | ---: | ---: |
| .010 | 5.686e-6 | 6.699e-6 |
| .013 | 6.617e-5 | 7.075e-5 |
| .020 | .002331 | .002230 |
| .030 | .049784 | .048342 |
| .040 | .175439 | .180784 |

A new independent campaign uses T=100 for ordinary BP and Q-BP, and 100 per
unicycle hypothesis (200 total maximum). It is explicitly labeled inferred;
no recovered paper setting or source-faithful numerical identity is claimed.
The previous long-budget curves remain separately visible. Tuning and fresh
confirmation both use T=100, with original settings retained as comparators.

Re-analysis (requires original local raw ledgers):

```
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python data/reproductions/mackay-0304161-budget-calibration/infer.py
```
