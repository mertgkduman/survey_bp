# Lifted-product [[1054,140]] full decoder stack

0/72 arm/rate workers independently audited. Fresh confirmation only below.

Original LP paper provides no LER plot/rate grid/numeric iteration cap for1054. Controlled prospective depolarizing grid0.02,0.04,0.06,0.08,0.10,0.12. Budget32 and scale0.625 borrowed from cited BP-OSD paper, whose schedule is layered; this study uses canonical flooding. No original LP paper curve ordinates exist to compare. Original LP Example4, depolarizing code capacity. Q-BP, tuning, Relay and beam are canonical adaptations. Search128 is explicitly4x the documented BP cap. No native runtime or statistical paper agreement is claimed before confirmation.

Noise: independent I/X/Y/Z, probabilities1-p,p/3,p/3,p/3. Both X/Z residuals count. Block LER and derived word error rate are different: WER=1-(1-LER)^(1/140). Means include both CSS components, or all joint edges for Q-BP, plus every search branch/relay. OSD elimination/candidates are included in latency. Latency excludes JIT/sampling/evaluation and uses1%-wide bins for quantiles. Tuning and confirmation seeds are disjoint. Fixed settings use32 BP sweeps per component/joint graph. Search128 has an explicit4x aggregate per-component ceiling.

| Arm | p | Shots | Block LER | 95% CI | Word error rate | Mean sweeps | Mean edge updates | Mean µs |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |

The original paper gives no LER curves for this code; paper-ordinate comparison is not applicable.
