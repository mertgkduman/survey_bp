# Roffe: joint numerical tuning and runtime-matched iteration sweeps

Checked interpretation: [completed-results assessment and per-cap figure](../../../.planning/quick/261114-pna-audit-completed-runtime-budget-joint-con/FINDINGS.md). Full audit/tuning archives and extraction instructions are in [EVIDENCE.md](EVIDENCE.md).

More iterations lowered BP LER at only1 of107 extended-cap strata. Joint tuning gives a median LER ratio of1.00 across this grid for both families. Actual confirmation runtime is within10% of reference at145/218 selected points;36 are over1.1x and remain flagged.

Independent audit: 218/218 completed point workers; 1464 confirmed control/cap measurements and 163668 retained training measurements.

Target: same-CPU mean warmed canonical BP+OSD0 decoder time per shot at original T=n. Candidate timing excludes sampling, truth evaluation, JIT and I/O. Actual time/reference ratios are shown; within10% is a calibration tolerance, not assumed equality. Values above1.1 exceed the budget. Values below.9 can indicate early-convergence saturation, calibration drift or a still-lower cap; inspect each point plan/history.

Training jointly searches old-V2C damping, constant or paper-scheduled min-sum scaling, and offset in natural-LLR units. Only fresh confirmation is in the main table. All tuning settings/caps are retained in tuning-results.csv. Different iteration caps/settings are explicit, and no unlike policies are pooled. Binary BP is X-only; joint Q-BP remains depolarizing at1.5p_X.

| Code | Decoder/noise | Matched p_X | Physical p | T | d | Scaling | Offset | LER | 95% interval | Mean sweeps | Time / OSD0 | Role |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 7.265 | 0.7532 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 232 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 8.758 | 0.8508 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 10.72 | 0.9174 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 1 | 0 | constant 0.75 | 0.5 | 0.2381 | [0.1519, 0.3342] | 1 | 1.017 | joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 20 | 0 | constant 0.75 | 0.5 | 0.021209 | [0.013, 0.03132] | 1.718 | 1.45 | joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 40 | 0 | constant 0.75 | 0.5 | 0.021209 | [0.013, 0.03132] | 2.142 | 1.581 | joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 81 | 0 | constant 0.75 | 0.5 | 0.021209 | [0.013, 0.03132] | 3.012 | 1.936 | joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 162 | 0 | constant 0.75 | 0.5 | 0.021209 | [0.013, 0.03132] | 4.73 | 2.724 | joint_selected |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 1 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 1 | 0.9747 | previous_damping |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.015361 | [0.009407, 0.02271] | 2.298 | 1.777 | previous_damping |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012293 | [0.007524, 0.01819] | 2.554 | 1.908 | previous_damping |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0063573 | [0.003887, 0.009418] | 2.843 | 2.054 | previous_damping |
| toric9 | bp4/depolarizing | 0.01 | 0.015 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.005226 | [0.003195, 0.007744] | 3.417 | 2.308 | previous_damping |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 162 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.095238 | [0.05915, 0.1383] | 24.63 | 0.8367 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 273 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.090498 | [0.05616, 0.1316] | 34.74 | 1.089 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 324 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.090498 | [0.05616, 0.1316] | 39.35 | 1.204 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 24.53 | 0.9042 | previous_damping |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 32.43 | 1.361 | previous_damping |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 40.33 | 1.202 | previous_damping |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 20 | 0.4 | constant 1 | 0 | 0.036166 | [0.02223, 0.05323] | 2.868 | 0.9037 | joint_selected |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 40 | 0.4 | constant 1 | 0 | 0.021622 | [0.01326, 0.03193] | 3.482 | 1.025 | joint_selected |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 81 | 0.4 | constant 1 | 0 | 0.0087758 | [0.005368, 0.01299] | 4.315 | 1.16 | joint_selected |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 162 | 0.4 | constant 1 | 0 | 0.0069955 | [0.004278, 0.01036] | 4.957 | 1.181 | joint_selected |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 10 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.069204 | [0.04278, 0.1011] | 3 | 0.9514 | previous_damping |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.043764 | [0.02693, 0.0643] | 3.497 | 1.066 | previous_damping |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.021552 | [0.01321, 0.03182] | 4.084 | 1.187 | previous_damping |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0078003 | [0.004771, 0.01155] | 4.876 | 1.397 | previous_damping |
| toric9 | bp4/depolarizing | 0.02 | 0.03 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0041161 | [0.002516, 0.006101] | 5.283 | 1.385 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 162 | 0.5 | constant 1 | 0 | 0.16393 | [0.1031, 0.2343] | 30.98 | 0.5507 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 324 | 0.5 | constant 1 | 0 | 0.1626 | [0.1022, 0.2325] | 58.98 | 0.8976 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 648 | 0.5 | constant 1 | 0 | 0.1626 | [0.1022, 0.2325] | 111.7 | 1.613 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 38.76 | 0.6562 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 283 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 58.76 | 0.9187 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 65.54 | 1.024 | previous_damping |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 20 | 0.5 | constant 1 | 0 | 0.084388 | [0.05231, 0.1229] | 4.882 | 0.9042 | joint_selected |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 40 | 0.5 | constant 1 | 0 | 0.021299 | [0.01306, 0.03145] | 5.59 | 0.9615 | joint_selected |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 81 | 0.5 | constant 1 | 0 | 0.0074019 | [0.004527, 0.01096] | 5.704 | 1.002 | joint_selected |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 121 | 0.5 | constant 1 | 0 | 0.006068 | [0.00371, 0.00899] | 6.074 | 1.057 | joint_selected |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 162 | 0.5 | constant 1 | 0 | 0.006068 | [0.00371, 0.00899] | 6.323 | 1.072 | joint_selected |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.066007 | [0.04078, 0.09651] | 5.053 | 0.9077 | previous_damping |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 25 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.047393 | [0.02919, 0.06958] | 5.209 | 0.9736 | previous_damping |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.025221 | [0.01547, 0.03721] | 5.817 | 0.9981 | previous_damping |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0080678 | [0.004935, 0.01195] | 6.073 | 1.023 | previous_damping |
| toric9 | bp4/depolarizing | 0.03 | 0.045 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0068681 | [0.0042, 0.01017] | 6.74 | 1.11 | previous_damping |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 162 | 0.3 | constant 1 | 0 | 0.20619 | [0.1307, 0.2917] | 46.19 | 0.5417 | joint_selected |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 253 | 0.3 | constant 1 | 0 | 0.20619 | [0.1307, 0.2917] | 64.95 | 0.7047 | joint_selected |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 324 | 0.3 | constant 1 | 0 | 0.20619 | [0.1307, 0.2917] | 79.59 | 0.8365 | joint_selected |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.21739 | [0.1381, 0.3067] | 45.65 | 0.5347 | previous_damping |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 263 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.21739 | [0.1381, 0.3067] | 67.61 | 0.7295 | previous_damping |
| toric9 | binary_css/x_only | 0.04 | 0.04 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.21739 | [0.1381, 0.3067] | 80.87 | 0.8432 | previous_damping |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 20 | 0.5 | constant 1 | 0 | 0.093897 | [0.0583, 0.1364] | 6.408 | 0.6297 | joint_selected |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 40 | 0.5 | constant 1 | 0 | 0.05988 | [0.03696, 0.08767] | 8.419 | 0.8268 | joint_selected |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 81 | 0.5 | constant 1 | 0 | 0.027473 | [0.01686, 0.04051] | 9.843 | 0.9126 | joint_selected |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 121 | 0.5 | constant 1 | 0 | 0.020429 | [0.01252, 0.03017] | 10.57 | 0.9916 | joint_selected |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 162 | 0.5 | constant 1 | 0 | 0.020429 | [0.01252, 0.03017] | 11.41 | 1.062 | joint_selected |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.096618 | [0.06002, 0.1403] | 6.623 | 0.7545 | previous_damping |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.062305 | [0.03847, 0.09117] | 8.773 | 0.8447 | previous_damping |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.038095 | [0.02342, 0.05605] | 10.84 | 0.9713 | previous_damping |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 101 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.027473 | [0.01686, 0.04051] | 10.94 | 0.9718 | previous_damping |
| toric9 | bp4/depolarizing | 0.04 | 0.06 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.027473 | [0.01686, 0.04051] | 12.61 | 1.1 | previous_damping |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 98.5 | 0.8881 | joint_selected |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 232 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 139.7 | 1.238 | joint_selected |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 324 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 193.8 | 2.127 | joint_selected |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 99.26 | 1.302 | previous_damping |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 263 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 157 | 1.391 | previous_damping |
| toric9 | binary_css/x_only | 0.05 | 0.05 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 191.8 | 1.487 | previous_damping |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 20 | 0.4 | constant 1 | 0 | 0.18018 | [0.1137, 0.2565] | 8.919 | 0.9151 | joint_selected |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 40 | 0.4 | constant 1 | 0 | 0.088106 | [0.05465, 0.1282] | 12 | 1.16 | joint_selected |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 45 | 0.4 | constant 1 | 0 | 0.088106 | [0.05465, 0.1282] | 12.44 | 1.218 | joint_selected |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 81 | 0.4 | constant 1 | 0 | 0.075188 | [0.04653, 0.1097] | 15.06 | 1.382 | joint_selected |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 162 | 0.4 | constant 1 | 0 | 0.066007 | [0.04078, 0.09651] | 20.62 | 1.851 | joint_selected |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.17241 | [0.1086, 0.2459] | 8.897 | 0.9052 | previous_damping |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.125 | [0.07805, 0.1803] | 10.26 | 1.005 | previous_damping |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.092593 | [0.05748, 0.1346] | 12.16 | 1.159 | previous_damping |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.066007 | [0.04078, 0.09651] | 15.35 | 1.417 | previous_damping |
| toric9 | bp4/depolarizing | 0.05 | 0.075 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.063694 | [0.03934, 0.09317] | 20.57 | 1.814 | previous_damping |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 162 | 0.4 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 98.15 | 0.7396 | joint_selected |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 263 | 0.4 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 147.4 | 1.028 | joint_selected |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 324 | 0.4 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 177.1 | 1.259 | joint_selected |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 99.36 | 0.7435 | previous_damping |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 253 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 146 | 1.027 | previous_damping |
| toric9 | binary_css/x_only | 0.06 | 0.06 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 182.4 | 1.322 | previous_damping |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 20 | 0.4 | constant 1 | 0 | 0.14706 | [0.0922, 0.211] | 9.419 | 0.8784 | joint_selected |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 40 | 0.4 | constant 1 | 0 | 0.076336 | [0.04725, 0.1113] | 12.26 | 0.9154 | joint_selected |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 50 | 0.4 | constant 1 | 0 | 0.074627 | [0.04618, 0.1089] | 13.25 | 1.018 | joint_selected |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 81 | 0.4 | constant 1 | 0 | 0.074627 | [0.04618, 0.1089] | 15.57 | 1.118 | joint_selected |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 162 | 0.4 | constant 1 | 0 | 0.073529 | [0.04549, 0.1073] | 21.76 | 1.49 | joint_selected |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.13793 | [0.08633, 0.1984] | 9.586 | 0.751 | previous_damping |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 35 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.088496 | [0.05489, 0.1287] | 11.86 | 0.8966 | previous_damping |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.076336 | [0.04725, 0.1113] | 12.35 | 0.9256 | previous_damping |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.074627 | [0.04618, 0.1089] | 15.68 | 1.131 | previous_damping |
| toric9 | bp4/depolarizing | 0.06 | 0.09 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.073529 | [0.04549, 0.1073] | 22.06 | 1.516 | previous_damping |
| toric9 | binary_css/x_only | 0.07 | 0.07 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 130.8 | 0.8519 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.07 | 0.07 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 193.2 | 1.16 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.07 | 0.07 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 255.5 | 1.423 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.07 | 0.105 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 13.58 | 0.9899 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.07 | 0.105 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.34483 | [0.2249, 0.4706] | 17.05 | 1.109 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.07 | 0.105 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.33333 | [0.2169, 0.4564] | 20.52 | 1.348 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.07 | 0.105 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 31.45 | 1.923 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.07 | 0.105 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 52.76 | 3.047 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 162 | 0.5 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 102.3 | 0.6229 | joint_selected |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 253 | 0.5 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 155.1 | 1.297 | joint_selected |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 324 | 0.5 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 196.4 | 1.064 | joint_selected |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 107.7 | 0.6669 | previous_damping |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 154.7 | 0.882 | previous_damping |
| toric9 | binary_css/x_only | 0.08 | 0.08 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 201.8 | 1.121 | previous_damping |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 20 | 0.3 | constant 1 | 0 | 0.42553 | [0.2826, 0.5677] | 14.4 | 0.9349 | joint_selected |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 21 | 0.3 | constant 1 | 0 | 0.40816 | [0.27, 0.5473] | 14.96 | 0.9718 | joint_selected |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 40 | 0.3 | constant 1 | 0 | 0.2381 | [0.1519, 0.3342] | 20.93 | 1.292 | joint_selected |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 81 | 0.3 | constant 1 | 0 | 0.2381 | [0.1519, 0.3342] | 30.69 | 1.81 | joint_selected |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 162 | 0.3 | constant 1 | 0 | 0.2381 | [0.1519, 0.3342] | 49.98 | 2.743 | joint_selected |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 14.64 | 0.9522 | previous_damping |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 21 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 15.09 | 1.002 | previous_damping |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.2381 | [0.1519, 0.3342] | 20.76 | 1.306 | previous_damping |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.2381 | [0.1519, 0.3342] | 30.52 | 1.844 | previous_damping |
| toric9 | bp4/depolarizing | 0.08 | 0.12 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.2381 | [0.1519, 0.3342] | 49.81 | 2.863 | previous_damping |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 162 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 144.6 | 1.269 | joint_selected |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 232 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 202.4 | 1.248 | joint_selected |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 324 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 278.4 | 1.584 | joint_selected |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 147.8 | 0.8601 | previous_damping |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 232 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 203.5 | 1.114 | previous_damping |
| toric9 | binary_css/x_only | 0.09 | 0.09 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 276.3 | 2.03 | previous_damping |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 20 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 18.11 | 1.076 | joint_selected |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 22 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 19.54 | 1.158 | joint_selected |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 40 | 0.3 | constant 1 | 0 | 0.60606 | [0.4214, 0.763] | 31.39 | 1.749 | joint_selected |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 81 | 0.3 | constant 1 | 0 | 0.60606 | [0.4214, 0.763] | 56.24 | 2.984 | joint_selected |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 162 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 104.8 | 5.953 | joint_selected |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 17.96 | 1.092 | previous_damping |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 21 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 18.68 | 1.091 | previous_damping |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 31.09 | 1.757 | previous_damping |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.55556 | [0.381, 0.7117] | 54.61 | 2.902 | previous_damping |
| toric9 | bp4/depolarizing | 0.09 | 0.135 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.55556 | [0.381, 0.7117] | 99.61 | 5.118 | previous_damping |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 162 | 0.4 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 126.4 | 0.9135 | joint_selected |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 222 | 0.4 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 169.6 | 1.025 | joint_selected |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 324 | 0.4 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 243.1 | 2.122 | joint_selected |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 123.4 | 0.716 | previous_damping |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 222 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 162.7 | 1.522 | previous_damping |
| toric9 | binary_css/x_only | 0.091 | 0.091 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 229.3 | 1.512 | previous_damping |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 20 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 16.41 | 0.9582 | joint_selected |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 40 | 0.3 | constant 1 | 0 | 0.41667 | [0.2761, 0.5573] | 25.96 | 1.388 | joint_selected |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 81 | 0.3 | constant 1 | 0 | 0.33898 | [0.2208, 0.4634] | 40.76 | 2.023 | joint_selected |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 162 | 0.3 | constant 1 | 0 | 0.33333 | [0.2169, 0.4564] | 67.52 | 3.325 | joint_selected |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.55556 | [0.381, 0.7117] | 16.56 | 1.017 | previous_damping |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.38462 | [0.253, 0.5192] | 26.25 | 1.396 | previous_damping |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.35088 | [0.2291, 0.4781] | 39.77 | 2.054 | previous_damping |
| toric9 | bp4/depolarizing | 0.091 | 0.1365 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.33898 | [0.2208, 0.4634] | 66.27 | 3.531 | previous_damping |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 162 | 0.5 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 133.9 | 1.236 | joint_selected |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 232 | 0.5 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 187.8 | 1.002 | joint_selected |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 324 | 0.5 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 258.5 | 1.283 | joint_selected |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 146.6 | 0.8502 | previous_damping |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 222 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 198.8 | 1.07 | previous_damping |
| toric9 | binary_css/x_only | 0.093 | 0.093 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 287.5 | 1.498 | previous_damping |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 20 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 18.03 | 1.046 | joint_selected |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 40 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 29.97 | 1.64 | joint_selected |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 81 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 52.88 | 2.725 | joint_selected |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 162 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 98.15 | 4.845 | joint_selected |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 17.7 | 1.051 | previous_damping |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 31.03 | 1.664 | previous_damping |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 55.03 | 2.818 | previous_damping |
| toric9 | bp4/depolarizing | 0.093 | 0.1395 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 101.9 | 5.036 | previous_damping |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 162 | 0.4 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 110.7 | 0.5967 | joint_selected |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 243 | 0.4 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 155.2 | 0.788 | joint_selected |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 324 | 0.4 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 198.2 | 0.9879 | joint_selected |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 115.5 | 0.5999 | previous_damping |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 253 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 174 | 1.312 | previous_damping |
| toric9 | binary_css/x_only | 0.094 | 0.094 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 219.6 | 1.081 | previous_damping |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 20 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 16.14 | 0.969 | joint_selected |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 40 | 0.3 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 28.94 | 1.603 | joint_selected |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 81 | 0.3 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 50.72 | 2.584 | joint_selected |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 162 | 0.3 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 93.75 | 4.566 | joint_selected |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 16.67 | 0.9878 | previous_damping |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 28.48 | 1.591 | previous_damping |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 51.06 | 2.585 | previous_damping |
| toric9 | bp4/depolarizing | 0.094 | 0.141 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 94.09 | 4.599 | previous_damping |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 162 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 127.4 | 0.6889 | joint_selected |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 232 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 177 | 0.8971 | joint_selected |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 324 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 242.1 | 1.187 | joint_selected |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 130.2 | 0.6859 | previous_damping |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 190.1 | 0.9279 | previous_damping |
| toric9 | binary_css/x_only | 0.095 | 0.095 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 250 | 1.195 | previous_damping |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 20 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 18.07 | 1.029 | joint_selected |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 40 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 32 | 1.66 | joint_selected |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 81 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 58.18 | 2.939 | joint_selected |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 162 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 105.8 | 5.199 | joint_selected |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 18.61 | 1.042 | previous_damping |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 31.42 | 2.136 | previous_damping |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 57.59 | 2.902 | previous_damping |
| toric9 | bp4/depolarizing | 0.095 | 0.1425 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 105.4 | 5.077 | previous_damping |
| toric9 | binary_css/x_only | 0.099 | 0.099 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 159.2 | 0.8822 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.099 | 0.099 | 222 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 214.2 | 1.136 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.099 | 0.099 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 306.9 | 1.576 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 18 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 15.97 | 0.9777 | joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 20 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 17.3 | 1.045 | joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 40 | 0.3 | constant 1 | 0 | 0.54054 | [0.3692, 0.6959] | 29.22 | 1.677 | joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 81 | 0.3 | constant 1 | 0 | 0.5 | [0.338, 0.6522] | 49.23 | 3.101 | joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 162 | 0.3 | constant 1 | 0 | 0.5 | [0.338, 0.6522] | 87.7 | 4.731 | joint_selected |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 16.07 | 1.217 | previous_damping |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 17.5 | 1.058 | previous_damping |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 29.43 | 2.16 | previous_damping |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 47.4 | 2.657 | previous_damping |
| toric9 | bp4/depolarizing | 0.099 | 0.1485 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 83.64 | 5.216 | previous_damping |
| toric9 | binary_css/x_only | 0.1 | 0.1 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 133.6 | 0.7872 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.1 | 0.1 | 222 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 179.2 | 0.9934 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.1 | 0.1 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 256.8 | 1.465 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.1 | 0.15 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 17.87 | 0.9933 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.1 | 0.15 | 22 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 19.29 | 1.12 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.1 | 0.15 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 31.16 | 1.63 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.1 | 0.15 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 55.55 | 2.757 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.1 | 0.15 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 102.2 | 4.938 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 150.9 | 0.86 | joint_selected |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 202 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 183.6 | 1.024 | joint_selected |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 324 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 278.8 | 1.495 | joint_selected |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 143.2 | 0.807 | previous_damping |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 202 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 172.4 | 0.9647 | previous_damping |
| toric9 | binary_css/x_only | 0.101 | 0.101 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 261.6 | 1.36 | previous_damping |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 20 | 0.3 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 16.14 | 0.9517 | joint_selected |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 40 | 0.3 | constant 1 | 0 | 0.42553 | [0.2826, 0.5677] | 24.3 | 1.36 | joint_selected |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 81 | 0.3 | constant 1 | 0 | 0.37736 | [0.2479, 0.5104] | 40.72 | 2.209 | joint_selected |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 162 | 0.3 | constant 1 | 0 | 0.37037 | [0.2429, 0.502] | 70.3 | 3.982 | joint_selected |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 15.27 | 0.909 | previous_damping |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 16.44 | 0.972 | previous_damping |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4 | [0.2641, 0.5376] | 25.52 | 1.442 | previous_damping |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.38462 | [0.253, 0.5192] | 41.48 | 2.25 | previous_damping |
| toric9 | bp4/depolarizing | 0.101 | 0.1515 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.37736 | [0.2479, 0.5104] | 71.47 | 3.74 | previous_damping |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 162 | 0.5 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 133.8 | 0.7581 | joint_selected |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 243 | 0.5 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 195.4 | 0.9069 | joint_selected |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 324 | 0.5 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 257 | 1.227 | joint_selected |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 133.6 | 0.7498 | previous_damping |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 195.2 | 0.9681 | previous_damping |
| toric9 | binary_css/x_only | 0.102 | 0.102 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 256.8 | 1.244 | previous_damping |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 18 | 0.4 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 16.84 | 1.017 | joint_selected |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 20 | 0.4 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 18.44 | 1.107 | joint_selected |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 40 | 0.4 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 32.82 | 1.82 | joint_selected |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 81 | 0.4 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 59.21 | 3.145 | joint_selected |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 162 | 0.4 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 106.5 | 5.425 | joint_selected |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 16.3 | 0.9642 | previous_damping |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 17.78 | 1.037 | previous_damping |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 32.82 | 2.456 | previous_damping |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 58.29 | 3.93 | previous_damping |
| toric9 | bp4/depolarizing | 0.102 | 0.153 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.55556 | [0.381, 0.7117] | 105.4 | 5.703 | previous_damping |
| toric9 | binary_css/x_only | 0.103 | 0.103 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 129.4 | 0.7345 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.103 | 0.103 | 212 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 166 | 0.8797 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.103 | 0.103 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 247.8 | 1.226 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 20 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 17.57 | 1.025 | joint_selected |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 40 | 0.3 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 28.51 | 1.967 | joint_selected |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 81 | 0.3 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 51.94 | 2.651 | joint_selected |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 162 | 0.3 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 98.23 | 4.869 | joint_selected |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 16.2 | 0.9069 | previous_damping |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 17.93 | 1.008 | previous_damping |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 28.97 | 1.542 | previous_damping |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 52.4 | 2.688 | previous_damping |
| toric9 | bp4/depolarizing | 0.103 | 0.1545 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 98.69 | 5.547 | previous_damping |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 162 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 124.9 | 0.7806 | joint_selected |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 243 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 177.8 | 1.017 | joint_selected |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 324 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 230.8 | 1.266 | joint_selected |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 123.6 | 1.066 | previous_damping |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 202 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 150.2 | 0.8815 | previous_damping |
| toric9 | binary_css/x_only | 0.104 | 0.104 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 231.6 | 1.25 | previous_damping |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 18 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 15.44 | 0.9207 | joint_selected |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 20 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 16.85 | 0.9915 | joint_selected |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 40 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 30.3 | 1.707 | joint_selected |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 81 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 56.27 | 2.98 | joint_selected |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 162 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 107.6 | 7.299 | joint_selected |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 15.86 | 0.9464 | previous_damping |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 17.21 | 1.029 | previous_damping |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 29.52 | 1.619 | previous_damping |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 53.12 | 3.161 | previous_damping |
| toric9 | bp4/depolarizing | 0.104 | 0.156 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 99.76 | 5.147 | previous_damping |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 162 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 147.9 | 0.8941 | joint_selected |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 202 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 180.9 | 1.066 | joint_selected |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 324 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 281.7 | 1.568 | joint_selected |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 147.7 | 0.8996 | previous_damping |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 214.6 | 1.235 | previous_damping |
| toric9 | binary_css/x_only | 0.105 | 0.105 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 281.5 | 1.581 | previous_damping |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 20 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 17.69 | 1.436 | joint_selected |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 40 | 0.3 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 30.69 | 1.694 | joint_selected |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 81 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 52.97 | 3.164 | joint_selected |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 162 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 95.85 | 4.913 | joint_selected |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 16.38 | 0.9708 | previous_damping |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 17.48 | 1.024 | previous_damping |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 30.32 | 1.686 | previous_damping |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 53.65 | 2.832 | previous_damping |
| toric9 | bp4/depolarizing | 0.105 | 0.1575 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 96.53 | 4.951 | previous_damping |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 162 | 0.6 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 137.7 | 0.873 | joint_selected |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 202 | 0.6 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 168.1 | 1.02 | joint_selected |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 324 | 0.6 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 260.8 | 1.512 | joint_selected |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 135.7 | 0.8567 | previous_damping |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 192 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 158.5 | 0.985 | previous_damping |
| toric9 | binary_css/x_only | 0.106 | 0.106 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 258.8 | 1.504 | previous_damping |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 18 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 16.36 | 1.559 | joint_selected |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 20 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 18.09 | 1.07 | joint_selected |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 40 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 32.43 | 1.859 | joint_selected |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 81 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 59.77 | 3.217 | joint_selected |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 162 | 0.3 | constant 1 | 0 | 0.625 | [0.4369, 0.7815] | 104.7 | 5.448 | joint_selected |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 16.73 | 0.9927 | previous_damping |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 18.45 | 1.095 | previous_damping |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 32.96 | 2.534 | previous_damping |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 60.14 | 3.948 | previous_damping |
| toric9 | bp4/depolarizing | 0.106 | 0.159 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 111.3 | 6.353 | previous_damping |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 162 | 0.6 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 141.4 | 0.823 | joint_selected |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 202 | 0.6 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 175.9 | 0.9814 | joint_selected |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 324 | 0.6 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 281.3 | 1.453 | joint_selected |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 141.7 | 0.8457 | previous_damping |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 202 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 174.8 | 1.002 | previous_damping |
| toric9 | binary_css/x_only | 0.107 | 0.107 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 275.6 | 1.434 | previous_damping |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 20 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 17.83 | 1.026 | joint_selected |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 40 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 30.87 | 1.661 | joint_selected |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 81 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 56 | 2.854 | joint_selected |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 162 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 105.6 | 5.259 | joint_selected |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 16.44 | 1.544 | previous_damping |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 17.96 | 1.03 | previous_damping |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 31.59 | 1.733 | previous_damping |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 57.42 | 2.97 | previous_damping |
| toric9 | bp4/depolarizing | 0.107 | 0.1605 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 107.1 | 5.283 | previous_damping |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 162 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 128.3 | 0.7683 | joint_selected |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 243 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 187.5 | 1.04 | joint_selected |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 324 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 246.7 | 1.302 | joint_selected |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 129 | 0.7724 | previous_damping |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 202 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 158.3 | 0.9078 | previous_damping |
| toric9 | binary_css/x_only | 0.108 | 0.108 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 247.4 | 1.315 | previous_damping |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 18 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 15.57 | 0.9616 | joint_selected |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 20 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 16.83 | 1 | joint_selected |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 40 | 0.3 | constant 1 | 0 | 0.57143 | [0.3935, 0.7281] | 28.23 | 1.55 | joint_selected |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 81 | 0.3 | constant 1 | 0 | 0.55556 | [0.381, 0.7117] | 50.33 | 2.695 | joint_selected |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 162 | 0.3 | constant 1 | 0 | 0.55556 | [0.381, 0.7117] | 90.83 | 4.536 | joint_selected |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 15.64 | 0.9067 | previous_damping |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 17.11 | 0.9862 | previous_damping |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 29.75 | 1.628 | previous_damping |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 54.09 | 2.821 | previous_damping |
| toric9 | bp4/depolarizing | 0.108 | 0.162 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 98.97 | 4.913 | previous_damping |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 162 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 148 | 0.8294 | joint_selected |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 232 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 205.9 | 1.052 | joint_selected |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 324 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 281.9 | 1.708 | joint_selected |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 149.8 | 0.8576 | previous_damping |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 192 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 175.7 | 0.9021 | previous_damping |
| toric9 | binary_css/x_only | 0.109 | 0.109 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 289.7 | 1.462 | previous_damping |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 18 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 15.96 | 0.9288 | joint_selected |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 20 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 17.39 | 1.544 | joint_selected |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 40 | 0.3 | constant 1 | 0 | 0.54054 | [0.3692, 0.6959] | 30.08 | 1.609 | joint_selected |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 81 | 0.3 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 50.51 | 2.834 | joint_selected |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 162 | 0.3 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 87.9 | 4.194 | joint_selected |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 16.46 | 0.9598 | previous_damping |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 17.86 | 1.029 | previous_damping |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 30.7 | 1.653 | previous_damping |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 51.5 | 2.652 | previous_damping |
| toric9 | bp4/depolarizing | 0.109 | 0.1635 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 87.95 | 4.235 | previous_damping |
| toric9 | binary_css/x_only | 0.11 | 0.11 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 148.4 | 1.097 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.11 | 0.11 | 222 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 202.9 | 0.8989 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.11 | 0.11 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 295.6 | 1.217 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.11 | 0.165 | 18 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 17.26 | 0.9845 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.11 | 0.165 | 20 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 18.96 | 1.077 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.11 | 0.165 | 40 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 32.47 | 1.728 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.11 | 0.165 | 81 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 57.37 | 2.925 | previous_damping,joint_selected |
| toric9 | bp4/depolarizing | 0.11 | 0.165 | 162 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 106 | 5.145 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 242 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.033613 | [0.02065, 0.0495] | 11.88 | 0.555 | joint_selected |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 453 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.033613 | [0.02065, 0.0495] | 18.97 | 0.7701 | joint_selected |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 484 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.033613 | [0.02065, 0.0495] | 20.02 | 0.8016 | joint_selected |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.035778 | [0.02199, 0.05266] | 12.13 | 0.5839 | previous_damping |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 468 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.035778 | [0.02199, 0.05266] | 20.21 | 0.8093 | previous_damping |
| toric11 | binary_css/x_only | 0.01 | 0.01 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.035778 | [0.02199, 0.05266] | 20.78 | 0.8278 | previous_damping |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 30 | 0.5 | constant 1 | 0 | 0.027816 | [0.01707, 0.04102] | 2.381 | 0.9688 | joint_selected |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 43 | 0.5 | constant 1 | 0 | 0.020305 | [0.01245, 0.02999] | 2.65 | 1.034 | joint_selected |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 60 | 0.5 | constant 1 | 0 | 0.017361 | [0.01064, 0.02566] | 2.944 | 1.111 | joint_selected |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 121 | 0.5 | constant 1 | 0 | 0.0081599 | [0.004991, 0.01208] | 3.488 | 1.269 | joint_selected |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 242 | 0.5 | constant 1 | 0 | 0.0081599 | [0.004991, 0.01208] | 4.476 | 1.542 | joint_selected |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 9 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.045558 | [0.02805, 0.06691] | 2.371 | 1.011 | previous_damping |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.027816 | [0.01707, 0.04102] | 3.108 | 1.219 | previous_damping |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.018198 | [0.01115, 0.02689] | 3.67 | 1.363 | previous_damping |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0098717 | [0.00604, 0.01461] | 4.355 | 1.546 | previous_damping |
| toric11 | bp4/depolarizing | 0.01 | 0.015 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0089445 | [0.005472, 0.01324] | 5.542 | 1.929 | previous_damping |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 242 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 55.36 | 0.9201 | joint_selected |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 332 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 69.88 | 1.094 | joint_selected |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 484 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 94.4 | 1.416 | joint_selected |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.18018 | [0.1137, 0.2565] | 51.07 | 0.823 | previous_damping |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 393 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.18018 | [0.1137, 0.2565] | 78.28 | 1.167 | previous_damping |
| toric11 | binary_css/x_only | 0.02 | 0.02 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.18018 | [0.1137, 0.2565] | 94.68 | 1.376 | previous_damping |
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.00369 | [0.002255, 0.00547] | 6.309 | 0.9643 | joint_selected |
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.00369 | [0.002255, 0.00547] | 7.202 | 1.078 | joint_selected |
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0052002 | [0.003179, 0.007706] | 6.882 | 1.03 | previous_damping |
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 484 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0052002 | [0.003179, 0.007706] | 8.141 | 1.19 | previous_damping |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 242 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 95.03 | 0.8636 | joint_selected |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 347 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 122.7 | 1.092 | joint_selected |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 484 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 158.7 | 1.373 | joint_selected |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 85 | 0.7577 | previous_damping |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 378 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 120.8 | 1.04 | previous_damping |
| toric11 | binary_css/x_only | 0.03 | 0.03 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.26316 | [0.1687, 0.367] | 148.7 | 1.245 | previous_damping |
| toric11 | bp4/depolarizing | 0.03 | 0.045 | 242 | 0.7 | constant 1 | 0 | 0.0065274 | [0.003992, 0.00967] | 10.57 | 0.9085 | joint_selected |
| toric11 | bp4/depolarizing | 0.03 | 0.045 | 484 | 0.7 | constant 1 | 0 | 0.0065274 | [0.003992, 0.00967] | 12.15 | 1.018 | joint_selected |
| toric11 | bp4/depolarizing | 0.03 | 0.045 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012674 | [0.007758, 0.01875] | 10.83 | 0.8996 | previous_damping |
| toric11 | bp4/depolarizing | 0.03 | 0.045 | 484 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012674 | [0.007758, 0.01875] | 13.9 | 1.117 | previous_damping |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 242 | 0.3 | constant 1 | 0 | 0.44444 | [0.2964, 0.5897] | 118.5 | 0.7285 | joint_selected |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 363 | 0.3 | constant 1 | 0 | 0.44444 | [0.2964, 0.5897] | 172.3 | 1.007 | joint_selected |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 484 | 0.3 | constant 1 | 0 | 0.44444 | [0.2964, 0.5897] | 226 | 1.316 | joint_selected |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 118.1 | 0.718 | previous_damping |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 378 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 178.6 | 1.242 | previous_damping |
| toric11 | binary_css/x_only | 0.04 | 0.04 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 225.7 | 1.281 | previous_damping |
| toric11 | bp4/depolarizing | 0.04 | 0.06 | 242 | 0.6 | constant 1 | 0 | 0.02193 | [0.01345, 0.03238] | 14.95 | 0.903 | joint_selected |
| toric11 | bp4/depolarizing | 0.04 | 0.06 | 484 | 0.6 | constant 1 | 0 | 0.02193 | [0.01345, 0.03238] | 20.26 | 1.176 | joint_selected |
| toric11 | bp4/depolarizing | 0.04 | 0.06 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.024814 | [0.01522, 0.03661] | 15.49 | 0.9243 | previous_damping |
| toric11 | bp4/depolarizing | 0.04 | 0.06 | 484 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.024814 | [0.01522, 0.03661] | 21.49 | 1.241 | previous_damping |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 165.7 | 0.853 | joint_selected |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 332 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 225.4 | 1.434 | joint_selected |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 484 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 320.4 | 1.537 | joint_selected |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 165.3 | 0.8374 | previous_damping |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 363 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 243.4 | 1.502 | previous_damping |
| toric11 | binary_css/x_only | 0.05 | 0.05 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 321.4 | 1.516 | previous_damping |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 30 | 0.5 | constant 1 | 0 | 0.15504 | [0.09735, 0.2221] | 13.58 | 0.7111 | joint_selected |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 60 | 0.5 | constant 1 | 0 | 0.11561 | [0.07206, 0.1671] | 17.76 | 0.8941 | joint_selected |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 121 | 0.5 | constant 1 | 0 | 0.10989 | [0.06843, 0.1591] | 24.87 | 1.201 | joint_selected |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 242 | 0.5 | constant 1 | 0 | 0.10989 | [0.06843, 0.1591] | 38.16 | 1.772 | joint_selected |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.20619 | [0.1307, 0.2917] | 14.08 | 0.7341 | previous_damping |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.11834 | [0.07381, 0.171] | 17.54 | 0.8835 | previous_damping |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.11834 | [0.07381, 0.171] | 24.76 | 1.196 | previous_damping |
| toric11 | bp4/depolarizing | 0.05 | 0.075 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.11765 | [0.07336, 0.17] | 39.88 | 1.848 | previous_damping |
| toric11 | binary_css/x_only | 0.06 | 0.06 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 176.1 | 0.7945 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.06 | 0.06 | 332 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 233.1 | 1.032 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.06 | 0.06 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 329.3 | 1.435 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 30 | 0.4 | constant 1 | 0 | 0.26316 | [0.1687, 0.367] | 15.59 | 0.7496 | joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 60 | 0.4 | constant 1 | 0 | 0.1227 | [0.07658, 0.1771] | 18.34 | 0.8622 | joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 67 | 0.4 | constant 1 | 0 | 0.11111 | [0.0692, 0.1608] | 18.69 | 0.8745 | joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 121 | 0.4 | constant 1 | 0 | 0.1105 | [0.06881, 0.1599] | 24.99 | 1.129 | joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 242 | 0.4 | constant 1 | 0 | 0.1105 | [0.06881, 0.1599] | 38.36 | 1.669 | joint_selected |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.22989 | [0.1464, 0.3233] | 15.53 | 0.746 | previous_damping |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.11111 | [0.0692, 0.1608] | 17.92 | 0.8411 | previous_damping |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 63 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.11111 | [0.0692, 0.1608] | 18.25 | 0.8537 | previous_damping |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.1105 | [0.06881, 0.1599] | 24.97 | 1.126 | previous_damping |
| toric11 | bp4/depolarizing | 0.06 | 0.09 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.1105 | [0.06881, 0.1599] | 38.34 | 1.667 | previous_damping |
| toric11 | binary_css/x_only | 0.07 | 0.07 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 164.8 | 0.7095 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.07 | 0.07 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 201.5 | 0.8421 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.07 | 0.07 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 313.1 | 1.257 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 30 | 0.3 | constant 1 | 0 | 0.4 | [0.2641, 0.5376] | 20.46 | 0.9108 | joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 45 | 0.3 | constant 1 | 0 | 0.30769 | [0.1991, 0.4242] | 26.72 | 1.159 | joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 60 | 0.3 | constant 1 | 0 | 0.29851 | [0.1928, 0.4125] | 31.39 | 1.336 | joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 121 | 0.3 | constant 1 | 0 | 0.29851 | [0.1928, 0.4125] | 49.6 | 2.033 | joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 242 | 0.3 | constant 1 | 0 | 0.29851 | [0.1928, 0.4125] | 85.72 | 3.394 | joint_selected |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.44444 | [0.2964, 0.5897] | 20.98 | 0.9338 | previous_damping |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 43 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.35714 | [0.2336, 0.4858] | 26.05 | 1.13 | previous_damping |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.32787 | [0.2131, 0.4496] | 32.82 | 1.393 | previous_damping |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.29851 | [0.1928, 0.4125] | 52.1 | 2.132 | previous_damping |
| toric11 | bp4/depolarizing | 0.07 | 0.105 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.29851 | [0.1928, 0.4125] | 88.22 | 3.503 | previous_damping |
| toric11 | binary_css/x_only | 0.08 | 0.08 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 187.6 | 0.7106 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.08 | 0.08 | 332 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 251.9 | 0.8972 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.08 | 0.08 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 363.2 | 1.362 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 30 | 0.3 | constant 1 | 0 | 0.55556 | [0.381, 0.7117] | 23.25 | 0.9945 | joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 33 | 0.3 | constant 1 | 0 | 0.55556 | [0.381, 0.7117] | 24.92 | 1.054 | joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 60 | 0.3 | constant 1 | 0 | 0.5 | [0.338, 0.6522] | 40.73 | 1.648 | joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 121 | 0.3 | constant 1 | 0 | 0.4 | [0.2641, 0.5376] | 66.62 | 2.624 | joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 242 | 0.3 | constant 1 | 0 | 0.37736 | [0.2479, 0.5104] | 113.3 | 4.376 | joint_selected |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 22.68 | 0.9725 | previous_damping |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 33 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 24.3 | 1.066 | previous_damping |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 39.85 | 1.621 | previous_damping |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4 | [0.2641, 0.5376] | 65.28 | 2.583 | previous_damping |
| toric11 | bp4/depolarizing | 0.08 | 0.12 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4 | [0.2641, 0.5376] | 113.7 | 4.398 | previous_damping |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 242 | 0.4 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 201.4 | 0.7516 | joint_selected |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 317 | 0.4 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 257 | 0.9207 | joint_selected |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 484 | 0.4 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 380.7 | 1.313 | joint_selected |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 216.6 | 0.7941 | previous_damping |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 332 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 294.8 | 1.032 | previous_damping |
| toric11 | binary_css/x_only | 0.09 | 0.09 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 427 | 1.453 | previous_damping |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 28 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 26.12 | 1.088 | joint_selected |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 30 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 27.79 | 1.15 | joint_selected |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 60 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 52.08 | 2.05 | joint_selected |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 121 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 100.9 | 3.844 | joint_selected |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 242 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 197.7 | 7.412 | joint_selected |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 26.13 | 1.092 | previous_damping |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 27.87 | 1.156 | previous_damping |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 52.36 | 2.065 | previous_damping |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 97.61 | 3.726 | previous_damping |
| toric11 | bp4/depolarizing | 0.09 | 0.135 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 184 | 6.906 | previous_damping |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 242 | 0.7 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 236.5 | 0.8523 | joint_selected |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 302 | 0.7 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 293.7 | 1.047 | joint_selected |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 484 | 0.7 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 467 | 1.629 | joint_selected |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 235.4 | 0.8612 | previous_damping |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 292.5 | 1.074 | previous_damping |
| toric11 | binary_css/x_only | 0.091 | 0.091 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 465.9 | 1.581 | previous_damping |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 28 | 0.3 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 22.03 | 0.921 | joint_selected |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 30 | 0.3 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 23.05 | 0.9742 | joint_selected |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 60 | 0.3 | constant 1 | 0 | 0.5 | [0.338, 0.6522] | 38.4 | 1.589 | joint_selected |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 121 | 0.3 | constant 1 | 0 | 0.5 | [0.338, 0.6522] | 68.9 | 2.7 | joint_selected |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 242 | 0.3 | constant 1 | 0 | 0.47619 | [0.32, 0.6258] | 127.5 | 4.856 | joint_selected |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.52632 | [0.3582, 0.6808] | 23.53 | 0.9859 | previous_damping |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 24.72 | 1.036 | previous_damping |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4878 | [0.3288, 0.6387] | 40.46 | 1.632 | previous_damping |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4878 | [0.3288, 0.6387] | 70.22 | 2.792 | previous_damping |
| toric11 | bp4/depolarizing | 0.091 | 0.1365 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.4878 | [0.3288, 0.6387] | 129.2 | 4.924 | previous_damping |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 242 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 229.6 | 0.8933 | joint_selected |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 302 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 284.1 | 1.069 | joint_selected |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 484 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 449.6 | 1.69 | joint_selected |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 242 | 0.9121 | previous_damping |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 302 | 1.144 | previous_damping |
| toric11 | binary_css/x_only | 0.092 | 0.092 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 484 | 1.656 | previous_damping |
| toric11 | bp4/depolarizing | 0.092 | 0.138 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 24.23 | 1.018 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.092 | 0.138 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 25.71 | 1.075 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.092 | 0.138 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 45.06 | 1.836 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.092 | 0.138 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 84.42 | 3.372 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.092 | 0.138 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.625 | [0.4369, 0.7815] | 163.8 | 6.418 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 242 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 221.6 | 0.8791 | joint_selected |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 302 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 276.1 | 1.061 | joint_selected |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 484 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 441.6 | 1.641 | joint_selected |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 221.8 | 0.8448 | previous_damping |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 317 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 290 | 1.055 | previous_damping |
| toric11 | binary_css/x_only | 0.093 | 0.093 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 441.8 | 1.581 | previous_damping |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 28 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 24.59 | 1.024 | joint_selected |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 30 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 26.18 | 1.086 | joint_selected |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 60 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 45.52 | 1.843 | joint_selected |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 121 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 84.87 | 3.363 | joint_selected |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 242 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 162.9 | 6.385 | joint_selected |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 25.11 | 1.066 | previous_damping |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 26.59 | 1.117 | previous_damping |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 46.55 | 1.889 | previous_damping |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 85.9 | 3.405 | previous_damping |
| toric11 | bp4/depolarizing | 0.093 | 0.1395 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 164 | 6.808 | previous_damping |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 242 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 212 | 0.8015 | joint_selected |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 302 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 264.2 | 0.9719 | joint_selected |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 484 | 0.4 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 422.4 | 1.475 | joint_selected |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 211.9 | 0.7978 | previous_damping |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 264 | 0.9612 | previous_damping |
| toric11 | binary_css/x_only | 0.094 | 0.094 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 422.3 | 1.467 | previous_damping |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 30 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 24.13 | 0.9594 | joint_selected |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 60 | 0.3 | constant 1 | 0 | 0.54054 | [0.3692, 0.6959] | 41.7 | 1.595 | joint_selected |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 121 | 0.3 | constant 1 | 0 | 0.54054 | [0.3692, 0.6959] | 74.68 | 2.778 | joint_selected |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 242 | 0.3 | constant 1 | 0 | 0.54054 | [0.3692, 0.6959] | 140.1 | 5.105 | joint_selected |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 24.16 | 0.9657 | previous_damping |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 42.63 | 1.629 | previous_damping |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 75.92 | 2.823 | previous_damping |
| toric11 | bp4/depolarizing | 0.094 | 0.141 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.54054 | [0.3692, 0.6959] | 141.3 | 5.138 | previous_damping |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 242 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 219.4 | 0.8604 | joint_selected |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 302 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 271.2 | 1.043 | joint_selected |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 484 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 428.4 | 1.54 | joint_selected |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 225 | 0.8544 | previous_damping |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 279.5 | 1.033 | previous_damping |
| toric11 | binary_css/x_only | 0.095 | 0.095 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 445 | 1.867 | previous_damping |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 30 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 28.52 | 1.107 | joint_selected |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 60 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 50.82 | 1.853 | joint_selected |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 121 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 94.39 | 3.451 | joint_selected |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 242 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 180.8 | 6.391 | joint_selected |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 26.57 | 1.04 | previous_damping |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 28.3 | 1.102 | previous_damping |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 50.11 | 1.904 | previous_damping |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 95.04 | 3.451 | previous_damping |
| toric11 | bp4/depolarizing | 0.095 | 0.1425 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 181.5 | 6.713 | previous_damping |
| toric11 | binary_css/x_only | 0.096 | 0.096 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 231 | 0.9084 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.096 | 0.096 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 288.1 | 1.095 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.096 | 0.096 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 461.4 | 1.659 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.096 | 0.144 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 23.26 | 1.177 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.096 | 0.144 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 24.55 | 0.9901 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.096 | 0.144 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 42 | 1.621 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.096 | 0.144 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.57143 | [0.3935, 0.7281] | 76.86 | 2.87 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.096 | 0.144 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.55556 | [0.381, 0.7117] | 146.9 | 5.376 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.097 | 0.097 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 230.9 | 0.9782 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.097 | 0.097 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 288 | 1.01 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.097 | 0.097 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 461.4 | 1.577 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.097 | 0.1455 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 22.88 | 0.8861 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.097 | 0.1455 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.58824 | [0.407, 0.7452] | 24.06 | 0.9329 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.097 | 0.1455 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.52632 | [0.3582, 0.6808] | 40.58 | 1.515 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.097 | 0.1455 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.52632 | [0.3582, 0.6808] | 72.68 | 2.618 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.097 | 0.1455 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.52632 | [0.3582, 0.6808] | 136.4 | 4.855 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.098 | 0.098 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 212.1 | 0.8225 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.098 | 0.098 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 249.6 | 0.938 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.098 | 0.098 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 413.8 | 1.465 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 28 | 0.2 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 26.21 | 1.005 | joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 30 | 0.2 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 27.88 | 1.065 | joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 60 | 0.2 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 53.08 | 1.957 | joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 121 | 0.2 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 102.1 | 3.582 | joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 242 | 0.2 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 188.6 | 6.441 | joint_selected |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 25.58 | 0.9979 | previous_damping |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 27.12 | 1.059 | previous_damping |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 49.52 | 1.831 | previous_damping |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 94.7 | 3.306 | previous_damping |
| toric11 | bp4/depolarizing | 0.098 | 0.147 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 184.3 | 6.317 | previous_damping |
| toric11 | binary_css/x_only | 0.099 | 0.099 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 233.1 | 0.8652 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.099 | 0.099 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 287.4 | 1.033 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.099 | 0.099 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 452.1 | 1.534 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 30 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 25.61 | 0.9368 | joint_selected |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 60 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 47.04 | 1.645 | joint_selected |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 121 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 90.61 | 3.037 | joint_selected |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 242 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 177 | 5.815 | joint_selected |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 24.22 | 0.8931 | previous_damping |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 25.7 | 0.945 | previous_damping |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 47.36 | 1.638 | previous_damping |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 90.93 | 3.033 | previous_damping |
| toric11 | bp4/depolarizing | 0.099 | 0.1485 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 177.4 | 5.806 | previous_damping |
| toric11 | binary_css/x_only | 0.1 | 0.1 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 235.8 | 0.8707 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.1 | 0.1 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 292.8 | 1.045 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.1 | 0.1 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 465.7 | 1.562 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 28 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 26.19 | 0.9453 | joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 30 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 27.73 | 1.024 | joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 60 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 49.65 | 1.758 | joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 121 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 91.88 | 3.152 | joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 242 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 175.7 | 5.778 | joint_selected |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 26.44 | 0.9553 | previous_damping |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 28.04 | 1.037 | previous_damping |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 49.92 | 1.733 | previous_damping |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 92.15 | 3.099 | previous_damping |
| toric11 | bp4/depolarizing | 0.1 | 0.15 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 175.9 | 5.723 | previous_damping |
| toric11 | binary_css/x_only | 0.101 | 0.101 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 242 | 0.8963 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.101 | 0.101 | 302 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 302 | 1.083 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.101 | 0.101 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 484 | 1.649 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.101 | 0.1515 | 28 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 24.61 | 0.8524 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.101 | 0.1515 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 26.07 | 0.947 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.101 | 0.1515 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 45.72 | 1.585 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.101 | 0.1515 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 85.69 | 2.816 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.101 | 0.1515 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 165 | 5.272 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 242 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 242 | 0.8975 | joint_selected |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 302 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 302 | 1.085 | joint_selected |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 484 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 484 | 1.656 | joint_selected |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 242 | 0.9038 | previous_damping |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 287 | 1.044 | previous_damping |
| toric11 | binary_css/x_only | 0.102 | 0.102 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 477.8 | 1.638 | previous_damping |
| toric11 | bp4/depolarizing | 0.102 | 0.153 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 25.64 | 1.081 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.102 | 0.153 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 29.27 | 1.232 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.102 | 0.153 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 54.43 | 2.159 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.102 | 0.153 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 100.5 | 3.897 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.102 | 0.153 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 192.5 | 7.133 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.103 | 0.103 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 242 | 0.9376 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.103 | 0.103 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 287 | 1.088 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.103 | 0.103 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 484 | 1.727 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 26 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 23.79 | 1.005 | joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 30 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 27.12 | 1.109 | joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 60 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 52.12 | 2.078 | joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 121 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 103 | 3.978 | joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 242 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 203.8 | 7.276 | joint_selected |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 24.25 | 1.02 | previous_damping |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 27.58 | 1.154 | previous_damping |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 52.58 | 2.08 | previous_damping |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 103.4 | 4.235 | previous_damping |
| toric11 | bp4/depolarizing | 0.103 | 0.1545 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 204.2 | 7.637 | previous_damping |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 242 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 242 | 0.8898 | joint_selected |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 287 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 287 | 1.028 | joint_selected |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 484 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 484 | 1.65 | joint_selected |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 240.9 | 0.8919 | previous_damping |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 283.8 | 1.024 | previous_damping |
| toric11 | binary_css/x_only | 0.105 | 0.105 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 471.4 | 1.608 | previous_damping |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 28 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 24.29 | 0.9433 | joint_selected |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 30 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 25.71 | 0.9926 | joint_selected |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 60 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 47.14 | 1.729 | joint_selected |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 121 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 91.21 | 3.283 | joint_selected |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 242 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 174.7 | 6.101 | joint_selected |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 22.75 | 0.9015 | previous_damping |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 25.61 | 0.9876 | previous_damping |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 47.04 | 1.724 | previous_damping |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 90.1 | 3.225 | previous_damping |
| toric11 | bp4/depolarizing | 0.105 | 0.1575 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 173.6 | 6.101 | previous_damping |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 242 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 211 | 0.8001 | joint_selected |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 287 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 248.2 | 0.9133 | joint_selected |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 484 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 411 | 1.396 | joint_selected |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 223.8 | 0.8449 | previous_damping |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 264.5 | 0.9696 | previous_damping |
| toric11 | binary_css/x_only | 0.106 | 0.106 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 442.7 | 1.507 | previous_damping |
| toric11 | bp4/depolarizing | 0.106 | 0.159 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 25.64 | 0.9912 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.106 | 0.159 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 29.22 | 1.135 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.106 | 0.159 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 54.71 | 2.006 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.106 | 0.159 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 105.5 | 3.761 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.106 | 0.159 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 206.4 | 7.222 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 242 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 235.6 | 0.8961 | joint_selected |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 287 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 278.4 | 1.028 | joint_selected |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 484 | 0.6 | constant 1 | 0 | 1 | [0.8316, 1] | 465.5 | 1.611 | joint_selected |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 234.6 | 0.888 | previous_damping |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 277.3 | 1.021 | previous_damping |
| toric11 | binary_css/x_only | 0.107 | 0.107 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 464.4 | 1.596 | previous_damping |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 26 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 24.08 | 0.942 | joint_selected |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 30 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 27.15 | 1.049 | joint_selected |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 60 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 48.7 | 1.812 | joint_selected |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 121 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 89.37 | 3.284 | joint_selected |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 242 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 170 | 6.077 | joint_selected |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 24.17 | 0.9495 | previous_damping |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 27.71 | 1.08 | previous_damping |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 49.72 | 1.865 | previous_damping |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 91 | 3.339 | previous_damping |
| toric11 | bp4/depolarizing | 0.107 | 0.1605 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 171.7 | 6.54 | previous_damping |
| toric11 | binary_css/x_only | 0.108 | 0.108 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 238.7 | 0.902 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.108 | 0.108 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 281.4 | 1.043 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.108 | 0.108 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 468.6 | 1.62 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 26 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 23.4 | 0.8872 | joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 30 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 26.73 | 1.01 | joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 60 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 49.81 | 1.803 | joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 121 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 96.73 | 3.348 | joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 242 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 189.8 | 6.477 | joint_selected |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 24 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 22.33 | 0.8595 | previous_damping |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 27.4 | 1.058 | previous_damping |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 50.73 | 1.809 | previous_damping |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 97.65 | 3.38 | previous_damping |
| toric11 | bp4/depolarizing | 0.108 | 0.162 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 190.7 | 6.509 | previous_damping |
| toric11 | binary_css/x_only | 0.109 | 0.109 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 221.1 | 0.8309 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.109 | 0.109 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 260.2 | 0.9519 | previous_damping,joint_selected |
| toric11 | binary_css/x_only | 0.109 | 0.109 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 431.5 | 1.479 | previous_damping,joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 24 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 23.26 | 0.9658 | joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 30 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 28.48 | 1.177 | joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 60 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 53.84 | 2.219 | joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 121 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 102.6 | 3.993 | joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 242 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 199.4 | 8.053 | joint_selected |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 24 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 23.3 | 1.04 | previous_damping |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 28.52 | 1.195 | previous_damping |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 54.61 | 2.197 | previous_damping |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 106.9 | 4.692 | previous_damping |
| toric11 | bp4/depolarizing | 0.109 | 0.1635 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 203.7 | 7.97 | previous_damping |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 242 | 0.6 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 213.5 | 0.8142 | joint_selected |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 287 | 0.6 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 251 | 0.931 | joint_selected |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 484 | 0.6 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 415.2 | 1.452 | joint_selected |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 242 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 217 | 0.8253 | previous_damping |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 287 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 256.1 | 0.9518 | previous_damping |
| toric11 | binary_css/x_only | 0.11 | 0.11 | 484 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 427.4 | 1.485 | previous_damping |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 26 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 24.39 | 1.262 | joint_selected |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 30 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 27.87 | 1.071 | joint_selected |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 60 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 53.96 | 1.987 | joint_selected |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 121 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 107 | 3.822 | joint_selected |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 242 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 212.2 | 7.433 | joint_selected |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 26 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 24.39 | 0.9488 | previous_damping |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 30 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 27.87 | 1.072 | previous_damping |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 60 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 53.96 | 2.005 | previous_damping |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 121 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 107 | 4.205 | previous_damping |
| toric11 | bp4/depolarizing | 0.11 | 0.165 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 212.2 | 7.467 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 338 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 25.67 | 0.8124 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 443 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 31.6 | 0.9673 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 676 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 44.77 | 1.19 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 24.32 | 0.7882 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 485 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 32.62 | 0.944 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 43.41 | 1.345 | previous_damping |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 42 | 0.6 | constant 1 | 0 | 0.017762 | [0.01088, 0.02625] | 3.093 | 0.8803 | joint_selected |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 84 | 0.6 | constant 1 | 0 | 0.013532 | [0.008285, 0.02002] | 3.822 | 0.9861 | joint_selected |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 115 | 0.6 | constant 1 | 0 | 0.010422 | [0.006377, 0.01543] | 4.411 | 1.144 | joint_selected |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 169 | 0.6 | constant 1 | 0 | 0.010422 | [0.006377, 0.01543] | 4.973 | 1.242 | joint_selected |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 338 | 0.6 | constant 1 | 0 | 0.010422 | [0.006377, 0.01543] | 6.735 | 1.619 | joint_selected |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 39 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.028249 | [0.01734, 0.04165] | 3.904 | 1.029 | previous_damping |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.027174 | [0.01668, 0.04008] | 4.053 | 1.085 | previous_damping |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.01444 | [0.008842, 0.02136] | 4.562 | 1.193 | previous_damping |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.010521 | [0.006438, 0.01557] | 5.827 | 1.437 | previous_damping |
| toric13 | bp4/depolarizing | 0.01 | 0.015 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.010521 | [0.006438, 0.01557] | 7.605 | 1.857 | previous_damping |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 65.1 | 0.5689 | joint_selected |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 507 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 92.36 | 0.8578 | joint_selected |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.16129 | [0.1014, 0.2307] | 119.6 | 0.9874 | joint_selected |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16667 | [0.1049, 0.2381] | 64.91 | 0.6122 | previous_damping |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 528 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16667 | [0.1049, 0.2381] | 96.58 | 0.8088 | previous_damping |
| toric13 | binary_css/x_only | 0.02 | 0.02 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16667 | [0.1049, 0.2381] | 121.2 | 1.002 | previous_damping |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 338 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.0047472 | [0.002902, 0.007035] | 10.04 | 0.8734 | joint_selected |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 676 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.0047472 | [0.002902, 0.007035] | 11.65 | 1.014 | joint_selected |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 1352 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.0047472 | [0.002902, 0.007035] | 14.86 | 1.241 | joint_selected |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012151 | [0.007437, 0.01798] | 12.12 | 1.013 | previous_damping |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 549 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012151 | [0.007437, 0.01798] | 14.69 | 1.194 | previous_damping |
| toric13 | bp4/depolarizing | 0.02 | 0.03 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.012151 | [0.007437, 0.01798] | 16.23 | 1.349 | previous_damping |
| toric13 | binary_css/x_only | 0.03 | 0.03 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 189.1 | 0.9194 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.03 | 0.03 | 507 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 275.8 | 1.294 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.03 | 0.03 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 362.5 | 1.717 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.03 | 0.045 | 338 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.013351 | [0.008174, 0.01975] | 16.17 | 0.9014 | joint_selected |
| toric13 | bp4/depolarizing | 0.03 | 0.045 | 676 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.013115 | [0.008029, 0.0194] | 20.87 | 1.138 | joint_selected |
| toric13 | bp4/depolarizing | 0.03 | 0.045 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.014035 | [0.008594, 0.02076] | 14.28 | 0.7803 | previous_damping |
| toric13 | bp4/depolarizing | 0.03 | 0.045 | 633 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.014035 | [0.008594, 0.02076] | 18.42 | 0.9971 | previous_damping |
| toric13 | bp4/depolarizing | 0.03 | 0.045 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.014035 | [0.008594, 0.02076] | 19.03 | 1.037 | previous_damping |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 338 | 0.3 | constant 1 | 0 | 0.46512 | [0.3118, 0.6133] | 168.5 | 0.6091 | joint_selected |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 507 | 0.3 | constant 1 | 0 | 0.46512 | [0.3118, 0.6133] | 247.1 | 0.869 | joint_selected |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 676 | 0.3 | constant 1 | 0 | 0.46512 | [0.3118, 0.6133] | 325.7 | 1.122 | joint_selected |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 168.1 | 0.6055 | previous_damping |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 528 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 256.4 | 0.8976 | previous_damping |
| toric13 | binary_css/x_only | 0.04 | 0.04 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 325.3 | 1.122 | previous_damping |
| toric13 | bp4/depolarizing | 0.04 | 0.06 | 338 | 0.7 | constant 1 | 0 | 0.046296 | [0.0285, 0.06799] | 29.2 | 1.089 | joint_selected |
| toric13 | bp4/depolarizing | 0.04 | 0.06 | 676 | 0.7 | constant 1 | 0 | 0.046296 | [0.0285, 0.06799] | 44.85 | 1.683 | joint_selected |
| toric13 | bp4/depolarizing | 0.04 | 0.06 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.046296 | [0.0285, 0.06799] | 26.97 | 0.9861 | previous_damping |
| toric13 | bp4/depolarizing | 0.04 | 0.06 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.044843 | [0.0276, 0.06587] | 43.11 | 1.536 | previous_damping |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 246.8 | 0.825 | joint_selected |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 464 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 328.1 | 1.07 | joint_selected |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 464.8 | 1.465 | joint_selected |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 268.5 | 0.8569 | previous_damping |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 485 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 377.4 | 1.195 | previous_damping |
| toric13 | binary_css/x_only | 0.05 | 0.05 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 518.9 | 1.575 | previous_damping |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 42 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.14925 | [0.09362, 0.2141] | 18.49 | 0.5245 | joint_selected |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 84 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.089686 | [0.05565, 0.1304] | 22.04 | 0.6013 | joint_selected |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 169 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.089686 | [0.05565, 0.1304] | 29.66 | 0.7941 | joint_selected |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.088889 | [0.05514, 0.1293] | 45.46 | 1.167 | joint_selected |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.12987 | [0.08117, 0.1871] | 17.16 | 0.4968 | previous_damping |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.085837 | [0.05322, 0.1249] | 21.27 | 0.5942 | previous_damping |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.085837 | [0.05322, 0.1249] | 28.56 | 0.7562 | previous_damping |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 232 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.085837 | [0.05322, 0.1249] | 33.97 | 0.886 | previous_damping |
| toric13 | bp4/depolarizing | 0.05 | 0.075 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.085837 | [0.05322, 0.1249] | 43.07 | 1.107 | previous_damping |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 338 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 322 | 0.9755 | joint_selected |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 464 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 442 | 1.082 | joint_selected |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 676 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 644 | 1.57 | joint_selected |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 312.2 | 0.7949 | previous_damping |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 485 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 445.9 | 1.105 | previous_damping |
| toric13 | binary_css/x_only | 0.06 | 0.06 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 619.5 | 1.513 | previous_damping |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 42 | 0.4 | constant 1 | 0 | 0.24691 | [0.1578, 0.3458] | 21.05 | 0.7492 | joint_selected |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 84 | 0.4 | constant 1 | 0 | 0.22727 | [0.1447, 0.3198] | 30.75 | 0.9841 | joint_selected |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 136 | 0.4 | constant 1 | 0 | 0.22727 | [0.1447, 0.3198] | 42.57 | 1.332 | joint_selected |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 169 | 0.4 | constant 1 | 0 | 0.22727 | [0.1447, 0.3198] | 50.07 | 1.545 | joint_selected |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 338 | 0.4 | constant 1 | 0 | 0.22727 | [0.1447, 0.3198] | 88.48 | 2.66 | joint_selected |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.24691 | [0.1578, 0.3458] | 21.59 | 0.7227 | previous_damping |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.21053 | [0.1336, 0.2975] | 30.46 | 0.9839 | previous_damping |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 89 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.21053 | [0.1336, 0.2975] | 31.52 | 1.016 | previous_damping |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.21053 | [0.1336, 0.2975] | 48.36 | 1.566 | previous_damping |
| toric13 | bp4/depolarizing | 0.06 | 0.09 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.21053 | [0.1336, 0.2975] | 83.94 | 2.586 | previous_damping |
| toric13 | binary_css/x_only | 0.07 | 0.07 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 253.4 | 0.7578 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.07 | 0.07 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 494.9 | 1.531 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 42 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.47619 | [0.32, 0.6258] | 29.07 | 0.9343 | joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 63 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.47619 | [0.32, 0.6258] | 39.07 | 1.221 | joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 84 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 48.64 | 1.518 | joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 169 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.41667 | [0.2761, 0.5573] | 84.67 | 2.575 | joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.41667 | [0.2761, 0.5573] | 155.1 | 4.532 | joint_selected |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 28.97 | 0.9223 | previous_damping |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 65 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.47619 | [0.32, 0.6258] | 40.67 | 1.25 | previous_damping |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 49.36 | 1.491 | previous_damping |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 88 | 2.567 | previous_damping |
| toric13 | bp4/depolarizing | 0.07 | 0.105 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 164.8 | 4.959 | previous_damping |
| toric13 | binary_css/x_only | 0.08 | 0.08 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 313.4 | 0.8658 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.08 | 0.08 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 370.6 | 1.006 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.08 | 0.08 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 620.6 | 1.627 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 42 | 0.3 | constant 1 | 0 | 0.52632 | [0.3582, 0.6808] | 29.58 | 0.8731 | joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 44 | 0.3 | constant 1 | 0 | 0.51282 | [0.3478, 0.6662] | 30.95 | 0.9396 | joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 84 | 0.3 | constant 1 | 0 | 0.45455 | [0.3039, 0.6012] | 49.61 | 1.536 | joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 169 | 0.3 | constant 1 | 0 | 0.45455 | [0.3039, 0.6012] | 88.25 | 2.546 | joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 338 | 0.3 | constant 1 | 0 | 0.45455 | [0.3039, 0.6012] | 165.1 | 4.529 | joint_selected |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.51282 | [0.3478, 0.6662] | 29.21 | 0.8789 | previous_damping |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 44 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 30.55 | 0.9067 | previous_damping |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 48.66 | 1.377 | previous_damping |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 87.3 | 2.414 | previous_damping |
| toric13 | bp4/depolarizing | 0.08 | 0.12 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 164.1 | 4.512 | previous_damping |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 338 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 322.3 | 0.9267 | joint_selected |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 380 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 362.3 | 1.326 | joint_selected |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 676 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 644.2 | 1.808 | joint_selected |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 322.4 | 1.202 | previous_damping |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 359 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 342.4 | 0.9706 | previous_damping |
| toric13 | binary_css/x_only | 0.09 | 0.09 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 634.4 | 1.75 | previous_damping |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 42 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 37.33 | 1.101 | joint_selected |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 84 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 68.44 | 1.901 | joint_selected |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 169 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 131.4 | 3.506 | joint_selected |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 255.4 | 7.097 | joint_selected |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 39 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 35.15 | 1.003 | previous_damping |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 37.37 | 1.115 | previous_damping |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 68.48 | 1.898 | previous_damping |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 132.6 | 3.527 | previous_damping |
| toric13 | bp4/depolarizing | 0.09 | 0.135 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 253.4 | 6.737 | previous_damping |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 338 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 338 | 1.092 | joint_selected |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 401 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 401 | 1.051 | joint_selected |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 676 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 676 | 1.697 | joint_selected |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.9058 | previous_damping |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.281 | previous_damping |
| toric13 | binary_css/x_only | 0.091 | 0.091 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.917 | previous_damping |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 39 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 32.76 | 0.9762 | joint_selected |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 42 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 34.83 | 1.06 | joint_selected |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 84 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 63.03 | 1.803 | joint_selected |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 169 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 117.9 | 3.29 | joint_selected |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 338 | 0.3 | constant 1 | 0 | 0.60606 | [0.4214, 0.763] | 220.4 | 6.016 | joint_selected |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 39 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 32.68 | 0.9564 | previous_damping |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 34.61 | 1.015 | previous_damping |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 61.71 | 1.732 | previous_damping |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.64516 | [0.4537, 0.8007] | 116.5 | 3.201 | previous_damping |
| toric13 | bp4/depolarizing | 0.091 | 0.1365 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.60606 | [0.4214, 0.763] | 219.9 | 5.98 | previous_damping |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 326.8 | 0.9617 | joint_selected |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 359 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 346.8 | 1.132 | joint_selected |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 676 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 648.7 | 1.956 | joint_selected |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 326.8 | 0.9476 | previous_damping |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 386.8 | 1.094 | previous_damping |
| toric13 | binary_css/x_only | 0.092 | 0.092 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 648.7 | 1.771 | previous_damping |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 39 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 35.15 | 1.006 | joint_selected |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 42 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 37.46 | 1.092 | joint_selected |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 84 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 68.54 | 1.907 | joint_selected |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 169 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 129.2 | 3.528 | joint_selected |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 338 | 0.3 | constant 1 | 0 | 0.71429 | [0.5133, 0.8625] | 250 | 6.747 | joint_selected |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 39 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 35.56 | 1.028 | previous_damping |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 37.96 | 1.089 | previous_damping |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 68.43 | 1.915 | previous_damping |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 129.1 | 3.518 | previous_damping |
| toric13 | bp4/depolarizing | 0.092 | 0.138 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 249.9 | 6.736 | previous_damping |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 338 | 0.5 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 296.4 | 0.731 | joint_selected |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 422 | 0.5 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 369.4 | 0.8727 | joint_selected |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 676 | 0.5 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 590.3 | 1.374 | joint_selected |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 299.9 | 0.7484 | previous_damping |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 464 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 409.5 | 0.9998 | previous_damping |
| toric13 | binary_css/x_only | 0.093 | 0.093 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 593.8 | 1.421 | previous_damping |
| toric13 | bp4/depolarizing | 0.093 | 0.1395 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 33.15 | 1.009 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.093 | 0.1395 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 37.77 | 1.143 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.093 | 0.1395 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 70.08 | 2.063 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.093 | 0.1395 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 135.5 | 3.931 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.093 | 0.1395 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 267.2 | 7.887 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.094 | 0.094 | 338 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 330.9 | 0.8468 | joint_selected |
| toric13 | binary_css/x_only | 0.094 | 0.094 | 676 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 652.8 | 1.595 | joint_selected |
| toric13 | binary_css/x_only | 0.094 | 0.094 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 325.4 | 0.8337 | previous_damping |
| toric13 | binary_css/x_only | 0.094 | 0.094 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 385.4 | 0.962 | previous_damping |
| toric13 | binary_css/x_only | 0.094 | 0.094 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 647.3 | 1.558 | previous_damping |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 39 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 34.72 | 1.019 | joint_selected |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 42 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 37.12 | 1.11 | joint_selected |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 84 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 67.93 | 1.957 | joint_selected |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 169 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 126.6 | 3.491 | joint_selected |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 338 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 243.1 | 6.73 | joint_selected |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 39 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 34.4 | 1.011 | previous_damping |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 36.8 | 1.081 | previous_damping |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 69.58 | 1.981 | previous_damping |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 133.1 | 3.656 | previous_damping |
| toric13 | bp4/depolarizing | 0.094 | 0.141 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 258.3 | 6.978 | previous_damping |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 322.1 | 0.8008 | joint_selected |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 422 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 402.1 | 0.9617 | joint_selected |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 676 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 644 | 1.486 | joint_selected |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 322.1 | 0.7775 | previous_damping |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 422 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 402.1 | 0.9434 | previous_damping |
| toric13 | binary_css/x_only | 0.095 | 0.095 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 644 | 1.467 | previous_damping |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 36 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 32.12 | 1.154 | joint_selected |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 42 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 37.16 | 1.4 | joint_selected |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 84 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 70.81 | 2.342 | joint_selected |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 169 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 135.8 | 4.007 | joint_selected |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 338 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 261 | 7.373 | joint_selected |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 32.35 | 0.9978 | previous_damping |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 36.96 | 1.131 | previous_damping |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.74074 | [0.5372, 0.8843] | 68.78 | 2.048 | previous_damping |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 130.3 | 3.798 | previous_damping |
| toric13 | bp4/depolarizing | 0.095 | 0.1425 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.71429 | [0.5133, 0.8625] | 251 | 7.09 | previous_damping |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 326.6 | 0.8624 | joint_selected |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 422 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 406.6 | 1.027 | joint_selected |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 676 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 648.5 | 1.585 | joint_selected |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 326.8 | 0.8445 | previous_damping |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 386.8 | 0.9755 | previous_damping |
| toric13 | binary_css/x_only | 0.096 | 0.096 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 648.7 | 1.563 | previous_damping |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 36 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 33.3 | 1.022 | joint_selected |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 42 | 0.3 | constant 1 | 0 | 0.74074 | [0.5372, 0.8843] | 37.74 | 1.155 | joint_selected |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 84 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 67.83 | 2.026 | joint_selected |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 169 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 126.4 | 3.704 | joint_selected |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 338 | 0.3 | constant 1 | 0 | 0.68966 | [0.4917, 0.8412] | 243 | 6.958 | joint_selected |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 32.96 | 1.021 | previous_damping |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 37.77 | 1.158 | previous_damping |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 68.1 | 2.023 | previous_damping |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 126.7 | 3.61 | previous_damping |
| toric13 | bp4/depolarizing | 0.096 | 0.144 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.68966 | [0.4917, 0.8412] | 243.3 | 6.779 | previous_damping |
| toric13 | binary_css/x_only | 0.098 | 0.098 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 1.126 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.098 | 0.098 | 380 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 380 | 0.9866 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.098 | 0.098 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.947 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 39 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 35.08 | 0.9873 | joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 42 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 37.48 | 1.047 | joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 84 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 70 | 1.922 | joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 169 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 135.4 | 3.607 | joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 338 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 265.4 | 6.997 | joint_selected |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 32.96 | 0.9285 | previous_damping |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 37.76 | 1.052 | previous_damping |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 70.38 | 1.898 | previous_damping |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 135.8 | 3.594 | previous_damping |
| toric13 | bp4/depolarizing | 0.098 | 0.147 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 265.8 | 6.937 | previous_damping |
| toric13 | binary_css/x_only | 0.099 | 0.099 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 1.167 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.099 | 0.099 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.032 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.099 | 0.099 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.661 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 36 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 33.29 | 0.9431 | joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 42 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 38.29 | 1.079 | joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 84 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 73.29 | 2.006 | joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 169 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 144.1 | 3.83 | joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 338 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 285 | 7.545 | joint_selected |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 33.25 | 0.9508 | previous_damping |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 38.25 | 1.115 | previous_damping |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 73.25 | 2.034 | previous_damping |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 144.1 | 3.986 | previous_damping |
| toric13 | bp4/depolarizing | 0.099 | 0.1485 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 284.9 | 7.532 | previous_damping |
| toric13 | binary_css/x_only | 0.1 | 0.1 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 325.7 | 0.8125 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.1 | 0.1 | 422 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 402.1 | 0.9837 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.1 | 0.1 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 633 | 1.501 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 36 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 34.59 | 1.007 | joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 42 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 40.05 | 1.156 | joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 84 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 78.23 | 2.176 | joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 169 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 155.5 | 4.227 | joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 338 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 309.1 | 8.33 | joint_selected |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 34.59 | 1.039 | previous_damping |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 40.05 | 1.185 | previous_damping |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 78.23 | 2.234 | previous_damping |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 155.5 | 4.494 | previous_damping |
| toric13 | bp4/depolarizing | 0.1 | 0.15 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 309.1 | 8.366 | previous_damping |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8312 | joint_selected |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 401 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.01 | joint_selected |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 676 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.611 | joint_selected |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.774 | previous_damping |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 0.9284 | previous_damping |
| toric13 | binary_css/x_only | 0.101 | 0.101 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.524 | previous_damping |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 36 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 33.13 | 0.9405 | joint_selected |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 42 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 38.35 | 1.078 | joint_selected |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 84 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 74.88 | 2.029 | joint_selected |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 169 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 143.8 | 3.865 | joint_selected |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 338 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 279 | 7.294 | joint_selected |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 33.22 | 0.9403 | previous_damping |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 38.43 | 1.087 | previous_damping |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 75 | 2.031 | previous_damping |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 143.7 | 3.879 | previous_damping |
| toric13 | bp4/depolarizing | 0.101 | 0.1515 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 278.9 | 7.449 | previous_damping |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 338 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 338 | 0.9529 | joint_selected |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 401 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 401 | 1.1 | joint_selected |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 676 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 676 | 1.796 | joint_selected |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 1.165 | previous_damping |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 422 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 422 | 1.183 | previous_damping |
| toric13 | binary_css/x_only | 0.102 | 0.102 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.828 | previous_damping |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 33 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 32.18 | 0.9957 | joint_selected |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 42 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 40.36 | 1.246 | joint_selected |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 84 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 78.55 | 2.363 | joint_selected |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 169 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 155.8 | 4.624 | joint_selected |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 338 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 309.5 | 9.405 | joint_selected |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 33 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 32.1 | 0.9909 | previous_damping |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 40.59 | 1.249 | previous_damping |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 78.77 | 2.366 | previous_damping |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 156 | 4.627 | previous_damping |
| toric13 | bp4/depolarizing | 0.102 | 0.153 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 309.7 | 9.123 | previous_damping |
| toric13 | binary_css/x_only | 0.103 | 0.103 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 327.2 | 0.8339 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.103 | 0.103 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 387.2 | 0.9888 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.103 | 0.103 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 649.1 | 1.569 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 39 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 36.82 | 0.908 | joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 42 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 39.55 | 0.9977 | joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 84 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 76.52 | 1.866 | joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 169 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 150.4 | 3.57 | joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 338 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 297.4 | 6.988 | joint_selected |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 34.23 | 0.8894 | previous_damping |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 39.68 | 1.035 | previous_damping |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 77.57 | 1.909 | previous_damping |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 151.5 | 3.641 | previous_damping |
| toric13 | bp4/depolarizing | 0.103 | 0.1545 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 298.4 | 6.916 | previous_damping |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 338 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 338 | 0.8636 | joint_selected |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 401 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 401 | 0.9969 | joint_selected |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 676 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 676 | 1.646 | joint_selected |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8532 | previous_damping |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 0.9792 | previous_damping |
| toric13 | binary_css/x_only | 0.104 | 0.104 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.609 | previous_damping |
| toric13 | bp4/depolarizing | 0.104 | 0.156 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 33.74 | 0.8968 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.104 | 0.156 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 38.96 | 1.048 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.104 | 0.156 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 75.48 | 1.948 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.104 | 0.156 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 146.7 | 3.729 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.104 | 0.156 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 287.5 | 7.069 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.105 | 0.105 | 338 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 338 | 0.8943 | joint_selected |
| toric13 | binary_css/x_only | 0.105 | 0.105 | 676 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 676 | 1.684 | joint_selected |
| toric13 | binary_css/x_only | 0.105 | 0.105 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8993 | previous_damping |
| toric13 | binary_css/x_only | 0.105 | 0.105 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.045 | previous_damping |
| toric13 | binary_css/x_only | 0.105 | 0.105 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.678 | previous_damping |
| toric13 | bp4/depolarizing | 0.105 | 0.1575 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 40.76 | 0.9518 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.105 | 0.1575 | 44 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 42.67 | 0.9998 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.105 | 0.1575 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 80.76 | 1.879 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.105 | 0.1575 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 161.7 | 3.88 | previous_damping,joint_selected |
| toric13 | bp4/depolarizing | 0.105 | 0.1575 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 322.7 | 7.233 | previous_damping,joint_selected |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 338 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8512 | joint_selected |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 401 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.011 | joint_selected |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 676 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.704 | joint_selected |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8424 | previous_damping |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 422 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 422 | 1.049 | previous_damping |
| toric13 | binary_css/x_only | 0.106 | 0.106 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.583 | previous_damping |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 42 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 38.13 | 0.9413 | joint_selected |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 84 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 72.83 | 1.761 | joint_selected |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 169 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 143 | 3.408 | joint_selected |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 338 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 282.7 | 6.694 | joint_selected |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 33 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 31.09 | 0.7747 | previous_damping |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 39.27 | 0.9677 | previous_damping |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 76 | 1.825 | previous_damping |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 149.9 | 3.549 | previous_damping |
| toric13 | bp4/depolarizing | 0.106 | 0.159 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 296.9 | 6.986 | previous_damping |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 338 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8637 | joint_selected |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 401 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 1.007 | joint_selected |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 676 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.64 | joint_selected |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8463 | previous_damping |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 422 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 422 | 1.086 | previous_damping |
| toric13 | binary_css/x_only | 0.107 | 0.107 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.581 | previous_damping |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 36 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 35.52 | 0.9325 | joint_selected |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 42 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 41.24 | 1.076 | joint_selected |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 84 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 81.24 | 2.06 | joint_selected |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 169 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 162.2 | 4.027 | joint_selected |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 338 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 323.1 | 7.988 | joint_selected |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 33 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 32.52 | 0.8606 | previous_damping |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 41.1 | 1.075 | previous_damping |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 81.1 | 2.056 | previous_damping |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 162 | 4.04 | previous_damping |
| toric13 | bp4/depolarizing | 0.107 | 0.1605 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 323 | 7.97 | previous_damping |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 338 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 1.006 | joint_selected |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 401 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 0.9906 | joint_selected |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 676 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.608 | joint_selected |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.84 | previous_damping |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 443 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 443 | 1.174 | previous_damping |
| toric13 | binary_css/x_only | 0.108 | 0.108 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.556 | previous_damping |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 39 | 0.4 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 35.46 | 0.878 | joint_selected |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 42 | 0.4 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 37.96 | 0.9387 | joint_selected |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 84 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 71.38 | 1.766 | joint_selected |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 169 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 136.8 | 3.449 | joint_selected |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 338 | 0.4 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 266.8 | 6.3 | joint_selected |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 32.76 | 0.8252 | previous_damping |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 37.56 | 0.9446 | previous_damping |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 71.16 | 1.721 | previous_damping |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 139.2 | 3.321 | previous_damping |
| toric13 | bp4/depolarizing | 0.108 | 0.162 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 271 | 6.382 | previous_damping |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 338 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 303.1 | 0.7756 | joint_selected |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 380 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 339.7 | 0.8653 | joint_selected |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 676 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 597 | 1.435 | joint_selected |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 303.6 | 0.7773 | previous_damping |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 358.3 | 0.911 | previous_damping |
| toric13 | binary_css/x_only | 0.109 | 0.109 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 597.5 | 1.453 | previous_damping |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 39 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 36.73 | 0.9193 | joint_selected |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 42 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 39.27 | 1.002 | joint_selected |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 84 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 73.64 | 1.895 | joint_selected |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 169 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 143.2 | 3.44 | joint_selected |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 338 | 0.4 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 281.5 | 6.594 | joint_selected |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 36 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 34.05 | 0.8718 | previous_damping |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 39 | 1.011 | previous_damping |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 73.36 | 1.887 | previous_damping |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 142.9 | 3.585 | previous_damping |
| toric13 | bp4/depolarizing | 0.109 | 0.1635 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 281.2 | 6.746 | previous_damping |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 338 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.817 | joint_selected |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 380 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 380 | 1.176 | joint_selected |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 676 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.551 | joint_selected |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 338 | 0.8243 | previous_damping |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 401 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 401 | 0.9475 | previous_damping |
| toric13 | binary_css/x_only | 0.11 | 0.11 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 676 | 1.54 | previous_damping |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 33 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 30.61 | 0.8189 | joint_selected |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 42 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 38.43 | 1.028 | joint_selected |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 84 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 74.96 | 1.958 | joint_selected |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 169 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 148.9 | 3.774 | joint_selected |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 338 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 295.8 | 7.207 | joint_selected |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 33 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 30.52 | 0.9402 | previous_damping |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 38.35 | 1.018 | previous_damping |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 84 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 74.87 | 1.974 | previous_damping |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 169 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 148.8 | 3.682 | previous_damping |
| toric13 | bp4/depolarizing | 0.11 | 0.165 | 338 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 295.7 | 7.191 | previous_damping |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 51.96 | 0.9989 | joint_selected |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 675 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 75.4 | 1.395 | joint_selected |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 900 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 98.84 | 1.784 | joint_selected |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 52.07 | 0.9739 | previous_damping |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 703 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 78.42 | 1.427 | previous_damping |
| toric15 | binary_css/x_only | 0.01 | 0.01 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.10417 | [0.0648, 0.151] | 98.94 | 1.903 | previous_damping |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 56 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.020534 | [0.01259, 0.03033] | 4.616 | 0.8094 | joint_selected |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 112 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.010718 | [0.006559, 0.01586] | 5.599 | 0.9751 | joint_selected |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 225 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.0091491 | [0.005597, 0.01355] | 6.604 | 1.107 | joint_selected |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 450 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.0091491 | [0.005597, 0.01355] | 8.663 | 1.49 | joint_selected |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.026144 | [0.01604, 0.03856] | 4.706 | 0.8568 | previous_damping |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.015974 | [0.009784, 0.02362] | 5.723 | 1.023 | previous_damping |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 140 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.010846 | [0.006637, 0.01605] | 6.286 | 1.098 | previous_damping |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.010846 | [0.006637, 0.01605] | 7.208 | 1.29 | previous_damping |
| toric15 | bp4/depolarizing | 0.01 | 0.015 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.010846 | [0.006637, 0.01605] | 9.649 | 1.62 | previous_damping |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 450 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 165.4 | 0.9375 | joint_selected |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 675 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 237.9 | 1.317 | joint_selected |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 900 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 310.5 | 1.692 | joint_selected |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 158 | 0.8706 | previous_damping |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 703 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 239.6 | 1.281 | previous_damping |
| toric15 | binary_css/x_only | 0.02 | 0.02 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.32258 | [0.2094, 0.4429] | 303.2 | 1.612 | previous_damping |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 450 | 0.85 | 1×(1−2⁻ᵗ) | 0 | 0.004561 | [0.002788, 0.00676] | 17.03 | 0.8803 | joint_selected |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 900 | 0.85 | 1×(1−2⁻ᵗ) | 0 | 0.0044326 | [0.00271, 0.00657] | 19.1 | 0.9746 | joint_selected |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 1800 | 0.85 | 1×(1−2⁻ᵗ) | 0 | 0.0044326 | [0.00271, 0.00657] | 23.09 | 1.163 | joint_selected |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 3600 | 0.85 | 1×(1−2⁻ᵗ) | 0 | 0.0044326 | [0.00271, 0.00657] | 31.07 | 1.533 | joint_selected |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.013928 | [0.008528, 0.0206] | 14.64 | 0.7123 | previous_damping |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 900 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.013928 | [0.008528, 0.0206] | 20.91 | 1.057 | previous_damping |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 1350 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.013928 | [0.008528, 0.0206] | 27.18 | 1.303 | previous_damping |
| toric15 | bp4/depolarizing | 0.02 | 0.03 | 1800 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.013928 | [0.008528, 0.0206] | 33.44 | 1.626 | previous_damping |
| toric15 | binary_css/x_only | 0.03 | 0.03 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 235.1 | 0.7679 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.03 | 0.03 | 646 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 333.1 | 1.078 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.03 | 0.03 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.5 | [0.338, 0.6522] | 460.1 | 1.47 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 450 | 0.7 | constant 1 | 0 | 0.014738 | [0.009025, 0.0218] | 19.31 | 0.6004 | joint_selected |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 900 | 0.7 | constant 1 | 0 | 0.014738 | [0.009025, 0.0218] | 25.95 | 0.7941 | joint_selected |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 1293 | 0.7 | constant 1 | 0 | 0.014738 | [0.009025, 0.0218] | 31.74 | 0.9495 | joint_selected |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 1800 | 0.7 | constant 1 | 0 | 0.014738 | [0.009025, 0.0218] | 39.21 | 1.172 | joint_selected |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.016026 | [0.009816, 0.02369] | 18.69 | 0.5783 | previous_damping |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 900 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.016026 | [0.009816, 0.02369] | 25.9 | 0.7872 | previous_damping |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 1181 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.016026 | [0.009816, 0.02369] | 30.41 | 0.9121 | previous_damping |
| toric15 | bp4/depolarizing | 0.03 | 0.045 | 1800 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.016026 | [0.009816, 0.02369] | 40.33 | 1.201 | previous_damping |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 450 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 286.6 | 0.819 | joint_selected |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 590 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 368.9 | 0.9512 | joint_selected |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 900 | 0.3 | constant 1 | 0 | 0.58824 | [0.407, 0.7452] | 551.3 | 1.383 | joint_selected |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 312.5 | 0.7921 | previous_damping |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 618 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 424.5 | 1.057 | previous_damping |
| toric15 | binary_css/x_only | 0.04 | 0.04 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 612.5 | 1.573 | previous_damping |
| toric15 | bp4/depolarizing | 0.04 | 0.06 | 450 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.046948 | [0.02891, 0.06894] | 40.48 | 0.9753 | joint_selected |
| toric15 | bp4/depolarizing | 0.04 | 0.06 | 900 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 0.046948 | [0.02891, 0.06894] | 61.61 | 1.49 | joint_selected |
| toric15 | bp4/depolarizing | 0.04 | 0.06 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.047847 | [0.02947, 0.07024] | 37.67 | 0.9373 | previous_damping |
| toric15 | bp4/depolarizing | 0.04 | 0.06 | 900 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.047847 | [0.02947, 0.07024] | 59.2 | 1.427 | previous_damping |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 450 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 404.7 | 0.8846 | joint_selected |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 590 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 526.5 | 1.148 | joint_selected |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 900 | 0.6 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 796 | 1.714 | joint_selected |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 399 | 0.8901 | previous_damping |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 496.4 | 1.103 | previous_damping |
| toric15 | binary_css/x_only | 0.05 | 0.05 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 790.3 | 1.72 | previous_damping |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 56 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.16949 | [0.1067, 0.2419] | 25.25 | 0.5888 | joint_selected |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 112 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.12903 | [0.08063, 0.1859] | 32.71 | 0.7233 | joint_selected |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 210 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.10929 | [0.06805, 0.1582] | 42.7 | 0.9323 | joint_selected |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 225 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.10929 | [0.06805, 0.1582] | 44.34 | 0.9943 | joint_selected |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 450 | 0.6 | 1×(1−2⁻ᵗ) | 0 | 0.1087 | [0.06767, 0.1574] | 70.03 | 1.515 | joint_selected |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.13699 | [0.08573, 0.197] | 22.01 | 0.513 | previous_damping |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.1227 | [0.07658, 0.1771] | 29.93 | 0.6709 | previous_damping |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.10929 | [0.06805, 0.1582] | 41.97 | 0.9147 | previous_damping |
| toric15 | bp4/depolarizing | 0.05 | 0.075 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.10929 | [0.06805, 0.1582] | 66.56 | 1.44 | previous_damping |
| toric15 | binary_css/x_only | 0.06 | 0.06 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 364.3 | 0.7579 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.06 | 0.06 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 450.4 | 0.8777 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.06 | 0.06 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 710.4 | 1.354 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 56 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.24096 | [0.1538, 0.338] | 25.9 | 0.581 | joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 112 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.22727 | [0.1447, 0.3198] | 38.82 | 0.8738 | joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 119 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.22727 | [0.1447, 0.3198] | 40.41 | 0.8864 | joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 225 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.22727 | [0.1447, 0.3198] | 64.5 | 1.406 | joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.22727 | [0.1447, 0.3198] | 115.6 | 2.578 | joint_selected |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.2381 | [0.1519, 0.3342] | 27.27 | 0.6077 | previous_damping |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.22472 | [0.143, 0.3165] | 40.61 | 0.9023 | previous_damping |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 119 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.22472 | [0.143, 0.3165] | 42.18 | 0.9269 | previous_damping |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.22222 | [0.1413, 0.3131] | 66.67 | 1.444 | previous_damping |
| toric15 | bp4/depolarizing | 0.06 | 0.09 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.22222 | [0.1413, 0.3131] | 116.7 | 2.562 | previous_damping |
| toric15 | binary_css/x_only | 0.07 | 0.07 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 400.8 | 0.7337 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.07 | 0.07 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 498.2 | 0.9136 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.07 | 0.07 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 792.1 | 1.526 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 56 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 39.51 | 0.8799 | joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 77 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 49.28 | 1.093 | joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 112 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 65.56 | 1.38 | joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 225 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 120.5 | 2.521 | joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 222.8 | 4.598 | joint_selected |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 38.51 | 0.8537 | previous_damping |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 77 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 48.28 | 1.03 | previous_damping |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.46512 | [0.3118, 0.6133] | 64.56 | 1.382 | previous_damping |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 119.3 | 2.483 | previous_damping |
| toric15 | bp4/depolarizing | 0.07 | 0.105 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.45455 | [0.3039, 0.6012] | 221.5 | 4.696 | previous_damping |
| toric15 | binary_css/x_only | 0.08 | 0.08 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 433.5 | 0.8701 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.08 | 0.08 | 506 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 486.8 | 0.9648 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.08 | 0.08 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 862 | 1.666 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 56 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 45.13 | 0.9745 | joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 59 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 47.13 | 1.04 | joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 112 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 82.47 | 1.764 | joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 225 | 0.3 | constant 1 | 0 | 0.66667 | [0.4719, 0.8206] | 157.8 | 3.232 | joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 450 | 0.3 | constant 1 | 0 | 0.64516 | [0.4537, 0.8007] | 312 | 6.257 | joint_selected |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 44.37 | 0.8986 | previous_damping |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 59 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 46.37 | 0.9876 | previous_damping |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 81.7 | 1.685 | previous_damping |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 157 | 3.226 | previous_damping |
| toric15 | bp4/depolarizing | 0.08 | 0.12 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.66667 | [0.4719, 0.8206] | 307 | 6.242 | previous_damping |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 450 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.7567 | joint_selected |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 506 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 506 | 0.8625 | joint_selected |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 900 | 0.4 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.459 | joint_selected |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 434.1 | 0.7323 | previous_damping |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 514.1 | 0.8533 | previous_damping |
| toric15 | binary_css/x_only | 0.09 | 0.09 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 862.7 | 1.537 | previous_damping |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 49 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 45.87 | 0.9997 | joint_selected |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 56 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 51.96 | 1.133 | joint_selected |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 112 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 100.7 | 2.172 | joint_selected |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 225 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 198.9 | 4.115 | joint_selected |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 450 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 394.6 | 7.776 | joint_selected |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 46 | 0.9038 | previous_damping |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 52.36 | 1.059 | previous_damping |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 101.5 | 2.043 | previous_damping |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 199.8 | 4.008 | previous_damping |
| toric15 | bp4/depolarizing | 0.09 | 0.135 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 395.4 | 7.875 | previous_damping |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 450 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 433.5 | 0.705 | joint_selected |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 562 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 540.2 | 0.8623 | joint_selected |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 900 | 0.4 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 862.1 | 1.37 | joint_selected |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 433.5 | 0.8594 | previous_damping |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 646 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 620.1 | 1.009 | previous_damping |
| toric15 | binary_css/x_only | 0.091 | 0.091 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 862 | 1.35 | previous_damping |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 49 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 44.44 | 1.061 | joint_selected |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 56 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 50.04 | 1.174 | joint_selected |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 112 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 94.84 | 2.129 | joint_selected |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 225 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 185.2 | 4.171 | joint_selected |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 450 | 0.3 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 365.2 | 7.994 | joint_selected |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 42.96 | 1.007 | previous_damping |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 48.56 | 1.132 | previous_damping |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 93.73 | 2.096 | previous_damping |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 180.7 | 4.056 | previous_damping |
| toric15 | bp4/depolarizing | 0.091 | 0.1365 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.76923 | [0.5635, 0.9064] | 353.7 | 7.781 | previous_damping |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 440 | 0.72 | joint_selected |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 534 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 520 | 0.8343 | joint_selected |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 900 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 868.6 | 1.363 | joint_selected |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.7367 | previous_damping |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 562 | 1.047 | previous_damping |
| toric15 | binary_css/x_only | 0.092 | 0.092 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.41 | previous_damping |
| toric15 | bp4/depolarizing | 0.092 | 0.138 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 47.68 | 1.104 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.092 | 0.138 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 54.05 | 1.198 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.092 | 0.138 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 105 | 2.26 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.092 | 0.138 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 207.7 | 4.723 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.092 | 0.138 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 412.2 | 8.772 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.093 | 0.093 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8729 | joint_selected |
| toric15 | binary_css/x_only | 0.093 | 0.093 | 900 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.667 | joint_selected |
| toric15 | binary_css/x_only | 0.093 | 0.093 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8597 | previous_damping |
| toric15 | binary_css/x_only | 0.093 | 0.093 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 1.009 | previous_damping |
| toric15 | binary_css/x_only | 0.093 | 0.093 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.65 | previous_damping |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 49 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 45.17 | 1.019 | joint_selected |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 56 | 0.3 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 51.26 | 1.144 | joint_selected |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 112 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 98.42 | 2.18 | joint_selected |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 225 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 192.6 | 4.151 | joint_selected |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 450 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 380.1 | 8.071 | joint_selected |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 45.61 | 1.023 | previous_damping |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 51.7 | 1.153 | previous_damping |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 100.2 | 2.181 | previous_damping |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 194.3 | 4.161 | previous_damping |
| toric15 | bp4/depolarizing | 0.093 | 0.1395 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 381.8 | 8.118 | previous_damping |
| toric15 | binary_css/x_only | 0.094 | 0.094 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.9525 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.094 | 0.094 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 2.075 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 42 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 38.96 | 1.001 | joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 56 | 0.3 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 50.62 | 1.322 | joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 112 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 95.38 | 2.374 | joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 225 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 182.3 | 4.593 | joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 450 | 0.3 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 355.4 | 8.31 | joint_selected |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 38.04 | 0.9511 | previous_damping |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 49.71 | 1.471 | previous_damping |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 96.38 | 2.283 | previous_damping |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 190.5 | 4.38 | previous_damping |
| toric15 | bp4/depolarizing | 0.094 | 0.141 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 378 | 8.771 | previous_damping |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 450 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.696 | joint_selected |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 534 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 534 | 0.817 | joint_selected |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 900 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.353 | joint_selected |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8514 | previous_damping |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 646 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 646 | 1.019 | previous_damping |
| toric15 | binary_css/x_only | 0.096 | 0.096 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.339 | previous_damping |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 42 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 41.81 | 1.074 | joint_selected |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 56 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 55.14 | 1.41 | joint_selected |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 112 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 107.4 | 2.581 | joint_selected |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 225 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 210.1 | 4.927 | joint_selected |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 450 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 414.7 | 9.587 | joint_selected |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 42 | 1.016 | previous_damping |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 55.18 | 1.384 | previous_damping |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 106.1 | 2.515 | previous_damping |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 208.8 | 4.968 | previous_damping |
| toric15 | bp4/depolarizing | 0.096 | 0.144 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 413.4 | 9.633 | previous_damping |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 450 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8278 | joint_selected |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 534 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 0.9601 | joint_selected |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 900 | 0.7 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.575 | joint_selected |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.814 | previous_damping |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 562 | 1.002 | previous_damping |
| toric15 | binary_css/x_only | 0.097 | 0.097 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.547 | previous_damping |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 42 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 39.82 | 0.9734 | joint_selected |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 56 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 52.55 | 1.558 | joint_selected |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 112 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 103.5 | 2.419 | joint_selected |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 225 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 206.2 | 4.802 | joint_selected |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 450 | 0.2 | constant 1 | 0 | 0.83333 | [0.6262, 0.9505] | 404.7 | 9.277 | joint_selected |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 39.04 | 0.9688 | previous_damping |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 51.22 | 1.275 | previous_damping |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 99.62 | 2.697 | previous_damping |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 193.8 | 4.601 | previous_damping |
| toric15 | bp4/depolarizing | 0.097 | 0.1455 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 382.9 | 8.78 | previous_damping |
| toric15 | binary_css/x_only | 0.098 | 0.098 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.9147 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.098 | 0.098 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 562 | 1.007 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.098 | 0.098 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.567 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 42 | 0.2 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 39.28 | 0.9507 | joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 56 | 0.2 | constant 1 | 0 | 0.8 | [0.593, 0.9287] | 50.48 | 1.206 | joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 112 | 0.2 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 94.96 | 2.278 | joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 225 | 0.2 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 181.9 | 4.246 | joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 450 | 0.2 | constant 1 | 0 | 0.76923 | [0.5635, 0.9064] | 355 | 8.027 | joint_selected |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 40.23 | 0.9648 | previous_damping |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 51.75 | 1.223 | previous_damping |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 98.42 | 2.269 | previous_damping |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 192.6 | 4.408 | previous_damping |
| toric15 | bp4/depolarizing | 0.098 | 0.147 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 380.1 | 8.601 | previous_damping |
| toric15 | binary_css/x_only | 0.099 | 0.099 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 1.109 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.099 | 0.099 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 0.9199 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.099 | 0.099 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.488 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 45 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 42.33 | 0.9918 | joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 56 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 51.5 | 1.156 | joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 112 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 98.17 | 2.138 | joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 225 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 192.3 | 4.226 | joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 450 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 379.8 | 8.231 | joint_selected |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 45 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 42.08 | 0.9447 | previous_damping |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 51.25 | 1.158 | previous_damping |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 97.92 | 2.145 | previous_damping |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 192.1 | 4.232 | previous_damping |
| toric15 | bp4/depolarizing | 0.099 | 0.1485 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.83333 | [0.6262, 0.9505] | 379.6 | 8.09 | previous_damping |
| toric15 | binary_css/x_only | 0.1 | 0.1 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8601 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.1 | 0.1 | 506 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 506 | 0.8789 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.1 | 0.1 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.623 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.1 | 0.15 | 45 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 43.9 | 1.045 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.1 | 0.15 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 54.05 | 1.213 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.1 | 0.15 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 105 | 2.312 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.1 | 0.15 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 207.7 | 4.525 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.1 | 0.15 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 412.2 | 8.819 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.101 | 0.101 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8353 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.101 | 0.101 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 0.9868 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.101 | 0.101 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.631 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.101 | 0.1515 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 46.43 | 1.048 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.101 | 0.1515 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 52.52 | 1.136 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.101 | 0.1515 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 101.2 | 2.116 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.101 | 0.1515 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 199.5 | 4.211 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.101 | 0.1515 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 395.1 | 8.046 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.102 | 0.102 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.7296 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.102 | 0.102 | 618 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 618 | 0.979 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.102 | 0.102 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.445 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.102 | 0.153 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 41.1 | 0.9882 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.102 | 0.153 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 54.23 | 1.287 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.102 | 0.153 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 105.1 | 2.477 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.102 | 0.153 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 207.9 | 5.111 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.102 | 0.153 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 412.4 | 9.457 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.103 | 0.103 | 450 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.8932 | joint_selected |
| toric15 | binary_css/x_only | 0.103 | 0.103 | 900 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.715 | joint_selected |
| toric15 | binary_css/x_only | 0.103 | 0.103 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8862 | previous_damping |
| toric15 | binary_css/x_only | 0.103 | 0.103 | 506 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 506 | 0.9819 | previous_damping |
| toric15 | binary_css/x_only | 0.103 | 0.103 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.733 | previous_damping |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 45 | 0.2 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 44.24 | 1.038 | joint_selected |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 56 | 0.2 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 54.71 | 1.216 | joint_selected |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 112 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 106.2 | 2.365 | joint_selected |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 225 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 208.9 | 4.715 | joint_selected |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 450 | 0.2 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 412.6 | 8.937 | joint_selected |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 45 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 43.95 | 0.9994 | previous_damping |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 54.43 | 1.26 | previous_damping |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 105.5 | 2.224 | previous_damping |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 208.3 | 4.462 | previous_damping |
| toric15 | bp4/depolarizing | 0.103 | 0.1545 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 412.8 | 8.893 | previous_damping |
| toric15 | binary_css/x_only | 0.104 | 0.104 | 450 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.8578 | joint_selected |
| toric15 | binary_css/x_only | 0.104 | 0.104 | 900 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.643 | joint_selected |
| toric15 | binary_css/x_only | 0.104 | 0.104 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.9157 | previous_damping |
| toric15 | binary_css/x_only | 0.104 | 0.104 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 0.9808 | previous_damping |
| toric15 | binary_css/x_only | 0.104 | 0.104 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.601 | previous_damping |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 45 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 45 | 1.224 | joint_selected |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 56 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 55.81 | 1.534 | joint_selected |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 112 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 109.1 | 2.747 | joint_selected |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 225 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 216.8 | 5.071 | joint_selected |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 450 | 0.2 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 431 | 9.64 | joint_selected |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 45 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 45 | 1.221 | previous_damping |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 56 | 1.485 | previous_damping |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 109.3 | 2.761 | previous_damping |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 217 | 5.11 | previous_damping |
| toric15 | bp4/depolarizing | 0.104 | 0.156 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 431.2 | 9.797 | previous_damping |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 450 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8092 | joint_selected |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 562 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 562 | 0.9191 | joint_selected |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 900 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.423 | joint_selected |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 437 | 0.7424 | previous_damping |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 562 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 543.7 | 0.9033 | previous_damping |
| toric15 | binary_css/x_only | 0.105 | 0.105 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 865.6 | 1.359 | previous_damping |
| toric15 | bp4/depolarizing | 0.105 | 0.1575 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 48.57 | 1.007 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.105 | 0.1575 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 55.24 | 1.115 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.105 | 0.1575 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.90909 | [0.7084, 0.9883] | 106.5 | 2.117 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.105 | 0.1575 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 194.8 | 3.843 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.105 | 0.1575 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.8 | [0.593, 0.9287] | 374.8 | 7.344 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.106 | 0.106 | 450 | 0.75 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8506 | joint_selected |
| toric15 | binary_css/x_only | 0.106 | 0.106 | 900 | 0.75 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.645 | joint_selected |
| toric15 | binary_css/x_only | 0.106 | 0.106 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8535 | previous_damping |
| toric15 | binary_css/x_only | 0.106 | 0.106 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 0.997 | previous_damping |
| toric15 | binary_css/x_only | 0.106 | 0.106 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.631 | previous_damping |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 45 | 0.2 | constant 1 | 0 | 1 | [0.8316, 1] | 45 | 1.131 | joint_selected |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 56 | 0.2 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 55.52 | 1.278 | joint_selected |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 112 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 107.3 | 2.483 | joint_selected |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 225 | 0.2 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 210 | 4.683 | joint_selected |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 450 | 0.2 | constant 1 | 0 | 0.86957 | [0.6641, 0.9709] | 407.4 | 9.14 | joint_selected |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 42 | 1.101 | previous_damping |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 55.86 | 1.376 | previous_damping |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 107.7 | 2.497 | previous_damping |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 205.9 | 4.58 | previous_damping |
| toric15 | bp4/depolarizing | 0.106 | 0.159 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.86957 | [0.6641, 0.9709] | 401.6 | 8.735 | previous_damping |
| toric15 | binary_css/x_only | 0.107 | 0.107 | 450 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.9043 | joint_selected |
| toric15 | binary_css/x_only | 0.107 | 0.107 | 900 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.695 | joint_selected |
| toric15 | binary_css/x_only | 0.107 | 0.107 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8752 | previous_damping |
| toric15 | binary_css/x_only | 0.107 | 0.107 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 1.025 | previous_damping |
| toric15 | binary_css/x_only | 0.107 | 0.107 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.657 | previous_damping |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 42 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 42 | 1.23 | joint_selected |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 56 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 56 | 1.599 | joint_selected |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 112 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 112 | 2.762 | joint_selected |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 225 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 225 | 4.989 | joint_selected |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 450 | 0.3 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 9.867 | joint_selected |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 42 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 42 | 1.072 | previous_damping |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 56 | 1.37 | previous_damping |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 112 | 2.478 | previous_damping |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 225 | 5.031 | previous_damping |
| toric15 | bp4/depolarizing | 0.107 | 0.1605 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 9.964 | previous_damping |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 450 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 0.7087 | joint_selected |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 534 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 534 | 0.8236 | joint_selected |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 900 | 0.7 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.365 | joint_selected |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.7236 | previous_damping |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 646 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 646 | 0.9856 | previous_damping |
| toric15 | binary_css/x_only | 0.108 | 0.108 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.35 | previous_damping |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 45 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 44.81 | 0.9852 | joint_selected |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 56 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 55.29 | 1.23 | joint_selected |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 112 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 108.6 | 2.358 | joint_selected |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 225 | 0.3 | constant 1 | 0 | 0.95238 | [0.7618, 0.9987] | 216.2 | 4.613 | joint_selected |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 450 | 0.3 | constant 1 | 0 | 0.90909 | [0.7084, 0.9883] | 428.8 | 9.078 | joint_selected |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 45 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 45 | 0.9951 | previous_damping |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 56 | 1.251 | previous_damping |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 112 | 2.433 | previous_damping |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 225 | 4.75 | previous_damping |
| toric15 | bp4/depolarizing | 0.108 | 0.162 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 9.489 | previous_damping |
| toric15 | binary_css/x_only | 0.109 | 0.109 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.8852 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.109 | 0.109 | 506 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 506 | 0.9806 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.109 | 0.109 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.658 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.109 | 0.1635 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 48.1 | 0.9875 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.109 | 0.1635 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 54.76 | 1.222 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.109 | 0.1635 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 108.1 | 2.491 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.109 | 0.1635 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 215.7 | 4.442 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.109 | 0.1635 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 430 | 8.643 | previous_damping,joint_selected |
| toric15 | binary_css/x_only | 0.11 | 0.11 | 450 | 0.2 | constant 1 | 0 | 1 | [0.8316, 1] | 450 | 1.074 | joint_selected |
| toric15 | binary_css/x_only | 0.11 | 0.11 | 900 | 0.2 | constant 1 | 0 | 1 | [0.8316, 1] | 900 | 1.863 | joint_selected |
| toric15 | binary_css/x_only | 0.11 | 0.11 | 450 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 450 | 0.888 | previous_damping |
| toric15 | binary_css/x_only | 0.11 | 0.11 | 534 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 534 | 1.217 | previous_damping |
| toric15 | binary_css/x_only | 0.11 | 0.11 | 900 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 1 | [0.8316, 1] | 900 | 1.65 | previous_damping |
| toric15 | bp4/depolarizing | 0.11 | 0.165 | 49 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 47.43 | 0.9783 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.11 | 0.165 | 56 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 54.1 | 1.14 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.11 | 0.165 | 112 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 107.4 | 2.351 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.11 | 0.165 | 225 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 215 | 4.374 | previous_damping,joint_selected |
| toric15 | bp4/depolarizing | 0.11 | 0.165 | 450 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.95238 | [0.7618, 0.9987] | 429.3 | 8.435 | previous_damping,joint_selected |

All218 point workers are complete; calibrated plans and raw event ledgers remain under results/. A zero-failure completed point is displayed as an upper bound. All20-failure/1e8-shot intervals respect the stopping rule. Timing cohorts and confirmation uncertainty are different quantities; the table does not assert simultaneous superiority or a same-channel comparison between BP and Q-BP.
