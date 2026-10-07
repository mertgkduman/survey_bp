---
phase: 10-correlated-quaternary-execution
plan: "12"
subsystem: quaternary decoder execution
tags: [asced, css, bp4, mbp4, replay, event-ledger]
requires:
  - phase: 10-10
    provides: verified constructed CSS splitter batches
  - phase: 10-11
    provides: verified constructed overcomplete maps
provides:
  - Complete CSS aSCED all-path controller with original-space selection
  - Public aSCED execution, evidence ledger, and deterministic replay
affects: [phase-10-native-aSCED-evidence, phase-11]
actuals:
  tokens: 11711
  tasks: 2
  commits: 6
plan_head_before: 57340f5e3b09206fdc6fc6eee11febd0cffc08f7
tech-stack:
  added: []
  patterns: [receipt-bound transformed decoder sessions, LSB virtual-path evidence, original-syndrome candidate selection]
key-files:
  created: [tests/canonical/quaternary/test_asced_ensemble.py]
  modified: [src/bp_registry/quaternary/asced.py, src/bp_registry/quaternary/execution.py, src/bp_registry/runner.py]
key-decisions:
  - "Execute every L*2^Delta path in stable LSB order before original-space selection."
  - "Treat verified constructed splitter/map artifacts and stable ties as canonical_adaptation even with source-backed paper components."
requirements-completed: [QBP-04]
coverage:
  - id: D1
    description: All-path CSS aSCED decoding, original-syndrome selection, and receipt-bound overcomplete paths.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: tests/canonical/quaternary/test_asced_ensemble.py
        status: pass
    human_judgment: false
  - id: D2
    description: Public CSS aSCED preflight, event ledger, and deterministic replay.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: tests/canonical/quaternary/test_public_execution.py#test_public_css_asced_preflights_runs_all_paths_and_replays
        status: pass
    human_judgment: false
duration: 11m
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 12: Complete CSS aSCED Execution Summary

**A receipt-bound canonical CSS aSCED controller executes every LSB-ordered virtual path, selects only original-syndrome-valid minimum-weight candidates, and persists replayable public evidence.**

## Performance

- **Duration:** 11m
- **Started:** 2026-10-07T20:14:15Z
- **Completed:** 2026-10-07T20:25:19Z
- **Tasks:** 2
- **Files modified:** 7
- **Verification:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` — 151 passed

## Accomplishments

- Added `AscedController`, immutable per-path evidence, exhaustive LSB-first path enumeration, dual validity checks, stable batch/path tie selection, type-I terminal, and deterministic controller replay.
- Bound overcomplete sessions to Plan 10-10's verified `QualifiedAscedBatch` plus Plan 10-11's typed constructed map receipt; comparison-only maps are rejected.
- Added public CSS aSCED preflight, bounded all-path work, complete ledger events, canonical-adaptation fidelity, and exact public replay verification.

## Task Commits

1. **Task 1: Run all CSS aSCED paths and select by the paper rule** — `680eeee` (RED), `dda8f9a` (GREEN)
2. **Task 2: Execute and independently replay aSCED publicly** — `c1f777f` (RED), `da8621d` (GREEN)

The measured ledger contains 6 commits because Plan 10-11's concurrent hardening commits (`9968ea3`, `d0432ce`) landed after this plan's recorded base; the four commits above are Plan 10-12's task commits.

## Files Created/Modified

- `src/bp_registry/quaternary/asced.py` — all-path controller, exact map binding, work/selection evidence, replay.
- `src/bp_registry/quaternary/kernel.py` and `src/bp_registry/quaternary/mbp4.py` — accept certified immutable noncommuting aSCED graphs for fresh decoder sessions.
- `src/bp_registry/quaternary/execution.py` and `src/bp_registry/runner.py` — public CSS aSCED execution and deterministic verification.
- `src/bp_registry/quaternary/compatibility.py` — CSS-only aSCED fidelity resolution.
- `tests/canonical/quaternary/test_asced_ensemble.py` and `tests/canonical/quaternary/test_public_execution.py` — controller, receipt, public, non-CSS, and replay tests.

## Decisions Made

- Virtual syndrome integers persist least-significant-bit-first vectors, partitioned as `g_X` then `g_Z` in `[s_X,g_X,s_Z,g_Z]` order.
- Extended validity remains path evidence; only original-syndrome validity admits a candidate to selection.
- The enclosing execution is `canonical_adaptation` because deterministic construction and the stable tie interpretation are project-owned.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Made fresh BP4/MBP4 sessions accept certified aSCED working graphs**
- **Found during:** Task 1
- **Issue:** Existing sessions accepted only commuting stabilizer `QuaternaryOriginalProblem` instances, while the qualified aSCED augmented graph intentionally has noncommuting splitter rows.
- **Fix:** Added a narrow immutable `checks/syndrome/n` structural admission gate; ordinary original-problem execution remains unchanged.
- **Files modified:** `src/bp_registry/quaternary/kernel.py`, `src/bp_registry/quaternary/mbp4.py`
- **Verification:** Focused controller plus kernel/MBP4 tests and the full quaternary suite passed.
- **Committed in:** `dda8f9a`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to execute fresh canonical sessions on the plan's certified transformed graph; no new dependency or native execution was introduced.

## Known Stubs

None.

## Next Phase Readiness

The canonical all-path CSS aSCED engine, public contract, and replay evidence are ready for bounded native/mechanism evidence. Native code was not built or executed.

## Self-Check: PASSED

- Found all task commits and the aSCED controller/public test files.
