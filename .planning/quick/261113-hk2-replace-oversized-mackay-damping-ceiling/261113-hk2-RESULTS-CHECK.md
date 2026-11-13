# T100 damping confirmation results check

Observed at 2026-11-13T19:18:32+00:00. Continuing GSD quick 261113-hk2.

**38 of 40 terminal points**; 5,842,388 completed shots / 760 block failures. The full-ledger audit of these 38 terminal points passed, including immutable pins, ledger/count/work totals, manifest and summary hashes, and first/last scientific replay. The campaign remains incomplete until both live points finish and the complete audit succeeds.

All comparisons below use the independent confirmation seed 2026111323, the same 100-iteration ceiling, and the original versus previously frozen selected damping. These are measured point estimates, with 20 failures per completed point; they do not by themselves establish superiority across the full grid. Binary BP uses X-only noise; Q-BP uses depolarizing noise with matched marginal rate, so compare damping within each row.

Means are actual executed iterations per retained shot. Directed-edge update means remain available in the audited portable receipt and are not equated across different graphs.

| Code length | Decoder | Physical p | Damping original → selected | LER original → selected | Mean iterations original → selected |
| --- | --- | ---: | --- | --- | --- |
| 274 | BP (SP, X-only) | 0.01 | 0 → 0.85 | 0.0117994 → 4.24167e-06 | 2.17 → 1.047 |
| 274 | BP (SP, X-only) | 0.013 | 0 → 0.85 | 0.0116212 → 4.82288e-05 | 2.195 → 1.064 |
| 274 | BP (SP, X-only) | 0.02 | 0 → 0.85 | 0.0144092 → 0.00172741 | 2.658 → 1.359 |
| 274 | BP (SP, X-only) | 0.03 | 0 → 0.85 | 0.0766284 → 0.0421053 | 8.241 → 4.236 |
| 274 | BP (SP, X-only) | 0.04 | 0 → 0.85 | 0.350877 → 0.307692 | 26.54 → 21.98 |
| 274 | Q-BP (SP, depolarizing) | 0.015 | 0.1 → 0.95 | 0.0135135 → running | 2.341 → running |
| 274 | Q-BP (SP, depolarizing) | 0.0195 | 0.1 → 0.95 | 0.0204082 → running | 3.057 → running |
| 274 | Q-BP (SP, depolarizing) | 0.03 | 0.1 → 0.95 | 0.0201816 → 0.000139112 | 3.257 → 1.58 |
| 274 | Q-BP (SP, depolarizing) | 0.045 | 0.1 → 0.95 | 0.0222965 → 0.00825764 | 3.749 → 5.03 |
| 274 | Q-BP (SP, depolarizing) | 0.06 | 0.1 → 0.95 | 0.0909091 → 0.0909091 | 7.109 → 16.2 |
| 74 | BP (SP, X-only) | 0.01 | 0 → 0.7 | 0.0094162 → 0.000259104 | 1.891 → 1.035 |
| 74 | BP (SP, X-only) | 0.013 | 0 → 0.7 | 0.0141743 → 0.0012809 | 2.347 → 1.068 |
| 74 | BP (SP, X-only) | 0.02 | 0 → 0.7 | 0.0146735 → 0.00856531 | 2.279 → 1.317 |
| 74 | BP (SP, X-only) | 0.03 | 0 → 0.7 | 0.0606061 → 0.0423729 | 5.745 → 1.945 |
| 74 | BP (SP, X-only) | 0.04 | 0 → 0.7 | 0.123457 → 0.097561 | 8.389 → 5.439 |
| 74 | Q-BP (SP, depolarizing) | 0.015 | 0.1 → 0.95 | 0.011274 → 5.79235e-05 | 2.116 → 1.022 |
| 74 | Q-BP (SP, depolarizing) | 0.0195 | 0.1 → 0.95 | 0.029985 → 0.000255516 | 3.682 → 1.041 |
| 74 | Q-BP (SP, depolarizing) | 0.03 | 0.1 → 0.95 | 0.0305344 → 0.00145012 | 4 → 1.156 |
| 74 | Q-BP (SP, depolarizing) | 0.045 | 0.1 → 0.95 | 0.0790514 → 0.0131926 | 7.126 → 2.003 |
| 74 | Q-BP (SP, depolarizing) | 0.06 | 0.1 → 0.95 | 0.0757576 → 0.0297619 | 5.356 → 3.708 |

Two length-274 selected Q-BP points (depolarizing p=.015 and .0195) remain running. Live counters at 2026-11-13T19:20:30+00:00: p=0.015: 0 failures / 2,980,864 shots; p=0.0195: 9 failures / 2,714,048 shots. These ongoing counts have no terminal LER or transferred stopping interval. Both continue to 20 failures or 100 million shots.

At length 274, depolarizing p=.060, the observed LER is .09091 for both damping values, but mean iterations increase from 7.109 to 16.2. Thus the frozen global damping choice is not uniformly faster or better at every rate. At p=.045, LER decreases while mean iterations increase. Do not silently change the frozen tuning choice using this holdout data.

Roffe remains unsubmitted and waits for all 40 confirmation points and the successful complete audit. Its frozen 218-point design still uses paper T=n (162/242/338/450), source min-sum settings and code-specific paper grids; its 40 implementation pins pass. No 88,200-iteration damping is active and no old curves were altered.

The 38-point portable audit receipt and timestamped progress snapshot are stored in `data/reproductions/mackay-0304161-damping-t100/confirmation/verified.json` and `progress.json`. No new simulations were started during this check. Partial holdout curves are held for the planned complete audit; the public view remains 76 curves / 399 points / 8 codes / 0 circuits.
