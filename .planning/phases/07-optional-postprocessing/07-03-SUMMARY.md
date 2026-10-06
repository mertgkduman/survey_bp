---
phase: 07-optional-postprocessing
plan: "03"
subsystem: standalone OSD qualification
tags: [postprocessing, osd, qualification, isolation, fail-closed]
requires:
  - phase: 07-01
    provides: canonical failed-BP handoff contract
  - phase: 07-02
    provides: human approval of the exact standalone OSD source and isolated build boundary
provides:
  - Exact-source isolated build/API/fixture receipt with a fail-closed non-admission disposition
  - Reproducible qualification command that leaves the primary ldpc environment unchanged
affects: [07-03-task-2, POST-01, phase-07-optional-postprocessing]
tech-stack:
  added: []
  patterns: ["Receipt-bound external admission fails closed when required native evidence is not exposed."]
key-files:
  created:
    - scripts/qualify_phase7_standalone_osd.py
    - data/qualifications/phase7-standalone-osd-baec4c8.json
  modified:
    - tests/canonical/test_postprocessing_osd.py
key-decisions:
  - "Do not admit the approved standalone OSD source because it exposes only OSD0 and final OSD-W output, not its higher-order candidate enumeration."
  - "Do not substitute or patch an OSD kernel; POST-01 remains blocked until an approved source/interface can retain the required candidate evidence."
requirements-completed: []
actuals:
  tokens: 5910
  tasks: 1
  commits: 2
plan_head_before: 5e3523ef063148c37d4638d69320fdcc8e037f81
commits: 2
metrics:
  duration: 31m
  completed: 2026-10-06
status: halted
---

# Phase 07 Plan 03: Standalone OSD Qualification Summary

The approved `standalone_osd` commit builds and decodes in a fresh isolated environment, but is deliberately not admitted because its Python API cannot expose the full higher-order candidate set required for canonical OSD evidence.

## Performance

- **Duration:** 31m
- **Tasks:** 1/2 reached the qualification gate; Task 2 was not started.
- **Files modified:** 5
- **Primary environment:** verified unchanged at `ldpc==2.4.1`.

## Accomplishments

- Cloned only `quantumgizmos/ldpc.git@baec4c8bfa2a679b0ba0e72df5582e277cd6918b`, built its wheel in a fresh virtual environment, and retained source-tree, wheel, compiler, dependency-freeze, API, and fixture evidence.
- Verified valid tiny-matrix outputs for full-rank, rank-deficient, and equal-weight inputs with `OSD_0`, `OSD_E`, and `OSD_CS`.
- Recorded a signed failed receipt because the approved API has `osd0_decoding` and `osdw_decoding` only; it does not expose the C++ `osd_candidate_strings` needed to retain every higher-order candidate and score.
- Added a regression test that prevents this receipt from being treated as runnable.

## Task Commits

1. **Task 1 RED: qualification receipt contract** — `cfe5525` (`test`)
2. **Task 1 fail-closed qualification evidence** — `44d5aec` (`chore`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_osd.py -x` — **1 passed**.
- `.venv/bin/python -m py_compile scripts/qualify_phase7_standalone_osd.py` — **passed**.
- Qualification command exited **2**, as designed for a failed receipt, after isolated build/API/fixture probes.
- Receipt digest recomputation passed; its disposition is `failed` and `runnable` is `false`.
- The primary interpreter still reports `ldpc==2.4.1`.

## TDD Gate Compliance

- **RED:** passed and committed in `cfe5525`; the named receipt-admission assertion failed because no qualification receipt existed.
- **GREEN admission:** intentionally not performed. The exact approved source fails the required API gate, so implementing an adapter would violate the plan's fail-closed rule.

## Decisions Made

- The internal C++ vector `osd_candidate_strings` is not sufficient evidence by itself because the approved Cython/Python API does not expose it to the isolated worker.
- The receipt stays non-runnable even though the wheel builds and its returned final candidates satisfy the tiny syndrome fixtures. Buildability and one final output do not establish the complete candidate provenance required by D-06/D-08.

## Deviations from Plan

None - the plan explicitly requires a failed build/API/differential qualification to block runnable admission without a substituted OSD kernel.

## Issues Encountered

The first fresh isolated build lacked the source-declared `setuptools>=68.2.2` backend requirement. The qualifier now installs that declared build prerequisite only inside its disposable environment. The completed run then built successfully and reached the intended API gate.

## Next Phase Readiness

**Blocked:** POST-01 and Plan 07-03 Task 2 cannot proceed. A future plan must obtain an explicitly approved upstream interface that exposes every higher-order candidate (or a separately approved evidence design change). No canonical OSD adapter, worker, or alternate kernel was added.

## Self-Check: PASSED

The qualification script, failed receipt, test, and both commits exist. The focused test and primary-environment invariance checks passed.
