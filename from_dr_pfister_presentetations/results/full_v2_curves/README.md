# Full v2 presentation-curve campaign

This campaign covers all 12 distinct `(code, physical p)` points and the 41
plotted source values in `../source_curves.csv`. The local measurements retain
separate identities for float64 canonical v2 adaptations and the existing Q8
policy controls. They are independent, same-error code-capacity experiments,
not copies of presentation values.

## Execution

- Source commit: `6dbeafb` (`spike: prepare full presentation v2 curve campaign`).
- Runner: `../../run_full_v2_curve.py`.
- Slurm array: `60074265`, indices `0-11`, at most six one-CPU jobs at once.
- Dependent audit/plot job: `60074272`, `afterok:60074265`.
- Physical sampler: NumPy PCG64; one deterministic error stream per code/p;
  each arm at that point receives the same prefix of sampled errors.
- Decoder prior: `p0=p`; binary marginal prior: `2p/3`.
- Maximum iterations: 1000; first syndrome-matching candidate; no downstream
  OSD or other fallback.
- Failure: missed target syndrome (Type I) or syndrome-consistent logical
  residual (Type II). Stabilizer-equivalent corrections count as successes.
- Per-shot compressed JSONL ledgers include a sampled-error SHA256, outcome,
  iteration/work count, elapsed time, and arm identity. Each point summary
  includes an SHA256 of the uncompressed ledger; `analyze_full_v2_curves.py`
  verifies these plus record counts before producing the final CSV and plot.

## Arms and interpretation

| Local arm | Implementation | Presentation series |
|---|---|---|
| `bp4_vanilla_sp_v2` | Compiled canonical float64 BP4 v2, V2C damping 0 | Vanilla BP4 SP; numerical adaptation because source uses Q8 scale 16 |
| `bp4_tuned_sp_v2` | Compiled canonical float64 BP4 v2, V2C damping 0.1 | Tuned BP4 SP; numerical adaptation because source uses Q8 scale 4 |
| `binary_tuned_spa_v2` | Compiled canonical float64 binary SPA v2, V2C damping 0.1 | Same p positions as tuned binary OMS; **different check rule** |
| `bp4_vanilla_ms_q8` | Existing experimental Q8 BP4 min-sum, scale 16, damping 0 | Vanilla BP4 MS policy control; not a v2 kernel |
| `binary_tuned_oms_q8` | Existing experimental Q8 binary OMS, scale 4, damping 0.1, alpha 1, beta 0.25 | Tuned binary OMS policy control; not a v2 kernel |

The presentation denominator is unknown for all observed points. Its
double-Gross BP4 point at `p=.06` is a one-sided 95% upper bound from zero
failures in 100,000 trials, not an observed rate. The campaign's local
intervals are exact 95% binomial intervals; inclusion of a source estimate
in a local interval is descriptive and is not a two-sample hypothesis test.

## Fixed sample targets

Sample targets were set before execution from a 30-expected-failure target
using each reported source rate, with a floor of 50,000 shots except 20,000
at the highest physical p, and a cap of 10 million. The source zero-failure
bound receives one million local trials. Binary SPA v2 receives the same
sample prefix as the tuned OMS control. All attempted shots stay in the
denominator.

| Code | p | Vanilla BP4 SP/MS | Tuned binary OMS/SPA v2 | Tuned BP4 v2 |
|---|---:|---:|---:|---:|
| B1 | .060 | 50,000 | 1,071,429 | 4,225,353 |
| B1 | .065 | — | 344,828 | 3,571,429 |
| B1 | .080 | 50,000 | 50,000 | 1,224,490 |
| B1 | .100 | 50,000 | 50,000 | 93,750 |
| B1 | .120 | 20,000 | 20,000 | 20,000 |
| B1 | .140 | 20,000 | 20,000 | 20,000 |
| double-Gross | .040 | — | 750,000 | 10,000,000 |
| double-Gross | .050 | — | 95,239 | — |
| double-Gross | .060 | 50,000 | 50,000 | 1,000,000 |
| double-Gross | .080 | 50,000 | 50,000 | 50,000 |
| double-Gross | .100 | 50,000 | 50,000 | 50,000 |
| double-Gross | .120 | 20,000 | 20,000 | 20,000 |

## Outputs

Each `b1_p####` or `double_gross_p####` folder contains `events.jsonl.gz`
and, on completion, `summary.json`. The analyzer writes `comparison.csv`,
`curves.png`, `analysis.json`, and `REPORT.md` after all jobs finish. `logs/` retains Slurm
stdout and stderr. The `smoke_*` and `benchmark_*` directories are preflight
checks and are excluded from campaign analysis.
