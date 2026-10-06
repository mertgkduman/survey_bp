---
phase: 07-optional-postprocessing
plan: "04"
subsystem: canonical postprocessing
tags: [stabilizer-inactivation, css, gf2, postprocessing, tdd]
requires:
  - phase: 07-01
    provides: frozen failed-attempt handoff and one-method postprocessing boundary
provides:
  - Deterministic, source-labeled CSS stabilizer-inactivation reduction
  - Method-owned reduced reruns, GF(2) solves, lifts, and original validation
affects: [07-optional-postprocessing, phase-08-campaigns]
tech-stack:
  added: []
  patterns: [source-blocked faithful status beside explicit canonical adaptation controls, leaf-reserved SI trial work]
key-files:
  created:
    - src/bp_registry/canonical/postprocessing/si.py
    - src/bp_registry/canonical/postprocessing/work.py
    - tests/canonical/test_postprocessing_si.py
  modified:
    - src/bp_registry/canonical/postprocessing/__init__.py
key-decisions:
  - "Keep paper-v3 SI non-runnable for unresolved tie, GF(2)-solution, and author-code conventions."
  - "Use ascending stabilizer-ID ties and zero free variables only as named canonical-adaptation controls."
patterns-established:
  - "Optional methods reserve each method-owned work leaf before rerun, solve, lift, or original validation."
requirements-completed: [POST-03]
coverage:
  - id: D1
    description: Source-blocked SI status and deterministic CSS reduction.
    requirement: POST-03
    verification:
      - kind: unit
        ref: tests/canonical/test_postprocessing_si.py
        status: pass
    human_judgment: false
  - id: D2
    description: Method-owned SI rerun, GF(2) solve, lift, cap retention, and original validation.
    requirement: POST-03
    verification:
      - kind: unit
        ref: tests/canonical/test_postprocessing_si.py
        status: pass
    human_judgment: false
actuals:
  tokens: 7947
  tasks: 2
  commits: 4
plan_head_before: d333d3ae32e6b5209cb8c2778aeed4ab20fa5449
duration: 28min
completed: 2026-10-06
status: complete
---

# Phase 07 Plan 04: Stabilizer Inactivation Summary

Canonical CSS stabilizer inactivation now performs deterministic support reduction, same-kernel reruns, GF(2) reconstruction, and immutable-original validation while preserving the paper-v3 source blockers.

## Accomplishments

- Added explicit non-runnable source-faithful status for unresolved equal-reliability ties, GF(2) solution selection, and author-code identity.
- Added canonical reduction from magnitude posterior LLR reliability with score then stabilizer-ID ordering, CSS compatibility checks, and immutable certified working problems.
- Added SI-owned rerun, zero-free-variable GF(2) solve, lift, original-check, candidate selection, cap retention, and typed unique budget leaves.
- Generalized the closed postprocessing controller to accept one structural method protocol, allowing SI to remain one fallback call rather than a chain.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_si.py -x` — 9 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase7_public_execution.py -x` — 5 passed.
- The planned `tests/canonical/test_postprocessing_handoff.py` regression could not run because the file is absent in this checkout. The source change is covered by the existing Phase 7 public regression above.

## TDD Gate Compliance

| Task | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| 1 | `.gsd/tdd-evidence/07-04-task-1-red.json` (`RED_EVIDENCE_OK`) | `2e0c570` | Passed |
| 2 | `.gsd/tdd-evidence/07-04-task-2-red.json` (`RED_EVIDENCE_OK`) | `0652619` | Passed |

## Task Commits

1. `1d9b111` — `test(07-04): add failing SI reduction contracts`
2. `2e0c570` — `feat(07-04): add canonical SI reduction`
3. `64868dc` — `test(07-04): add failing SI rerun contracts`
4. `0652619` — `feat(07-04): execute canonical SI reruns`

## Deviations from Plan

None - plan behavior was delivered as specified. The planned handoff regression file is not present in this checkout; its unavailable command is recorded above.

## Self-Check: PASSED

The SI implementation, typed work model, and focused tests exist. All four task commits are present in Git history.
