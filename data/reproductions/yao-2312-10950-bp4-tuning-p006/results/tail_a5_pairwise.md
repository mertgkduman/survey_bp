# A5 long-cap paired comparisons

Positive rescues mean the right candidate corrected a failure of the left.
P-values are one-sided exact McNemar tests and unadjusted for multiple comparisons.
For cap-only increases, saturation requires the exact one-sided 90% upper bound
on rescue rate to fit inside the left candidate's exact two-sided 90% LER interval.

| Left | Right | Failures left/right | Rescues/losses | p(right better) | Rescue upper 90% | Cap saturated? |
|---|---|---:|---:|---:|---:|---:|
| sp_f64_v2_d01_p006_t10000 | sp_f64_v2_d01_p006_t20000 | 47/46 | 1/0 | 0.5 | 7.7792e-05 | yes |
| sp_f64_v2_d01_p006_t10000 | sp_f64_v2_d01_p006_t50000 | 47/45 | 2/0 | 0.25 | 0.00010644 | yes |
| sp_f64_v2_d01_p006_t20000 | sp_f64_v2_d01_p006_t50000 | 46/45 | 1/0 | 0.5 | 7.7792e-05 | yes |
