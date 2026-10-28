# BP4 p=.06 extend results

Audited 6/6 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p006_t2000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p006_t10000 | 55/50000 | 0.0011 [0.00086801, 0.0013768] | 8/0 | 0.003906 | 15.37 |
| sp_f64_v2_d01_p006_t5000 | 56/50000 | 0.00112 [0.0008858, 0.001399] | 7/0 | 0.007812 | 9.85 |
| sp_f64_v2_d02_p006_t2000 | 58/50000 | 0.00116 [0.00092144, 0.0014433] | 9/4 | 0.1334 | 6.07 |
| sp_f64_v2_d02_p006_t1000 | 63/50000 | 0.00126 [0.0010109, 0.0015538] | 7/7 | 0.6047 | 4.85 |
| sp_f64_v2_d01_p006_t2000 | 63/50000 | 0.00126 [0.0010109, 0.0015538] | 0/0 | 1 | 6.34 |
| sp_f64_v2_d01_p006_t1000 | 68/50000 | 0.00136 [0.0011007, 0.0016639] | 0/5 | 1 | 5.04 |

## B2

Paired reference: `sp_f64_v2_d01_p006_t2000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
