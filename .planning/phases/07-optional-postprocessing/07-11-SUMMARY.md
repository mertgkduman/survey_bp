---
phase: 07-optional-postprocessing
plan: "11"
subsystem: canonical postprocessing handoff
tags: [postprocessing, flooding, mbbp, terminal-snapshot, tdd]
requires:
  - phase: 07-01
    provides: immutable failed-attempt and closed LSD fallback seam
provides:
  - Immutable compatibility-typed snapshots for canonical flooding terminals
  - Complete declared-order MBBP failed-member snapshots with posterior reliability
  - Closed unsupported-composition dispositions for controllers lacking snapshot coverage
affects: [07-optional-postprocessing, phase-08-campaigns]
tech-stack:
  added: []
  patterns: [whole-composition fallback gating, immutable terminal snapshots, declared-order handoff ranking]
key-files:
  created:
    - tests/canonical/test_postprocessing_handoff.py
  modified:
    - src/bp_registry/canonical/postprocessing/__init__.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/phase7.py
    - src/bp_registry/canonical/mbbp.py
    - src/bp_registry/canonical/schedules.py
    - tests/canonical/test_mbbp.py
    - tests/test_phase6_public_execution.py
key-decisions:
  - "Recompute original-syndrome validity from terminal candidates before postprocessing eligibility so a budget-limited member cannot trigger fallback after a valid BP result."
  - "Treat missing or unusable terminal evidence as an incompatible handoff and skip fallback rather than dropping a failed attempt."
  - "Keep Relay, fair Beam/Relay, interventions, restart, and unknown transformed controllers closed until they expose complete terminal snapshot contracts."
requirements-completed: [POST-02, POST-05]
coverage:
  - id: D1
    description: Base flooding emits immutable truth-free snapshots or typed fallback-skip dispositions.
    requirement: POST-05
    verification:
      - kind: unit
        ref: tests/canonical/test_postprocessing_handoff.py
        status: pass
    human_judgment: false
  - id: D2
    description: MBBP retains terminal candidate and posterior evidence for every completed member, selects only after whole-composition failure, and rejects unadapted controllers.
    requirement: POST-02
    verification:
      - kind: unit
        ref: tests/canonical/test_mbbp.py
        status: pass
    human_judgment: false
actuals:
  tokens: 7613
  tasks: 2
  commits: 6
plan_head_before: f0cbe29945c806cdd2e2fdf3a06ad7b0f0aad4aa
duration: 8min
completed: 2026-10-06
status: complete
---

# Phase 07 Plan 11: Terminal Handoff Summary

Canonical flooding and MBBP now freeze decoder-visible terminal reliability before fallback, while unsupported multi-attempt controllers fail closed.

## Accomplishments

- Added a typed composition snapshot result for compatible failures, incompatible reliability, completed BP success, and named unsupported controller kinds.
- Routed the V8 flooding tracer through the immutable terminal adapter before any evaluator access or fallback execution.
- Preserved each MBBP member's last committed candidate and finite posterior, then ranked compatible failures only after confirming no member has an original-valid candidate.
- Added deterministic tests for snapshot immutability, malformed reliability, completion-order invariance, later success suppression, and unsupported Relay rejection.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_postprocessing_handoff.py -k 'member and (posterior or snapshot or completion_order or later_success or all_failed or ranking or unsupported or budget)' -x` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_postprocessing_handoff.py tests/test_phase7_public_execution.py -x` — 24 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_css_literature_gate.py::test_gate_package_replays_all_three_and_rejects_result_tamper -x --tb=short` — 1 passed in 205.13s.

## TDD Gate Compliance

| Task | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| 1 | `.gsd/tdd-evidence/07-11-task-1-red.json` (`RED_EVIDENCE_OK`) | `ba713b1` | Passed |
| 2 | `.gsd/tdd-evidence/07-11-task-2-red.json` (`RED_EVIDENCE_OK`) | `6fb5b66` | Passed |

## Task Commits

1. `2bbd89c` — `test(07-11): add failing terminal handoff contract`
2. `358a6d4` — `test(07-11): make terminal handoff RED assertion intentional`
3. `ba713b1` — `feat(07-11): freeze canonical terminal handoff`
4. `3d35202` — `test(07-11): add failing MBBP handoff contracts`
5. `6fb5b66` — `feat(07-11): retain MBBP terminal handoffs`
6. `b47a236` — `fix(07-11): preserve Phase 6 member event grammar`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Routed the existing V8 tracer through the new terminal adapter.**
- **Found during:** Task 1
- **Issue:** The tracer still constructed snapshots inline, which could diverge from the public compatibility disposition.
- **Fix:** Replaced inline construction with `adapt_flooding_attempt` and `execute_composition`.
- **Files modified:** `src/bp_registry/canonical/phase7.py`
- **Verification:** Phase 7 public execution regression passed.
- **Committed in:** `ba713b1`

**2. [Rule 2 - Correctness] Exposed committed serial posterior reliability for MBBP.**
- **Found during:** Task 2
- **Issue:** The serial schedule returned a terminal candidate but discarded the corresponding posterior needed for a complete MBBP handoff.
- **Fix:** Added an immutable posterior to admitted local-step results and retained it in each MBBP terminal member record.
- **Files modified:** `src/bp_registry/canonical/schedules.py`, `src/bp_registry/canonical/mbbp.py`
- **Verification:** MBBP and handoff regression suite passed.
- **Committed in:** `6fb5b66`

**3. [Rule 1 - Bug] Preserved sealed Phase 6 member-event payloads.**
- **Found during:** Wave 2 integration gate
- **Issue:** Serial posterior evidence added for Phase 7 was serialized through the existing Phase 6 MBBP event projection, causing historical V7 receipts to differ from deterministic replay.
- **Fix:** Kept `terminal_posterior` on the in-memory MBBP member for the Phase 7 adapter while excluding it from the established Phase 6 structural payload grammar.
- **Files modified:** `src/bp_registry/canonical/mbbp.py`, `tests/test_phase6_public_execution.py`
- **Verification:** Phase 6 payload regression and the previously failing three-package literature gate passed.
- **Committed in:** `b47a236`

## Issues Encountered

The first Task 1 RED probe initially failed during import collection. The test was corrected to make a direct assertion about the missing public adapter before implementation; the recorded RED evidence then passed the TDD gate.

## Known Stubs

None.

## Self-Check: PASSED

All implementation/test files and the summary exist. The six recorded task commits are present in Git.

## Next Phase Readiness

Plan 07-07 can consume the supported flooding/MBBP dispositions during public preflight. Unsupported composition kinds expose stable reasons before artifact loading or sampling.
