# BP4 p=.06 a5_final_neighborhood stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p0005_t10000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p0005_t10000`, 59/100000 = 0.00059; 90% CI [0.000469617, 0.000732784].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d02_p0005_t10000 | 41/100000 | 19/1 | 2.003e-05 | yes |
| sp_f64_v2_d015_p0005_t10000 | 48/100000 | 16/5 | 0.0133 | yes |
| sp_f64_v2_d01_p0005_t20000 | 53/100000 | 6/0 | 0.01562 | yes |
| sp_f64_v2_d01_p0005_t5000 | 70/100000 | 0/11 | 1 | no |
| sp_f64_v2_d005_p0005_t10000 | 80/100000 | 3/24 | 1 | no |

Stop under the stated rule: no
