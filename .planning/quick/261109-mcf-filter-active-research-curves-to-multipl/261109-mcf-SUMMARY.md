---
quick_id: 261109-mcf
status: complete
date: 2026-11-09
implementation_commit: 7eeddf7
verification: passed
---

# Multi-rate active research view and results-backed inputs

Delivered central v2 eligibility in `ResearchCurves.project` / `active`, after retirement, valid-point selection and existing conservative evidence projection. Eligibility requires two distinct measured error-rate coordinates; repeated cohorts count once, and valid zero-failure bounds count. Nonphysical setting/prior axes cannot qualify or join physical-rate evidence. No thresholds, pooling contracts or decoder kernels changed.

All plots, selectors, availability, tables, receipts/CSV and saved-decoder choices consume the same active view. Public codes/circuits derive from its input identities; saved decoders derive from its original provenance members. Removed the permissive fallback projection. Imported results and catalog rebuilds reuse this boundary while retaining all underlying records.

Refresh and render reconcile stale plot inputs/curves, exact saved mode and builder choices, clear removed-input matrices/Stim, and invalidate downloads. Missing defaults and empty results remain usable with custom matrix/Stim construction and the new-experiment baseline presets. An async circuit load cannot restore bytes after its selection changes. Fixture aliases cannot reappear through imports.

| Active view | Before | After |
|---|---:|---:|
| Curves | 105 | 63 |
| Measurement points | 361 | 319 |
| Codes | 7 | 6 |
| Registered circuits | 3 | 0 |

Removed 42 one-rate curves; hidden GB46 and all three one-rate registered circuits. Every removed curve and its original provenance is listed in `REMOVED-FROM-ACTIVE-VIEW.md` / `active-view-audit.json`. The three-qubit fixture was already absent from current public examples and catalog. Remaining historical v1/internal references are preserved by design.

Verification: 118 research tests; 14 browser workflow groups; two real retained-result browser imports (singleton remains hidden, multi-rate circuit appears and survives reload); empty-state and stale-selection checks pass. Rebuild produced byte-identical catalog/contracts/templates/policies/matrix assets. Archived v1 bytes, raw evidence, manifests, registry, backends, model configuration and scientific phase progress remain unchanged. No retained campaign was rerun. See `261109-mcf-VERIFICATION.md` and companion JSON receipts.

Executed inline using gsd-quick's no-auto-spawn fallback. No subagents, model changes or publication actions. Phase 11 remains executing, Phase 5 human review remains open and Phase 7 stays paused.
