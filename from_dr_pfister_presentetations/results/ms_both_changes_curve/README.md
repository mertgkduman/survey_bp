# BP4 min-sum both-changes curve check

This exploratory campaign reruns the nine reported vanilla BP4 min-sum
`(code,p)` points with the `both_changes` diagnostic arm from
`inspect_q8_minsum_clipping.py`. The arm retains Q8 scalar projected and
check messages at scale 16 but uses unbounded float64 three-coordinate V2C
and forms the full commuting-minus-anticommuting log-sum-exp difference
before quantizing the scalar. It is a hybrid numerical policy; agreement
with source values does not establish that the source used these internals.
The complete policy is recorded in
`../../decoders/bp4_ms_both_changes_diagnostic.json`.

- Physical noise: code-capacity depolarizing, `p0=p`, perfect syndrome.
- MS check: unscaled, unoffset; flooding; V2C damping zero.
- Stop: first syndrome match or `T=1000`. Every shot remains in the
  denominator; the independent evaluator counts both syndrome misses and
  syndrome-consistent logical failures.
- Shots: 10,000 per source MS point, selected before observing these results.
- Sampler: NumPy PCG64, with the same per-point seed and error stream as the
  existing `full_v2_curves` campaign. Per-shot SHA-256 values are compared
  during analysis.
- Environment: Python 3.12.2, NumPy 2.2.6, SciPy 1.17.1, Numba 0.64.0.
- Jobs: Slurm array `60240869` for the nine points; B1 `p=.14` task 4 was
  canceled for throughput before emitting a result and replaced by the five
  contiguous 2,000-shot shards in array `60241649`. The interruption record
  is retained in `b1_p0140_interrupted_unsharded/`.
- Per-point folders hold an independently evaluable `summary.json` and
  compressed per-shot `events.jsonl.gz`, with uncompressed ledger SHA-256.
  `b1_p0140/` is produced by validating and concatenating the five shards.
- `analyze_ms_both_changes_curve.py` audits all nine ledgers and compares
  each 10,000-shot prefix with the original Q8 arm on identical errors.
- An independent 50,000-shot holdout at double-Gross `p=.06` uses seed
  `20261230` and is audited by the same analyzer. It probes the weakest
  pointwise match without reusing its original sampled errors.

The source denominators are unknown, so its reported rates are compared
descriptively against exact local binomial intervals. The completed analysis
is in `REPORT.md`, `comparison.csv`, `analysis.json`, and the PNG/PDF
`curve_comparison` plots. All nine 10,000-shot
intervals include the reference point, but the independent double-Gross
`p=.06` holdout interval excludes its reported point estimate. The source's
own uncertainty cannot be calculated from the excerpt.
