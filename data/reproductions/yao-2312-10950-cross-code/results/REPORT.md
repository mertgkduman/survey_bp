# Plain BP and QBP across four codes

All plain decoders use flooding sum-product, float64, no damping, and T=100, matching the plain decoder limit for each code in [Yao et al.](https://arxiv.org/pdf/2312.10950v2). Each local comparison uses the same physical errors. These added baselines are controlled experiments; the paper supplies no reference curve for the missing decoder/code combinations.

A5/B2 retain depolarizing noise, with separate binary priors q_X=q_Z=2p/3 and joint QBP priors (1-p,p/3,p/3,p/3). B1/C2 retain X-only noise, with QBP prior (1-p,p,0,0); they do not use a depolarizing prior. The full quaternary graph is executed. Excluded Y/Z coordinates are held more than 1024 log units below the I/X states by a degree-based guard, so their float64 projection mass is exactly zero. Under this channel the active QBP equations reduce to binary BP; any measured difference comes from numerical details, hard-decision ties, or message clipping.

A5/B2 use independently audited fixed-shot paired v2 results from the earlier vanilla campaign. The completed independent B2 p=0.05 follow-up replaces its first lower-count cohort. A new independently fixed 500,000-shot two-arm B2 p=0.04 campaign replaces its original 92-failure QBP cohort; the interrupted earlier four-arm follow-up is excluded. B1/C2 use the new prespecified fixed-shot paired campaign. All shots, including zero syndromes and nonconvergence, enter the denominator. Type I is syndrome-inconsistent failure; Type II is a syndrome-valid logical failure. Stabilizer-equivalent corrections count as success.

## Logical error rates

| Code | Channel | p | N paired | BP failures (rate) | QBP failures (rate) | BP/QBP LER | QBP rescues/losses | Existing paper curve |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A5 | depolarizing | 0.04 | 529,662 | 2,124 (0.0040101) | 130 (0.00024544) | 16.3 | 2035/41 | QBP=0.000236 |
| A5 | depolarizing | 0.05 | 142,695 | 2,282 (0.0159922) | 113 (0.000791899) | 20.2 | 2193/24 | QBP=0.000876 |
| A5 | depolarizing | 0.06 | 39,570 | 1,935 (0.0489007) | 131 (0.00331059) | 14.8 | 1816/12 | QBP=0.003159 |
| A5 | depolarizing | 0.07 | 10,442 | 1,205 (0.115399) | 144 (0.0137905) | 8.37 | 1080/19 | QBP=0.011972 |
| A5 | depolarizing | 0.08 | 3,153 | 737 (0.233746) | 131 (0.0415477) | 5.63 | 615/9 | QBP=0.039651 |
| A5 | depolarizing | 0.09 | 1,333 | 489 (0.366842) | 110 (0.0825206) | 4.45 | 383/4 | QBP=0.093809 |
| A5 | depolarizing | 0.10 | 867 | 462 (0.532872) | 147 (0.16955) | 3.14 | 315/0 | QBP=0.1443 |
| B2 | depolarizing | 0.04 | 500,000 | 1,922 (0.003844) | 183 (0.000366) | 10.5 | 1870/131 | QBP=0.000406 |
| B2 | depolarizing | 0.05 | 200,000 | 2,378 (0.01189) | 196 (0.00098) | 12.1 | 2300/118 | QBP=0.001265 |
| B2 | depolarizing | 0.06 | 48,658 | 1,432 (0.0294299) | 110 (0.00226068) | 13 | 1386/64 | QBP=0.002569 |
| B2 | depolarizing | 0.07 | 18,505 | 1,268 (0.068522) | 129 (0.00697109) | 9.83 | 1200/61 | QBP=0.006755 |
| B2 | depolarizing | 0.08 | 8,291 | 1,164 (0.140393) | 101 (0.0121819) | 11.5 | 1101/38 | QBP=0.015077 |
| B2 | depolarizing | 0.09 | 4,198 | 1,089 (0.259409) | 101 (0.0240591) | 10.8 | 1016/28 | QBP=0.02978 |
| B2 | depolarizing | 0.10 | 2,073 | 901 (0.434636) | 100 (0.0482393) | 9.01 | 823/22 | QBP=0.060326 |
| B1 | X_only | 0.04 | 9,217 | 388 (0.0420961) | 388 (0.0420961) | 1 | 0/0 | BP=0.0434 |
| B1 | X_only | 0.05 | 5,000 | 427 (0.0854) | 427 (0.0854) | 1 | 0/0 | BP=0.0867 |
| B1 | X_only | 0.06 | 5,000 | 749 (0.1498) | 749 (0.1498) | 1 | 0/0 | BP=0.1449 |
| B1 | X_only | 0.07 | 5,000 | 1,195 (0.239) | 1,195 (0.239) | 1 | 0/0 | BP=0.2505 |
| B1 | X_only | 0.08 | 5,000 | 2,237 (0.4474) | 2,237 (0.4474) | 1 | 0/0 | BP=0.4448 |
| B1 | X_only | 0.09 | 5,000 | 3,551 (0.7102) | 3,551 (0.7102) | 1 | 0/0 | BP=0.7141 |
| B1 | X_only | 0.10 | 5,000 | 4,598 (0.9196) | 4,598 (0.9196) | 1 | 0/0 | BP=0.9139 |
| C2 | X_only | 0.04 | 5,000 | 561 (0.1122) | 561 (0.1122) | 1 | 0/0 | BP=0.080058 |
| C2 | X_only | 0.05 | 5,000 | 959 (0.1918) | 959 (0.1918) | 1 | 0/0 | BP=0.157581 |
| C2 | X_only | 0.06 | 5,000 | 1,525 (0.305) | 1,525 (0.305) | 1 | 0/0 | BP=0.268469 |
| C2 | X_only | 0.07 | 5,000 | 2,229 (0.4458) | 2,229 (0.4458) | 1 | 0/0 | BP=0.400398 |
| C2 | X_only | 0.08 | 5,000 | 3,131 (0.6262) | 3,131 (0.6262) | 1 | 0/0 | BP=0.636991 |
| C2 | X_only | 0.09 | 5,000 | 4,335 (0.867) | 4,335 (0.867) | 1 | 0/0 | BP=0.872285 |
| C2 | X_only | 0.10 | 5,000 | 4,929 (0.9858) | 4,929 (0.9858) | 1 | 0/0 | BP=0.983284 |

## Observed performance

On A5 under depolarizing noise, QBP has lower observed LER at every measured p. The BP/QBP rate ratio ranges from 3.14 to 20.19. At p=0.06, binary BP has 1935/39,570 failures (0.0489007), compared with QBP's 131/39,570 (0.00331059).

On B2 under depolarizing noise, QBP has lower observed LER at every measured p. The BP/QBP rate ratio ranges from 9.01 to 13.02. At p=0.06, binary BP has 1432/48,658 failures (0.0294299), compared with QBP's 110/48,658 (0.00226068).

On the 74,217 paired B1/C2 X-only shots, QBP and binary v2 have 0 different terminal correction digests, with 0 QBP rescues and 0 losses. This supports the expected binary reduction for this channel; it does not imply that QBP and binary BP behave identically under depolarizing noise.

The full QBP graph on these X-only samples takes 1.79–2.14 times the mean decoding time of binary v2 across the 14 same-run points. This implementation processes both check types and four-state coordinates even though only I and X have support.


## X-only numerical controls

The paper-style binary control clips outgoing V2C messages to ±25 and selects X on an exact zero belief. Binary v2 leaves V2C unbounded and selects I on an exact zero belief. QBP v2 leaves its state coordinates unbounded and selects X on an I/X tie under X-only support. Both v2 kernels apply the same tanh-product check rule and endpoint safeguard. No tuning or decimation is used.

| Code | p | Paper BP failures | Binary v2 failures | QBP v2 failures | QBP vs binary v2 candidate differences | QBP vs paper BP rescues/losses |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 0.04 | 401 | 388 | 388 | 0 | 269/256 |
| B1 | 0.05 | 392 | 427 | 427 | 0 | 220/255 |
| B1 | 0.06 | 726 | 749 | 749 | 0 | 289/312 |
| B1 | 0.07 | 1188 | 1195 | 1195 | 0 | 287/294 |
| B1 | 0.08 | 2247 | 2237 | 2237 | 0 | 149/139 |
| B1 | 0.09 | 3566 | 3551 | 3551 | 0 | 50/35 |
| B1 | 0.10 | 4596 | 4598 | 4598 | 0 | 4/6 |
| C2 | 0.04 | 390 | 561 | 561 | 0 | 243/414 |
| C2 | 0.05 | 749 | 959 | 959 | 0 | 377/587 |
| C2 | 0.06 | 1255 | 1525 | 1525 | 0 | 483/753 |
| C2 | 0.07 | 2078 | 2229 | 2229 | 0 | 458/609 |
| C2 | 0.08 | 3062 | 3131 | 3131 | 0 | 230/299 |
| C2 | 0.09 | 4313 | 4335 | 4335 | 0 | 43/65 |
| C2 | 0.10 | 4929 | 4929 | 4929 | 0 | 2/2 |

At C2 p=0.04, the paper-style binary control has 390/5,000 failures (0.078), compared with 561/5,000 (0.1122) for binary v2. The latter's observed LER is 1.44 times as high. The v2 numerical profile therefore does not improve every code/channel combination. Its outgoing-message cap and exact-zero hard decision differ from the paper control; their separate effects are not isolated by this experiment.


## Audit and interpretation

The historical evaluator XOR-combined X and Z logical signatures. A simultaneous identical nonzero X/Z signature can cancel under that expression. This assessment keeps both signatures separately and replays every retained nonexact converged A5/B2 v2 correction: 22,863 candidates audited, 0 logical classifications corrected. Raw historical ledgers remain immutable; the replay evidence is [logical-outcome-audit.jsonl](logical-outcome-audit.jsonl). Exact-success hashes, all sampled-error hashes, outcome counts, ledger SHA-256 values, and manifest identities are independently checked. New fixed-stride and boundary shots are replayed through all three kernels with the separate-signature evaluator.

Each rate has a fixed-N Clopper–Pearson 95% interval in [performance.csv](performance.csv). [paired.csv](paired.csv) reports QBP rescues (BP fails, QBP succeeds), losses (QBP fails, BP succeeds), exact McNemar p-values and conservative paired difference intervals formed from simultaneous 97.5% binomial intervals for the two discordant probabilities. Comparisons are exploratory; p-values are not adjusted across p or code.

The independent B2 p=0.04 follow-up was sized after inspecting the original pilot, and only its fresh fixed sample enters this comparison. Its ten 50,000-shot shards were frozen together; the assessor rejects incomplete stages and verifies all sample indices. This cross-code study does not close the unfinished earlier BP/BPGD rare-event reproduction task.

Iteration depth for separate binary decoding is max(I_X,I_Z), while mean iterations per component is (I_X+I_Z)/2. Directed edge updates count 2E per executed component sweep; QBP has more arithmetic per edge, so these counts are not flop equivalence. The CSV includes mean edge updates, p99 iteration depth, mean decoding time and p99 decoding time. A5/B2 timings come from historical four-arm runs except the fresh two-arm B2 p=0.04 campaign. B1/C2 timings rotate arm order on the same host. Runtime ratios across those campaigns are not controlled speed comparisons. The X-only QBP graph also processes X checks that add no inference information.

The two channels differ across code groups. A5/B2 versus B1/C2 LER is not an isolated comparison of code quality.

Artifacts: [performance.csv](performance.csv), [paired.csv](paired.csv), [comparison.png](comparison.png), [comparison.pdf](comparison.pdf), [audit.json](audit.json).
