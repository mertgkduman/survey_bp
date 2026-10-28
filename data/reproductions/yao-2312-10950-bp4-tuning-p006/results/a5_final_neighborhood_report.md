# BP4 p=.06 a5_final_neighborhood results

Audited 6/6 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p0005_t10000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d02_p0005_t10000 | 41/100000 | 0.00041 [0.00031068, 0.00053194] | 19/1 | 2.003e-05 | 8.92 |
| sp_f64_v2_d015_p0005_t10000 | 48/100000 | 0.00048 [0.00037202, 0.0006105] | 16/5 | 0.0133 | 10.19 |
| sp_f64_v2_d01_p0005_t20000 | 53/100000 | 0.00053 [0.00041622, 0.00066624] | 6/0 | 0.01562 | 17.34 |
| sp_f64_v2_d01_p0005_t10000 | 59/100000 | 0.00059 [0.00046962, 0.00073278] | 0/0 | 1 | 11.78 |
| sp_f64_v2_d01_p0005_t5000 | 70/100000 | 0.0007 [0.00056833, 0.00085398] | 0/11 | 1 | 8.53 |
| sp_f64_v2_d005_p0005_t10000 | 80/100000 | 0.0008 [0.00065882, 0.00096342] | 3/24 | 1 | 15.57 |
