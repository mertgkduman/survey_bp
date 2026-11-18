# PriorTilt Fig. 1 result check — 2026-11-18

All 13 PriorTilt and all 13 Relay points have completed full worker audits. Beam
has 12/13 audited points. Sampling is complete for all 39 points; only GB102
Beam at p=0.0005 awaits its full audit (array61971019 task29, 10 CPUs). Its
completed sampling receipt is deliberately excluded from the status table.
Collector61971020 remains dependency-pending.

The checked status snapshot has **38/39 points**, 1,661,754,800 decoded
memory-basis shots and 1,447 observable errors. Ten points are new relative to
the last 28-point publication. All 28 earlier complete CSV rows are identical.
See [all 13 PriorTilt rates and comparisons](PRIORTILT-TABLE.md) and the
[38-point status CSV](comparison-snapshot.csv).

| Newly completed PriorTilt point | Local LER/cycle | Paper LER/cycle | Local 95% interval |
|---|---:|---:|---:|
| BB144, p=0.001 | 2.91667e-8 | 2.08229e-8 | [1.58254e-8, 4.90661e-8] |
| BB70, p=0.0005 | 2.88889e-8 | 2.54276e-8 | [1.43116e-8, 5.23233e-8] |
| GB102, p=0.0005 | 1.22222e-8 | 1.16667e-8 | [3.58872e-9, 2.99735e-8] |
| GB102, p=0.0008 | 1.29053e-7 | 1.12448e-7 | [7.31618e-8, 2.02176e-7] |

All 38 corresponding paper ordinates lie within their local pointwise 95%
intervals. Local/paper ratios span 0.771–1.401. This supports consistency at
local precision; it is not simultaneous whole-figure equivalence. PriorTilt has
the lowest estimate in all 12 fully compared three-decoder strata: Relay/PriorTilt
LER ratios span 1.147–2.910 and Beam/PriorTilt span 1.461–2.837. Intervals can
overlap, so strict superiority is not established at every rate. These are the
published algorithm settings, not matched-latency comparisons.

Nine audited memory bases stopped at 100 million shots rather than 20 errors.
The rarest PriorTilt points BB144/.001, BB70/.0005 and GB102/.0005 reached that
cap in both bases; their error counts are respectively X/Z=19/16, 8/18 and 6/5.
The metric remains (X-memory observable rate + Z-memory observable rate) / cycles,
matching the released scoring convention. Nonconvergence is separate.

## Verification scope

Matching final audit/complete receipts, frozen parent/resource identities,
manifest hashes and resolved policies pass. Independent source-count, denominator,
stopping, joint-outcome, exact capped-interval and work/latency-summary checks
pass for all 38 rows. The source ordinates are recomputed from the authors'
released X/Z counts. All 63 frozen implementation files remain unchanged.

For all 15 audited parallel points, additive receipt accounting reconciles:
1,190,545,664 computed shots = 1,189,379,980 retained + 1,165,684 speculative.
All 45,747 inherited marker digests are preserved in the full-audit receipts.
Fresh sampled on-disk checks cover 90 inherited markers, 90 canonical
marker/NPZ/noise bindings, and 87 sealed-stage marker/NPZ/noise bindings,
chosen deterministically first/middle/last per basis. The work receipts declare
145,339 stages. Speculative outcomes remain excluded from LER and retained means.

A complete publication/raw-resource rehash was started and deliberately stopped
because it duplicated already completed full worker audits over 1.66 billion
shots for a status request. Interrupted logs and the attempted full checker are
retained; they are not claimed as completed whole-ledger verification. One
parallel point's full resource check finished before interruption, as recorded
in that log. The checked status extraction uses retained full worker audits,
aggregate reconciliation and explicitly sampled disk checks. The canonical
RESULTS.md/comparison.csv/figure remain byte-unchanged at 28 points; the existing
scheduled collector will perform the full refresh after the final Beam audit.
No updated full-publication figure is claimed here.

Parent plan: 3e466081790d913ae2fb0a477f654bd0218504a79e7d969b989b62043b7e829c.
Resource amendment: da570e399be73f21d768d015c124b02fb5ee82796bda498effa284e8ddeb6a22.

No simulations were submitted, cancelled or rerun; no decoder, scoring,
canonical kernel, frozen implementation, public HTML/catalog or v1 files were
changed. Software tests were not repeated for an unchanged-code status check.
The 16 pre-existing tracked collector changes remain outside staging. Phase 11
and spike060 remain open pending their existing scientific gates/final audit.
