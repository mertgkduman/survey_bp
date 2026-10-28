# BP4 p=.06 followup stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p006_t5000`; B2: `sp_f64_v2_d01_p006_t1000`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p006_t5000`, 53/50000 = 0.00106; 90% CI [0.000832489, 0.00133239].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p006_t10000 | 45/50000 | 8/0 | 0.003906 | yes |
| sp_f64_v2_d03_p006_t5000 | 50/50000 | 13/10 | 0.3388 | no |
| sp_f64_v2_d02_p006_t5000 | 52/50000 | 13/12 | 0.5 | no |
| sp_f64_v2_d02_p0075_t5000 | 60/50000 | 11/18 | 0.932 | no |
| sp_f64_v2_d01_p0075_t5000 | 64/50000 | 3/14 | 0.9988 | no |

Stop under the stated rule: no

## B2

Incumbent: `sp_f64_v2_d01_p006_t1000`, 25/50000 = 0.0005; 90% CI [0.000347666, 0.000698252].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p012_t1000 | 19/50000 | 12/6 | 0.1189 | no |
| sp_f64_v2_d01_p006_t5000 | 20/50000 | 5/0 | 0.03125 | yes |
| sp_f64_v2_d01_p015_t2000 | 20/50000 | 13/8 | 0.1917 | no |
| sp_f64_v2_d01_p006_t2000 | 23/50000 | 2/0 | 0.25 | no |
| sp_f64_v2_d01_p015_t1000 | 25/50000 | 13/13 | 0.5775 | no |
| sp_f64_v2_d01_p015_t300 | 33/50000 | 11/19 | 0.9506 | no |
| sp_f64_v2_d02_p006_t1000 | 47/50000 | 8/30 | 0.9999 | no |

Stop under the stated rule: no
