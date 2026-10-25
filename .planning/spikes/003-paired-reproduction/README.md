---
spike: 003
idea: pfister-slide-bp-reproduction
name: paired-reproduction
type: standard
validates: "Given qualified code and policy variants, when shared errors are decoded, then measured LER and work can be compared with the slide"
verdict: PARTIAL
related: [001-slide-evidence, 002-policy-kernel]
tags: [simulation, statistics]
---

# Spike 003: Paired reproduction

## What This Validates

The same depolarizing error samples can be decoded by all four arms, with per-shot provenance, failure counts, BP4-equivalent work, and rescue/loss counts compared to the reported rates.

## How to Run

`PYTHONPATH=src .venv/bin/python from_dr_pfister_presentetations/run_reproduction.py --code double_gross --p 0.08 --shots 100 --seed 20261027`

Then run `.venv/bin/python from_dr_pfister_presentetations/summarize_results.py` and `.venv/bin/python from_dr_pfister_presentetations/plot_results.py`.

## What to Expect

The first command writes one immutable JSON summary and per-shot JSONL ledger under `from_dr_pfister_presentetations/results/`. The summary script makes exact two-sided 95% binomial intervals. The plot script makes `plots/pilot_vs_source.png`.

## Observability

Each shot retains an error SHA-256, arm outcome, syndrome validity, convergence, iteration count, BP4-equivalent work, and elapsed seconds. The summary retains ledger SHA-256, per-arm failures/work percentiles, and paired BP4 rescue/loss counts. Timing is exploratory because Python call overhead and machine scheduling are not controlled.

## Investigation Trail

1. A two-shot `T=10` smoke run verified execution; it is excluded from the `T=1000` comparison table.
2. Three 100-shot `T=1000` pilots used shared errors at B1 p=0.10 and double-Gross p=0.08 and 0.12.
3. Tuned binary OMS rates were 0.06, 0.03, and 0.49, close to slide rates 0.04571, 0.03153, and 0.4898. These small pilots cannot prove statistical agreement.
4. Local vanilla/tuned BP4 rates were 0.75/0.40, 0.15/0.07, and 0.57/0.36, respectively, far above the slide points. Exact 95% intervals and raw counts are in `pilot_summary.csv`.
5. Float64 BP4 diagnostics were 15/20 failures on B1 p=0.10 and 45/100 on double-Gross p=0.12. A variable-serial Q8 diagnostic at double-Gross p=0.08 gave 11/100 vanilla and 5/100 tuned failures; schedule alone did not close the gap.

## Results

**PARTIAL.** The paired, auditable comparison works; the current BP4 implementation/assumptions do not reproduce the reported curves. The next decisive input is the source BP4 decoder or a full specification of its schedule, message representation, quantization, damping, and stopping. Increasing Monte Carlo N now would measure the current mismatch more precisely without addressing it.
