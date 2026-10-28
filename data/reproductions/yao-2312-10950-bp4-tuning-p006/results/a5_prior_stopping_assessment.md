# BP4 p=.06 a5_prior stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p0045_t10000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p0045_t10000`, 90/100000 = 0.0009; 90% CI [0.000749896, 0.00107229].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p003_t10000 | 71/100000 | 22/3 | 7.826e-05 | yes |
| sp_f64_v2_d01_p0035_t10000 | 79/100000 | 17/6 | 0.01734 | yes |
| sp_f64_v2_d01_p004_t10000 | 79/100000 | 13/2 | 0.003693 | yes |
| sp_f64_v2_d01_p005_t10000 | 88/100000 | 11/9 | 0.4119 | no |
| sp_f64_v2_d01_p0055_t10000 | 100/100000 | 8/18 | 0.9855 | no |
| sp_f64_v2_d01_p006_t10000 | 107/100000 | 8/25 | 0.9993 | no |

Stop under the stated rule: no
