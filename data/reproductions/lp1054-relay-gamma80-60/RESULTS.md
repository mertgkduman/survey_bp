# LP1054 uniform80/disordered60 gamma tuning

6/12 background/rate workers fully audited; 24 distinct fresh policies.

User-confirmed one80-sweep uniform-memory leg plus one60-sweep disordered-memory leg,140 maximum per CSS component. Code-capacity adaptation of Relay Eq4, not circuit-paper reproduction. Both logical components count. Numerical backgrounds are fixed source NMS or parent training-only selected BP settings; no parent fresh outcome enters selection. Independent noise/memory streams and four disjoint stage seeds. All selected and ablation confirmations remain separate. This140 budget differs from prior32/128 studies. New latency excludes provenance hashing and is not directly comparable to older instrumented timings.

The first leg uses one scalar gamma for all variables, with80 sweeps maximum. If needed, one further60-sweep leg uses a quenched independent gamma per variable. Each leg stops at syndrome convergence; S=1. Gamma changes the prior-memory equation, not the separately fixed V2C damping coefficient. Zero-width intervals are exact fixed-gamma ablations.

Fresh roles: selected full gamma, first phase only, disordered phase only, zero-memory80/60 reset and continuous BP140. Roles sharing the same exact policy reuse one cohort; no duplicate shot counts. Tuning uses three separate training stages; none is pooled into fresh confirmation. Work includes both components and every attempted segment. New latency excludes external hashes and cannot be directly ranked against old provenance-instrumented times.

| Background | p | Roles | gamma0 | Gamma interval | Block LER | 95% CI | Shots | Mean sweeps | Mean edges | Mean µs |
| --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| prior_tuned_numerics | 0.06 | continuous_bp140 | None | continuous BP | 0.0192123 | [0.0117739,0.0283832] | 1041 | 14.748 | 109727.5 | 650.90 |
| prior_tuned_numerics | 0.06 | gamma_selected,disordered_phase_only | 0.0 | [-0.375,0.5] | 0.0178412 | [0.0109311,0.0263655] | 1121 | 14.724 | 109549.2 | 762.45 |
| prior_tuned_numerics | 0.06 | uniform_phase_only,reset_zero_gamma | 0.0 | [0.0,0.0] | 0.0192123 | [0.0117739,0.0283832] | 1041 | 14.748 | 109727.5 | 781.76 |
| source_numerics | 0.06 | continuous_bp140 | None | continuous BP | 0.0430108 | [0.0264669,0.063209] | 465 | 21.123 | 157152.0 | 1112.44 |
| source_numerics | 0.06 | gamma_selected,disordered_phase_only | 0.0 | [0.0,0.375] | 0.0252207 | [0.015472,0.0372105] | 793 | 20.096 | 149513.0 | 1283.54 |
| source_numerics | 0.06 | uniform_phase_only,reset_zero_gamma | 0.0 | [0.0,0.0] | 0.0430108 | [0.0264669,0.063209] | 465 | 21.123 | 157152.0 | 1337.17 |
| prior_tuned_numerics | 0.08 | continuous_bp140 | None | continuous BP | 0.113636 | [0.0708102,0.164348] | 176 | 42.693 | 317637.3 | 2308.16 |
| prior_tuned_numerics | 0.08 | disordered_phase_only | 0.0 | [-0.125,0.125] | 0.108696 | [0.0676708,0.157382] | 184 | 42.870 | 318949.6 | 2855.68 |
| prior_tuned_numerics | 0.08 | gamma_selected | 0.0625 | [-0.125,0.125] | 0.121951 | [0.0761066,0.176034] | 164 | 47.957 | 356802.4 | 3204.18 |
| prior_tuned_numerics | 0.08 | reset_zero_gamma | 0.0 | [0.0,0.0] | 0.113636 | [0.0708102,0.164348] | 176 | 42.693 | 317637.3 | 2808.47 |
| prior_tuned_numerics | 0.08 | uniform_phase_only | 0.0625 | [0.0,0.0] | 0.097561 | [0.0606167,0.141623] | 205 | 48.810 | 363144.6 | 3188.45 |
| source_numerics | 0.08 | continuous_bp140 | None | continuous BP | 0.224719 | [0.142995,0.316453] | 89 | 60.753 | 452000.9 | 3023.86 |
| source_numerics | 0.08 | disordered_phase_only | 0.0 | [-0.125,0.25] | 0.204082 | [0.129342,0.288861] | 98 | 66.378 | 493849.0 | 4095.13 |
| source_numerics | 0.08 | gamma_selected | 0.125 | [-0.125,0.25] | 0.190476 | [0.120404,0.270502] | 105 | 56.143 | 417702.9 | 3571.09 |
| source_numerics | 0.08 | reset_zero_gamma | 0.0 | [0.0,0.0] | 0.243902 | [0.155791,0.34182] | 82 | 60.756 | 452025.4 | 3752.63 |
| source_numerics | 0.08 | uniform_phase_only | 0.125 | [0.0,0.0] | 0.194175 | [0.122829,0.275506] | 103 | 55.573 | 413461.7 | 3539.64 |
| prior_tuned_numerics | 0.1 | continuous_bp140 | None | continuous BP | 0.666667 | [0.47188,0.820616] | 30 | 161.467 | 1201312.0 | 7031.07 |
| prior_tuned_numerics | 0.1 | gamma_selected,disordered_phase_only | 0.0 | [0.0,0.375] | 0.666667 | [0.47188,0.820616] | 30 | 162.400 | 1208256.0 | 7752.18 |
| prior_tuned_numerics | 0.1 | uniform_phase_only,reset_zero_gamma | 0.0 | [0.0,0.0] | 0.666667 | [0.47188,0.820616] | 30 | 162.400 | 1208256.0 | 7811.34 |
| source_numerics | 0.1 | continuous_bp140 | None | continuous BP | 0.769231 | [0.563525,0.906436] | 26 | 189.000 | 1406160.0 | 7637.68 |
| source_numerics | 0.1 | disordered_phase_only | 0.0 | [-0.125,0.125] | 0.769231 | [0.563525,0.906436] | 26 | 189.000 | 1406160.0 | 8586.99 |
| source_numerics | 0.1 | gamma_selected | 0.125 | [-0.125,0.125] | 0.833333 | [0.626158,0.950492] | 24 | 187.417 | 1394380.0 | 8591.82 |
| source_numerics | 0.1 | reset_zero_gamma | 0.0 | [0.0,0.0] | 0.769231 | [0.563525,0.906436] | 26 | 189.000 | 1406160.0 | 8577.56 |
| source_numerics | 0.1 | uniform_phase_only | 0.125 | [0.0,0.0] | 0.8 | [0.592963,0.928681] | 25 | 185.720 | 1381756.8 | 8511.37 |
