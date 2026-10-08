---
phase: 10-correlated-quaternary-execution
plan: "15"
subsystem: native-aSCED-qualification
tags: [asced, native-reference, cmake, provenance, quaternary]
requires:
  - phase: 10-14
    provides: Exact source-spec approval and verbal collaborator-author permission for the bounded isolated build/run
provides:
  - Exact isolated native aSCED build and import receipt
  - Bounded GB46 native aggregate terminal with qualified missingness
  - Tested I/X/Y/Z to I/X/Z/Y native translation boundary
affects: [phase-10-plan-16, quaternary-native-evidence]
tech-stack:
  added: [isolated CPython 3.12 build environment, Kitware CMake 4.2.0]
  patterns: [digest-bound native receipts, isolated native aggregate adapter, source-qualified missingness]
key-files:
  created: [src/bp_registry/quaternary/native_asced.py, data/native/phase10-asced-build-receipt.json, data/native/phase10-asced-run-receipt.json]
  modified: [scripts/qualify_phase10_native_asced.py, tests/canonical/quaternary/test_asced_evidence.py]
key-decisions:
  - "Accept the Plan 10-14 user attestation of verbal collaborator-author permission for this bounded isolated build and run; no formal license or written grant is claimed."
  - "Keep native aggregate output distinct from canonical execution and retain unavailable seed, shot, path, edge-work, and control-flow facts."
  - "Record the compiler and source-declared transitive nlohmann/json header digest in the build receipt."
requirements-completed: [QBP-04]
plan_head_before: b618b59cdcf73ece850577944b65a40c51d18edb
actuals:
  tokens: 15232
  tasks: 2
  commits: 5
metrics:
  duration: 22m
  completed: 2026-10-08
status: complete
coverage:
  - id: D1
    description: Exact approved kit-cel native source builds and imports in the disposable environment with receipt verification.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: "scripts/qualify_phase10_native_asced.py build + verify-receipt --require-terminal build_success"
        status: pass
    human_judgment: false
  - id: D2
    description: Bounded GB46 native aSCED aggregate probe succeeds with native Pauli translation and explicit unavailable observability.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: "scripts/qualify_phase10_native_asced.py run + verify-receipt --require-terminal native_success"
        status: pass
      - kind: unit
        ref: "tests/canonical/quaternary/test_asced_evidence.py"
        status: pass
    human_judgment: false
---

# Phase 10 Plan 15: Native aSCED Build and Terminal Summary

**The approved kit-cel native aSCED commit built in isolation and produced a bounded GB46 aggregate native terminal.**

## Performance

- **Duration:** 22m
- **Started:** 2026-10-07T23:46:23Z
- **Completed:** 2026-10-08T00:08:06Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Verified the Plan 10-14 approval signal and immutable source-spec SHA-256 before cloning exact commit `816772071486615dfc7d71d1e15df597edc58a26` into `/tmp/phase10-asced-native`.
- Built and imported the native extension using the approved locked wheels, pybind11 overlay, Kitware CMake executable, serial compiler invocation, and before/after source guards. The build receipt records the C++ compiler and the observed source-declared `nlohmann/json` header digest.
- Ran one GB46 native aSCED aggregate probe at physical error rate 0.05 with one worker, `max_trials=10000`, and `target_errors=10`. It terminated at 160 trials with 10 logical errors; it remains `not_assessed`.
- Preserved the native I/X/Z/Y representation, equal X/Y/Z channel proportions, native/canonical separation, and explicit missingness for unexposed per-shot and internal counters.

## Task Commits

1. **Task 1: Build the approved exact native source in isolation** — `9c34e80`, `a275ee3`
2. **Task 2: Invoke the bounded native reference to a required successful terminal** — `9cb1383`, `087da83`
3. **Provenance completion** — `d9225bd`

## Verification

- `pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'native_run or exact_terminal or equal_proportion or pauli_translation or aggregate or missingness or unavailable or not_assessed or receipt_chain' -x` — 2 passed.
- `qualify_phase10_native_asced.py verify-receipt ... --require-terminal build_success` — passed.
- `qualify_phase10_native_asced.py verify-receipt ... --require-terminal native_success` — passed.
- `docs/environment-freeze.txt` SHA-256 remained `adff1f54bb2f574a9eec84fc71ff16720d8e29b0051818484612b29c541a7cd4`.

## Decisions Made

- Recorded the user-attested verbal collaborator-author permission accurately as the bounded execution authority. This does not claim a formal license, written grant, or redistribution right.
- Used only native aggregate observations as native evidence. No canonical result substitutes for a native output, and missing native instrumentation remains unavailable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical provenance] Added explicit compiler and source-declared transitive build-input evidence.**
- **Found during:** Task 2
- **Issue:** The initial successful receipt contained the compiler only in CMake output and did not explicitly retain the materialized `nlohmann/json` header digest.
- **Fix:** Recorded the compiler path/version and the source-declared `nlohmann/json` header SHA-256, then rebuilt and reran the linked native probe.
- **Files modified:** `scripts/qualify_phase10_native_asced.py`, `tests/canonical/quaternary/test_asced_evidence.py`, native receipts
- **Verification:** Rebuilt successfully and independently verified both receipts.
- **Committed in:** `d9225bd`

**Total deviations:** 1 auto-fixed (Rule 2).

## Known Stubs

None. The deliberately unavailable native observability fields are typed evidence facts, not placeholders.

## Next Phase Readiness

Plan 10-16 can consume independently verified native build/run receipts. The native terminal is aggregate evidence only and must remain separate from canonical or shot-matched comparisons.

## Self-Check: PASSED

All five task artifacts exist and all five task commits are present in Git history.
