# BP4 p=.06 a5_tiny_prior results

Audited 7/7 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p0005_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p0005_t10000 | 47/100000 | 0.00047 [0.00036322, 0.00059932] | 0/0 | 1 | 11.19 |
| sp_f64_v2_d01_p00005_t10000 | 50/100000 | 0.0005 [0.00038967, 0.00063283] | 9/12 | 0.8083 | 12.00 |
| sp_f64_v2_d01_p001_t10000 | 52/100000 | 0.00052 [0.00040736, 0.00065511] | 9/14 | 0.895 | 10.84 |
| sp_f64_v2_d01_p00075_t10000 | 52/100000 | 0.00052 [0.00040736, 0.00065511] | 5/10 | 0.9408 | 11.14 |
| sp_f64_v2_d01_p0002_t10000 | 52/100000 | 0.00052 [0.00040736, 0.00065511] | 7/12 | 0.9165 | 11.53 |
| sp_f64_v2_d01_p0003_t10000 | 52/100000 | 0.00052 [0.00040736, 0.00065511] | 9/14 | 0.895 | 11.78 |
| sp_f64_v2_d01_p0001_t10000 | 52/100000 | 0.00052 [0.00040736, 0.00065511] | 7/12 | 0.9165 | 12.26 |

## B2

Paired reference: `sp_f64_v2_d01_p0005_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
