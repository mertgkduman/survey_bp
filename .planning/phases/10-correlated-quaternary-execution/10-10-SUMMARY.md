---
phase: 10-correlated-quaternary-execution
plan: "10"
subsystem: canonical-quaternary-asced
tags: [asced, css, splitter, canonical-adaptation, provenance, lineage]
requires:
  - phase: 10-02
    provides: immutable quaternary original and transform conventions
  - phase: 10-13
    provides: pinned native aSCED source identity and provenance limits
provides:
  - Deterministic bounded CSS splitter search with rank and detectability witnesses
  - Immutable GB46 canonical-adaptation splitter and extended-graph fixture
  - Receipt-bound aSCED materialization with path-count preflight and transform lineage
affects: [phase-10-plan-11, phase-10-plan-12, phase-10-plan-15, canonical-asced-execution]
tech-stack:
  added: []
  patterns: [lexicographic-bounded-search, constructed-receipt-binding, immutable-factor-graph-lineage]
key-files:
  created:
    - src/bp_registry/quaternary/asced.py
    - data/fixtures/quaternary/asced-gb46-canonical-fixture.json
    - tests/canonical/quaternary/test_asced_splitters.py
    - tests/canonical/quaternary/fixtures/asced-splitters.json
  modified:
    - src/bp_registry/quaternary/asced.py
    - data/fixtures/quaternary/asced-gb46-canonical-fixture.json
    - tests/canonical/quaternary/test_asced_splitters.py
key-decisions:
  - "GB46 H is a pinned source input; deterministic T and H_ext are project-generated canonical_adaptation evidence."
  - "The extended aSCED factor graph retains immutable-original transform/lift lineage without claiming its noncommuting splitter rows are a stabilizer code."
requirements-completed: [QBP-04]
plan_head_before: c832c8cc7d6e7cd44f8bc84e5359fbe7220e668a
commits: 4
actuals:
  tokens: 16406
  tasks: 2
  commits: 4
coverage:
  - id: D1
    description: Deterministic CSS splitter construction, bounded exhaustion, source-component provenance, and pinned-input GB46 canonical receipt.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_asced_splitters.py
        status: pass
    human_judgment: false
  - id: D2
    description: Receipt-bound immutable aSCED graph materialization with transform lineage and path-cap preflight.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_asced_splitters.py
        status: pass
    human_judgment: false
metrics:
  duration: 12m
  completed: 2026-10-07
status: complete
---

# Phase 10 Plan 10: Canonical CSS aSCED Splitters Summary

Deterministic canonical CSS splitter batches are fully qualified and materialized before sampling, with source input provenance separated from project-generated graph evidence.

## Accomplishments

- Added lexicographic, bounded X-then-Z splitter construction with explicit exhaustion, source-component IDs, rank growth, detectable-rank, row weight, and no-new-same-role-cycle checks.
- Parsed the exact pinned GB46 H input and froze its deterministic `Delta=2`, weight-four canonical adaptation receipt, including immutable T/H_ext bytes and typed `[H_X,T_X,H_Z,T_Z]` row order.
- Materialized only receipt-bound qualified batches, calculated `L * 2^Delta` before execution, and attached each noncommuting factor graph to the immutable original through certified transform and lift identities.

## Task Commits

1. **Task 1: Construct and independently qualify deterministic splitter batches**
   - `d6ce3b3` `test(10-10): add failing splitter construction contract`
   - `023cc5a` `feat(10-10): construct canonical CSS splitter batches`
2. **Task 2: Materialize stable batch graphs and transform lineage**
   - `d01ca6c` `test(10-10): add failing batch materialization contract`
   - `6511e1e` `feat(10-10): materialize qualified aSCED batch graphs`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_splitters.py -k 'construct or canonical_adaptation or source_component or constructed_receipt or gb46 or h_ext_digest or independent_constructor or immutable or exhausted or witness or rank or detectable or partition or css_type or weight or cycle or even_delta or hash or reject_author_bytes or non_css' -x` — 7 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_splitters.py -k 'materialize or constructed_receipt or canonical_gb46 or fidelity or source_component or reject_raw or reject_exhausted or immutable or batch or transform or lineage or stable_order or path_count or cap or tamper' -x` — 6 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py -x` — 35 passed.
- `python -m pytest tests/canonical/quaternary/test_asced_splitters.py -q` — 8 passed after the receipt correction.

## TDD Gate Compliance

- Task 1 RED evidence: `RED_EVIDENCE_OK` for `test_constructs_ordered_canonical_adaptation_splitters`; GREEN passed.
- Task 2 RED evidence: `RED_EVIDENCE_OK` for `test_materializes_preflighted_batches_with_stable_transform_lineage`; GREEN passed.

## Decisions Made

- The exact source input has a fixed raw SHA-256 and parser, while all generated splitters and extended rows retain the distinct `canonical_adaptation` run fidelity.
- The materialized graph is an `AscedWorkingGraph` rather than a `PauliCode`, because the required detectable-rank condition makes its appended affine constraints noncommuting.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Kept partial search checks separate from full-batch qualification**
   - **Found during:** Task 1
   - **Issue:** Applying the even-Delta full-batch gate to each candidate incorrectly exhausted every search on its first splitter.
   - **Fix:** Candidate admission now checks incremental rank and detectability; the full qualification still applies only after all requested rows exist.
   - **Files modified:** `src/bp_registry/quaternary/asced.py`
   - **Verification:** Splitter construction and exhaustion tests passed.

2. **[Rule 1 - Bug] Preserved noncommuting affine splitter graphs outside the stabilizer-code value**
   - **Found during:** Task 2
   - **Issue:** `PauliCode` correctly rejects noncommuting rows, while a qualified aSCED splitter requires nonzero `T Lambda H^T`.
   - **Fix:** Added immutable `AscedWorkingGraph` with the same original-parent and transform/lift evidence, without misrepresenting it as a stabilizer code.
   - **Files modified:** `src/bp_registry/quaternary/asced.py`
   - **Verification:** Materialization, tamper, path-cap, and GB46 tests passed.

## Postcompletion Correction

- Corrected `SplitterSearchReceipt.candidates_examined` to record the number of candidates actually inspected: accepted candidates record `candidate_ordinal + 1`, and exhausted searches record `min(attempt_cap, math.comb(n, row_weight))` without materializing the combination space.
- Hardened materialization by checking the receipt hash, source artifact and component identities, profile hash, search totals, rejection tallies, accepted ordinals, and the deterministic reconstructed search before exposing a working graph.
- Regenerated the project-owned GB46 fixture with its receipt witness: X accepts ordinal 35 after 36 candidates; Z accepts ordinal 1937 after 1938 candidates.

## Known Stubs

None.

## Next Phase Readiness

Plan 10-11 can consume closed, receipt-bound batches without regenerating graph rows during a shot. Native aSCED remains pending the separate human decision in Plan 10-14; this plan did not build or execute native code.

## Self-Check: PASSED

All four task commits and all declared source, fixture, and test files are present.
