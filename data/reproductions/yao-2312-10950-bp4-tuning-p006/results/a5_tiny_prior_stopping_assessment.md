# BP4 p=.06 a5_tiny_prior stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p0005_t10000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p0005_t10000`, 47/100000 = 0.00047; 90% CI [0.000363216, 0.000599316].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p00005_t10000 | 50/100000 | 9/12 | 0.8083 | no |
| sp_f64_v2_d01_p0001_t10000 | 52/100000 | 7/12 | 0.9165 | no |
| sp_f64_v2_d01_p0002_t10000 | 52/100000 | 7/12 | 0.9165 | no |
| sp_f64_v2_d01_p0003_t10000 | 52/100000 | 9/14 | 0.895 | no |
| sp_f64_v2_d01_p00075_t10000 | 52/100000 | 5/10 | 0.9408 | no |
| sp_f64_v2_d01_p001_t10000 | 52/100000 | 9/14 | 0.895 | no |

Stop under the stated rule: yes
