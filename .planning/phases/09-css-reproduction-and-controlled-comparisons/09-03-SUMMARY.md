---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "03"
subsystem: literature-source-qualification
tags: [css, provenance, qualification, canonical-adaptation]
requires:
  - phase: 09-css-reproduction-and-controlled-comparisons
    plan: "02"
    provides: Yao and Rabeti target receipts
provides:
  - Bhatnagar unavailable-author-artifact qualification receipt
  - deterministic fourteen-variant source qualification inventory
affects: [EVAL-01, EVAL-02]
tech-stack:
  added: []
  patterns: [digest-bound receipt, monotone evidence states, deterministic compilation]
key-files:
  created:
    - literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/source-qualification-v1.json
  modified:
    - literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/PAPER.md
    - literature_policies/qualification-v1.json
    - src/bp_registry/literature.py
    - tests/test_phase9_source_qualification.py
key-decisions:
  - "Bhatnagar author data and implementation remain unavailable or unverified to this workspace, with a later content-addressed admission route."
  - "The Rabeti planning digest and observed live-byte digest remain distinct; their discrepancy blocks qualification."
  - "Every selected source and runnable variant remains a canonical adaptation and is ineligible for source-faithful assessment while prerequisites are unresolved."
actuals:
  tokens: 18462
  tasks: 2
  commits: 2
plan_head_before: 440a7db3643baba370ea7fce1c385a498c2eeec2
duration: 16m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 03: CSS Source Qualification Inventory Summary

**A deterministic inventory keeps all fourteen selected CSS variants visible while preserving missing author evidence and the Rabeti source-byte discrepancy as blockers.**

## Accomplishments

- Added the Bhatnagar receipt for the pinned paper and embedded Figure 5 vector bytes, explicit author-data and implementation unavailability, target-extraction block, later author-artifact requirements, and unperformed two-pass digitization route.
- Updated the Bhatnagar paper record to link the receipt and retain `first-convergence-0.toml` as a canonical adaptation.
- Added `qualify_phase9_source_inventory()`, which validates all approved source-spec digests and paper receipts, rejects duplicate identities or tampered inputs, and emits the checked-in sorted registry.
- Rebuilt `qualification-v1.json` with explicit target, native, source-execution, runnable-counterpart, assessment, and blocker states for every selected variant.
- Retained the Rabeti live archive SHA-256 `7b19e17fb1ffe04c3e61aef38d02967715cba84e568667206bce2a525a79928f` mismatch as `live_source_digest_discrepancy_unresolved`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'bhatnagar and unavailable' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'inventory or fourteen or monotone or faithful or tamper' -x` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -x` — 4 passed.
- Recompiled the inventory twice and compared both outputs with `qualification-v1.json` byte for byte — passed.

## Task Commits

1. **Task 1: Retain Bhatnagar's unavailable external evidence without inventing a curve**
   - `0a49c99` `feat(09-03): record Bhatnagar source qualification`
2. **Task 2: Compile the complete selected variant inventory with monotone evidence states**
   - `897ec8d` `feat(09-03): compile CSS qualification inventory`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Evidence integrity] Preserved the live Rabeti archive digest discrepancy in every derived record.**
- **Found during:** Task 2 receipt compilation.
- **Issue:** The qualification receipt contains the live source snapshot SHA-256 `7b19e17fb1ffe04c3e61aef38d02967715cba84e568667206bce2a525a79928f`, which differs from the approved planning pin.
- **Fix:** The compiler validates both facts and adds `live_source_digest_discrepancy_unresolved`; no source-faithful state can result.
- **Files modified:** `src/bp_registry/literature.py`, `literature_policies/qualification-v1.json`.
- **Commit:** `897ec8d`.

## Known Stubs

None.

## Self-Check: PASSED

- Found the Bhatnagar receipt, compiled inventory, compiler, and focused tests.
- Found both task commits in repository history.
