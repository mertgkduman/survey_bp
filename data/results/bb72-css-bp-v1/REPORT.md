# BB72 CSS BP comparison v1

Source-pinned [[72,12,6]] BB72 artifact; X-only code-capacity noise. Every evaluation denominator includes all terminal shots.
Selection: 128 matched samples per rate; evaluation: 512 new matched samples per rate.
Frozen design SHA-256: `b3e89645bde5061fb309474db574e88218345a8cd0e4008b81d405e29127cbdd`. All public arms replay-verified before this report.
The common cap is 40 flooding BP sweeps or 8,640 messages in each direction per shot; non-message work and realized cost differ and are reported separately.

## Selected configurations

- bpgd: `bpgd-g1000`
- bpsf: `bpsf-g1000`
- ms: `ms-g0500`
- nms: `nms-a0850-g1000`
- oms: `oms-o0200-g0500`
- spa: `spa-g0750`

## Shared-work view

| p | Configuration | Failures / 512 | 95% exact interval | Mean C2V updates |
| ---: | --- | ---: | --- | ---: |
| 0.03 | `spa-g1000` | 26 / 512 | [0.033, 0.074] | 586.4 |
| 0.03 | `bpgd-g1000` | 21 / 512 | [0.026, 0.062] | 540.0 |
| 0.03 | `bpsf-g1000` | 20 / 512 | [0.024, 0.060] | 518.5 |
| 0.03 | `ms-g0500` | 24 / 512 | [0.030, 0.069] | 519.8 |
| 0.03 | `nms-a0850-g1000` | 22 / 512 | [0.027, 0.064] | 670.4 |
| 0.03 | `oms-o0200-g0500` | 24 / 512 | [0.030, 0.069] | 508.8 |
| 0.03 | `spa-g0750` | 18 / 512 | [0.021, 0.055] | 436.6 |
| 0.05 | `spa-g1000` | 97 / 512 | [0.156, 0.226] | 1405.3 |
| 0.05 | `bpgd-g1000` | 92 / 512 | [0.147, 0.216] | 1336.5 |
| 0.05 | `bpsf-g1000` | 85 / 512 | [0.135, 0.201] | 1223.4 |
| 0.05 | `ms-g0500` | 91 / 512 | [0.146, 0.214] | 1105.3 |
| 0.05 | `nms-a0850-g1000` | 94 / 512 | [0.151, 0.220] | 1587.1 |
| 0.05 | `oms-o0200-g0500` | 91 / 512 | [0.146, 0.214] | 1157.6 |
| 0.05 | `spa-g0750` | 88 / 512 | [0.140, 0.207] | 1158.9 |
| 0.08 | `spa-g1000` | 268 / 512 | [0.479, 0.567] | 3701.5 |
| 0.08 | `bpgd-g1000` | 264 / 512 | [0.471, 0.560] | 3642.5 |
| 0.08 | `bpsf-g1000` | 252 / 512 | [0.448, 0.536] | 3326.5 |
| 0.08 | `ms-g0500` | 254 / 512 | [0.452, 0.540] | 2134.3 |
| 0.08 | `nms-a0850-g1000` | 264 / 512 | [0.471, 0.560] | 3725.6 |
| 0.08 | `oms-o0200-g0500` | 256 / 512 | [0.456, 0.544] | 2439.3 |
| 0.08 | `spa-g0750` | 262 / 512 | [0.467, 0.556] | 3575.4 |

## Paired comparisons with undamped SPA

| p | Family | Newly valid | Lost valid | Failure difference | Holm p | Assessment |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 0.03 | bpgd | 5 | 0 | -0.010 | 0.75 | inconclusive |
| 0.03 | bpsf | 7 | 1 | -0.012 | 0.7734 | inconclusive |
| 0.03 | ms | 3 | 1 | -0.004 | 1 | inconclusive |
| 0.03 | nms | 5 | 1 | -0.008 | 1 | inconclusive |
| 0.03 | oms | 3 | 1 | -0.004 | 1 | inconclusive |
| 0.03 | spa | 9 | 1 | -0.016 | 0.3438 | inconclusive |
| 0.05 | bpgd | 6 | 1 | -0.010 | 1 | inconclusive |
| 0.05 | bpsf | 15 | 3 | -0.023 | 0.1281 | inconclusive |
| 0.05 | ms | 10 | 4 | -0.012 | 1 | inconclusive |
| 0.05 | nms | 12 | 9 | -0.006 | 1 | inconclusive |
| 0.05 | oms | 9 | 3 | -0.012 | 1 | inconclusive |
| 0.05 | spa | 11 | 2 | -0.018 | 0.3438 | inconclusive |
| 0.08 | bpgd | 4 | 0 | -0.008 | 1 | inconclusive |
| 0.08 | bpsf | 20 | 4 | -0.031 | 0.02779 | lower_failure_than_reference |
| 0.08 | ms | 24 | 10 | -0.027 | 0.3438 | inconclusive |
| 0.08 | nms | 16 | 12 | -0.008 | 1 | inconclusive |
| 0.08 | oms | 21 | 9 | -0.023 | 0.5561 | inconclusive |
| 0.08 | spa | 8 | 2 | -0.012 | 1 | inconclusive |

## Source-settings view

These records distinguish the source paper's original problem and settings from the BB72 CSS arms above. No row below is a source-curve reproduction.

| Source configuration | BB72 CSS status | Reason |
| --- | --- | --- |
| bravyi_bb72_bp_osd | not_applicable_as_faithful_reproduction | The pinned source uses circuit-level BP-OSD; this study has perfect-syndrome X-only CSS noise and BP-only arms. |
| yao_bpgd | modified_settings_transplant | The controlled BB72 arm uses T=5 and R=8 under the common cap; the B1 source reports T=10 or 100 and a larger decimation envelope. |
| gokduman_damping | equation_transplant_only | The same V2C recurrence is used on an X-bit-flip channel with project-selected gamma values; published erasure-channel optimized gamma values are not imported. |
| bpsf | controlled_css_adaptation | Seeded stable test order and first-valid original-problem selection replace source unseeded parallel arrival semantics. |

The exact paper links, per-arm manifests, terminal ledgers, and uncertainty rules are in the frozen design and study output. A difference at one BB72 rate does not establish a decoder ranking across codes or channels.
