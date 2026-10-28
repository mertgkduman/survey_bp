# BP4 p=.06 validate stopping assessment

The code-specific incumbents were frozen in the study plan before this stage's samples:
A5: `sp_f64_v2_d01_p006_t1000`; B2: `sp_f64_v2_d01_p015_t100`.
A tested neighbor triggers more tuning if its observed LER falls below the incumbent's
exact two-sided 90% lower limit, or if its paired one-sided exact McNemar p < 0.10.
This is a finite-neighborhood stopping rule, not proof of equivalence or global optimality.

## A5

Incumbent: `sp_f64_v2_d01_p006_t1000`, 76/50000 = 0.00152; 90% CI [0.00124518, 0.00183929].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d02_p006_t1000 | 71/50000 | 14/9 | 0.2024 | no |
| sp_f64_v2_d01_p006_t2000 | 72/50000 | 4/0 | 0.0625 | yes |
| sp_f64_v2_d03_p0075_t1000 | 80/50000 | 13/17 | 0.8192 | no |
| sp_f64_v2_d05_p006_t100 | 82/50000 | 14/20 | 0.8853 | no |
| sp_f64_v2_d01_p006_t300 | 87/50000 | 0/11 | 1 | no |
| sp_f64_v2_d03_p006_t100 | 87/50000 | 13/24 | 0.9765 | no |
| sp_q8_s4_edge_d02 | 90/50000 | 6/20 | 0.9988 | no |
| sp_f64_v2_d03_p0075_t100 | 98/50000 | 7/29 | 1 | no |
| sp_f64_v2_d0_p006_t100 | 175/50000 | 1/100 | 1 | no |

Stop under the stated rule: no

## B2

Incumbent: `sp_f64_v2_d01_p015_t100`, 48/50000 = 0.00096; 90% CI [0.000744078, 0.00122092].

| Neighbor | Failures/N | Rescues/losses | Paired p | Continue? |
|---|---:|---:|---:|---:|
| sp_f64_v2_d01_p006_t1000 | 24/50000 | 36/12 | 0.0003586 | yes |
| sp_f64_v2_d01_p015_t300 | 25/50000 | 23/0 | 1.192e-07 | yes |
| sp_f64_v2_d01_p006_t300 | 31/50000 | 31/14 | 0.008047 | yes |
| sp_f64_v2_d02_p012_t100 | 41/50000 | 22/15 | 0.162 | no |
| sp_f64_v2_d01_p012_t100 | 49/50000 | 20/21 | 0.6224 | no |
| sp_f64_v2_d01_p018_t100 | 51/50000 | 18/21 | 0.7388 | no |
| sp_f64_v2_d01_p024_t100 | 60/50000 | 18/30 | 0.9703 | no |
| sp_f64_v2_d0_p006_t100 | 137/50000 | 17/106 | 1 | no |
| sp_f64_v2_d01_p030_t100 | 279/50000 | 13/244 | 1 | no |

Stop under the stated rule: no
