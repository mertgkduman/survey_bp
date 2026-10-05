# BB72 CSS BeamSearch versus RelayBP: matched parameter study

This is a controlled X-only CSS adaptation, not either paper's circuit-level reproduction. 
Selection and evaluation use disjoint physical sample identities. All terminal shots count.

Design SHA-256: `9b013e8ee67fafc3e8891407b94264575f4f3ae66711176b6d1958d3d888c904`. Selection lock SHA-256: `cbcb544b1b9bd300735170a9b4974438e8468314aecb3072d18a2985ea074f3a`.

## Selected settings, failures, and cost

| p | damping gamma | method | extra iterations/unit | failures/shots | 95% exact interval | mean total C2V | mean runtime ms |
| ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| 0.05 | 1.0 | beam | 10 | 232/512 | [0.409, 0.497] | 5988.7 | 513.0 |
| 0.05 | 1.0 | relay | 10 | 96/512 | [0.155, 0.224] | 3441.2 | 294.4 |
| 0.05 | 0.5 | beam | 5 | 82/512 | [0.129, 0.195] | 939.8 | 31.4 |
| 0.05 | 0.5 | relay | 20 | 81/512 | [0.128, 0.193] | 961.9 | 103.2 |
| 0.08 | 1.0 | beam | 5 | 1030/1280 | [0.782, 0.826] | 10190.2 | 955.6 |
| 0.08 | 1.0 | relay | 10 | 643/1280 | [0.475, 0.530] | 6560.8 | 616.8 |
| 0.08 | 0.5 | beam | 5 | 590/1280 | [0.433, 0.489] | 2026.0 | 188.0 |
| 0.08 | 0.5 | relay | 20 | 584/1280 | [0.429, 0.484] | 1965.8 | 181.0 |

## Prespecified paired contrasts

| p / gamma | Beam-only valid | Relay-only valid | Beam minus Relay failure | Holm p | Assessment |
| --- | ---: | ---: | ---: | ---: | --- |
| p050/g1000 | 1 | 137 | +0.266 | 2.39e-39 | relay_lower_failure |
| p050/g0500 | 4 | 5 | +0.002 | 1 | inconclusive |
| p080/g1000 | 2 | 389 | +0.302 | 1.22e-112 | relay_lower_failure |
| p080/g0500 | 11 | 17 | +0.005 | 0.69 | inconclusive |

## Full prespecified parameter grid

| p | gamma | profile | method | failures/shots | mean initial C2V | mean extra C2V | mean runtime ms |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 0.05 | 1.0 | i05 | beam | 236/512 | 2160.0 | 3817.0 | 200.9 |
| 0.05 | 1.0 | i05 | relay | 118/512 | 2160.0 | 2013.2 | 138.0 |
| 0.05 | 1.0 | i10 | beam | 232/512 | 2160.0 | 3828.7 | 513.0 |
| 0.05 | 1.0 | i10 | relay | 96/512 | 2160.0 | 1281.2 | 294.4 |
| 0.05 | 1.0 | i20 | beam | 233/512 | 2160.0 | 3875.2 | 641.7 |
| 0.05 | 1.0 | i20 | relay | 101/512 | 2160.0 | 1016.3 | 339.6 |
| 0.05 | 0.5 | i05 | beam | 82/512 | 842.9 | 96.9 | 31.4 |
| 0.05 | 0.5 | i05 | relay | 79/512 | 842.9 | 179.3 | 33.9 |
| 0.05 | 0.5 | i10 | beam | 81/512 | 842.9 | 121.2 | 82.6 |
| 0.05 | 0.5 | i10 | relay | 79/512 | 842.9 | 144.7 | 84.0 |
| 0.05 | 0.5 | i20 | beam | 81/512 | 842.9 | 131.0 | 104.3 |
| 0.05 | 0.5 | i20 | relay | 81/512 | 842.9 | 119.0 | 103.2 |
| 0.08 | 1.0 | i05 | beam | 1030/1280 | 3528.1 | 6662.2 | 955.6 |
| 0.08 | 1.0 | i05 | relay | 743/1280 | 3528.1 | 4824.1 | 775.5 |
| 0.08 | 1.0 | i10 | beam | 1028/1280 | 3528.1 | 6709.6 | 966.6 |
| 0.08 | 1.0 | i10 | relay | 643/1280 | 3528.1 | 3032.8 | 616.8 |
| 0.08 | 1.0 | i20 | beam | 1029/1280 | 3528.1 | 6764.6 | 946.7 |
| 0.08 | 1.0 | i20 | relay | 639/1280 | 3528.1 | 2326.7 | 539.2 |
| 0.08 | 0.5 | i05 | beam | 590/1280 | 1638.1 | 388.0 | 188.0 |
| 0.08 | 0.5 | i05 | relay | 590/1280 | 1638.1 | 676.5 | 214.3 |
| 0.08 | 0.5 | i10 | beam | 587/1280 | 1638.1 | 426.2 | 194.8 |
| 0.08 | 0.5 | i10 | relay | 585/1280 | 1638.1 | 365.5 | 188.7 |
| 0.08 | 0.5 | i20 | beam | 588/1280 | 1638.1 | 495.7 | 196.2 |
| 0.08 | 0.5 | i20 | relay | 584/1280 | 1638.1 | 327.7 | 181.0 |

Initial-BP baselines and every outcome count are in result.json. The per-shot outcomes, work vectors, and observed serial runtime are in the shard ledgers.

## Source and budget limits

Relay extra units are disordered-memory legs after shared plain BP; Beam extra units are masked branches. Their equal additional C2V cap does not make a leg and a branch compute-equivalent. Observed runtime is serial same-process time. The source experiments used circuit-level conditions.
