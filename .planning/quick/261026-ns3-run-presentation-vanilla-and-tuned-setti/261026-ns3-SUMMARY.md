---
quick_id: 261026-ns3
date: 2026-10-26
status: verified
---

# BP4 min-sum presentation-knob follow-up

Added an explicit min-sum switch to the experimental Q8 BP4 screen runner and
ran the requested vanilla (`T=1000,s=16,d=0`) and tuned-knob
(`T=1000,s=4,d=0.1`) settings. The check update is unscaled, unoffset min-sum
(`α=1,β=0`), an explicit inference because the presentation excerpt does not
specify these values for vanilla min-sum. The source's tuned BP4 curve is
sum-product; the tuned-knob min-sum arm is a new adaptation.

On matched B1 errors at `p=0.10`, min-sum failed 177/200 vanilla and 122/200
tuned. On matched double-Gross errors at `p=0.08`, it failed 244/1000 vanilla
and 81/1000 tuned. Sum-product on the same errors failed 144/200 and 72/200
for B1, 159/1000 and 55/1000 for double-Gross, respectively. Per-shot
rescues/losses and exact intervals are in the report and audited CSVs.

Evidence is in `from_dr_pfister_presentetations/results/performance_investigation/`:
`MINSUM_FOLLOWUP.md`, two run config files, two event ledgers with summaries,
`audited_rates.csv`, `paired_comparisons.csv`, and `minsum_vs_sumproduct.png/svg`.
Policies are in `from_dr_pfister_presentetations/decoders/`.

Verification: performance analyzer recounted 68 arms and 70 paired comparisons,
verified cross-run error hashes, and reproduced all 10,000 native replay flags;
`verify_spike.py` passed; ten quaternary kernel tests passed; Python compilation
and `git diff --check` passed. No source-curve agreement is claimed.
