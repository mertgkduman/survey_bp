# Roffe: joint numerical tuning and runtime-matched iteration sweeps

Independent audit: 6/218 completed point workers; 45 confirmed control/cap measurements and 5496 retained training measurements.

Target: same-CPU mean warmed canonical BP+OSD0 decoder time per shot at original T=n. Candidate timing excludes sampling, truth evaluation, JIT and I/O. Actual time/reference ratios are shown; within10% is a calibration tolerance, not assumed equality. Values above1.1 exceed the budget. Values below.9 can indicate early-convergence saturation, calibration drift or a still-lower cap; inspect each point plan/history.

Training jointly searches old-V2C damping, constant or paper-scheduled min-sum scaling, and offset in natural-LLR units. Only fresh confirmation is in the main table. All tuning settings/caps are retained in tuning-results.csv. Different iteration caps/settings are explicit, and no unlike policies are pooled. Binary BP is X-only; joint Q-BP remains depolarizing at1.5p_X.

| Code | Decoder/noise | Matched p_X | Physical p | T | d | Scaling | Offset | LER | 95% interval | Mean sweeps | Time / OSD0 | Role |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 7.265 | 0.7532 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 232 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 8.758 | 0.8508 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.01 | 0.01 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.021322 | [0.01307, 0.03149] | 10.72 | 0.9174 | previous_damping,joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 162 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.095238 | [0.05915, 0.1383] | 24.63 | 0.8367 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 273 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.090498 | [0.05616, 0.1316] | 34.74 | 1.089 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 324 | 0.4 | 1×(1−2⁻ᵗ) | 0 | 0.090498 | [0.05616, 0.1316] | 39.35 | 1.204 | joint_selected |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 24.53 | 0.9042 | previous_damping |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 243 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 32.43 | 1.361 | previous_damping |
| toric9 | binary_css/x_only | 0.02 | 0.02 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.097561 | [0.06062, 0.1416] | 40.33 | 1.202 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 162 | 0.5 | constant 1 | 0 | 0.16393 | [0.1031, 0.2343] | 30.98 | 0.5507 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 324 | 0.5 | constant 1 | 0 | 0.1626 | [0.1022, 0.2325] | 58.98 | 0.8976 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 648 | 0.5 | constant 1 | 0 | 0.1626 | [0.1022, 0.2325] | 111.7 | 1.613 | joint_selected |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 162 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 38.76 | 0.6562 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 283 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 58.76 | 0.9187 | previous_damping |
| toric9 | binary_css/x_only | 0.03 | 0.03 | 324 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.16529 | [0.104, 0.2362] | 65.54 | 1.024 | previous_damping |
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
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 242 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0052002 | [0.003179, 0.007706] | 6.882 | 1.03 | previous_damping |
| toric11 | bp4/depolarizing | 0.02 | 0.03 | 484 | 0.3 | 1×(1−2⁻ᵗ) | 0 | 0.0052002 | [0.003179, 0.007706] | 8.141 | 1.19 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 338 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 25.67 | 0.8124 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 443 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 31.6 | 0.9673 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 676 | 0.2 | constant 1 | 0 | 0.056497 | [0.03485, 0.08278] | 44.77 | 1.19 | joint_selected |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 338 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 24.32 | 0.7882 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 485 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 32.62 | 0.944 | previous_damping |
| toric13 | binary_css/x_only | 0.01 | 0.01 | 676 | 0.5 | 1×(1−2⁻ᵗ) | 0 | 0.056497 | [0.03485, 0.08278] | 43.41 | 1.345 | previous_damping |

Missing point workers remain pending; their calibrated plans and raw progress are retained under results/. A zero-failure completed point is displayed as an upper bound. All20-failure/1e8-shot intervals respect the stopping rule. Timing cohorts and confirmation uncertainty are different quantities; the table does not assert simultaneous superiority or a same-channel comparison between BP and Q-BP.
