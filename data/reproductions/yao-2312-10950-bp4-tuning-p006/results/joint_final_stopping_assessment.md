# BP4 p=.06 joint_final stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p006_t10000`; B2: `sp_f64_v2_d01_p015_t5000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p006_t10000`, 60/60000 = 0.001; 90% CI [0.000797613, 0.00123968].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p0045_t10000 | 53/60000 | 12/5 | 0.07173 | yes |
| sp_f64_v2_d02_p006_t10000 | 63/60000 | 12/15 | 0.779 | no |
| sp_f64_v2_d03_p006_t10000 | 63/60000 | 12/15 | 0.779 | no |
| sp_f64_v2_d01_p0075_t10000 | 83/60000 | 4/27 | 1 | no |

Stop under the stated rule: no

## B2

Incumbent: `sp_f64_v2_d01_p015_t5000`, 22/60000 = 0.000366667; 90% CI [0.000248242, 0.000523539].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p016_t5000 | 16/60000 | 7/1 | 0.03516 | yes |
| sp_f64_v2_d01_p014_t5000 | 17/60000 | 7/2 | 0.08984 | yes |
| sp_f64_v2_d005_p015_t5000 | 19/60000 | 5/2 | 0.2266 | no |
| sp_f64_v2_d015_p015_t5000 | 19/60000 | 6/3 | 0.2539 | no |
| sp_f64_v2_d01_p018_t5000 | 20/60000 | 8/6 | 0.3953 | no |
| sp_f64_v2_d02_p015_t5000 | 23/60000 | 5/6 | 0.7256 | no |

Stop under the stated rule: no
