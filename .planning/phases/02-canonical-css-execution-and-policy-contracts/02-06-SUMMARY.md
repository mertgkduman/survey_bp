---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "06"
subsystem: native-and-canonical-metric-evidence
tags: [css, native-reference, metric-missingness, ledger, provenance]
requires:
  - phase: 02-04
    provides: qualified canonical work and runtime measurement facts
  - phase: 02-05
    provides: versioned canonical ledger evidence
provides:
  - strict observed-or-unavailable native metric facts
  - availability-preserving native ledger queries and summaries
  - explicit unavailable native evidence for error and interrupted terminals
affects: [controlled-comparisons, native-reproduction, evidence-querying]
tech-stack:
  added: []
  patterns: [tagged-missingness, qualified-native-observability, availability-only-aggregation]
key-files:
  created:
    - src/bp_registry/canonical/metrics.py
  modified:
    - src/bp_registry/reference.py
    - src/bp_registry/ledger.py
    - src/bp_registry/runner.py
    - src/bp_registry/cli.py
    - tests/test_reference_smoke.py
    - tests/test_ledger.py
key-decisions:
  - "ldpc.BpDecoder.iter is retained only as an observed public-SDK native-iteration fact and is not equated with canonical flooding work."
  - "Opaque native edge-update and control-flow counters are serialized as unavailable facts with a method, scope, unit, qualification, and reason."
patterns-established:
  - "Durable native metric summaries report observed and unavailable populations separately; they do not synthesize numeric totals from missing facts."
requirements-completed: [LED-04]
coverage:
  - id: D1
    description: "Native adapter exposes qualified observed iteration facts and explicit unavailable opaque internal counters."
    requirement: LED-04
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Terminal, reconciliation, summary, and result paths preserve typed missingness without coercing unavailable work to zero."
    requirement: LED-04
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py"
        status: pass
    human_judgment: false
metrics:
  duration: 8 min
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 7
status: complete
plan_head_before: 6775b748c14d2ac8f7fea510914e7f8f808c2aa3
commits: 4
actuals:
  tokens: 6689
  tasks: 2
  commits: 4
---

# Phase 02 Plan 06: Native Metric Missingness Summary

Native `ldpc.BpDecoder` evidence now records public iteration observations separately from unavailable opaque internal work, carrying that distinction through durable ledgers, queries, summaries, and pilot result serialization.

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-23T08:54:54Z
- **Completed:** 2026-09-23T09:02:31Z
- **Tasks:** 2
- **Files changed:** 7

## Accomplishments

1. Added strict `MetricFact` evidence with tagged observed/unavailable states, finite nonnegative observation validation, and mandatory missingness reasons.
2. Made native adapter results expose public-SDK iteration facts while preserving edge-message and control-flow counters as explicit unavailable evidence.
3. Added durable metric-envelope validation, availability-only summaries, result serialization, and repaired-terminal facts without reconstructing native internals.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py` → `18 passed`.

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` → `113 passed`.

## Task Commits

1. **Task 1: Type observed and unavailable metrics at the native boundary**
   - `539d7ee` test: native metric-fact contracts
   - `a115841` feat: qualified native metric evidence
2. **Task 2: Preserve native missingness through durable summaries**
   - `1824eb4` test: durable native metric contracts
   - `ad0c881` feat: persisted qualified native metric facts

## Decisions Made

- Native parallel iterations remain explicitly qualified SDK observations; they never stand in for canonical flooding sweeps or inferred edge work.
- Metrics with unavailable internal instrumentation are queryable evidence with null values and reasons, not zero-valued totals.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Wired typed native facts through runner and pilot result serialization**

- **Found during:** Task 2
- **Issue:** The listed ledger changes alone could not preserve native metric facts from the adapter into terminal rows and serialized pilot results.
- **Fix:** Passed typed facts through `runner.py` and exposed availability-only result evidence in `cli.py`, retaining legacy result compatibility when historical rows lack the new envelope.
- **Files modified:** `src/bp_registry/runner.py`, `src/bp_registry/cli.py`, `tests/test_reference_smoke.py`
- **Verification:** Targeted ledger/reference tests and full suite pass.
- **Committed in:** `ad0c881`

**2. [Rule 1 - Bug] Avoided ledger-to-canonical circular import during reconciliation**

- **Found during:** Task 2 full verification
- **Issue:** Importing the canonical metrics module at ledger import time re-entered canonical execution while `LedgerWriter` was only partially initialized, breaking spawned reconciliation workers.
- **Fix:** Deferred metric-module imports to strict conversion helpers, after ledger initialization is complete.
- **Files modified:** `src/bp_registry/ledger.py`
- **Verification:** Multiprocessing reconciliation and the full 113-test suite pass.
- **Committed in:** `ad0c881`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2).

## Known Stubs

None.

## TDD Gate Compliance

- Task 1 RED (`539d7ee`) and GREEN (`a115841`) committed in order; `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- Task 2 RED (`1824eb4`) and GREEN (`ad0c881`) committed in order; `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.

## Self-Check: PASSED

The metric module, all seven modified source/test artifacts, and task commits `539d7ee`, `a115841`, `1824eb4`, and `ad0c881` exist.

---
*Phase: 02-canonical-css-execution-and-policy-contracts*
*Completed: 2026-09-23*
