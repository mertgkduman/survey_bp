---
phase: 01-evidence-registry-and-native-css-baseline
plan: 08
subsystem: research-artifacts
tags: [css, bivariate-bicycle, gf2, provenance, bposd]
requires:
  - phase: 01-04
    provides: CSS algebra and immutable artifact loading contracts
  - phase: 01-06
    provides: source-linked evidence records
provides:
  - Pinned Bravyi BB-144 CSS matrices and an ordered paired logical basis
  - Candidate inventory distinguishing B1 lifted product, C2 HGP, and Gross BB
  - Reproducible source probe and raw/semantic artifact identities
affects: [01-09, native-css-pilot, manifests]
actuals:
  tokens: 19382
  tasks: 2
  commits: 3
plan_head_before: 7a3c1a9d660fc2ba71bd6f09e62a4ac89c82ee7d
tech-stack:
  added: []
  patterns:
    - Read pinned source construction without importing its side-effecting simulation program
    - Retain provider logical row identity while explicitly normalizing an ordered paired basis
key-files:
  created:
    - tools/freeze_css_source.py
    - data/evidence/code-inventory.json
    - data/artifacts/selected-css.json
    - data/artifacts/selected-css.provenance.json
    - docs/phase1-source-decisions.md
    - tests/test_source_artifact.py
  modified: []
key-decisions:
  - "Selected Gross/BB-144 from Bravyi commit fa77e3333d3ec44c79d8f914dd24c040d1da471b after independent source and GF(2) checks."
  - "Treat BB-144 as a pilot adaptation because its construction source is circuit-level BP-OSD while the linked impulse result is code-capacity."
requirements-completed: [CSS-01, CSS-02, REG-02, REG-03, MAP-03]
coverage:
  - id: D1
    description: Pinned Gross source construction, frozen rows, and independent CSS algebra
    requirement: CSS-01
    verification:
      - kind: unit
        ref: tests/test_source_artifact.py#test_selected_artifact_regenerates_pinned_rows_and_independent_algebra
        status: pass
    human_judgment: false
  - id: D2
    description: Candidate inventory and D-04 source selection rationale
    requirement: MAP-03
    verification:
      - kind: unit
        ref: tests/test_source_artifact.py#test_inventory_distinguishes_b1_c2_and_gross_and_records_d04_gate
        status: pass
    human_judgment: false
duration: 40min
completed: 2026-09-22
status: complete
---

# Phase 01 Plan 08: CSS Source Artifact Selection Summary

**Pinned Bravyi BB-144 matrices and ordered paired logicals with independent GF(2), source-file, raw-byte, and semantic identity checks.**

## Performance

- **Duration:** 40min
- **Started:** 2026-09-22T01:39:33Z
- **Completed:** 2026-09-22T02:19:33Z
- **Tasks:** 2/2
- **Files modified:** 6
- **Verification:** `python -m pytest -q tests/test_source_artifact.py tests/test_css_small.py` — 12 passed

## Accomplishments

- Recorded separate B1 lifted-product, BPGD C2 HGP, and Gross/BB-144 candidates with paper relations, source gaps, and D-04 ranking evidence.
- Probed Bravyi's clean `fa77e3333d3ec44c79d8f914dd24c040d1da471b` checkout without executing its circuit-generation program, then froze the Gross `Hx`, `Hz`, `Lx`, and ordered paired `Lz` rows.
- Saved actual artifact raw SHA-256 `2c02a3b99bf7267acf35efe28e0a2ef0d3827e5a22b948d53da14ae8df68ceb0` and semantic SHA-256 `e175e67c0f9ae6f4e0968461ad2f87ba38ad5344166b793c53dd038976d4f427` with source and logical-provider fingerprints.

## Task Commits

1. **Task 1: Compare candidate source and artifact completeness** — `01475a8` (feat)
2. **Task 2 RED: Freeze and independently verify selected matrices and logicals** — `20d941d` (test)
3. **Task 2 GREEN: Freeze and independently verify selected matrices and logicals** — `9b43b34` (feat)

## Files Created

- `tools/freeze_css_source.py` — validates the clean pinned source, reconstructs only the reviewed matrix recipe, and freezes an identity-bearing artifact.
- `data/evidence/code-inventory.json` — candidate identities, source evidence, rejection rationale, and selected Gross result.
- `data/artifacts/selected-css.json` and `data/artifacts/selected-css.provenance.json` — frozen matrices/logicals plus actual source, provider, raw, and semantic hashes.
- `docs/phase1-source-decisions.md` — D-03/D-04 decision record and pilot-adaptation boundary.
- `tests/test_source_artifact.py` — inventory, regeneration, independent algebra, and mutation-preflight checks.

## Decisions Made

- Gross/BB-144 won the D-04 gate because it alone supplied a complete pinned source construction and executable ordered-logical path; B1 and C2 remain documented, unpromoted source leads.
- Source Lx row order is retained. Source Lz rows are transformed by the inverse GF(2) pairing so the stored basis explicitly satisfies `Lx_i · Lz_j = δ_ij`; the source and paired row hashes preserve that lineage.
- The selection supports a disclosed pilot adaptation only. It does not establish a source-faithful decoder reproduction or statistical curve agreement.

## TDD Gate Compliance

- **RED:** `20d941d` added artifact tests; `pytest` failed on the missing selected artifact and provenance files.
- **GREEN:** `9b43b34` materialized the artifact using the pinned source recipe; the source-artifact and CSS suites passed.
- **REFACTOR:** No separate cleanup was needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test expectation] Updated the source-decision assertion after artifact promotion.**
- **Found during:** Task 2 verification
- **Issue:** The Task 1 report test still expected Gross's conditional pre-freeze wording after the verified selection was recorded.
- **Fix:** Asserted the final verified-selection wording while retaining the conditional-ranking section.
- **Files modified:** `tests/test_source_artifact.py`
- **Verification:** Source-artifact and CSS suites passed.
- **Committed in:** `9b43b34`

**Total deviations:** 1 auto-fixed.

## Issues Encountered

The requested main checkout initially pointed at protected `master`; the coordinator moved it to `gsd/phase-01-evidence-registry-native-css` before the first task commit. No project configuration was changed.

## Known Stubs

None.

## Next Phase Readiness

Plan 09 can reference `gross-bb-144` only through the frozen artifact and provenance identities. B1 and C2 remain inventory records until exact matrices and ordered logical bases are obtained.

## Self-Check: PASSED

- All six created task files exist.
- Task commits `01475a8`, `20d941d`, and `9b43b34` exist in git history.

*Phase: 01-evidence-registry-and-native-css-baseline*
*Completed: 2026-09-22*
