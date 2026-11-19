# PriorTilt BP results check

Checked 25/28 final worker audits, containing 77,735,259 decoded memory shots and 1,000 observable errors.
Reconciled the receipts, stopping rules, exact intervals and retained work. Rehashed 134 sampled ledger and noise bindings.
The scheduled collector still handles the full publication rehash.

| Mode | Code | p | Ordinary BP LER/cycle | Tuned BP LER/cycle | Tuned / ordinary LER | Mean BP sweeps per shot, ordinary → tuned | Local XZ PriorTilt LER/cycle |
|---|---|---:|---:|---:|---:|---:|---:|
| XZ | BB144 | 0.001 | 1.286e-05 | 7.195e-05 | 5.593 | 13.02 → 11.4 | 2.917e-08 |
| XZ | BB144 | 0.002 | 0.0002916 | 0.0002965 | 1.017 | 83.53 → 70.63 | 2.723e-06 |
| XZ | BB144 | 0.003 | 0.002032 | 0.001521 | 0.749 | 416.6 → 273.3 | 5.574e-05 |
| XZ | BB144 | 0.004 | 0.01468 | 0.0111 | 0.756 | 1935 → 1360 | 0.0006416 |
| XZ | BB144 | 0.005 | 0.04339 | 0.02784 | 0.641 | 5550 → 3694 | 0.005509 |
| XZ | BB70 | 0.0005 | 1.195e-06 | 3.2e-06 | 2.678 | 4.082 → 2.52 | 2.889e-08 |
| XZ | BB70 | 0.0008 | 6.68e-06 | 1.647e-05 | 2.465 | 6.568 → 4.666 | 1.694e-07 |
| XZ | BB70 | 0.001 | 1.972e-05 | 2.425e-05 | 1.230 | 9.009 → 6.05 | 3.958e-07 |
| XZ | BB70 | 0.002 | 0.0003831 | 0.0003725 | 0.972 | 60.74 → 47.42 | 1.164e-05 |
| XZ | GB102 | 0.0008 | 3.936e-07 | 3.936e-07 | 1.000 | 8.262 → 8.262 | 1.291e-07 |
| XZ | GB102 | 0.001 | 1.131e-06 | 1.131e-06 | 1.000 | 9.599 → 9.599 | 3.847e-07 |
| XZ | GB102 | 0.002 | 6.381e-05 | 6.381e-05 | 1.000 | 24.29 → 24.29 | 1.907e-05 |
| XYZ | BB144 | 0.003 | 0.002877 | — | — | 3027 → — | — |

Mean sweeps are weighted by the retained shots across both memories. The CSV gives separate X and Z work and 95% pointwise LER intervals.

| Training group | Damping | Scaling | Offset | Selected / ordinary errors on final training round |
|---|---:|---:|---:|---:|
| xz-bb144 | 0.25 | 1.0 | 0.0 | 49 / 59 |
| xz-bb70 | 0.25 | 1.0 | 0.0 | 32 / 33 |
| xz-gb102 | 0.0 | 1.0 | 0.0 | 20 / 20 |

All three completed training groups used 2,048 shots per memory basis in the final tuning round.
BB144 XZ and BB70 XZ selected damping 0.25 with scaling 1 and offset 0. The GB102 neutral selection produces the same counts and iteration work on the common evaluation samples.
Tuned BB144 XZ at p=.003 has an estimated 25% lower LER and 34% fewer sweeps, with overlapping LER intervals. At p=.001 the estimate is 5.59 times higher and the pointwise intervals are disjoint. BB70 at the low-rate points also has higher estimated LER, with overlapping intervals.

| Unfinished point | X errors / shots | Z errors / shots |
|---|---:|---:|
| xz-gb102-p000500-bp | 13 / 51,914,240 | 8 / 51,913,728 |
| xz-gb102-p000500-tuned-bp | 13 / 51,902,464 | 8 / 51,901,952 |
| Original XYZ priortilt | 18 / 466,304 | 20 / 297,260 |
| Original XYZ relay5 | 7 / 162,432 | 12 / 162,432 |

The tuned XYZ point depends on completion of XYZ tuning. The counts above are running progress.
Ordinary XYZ BP at p=.003 has an audited LER/cycle of 2.877e-3. The released Table 4 reference LERs are 1.039e-5 for PriorTilt and 1.096e-5 for RelayBP-5, at their respective paper iteration limits.

[Audited result CSV](audited-bp.csv) · [Checked aggregate evidence](assessment.json) · [Scheduler snapshot](scheduler.txt)
