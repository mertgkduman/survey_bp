# BP4 min-sum with both numerical changes: full source-point check

All nine reported vanilla BP4 MS `(code,p)` positions were run with 10,000
shots each, using the existing full-v2 point seed and `p0=p`. The hybrid
retains Q8 scalar commutation and check messages at scale 16, while
keeping the three identity-referenced V2C coordinates unbounded and
forming the complete log-sum-exp difference before scalar quantization.
It is not the source's proven Q8 implementation. Its explicit policy
is in `../../decoders/bp4_ms_both_changes_diagnostic.json`.

Every new per-shot ledger SHA-256, shot sequence, outcome partition,
failure count, and confidence interval was independently checked.
Each error hash matched the corresponding original Q8 run's prefix.

| Code | p | Reference LER | Hybrid failures/N | Hybrid LER [exact 95% CI] | Reference inside CI? | Original Q8 failures/10k | Rescues/losses | Mean iterations |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| b1 | 0.060 | 0.01063 | 109/10000 | 0.0109 [0.00896, 0.0131] | yes | 1910/10000 | 1875/74 | 25.92 |
| b1 | 0.080 | 0.00995 | 110/10000 | 0.011 [0.00905, 0.0132] | yes | 5104/10000 | 5033/39 | 36.18 |
| b1 | 0.100 | 0.0079 | 87/10000 | 0.0087 [0.00697, 0.0107] | yes | 8622/10000 | 8549/14 | 51.96 |
| b1 | 0.120 | 0.0931 | 963/10000 | 0.0963 [0.0906, 0.102] | yes | 9886/10000 | 8923/0 | 185.24 |
| b1 | 0.140 | 0.581 | 5840/10000 | 0.584 [0.574, 0.594] | yes | 9993/10000 | 4153/0 | 667.20 |
| double_gross | 0.060 | 0.00245 | 35/10000 | 0.0035 [0.00244, 0.00486] | yes | 652/10000 | 638/21 | 12.15 |
| double_gross | 0.080 | 0.00525 | 50/10000 | 0.005 [0.00371, 0.00659] | yes | 2153/10000 | 2118/15 | 20.92 |
| double_gross | 0.100 | 0.0427 | 435/10000 | 0.0435 [0.0396, 0.0477] | yes | 5102/10000 | 4673/6 | 76.85 |
| double_gross | 0.120 | 0.21935 | 2173/10000 | 0.2173 [0.209, 0.226] | yes | 7872/10000 | 5703/4 | 273.90 |

## Independent low-p holdout

The weakest 10,000-shot comparison, double-Gross p=.06, was checked
on 50,000 independent errors (seed 20261230). The hybrid had
154/50,000 failures = 0.00308, with an exact
95% interval [0.0026133, 0.0036057].
The reference point estimate 0.00245 is below this
local interval. This leaves a residual low-p discrepancy despite the
strong overall improvement. The source's own sampling uncertainty is
unknown, so this does not establish a formal two-sample difference.

The source denominators are unknown. Inclusion in a local interval
is a descriptive proximity check, not a formal two-sample test.
A zero observed rate is not a zero true rate. This hybrid changes the
internal numerical policy and should not be labeled source-faithful Q8.
