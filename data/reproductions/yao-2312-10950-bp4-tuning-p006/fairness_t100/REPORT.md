# BP4 fairness comparison at physical p=0.06

The previously quoted approximately 7.5–7.7× tuned-versus-untuned ratios
combined parameter and iteration-cap changes on independent shot sets; they
were not equal-budget comparisons. This fresh fixed-shot evaluation makes two
paired comparisons on each
code: **equal cap T=100**, and **approximately equal mean iterations**.
Each code has 100,000 shared physical errors across its four arms. Exact and
stabilizer-equivalent corrections count as successes; Type I syndrome mismatch
and Type II logical failure count as block failures.

The kernel is compiled canonical BP4 float64 v2 flooding sum-product in every
arm. Untuned uses decoder prior p0=0.06, outgoing V2C damping d=0, no check cap,
and check-product epsilon 1e-10. The tuned prior/damping were selected in the
preceding study; only the cap is truncated to 100 in the equal-cap arm.

## A5

| Arm | p0 | d | T | Type I / II | Failures / N | LER (exact 90% CI) | Mean iterations | Mean ms/decode |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Untuned, T=100 | 0.06 | 0 | 100 | 393 / 0 | 393 / 100,000 | 0.00393 [0.00361026, 0.00427135] | 4.006 | 1.964 |
| Selected parameters, T=100 | 0.005 | 0.2 | 100 | 186 / 0 | 186 / 100,000 | 0.00186 [0.00164167, 0.00210022] | 3.887 | 1.755 |
| Untuned, T=3,000 | 0.06 | 0 | 3,000 | 178 / 0 | 178 / 100,000 | 0.00178 [0.00156654, 0.00201537] | 10.249 | 3.648 |
| Selected parameters and cap | 0.005 | 0.2 | 10,000 | 42 / 0 | 42 / 100,000 | 0.00042 [0.000319396, 0.000543206] | 9.381 | 3.295 |

| Paired comparison | Untuned/tuned failures | Rate ratio | Rescues/losses | p(tuned better) | Two-sided p |
|---|---:|---:|---:|---:|---:|
| Equal T=100 | 393/186 | 2.11× | 224/17 | 1.51e-47 | 3.01e-47 |
| Pilot-calibrated mean work | 178/42 | 4.24× | 140/4 | 7.93e-37 | 1.59e-36 |

The work-control cap was frozen at T=3,000 from a separate 20,000-shot
pilot. Its pilot mean was 9.293
versus the selected policy's earlier 100,000-shot target 9.208. On the fresh
evaluation, untuned averaged 10.249 and tuned averaged
9.381 iterations (+9.3% untuned relative to tuned).

## B2

| Arm | p0 | d | T | Type I / II | Failures / N | LER (exact 90% CI) | Mean iterations | Mean ms/decode |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Untuned, T=100 | 0.06 | 0 | 100 | 255 / 0 | 255 / 100,000 | 0.00255 [0.00229343, 0.00282834] | 5.779 | 10.025 |
| Selected parameters, T=100 | 0.15 | 0.1 | 100 | 100 / 0 | 100 / 100,000 | 0.001 [0.000841455, 0.00118069] | 5.117 | 10.025 |
| Untuned, T=2,400 | 0.06 | 0 | 2,400 | 27 / 0 | 27 / 100,000 | 0.00027 [0.000190588, 0.000372323] | 6.803 | 11.253 |
| Selected parameters and cap | 0.15 | 0.1 | 5,000 | 32 / 4 | 36 / 100,000 | 0.00036 [0.000267323, 0.00047538] | 6.974 | 11.540 |

| Paired comparison | Untuned/tuned failures | Rate ratio | Rescues/losses | p(tuned better) | Two-sided p |
|---|---:|---:|---:|---:|---:|
| Equal T=100 | 255/100 | 2.55× | 197/42 | 1.73e-25 | 3.46e-25 |
| Pilot-calibrated mean work | 27/36 | 0.75× | 14/23 | 0.951 | 0.188 |

The work-control cap was frozen at T=2,400 from a separate 20,000-shot
pilot. Its pilot mean was 6.846
versus the selected policy's earlier 100,000-shot target 6.743. On the fresh
evaluation, untuned averaged 6.803 and tuned averaged
6.974 iterations (-2.4% untuned relative to tuned).

At approximately equal mean work, the B2 point estimate favors
untuned BP4. The two-sided paired difference is unresolved at 90% confidence (exact p=0.188). A one-sided test in the observed untuned direction gives p=0.0939; that direction was not prespecified for this comparison.

## Interpretation and provenance

Equal T=100 controls the iteration cap; measured mean work can still differ
because the policies converge on different shots. The work control uses
mean completed iterations as the common unit on the same Tanner graph.
Wall time is listed separately and varies across HPC nodes; damping can
also change per-iteration arithmetic. The pilot chose caps without using
evaluation outcomes, and the tuning study chose priors/damping before this
fresh evaluation seed. These settings were optimized at longer caps, so
the T=100 arm is a cap-truncation control, not a new T=100 optimization.

All per-shot event ledgers, manifests, counts, source/policy hashes, and
sample-stream pairing passed [`analyze.py`](analyze.py). The fixed plans
and machine-readable results are in this folder. Raw ledgers remain on
the HPC filesystem and are excluded from Git; manifests and summaries
retain their SHA-256 digests. The [interval plot](comparison.pdf) shows
the four arms on each code.
