---
phase: 10-correlated-quaternary-execution
plan: "11"
subsystem: canonical-quaternary-asced
tags: [asced, overcomplete, gf2, provenance, canonical-adaptation, tamper-checking]
requires:
  - phase: 10-10
    provides: receipt-bound canonical GB46 splitter graph and typed H_ext order
provides:
  - Qualified generic GF(2) overcomplete maps with H_oc=M H_ext and z_oc=M z_ext
  - Deterministic GB46 canonical-adaptation map with a 46-row identity prefix and two typed parity rows
  - Comparison-only identities for pinned GB46 and toric author artifacts
affects: [phase-10-plan-12, phase-10-plan-15, canonical-asced-execution]
tech-stack:
  added: []
  patterns: [typed-syndrome-segments, bounded-pair-search, receipt-bound-derived-map, comparison-only-source-fixtures]
key-files:
  created:
    - src/bp_registry/quaternary/asced_overcomplete.py
    - data/fixtures/quaternary/asced-gb46-canonical-overcomplete-map.json
    - tests/canonical/quaternary/fixtures/asced-overcomplete.json
  modified:
    - tests/canonical/quaternary/test_asced_overcomplete.py
key-decisions:
  - "Canonical GB46 overcomplete construction uses identity rows followed by the first valid X pair image and first valid Z pair image under a 1000-pair cap."
  - "The map accepts named [s_X,g_X,s_Z,g_Z] segments and binds their typed H_ext row order before applying M."
  - "Pinned author triplets remain digest-recorded comparison artifacts and cannot enter canonical execution."
  - "Canonical map construction admits only a reverified QualifiedAscedBatch, never caller-supplied graph bytes or a standalone receipt."
patterns-established:
  - "Derived check transforms retain full matrix, row-origin, construction, and qualification digests."
requirements-completed: [QBP-04]
plan_head_before: 331f6a348af670d9b24417433282087b84e0ded5
commits: 6
actuals:
  tokens: 24027
  tasks: 1
  commits: 6
coverage:
  - id: D1
    description: Qualified generic and canonical overcomplete maps preserve GF(2) check and syndrome relations with receipt-bound order.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_asced_overcomplete.py
        status: pass
    human_judgment: false
metrics:
  duration: 11m
  completed: 2026-10-07
status: complete
---

# Phase 10 Plan 11: Overcomplete aSCED Map Summary

Receipt-bound canonical GB46 overcomplete mapping with an identity-preserving GF(2) transform, typed syndrome assembly, and comparison-only source artifacts.

## Accomplishments

- Added immutable generic overcomplete-map qualification that rejects incompatible dimensions, rank loss, content tampering, implicit row order, and broken `H_oc=M H_ext` equations.
- Constructed the canonical GB46 map only after replaying the complete repaired Plan 10-10 `QualifiedAscedBatch`: a 46-row identity prefix followed by one deterministic X pair image and one deterministic Z pair image under the 1000-pair bound.
- Bound `M`, `H_oc`, the source `H_ext`, typed row-origin map, construction profile, and qualification into a `ConstructedOvercompleteReceipt`; all four Delta=2 virtual syndrome paths use named `[s_X,g_X,s_Z,g_Z]` assembly before `z_oc=M z_ext`.
- Recorded and independently audited pinned GB46 and toric author matrix identities as standalone comparison-only evidence. They are rejected from canonical syndrome mapping.

## Task Commits

1. **Task 1: Qualify and apply generic overcomplete aSCED mappings**
   - `ed49bcc` `test(10-11): add failing overcomplete map contract`
   - `b91f9bc` `feat(10-11): qualify canonical overcomplete aSCED maps`
   - `9968ea3` `fix(10-11): require verified splitter batches for canonical maps`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_overcomplete.py -k 'constructed_splitter_binding or exact_h_ext_digest or deterministic_nontrivial_m or search_order or search_cap or exhausted or constructed_map_receipt or matrix_relation or syndrome_mapping or all_virtual_bits or gf2 or rank or row_order or comparison_only or reject_unmatched_source_map or gb46 or toric or immutable or tamper' -x` — 8 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_overcomplete.py tests/canonical/quaternary/test_asced_splitters.py -x` — 16 passed.
- The exact pinned source checkout at `kit-cel/quantum_asced@816772071486615dfc7d71d1e15df597edc58a26` was read without build or execution; its GB46 and toric l0 source triplets each satisfied their standalone GF(2) matrix relation.

## TDD Gate Compliance

- RED evidence: `RED_EVIDENCE_OK` for `test_generic_matrix_relation_and_syndrome_mapping`.
- GREEN: the focused contract and full related splitter/overcomplete suites pass after the admission-boundary hardening.

## Decisions Made

- Retain all original extended observation bits by requiring `rank(M)=rows(H_ext)` and placing its identity block first.
- Make source comparison fixtures non-executable at the syndrome mapping boundary, preventing substitution into the canonical receipt chain.
- Replay the full splitter construction receipt and qualification at canonical-map admission so a matching H_ext digest alone cannot authorize execution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Closed the standalone-receipt canonical-map admission path**
- **Found during:** Postcompletion audit of Task 1.
- **Issue:** A caller could supply arbitrary H_ext, row-map, and a fabricated typed splitter receipt whose H_ext digest matched, bypassing the full splitter receipt, source identity, qualification, and search-witness checks.
- **Fix:** `construct_overcomplete_map` now accepts only `QualifiedAscedBatch` and invokes Plan 10-10's full `_verify_qualified_batch` gate before deriving any map input. Tests cover raw-object rejection, altered graph rows/order, and forged receipt digests.
- **Files modified:** `src/bp_registry/quaternary/asced_overcomplete.py`, `tests/canonical/quaternary/test_asced_overcomplete.py`, both overcomplete fixtures.
- **Verification:** Focused overcomplete suite: 8 passed; combined overcomplete/splitter suite: 16 passed.
- **Committed in:** `9968ea3`.

## Known Stubs

None.

## Next Phase Readiness

Plan 10-12 can require the exact constructed splitter/map receipt pair and build all decoder paths from the typed virtual-syndrome order. Its constructor call now supplies the full verified `QualifiedAscedBatch`.

## Self-Check: PASSED

All declared module, fixture, test, and canonical map receipt files exist. The three Task 1 commits are present.
