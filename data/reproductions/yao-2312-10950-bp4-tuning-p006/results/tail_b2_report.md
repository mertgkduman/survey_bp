# BP4 p=.06 tail_b2 results

Audited 8/8 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## A5

Paired reference: `sp_f64_v2_d01_p012_t1000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|

## B2

Paired reference: `sp_f64_v2_d01_p012_t1000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p015_t5000 | 10/50000 | 0.0002 [0.00010851, 0.00033922] | 15/0 | 3.052e-05 | 6.31 |
| sp_f64_v2_d01_p015_t2000 | 13/50000 | 0.00026 [0.0001538, 0.00041334] | 13/1 | 0.0009155 | 5.70 |
| sp_f64_v2_d01_p012_t10000 | 20/50000 | 0.0004 [0.00026511, 0.00058119] | 5/0 | 0.03125 | 8.99 |
| sp_f64_v2_d01_p012_t5000 | 21/50000 | 0.00042 [0.00028146, 0.00060475] | 4/0 | 0.0625 | 7.13 |
| sp_f64_v2_d01_p012_t2000 | 22/50000 | 0.00044 [0.00029789, 0.00062824] | 3/0 | 0.125 | 5.91 |
| sp_f64_v2_d01_p012_t1000 | 25/50000 | 0.0005 [0.00034767, 0.00069825] | 0/0 | 1 | 5.47 |
| sp_f64_v2_d01_p006_t5000 | 29/50000 | 0.00058 [0.00041495, 0.00079074] | 11/15 | 0.8365 | 8.12 |
| sp_f64_v2_d01_p006_t10000 | 29/50000 | 0.00058 [0.00041495, 0.00079074] | 11/15 | 0.8365 | 10.92 |
