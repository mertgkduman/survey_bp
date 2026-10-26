# BP4 min-sum at the presentation scale and damping settings

This exploratory follow-up runs the requested two BP4 min-sum policies on the
local B1 and double-Gross matrices. Both use `T=1000`, physical code-capacity
depolarizing probability `p`, and decoder prior `p₀=p`. The vanilla policy has
Q8 scale `s=16` and damping `d=0`; the tuned-knob policy has `s=4` and `d=0.1`.
Both use flooding check updates and unscaled, unoffset min-sum (`α=1, β=0`).
The min-sum parameters are inferred because the excerpt does not state `α`
and `β` for its vanilla MS curve. Its published *tuned BP4* curve uses
sum-product; the tuned-knob min-sum arm here is a user-requested variation,
not a transcription of that curve.

The experimental Q8 adapter stores three log ratios per qubit-to-check edge,
compresses each into a commutation LLR, applies a syndrome-signed extrinsic
min-sum check update, and then forms four-Pauli hard decisions. It rounds each
public message to the nearest multiple of `1/s` (ties to even), clips at
`±127/s`, damps qubit-to-check messages, and stops at the first syndrome match.
The slides omit rounding order, damping target, tie rule, exact schedule,
graph realization, and decoder prior. This test does not invoke the separate
`affine_decoder` Python reference decoder.

## Results on identical errors

The stored sum-product (SP) arms and new min-sum (MS) arms were replayed with
the same code, physical `p`, seed, and shot count. The analyzer checked every
cross-run error SHA-256. Failures include a missing syndrome match or a
nontrivial logical residual; in these four MS arms, every failure lacked a
syndrome match. Intervals are exact two-sided 95% binomial intervals.

| Code, physical `p`, shots | Policy | Failures | LER (95% interval) | Mean iterations |
|---|---|---:|---:|---:|
| B1, 0.10, 200 | SP vanilla, `s=16,d=0` | 144/200 | 0.720 (0.652–0.781) | 725.3 |
| B1, 0.10, 200 | MS vanilla, `s=16,d=0` | 177/200 | 0.885 (0.832–0.926) | 887.3 |
| B1, 0.10, 200 | SP tuned knobs, `s=4,d=0.1` | 72/200 | 0.360 (0.294–0.431) | 365.6 |
| B1, 0.10, 200 | MS tuned knobs, `s=4,d=0.1` | 122/200 | 0.610 (0.539–0.678) | 614.4 |
| double-Gross, 0.08, 1,000 | SP vanilla, `s=16,d=0` | 159/1000 | 0.159 (0.137–0.183) | 163.8 |
| double-Gross, 0.08, 1,000 | MS vanilla, `s=16,d=0` | 244/1000 | 0.244 (0.218–0.272) | 253.6 |
| double-Gross, 0.08, 1,000 | SP tuned knobs, `s=4,d=0.1` | 55/1000 | 0.055 (0.042–0.071) | 59.9 |
| double-Gross, 0.08, 1,000 | MS tuned knobs, `s=4,d=0.1` | 81/1000 | 0.081 (0.065–0.100) | 87.4 |

The new tuned-knob MS arm rescues 60 and loses 5 B1 shots relative to vanilla
MS; on double-Gross it rescues 174 and loses 11. Against SP at the *same*
scale and damping, MS rescues/loses 2/35 (B1 vanilla), 10/60 (B1 tuned),
27/112 (double-Gross vanilla), and 17/43 (double-Gross tuned). Thus the
requested scale and damping change helps this min-sum implementation, but
min-sum is worse than sum-product at both tested settings. These comparisons
are paired observations, not an assertion that all possible MS parameter
settings are worse than SP.

The presentation reports vanilla MS LER 0.0079 for B1 at `p=0.10` and 0.00525
for double-Gross at `p=0.08`; both remain far below the local vanilla MS
results. The local MS run therefore does not explain or reproduce the source
gap. The source does not specify enough implementation details to isolate its
cause from these runs alone.

## Reproduction files

- Policies: [`../../decoders/bp4_vanilla_ms.json`](../../decoders/bp4_vanilla_ms.json)
  and [`../../decoders/bp4_ms_tuned_slide_knobs.json`](../../decoders/bp4_ms_tuned_slide_knobs.json).
- Run configurations: [`b1_minsum_configs.json`](b1_minsum_configs.json) and
  [`gross_minsum_configs.json`](gross_minsum_configs.json).
- Per-shot ledgers and summaries:
  [`B1`](b1_minsum_p010_n200_seed20261101/summary.json) and
  [`double-Gross`](gross_minsum_p008_n1000_seed20261031/summary.json).
- Audited counts and exact intervals: [`audited_rates.csv`](audited_rates.csv).
  Rescue/loss counts: [`paired_comparisons.csv`](paired_comparisons.csv).
- Comparison plot: [`minsum_vs_sumproduct.png`](minsum_vs_sumproduct.png)
  ([SVG](minsum_vs_sumproduct.svg)).

Rebuild the audit and plot with
`PYTHONPATH=src .venv/bin/python from_dr_pfister_presentetations/analyze_bp4_performance.py`.
