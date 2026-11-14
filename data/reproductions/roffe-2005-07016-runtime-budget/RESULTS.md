# Roffe: joint numerical tuning and runtime-matched iteration sweeps

Independent audit: 0/218 completed point workers; 0 confirmed control/cap measurements and 0 retained training measurements.

Target: same-CPU mean warmed canonical BP+OSD0 decoder time per shot at original T=n. Candidate timing excludes sampling, truth evaluation, JIT and I/O. Actual time/reference ratios are shown; within10% is a calibration tolerance, not assumed equality. Values above1.1 exceed the budget. Values below.9 can indicate early-convergence saturation, calibration drift or a still-lower cap; inspect each point plan/history.

Training jointly searches old-V2C damping, constant or paper-scheduled min-sum scaling, and offset in natural-LLR units. Only fresh confirmation is in the main table. All tuning settings/caps are retained in tuning-results.csv. Different iteration caps/settings are explicit, and no unlike policies are pooled. Binary BP is X-only; joint Q-BP remains depolarizing at1.5p_X.

| Code | Decoder/noise | Matched p_X | Physical p | T | d | Scaling | Offset | LER | 95% interval | Mean sweeps | Time / OSD0 | Role |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |

Missing point workers remain pending; their calibrated plans and raw progress are retained under results/. A zero-failure completed point is displayed as an upper bound. All20-failure/1e8-shot intervals respect the stopping rule. Timing cohorts and confirmation uncertainty are different quantities; the table does not assert simultaneous superiority or a same-channel comparison between BP and Q-BP.
