# Corrected B1 p=0.05 matched intervention and damping pilot v2

128 matched physical samples per arm, 14 arms, V2C damping γ=0.5. Every terminal shot is retained.
Verification: all 14 public runs replayed and the aggregate ledger and physical sample identities matched.
Evidence relation: `pilot_adaptation`; assessment: `not_assessed`. These descriptive counts do not establish decoder ranking or source-curve agreement. The v1 run was invalidated by source-semantic defects.

| Intervention | Valid off | Valid damped | Newly valid | Lost valid | Unavailable off | Unavailable damped | Mean BP sweeps off | Mean BP sweeps damped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| identity | 115 | 128 | 13 | 0 | 13 | 0 | 24.67 | 9.59 |
| guided_decimation | 120 | 128 | 8 | 0 | 8 | 0 | 27.69 | 9.59 |
| impulse | 115 | 128 | 13 | 0 | 13 | 0 | 28.02 | 9.59 |
| freezing | 102 | 105 | 11 | 8 | 26 | 23 | 29.65 | 25.46 |
| syndrome_flip | 119 | 128 | 9 | 0 | 9 | 0 | 27.15 | 9.59 |
| sign_flip | 120 | 126 | 7 | 1 | 8 | 2 | 22.47 | 14.92 |
| restart_belief | 92 | 102 | 18 | 8 | 36 | 26 | 82.42 | 81.53 |

Valid means exact or stabilizer-equivalent recovery on the original CSS problem. Newly valid and lost valid compare the same physical sample under damping off and on.
Mean BP sweeps counts admitted convergence checks per sample across all attempts and branches. `summary.json` also records intervention actions, BP calls, exact outcomes, logical failures, and termination counts.
Each arm has its own `manifest.json`, `events.jsonl`, and `result.json`; the root `events.jsonl` and `result.json` bind the aggregate evidence.
