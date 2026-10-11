---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "02"
subsystem: literature-source-receipts
tags: [css, source-provenance, yao, rabeti, canonical-adaptation]
requires:
  - phase: 09-css-reproduction-and-controlled-comparisons
    plan: "01"
    provides: strict target and source-qualification receipt models
provides:
  - literal Yao Figure 3/Figure 6 target inventory
  - literal Rabeti Figure 5 target inventory
  - queryable source-identity and stopping gaps per selected target
affects: [EVAL-01, EVAL-02, CSS reproduction assessment]
tech-stack:
  added: []
  patterns: [literal-decimal receipts, locator-specific stopping evidence, canonical-adaptation labels]
key-files:
  created:
    - literature_policies/yao-2024-guided-decimation/paper_reproduction/source-targets-v1.json
    - literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/source-targets-v1.json
    - tests/test_phase9_source_receipts.py
  modified:
    - literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md
    - literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/PAPER.md
key-decisions:
  - "Figure 6 does not inherit Figure 3's 100-error stopping statement."
  - "The B1 candidate and both runnable policy files remain canonical adaptations because ordered paper identity and author implementation facts are unresolved."
  - "The Rabeti planning digest remains pinned while a changed live source-byte digest is retained as a qualification blocker."
requirements-completed: [EVAL-01, EVAL-02]
actuals:
  tokens: 11400
  tasks: 2
  commits: 4
plan_head_before: 17b6a8e2b9835e470698db336eed88816a338dad
duration: 19m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 02: Authored CSS Source Targets Summary

**Frozen Yao and Rabeti authored CSS coordinates preserve source precision, locator-specific stopping evidence, and every remaining source-identity gap.**

## Accomplishments

- Added 70 literal Yao targets for Figure 3 and Figure 6 and seven Rabeti Figure 5 targets, each with a point locator and half-last-digit rounding interval.
- Bound the approved Yao and Rabeti planning source digests, canonical policy digests, project-derived B1 status, native identity status, and unqualified source-experiment receipts.
- Kept Yao Figure 6 stopping explicitly unavailable; retained Figure 3 and Rabeti's observed 100-failure statements only at their source locators.
- Updated both paper records to link immutable receipts and describe runnable configurations as canonical adaptations.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_receipts.py -k 'yao and tracer' -x` — 2 passed, 3 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_receipts.py -k 'authored_coordinates or locator or stopping or identity_gap' -x` — 2 passed, 3 deselected.
- Full receipt module — 5 passed.
- Strict target and qualification models validated the serialized Yao and Rabeti receipt objects.

## Task Commits

1. **Task 1: Freeze the first Yao Figure 3 target with its unresolved experiment identity**
   - `69a9dfd` `test(09-02): add failing Yao source receipt coverage`
   - `92f1297` `feat(09-02): freeze Yao authored source targets`
2. **Task 2: Expand authored Yao and Rabeti target inventories without inheriting missing facts**
   - `62c0079` `test(09-02): cover full authored target inventories`
   - `adb1f88` `feat(09-02): freeze Rabeti authored source targets`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Evidence integrity] Kept a live Rabeti archive digest discrepancy explicit.**
- **Found during:** Task 2 source-byte verification.
- **Issue:** The live `arXiv:2605.14170v1` e-print stream hashed to `7b19e17fb1ffe04c3e61aef38d02967715cba84e568667206bce2a525a79928f`, while the planned immutable research pin is `467622e2f17f01d302d6c790b13078569f17d71cd83910558535019a594e07c1`.
- **Fix:** Retained the approved planning digest as the pinned target-receipt identity, retained the observed live-byte digest separately in model-validated source snapshots, and recorded reconciliation as a source-qualification blocker.
- **Files modified:** `literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/source-targets-v1.json`, `literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/PAPER.md`
- **Commit:** `adb1f88`

## Known Stubs

None.

## Self-Check: PASSED

- Found both receipt files, both PAPER records, and `tests/test_phase9_source_receipts.py`.
- Found all four task commits in repository history.
