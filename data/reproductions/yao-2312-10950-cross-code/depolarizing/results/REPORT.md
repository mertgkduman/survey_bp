# Plain BP and QBP under depolarizing noise

All four codes use the same independent code-capacity channel: P(I)=1-p and P(X)=P(Y)=P(Z)=p/3 on every qubit, with perfect syndrome measurements. Binary BP uses separate X/Z marginals 2p/3; QBP uses the joint Pauli prior. Both are plain, undamped float64 flooding sum-product v2 with T=100. B1/C2 depolarizing curves are new controlled results without paper reference points.

Both kernels start with the same scalar commuting/anticommuting edge LLR, $m_{v\to c}^{(0)}=\log[(1-2p/3)/(2p/3)]$. QBP subsequently combines both check types through one four-state qubit belief; separate binary BP retains only the two marginals. A performance difference under these settings therefore is not explained by using the physical p as a binary prior.

B1/C2 pilot shots choose a fresh fixed sample size and are excluded from every estimate. Fixed cohorts target 200 expected failures using the pilot, with 20,000 minimum and 1,000,000 maximum shots. Low-count estimates remain labeled; zero failures are reported as exact one-sided 95% upper bounds, not observed nonzero rates. A5/B2 points are inherited from the independently audited prior comparison.

The completed B1/C2 follow-up contains 381,309 paired physical errors. Its 28 decoder estimates each have at least 153 failures.

| Code | p | Paired N | Binary BP failures (LER) | QBP failures (LER or 95% upper bound) | QBP precision |
|---|---:|---:|---:|---:|---|
| A5 | 0.04 | 529,662 | 2,124 (0.0040101) | 130 (0.00024544) | ≥100 failures |
| A5 | 0.05 | 142,695 | 2,282 (0.0159922) | 113 (0.000791899) | ≥100 failures |
| A5 | 0.06 | 39,570 | 1,935 (0.0489007) | 131 (0.00331059) | ≥100 failures |
| A5 | 0.07 | 10,442 | 1,205 (0.115399) | 144 (0.0137905) | ≥100 failures |
| A5 | 0.08 | 3,153 | 737 (0.233746) | 131 (0.0415477) | ≥100 failures |
| A5 | 0.09 | 1,333 | 489 (0.366842) | 110 (0.0825206) | ≥100 failures |
| A5 | 0.10 | 867 | 462 (0.532872) | 147 (0.16955) | ≥100 failures |
| B2 | 0.04 | 500,000 | 1,922 (0.003844) | 183 (0.000366) | ≥100 failures |
| B2 | 0.05 | 200,000 | 2,378 (0.01189) | 196 (0.00098) | ≥100 failures |
| B2 | 0.06 | 48,658 | 1,432 (0.0294299) | 110 (0.00226068) | ≥100 failures |
| B2 | 0.07 | 18,505 | 1,268 (0.068522) | 129 (0.00697109) | ≥100 failures |
| B2 | 0.08 | 8,291 | 1,164 (0.140393) | 101 (0.0121819) | ≥100 failures |
| B2 | 0.09 | 4,198 | 1,089 (0.259409) | 101 (0.0240591) | ≥100 failures |
| B2 | 0.10 | 2,073 | 901 (0.434636) | 100 (0.0482393) | ≥100 failures |
| B1 | 0.04 | 44,445 | 1,231 (0.0276972) | 153 (0.00344246) | ≥100 failures |
| B1 | 0.05 | 80,000 | 4,301 (0.0537625) | 461 (0.0057625) | ≥100 failures |
| B1 | 0.06 | 23,530 | 2,063 (0.0876753) | 242 (0.0102847) | ≥100 failures |
| B1 | 0.07 | 20,000 | 2,707 (0.13535) | 347 (0.01735) | ≥100 failures |
| B1 | 0.08 | 20,000 | 3,799 (0.18995) | 529 (0.02645) | ≥100 failures |
| B1 | 0.09 | 20,000 | 5,329 (0.26645) | 841 (0.04205) | ≥100 failures |
| B1 | 0.10 | 20,000 | 7,231 (0.36155) | 1,242 (0.0621) | ≥100 failures |
| C2 | 0.04 | 33,334 | 2,124 (0.0637187) | 240 (0.00719986) | ≥100 failures |
| C2 | 0.05 | 20,000 | 2,431 (0.12155) | 292 (0.0146) | ≥100 failures |
| C2 | 0.06 | 20,000 | 3,945 (0.19725) | 568 (0.0284) | ≥100 failures |
| C2 | 0.07 | 20,000 | 5,834 (0.2917) | 916 (0.0458) | ≥100 failures |
| C2 | 0.08 | 20,000 | 8,057 (0.40285) | 1,388 (0.0694) | ≥100 failures |
| C2 | 0.09 | 20,000 | 10,244 (0.5122) | 2,218 (0.1109) | ≥100 failures |
| C2 | 0.10 | 20,000 | 12,328 (0.6164) | 3,212 (0.1606) | ≥100 failures |

## Paired B1/C2 results

| Code | p | QBP rescues | QBP losses | Failure difference QBP−BP | Conservative paired 95% interval |
|---|---:|---:|---:|---:|---:|
| B1 | 0.04 | 1209 | 131 | -0.0242547 | [-0.0265813, -0.0219226] |
| B1 | 0.05 | 4208 | 368 | -0.048 | [-0.0503156, -0.0456795] |
| B1 | 0.06 | 2003 | 182 | -0.0773906 | [-0.0827788, -0.0719756] |
| B1 | 0.07 | 2590 | 230 | -0.118 | [-0.125039, -0.110915] |
| B1 | 0.08 | 3597 | 327 | -0.1635 | [-0.171616, -0.155321] |
| B1 | 0.09 | 4955 | 467 | -0.2244 | [-0.233644, -0.215072] |
| B1 | 0.10 | 6551 | 562 | -0.29945 | [-0.309501, -0.289286] |
| C2 | 0.04 | 2068 | 184 | -0.0565189 | [-0.0604137, -0.0526098] |
| C2 | 0.05 | 2350 | 211 | -0.10695 | [-0.113703, -0.100155] |
| C2 | 0.06 | 3748 | 371 | -0.16885 | [-0.177192, -0.160444] |
| C2 | 0.07 | 5428 | 510 | -0.2459 | [-0.25545, -0.236257] |
| C2 | 0.08 | 7319 | 650 | -0.33345 | [-0.343883, -0.322893] |
| C2 | 0.09 | 8911 | 885 | -0.4013 | [-0.412412, -0.390039] |
| C2 | 0.10 | 10101 | 985 | -0.4558 | [-0.467119, -0.444312] |

## Observed performance

On B1, QBP has lower observed LER at 7/7 measured rates. Among points with nonzero QBP failures, the binary/QBP rate ratio spans 5.82–9.33.

At p=0.06, binary BP has 2063/23,530 failures (0.0876753); QBP has 242/23,530 (0.0102847). Mean iterations per component are 16.06 and 9.50, respectively; mean decoding times are 14.229 ms and 9.941 ms.

On C2, QBP has lower observed LER at 7/7 measured rates. Among points with nonzero QBP failures, the binary/QBP rate ratio spans 3.84–8.85.

At p=0.06, binary BP has 3945/20,000 failures (0.19725); QBP has 568/20,000 (0.0284). Mean iterations per component are 29.48 and 17.33, respectively; mean decoding times are 46.479 ms and 33.025 ms.


### Failure types at p=0.06

| Code | Paired N | BP Type I | BP Type II | QBP Type I | QBP Type II |
|---|---:|---:|---:|---:|---:|
| A5 | 39,570 | 1935 | 0 | 131 | 0 |
| B2 | 48,658 | 1431 | 1 | 110 | 0 |
| B1 | 23,530 | 2063 | 0 | 242 | 0 |
| C2 | 20,000 | 3942 | 3 | 568 | 0 |

## Channel comparison

The earlier B1/C2 X-only study has identical QBP/binary-v2 corrections because only I/X states have prior support. Depolarizing noise permits Y/Z and supplies within-qubit correlation to QBP. The numerical value of p has different marginal meaning between the two channels: binary X-flip probability is p in the X-only channel and 2p/3 in the depolarizing channel.

| Code | p | X-only binary/QBP LER | Depolarizing binary LER | Depolarizing QBP LER or upper bound |
|---|---:|---:|---:|---:|
| B1 | 0.04 | 0.0420961 | 0.0276972 | 0.00344246 |
| B1 | 0.05 | 0.0854 | 0.0537625 | 0.0057625 |
| B1 | 0.06 | 0.1498 | 0.0876753 | 0.0102847 |
| B1 | 0.07 | 0.239 | 0.13535 | 0.01735 |
| B1 | 0.08 | 0.4474 | 0.18995 | 0.02645 |
| B1 | 0.09 | 0.7102 | 0.26645 | 0.04205 |
| B1 | 0.10 | 0.9196 | 0.36155 | 0.0621 |
| C2 | 0.04 | 0.1122 | 0.0637187 | 0.00719986 |
| C2 | 0.05 | 0.1918 | 0.12155 | 0.0146 |
| C2 | 0.06 | 0.305 | 0.19725 | 0.0284 |
| C2 | 0.07 | 0.4458 | 0.2917 | 0.0458 |
| C2 | 0.08 | 0.6262 | 0.40285 | 0.0694 |
| C2 | 0.09 | 0.867 | 0.5122 | 0.1109 |
| C2 | 0.10 | 0.9858 | 0.6164 | 0.1606 |

## Evidence and interpretation

All physical draws, syndrome hashes, manifests, event hashes, counts and disjoint shard boundaries are independently verified. Boundary and fixed-stride corrections and all Type II events are replayed. The independent evaluator retains X/Z logical signatures separately, so logical Y errors cannot cancel. Syndrome-inconsistent outputs are Type I failures; syndrome-valid nontrivial logical residuals are Type II. Stabilizer-equivalent corrections count as successes; all samples enter the denominator.

Rates use fixed-N Clopper–Pearson 95% intervals. Zero-failure triangles show 1−0.05^(1/N). The paired failure-difference interval is formed from simultaneous 97.5% binomial intervals for rescues and losses, with exact McNemar test p-values in paired.csv. A p-value stored as 0 reflects floating-point underflow, not a mathematically zero probability. Low-count QBP points do not establish a precise rate or a measured error floor. No multiple-comparison adjustment is applied to this exploratory analysis.

Performance CSVs include mean iterations per component, p99 iteration depth, directed edge updates, and mean/p99 decoding time. Separate binary mean iterations are (I_X+I_Z)/2; depth is max(I_X,I_Z); directed work is twice the edge count per executed component sweep. This is not equal arithmetic cost per edge. Historical A5/B2 timings and new B1/C2 timings are from different campaigns.

Across-code LER differences also involve block length, dimension, Tanner graph and convergence within T=100. These are plain-decoder baselines at a shared iteration cap; comparisons of optimized codes or tuned decoders require their own controls. The paired BP/QBP contrast within a code holds its sampled physical errors fixed.

Files: [all four-code rates](all_depolarizing.csv), [new B1/C2 performance](performance.csv), [paired differences](paired.csv), [plot PNG](comparison.png), [plot PDF](comparison.pdf), [audit](audit.json).
