# BP4 p=.06 sweet_b2 results

Audited 8/8 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p015_t5000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|

## B2

Paired reference: `sp_f64_v2_d01_p015_t5000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p016_t10000 | 22/80000 | 0.000275 [0.00018618, 0.00039266] | 7/3 | 0.1719 | 8.15 |
| sp_f64_v2_d01_p016_t5000 | 23/80000 | 0.0002875 [0.0001965, 0.00040729] | 7/4 | 0.2744 | 6.88 |
| sp_f64_v2_d01_p014_t5000 | 24/80000 | 0.0003 [0.00020687, 0.00042188] | 7/5 | 0.3872 | 6.66 |
| sp_f64_v2_d01_p015_t10000 | 24/80000 | 0.0003 [0.00020687, 0.00042188] | 2/0 | 0.25 | 8.23 |
| sp_f64_v2_d01_p015_t20000 | 24/80000 | 0.0003 [0.00020687, 0.00042188] | 2/0 | 0.25 | 10.93 |
| sp_f64_v2_d01_p015_t5000 | 26/80000 | 0.000325 [0.00022774, 0.00045093] | 0/0 | 1 | 6.82 |
| sp_f64_v2_d01_p018_t5000 | 26/80000 | 0.000325 [0.00022774, 0.00045093] | 8/8 | 0.5982 | 7.17 |
| sp_f64_v2_d01_p020_t5000 | 30/80000 | 0.000375 [0.00026994, 0.0005086] | 6/10 | 0.8949 | 7.75 |
