---
phase: 11-quaternary-reproduction-and-comparisons
plan: "04"
subsystem: native-source-evidence
tags: [asced, native, injected-errors, provenance, source-diff, review-only]
requires:
  - phase: 10-correlated-quaternary-execution
    provides: pinned aSCED source, isolated build receipt, and aggregate-only native result
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "01"
    provides: source-fidelity target and blocked-evidence conventions
provides:
  - Read-only proof that the pinned aSCED pybind interface cannot accept matched injected Pauli errors
  - Digest-bound, unapplied injected-error source diff and authorization package
affects: [phase-11-native-qualification, quaternary-reproduction, controlled-comparisons]
tech-stack:
  added: []
  patterns: [read-only external-source qualification, review-only derivative receipt, patch-digest binding]
key-files:
  created:
    - scripts/qualify_phase11_native_asced.py
    - data/native/phase11-asced-injected-input-proposal.json
    - data/native/phase11-asced-injected-input-diff.patch
    - tests/canonical/quaternary/test_phase11_native_asced.py
  modified: []
key-decisions:
  - "The retained Phase 10 aggregate is evidence of an unchanged native build/run only; it cannot supply a per-shot matched-input identity."
  - "The proposed bypass is an unapplied three-file diff that preserves the syndrome, decode, and evaluation sequence while requiring separate rights and derivative-identity approval."
patterns-established:
  - "External source qualifications verify exact checkout and receipt bytes before emitting review artifacts."
  - "Derivative proposals bind before/after file hashes and diff bytes while leaving source, build, run, and fidelity authorization false."
requirements-completed: [QEV-01]
actuals:
  tokens: 8053
  tasks: 2
  commits: 4
plan_head_before: 107fa4101230c2e3bbf415fe5dbc02386330fa68
coverage:
  - id: D1
    description: "Read-only qualification proves the current native binding samples internally and exposes no injected-error pybind entrypoint."
    requirement: QEV-01
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_phase11_native_asced.py#test_tracer_current_unavailable_is_read_only_and_aggregate_only
        status: pass
    human_judgment: false
  - id: D2
    description: "A digest-bound unapplied patch records narrow injected-input changes, translation round trips, source discrepancies, and authorization requirements."
    requirement: QEV-01
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_phase11_native_asced.py#test_proposal_checked_in_review_package_is_an_unapplied_validated_derivative
        status: pass
    human_judgment: false
duration: 17m
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 04: Native aSCED Matched-Input Qualification Summary

**A read-only qualification records that pinned native aSCED cannot consume matched Pauli errors, with a digest-bound three-file review patch that grants no derivative authority.**

## Performance

- **Duration:** 17m
- **Started:** 2026-10-14T20:10:23Z
- **Completed:** 2026-10-14T20:27:23Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added a read-only qualification command that verifies the exact native commit, protected source digests, retained build/run receipts, internal `simulate_trial` sampling, and absent injected-error pybind interface.
- Persisted the truthful `unavailable` boundary: the Phase 10 aggregate has no error vector, shot identity, seed, or paired outcome and cannot be promoted to matched evidence.
- Added an unapplied minimal diff that accepts a native-order Pauli vector only after initialization, bypasses sampling, retains the syndrome/decode/evaluation path, caps use to one worker, and binds all review bytes by SHA-256.
- Added tamper, drift, translation, downstream-scope, aggregate-only, and authorization regressions.

## Task Commits

1. **Task 1: Prove current native matched-input unavailability** — `788020f` (test, RED) and `eedd0eb` (feat)
2. **Task 2: Generate an unapplied minimal injected-error diff and review package** — `62f0f88` (test, RED) and `8e93bad` (feat)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'tracer or current_unavailable or pinned or aggregate_only or no_execution or tamper' -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'proposal or diff_scope or translation or vector_digest or unchanged_downstream or authorization_required' -x` — passed (4 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -x` — passed (6 tests).
- `qualify_phase11_native_asced.py inspect` — reports `matched_input_status: unavailable` and every build/run authorization field as `false`.
- `qualify_phase11_native_asced.py verify-proposal` — reports `review_only_valid` and `execution_authorized: false`.

## Decisions Made

- The current source state remains `unavailable` for native/canonical same-error pairs. The aggregate result stays aggregate-only even though the pinned build succeeded.
- The review package names no derivative source, build, or run identity and cannot be applied, compiled, or executed as an authorization mechanism.
- The patch retains the native `I,X,Z,Y` ordering, requires recorded translation round trips and an injected-vector digest before any later approved execution, and leaves splitter randomness plus selection discrepancy explicit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Scoped diff validation to changed lines**

- **Found during:** Task 2 review-package verification.
- **Issue:** The first validator rejected unchanged unified-diff context mentioning `get_error_rates` as an aggregate-entrypoint modification.
- **Fix:** It now checks forbidden symbols only in added or removed patch lines.
- **Files modified:** `scripts/qualify_phase11_native_asced.py`
- **Verification:** Proposal verification and all six dedicated tests pass.
- **Committed in:** `8e93bad`

**Total deviations:** 1 auto-fixed Rule 1 issue.

## Known Stubs

None. The null derivative identities and missing vector digest are intentional authorization gates in a no-execution proposal, not runtime placeholders.

## Next Phase Readiness

Plan 11-05 must obtain a human decision on rights, source semantics, and derivative identity before anyone applies the patch, builds the derivative, or records a native matched shot. Native splitter randomness and selection differences remain explicit fidelity discrepancies.

## Self-Check: PASSED

- Confirmed all four task artifacts exist.
- Confirmed task commits `788020f`, `eedd0eb`, `62f0f88`, and `8e93bad` exist in Git history.
