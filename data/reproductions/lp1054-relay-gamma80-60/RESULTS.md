# LP1054 uniform80/disordered60 gamma tuning

2/12 background/rate workers fully audited; 6 distinct fresh policies.

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
