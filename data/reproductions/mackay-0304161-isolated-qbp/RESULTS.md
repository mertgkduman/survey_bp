# MacKay Construction-U: isolated decoder and damping results

Snapshot: 2026-11-13T21:37:16+00:00. Descriptive point estimates from audited receipts; no new sampling or decoding.

These matched-channel tables use identical depolarizing Pauli samples and the independent confirmation seed2026111323. All four methods have a100-full-graph-round ceiling; separate BP uses matched marginal priors2p/3 and Q-BP uses the joint prior p. Both X/Z logical residuals and nonconvergence count toward quantum block failure. Each complete point stopped at20 failures. The20 new d=0 points are fully audited; the existing damping confirmation has39/40 audited points.

Each column below is a quantum block failure probability. Method contrasts compare separate BP and Q-BP at d=0; damping contrasts compare d=0/.1/.95 within Q-BP. These point estimates do not assert simultaneous superiority or statistical equivalence. Work units, mean iterations, actual directed-edge updates, stopping intervals and per-point denominators are retained in results-table.csv.

## Length 274

| Depolarizing p | Separate BP d=0 | Q-BP d=0 | Q-BP d=.1 | Q-BP d=.95 |
| ---: | ---: | ---: | ---: | ---: |
| 0.015 | 0.01351 | 0.01351 | 0.01351 | Running |
| 0.0195 | 0.02132 | 0.02041 | 0.02041 | 2.951e-06 |
| 0.03 | 0.03968 | 0.02789 | 0.02018 | 0.0001391 |
| 0.045 | 0.1156 | 0.05236 | 0.0223 | 0.008258 |
| 0.06 | 0.2985 | 0.1333 | 0.09091 | 0.09091 |

## Length 74

| Depolarizing p | Separate BP d=0 | Q-BP d=0 | Q-BP d=.1 | Q-BP d=.95 |
| ---: | ---: | ---: | ---: | ---: |
| 0.015 | 0.01127 | 0.01127 | 0.01127 | 5.792e-05 |
| 0.0195 | 0.03008 | 0.02999 | 0.02999 | 0.0002555 |
| 0.03 | 0.03922 | 0.03053 | 0.03053 | 0.00145 |
| 0.045 | 0.1053 | 0.08163 | 0.07905 | 0.01319 |
| 0.06 | 0.1923 | 0.1075 | 0.07576 | 0.02976 |

## Original paper comparison

Source: MacKay, Mitchison and McFadden (2004), https://arxiv.org/abs/quant-ph/0304161v3. The published curve is classical block error on a binary symmetric channel. It uses the two-hypothesis unicycle decoder. Our unicycle adaptation below uses100 iterations per hypothesis (200 maximum total), an inferred rather than source-stated budget. Our ordinary and damped binary BP use X-only noise and T100. Classical and quantum error counts coincide in these listed length274 measurements. All paper ordinates are approximate digitizations.

| X rate | Published unicycle ≈ | Our unicycle | Ordinary BP d=0 | BP d=.85 |
| ---: | ---: | ---: | ---: | ---: |
| 0.01 | 6.699e-06 | 5.038e-06 | 0.0118 | 4.242e-06 |
| 0.013 | 7.075e-05 | 4.974e-05 | 0.01162 | 4.823e-05 |
| 0.02 | 0.00223 | 0.002071 | 0.01441 | 0.001727 |
| 0.03 | 0.04834 | 0.04283 | 0.07663 | 0.04211 |
| 0.04 | 0.1808 | 0.1923 | 0.3509 | 0.3077 |

For length74, the five requested paper ordinates are not reported in inspected arXiv versions1–3 and are blank/not_reported in the CSV. The paper does provide one fixed-target summary: marginal p≈.00681824 for the source convention of quantum error1e-4 / constituent classical error5e-5. That threshold is not a five-rate curve. See PAPER-EVIDENCE.md and paper-evidence.json for all source/member hashes and vector calibration.

Separate-BP mean rounds are max(X sweeps,Z sweeps); actual component sweeps and directed-edge work account for each component independently. Joint sweeps and unicycle branch sweeps remain explicitly typed. Shared samples across methods or damping settings are not pooled as independent observations.
