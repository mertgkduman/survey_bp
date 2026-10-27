# Why the experimental Q8 BP4 min-sum arm fails

## Verdict

The dominant observed failure is a **joint numerical-policy interaction** in
the experimental Q8 adapter: it saturates three identity-referenced V2C
messages at `±127/16`, then its commutation projection clips the *two
log-sum-exp operands separately* before subtracting them. The latter is not
equivalent to clipping the projected LLR. On matched errors, removing either
site alone helped little; removing both restored syndrome convergence in the
bounded diagnostic below. This identifies a local mechanism, not the unknown
implementation of the source presentation's Q8 MS curve.

The check update itself uses the syndrome sign, excludes the destination edge,
and takes the minimum magnitude. We found no sign or exclusion error in that
loop. The initial MS message is nevertheless 2.5 times the SP message on these
weight-six checks at B1 `p=0.10`, which makes the narrow V2C range especially
consequential. The previous explanation that unscaled min-sum alone explains
the large error rate was too strong.

## Source inspection

- [`policy_kernel.py`](../../policy_kernel.py) rounds and saturates each of
  the three V2C identity-referenced LLRs at initialization and again after
  every variable update; it also quantizes projected scalar and C2V messages.
- [`compiled.py`](../../../src/bp_registry/quaternary/compiled.py) implements
  `_commutation_llr` as `clip(clip(commute)-clip(anti))`. A valid projection is
  `clip(commute-anti)` when a final scalar clip is required. The operands are
  internal log masses, not individual edge messages.
- For an X-labeled edge with `x=y=z=-7.9375`, the exact commuting and
  anticommuting log masses are `7.937857` and `8.630647`. Their difference is
  `-0.692790`, but the existing function returns **zero** because it clips
  both masses to `7.9375` first.

The first-sweep min-sum scalar message is `2.625` on B1 at `p=0.10`, versus
`1.0625` from SP under the same scale. On double-Gross at `p=0.08`, the values
are `2.875` and `1.3125`. The bound is `7.9375`; the recorded first-sweep
counts show that almost half or more of all three-component V2C proposals
already exceed it. This is a direct property of the selected local Q8 policy.

## Matched ablation

All arms use the same physical errors, `p0=p`, flooding, unscaled/unoffset MS,
`d=0`, `s=16`, and `T=1000`. They retain the original Q8 quantization of
scalar projected and C2V messages. `exact_projection_only` forms the full
log-sum-exp difference before scalar quantization. `unbounded_v2c_only`
retains the original projection but removes Q8 rounding/saturation of the
three internal V2C coordinates. `both_changes` applies both modifications;
it is a **diagnostic hybrid**, not an 8-bit source reproduction.

| Code, physical p, N | Original Q8 MS | Exact projection only | Unbounded V2C only | Both changes | First-sweep V2C proposals outside Q8 range |
|---|---:|---:|---:|---:|---:|
| B1, 0.10, 100 | 87 | 78 | 85 | 0 | 782,971 / 1,587,600 = 49.3% |
| double-Gross, 0.08, 200 | 51 | 43 | 50 | 0 | 583,212 / 1,036,800 = 56.3% |

Entries in the four decoder columns are block failures. All observed failures
were Type I syndrome misses and used the full 1,000 iterations. All successful
`both_changes` outputs were independently checked for logical failure; none
occurred in this sample. Relative to the original Q8 arm, `both_changes`
rescued 87 shots and lost 0 on B1, and rescued 51 and lost 0 on double-Gross.
The small sample establishes a strong mechanism for the local collapse; it
does not estimate a full low-LER curve or prove agreement with source values.

Removing global rounding alone in a separate exploratory check left
approximately the same failure counts. The internal projection clip and V2C
range interact: with either one retained, the bounded trial remains poor.
The source excerpt specifies an 8-bit step and range but omits its internal
BP4 representation and rounding locations, so this local interaction cannot
be attributed to the source decoder.

## Provenance and audit

- Reproduction command: `PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/inspect_q8_minsum_clipping.py --code b1 --p 0.10 --shots 100 --seed 20261101 --output from_dr_pfister_presentetations/results/performance_investigation/q8_ms_clip_b1_p010_n100`.
- Second command uses `--code double_gross --p 0.08 --shots 200 --seed 20261031 --output from_dr_pfister_presentetations/results/performance_investigation/q8_ms_clip_gross_p008_n200`.
- The two output directories contain `summary.json` and an uncompressed
  per-shot `events.jsonl`. Each summary pins the ledger SHA-256, sampler,
  settings, failures, and first-sweep clipping count.
- Independent audit recomputed both ledger SHA-256 values and every arm's
  outcome and iteration counts, verified complete shot indices and four arm
  records per shot, and confirmed identical error hashes across arms.

Historical Q8 curve results remain valid observations of the recorded local
policy. Correcting the adapter requires a new policy identity and a separately
qualified reproduction run; the canonical float64 BP4 v2 kernel is unaffected.
