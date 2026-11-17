# OSD v2 matched benchmark

Single CPU: Intel(R) Xeon(R) Gold 6252 CPU @ 2.10GHz; Slurm 61984549. 9 alternating rounds, 3 actual BP failures per stratum. Warm calls exclude construction/JIT; every v2 call includes mandatory evidence. Times are medians in microseconds.

| Code / channel | OSD | v1 full | v2 fast | v2 full | No affine | Warm cache | Native final |
|---|---:|---:|---:|---:|---:|---:|---:|
| b1_882_nonuniform | 0 | — | 832.5 | 749.3 | 737.2 | 751.4 | 6875.3 |
| b1_882_nonuniform | 1 | — | 1891.8 | 3583.5 | 4134.8 | 905.6 | 18203.9 |
| b1_882_nonuniform | 10 | — | 1948.7 | 3790.7 | 4402.8 | 955.2 | 17782.0 |
| b1_882_nonuniform | 60 | — | 3582.3 | 12202.1 | 15811.3 | 2623.4 | 48200.5 |
| b1_882_uniform | 0 | 549.3 | 941.7 | 836.1 | 838.3 | 842.5 | 7106.3 |
| b1_882_uniform | 1 | 1715.4 | 1676.1 | 3336.6 | 4005.8 | 693.3 | 17359.3 |
| b1_882_uniform | 10 | 1694.3 | 1701.7 | 3532.8 | 4274.5 | 718.8 | 17828.1 |
| b1_882_uniform | 60 | 2594.1 | 2649.3 | 11307.2 | 15628.5 | 1687.6 | 47767.0 |
| lp1054_nonuniform | 0 | — | 1030.6 | 938.4 | 939.0 | 943.9 | 60556.7 |
| lp1054_nonuniform | 1 | — | 2462.1 | 4923.7 | 6230.0 | 1248.4 | 89127.3 |
| lp1054_nonuniform | 10 | — | 2545.8 | 5144.8 | 6581.6 | 1295.9 | 91532.6 |
| lp1054_nonuniform | 60 | — | 4635.7 | 14251.8 | 21412.7 | 3440.9 | 174663.3 |
| lp1054_uniform | 0 | 554.7 | 956.7 | 856.9 | 858.2 | 864.0 | 47951.3 |
| lp1054_uniform | 1 | 2497.4 | 2120.5 | 4578.4 | 5769.8 | 890.4 | 74581.2 |
| lp1054_uniform | 10 | 2484.6 | 2143.0 | 4758.4 | 6106.8 | 911.5 | 75161.9 |
| lp1054_uniform | 60 | 3521.5 | 3211.8 | 12853.8 | 19123.4 | 1989.4 | 136737.8 |
| toric15_nonuniform | 0 | — | 399.6 | 378.7 | 378.9 | 385.6 | 168.6 |
| toric15_nonuniform | 1 | — | 770.7 | 987.4 | 1067.1 | 465.6 | 1150.3 |
| toric15_nonuniform | 10 | — | 790.0 | 1055.2 | 1165.8 | 489.1 | 1316.5 |
| toric15_nonuniform | 60 | — | 1718.3 | 4197.7 | 5258.7 | 1396.7 | 7901.4 |
| toric15_uniform | 0 | 163.2 | 401.2 | 382.4 | 384.7 | 385.6 | 175.3 |
| toric15_uniform | 1 | 479.1 | 724.0 | 935.6 | 1030.6 | 422.4 | 1178.8 |
| toric15_uniform | 10 | 498.1 | 734.1 | 1019.9 | 1136.3 | 436.1 | 1341.7 |
| toric15_uniform | 60 | 1063.9 | 1399.1 | 3883.9 | 5055.9 | 1058.8 | 8017.3 |
| toric31_nonuniform | 0 | — | 1613.1 | 1568.8 | 1567.8 | 1571.7 | 709.3 |
| toric31_nonuniform | 1 | — | 5936.7 | 20926.1 | 21476.4 | 2392.2 | 18841.8 |
| toric31_nonuniform | 10 | — | 5996.4 | 21689.6 | 22198.2 | 2439.1 | 19475.2 |
| toric31_nonuniform | 60 | — | 8775.0 | 51382.9 | 54296.1 | 5256.0 | 50073.4 |
| toric31_uniform | 0 | 1605.1 | 2301.5 | 2264.1 | 2262.9 | 2266.0 | 890.6 |
| toric31_uniform | 1 | 5194.0 | 5368.9 | 20567.7 | 21581.4 | 1810.2 | 19661.7 |
| toric31_uniform | 10 | 5197.2 | 5504.2 | 21446.5 | 22797.7 | 1863.3 | 20800.7 |
| toric31_uniform | 60 | 7001.0 | 7191.8 | 50926.0 | 55072.4 | 3639.9 | 52719.0 |
| toric9_nonuniform | 0 | — | 303.8 | 289.0 | 289.3 | 293.7 | 86.9 |
| toric9_nonuniform | 1 | — | 518.1 | 539.0 | 538.1 | 443.1 | 349.1 |
| toric9_nonuniform | 10 | — | 546.0 | 579.5 | 585.6 | 455.9 | 453.6 |
| toric9_nonuniform | 60 | — | 1369.3 | 2313.2 | 2873.8 | 1196.0 | 4466.4 |
| toric9_uniform | 0 | 99.5 | 302.9 | 288.6 | 291.7 | 297.1 | 82.9 |
| toric9_uniform | 1 | 162.6 | 359.5 | 364.7 | 374.9 | 305.9 | 248.2 |
| toric9_uniform | 10 | 171.6 | 378.4 | 394.0 | 414.2 | 319.0 | 311.5 |
| toric9_uniform | 60 | 428.9 | 808.9 | 1319.0 | 1946.7 | 689.7 | 2726.5 |

All variants, paired round statistics, stage timings and typed work: [benchmark.json](benchmark.json) and [timings.csv](timings.csv).
Whole BP+OSD and activation rates: [pipeline.csv](pipeline.csv). Memory and storage/crossover measurements are in benchmark.json.

## Qualification

{"actual_failure_complete_sets_and_weighted_winners": 240, "matched_ablation_semantic_equivalence": 1320, "tiny_independent_complete_candidate_sets": 400, "tiny_native_weighted_complete_sets": 200}

## Limits

- Fixed small benchmark corpus; no LER, threshold, universal speedup or historic native claim.
- OSD standalone variants use identical unique order-equivalent ranks; actual posteriors qualified separately.
- Native final-only omits candidate hashing/mandatory ledger; native trace used only for qualification.
- Warm and cold basis reuse have different scopes; realistic changing-order cache hit rates are recorded.
- Packing ablation compares byte/bit candidate XOR with packed candidate XOR at the same bitwise scoring rule.
- RSS process high-water reset is OS-dependent; traced memory may omit native allocations.
