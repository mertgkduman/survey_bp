# Development and evidence update — 29 September 2026

Policy-Based BP Research Platform for QLDPC Decoding

Evidence captured 29 September 2026, 22:57 UTC. This is a dated status report, not a Phase 4 completion or journal reproduction claim.

## What changed since the 26 September update

The frozen three-code Relay memory calibration has finished. Its terminal result is `completed_with_inconclusive`: all 182 planned configurations and 5,824 shots were retained, but some configurations exhausted their declared work cap. An independent audit reconstructed every retained terminal Relay ledger and its manifest binding. The deterministic selections were then frozen from calibration data alone. BB-144 and generated HGP have eligible settings; B1 has none under its three-leg-equivalent work cap.

The [26 September report](development-update-20260926.md) remains a historical snapshot. Its lower-noise BB-144 experiment and exact-author agreement diagnostic remain completed, separate studies. No fresh post-selection Phase 4 evaluation, focused factorial result, or representative trace inventory has been produced. The roadmap still records three of fourteen phases complete and Phase 4 at twelve of fifteen plan summaries; its state file has not yet been advanced for the newly terminal calibration.

## Calibration completion and audit

| Code | Preset | Configurations | Eligible complete configurations | Completed shots | Work-budget terminations |
| --- | --- | ---: | ---: | ---: | ---: |
| Reconciled B1 | Canonical SPA | 21 | 0 | 517 | 155 |
| Reconciled B1 | Source-procedure min-sum | 21 | 0 | 374 | 298 |
| BB-144 | Canonical SPA | 55 | 20 | 1,760 | 0 |
| BB-144 | Source-procedure min-sum | 55 | 26 | 1,760 | 0 |
| Generated HGP | Canonical SPA | 15 | 6 | 480 | 0 |
| Generated HGP | Source-procedure min-sum | 15 | 7 | 480 | 0 |
| **Total** | | **182** | **59** | **5,371** | **453** |

Every configuration had 32 planned calibration shots. B1 used physical error rate 0.07 and a three-BP-call per-shot cap; BB-144 used 0.07 and generated HGP used 0.03, both with up to 31 BP calls. The 453 work-budget terminations are all in B1. They remain failures of eligibility, not silently dropped observations. The category charged 269,929.25 seconds against its frozen 688,243-second ceiling; the incomplete B1 search is caused by the per-shot work limit, not exhaustion of that category ceiling.

The read-only terminal audit passed frozen cap and plan identities, exact configuration and shot coverage, retained public verification receipts, deterministic sample identities, work limits and aggregate accounting. Its second pass streamed the aggregate ledger and reconstructed all 5,824 terminal Relay shots against the expected manifests, appended-byte digests, work, outcomes and termination fields. The audit is in isolated branch commit `263501e`; the campaign source and ledgers were not edited. This proves retained-evidence integrity for this gate. It does not turn calibration outcomes into unbiased performance estimates.

## Frozen memory settings

The selector followed the declared eligibility, logical-failure estimate, work and deterministic tie rules. Values below are first-leg `gamma0`, later-leg center and later-leg width, in that order. Each reported failure fraction is from only 32 **selection** shots at the code's calibration error rate, so it should not be read as fresh LER.

| Code | Preset | Selected `(gamma0, center, width)` | Calibration failures | Status |
| --- | --- | --- | ---: | --- |
| B1 | Canonical SPA | None | — | Inconclusive |
| B1 | Source-procedure min-sum | None | — | Inconclusive |
| BB-144 | Canonical SPA | `(0.375, 0.5, 0.875)` | 11/32 | Finite precision limited |
| BB-144 | Source-procedure min-sum | `(0.375, 0.5, 0.875)` | 11/32 | Finite precision limited |
| Generated HGP | Canonical SPA | `(0.5, 0.75, 2.0)` | 17/32 | Finite precision limited |
| Generated HGP | Source-procedure min-sum | `(0.25, 0.75, 0.5)` | 27/32 | Finite precision limited |

The separately selected **shared-memory** setting is `(0.125, 0.25, 1.25)` for BB-144 and `(0.5, 0.75, 2.0)` for generated HGP. B1 has no jointly eligible setting. Those shared settings are intended for a controlled same-memory comparison; the current frozen evaluation cap admits only baseline and the two separately selected procedure arms. A versioned supplemental cap and entitlement would be needed before sampling extra shared-setting arms. Selection is deterministic and audit-backed, but its 32-shot estimates are noisy and selection-biased. The high HGP failure fractions are a warning that fresh evaluation and careful problem matching are essential.

## Completed pilot LER and implementation agreement

The independent lower-noise experiment used **fixed, uncalibrated** settings on one X-only BB-144 CSS code-capacity component. Its all-shot decoder failure metric counts any shot without a selected, syndrome-valid, logically correct recovery as a failure.

| Physical error rate | Shots per arm | Canonical SPA baseline → Relay | Source-style min-sum baseline → Relay |
| --- | ---: | ---: | ---: |
| 0.05 | 8,192 | 4.114% → 3.528% | 4.309% → 3.540% |
| 0.06 | 2,048 | 9.668% → 8.691% | 10.693% → 9.082% |

The experiment met its prespecified within-arm precision rule. Its exact intervals and five diagnostic outcome cells are in the retained result and the 26 September update. Relay lowered the observed failure fraction in these matched cohorts, but no cross-arm superiority or equivalence test was prespecified. The nearly equal canonical and source-style aggregate LERs at 0.05 do not imply identical shot decisions. This pilot does not use the newly frozen coefficients and cannot validate them.

The separate pinned-author v0.2.2 diagnostic retained 128 matched native/canonical pairs per code. Success flags disagreed on 10 B1, 3 BB-144 and 9 generated-HGP pairs; exact candidate vectors disagreed on 37, 16 and 65 pairs respectively. These are controlled CSS implementation-agreement observations, not formal equivalence or reproduction of the source paper's circuit-level curves. The source-style canonical arm uses min-sum; the canonical-default arm uses SPA. Neither is the separately staged Rust author implementation.

## Remaining deviations and project gates

The Phase 4 pilots are CSS code-capacity adaptations. Their physical-noise model, code identity, caps and logical-failure denominator differ from circuit-level Relay experiments. The source-style, canonical-default and native arms also have distinct numerical and implementation semantics. Agreement of aggregate pilot LERs cannot establish paper-curve agreement, a universal decoder ranking, or a target-quality LER. B1's missing eligible calibration setting is explicit rather than filled from the other codes.

The isolated implementation branch contains additional ordinary-memory corrections, local disordered-affine execution, guarded evaluation/factorial preparation and notebook views. Those source changes remain separate from the frozen calibration producer. Historical ordinary-memory ledgers produced before its dispatch correction keep their original plain-BP meaning. Remaining Phase 4 work is to integrate verified source changes, finish or explicitly qualify the B1 evaluation gap under a versioned decision, run fresh matched evaluation and focused factorial arms, retain bounded traces and costs, then complete the notebook and phase verification. Phase 5 interventions and later quaternary/circuit work remain outside this report's measured scope.

## Provenance and rebuilding

The compact [status snapshot](evidence/phase4-status-snapshot-20260929.json) records the exact SHA-256 and byte count of the local calibration result and aggregate ledger, frozen selection, lower-noise result and exact-author diagnostic, along with the counts and settings used here. The large raw campaign artifacts are local retained evidence and are **not** included in this Git documentation commit. The selection file is likewise represented by its digest and the compact selected fields in the snapshot. Readers should use the original ledgers and public verifier for independent scientific reassessment.

Run `.venv/bin/python tools/build_phase4_status_pdf.py` to regenerate this report's PDF; `--check` verifies exact bytes. The builder reads only this Markdown file and the frozen snapshot, so subsequent simulations cannot silently change the dated PDF. The previous PDFs and their source documents remain unchanged.
