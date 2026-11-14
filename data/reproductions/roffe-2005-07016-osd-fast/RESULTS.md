# Roffe: canonical BP with OSD-0 and CS-10

Audited 0/218 points. Status: partial; missing points remain unavailable. No new sampling is performed by this report.

All new curves use X-only noise, canonical undamped flooding min-sum, alpha_t=1-2^-t, float64 and T=n. OSD activates only after original-syndrome nonconvergence; a converged BP output is kept even if independent evaluation later identifies a logical error. Both methods share the previous confirmation physical stream and preserve 20-failure/1e8-shot stopping without pooling.

BP sweeps and directed edge updates exclude OSD work. Separate invocation rate, candidate evaluations, elimination word-XOR counts and warmed BP/OSD/total times are in the CSV and workbench. Source CS60 values are approximate paper data. The previous damped Q-BP comparison is depolarizing at1.5p and is not a same-channel ranking.

## [[162,2,9]]; BP T=162

| X rate p | BP d=0 | BP d=.5 | OSD-0 | CS-10 | Paper CS-60≈ | Q-BP d=.3, depolarizing 1.5p |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 0.03968 | 0.03067 | pending | pending | $6.547\times10^{-7}$ | 0.006129 |
| 0.02 | 0.146 | 0.07273 | pending | pending | $3.271\times10^{-5}$ | 0.005637 |
| 0.03 | 0.2632 | 0.1818 | pending | pending | $3.951\times10^{-4}$ | 0.007138 |
| 0.04 | 0.3846 | 0.3226 | pending | pending | 0.002243 | 0.02144 |
| 0.05 | 0.7143 | 0.4167 | pending | pending | 0.008172 | 0.03448 |
| 0.06 | 0.625 | 0.3279 | pending | pending | 0.02234 | 0.08333 |
| 0.07 | 0.8333 | 0.5128 | pending | pending | 0.04961 | 0.1626 |
| 0.08 | 0.9524 | 0.6452 | pending | pending | 0.09296 | 0.2247 |
| 0.09 | 1 | 0.9091 | pending | pending | 0.1533 | 0.4082 |
| 0.091 | 1 | 0.8696 | pending | pending | 0.1596 | 0.5128 |
| 0.093 | 0.9524 | 0.8696 | pending | pending | 0.174 | 0.5128 |
| 0.094 | 0.8333 | 0.6452 | pending | pending | 0.1813 | 0.4878 |
| 0.095 | 0.8696 | 0.7692 | pending | pending | 0.1881 | 0.5882 |
| 0.099 | 0.9524 | 0.6667 | pending | pending | 0.2189 | 0.4762 |
| 0.1 | 0.9524 | 0.8 | pending | pending | 0.2264 | 0.8696 |
| 0.101 | 0.8333 | 0.8333 | pending | pending | 0.2341 | 0.7407 |
| 0.102 | 1 | 0.9524 | pending | pending | 0.2421 | 0.5405 |
| 0.103 | 0.9091 | 0.8 | pending | pending | 0.2507 | 0.6452 |
| 0.104 | 0.9091 | 0.8696 | pending | pending | 0.2582 | 0.6667 |
| 0.105 | 0.9524 | 0.8333 | pending | pending | 0.2662 | 0.5556 |
| 0.106 | 1 | 0.9091 | pending | pending | 0.274 | 0.5882 |
| 0.107 | 1 | 1 | pending | pending | 0.2826 | 0.7143 |
| 0.108 | 1 | 0.9091 | pending | pending | 0.2909 | 0.6667 |
| 0.109 | 1 | 0.7407 | pending | pending | 0.2988 | 0.7143 |
| 0.11 | 1 | 0.9524 | pending | pending | 0.3072 | 0.625 |

## [[242,2,11]]; BP T=242

| X rate p | BP d=0 | BP d=.5 | OSD-0 | CS-10 | Paper CS-60≈ | Q-BP d=.3, depolarizing 1.5p |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 0.06873 | 0.059 | pending | pending | $4.46\times10^{-8}$ | 0.006295 |
| 0.02 | 0.2469 | 0.2151 | pending | pending | $5.781\times10^{-6}$ | 0.005929 |
| 0.03 | 0.4255 | 0.2667 | pending | pending | $1.155\times10^{-4}$ | 0.01284 |
| 0.04 | 0.5263 | 0.4444 | pending | pending | $8.693\times10^{-4}$ | 0.03247 |
| 0.05 | 0.6667 | 0.5556 | pending | pending | 0.00421 | 0.0813 |
| 0.06 | 0.8 | 0.6667 | pending | pending | 0.01444 | 0.1802 |
| 0.07 | 0.9524 | 0.7692 | pending | pending | 0.03778 | 0.2817 |
| 0.08 | 0.9091 | 0.8 | pending | pending | 0.07999 | 0.4255 |
| 0.09 | 0.9524 | 0.8333 | pending | pending | 0.1438 | 0.5714 |
| 0.091 | 0.9091 | 0.8 | pending | pending | 0.1516 | 0.5405 |
| 0.092 | 0.9524 | 0.8 | pending | pending | 0.1591 | 0.7143 |
| 0.093 | 1 | 1 | pending | pending | 0.1665 | 0.7407 |
| 0.094 | 1 | 1 | pending | pending | 0.1751 | 0.625 |
| 0.095 | 1 | 0.9524 | pending | pending | 0.1832 | 0.625 |
| 0.096 | 1 | 0.9524 | pending | pending | 0.1911 | 0.5263 |
| 0.097 | 1 | 0.9091 | pending | pending | 0.2002 | 0.7143 |
| 0.098 | 0.9524 | 0.8696 | pending | pending | 0.2084 | 0.6667 |
| 0.099 | 1 | 0.9524 | pending | pending | 0.2172 | 0.8 |
| 0.1 | 1 | 0.9524 | pending | pending | 0.2259 | 0.8696 |
| 0.101 | 0.9091 | 0.8696 | pending | pending | 0.2353 | 0.8 |
| 0.102 | 1 | 0.9524 | pending | pending | 0.2437 | 0.8 |
| 0.103 | 0.9524 | 0.9524 | pending | pending | 0.2536 | 0.8 |
| 0.105 | 1 | 1 | pending | pending | 0.2714 | 0.8696 |
| 0.106 | 1 | 0.9524 | pending | pending | 0.2812 | 0.9091 |
| 0.107 | 1 | 1 | pending | pending | 0.2907 | 0.7407 |
| 0.108 | 1 | 1 | pending | pending | 0.2997 | 0.7143 |
| 0.109 | 0.9524 | 0.9091 | pending | pending | 0.3094 | 0.9524 |
| 0.11 | 1 | 1 | pending | pending | 0.3187 | 0.7143 |

## [[338,2,13]]; BP T=338

| X rate p | BP d=0 | BP d=.5 | OSD-0 | CS-10 | Paper CS-60≈ | Q-BP d=.3, depolarizing 1.5p |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 0.09346 | 0.06173 | pending | pending | $2.3\times10^{-9}$ | 0.01322 |
| 0.02 | 0.274 | 0.2299 | pending | pending | $1.004\times10^{-6}$ | 0.01144 |
| 0.03 | 0.5556 | 0.5128 | pending | pending | $2.994\times10^{-5}$ | 0.01166 |
| 0.04 | 0.625 | 0.4651 | pending | pending | $3.457\times10^{-4}$ | 0.04357 |
| 0.05 | 0.9524 | 0.6667 | pending | pending | 0.002233 | 0.107 |
| 0.06 | 0.8696 | 0.625 | pending | pending | 0.009488 | 0.1667 |
| 0.07 | 1 | 0.9091 | pending | pending | 0.02912 | 0.303 |
| 0.08 | 1 | 1 | pending | pending | 0.06952 | 0.4651 |
| 0.09 | 0.9524 | 0.8696 | pending | pending | 0.1366 | 0.6897 |
| 0.091 | 1 | 0.9524 | pending | pending | 0.1444 | 0.6897 |
| 0.092 | 1 | 0.9524 | pending | pending | 0.1527 | 0.7143 |
| 0.093 | 1 | 0.9524 | pending | pending | 0.1613 | 0.8696 |
| 0.094 | 1 | 1 | pending | pending | 0.17 | 0.7407 |
| 0.095 | 1 | 0.9524 | pending | pending | 0.1796 | 0.8333 |
| 0.096 | 1 | 0.9524 | pending | pending | 0.1888 | 0.6061 |
| 0.098 | 1 | 1 | pending | pending | 0.2071 | 0.7407 |
| 0.099 | 1 | 0.9091 | pending | pending | 0.2169 | 0.8333 |
| 0.1 | 1 | 1 | pending | pending | 0.227 | 0.8333 |
| 0.101 | 1 | 0.9524 | pending | pending | 0.2369 | 0.9524 |
| 0.102 | 1 | 0.9524 | pending | pending | 0.2474 | 0.7692 |
| 0.103 | 1 | 0.9524 | pending | pending | 0.2578 | 0.8696 |
| 0.104 | 1 | 1 | pending | pending | 0.2685 | 0.9524 |
| 0.105 | 1 | 0.9524 | pending | pending | 0.2775 | 0.9524 |
| 0.106 | 1 | 0.9524 | pending | pending | 0.2882 | 0.9524 |
| 0.107 | 1 | 1 | pending | pending | 0.2991 | 0.9091 |
| 0.108 | 1 | 1 | pending | pending | 0.3093 | 1 |
| 0.109 | 1 | 1 | pending | pending | 0.3205 | 0.9524 |
| 0.11 | 1 | 1 | pending | pending | 0.3303 | 0.8333 |

## [[450,2,15]]; BP T=450

| X rate p | BP d=0 | BP d=.5 | OSD-0 | CS-10 | Paper CS-60≈ | Q-BP d=.3, depolarizing 1.5p |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 0.1307 | 0.1136 | pending | pending | not plotted | 0.01175 |
| 0.02 | 0.3077 | 0.2326 | pending | pending | $1.946\times10^{-7}$ | 0.01326 |
| 0.03 | 0.6897 | 0.5556 | pending | pending | $9.853\times10^{-6}$ | 0.02006 |
| 0.04 | 0.8 | 0.7692 | pending | pending | $1.498\times10^{-4}$ | 0.06667 |
| 0.05 | 1 | 0.7407 | pending | pending | 0.001188 | 0.1227 |
| 0.06 | 1 | 0.9091 | pending | pending | 0.006369 | 0.4545 |
| 0.07 | 1 | 0.9524 | pending | pending | 0.02334 | 0.5263 |
| 0.08 | 1 | 1 | pending | pending | 0.06228 | 0.6667 |
| 0.09 | 1 | 1 | pending | pending | 0.1318 | 0.7692 |
| 0.091 | 1 | 1 | pending | pending | 0.1405 | 0.8333 |
| 0.092 | 1 | 1 | pending | pending | 0.15 | 0.7407 |
| 0.093 | 1 | 1 | pending | pending | 0.1587 | 0.8696 |
| 0.094 | 1 | 0.9524 | pending | pending | 0.1685 | 0.6667 |
| 0.096 | 1 | 1 | pending | pending | 0.187 | 0.8696 |
| 0.097 | 1 | 1 | pending | pending | 0.198 | 0.9091 |
| 0.098 | 1 | 1 | pending | pending | 0.2079 | 0.9091 |
| 0.099 | 1 | 1 | pending | pending | 0.2194 | 0.8696 |
| 0.1 | 1 | 1 | pending | pending | 0.2302 | 0.8333 |
| 0.101 | 1 | 1 | pending | pending | 0.241 | 0.9091 |
| 0.102 | 1 | 1 | pending | pending | 0.2535 | 0.9091 |
| 0.103 | 1 | 0.9524 | pending | pending | 0.2636 | 1 |
| 0.104 | 1 | 0.9524 | pending | pending | 0.2752 | 0.8696 |
| 0.105 | 1 | 0.9524 | pending | pending | 0.2872 | 0.9091 |
| 0.106 | 1 | 0.9524 | pending | pending | 0.2991 | 1 |
| 0.107 | 1 | 1 | pending | pending | 0.3095 | 1 |
| 0.108 | 1 | 1 | pending | pending | 0.3216 | 0.9524 |
| 0.109 | 1 | 1 | pending | pending | 0.3332 | 1 |
| 0.11 | 1 | 1 | pending | pending | 0.345 | 1 |

Complete candidate sets are exposed by the qualified processor API. Shot ledgers bind their set digest, selected candidate, terminal posterior and canonical input; full endpoint replay verifies provenance and work. Timing excludes deterministic warmup, sampling, truth evaluation and ledger I/O. Native/source provenance and benchmark limits are in Spike056.

Raw ledgers remain local under results/. All unavailable/upper-bound results are retained honestly; no automatic source-reproduction or superiority verdict is inferred.
