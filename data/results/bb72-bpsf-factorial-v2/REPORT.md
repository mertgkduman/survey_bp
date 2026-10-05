# BB72 BP-SF factorial v2

Independent controlled X-only BB72 CSS adaptation. The min-sum BP-SF arm remains different from the source's unseeded parallel first-arrival execution; no author-code reproduction or parallel-latency claim.
Independent fixed-shot cohort; no v1 shots pooled. All terminal outcomes remain in the denominator.
Design SHA-256: `3b9f7e5c7de5c803346a91f30fbfb8b264d943e88510b35b722437a582b93148`. All 24 arms passed public replay verification.

## Failure and cost view

| p | Arm | Failures / shots | 95% exact interval | Mean C2V | Mean BP calls | Mean measured runtime (ms) |
| ---: | --- | ---: | --- | ---: | ---: | ---: |
| 0.05 | `spa-g1000-bp20` | 102 / 512 | [0.165, 0.236] | 1012.9 | 1.00 | 289.8 |
| 0.05 | `spa-g1000-bp40` | 98 / 512 | [0.158, 0.228] | 1434.8 | 1.00 | 345.0 |
| 0.05 | `spa-g1000-bpsf20plus4x5` | 87 / 512 | [0.138, 0.205] | 1256.3 | 1.25 | 317.1 |
| 0.05 | `spa-g0500-bp20` | 94 / 512 | [0.151, 0.220] | 1020.5 | 1.00 | 263.7 |
| 0.05 | `spa-g0500-bp40` | 92 / 512 | [0.147, 0.216] | 1357.6 | 1.00 | 394.9 |
| 0.05 | `spa-g0500-bpsf20plus4x5` | 92 / 512 | [0.147, 0.216] | 1283.8 | 1.25 | 323.8 |
| 0.05 | `ms-g1000-bp20` | 244 / 512 | [0.433, 0.521] | 2210.2 | 1.00 | 129.8 |
| 0.05 | `ms-g1000-bp40` | 244 / 512 | [0.433, 0.521] | 4243.2 | 1.00 | 286.8 |
| 0.05 | `ms-g1000-bpsf20plus4x5` | 180 / 512 | [0.310, 0.395] | 3810.4 | 2.58 | 389.9 |
| 0.05 | `ms-g0500-bp20` | 103 / 512 | [0.167, 0.239] | 839.1 | 1.00 | 49.4 |
| 0.05 | `ms-g0500-bp40` | 102 / 512 | [0.165, 0.236] | 1039.9 | 1.00 | 60.5 |
| 0.05 | `ms-g0500-bpsf20plus4x5` | 92 / 512 | [0.147, 0.216] | 926.9 | 1.10 | 78.0 |
| 0.08 | `spa-g1000-bp20` | 657 / 1280 | [0.486, 0.541] | 2143.8 | 1.00 | 448.3 |
| 0.08 | `spa-g1000-bp40` | 648 / 1280 | [0.478, 0.534] | 3665.4 | 1.00 | 897.4 |
| 0.08 | `spa-g1000-bpsf20plus4x5` | 594 / 1280 | [0.436, 0.492] | 3297.4 | 2.11 | 686.1 |
| 0.08 | `spa-g0500-bp20` | 642 / 1280 | [0.474, 0.529] | 2315.8 | 1.00 | 562.1 |
| 0.08 | `spa-g0500-bp40` | 632 / 1280 | [0.466, 0.522] | 3800.6 | 1.00 | 822.4 |
| 0.08 | `spa-g0500-bpsf20plus4x5` | 628 / 1280 | [0.463, 0.518] | 3763.1 | 2.35 | 747.8 |
| 0.08 | `ms-g1000-bp20` | 1029 / 1280 | [0.781, 0.825] | 3526.4 | 1.00 | 213.8 |
| 0.08 | `ms-g1000-bp40` | 1029 / 1280 | [0.781, 0.825] | 6968.0 | 1.00 | 398.3 |
| 0.08 | `ms-g1000-bpsf20plus4x5` | 849 / 1280 | [0.637, 0.689] | 6460.6 | 3.83 | 509.7 |
| 0.08 | `ms-g0500-bp20` | 609 / 1280 | [0.448, 0.504] | 1583.9 | 1.00 | 76.4 |
| 0.08 | `ms-g0500-bp40` | 604 / 1280 | [0.444, 0.500] | 2040.0 | 1.00 | 114.5 |
| 0.08 | `ms-g0500-bpsf20plus4x5` | 580 / 1280 | [0.426, 0.481] | 1939.1 | 1.35 | 127.6 |

Runtime methods and scopes differ between BP-only and BP-SF arms; these are same-node serial observations, not source parallel latency. Full typed work vectors and runtime metadata are in `result.json`.

## Prespecified primary paired contrasts at p=0.08

| Contrast | Newly valid | Lost valid | Failure difference | Holm p | Assessment |
| --- | ---: | ---: | ---: | ---: | --- |
| `ms-bpsf-vs-ms-bp40` | 180 | 0 | -0.141 | 2.61e-54 | lower_failure_than_reference |
| `spa-bpsf-vs-spa-bp40` | 55 | 1 | -0.042 | 1.582e-15 | lower_failure_than_reference |

All other contrasts are descriptive and appear in `result.json`; no unadjusted directional claim is made for them.

## Source status

| Variant | Status | Reason |
| --- | --- | --- |
| spa_bpsf | controlled_css_adaptation | Canonical SPA messages and deterministic seeded test order differ from source min-sum parallel selection. |
| min_sum_bpsf | source_informed_kernel_adaptation | Min-sum update is source-informed, but seeded serial first-valid selection and fixed BB72 CSS conditions remain different from the paper. |
| bravyi_bb72_bp_osd | not_reproduced | The source BB72 experiment used circuit-level BP-OSD, not perfect-syndrome X-only CSS BP. |
