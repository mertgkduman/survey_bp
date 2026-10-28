# BP4 p=.06 a5_prior results

Audited 7/7 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p0045_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p003_t10000 | 71/100000 | 0.00071 [0.00057735, 0.00086495] | 22/3 | 7.826e-05 | 12.29 |
| sp_f64_v2_d01_p0035_t10000 | 79/100000 | 0.00079 [0.00064975, 0.0009525] | 17/6 | 0.01734 | 12.99 |
| sp_f64_v2_d01_p004_t10000 | 79/100000 | 0.00079 [0.00064975, 0.0009525] | 13/2 | 0.003693 | 13.31 |
| sp_f64_v2_d01_p005_t10000 | 88/100000 | 0.00088 [0.00073164, 0.0010506] | 11/9 | 0.4119 | 13.95 |
| sp_f64_v2_d01_p0045_t10000 | 90/100000 | 0.0009 [0.0007499, 0.0010723] | 0/0 | 1 | 13.98 |
| sp_f64_v2_d01_p0055_t10000 | 100/100000 | 0.001 [0.00084146, 0.0011807] | 8/18 | 0.9855 | 15.16 |
| sp_f64_v2_d01_p006_t10000 | 107/100000 | 0.00107 [0.0009058, 0.0012563] | 8/25 | 0.9993 | 15.99 |

## B2

Paired reference: `sp_f64_v2_d01_p0045_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
