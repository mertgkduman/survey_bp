# OSD v2 matched benchmark

Single CPU: Intel(R) Xeon(R) Gold 6252 CPU @ 2.10GHz; Slurm 61981163. 9 alternating rounds, 3 actual BP failures per stratum. Warm calls exclude construction/JIT; every v2 call includes mandatory evidence. Times are medians in microseconds.

| Code / channel | OSD | v1 full | v2 fast | v2 full | No affine | Warm cache | Native final |
|---|---:|---:|---:|---:|---:|---:|---:|
| b1_882_nonuniform | 0 | — | 691.2 | 711.4 | 703.9 | 706.0 | 5583.2 |
| b1_882_nonuniform | 1 | — | 1814.6 | 4089.3 | 5371.5 | 817.4 | 15032.1 |
| b1_882_nonuniform | 10 | — | 1894.1 | 4486.3 | 5692.1 | 922.1 | 15927.8 |
| b1_882_nonuniform | 60 | — | 3600.6 | 14761.0 | 20859.8 | 2590.5 | 42079.1 |
| b1_882_uniform | 0 | 434.1 | 742.1 | 657.8 | 657.2 | 661.2 | 5439.4 |
| b1_882_uniform | 1 | 1391.6 | 1407.1 | 3295.5 | 4392.8 | 573.4 | 13080.3 |
| b1_882_uniform | 10 | 1648.6 | 1667.4 | 4313.7 | 5777.8 | 750.1 | 16444.9 |
| b1_882_uniform | 60 | 2267.6 | 2708.9 | 13818.9 | 21060.8 | 1680.0 | 40903.6 |
| lp1054_nonuniform | 0 | — | 946.0 | 847.4 | 840.6 | 871.8 | 48257.6 |
| lp1054_nonuniform | 1 | — | 2658.8 | 6175.1 | 8356.4 | 1254.6 | 74383.8 |
| lp1054_nonuniform | 10 | — | 2621.1 | 6301.4 | 8539.8 | 1286.3 | 71511.2 |
| lp1054_nonuniform | 60 | — | 4857.7 | 18758.5 | 30201.9 | 3512.5 | 139683.1 |
| lp1054_uniform | 0 | 542.3 | 936.9 | 798.8 | 841.3 | 859.8 | 39933.7 |
| lp1054_uniform | 1 | 2309.8 | 2141.7 | 5550.0 | 7634.9 | 873.1 | 63814.3 |
| lp1054_uniform | 10 | 2003.8 | 1836.2 | 4741.9 | 6831.6 | 731.6 | 62238.1 |
| lp1054_uniform | 60 | 3239.1 | 3491.9 | 16998.0 | 26984.7 | 2156.5 | 113974.9 |
| toric15_nonuniform | 0 | — | 360.6 | 323.1 | 333.0 | 336.0 | 158.1 |
| toric15_nonuniform | 1 | — | 582.5 | 858.0 | 1062.5 | 368.8 | 942.0 |
| toric15_nonuniform | 10 | — | 627.2 | 946.2 | 1196.7 | 397.0 | 1077.9 |
| toric15_nonuniform | 60 | — | 1421.7 | 4125.4 | 6334.9 | 1167.5 | 6416.2 |
| toric15_uniform | 0 | 139.0 | 339.4 | 321.8 | 321.2 | 325.3 | 147.3 |
| toric15_uniform | 1 | 365.9 | 559.2 | 825.5 | 1033.2 | 341.2 | 966.7 |
| toric15_uniform | 10 | 389.7 | 591.7 | 901.9 | 1170.2 | 365.2 | 1115.2 |
| toric15_uniform | 60 | 894.7 | 1237.6 | 4130.5 | 6282.2 | 953.0 | 7224.2 |
| toric31_nonuniform | 0 | — | 1578.8 | 1537.1 | 1541.0 | 1556.7 | 665.5 |
| toric31_nonuniform | 1 | — | 5997.3 | 26024.7 | 33032.8 | 2431.8 | 18129.3 |
| toric31_nonuniform | 10 | — | 6144.6 | 27711.2 | 35084.6 | 2543.0 | 19339.8 |
| toric31_nonuniform | 60 | — | 9082.9 | 66133.7 | 89037.2 | 5495.8 | 48981.5 |
| toric31_uniform | 0 | 1505.7 | 2211.1 | 2192.6 | 2168.2 | 2166.2 | 825.3 |
| toric31_uniform | 1 | 4943.9 | 5387.2 | 25227.6 | 33143.2 | 1919.9 | 18287.5 |
| toric31_uniform | 10 | 4952.1 | 5463.9 | 26653.9 | 34266.7 | 1954.3 | 19232.2 |
| toric31_uniform | 60 | 6709.8 | 7550.7 | 65814.8 | 87301.1 | 4078.5 | 50088.2 |
| toric9_nonuniform | 0 | — | 252.4 | 240.6 | 240.1 | 242.1 | 74.1 |
| toric9_nonuniform | 1 | — | 309.4 | 331.8 | 333.6 | 285.3 | 220.7 |
| toric9_nonuniform | 10 | — | 302.9 | 364.5 | 370.9 | 273.3 | 266.4 |
| toric9_nonuniform | 60 | — | 827.9 | 1603.1 | 1877.1 | 742.7 | 2309.9 |
| toric9_uniform | 0 | 80.6 | 228.1 | 216.0 | 216.3 | 220.0 | 63.5 |
| toric9_uniform | 1 | 134.0 | 289.1 | 304.4 | 321.0 | 251.7 | 214.2 |
| toric9_uniform | 10 | 135.9 | 296.0 | 355.6 | 361.0 | 266.6 | 261.0 |
| toric9_uniform | 60 | 361.0 | 775.4 | 1539.3 | 1893.9 | 718.2 | 2331.9 |

All variants, paired round statistics, stage timings and typed work: [benchmark.json](benchmark.json) and [timings.csv](timings.csv).
Whole BP+OSD and activation rates: [pipeline.csv](pipeline.csv). Memory and storage/crossover measurements are in benchmark.json.

## Qualification

{"actual_failure_complete_sets_and_weighted_winners": 240, "matched_ablation_semantic_equivalence": 1200, "tiny_independent_complete_candidate_sets": 400, "tiny_native_weighted_complete_sets": 200}

## Limits

- Fixed small benchmark corpus; no LER, threshold, universal speedup or historic native claim.
- OSD standalone variants use identical unique order-equivalent ranks; actual posteriors qualified separately.
- Native final-only omits candidate hashing/mandatory ledger; native trace used only for qualification.
- Warm and cold basis reuse have different scopes; realistic changing-order cache hit rates are recorded.
- Packing ablation compares byte/bit candidate XOR with packed candidate XOR at the same bitwise scoring rule.
- RSS process high-water reset is OS-dependent; traced memory may omit native allocations.
