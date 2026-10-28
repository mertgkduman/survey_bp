# BP4 tuning at physical depolarizing rate p = 0.06

## Selected policies

The selected policies use the compiled canonical BP4 float64 v2 flooding
sum-product kernel. Both use outgoing variable-to-check damping
`m_new = d*m_old + (1-d)*m_proposed`, no check-message cap, check-product
epsilon `1e-10`, and first syndrome-matching candidate stopping. `p0` is the
decoder's depolarizing prior; the physical sampler remains at `p=0.06`.

| Code | Decoder file | `p0` | `d` | `T` | Failures / shots | Block failure rate (exact 90% CI) | Type I / II | Mean iterations |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A5 `[[180,10]]` | [`a5_tuned.json`](../decoders/a5_tuned.json) | 0.005 | 0.2 | 10,000 | 43 / 100,000 | 0.000430 [0.000328, 0.000554] | 42 / 1 | 9.21 |
| B2 `[[882,48]]` | [`b2_tuned.json`](../decoders/b2_tuned.json) | 0.15 | 0.1 | 5,000 | 30 / 100,000 | 0.000300 [0.000216, 0.000407] | 26 / 4 | 6.74 |

These are separate fresh-seed fixed-shot estimates for each selected policy.
Type I is a syndrome mismatch; Type II is a syndrome-consistent logical
failure. Exact and stabilizer-equivalent corrections count as successes.
Elapsed per-decode times are in the stage CSV files; they depend on the HPC
node and are less portable than the iteration counts.

## Search and stopping evidence

The exploratory [screen](screen_report.md) used a matched prefix ending at
only six baseline block failures per code: A5 `N=1,148`, B2 `N=1,460`.
Because the prefix length depends on baseline failures, its rates were used
for ranking only. A fresh [refinement](refine_report.md) and
[50,000-shot holdout](validate_report.md) identified damping, prior, and cap
effects. The holdout did not satisfy the stopping rule, so the subsequent
stage plans and their full ledgers are retained. Every fixed-shot stage was
audited against its frozen policy registry, source hashes, manifest and event
digests, shot counts, and reconstructed shared PCG64 error stream. Across
all stages, 257 candidate tasks and 8,904,576 decoder shots completed.

**A5.** Lowering `p0` from 0.06 to 0.03 and then to 0.005 produced resolved
paired improvements in the [prior](a5_prior_report.md) and
[lower-prior](a5_low_prior_report.md) stages. A fresh
[tiny-prior bracket](a5_tiny_prior_report.md) found 47/100,000 at `p0=0.005`;
all tested priors from 0.0005 through 0.01 stayed within its exact 90% CI,
and none improved it by the one-sided paired 90% rule. At `p0=0.005`, the
[damping/cap check](a5_final_neighborhood_report.md) found `d=0.2` at
41/100,000 versus `d=0.1` at 59/100,000 on the same errors: 19 rescues, one
loss, exact one-sided paired `p=2.00e-5`. The final fresh
[d=0.2 neighborhood](a5_d02_neighborhood_report.md) yielded 43/100,000 for
the incumbent. The closest `p0=0.001` and `d=0.25` variants each yielded
37/100,000, but each had 12 rescues and 6 losses (`p=0.119`); neither moved
the point estimate below the incumbent's 90% CI lower limit. All other
tested prior and damping neighbors also failed the stated improvement rule.
The [A5 decision receipt](a5_final_selection_assessment.md) records this
finite-neighborhood conclusion.

Increasing A5's cap from 10,000 to 20,000 at the selected `p0,d` rescued
four of 100,000 shots with zero losses and raised mean work from 9.21 to
13.12 iterations. The exact one-sided 90% upper bound on additional rescue
probability is `7.99e-5`, below the selected policy's rate-minus-lower-CI
margin of `1.02e-4`; the 20,000-cap rate stays inside that interval. Under
the [prespecified practical cap rule](a5_d02_neighborhood_pairwise.md),
10,000 is the stopping choice despite the paired `p=0.0625` for the four
late rescues. A 5,000 cap had 70/100,000 failures in the preceding matched
stage, so it is too short for this policy.

**B2.** The initial [cap/prior study](sweet_b2_report.md) favored priors near
0.15. A [joint interaction check](joint_final_report.md) gave `p0=0.16` a
small apparent edge, so a new [100,000-shot confirmation](b2_prior_confirm_report.md)
was frozen. That independent run reversed the ordering: `p0=0.15` had
30/100,000 versus 39/100,000 at 0.16, with 15 rescues and 6 losses for 0.15
(`p=0.0392`). The [reselection assessment](b2_reselection_assessment.md)
shows that 0.14, 0.16, and 0.17 did not improve on 0.15 in paired tests.
Earlier local damping variants at the same cap had no resolved improvement.
At `p0=0.15`, raising the cap from 5,000 to 10,000 or 20,000 rescued only
two of 80,000 paired shots. The exact one-sided 90% rescue upper bound,
`6.65e-5`, is below the 5,000-cap point-to-lower-CI margin `9.73e-5`;
the [paired cap table](sweet_b2_pairwise.md) records both as practically
saturated. The chosen 5,000 cap has lower mean work.

## Interpretation and replay

The exact intervals describe fixed-shot uncertainty for the displayed
policies. Paired McNemar p-values are unadjusted after sequential policy
search; the finite-neighborhood stopping decision is **not** evidence of a
global optimum or of equal true rates among close settings. No settings
were tested here at physical rates other than 0.06. The very small A5 prior
and elevated B2 prior are empirical decoder choices, not changes to the
physical channel.

The [study README](../README.md) explains the policy files, stage plans,
replay commands, and ledger audit. PNG and PDF interval plots sit alongside
each stage report, including
[A5](a5_d02_neighborhood_intervals.pdf) and
[B2](b2_prior_confirm_intervals.pdf). Raw per-shot ledgers are retained on
the HPC filesystem and excluded from Git because of size; tracked manifests
and summaries retain their SHA-256 digests. One screen/refinement task hit a
transient shared Numba-cache I/O error and was rerun unchanged with a
node-local cache; its completed ledger passed the same audit.
