# Research and frozen decisions

## Completed MacKay check

Final arrays 61703094–61703096 and collector 61703097 completed 0:0.
All 30 points, 6,403,005 retained shots and 600 quantum block failures are
verified. All 29 previously published records are unchanged; the final .010
summary matches its audited receipt. The .010 and .013 source ordinates are
above local pointwise 95% intervals; .020/.030/.040 lie within their intervals.
The full curve is not a confirmed reproduction. Exact source iteration/numerical
conventions remain unresolved; tuning cannot retroactively change this evidence.

## Damping scope and objective

Apply to ordinary binary SP and joint Q-BP SP on both MacKay codes. Keep the
unicycle two-hypothesis decoder as its own source reference. Retain the five
source/matched-marginal rates, 88,200 iterations, float64-v2, matched priors and
uncapped checks. The old-message damping grid is 0/.1/.3/.5/.7/.85/.95. At every
rate, settings share 1,024 fixed physical samples; there are 140 tuning points.
One setting is chosen per code/family across the full rate curve.

Primary score: equally weighted mean block LER across the five rates. The
reference minimizes empirical LER (exact-score ties use ascending damping).
Speed candidates must have a simultaneous paired risk-regret upper bound no
larger than 10% of reference empirical LER. Separate exact binomial bounds on
positive and negative discordance at each rate give a conservative risk-difference
bound. Bonferroni covers all ordered pairs, rates, groups and tails, including
a data-selected reference. Secondary score is mean actual iterations. A zero
empirical reference risk has zero similarity margin. Overlapping confidence
intervals never establish equivalence. Selection remains provisional.

Confirmation uses an independent seed and both selected and original settings
(binary 0/Q-BP .1). Identical settings are run only once. Every rate stops at
20 quantum block failures or 100 million shots. Keep per-point uncertainty,
mean actual sweeps, both-directed-edge updates and all outcomes. No tuning
samples are pooled into holdout data; holdout summaries do not automatically
claim superiority. At most 16 tuning CPUs or 32 confirmation CPUs execute.

## Early BP-OSD paper selection

Selected **Roffe, White, Burton and Campbell (2020), Decoding Across the Quantum
LDPC Code Landscape**, arXiv:2005.07016v2, Phys. Rev. Research 2, 043423.
Primary sources: https://arxiv.org/html/2005.07016v2 and
https://arxiv.org/src/2005.07016v2; author repository
https://github.com/quantumgizmos/bp_osd. The paper credits the original 2019
Panteleev–Kalachev BP-OSD proposal (https://arxiv.org/abs/1904.02703).
The latter's inspected v3 uses quaternary normalized min-sum 0.625, layered
scheduling and 32 iterations. Roffe gives a direct regular-BP curve and a
fully explicit flooding min-sum pseudocode that our existing sweeps can execute.
This is an early BP-OSD study, not a claim that Roffe invented BP-OSD.

| Setting | Frozen choice / primary evidence |
| --- | --- |
| Baseline | Figure 3 dashed regular BP curves, no OSD |
| Codes | Toric [[162,2,9]], [[242,2,11]], [[338,2,13]], [[450,2,15]] |
| Construction | Source Eq. (4) symmetric HGP of ring repetition checks; redundant checks retained |
| Updates | Appendix C Algorithm 1, flooding min-sum, alpha_t=1-2^-t from t=1 |
| Iteration cap | Section V: T=n for each code (162/242/338/450) |
| Rates | Source vector figure's measured dashed vertices, checked against vertical error bars; 25/28/28/28 rates |
| Baseline noise | Section VI: binary X-only p, one species of symmetric independent X/Z problem |
| Q-BP | Additional joint min-sum using same alpha schedule and T=n; depolarizing p=1.5*p_X, separate controlled channel |
| Stopping | 20 block failures or 100 million shots, fresh seed 2026111311 |
| Outcome | Original-code syndrome validity and both logical signatures, Type I/II failure; not per-logical-qubit probability |
| Numerical scope | float64 canonical policies, MAP Pauli for Q-BP; exact author numerics and row ordering unavailable |

The original PGF provides measured coordinates, not a visually estimated regular
grid. Distances have different irregular grids near .10; there are 109 binary
points plus 109 Q-BP points. Figure/archive hashes and extraction calibration
are retained. No omitted coordinate is interpolated. Source ordinates are
approximate vector values; raw author sample counts are unavailable.

The variable-alpha controller only dispatches existing canonical public sweeps;
it implements no new check or variable-message equation. An independent direct
implementation of Algorithm 1 agrees on tested trajectories. Float64 alpha
rounds to one at t=54, so at most 54 immutable graph policies are cached.
Source-specific saved decoders stay on their original execution path and cannot
silently become constant-scale builder decoders. Public curve identity includes
the scale schedule and first source iteration, independently of concise labels.

## Preservation and sequencing

No canonical-kernel file, legacy frozen plan/runner/result, or archived v1 file
is changed. New code inputs stay hidden until eligible multi-rate results exist.
New catalogs are registered empty and consume only audited confirmation/paper
results. Raw tuning is retained separately. All future rebuilds use the existing
shared retirement/validity/projection/two-rate filter.

Freeze Roffe and tuning source/implementation/artifact/software identities before
submission. Successful tuning audit freezes selection and confirmation before
sampling. Successful confirmation audit publishes its results and submits the
already-frozen Roffe array. Failed/missing evidence stops advancement. Submission
locks and persistent receipts prevent duplicate arrays. Automatic refresh saves
a new catalog separately when the workbench has local edits.
