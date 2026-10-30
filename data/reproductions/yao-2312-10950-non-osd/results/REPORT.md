# Non-OSD Yao reproduction assessment

Source: [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2).
Local two-sided 95% intervals invert the negative-binomial distribution for runs stopped at a fixed failure count, or use Clopper–Pearson bounds for fixed/capped shot runs. Zero-failure triangles mark the exact one-sided 95% upper bound, about 3/N. Source points are published rates; their exact trial counts are not available from the plotted coordinates. Interval inclusion is a descriptive compatibility check, not a formal equivalence claim.

## Coverage

- external_source_only: 10
- interrupted_prefix_contains_source: 1
- local_95_contains_source: 65
- local_95_excludes_source: 7
- low_count_unresolved: 14
- pending: 62
- pilot_only: 5

## Principal curve points

B1 T=10 uses Figure 3 below; Figure 4's conflicting T=10 targets remain separate in the CSV.

| Code | p | Source plain BP | Local plain BP | Source guided T=10 | Local guided T=10 |
|---|---:|---:|---:|---:|---:|
| B1 | 0.04 | 0.0434 | 100/2267 (0.04411) | 6e-06 | — |
| B1 | 0.05 | 0.0867 | 100/1226 (0.08157) | 0.000179 | 2/10000 (0.0002) |
| B1 | 0.06 | 0.1449 | 436/3000 (0.1453) | 0.003891 | 10/2000 (0.005) |
| B1 | 0.07 | 0.2505 | 100/407 (0.2457) | 0.038801 | 100/2485 (0.04024) |
| B1 | 0.08 | 0.4448 | 100/244 (0.4098) | 0.21694 | 100/438 (0.2283) |
| B1 | 0.09 | 0.7141 | 100/132 (0.7576) | 0.59538 | 100/177 (0.565) |
| B1 | 0.10 | 0.9139 | 100/107 (0.9346) | 0.86325 | 100/117 (0.8547) |
| C2 | 0.04 | 0.080058 | 100/1052 (0.09506) | 0.000144 | — |
| C2 | 0.05 | 0.15758 | 100/694 (0.1441) | 0.00085 | — |
| C2 | 0.06 | 0.26847 | 779/3000 (0.2597) | 0.0058 | 9/2000 (0.0045) |
| C2 | 0.07 | 0.4004 | 100/253 (0.3953) | 0.035 | 73/2000 (0.0365) |
| C2 | 0.08 | 0.63699 | 100/160 (0.625) | 0.209 | 36/200 (0.18) |
| C2 | 0.09 | 0.87228 | 100/116 (0.8621) | 0.628 | 86/150 (0.5733) |
| C2 | 0.10 | 0.98328 | 100/102 (0.9804) | 0.925 | 91/100 (0.91) |
| A5 | 0.04 | 0.000236 | 130/529662 (0.0002454) | 5.8e-05 | 1/5000 (0.0002) |
| A5 | 0.05 | 0.000876 | 113/142695 (0.0007919) | 0.000295 | 2/5000 (0.0004) |
| A5 | 0.06 | 0.003159 | 131/39570 (0.003311) | 0.001608 | 5/3000 (0.001667) |
| A5 | 0.07 | 0.011972 | 144/10442 (0.01379) | 0.00614 | 37/5000 (0.0074) |
| A5 | 0.08 | 0.039651 | 131/3153 (0.04155) | 0.02159 | 100/4740 (0.0211) |
| A5 | 0.09 | 0.093809 | 110/1333 (0.08252) | 0.055219 | 100/1718 (0.05821) |
| A5 | 0.10 | 0.1443 | 147/867 (0.1696) | 0.12423 | 100/749 (0.1335) |
| B2 | 0.04 | 0.000406 | 92/307882 (0.0002988) | 8.4e-05 | 0/5000 (0) |
| B2 | 0.05 | 0.001265 | 89/98815 (0.0009007) | 0.00021 | 0/5000 (0) |
| B2 | 0.06 | 0.002569 | 110/48658 (0.002261) | 0.000455 | 1/5000 (0.0002) |
| B2 | 0.07 | 0.006755 | 129/18505 (0.006971) | 0.000905 | 4/5000 (0.0008) |
| B2 | 0.08 | 0.015077 | 101/8291 (0.01218) | 0.001895 | 11/5000 (0.0022) |
| B2 | 0.09 | 0.02978 | 101/4198 (0.02406) | 0.004651 | 22/5000 (0.0044) |
| B2 | 0.10 | 0.060326 | 100/2073 (0.04824) | 0.009561 | 50/5000 (0.01) |

## Representative p=0.06 points

| Figure | Code | Decoder | Source | Local failures/shots | Local 95% interval | Assessment |
|---:|---|---|---:|---:|---:|---|
| 3 | B1 | bp | 0.1449 | 436/3000 | [0.13291, 0.15846] | local_95_contains_source |
| 3 | B1 | bpgd_t10 | 0.003891 | 10/2000 | [0.0024002, 0.0091759] | low_count_unresolved |
| 5 | C2 | bp | 0.268469 | 779/3000 | [0.24405, 0.27575] | local_95_contains_source |
| 5 | C2 | bpgd_t10 | 0.0058 | 9/2000 | [0.0020597, 0.0085251] | low_count_unresolved |
| 7 | A5 | bpgd_t10 | 0.001608 | 5/3000 | [0.00054138, 0.0038851] | low_count_unresolved |
| 7 | A5 | qbp | 0.003159 | 131/39570 | [0.0027687, 0.0039273] | local_95_contains_source |
| 8 | B2 | bpgd_t10 | 0.000455 | 1/5000 | [5.0635e-06, 0.0011138] | low_count_unresolved |
| 8 | B2 | qbp | 0.002569 | 110/48658 | [0.0018584, 0.0027241] | local_95_contains_source |

## Points outside the local 95% interval

These are point-versus-interval flags, not formal two-sample discrepancy tests; the published estimates also have Monte Carlo uncertainty. Figures repeating the same result are shown once.

| Figure | Code | Decoder | p | Published | Local failures/shots (rate) | Local 95% interval |
|---:|---|---|---:|---:|---:|---:|
| 3 | B1 | bpgd_t1 | 0.06 | 0.00606 | 100/12358 (0.00809192) | [0.00658862, 0.00974539] |
| 7 | A5 | qbp | 0.10 | 0.1443 | 147/867 (0.16955) | [0.145153, 0.196216] |
| 8 | B2 | qbp | 0.04 | 0.000406 | 92/307882 (0.000298816) | [0.000240894, 0.000366459] |
| 8 | B2 | qbp | 0.05 | 0.001265 | 89/98815 (0.000900673) | [0.000723375, 0.00110824] |
| 8 | B2 | qbp | 0.08 | 0.015077 | 101/8291 (0.0121819) | [0.009933, 0.0147827] |
| 8 | B2 | qbp | 0.09 | 0.02978 | 101/4198 (0.0240591) | [0.0196382, 0.029158] |
| 8 | B2 | qbp | 0.10 | 0.060326 | 100/2073 (0.0482393) | [0.039419, 0.0583632] |

At B1 T=1, p=0.06, the local 100/12,358 estimate excludes the plotted 0.00606 point. Figure 3 says its points were also collected to 100 failures; approximating that source run as 100/16,502 gives a 95% interval that overlaps the local interval. This is a reproducibility lead, not evidence of a specific kernel error.

## Table 1: decimated variables

The paper specifies different T values in its prose and caption. The executed T=10 mean is shown separately.

| p | Source mean | Source shots | Local T=10 mean ± SE | Local shots |
|---:|---:|---:|---:|---:|
| 0.05 | 2.91 | 1,000,000 | 3.038 ± 0.167 | 10000 |
| 0.06 | 9.82 | 100,000 | 10.907 ± 1.558 | 2000 |
| 0.07 | 60.46 | 100,000 | 55.118 ± 3.802 | 2485 |
| 0.08 | 231.70 | 10,000 | 225.689 ± 17.707 | 438 |

At B1 p=0.08, 96 of 100 local guided failures are syndrome-inconsistent (Type I), while 4 are logical (Type II). This is consistent with the paper's statement that over 90% of these failures are non-convergence cases.

C2 p=0.07 used a recovered 2000-shot prefix: 12 Type I and 61 Type II failures. This breakdown refers only to the retained prefix.

## Table 2: fixed-error randomized decimation

The published 9,568/10,000 convergences and 111 distinct convergent corrections depend on fixed error bytes that were not released. The paper uses T=10, p=0.08, and top-gap randomization with gap 1.0. The following runs use newly seeded weight-73 errors and are not direct numerical comparisons.

| Local surrogate | Error selection | Trials | Converged | Distinct valid corrections | Distinct all candidates | Type I | Type II |
|---|---|---:|---:|---:|---:|---:|---:|
| table2-easy-surrogate-v2-seed20261031-n20 | first_weight73 | 20 | 20 | 1 | 1 | 0 | 0 |
| table2-hard-surrogate-seed20261031-n100 | first_BP_nonconvergent_weight73 | 100 | 0 | 0 | 100 | 100 | 0 |

## Source and scope notes

- Coverage counts plotted figure coordinates; identical BP rates repeated in several figures count more than once.
- Figures 3 and 4 publish different values for the nominally identical B1 T=10 curve. Both are retained as separate targets.
- Table 1's prose says T=10; its caption says T=100. The local fixations are reported under the actual executed T.
- Table 2's fixed error bytes were not published; its exact 10,000-run result cannot be reproduced from the source artifact.
- A superseded Table 2 smoke run remains on disk but is omitted from the table because its historical script bytes were not retained. The two displayed surrogates bind the current script hash.
- BP-SI points in Figures 4 and 5 were imported from [du Crest, Mhalla, and Savin](https://arxiv.org/abs/2205.06125). They use serial normalized min-sum (α=0.9), stabilizer inactivation, and a small linear solve; Yao et al. did not generate those shots. They are source-mapped here as a separate reproduction target. BP-OSD is excluded.
- Plain QBP v2 counts are imported from the earlier vanilla campaign, not rerun here. Its archive hash matches this source, but its recorded main.tex hash has a transcription error; this study records the independently verified TeX hash. The earlier count ledgers were not revalidated by this assessor.
- The new binary path is a compiled interpretation of the paper's V2C clipping and decimation pseudocode. The A5/B2 Q-BPGD path uses the existing compiled BP4 v2 kernel; these are canonical adaptations.
- All local results include Type I and Type II block failures. A correction differing from the sampled error by a stabilizer counts as success.
- Reaching 100 failures at the source B1 T=100, p=0.04 rate of 10⁻⁶ requires about 100 million shots in expectation; B1 T=10 at p=0.04 requires about 16.7 million. The bounded development campaigns do not resolve those rare-event points.

The complete point table is [comparison.csv](comparison.csv); plots are [comparison.png](comparison.png) and [comparison.pdf](comparison.pdf).
