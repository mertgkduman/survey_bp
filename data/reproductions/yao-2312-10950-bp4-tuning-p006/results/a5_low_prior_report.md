# BP4 p=.06 a5_low_prior results

Audited 7/7 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p003_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p0005_t10000 | 57/100000 | 0.00057 [0.00045178, 0.00071064] | 24/7 | 0.001663 | 11.69 |
| sp_f64_v2_d01_p002_t10000 | 59/100000 | 0.00059 [0.00046962, 0.00073278] | 21/6 | 0.002962 | 11.32 |
| sp_f64_v2_d01_p0015_t10000 | 61/100000 | 0.00061 [0.00048749, 0.00075489] | 20/7 | 0.009579 | 11.30 |
| sp_f64_v2_d01_p001_t10000 | 61/100000 | 0.00061 [0.00048749, 0.00075489] | 22/9 | 0.01472 | 11.57 |
| sp_f64_v2_d01_p0025_t10000 | 66/100000 | 0.00066 [0.00053232, 0.00081002] | 17/9 | 0.08432 | 11.73 |
| sp_f64_v2_d01_p003_t10000 | 74/100000 | 0.00074 [0.00060445, 0.00089783] | 0/0 | 1 | 12.53 |
| sp_f64_v2_d01_p004_t10000 | 85/100000 | 0.00085 [0.00070429, 0.0010179] | 9/20 | 0.9879 | 13.86 |

## B2

Paired reference: `sp_f64_v2_d01_p003_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
