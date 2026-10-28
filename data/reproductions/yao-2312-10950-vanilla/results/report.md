# Yao et al. vanilla Q-BP comparison

Source: [arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2), Figures 7 and 8.
Q-BP points were transcribed from the authors' TeX. Source denominators are unavailable;
the source point inside a local exact 95% interval is descriptive, not a two-sample test.
All local arms use 100 sum-product iterations and the same depolarizing errors per point.
v2 is undamped (d=0) to keep this a vanilla numerical comparison.

Completed shards: 128/128.

| Code | p | N | Source Q-BP | BP4 v1 | BP4 v2 | Binary v1 | Binary v2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A5 | 0.10 | 867 | 0.1443 | 437/867 (0.504037) | 147/867 (0.16955) | 461/867 (0.531719) | 462/867 (0.532872) |
| B2 | 0.10 | 2,073 | 0.060326 | 1914/2073 (0.9233) | 100/2073 (0.0482393) | 894/2073 (0.431259) | 901/2073 (0.434636) |
| A5 | 0.09 | 1,333 | 0.093809 | 498/1333 (0.373593) | 110/1333 (0.0825206) | 485/1333 (0.363841) | 489/1333 (0.366842) |
| B2 | 0.09 | 4,198 | 0.02978 | 3585/4198 (0.853978) | 101/4198 (0.0240591) | 1085/4198 (0.258456) | 1089/4198 (0.259409) |
| A5 | 0.08 | 3,153 | 0.039651 | 900/3153 (0.285442) | 131/3153 (0.0415477) | 739/3153 (0.23438) | 737/3153 (0.233746) |
| B2 | 0.08 | 8,291 | 0.015077 | 6532/8291 (0.787842) | 101/8291 (0.0121819) | 1109/8291 (0.133759) | 1164/8291 (0.140393) |
| A5 | 0.07 | 10,442 | 0.011972 | 1880/10442 (0.180042) | 144/10442 (0.0137905) | 1189/10442 (0.113867) | 1205/10442 (0.115399) |
| B2 | 0.07 | 18,505 | 0.006755 | 13040/18505 (0.704674) | 129/18505 (0.00697109) | 1236/18505 (0.0667928) | 1268/18505 (0.068522) |
| A5 | 0.06 | 39,570 | 0.003159 | 4541/39570 (0.114759) | 131/39570 (0.00331059) | 1949/39570 (0.0492545) | 1935/39570 (0.0489007) |
| B2 | 0.06 | 48,658 | 0.002569 | 28674/48658 (0.589297) | 110/48658 (0.00226068) | 1508/48658 (0.0309918) | 1432/48658 (0.0294299) |
| A5 | 0.05 | 142,695 | 0.000876 | 8558/142695 (0.0599741) | 113/142695 (0.000791899) | 2307/142695 (0.0161673) | 2282/142695 (0.0159922) |
| B2 | 0.05 | 98,815 | 0.001265 | 46028/98815 (0.4658) | 89/98815 (0.000900673) | 1192/98815 (0.0120629) | 1176/98815 (0.011901) |
| A5 | 0.04 | 529,662 | 0.000236 | 14786/529662 (0.0279159) | 130/529662 (0.00024544) | 2177/529662 (0.00411017) | 2124/529662 (0.0040101) |
| B2 | 0.04 | 307,882 | 0.000406 | 103657/307882 (0.336678) | 92/307882 (0.000298816) | 1368/307882 (0.00444326) | 1195/307882 (0.00388136) |

Published point inside local exact 95% interval, by code:
- A5: bp4_v1: 0/7, bp4_v2: 6/7, binary_v1: 0/7, binary_v2: 0/7.
- B2: bp4_v1: 0/7, bp4_v2: 2/7, binary_v1: 0/7, binary_v2: 0/7.

BP4 v2 is near the A5 Q-BP curve at six of seven plotted points.
On B2 it follows the same rate scale, but its local rate is lower than
the published point at six of seven values of p; only two published
B2 points fall inside the corresponding local intervals. BP4 v1 and
both separate-binary arms are outside those intervals at every point.
All BP4 v2 failures in this campaign are Type I syndrome failures.
These are observations about the named local profiles. The paper does
not specify enough numerical details to attribute the remaining B2
difference to a particular source implementation choice or defect.

Type I (syndrome failure), Type II (logical failure after valid syndrome),
exact/stabilizer success, exact intervals, paired rescues/losses, work, and time are in
[`comparison.csv`](comparison.csv) and [`merged.json`](merged.json).
Per-shot ledgers and manifests are under `results/shards/`; each is SHA-256 audited.
The published Q-BP implementation and exact numerical conventions are not identified
by the paper. Local v1/v2 curves are explicit canonical adaptations.
