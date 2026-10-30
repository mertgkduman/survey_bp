# Yao BP/BPGD reproduction assessment

Source: [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2).
This comparison contains only BP and BPGD. Direct-run two-sided 95% intervals invert the negative-binomial distribution for runs stopped at a fixed failure count, or use Clopper–Pearson bounds for fixed/capped shot runs. Mixture importance-sampling (IS) intervals are approximate normal intervals using the weighted shot variance and are marked separately. Zero-failure triangles mark the exact one-sided 95% upper bound, about 3/N. Figure captions say source points were collected to 100 errors; approximate source intervals infer N=round(100/plotted rate), because exact denominators were not supplied. Interval overlap is descriptive, not a formal equivalence test.

## Coverage

- importance_preliminary: 13
- interrupted_prefix_contains_source: 1
- local_95_contains_source: 106
- local_95_excludes_source: 16
- low_count_unresolved: 4
- pending: 11
- pilot_only: 3

## Rare-event estimator

For each IS shot, an iid error is drawn from 0.1 P_p + 0.9 P_q with q>p, decoded using the source p, and its failure indicator is weighted by P_p(error)/(0.1 P_p(error)+0.9 P_q(error)). The estimator averages these weighted indicators. The expected value is the ordinary iid error rate at p; the source simulation itself used direct iid shots. The assessor verifies the exact proposal draw and likelihood weight for every retained shot. Extension sizes are chosen from pilot data; the reported estimate uses only the latest independently fixed stage so the pilot does not enter its own adaptively sized follow-up. IS is promoted from preliminary only when that stage is complete, the effective weighted failure count reaches 100, and the approximate 95% relative half-width is at most 25%. This interval does not include uncertainty in the published point.

### IS progress by distinct decoder point

Raw failures are proposal-distribution failures. The effective weighted failure count (ESS) controls precision; an initial pilot with low ESS is not a completed reproduction.

| Code | Decoder | p | Stage | Source | IS rate | Raw failures/shots | Failure ESS |
|---|---|---:|---:|---:|---:|---:|---:|
| A5 | bpgd_t10 | 0.04 | 0 | 5.8e-05 | 3.61561e-05 | 21/10000 | 5.8 |
| A5 | bpgd_t10 | 0.05 | 0 | 0.000295 | 0.000297084 | 58/10000 | 13.1 |
| B1 | bpgd_random_t100 | 0.04 | 5 | 2.3e-05 | 1.31733e-05 | 33/4580 | 3.9 |
| B1 | bpgd_t1 | 0.04 | 6 | 2.9e-05 | 2.36521e-05 | 169/500000 | 13.3 |
| B1 | bpgd_t1 | 0.05 | 0 | 0.000391 | 0.000359427 | 480/10000 | 7.9 |
| B1 | bpgd_t10 | 0.04 | 8 | 3.21835e-06 | 6.41191e-06 | 33/250000 | 3.3 |
| B1 | bpgd_t10 | 0.05 | 0 | 0.000168463 | 0.000112356 | 377/10000 | 20.1 |
| B1 | bpgd_t10 | 0.06 | 0 | 0.00367353 | 0.00401222 | 410/10000 | 193.6 |
| B1 | bpgd_t100 | 0.04 | 0 | 1e-06 | 1.00847e-07 | 19/10000 | 3.7 |
| B1 | bpgd_t100_r10 | 0.04 | 1 | 0.000124 | 0.000180311 | 1527/124046 | 7.2 |
| B1 | bpgd_t100_r10 | 0.05 | 0 | 0.00094 | 0.000849514 | 761/10000 | 19.3 |
| B1 | bpgd_t100_r2 | 0.04 | 0 | 0.00944 | 0.00923187 | 743/10000 | 17.4 |
| B1 | bpgd_t100_r5 | 0.04 | 0 | 0.000588 | 0.000702647 | 232/10000 | 3.8 |
| B1 | bpgd_t100_r5 | 0.05 | 0 | 0.003396 | 0.00374512 | 978/10000 | 16.7 |
| B1 | bpgd_t100_r50 | 0.04 | 2 | 6.9e-05 | 7.9673e-05 | 2000/308435 | 8.3 |
| B1 | bpgd_t100_r50 | 0.05 | 0 | 0.00034 | 0.000345009 | 548/10000 | 7.8 |
| B1 | bpgd_t100_r50 | 0.06 | 0 | 0.006838 | 0.00654905 | 582/10000 | 255.5 |
| B1 | bpgd_t70 | 0.04 | 0 | 2e-06 | 2.0846e-07 | 21/10000 | 3.4 |
| B2 | bpgd_t10 | 0.04 | 0 | 8.4e-05 | 8.92147e-10 | 3/10000 | 2.2 |
| B2 | bpgd_t10 | 0.05 | 0 | 0.00021 | 0.000187826 | 13/10000 | 1.1 |
| B2 | bpgd_t10 | 0.07 | 0 | 0.000905 | 0.000139532 | 77/10000 | 4.4 |
| B2 | bpgd_t10 | 0.08 | 0 | 0.001895 | 0.00136349 | 80/10000 | 13.9 |
| B2 | bpgd_t10 | 0.09 | 0 | 0.004651 | 0.00433996 | 237/10000 | 20.1 |
| C2 | bpgd_t10 | 0.04 | 0 | 0.000144 | 3.54423e-05 | 59/10000 | 1.5 |

## Principal curve points

B1 T=10 uses Figure 3 below; Figure 4's conflicting T=10 targets remain separate in the CSV.

| Code | p | Source plain BP | Local plain BP | Source guided T=10 | Local guided T=10 |
|---|---:|---:|---:|---:|---:|
| B1 | 0.04 | 0.0434 | 100/2267 (0.04411) | 6e-06 | IS 6.412e-06 (N=250000, ESS=3.3) |
| B1 | 0.05 | 0.0867 | 100/1226 (0.08157) | 0.000179 | IS 0.0001124 (N=10000, ESS=20.1) |
| B1 | 0.06 | 0.1449 | 436/3000 (0.1453) | 0.003891 | 100/21372 (0.004679) |
| B1 | 0.07 | 0.2505 | 100/407 (0.2457) | 0.038801 | 100/2485 (0.04024) |
| B1 | 0.08 | 0.4448 | 100/244 (0.4098) | 0.21694 | 100/438 (0.2283) |
| B1 | 0.09 | 0.7141 | 100/132 (0.7576) | 0.59538 | 100/177 (0.565) |
| B1 | 0.10 | 0.9139 | 100/107 (0.9346) | 0.86325 | 100/117 (0.8547) |
| C2 | 0.04 | 0.080058 | 100/1052 (0.09506) | 0.000144 | IS 3.544e-05 (N=10000, ESS=1.5) |
| C2 | 0.05 | 0.15758 | 100/694 (0.1441) | 0.00085 | — |
| C2 | 0.06 | 0.26847 | 779/3000 (0.2597) | 0.0058 | 100/14752 (0.006779) |
| C2 | 0.07 | 0.4004 | 100/253 (0.3953) | 0.035 | 73/2000 (0.0365) |
| C2 | 0.08 | 0.63699 | 100/160 (0.625) | 0.209 | 36/200 (0.18) |
| C2 | 0.09 | 0.87228 | 100/116 (0.8621) | 0.628 | 86/150 (0.5733) |
| C2 | 0.10 | 0.98328 | 100/102 (0.9804) | 0.925 | 91/100 (0.91) |
| A5 | 0.04 | 0.000236 | 130/529662 (0.0002454) | 5.8e-05 | 1/5000 (0.0002) |
| A5 | 0.05 | 0.000876 | 113/142695 (0.0007919) | 0.000295 | 100/287770 (0.0003475) |
| A5 | 0.06 | 0.003159 | 131/39570 (0.003311) | 0.001608 | 100/67147 (0.001489) |
| A5 | 0.07 | 0.011972 | 144/10442 (0.01379) | 0.00614 | 100/15870 (0.006301) |
| A5 | 0.08 | 0.039651 | 131/3153 (0.04155) | 0.02159 | 100/4740 (0.0211) |
| A5 | 0.09 | 0.093809 | 110/1333 (0.08252) | 0.055219 | 100/1718 (0.05821) |
| A5 | 0.10 | 0.1443 | 147/867 (0.1696) | 0.12423 | 100/749 (0.1335) |
| B2 | 0.04 | 0.000406 | 92/307882 (0.0002988) | 8.4e-05 | 0/5000 (0) |
| B2 | 0.05 | 0.001265 | 89/98815 (0.0009007) | 0.00021 | 0/5000 (0) |
| B2 | 0.06 | 0.002569 | 110/48658 (0.002261) | 0.000455 | 1/5000 (0.0002) |
| B2 | 0.07 | 0.006755 | 129/18505 (0.006971) | 0.000905 | 100/167794 (0.000596) |
| B2 | 0.08 | 0.015077 | 101/8291 (0.01218) | 0.001895 | 100/68688 (0.001456) |
| B2 | 0.09 | 0.02978 | 101/4198 (0.02406) | 0.004651 | 100/28457 (0.003514) |
| B2 | 0.10 | 0.060326 | 100/2073 (0.04824) | 0.009561 | 100/11147 (0.008971) |

## Representative p=0.06 points

| Figure | Code | Decoder | Source | Local estimate | Local 95% interval | Assessment |
|---:|---|---|---:|---:|---:|---|
| 3 | B1 | bp | 0.1449 | 436/3000 | [0.13291, 0.15846] | local_95_contains_source |
| 3 | B1 | bpgd_t10 | 0.003891 | 100/21372 | [0.0038086, 0.005637] | local_95_contains_source |
| 5 | C2 | bp | 0.268469 | 779/3000 | [0.24405, 0.27575] | local_95_contains_source |
| 5 | C2 | bpgd_t10 | 0.0058 | 100/14752 | [0.0055188, 0.0081649] | local_95_contains_source |
| 7 | A5 | bpgd_t10 | 0.001608 | 100/67147 | [0.0012119, 0.0017947] | local_95_contains_source |
| 7 | A5 | qbp | 0.003159 | 131/39570 | [0.0027687, 0.0039273] | local_95_contains_source |
| 8 | B2 | bpgd_t10 | 0.000455 | 1/5000 | [5.0635e-06, 0.0011138] | low_count_unresolved |
| 8 | B2 | qbp | 0.002569 | 110/48658 | [0.0018584, 0.0027241] | local_95_contains_source |

## Points outside the local 95% interval

These are point-versus-interval flags, not formal two-sample discrepancy tests. The source interval below is approximate because its denominator is inferred from the caption's 100-failure rule and the rounded plotted rate. Figures repeating the same result are shown once.

| Figure | Code | Decoder | p | Published | Local estimate | Local 95% interval | Approx. source 95% interval | Overlap? |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 2 | B1 | bpgd_t100 | 0.07 | 0.036055 | 100/2217 (0.045106) | [0.0368481, 0.0541241] | [0.0294252, 0.0432954] | overlapping_95_intervals |
| 3 | B1 | bpgd_t1 | 0.06 | 0.00606 | 100/12358 (0.00809192) | [0.00658862, 0.00974539] | [0.00493319, 0.00729957] | overlapping_95_intervals |
| 3 | B1 | bpgd_t100 | 0.07 | 0.036055 | 100/2217 (0.045106) | [0.0368481, 0.0541241] | [0.0294252, 0.0432954] | overlapping_95_intervals |
| 4 | B1 | bpgd_t10 | 0.06 | 0.00367353 | 100/21372 (0.00467902) | [0.00380861, 0.00563699] | [0.00298988, 0.00442604] | overlapping_95_intervals |
| 6 | B1 | bpgd_t100_r2 | 0.04 | 0.00944 | 100/8273 (0.0120875) | [0.00984541, 0.0145517] | [0.00768733, 0.0113677] | overlapping_95_intervals |
| 6 | B1 | bpgd_t100_r5 | 0.06 | 0.022356 | 100/5730 (0.017452) | [0.0142216, 0.0209987] | [0.0182261, 0.0268868] | overlapping_95_intervals |
| 6 | B1 | bpgd_t100_r882 | 0.07 | 0.036055 | 100/2217 (0.045106) | [0.0368481, 0.0541241] | [0.0294252, 0.0432954] | overlapping_95_intervals |
| 7 | A5 | qbp | 0.10 | 0.1443 | 147/867 (0.16955) | [0.145153, 0.196216] | [0.118976, 0.171394] | overlapping_95_intervals |
| 8 | B2 | bpgd_t10 | 0.07 | 0.000905 | 100/167794 (0.000595969) | [0.00048493, 0.000718273] | [0.000736404, 0.00109069] | separated_95_intervals |
| 8 | B2 | bpgd_t10 | 0.08 | 0.001895 | 100/68688 (0.00145586) | [0.0011847, 0.00175448] | [0.00154212, 0.00228362] | overlapping_95_intervals |
| 8 | B2 | bpgd_t10 | 0.09 | 0.004651 | 100/28457 (0.00351407) | [0.00286008, 0.00423402] | [0.00378575, 0.00560319] | overlapping_95_intervals |
| 8 | B2 | qbp | 0.04 | 0.000406 | 92/307882 (0.000298816) | [0.000240894, 0.000366459] | [0.00033035, 0.000489329] | overlapping_95_intervals |
| 8 | B2 | qbp | 0.05 | 0.001265 | 89/98815 (0.000900673) | [0.000723375, 0.00110824] | [0.00102937, 0.00152451] | overlapping_95_intervals |
| 8 | B2 | qbp | 0.08 | 0.015077 | 101/8291 (0.0121819) | [0.009933, 0.0147827] | [0.0122829, 0.0181443] | overlapping_95_intervals |
| 8 | B2 | qbp | 0.09 | 0.02978 | 101/4198 (0.0240591) | [0.0196382, 0.029158] | [0.0242941, 0.0357881] | overlapping_95_intervals |
| 8 | B2 | qbp | 0.10 | 0.060326 | 100/2073 (0.0482393) | [0.039419, 0.0583632] | [0.0493397, 0.0722618] | overlapping_95_intervals |

At B1 T=1, p=0.06, the local 100/12,358 estimate excludes the plotted 0.00606 point. Figure 3 says its points were also collected to 100 failures; approximating that source run as 100/16,502 gives a 95% interval that overlaps the local interval. This is a reproducibility lead, not evidence of a specific kernel error.

## Table 1: decimated variables

The paper specifies different T values in its prose and caption. The executed T=10 mean is shown separately.

| p | Source mean | Source shots | Local T=10 mean ± SE | Local shots |
|---:|---:|---:|---:|---:|
| 0.05 | 2.91 | 1,000,000 | 3.038 ± 0.167 | 10000 |
| 0.06 | 9.82 | 100,000 | 10.563 ± 0.472 | 21372 |
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
- The comparison omits BP-OSD and BP-SI. The pinned raw source extraction retains their provenance, but neither appears in this BP/BPGD table or plot.
- Plain QBP v2 counts are imported from the earlier vanilla campaign, not rerun here. Its archive hash matches this source, but its recorded main.tex hash has a transcription error; this study records the independently verified TeX hash. The earlier count ledgers were not revalidated by this assessor.
- The new binary path is a compiled interpretation of the paper's V2C clipping and decimation pseudocode. The A5/B2 Q-BPGD path uses the existing compiled BP4 v2 kernel; these are canonical adaptations.
- All local results include Type I and Type II block failures. A correction differing from the sampled error by a stabilizer counts as success.
- Reaching 100 direct failures at the source B1 T=100, p=0.04 rate of 10⁻⁶ requires about 100 million shots in expectation; B1 T=10 at p=0.04 requires about 16.7 million. Rare-event estimates are explicitly marked IS and require the precision gate above before they are considered resolved.

The complete point table is [comparison.csv](comparison.csv); plots are [comparison.png](comparison.png) and [comparison.pdf](comparison.pdf).
