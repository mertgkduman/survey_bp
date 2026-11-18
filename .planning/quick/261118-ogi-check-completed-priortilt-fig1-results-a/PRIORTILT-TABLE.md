# Audited PriorTilt results at every paper rate

LER per syndrome cycle = (X-memory observable error rate + Z-memory observable error rate) / cycles. This uses the released observable-only scoring convention; nonconvergence is recorded separately. Local intervals are pointwise at-least-95% simultaneous X/Z bounds, not simultaneous coverage across this entire table. Source values are from the authors' released Fig. 1 counts.

| Code | p | Local PriorTilt LER/cycle (95%) | Paper PriorTilt LER/cycle | Relay / PriorTilt | Beam / PriorTilt |
|---|---:|---:|---:|---:|---:|
| BB144 | 0.001 | 2.9166667e-08 [1.5825353e-08, 4.9066056e-08] | 2.0822853e-08 | 2.910 | 1.903 |
| BB144 | 0.002 | 2.7233347e-06 [1.5439029e-06, 4.266412e-06] | 2.4667311e-06 | 2.133 | 1.575 |
| BB144 | 0.003 | 5.5735984e-05 [3.1599696e-05, 8.7309062e-05] | 5.740602e-05 | 2.129 | 2.353 |
| BB144 | 0.004 | 0.00064159441 [0.00036400033, 0.0010041251] | 0.00067611136 | 1.769 | 1.977 |
| BB144 | 0.005 | 0.0055087433 [0.003143113, 0.0085557394] | 0.0043946995 | 1.730 | 1.976 |
| BB70 | 0.0005 | 2.8888889e-08 [1.4311609e-08, 5.2323322e-08] | 2.5427618e-08 | 2.531 | 2.568 |
| BB70 | 0.0008 | 1.6938319e-07 [9.6025813e-08, 2.6535899e-07] | 1.5657799e-07 | 2.522 | 2.169 |
| BB70 | 0.001 | 3.9583626e-07 [2.2440541e-07, 6.2012461e-07] | 4.6778765e-07 | 2.476 | 2.730 |
| BB70 | 0.002 | 1.1636333e-05 [6.5968727e-06, 1.8229462e-05] | 1.5085533e-05 | 1.887 | 2.837 |
| GB102 | 0.0005 | 1.2222222e-08 [3.5887177e-09, 2.9973531e-08] | 1.1666667e-08 | 1.545 | awaiting full audit |
| GB102 | 0.0008 | 1.2905264e-07 [7.3161827e-08, 2.0217639e-07] | 1.1244776e-07 | 1.164 | 1.571 |
| GB102 | 0.001 | 3.846802e-07 [2.1808088e-07, 6.0264734e-07] | 3.6369822e-07 | 1.147 | 1.597 |
| GB102 | 0.002 | 1.9069198e-05 [1.0810788e-05, 2.9873501e-05] | 2.0988783e-05 | 1.461 | 1.461 |

Ratios compare local point estimates at the published algorithm settings. They do not imply matched latency or statistically strict superiority at every point. The rarest rates can stop at 100 million shots per basis before reaching 20 errors.

38/39 points in this checked status snapshot; all 38 corresponding paper ordinates lie within their local intervals. All 28 earlier full CSV rows are identical.

Scope: matching completed full-worker audit/complete receipts, manifest/policy/frozen-identity checks, independent aggregate reconciliation and sampled on-disk bindings. A fresh full raw-ledger rehash was deliberately not completed for this status check. The main publication remains at its prior 28-point snapshot pending the scheduled final collector.
