# BP4 p=.06 b2_prior_confirm results

Audited 5/5 tasks.
All rates use fixed N and exact two-sided 90% binomial intervals.
Paired p-values are one-sided exact McNemar tests versus the plan's code-specific incumbent;
P-values are unadjusted after policy search; treat them as exploratory.

## B2

Paired reference: `sp_f64_v2_d01_p016_t5000`.

| Candidate | Failures/N | LER (90% CI) | Rescues/losses | Paired p | Mean iters |
|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p015_t5000 | 30/100000 | 0.0003 [0.00021595, 0.00040688] | 15/6 | 0.03918 | 6.74 |
| sp_f64_v2_d01_p016_t10000 | 34/100000 | 0.00034 [0.00025011, 0.00045263] | 5/0 | 0.03125 | 8.84 |
| sp_f64_v2_d01_p014_t5000 | 38/100000 | 0.00038 [0.00028461, 0.00049806] | 12/11 | 0.5 | 7.05 |
| sp_f64_v2_d01_p017_t5000 | 38/100000 | 0.00038 [0.00028461, 0.00049806] | 11/10 | 0.5 | 7.24 |
| sp_f64_v2_d01_p016_t5000 | 39/100000 | 0.00039 [0.00029328, 0.00050937] | 0/0 | 1 | 7.20 |
