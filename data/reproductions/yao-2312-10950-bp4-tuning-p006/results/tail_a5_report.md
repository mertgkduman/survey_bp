# BP4 p=.06 tail_a5 results

Audited 3/3 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p006_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p006_t50000 | 45/50000 | 0.0009 [0.00069133, 0.0011538] | 2/0 | 0.25 | 50.70 |
| sp_f64_v2_d01_p006_t20000 | 46/50000 | 0.00092 [0.00070888, 0.0011762] | 1/0 | 0.5 | 23.58 |
| sp_f64_v2_d01_p006_t10000 | 47/50000 | 0.00094 [0.00072647, 0.0011986] | 0/0 | 1 | 14.37 |

## B2

Paired reference: `sp_f64_v2_d01_p006_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
