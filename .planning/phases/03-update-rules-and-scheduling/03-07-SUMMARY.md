---
phase: 03-update-rules-and-scheduling
plan: "07"
subsystem: css-artifacts
tags: [css, qldpc, generalized-hypergraph-product, gallager, provenance, npz]
requires:
  - phase: 01-foundation-and-evidence
    provides: CSS algebra, artifact identity, and source-evidence conventions
provides:
  - Exact source-derived B1 [[882,24]] CSS artifact with deterministic project logicals
  - Fixed-seed Gallager (3,4) HGP [[225,29]] pilot artifact
  - Confined, bounded NPZ loading and a non-substitutive pilot inventory
affects: [phase-03-experiments, reproduction-manifests, decoder-comparisons]
actuals:
  tokens: 11015
  tasks: 3
  commits: 6
plan_head_before: 2169218bd675b39eb2c2c3667960164e0242dc8a
tech-stack:
  added: []
  patterns:
    - Deterministic GF(2) quotient-derived logical bases for explicitly labelled project artifacts
    - Hash-pinned, pickle-free NPZ archives under a confined artifact root
key-files:
  created:
    - data/artifacts/b1-panteleev-kalachev-v3.json
    - data/artifacts/b1-panteleev-kalachev-v3.npz
    - data/artifacts/hgp-gallager-3-4-seed-20260923.json
    - data/artifacts/hgp-gallager-3-4-seed-20260923.npz
    - tests/test_phase3_codes.py
  modified:
    - src/bp_registry/code_constructions.py
    - data/evidence/code-inventory.json
    - tests/test_source_artifact.py
key-decisions:
  - "B1 check matrices are source-derived; its ordered logical basis is explicitly project-derived."
  - "The PCG64-seeded Gallager HGP is a disclosed generated-family pilot, not an author instance or reproduction."
  - "C2 remains unresolved and cannot be substituted by another HGP-family artifact."
patterns-established:
  - "Frozen binary CSS artifacts use deterministic ZIP metadata and verify raw and semantic identities."
  - "Artifact boundaries reject path escapes, symlinks, oversized archives, unexpected members, and non-uint8 arrays."
requirements-completed: [UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05]
coverage:
  - id: D1
    description: "Exact B1 CSS construction and frozen artifact with source provenance and project logicals"
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py -k 'b1 or gallager or hgp'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fixed PCG64 Gallager (3,4) HGP pilot with deterministic constituent, ranks, and archive bytes"
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py -k 'b1 or gallager or hgp'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Inventory registers Gross, B1, and generated HGP separately while retaining the C2 non-substitution boundary"
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/test_source_artifact.py tests/test_css_small.py"
        status: pass
    human_judgment: false
duration: 12 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 07: Exact CSS Pilot Artifacts Summary

**Source-traced B1 and seeded Gallager-HGP CSS pilots are frozen as deterministic, safely loadable artifacts without overstating their provenance.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-24T09:13:59Z
- **Completed:** 2026-09-24T09:25:53Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Expanded the Panteleev--Kalachev Appendix-B B1 construction into a hash-pinned [[882,24]] CSS artifact with source-derived checks and project-derived paired logicals.
- Generated and froze a PCG64-seeded Gallager (3,4) constituent and its [[225,29]] HGP pilot, including the exact draw permutations and an explicit non-author-instance label.
- Added bounded, confined, pickle-free NPZ loading; registered Gross, B1, and the generated HGP distinctly; and retained C2 as an unresolved non-substitution case.

## Task Commits

Each task was committed atomically through RED/GREEN task commits:

1. **Task 1: Freeze exact B1 CSS artifact** — `9ba8873` (test), `a045d2d` (feat)
2. **Task 2: Freeze Gallager HGP pilot adaptation** — `7c39b41` (test), `1a9227b` (feat)
3. **Task 3: Register pilot artifacts and inventory boundary** — `a2d2977` (test), `6c0a423` (feat)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py -k 'b1 or gallager or hgp'` — **3 passed**
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/test_source_artifact.py tests/test_css_small.py` — **17 passed**
- `git diff --check` — **passed**

## Files Created/Modified

- `src/bp_registry/code_constructions.py` — deterministic B1/Gallager/HGP construction, logical derivation, replayable writing, and bounded NPZ loading.
- `data/artifacts/b1-panteleev-kalachev-v3.{json,npz}` — source-traced B1 identity and frozen arrays.
- `data/artifacts/hgp-gallager-3-4-seed-20260923.{json,npz}` — disclosed seeded HGP adaptation and frozen arrays.
- `data/evidence/code-inventory.json` — provenance-aware inventory of all pilot candidates.
- `tests/test_phase3_codes.py` and `tests/test_source_artifact.py` — algebra, provenance, boundary, and byte-regeneration coverage.

## Decisions Made

- Kept the B1 check matrix provenance separate from its deterministic project logical basis, rather than claiming author-provided logical ordering.
- Used one fully recorded PCG64 seed and permutation sequence for the Gallager HGP pilot; it is not represented as an author code instance.
- Preserved C2's unresolved identity gate, so a same-family HGP pilot cannot silently replace it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added a safe NPZ artifact boundary**
- **Found during:** Task 3
- **Issue:** The existing project artifact loader accepted JSON only, while this plan requires binary NPZ artifacts to load through the project boundary with the stated safety properties.
- **Fix:** Added confined-root, symlink/path-escape, size, ZIP-member, uint8-dtype, raw-hash, semantic-hash, and `allow_pickle=False` checks before CSS validation.
- **Files modified:** `src/bp_registry/code_constructions.py`
- **Verification:** Full Phase 3 artifact suite passed.
- **Committed in:** `6c0a423`

**2. [Rule 1 - Bug] Updated the legacy fixed inventory assertion**
- **Found during:** Task 3
- **Issue:** The older source-artifact test asserted the pre-plan three-candidate inventory, so it rejected the required B1 and HGP registrations.
- **Fix:** Updated the assertion to validate the four provenance-distinct candidates and the generated-pilot boundary.
- **Files modified:** `tests/test_source_artifact.py`
- **Verification:** Full Phase 3 artifact suite passed.
- **Committed in:** `6c0a423`

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1).
**Impact on plan:** Both changes are necessary for the plan's binary-artifact safety and inventory acceptance criteria; neither expands the decoder architecture.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The B1 and generated-HGP inputs have reproducible matrices, logical conventions, identity hashes, and provenance labels for policy/scheduling experiments. Source-faithful C2 reproduction remains intentionally blocked by its unresolved artifact identity.

## Self-Check: PASSED

- All eight plan files exist and all six task commits are present in the worktree history.
- No stubs, skipped tests, unrun verification, or unplanned security surface remain.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
