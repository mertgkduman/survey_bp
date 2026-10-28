# BP4 p=.06 b2_prior_confirm stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
B2: `sp_f64_v2_d01_p016_t5000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## B2

Incumbent: `sp_f64_v2_d01_p016_t5000`, 39/100000 = 0.00039; 90% CI [0.000293282, 0.000509367].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p015_t5000 | 30/100000 | 15/6 | 0.03918 | yes |
| sp_f64_v2_d01_p016_t10000 | 34/100000 | 5/0 | 0.03125 | yes |
| sp_f64_v2_d01_p014_t5000 | 38/100000 | 12/11 | 0.5 | no |
| sp_f64_v2_d01_p017_t5000 | 38/100000 | 11/10 | 0.5 | no |

Stop under the stated rule: no
