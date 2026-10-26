---
status: resolved
trigger: Compare poor-performance BP4 implementations with the supplied standalone four-log-weight reference, measure tie-policy effects, and separate confirmed gaps from hypotheses.
created: 2026-10-26
updated: 2026-10-26
---

# BP4 reference performance gap

## Symptoms

- Expected: faithful BP4 kernel behavior under matched input graph, priors, check update, hard decision, stopping, and independent outcome evaluation.
- Actual: local B1 and double-Gross BP4 pilots fail far more often than the supplied presentation curves; the user supplied a separate Python reference contract for comparison.
- Errors: no runtime exception; observed excess nonconvergence.
- Timeline: gap persists across Q8 min-sum/sum-product and compiled float64 diagnostics.
- Reproduction: use stored matched B1 p=0.10 and double-Gross p=0.08 event sequences and inspect canonical/experimental BP4 implementations.

## Current Focus

- hypothesis: Global float64 clipping and hard-decision ties account for substantial local BP4 nonconvergence.
- test: Matched B1 and double-Gross ablations with per-shot hashes, independent four-log-weight oracle, and ledger audit.
- expecting: Removing clipping markedly improves convergence; tie changes some outcomes but cannot explain the full gap.
- next_action: Completed; source package and original presentation matrices remain unavailable for direct replay.

## Evidence

- 2026-10-26: Initial depolarizing identity LLR and projected commutation LLR are distinct and computed correctly at p0=.08 and .10. Internal I/X/Y/Z graph, sample, and evaluator semantics are consistent; X checks precede Z checks.
- 2026-10-26: B1 p=.10 on 200 identical errors: canonical compiled float64 155 Type I failures; changing only the tie ladder 102; reference check product with global clip 105; unclipped box-plus 0; reference-style product without global clip 0.
- 2026-10-26: double-Gross p=.08 on 1000 identical errors: canonical compiled float64 116 Type I failures; reference tie 97; reference check product with global clip 94; projection-only clip 120; posterior/V2C-only clip 100; unclipped box-plus 2; reference-style product without global clip 1.
- 2026-10-26: Tuned Q8 SP tie ablation changed failure counts 72→72 on B1 and 55→53 on double-Gross; original outcomes and iterations exactly matched all 1200 prior Q8 ledger entries.
- 2026-10-26: Reference-style diagnostic corrections matched independently coded four-log-weight reference-order oracle on one B1 and three double-Gross shots; one B1 stop iteration differed (26 vs 27), preserving arithmetic-order uncertainty.
- 2026-10-26: All new ledgers and cross-run error hashes audited in `reference_gap_rates.csv` and `reference_gap_paired.csv`; report `REFERENCE_GAP_AUDIT.md` records confirmed differences and remaining source-fidelity hypotheses.

## Eliminated

- hypothesis: Depolarizing prior uses the identity-referenced LLR in place of the commuting projection; direct checks found correct distinct values.
- hypothesis: A local X/Z label swap or incorrect syndrome block order causes the two-code gap; graph/evaluator checks and four-state oracle agree after 2↔3 translation.
- hypothesis: An in-place compiled V2C update changes flooding into a partial serial schedule; source inspection and baseline replay show separate old/new buffers.

## Resolution

- root_cause: The canonical numerical profile globally clips prior, projected, posterior, and V2C LLRs at ±25. Matched ablations show this policy causes most local nonconvergence relative to the supplied reference-style numeric path. The local hard-decision tie rule contributes additional failures in the clipped float64 profile. Exact presentation-code reproduction remains unresolved because original artifacts and reference package were not available.
- fix: No silent change to the canonical default. Added a reproducible reference-style diagnostic, controlled ablations, four-weight oracle, audited ledgers, and an implementation comparison report.
- verification: 16 audited arms, 12 paired contrasts, identical shot hashes; four-weight oracle correction agreement on four shots; production compiled baseline matches the diagnostic on 20 double-Gross shots; Q8 baseline matches 1200 prior ledger entries; presentation structural checks passed; 39 quaternary compiled/kernel/sampling tests passed; Python compilation and diff checks passed.
- files_changed: `from_dr_pfister_presentetations/diagnose_bp4_reference_gap.py`, `verify_reference_diagnostic.py`, `analyze_reference_gap.py`, `results/performance_investigation/REFERENCE_GAP_AUDIT.md`, run ledgers and audited CSV/plot, `README.md`, `results/performance_investigation/REPORT.md`.
