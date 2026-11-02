---
status: complete
date: 2026-11-02
---

# B1/C2 depolarizing extension completed

Delivered the separate `depolarizing/` experiment under
`data/reproductions/yao-2312-10950-cross-code/`. Final data/report commit:
`b204164`. Existing X-only results and frozen policies remain separate.

All 14 B1/C2 points, p=0.04,...,0.10, use plain binary BP v2 and QBP v2,
float64 flooding SP, no damping and T=100. The two arms decode identical
physical errors. Joint priors are (1-p,p/3,p/3,p/3), binary marginals 2p/3;
syndrome measurements are perfect. Both begin with the same scalar edge LLR.

The 28,000 pilot samples were independently audited before selecting fresh
fixed cohorts, and are excluded from final estimates. The final comparison
uses 381,309 paired samples over 15 disjoint shards. All 28 new arm estimates
exceed 100 failures (minimum 153); no low-count or zero-failure point remains.
Pilot and final seed namespaces are disjoint, and all 14 denominator choices
were checked against the prospective pilot rule.

QBP has lower observed LER at every p on both codes. Binary/QBP ratios are
5.82–9.33 on B1 and 3.84–8.85 on C2. At p=0.06:

| Code | Paired N | Binary failures | QBP failures | Binary LER | QBP LER |
|---|---:|---:|---:|---:|---:|
| B1 | 23,530 | 2,063 | 242 | 0.0876753 | 0.0102847 |
| C2 | 20,000 | 3,945 | 568 | 0.19725 | 0.0284 |

At this point QBP also takes about 30% less mean decoding time on each code.
The LER gain is mostly reduced syndrome nonconvergence. Paired rescue/loss
counts, 95% difference intervals, exact McNemar tests, Type I/II counts,
iteration/depth statistics, directed edge work and mean/p99 times are saved.

`results/all_depolarizing.csv` contains both decoders on all four codes,
56 measurements in 28 code/rate cells. Existing A5/B2 results were imported
only after their audited CSV hashes were checked. The report includes a
separate comparison with B1/C2 X-only results and explains the differing
component marginals between channels. PNG/PDF figures share their vertical
scales for the four-code comparison and were visually inspected.

Validation: every new physical sample and syndrome hash, manifest identity,
ledger hash, count aggregate and shard boundary was independently checked.
Boundary/fixed-stride corrections and all Type II events were replayed with
separate X/Z logical signatures. Three focused tests passed. The independent
sparse syndrome traversal was tested against dense Pauli algebra. All 29
pilot/follow-up Slurm tasks completed with exit code zero; scheduler accounting
is saved. Completed ledgers were losslessly compressed with byte-exact checks.
CSV schema compatibility, artifact hashes, render-only rebuild and Git
whitespace checks passed.

Execution deviation: the first follow-up freezer encountered a test-created
Numba cache referring to `<dynamic>` before it wrote a final plan. Disabling
disk caching for the independently loaded audit-only syndrome function fixed
it. All pilots were then verified before final sampling. Simulation kernels
and policies did not change.

This completes the requested controlled depolarizing extension. The separate
earlier BP/BPGD rare-event reproduction task is not closed by these results.
