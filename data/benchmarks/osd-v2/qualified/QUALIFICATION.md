# Qualified OSD v2: implementation and performance

Measured on **one CPU**, Intel(R) Xeon(R) Gold 6252 CPU @ 2.10GHz, Slurm 61984549; 9 alternating matched rounds, three actual canonical BP failures per code/channel. Five matrices (n=162, 450, 882, 1054, 1922), two channels, OSD0/CS1/CS10/CS60. All v2 timings include mandatory candidate/weight hashing, original-H validation, stage/work counters and ledger construction. Construction/JIT are separate.

The new processor adds nonuniform scoring, sparse ownership, bounded cache reuse and streamed evidence. Affine reuse and packed XOR/popcount were already present in v1; their ablation gains are not new algorithmic discoveries. Full and fast evidence preserve the same candidate sequence, first winner and digest.

## Independent qualification

| Check | Comparisons |
|---|---:|
| actual_failure_complete_sets_and_weighted_winners | 240 |
| matched_ablation_semantic_equivalence | 1320 |
| tiny_independent_complete_candidate_sets | 400 |
| tiny_native_weighted_complete_sets | 200 |

Counts are comparisons with overlapping fixtures, not independent statistical trials. The dense oracle independently solves each candidate; native weighted and full-candidate comparisons use the unmodified pinned C++ algorithm through a vector-prior bridge. Both source log-inverse-p and separately named Bernoulli likelihood scores are checked. Native qsort ties are controlled with the same stable-order-equivalent ranks for both timed interfaces. Equivalence is also checked on the original BP posteriors. No LER inference is made.

## Before and after

Warm standalone medians, microseconds. v1 includes full candidate materialization/digest, but lacks the v2 ledger/timing/weighted evidence contract. Native timings return the winner only; candidate tracing is enabled for qualification separately.

| Code/channel | Method | v1 full | Initial v2 | Qualified v2 fast | Native final | Paired v1/v2 speed |
|---|---:|---:|---:|---:|---:|---:|
| b1_882_nonuniform | CS10 | — | 2046.0 | 1948.7 | 17782.0 | — |
| b1_882_nonuniform | CS60 | — | 3753.6 | 3582.3 | 48200.5 | — |
| b1_882_uniform | CS10 | 1694.3 | 1735.5 | 1701.7 | 17828.1 | 1.03× |
| b1_882_uniform | CS60 | 2594.1 | 2894.7 | 2649.3 | 47767.0 | 0.96× |
| lp1054_nonuniform | CS10 | — | 2691.6 | 2545.8 | 91532.6 | — |
| lp1054_nonuniform | CS60 | — | 4968.7 | 4635.7 | 174663.3 | — |
| lp1054_uniform | CS10 | 2484.6 | 2317.9 | 2143.0 | 75161.9 | 1.18× |
| lp1054_uniform | CS60 | 3521.5 | 3616.6 | 3211.8 | 136737.8 | 1.09× |
| toric15_nonuniform | CS10 | — | 783.1 | 790.0 | 1316.5 | — |
| toric15_nonuniform | CS60 | — | 1841.9 | 1718.3 | 7901.4 | — |
| toric15_uniform | CS10 | 498.1 | 739.3 | 734.1 | 1341.7 | 0.73× |
| toric15_uniform | CS60 | 1063.9 | 1472.4 | 1399.1 | 8017.3 | 0.81× |
| toric31_nonuniform | CS10 | — | 6184.7 | 5996.4 | 19475.2 | — |
| toric31_nonuniform | CS60 | — | 9153.8 | 8775.0 | 50073.4 | — |
| toric31_uniform | CS10 | 5197.2 | 5561.3 | 5504.2 | 20800.7 | 0.95× |
| toric31_uniform | CS60 | 7001.0 | 7682.3 | 7191.8 | 52719.0 | 0.98× |
| toric9_nonuniform | CS10 | — | 533.8 | 546.0 | 453.6 | — |
| toric9_nonuniform | CS60 | — | 1480.5 | 1369.3 | 4466.4 | — |
| toric9_uniform | CS10 | 171.6 | 365.2 | 378.4 | 311.5 | 0.45× |
| toric9_uniform | CS60 | 428.9 | 892.3 | 808.9 | 2726.5 | 0.53× |

**No blanket speedup:** small uniform inputs and OSD0 often remain slower than v1. The richer evidence contract has a measurable cost. On LP1054 uniform inputs the qualified CS10/CS60 calls improve on v1, while the toric31 uniform comparisons remain mixed. Read each row rather than pooling distinct workloads.

## Matched component ablations

Each entry is the median paired per-stratum ratio across ten code/channel strata, with the stratum minimum–maximum in parentheses. A speed ratio greater than 1 favors the retained implementation. Full-check and materialization rows are cost ratios relative to fast streamed evidence. All retain mandatory digests and ledgers.

| Comparison | OSD0 | CS1 | CS10 | CS60 |
|---|---:|---:|---:|---:|
| Affine reuse speed | 0.95 (0.90–0.99) | 2.29 (1.03–4.03) | 2.39 (1.07–4.09) | 4.56 (2.10–7.58) |
| Live-coefficient response speed | 0.95 (0.88–0.99) | 1.29 (0.99–1.54) | 1.28 (0.97–1.55) | 1.18 (0.93–1.34) |
| Packed vs byte candidate XOR speed, same bit scoring | 1.03 (1.01–1.08) | 1.32 (1.15–1.39) | 1.36 (1.19–1.39) | 1.62 (1.57–1.67) |
| Popcount/set-bit vs all-bit scoring speed | 0.95 (0.89–1.00) | 1.48 (1.03–1.79) | 1.50 (1.04–1.85) | 2.08 (1.56–2.96) |
| 512 vs 128 candidate block speed | 0.96 (0.89–0.99) | 0.98 (0.94–1.01) | 0.98 (0.93–1.02) | 1.02 (1.01–1.09) |
| Incremental optimization vs initial v2 speed | 0.98 (0.96–1.03) | 1.03 (0.96–1.09) | 1.03 (0.98–1.09) | 1.07 (1.04–1.17) |
| Repeated-order cache speed | 1.04 (1.00–1.11) | 2.03 (1.16–2.96) | 1.99 (1.18–2.97) | 1.35 (1.14–1.98) |
| Changing-order one-entry cache speed | 1.04 (1.00–1.11) | 0.95 (0.92–1.01) | 0.96 (0.94–1.01) | 0.98 (0.96–1.05) |
| Full original-H validation cost | 0.95 (0.90–0.99) | 1.95 (1.01–3.84) | 1.99 (1.06–3.87) | 3.22 (1.63–7.14) |
| Candidate materialization cost | 0.97 (0.90–1.00) | 0.98 (0.93–1.03) | 0.98 (0.94–1.02) | 1.03 (0.93–1.05) |

OSD0 bypasses the affine cache and does not construct single responses; ratios near 1 there are measurement variation, not basis-reuse gains. Cache-hit results require repeated exact column orders. The one-entry cache cycles through changing actual failure orders and exposes miss/transform/copy overhead. It is **disabled by default**.

## Whole canonical BP+OSD calls

External whole-call medians, microseconds, include canonical BP, fallback activation and a per-call ledger. v1 uses the same canonical BP engine with a historical-evidence wrapper. v2 has the richer versioned evidence described above. Each sample reruns BP; OSD-only timings must not be substituted for these values.

| Code/channel | Method | Population | OSD calls/shots | v1 full | v2 fast | Cached v2 | No affine v2 |
|---|---:|---|---:|---:|---:|---:|---:|
| toric9_uniform | 0 | failure_conditioned | 3/3 | 696.7 | 930.5 | 929.5 | 934.0 |
| toric9_uniform | 0 | mixed_16_shots | 14/16 | 625.5 | 849.0 | 853.5 | 847.3 |
| toric9_uniform | 10 | failure_conditioned | 3/3 | 761.4 | 1009.1 | 974.8 | 1059.3 |
| toric9_uniform | 10 | mixed_16_shots | 14/16 | 687.8 | 940.2 | 869.2 | 963.2 |
| toric9_uniform | 60 | failure_conditioned | 3/3 | 1048.0 | 1403.2 | 1354.0 | 2645.1 |
| toric9_uniform | 60 | mixed_16_shots | 14/16 | 922.1 | 1230.5 | 1198.2 | 2341.8 |
| lp1054_uniform | 0 | failure_conditioned | 3/3 | 2507.9 | 2913.1 | 2965.7 | 2963.3 |
| lp1054_uniform | 0 | mixed_16_shots | 16/16 | 2542.2 | 2933.5 | 2939.2 | 2931.6 |
| lp1054_uniform | 10 | failure_conditioned | 3/3 | 4466.0 | 4107.7 | 2972.0 | 8114.9 |
| lp1054_uniform | 10 | mixed_16_shots | 16/16 | 4482.5 | 4097.6 | 2903.3 | 8114.8 |
| lp1054_uniform | 60 | failure_conditioned | 3/3 | 5550.1 | 5186.6 | 4052.9 | 21249.3 |
| lp1054_uniform | 60 | mixed_16_shots | 16/16 | 5585.7 | 5176.9 | 4013.6 | 21531.1 |
| lp1054_nonuniform | 0 | failure_conditioned | 3/3 | — | 3081.4 | 3106.2 | 3105.2 |
| lp1054_nonuniform | 0 | mixed_16_shots | 13/16 | — | 2721.1 | 2716.8 | 2721.2 |
| lp1054_nonuniform | 10 | failure_conditioned | 3/3 | — | 4650.6 | 3453.2 | 8762.7 |
| lp1054_nonuniform | 10 | mixed_16_shots | 13/16 | — | 3941.9 | 2979.5 | 7266.3 |
| lp1054_nonuniform | 60 | failure_conditioned | 3/3 | — | 6824.3 | 5645.9 | 24172.8 |
| lp1054_nonuniform | 60 | mixed_16_shots | 13/16 | — | 5673.1 | 4701.8 | 19449.6 |
| toric31_nonuniform | 0 | failure_conditioned | 3/3 | — | 7593.7 | 7636.1 | 7606.7 |
| toric31_nonuniform | 0 | mixed_16_shots | 16/16 | — | 7670.9 | 7733.2 | 7671.1 |
| toric31_nonuniform | 10 | failure_conditioned | 3/3 | — | 11933.6 | 8438.7 | 28118.4 |
| toric31_nonuniform | 10 | mixed_16_shots | 16/16 | — | 11860.4 | 8344.9 | 28088.1 |
| toric31_nonuniform | 60 | failure_conditioned | 3/3 | — | 14679.3 | 11237.0 | 60197.0 |
| toric31_nonuniform | 60 | mixed_16_shots | 16/16 | — | 14522.0 | 10975.0 | 59389.1 |

The mixed population is the first 16 sampled syndromes before failure selection. Some strata have 16/16 failures; the activation fraction is therefore shown explicitly. These bounded fixed samples do not estimate operational LER, average production latency or a threshold. All 280 measured pipeline rows are available in pipeline.csv.

## Sparse/packed storage crossover

OSD-CS10, same first failure per code. Retained bytes include the exact canonical CSR key (shared by CSR views), and packed original H if selected. v1 retains dense H plus packed H. Construction includes channel-weight caching in v2. `auto` picks storage by byte count; measured decode speed can favor packed rows even when CSR saves memory.

| Code | Original storage | Retained matrix bytes | Constructor µs | Decode µs |
|---|---|---:|---:|---:|
| toric9 | sparse | 3,264 | 256.1 | 375.1 |
| toric9 | packed | 5,208 | 259.4 | 360.6 |
| toric9 | v1_dense_and_packed | 15,066 | 55.3 | 137.7 |
| toric15 | sparse | 9,024 | 441.3 | 704.4 |
| toric15 | packed | 23,424 | 430.3 | 678.3 |
| toric15 | v1_dense_and_packed | 115,650 | 127.5 | 474.5 |
| b1_882 | sparse | 24,720 | 756.1 | 1635.9 |
| b1_882 | packed | 74,112 | 750.5 | 1599.9 |
| b1_882 | v1_dense_and_packed | 438,354 | 411.9 | 1692.3 |
| lp1054 | sparse | 33,504 | 833.4 | 2126.1 |
| lp1054 | packed | 96,744 | 862.7 | 2068.4 |
| lp1054 | v1_dense_and_packed | 553,350 | 572.2 | 2520.5 |
| toric31 | sparse | 38,464 | 1367.3 | 5447.8 |
| toric31 | packed | 276,792 | 1449.4 | 5355.7 |
| toric31 | v1_dense_and_packed | 2,085,370 | 1930.0 | 5102.0 |

A packed elimination backend is used after sparse ingestion because elimination can fill in. This experiment profiles original storage, construction and validation crossover; it does not claim a universal sparse-elimination crossover.

## Peak memory

Fresh child processes, JIT/page warmup before measurement. Linux RSS high-water reset availability is recorded in raw data. The traced peak captures Python/NumPy allocation and may omit native allocation; process RSS is independently measured. A zero RSS increment reflects resident-page reuse/granularity, not zero allocation.

| Stratum | Method | Mode | Traced peak bytes | Process peak RSS MiB | RSS increment bytes | Materialized bytes |
|---|---:|---|---:|---:|---:|---:|
| toric9_uniform | 0 | v2_fast | 21,123 | 150.23 | 0 | 0 |
| toric9_uniform | 0 | v2_materialized | 21,420 | 149.70 | 0 | 24 |
| toric9_uniform | 0 | v2_bytes | 22,155 | 149.81 | 0 | 0 |
| toric9_uniform | 0 | v2_full | 21,117 | 150.70 | 0 | 0 |
| toric9_uniform | 1 | v2_fast | 26,962 | 150.49 | 0 | 0 |
| toric9_uniform | 1 | v2_materialized | 31,315 | 150.78 | 0 | 1,992 |
| toric9_uniform | 1 | v2_bytes | 58,863 | 149.31 | 0 | 0 |
| toric9_uniform | 1 | v2_full | 26,994 | 150.70 | 0 | 0 |
| toric9_uniform | 10 | v2_fast | 29,218 | 150.84 | 0 | 0 |
| toric9_uniform | 10 | v2_materialized | 35,731 | 150.58 | 0 | 3,072 |
| toric9_uniform | 10 | v2_bytes | 69,290 | 149.76 | 0 | 0 |
| toric9_uniform | 10 | v2_full | 29,250 | 150.42 | 0 | 0 |
| toric9_uniform | 60 | v2_fast | 63,290 | 150.95 | 0 | 0 |
| toric9_uniform | 60 | v2_materialized | 152,603 | 150.77 | 0 | 44,472 |
| toric9_uniform | 60 | v2_bytes | 241,315 | 150.50 | 110,592 | 0 |
| toric9_uniform | 60 | v2_full | 63,354 | 149.45 | 0 | 0 |
| toric31_nonuniform | 0 | v2_fast | 324,635 | 150.93 | 0 | 0 |
| toric31_nonuniform | 0 | v2_materialized | 325,468 | 150.71 | 0 | 248 |
| toric31_nonuniform | 0 | v2_bytes | 329,527 | 150.63 | 0 | 0 |
| toric31_nonuniform | 0 | v2_full | 324,635 | 150.27 | 0 | 0 |
| toric31_nonuniform | 1 | v2_fast | 769,317 | 151.06 | 110,592 | 0 |
| toric31_nonuniform | 1 | v2_materialized | 1,166,519 | 152.86 | 110,592 | 238,824 |
| toric31_nonuniform | 1 | v2_bytes | 4,543,013 | 153.73 | 1,314,816 | 0 |
| toric31_nonuniform | 1 | v2_full | 769,541 | 152.00 | 0 | 0 |
| toric31_nonuniform | 10 | v2_fast | 781,197 | 150.57 | 122,880 | 0 |
| toric31_nonuniform | 10 | v2_materialized | 1,201,143 | 151.43 | 122,880 | 249,984 |
| toric31_nonuniform | 10 | v2_bytes | 4,630,223 | 153.07 | 790,528 | 0 |
| toric31_nonuniform | 10 | v2_full | 781,421 | 150.88 | 0 | 0 |
| toric31_nonuniform | 60 | v2_fast | 799,517 | 152.23 | 192,512 | 0 |
| toric31_nonuniform | 60 | v2_materialized | 2,002,103 | 151.91 | 0 | 677,784 |
| toric31_nonuniform | 60 | v2_bytes | 4,675,359 | 154.85 | 1,003,520 | 0 |
| toric31_nonuniform | 60 | v2_full | 799,741 | 151.83 | 0 | 0 |

## Stage timing and provenance cost

Median instrumented stage timings for the last fixed fixture of each round, microseconds. “Provenance” sums candidate/weight hashing and ledger/snapshot construction; full original-H checking is shown separately. Input/sort/packing and wrapper gaps remain in total. The external latency tables are authoritative for whole calls.

| Stratum / mode | CS | Factor/transform | Responses/store | Generate/score | Original-H check | Provenance | Instrumented total |
|---|---:|---:|---:|---:|---:|---:|---:|
| toric9_uniform/v2_fast | 10 | 44.1 | 10.3 | 22.2 | 5.5 | 186.0 | 340.5 |
| toric9_uniform/v2_full | 10 | 44.3 | 10.4 | 21.9 | 44.1 | 182.8 | 380.1 |
| toric9_uniform/v2_cache_hit | 10 | 6.8 | 0.3 | 23.1 | 5.5 | 182.1 | 296.9 |
| toric9_uniform/v2_fast | 60 | 44.5 | 10.9 | 145.0 | 6.1 | 430.9 | 717.4 |
| toric9_uniform/v2_full | 60 | 44.9 | 10.7 | 141.8 | 592.1 | 430.6 | 1302.3 |
| toric9_uniform/v2_cache_hit | 60 | 6.6 | 0.3 | 145.4 | 6.0 | 424.5 | 666.6 |
| lp1054_uniform/v2_fast | 10 | 871.4 | 227.6 | 76.7 | 13.6 | 607.8 | 1978.1 |
| lp1054_uniform/v2_full | 10 | 867.6 | 230.3 | 79.7 | 2712.5 | 577.0 | 4685.5 |
| lp1054_uniform/v2_cache_hit | 10 | 19.3 | 0.3 | 79.3 | 15.2 | 582.3 | 873.0 |
| lp1054_uniform/v2_fast | 60 | 870.4 | 233.7 | 244.9 | 16.5 | 1482.7 | 3047.7 |
| lp1054_uniform/v2_full | 60 | 873.2 | 234.7 | 255.8 | 9868.2 | 1321.0 | 12789.8 |
| lp1054_uniform/v2_cache_hit | 60 | 20.2 | 0.3 | 240.7 | 17.2 | 1468.1 | 1940.5 |
| toric31_nonuniform/v2_fast | 10 | 3307.8 | 215.7 | 798.2 | 46.9 | 1282.2 | 5970.3 |
| toric31_nonuniform/v2_full | 10 | 3336.3 | 217.8 | 817.5 | 15831.2 | 1146.7 | 21679.8 |
| toric31_nonuniform/v2_cache_hit | 10 | 55.6 | 0.4 | 786.8 | 47.2 | 1253.9 | 2443.8 |
| toric31_nonuniform/v2_fast | 60 | 3322.0 | 212.7 | 2108.6 | 50.2 | 2771.7 | 8811.8 |
| toric31_nonuniform/v2_full | 60 | 3321.5 | 215.7 | 2052.2 | 42984.8 | 2445.9 | 51396.6 |
| toric31_nonuniform/v2_cache_hit | 60 | 58.9 | 0.5 | 2121.5 | 51.3 | 2789.8 | 5361.2 |

## Scope and decisions

- Retain uniform integer popcount and exact v1 candidate digests; weighted scores are separately encoded and source/ML conventions cannot be pooled.
- Use packed elimination and live-coefficient response construction; keep sparse original storage as an explicit memory/latency choice.
- Keep the exact-order cache opt-in: warm reuse is valuable, changing-order misses can erase it. Its payload budget charges key bytes per entry conservatively, including shared immutable keys.
- Use 512-candidate streaming blocks by default. Pair storage stays bounded by block size; weights remain O(candidate count) through their digest stage.
- Fast evidence is the default; it retains full ordered digests and replay. Use full evidence when checking every candidate is needed, and materialize only for inspection/qualification.
- Affine reuse/packing are inherited foundations; new response, cache, ownership and streaming gains are separated from them. Small-input/OSD0 regressions remain explicit.
- Both benchmark runs, source snapshots, raw timing rounds, fixtures, ledgers, work, peak-memory measurements and source/build identities are retained. Historical simulations and v1 are unchanged.

All source and raw evidence identities: [manifest.json](manifest.json), [benchmark.json](benchmark.json). Full timing and pipeline tables: [timings.csv](timings.csv), [pipeline.csv](pipeline.csv). Algorithm/API contract: [docs/osd-v2.md](../../../../docs/osd-v2.md).
