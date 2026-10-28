# BP4 p=.06 a5_low_prior stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p003_t10000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p003_t10000`, 74/100000 = 0.00074; 90% CI [0.000604451, 0.000897832].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p0005_t10000 | 57/100000 | 24/7 | 0.001663 | yes |
| sp_f64_v2_d01_p002_t10000 | 59/100000 | 21/6 | 0.002962 | yes |
| sp_f64_v2_d01_p001_t10000 | 61/100000 | 22/9 | 0.01472 | yes |
| sp_f64_v2_d01_p0015_t10000 | 61/100000 | 20/7 | 0.009579 | yes |
| sp_f64_v2_d01_p0025_t10000 | 66/100000 | 17/9 | 0.08432 | yes |
| sp_f64_v2_d01_p004_t10000 | 85/100000 | 9/20 | 0.9879 | no |

Stop under the stated rule: no
