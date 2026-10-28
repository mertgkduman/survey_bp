# BP4 p=.06 a5_d02_neighborhood stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d02_p0005_t10000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d02_p0005_t10000`, 43/100000 = 0.00043; 90% CI [0.000328131, 0.000554455].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d02_p0001_t10000 | 37/100000 | 12/6 | 0.1189 | no |
| sp_f64_v2_d025_p0005_t10000 | 37/100000 | 12/6 | 0.1189 | no |
| sp_f64_v2_d02_p001_t10000 | 39/100000 | 13/9 | 0.2617 | no |
| sp_f64_v2_d04_p0005_t10000 | 39/100000 | 14/10 | 0.2706 | no |
| sp_f64_v2_d02_p0005_t20000 | 39/100000 | 4/0 | 0.0625 | yes |
| sp_f64_v2_d03_p0005_t10000 | 40/100000 | 13/10 | 0.3388 | no |
| sp_f64_v2_d02_p0002_t10000 | 42/100000 | 8/7 | 0.5 | no |
| sp_f64_v2_d02_p0003_t10000 | 45/100000 | 7/9 | 0.7728 | no |
| sp_f64_v2_d02_p00075_t10000 | 46/100000 | 10/13 | 0.7976 | no |

Stop under the stated rule: no
