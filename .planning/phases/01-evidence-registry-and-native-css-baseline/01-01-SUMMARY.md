---
phase: 01-evidence-registry-and-native-css-baseline
plan: 01
subsystem: testing
tags: [pytest, python, ldpc, environment]
requires: []
provides:
  - Collectable Phase 1 contract test scaffold
  - Observed local Python and native BP environment identity
affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07]
actuals: {tokens: 1500, tasks: 2, commits: 2}
tech-stack:
  added: [setuptools, pytest]
  patterns: [src-layout namespace package, production imports inside test functions]
key-files:
  created: [pyproject.toml, tests/conftest.py, docs/environment-pins.md]
  modified: []
key-decisions:
  - "Use existing installed distributions for the probe; defer every new install to Plan 02's human gate."
patterns-established:
  - "Collectable behavior contracts can precede implementation."
requirements-completed: [MAP-01, REG-01, CSS-01, LED-01]
coverage:
  - id: D1
    description: Six Phase 1 test modules collect substantive behavioral contracts
    requirement: REG-01
    verification:
      - {kind: unit, ref: "python -m pytest --collect-only -q", status: pass}
    human_judgment: false
  - id: D2
    description: Native API and development environment were observed on the current node
    requirement: CSS-01
    verification:
      - {kind: integration, ref: "docs/environment-pins.md#Native API probe", status: pass}
    human_judgment: false
duration: 8min
completed: 2026-09-22
status: complete
---

# Phase 1 Plan 01 Summary

**The Phase 1 Python test scaffold collects 19 behavior contracts and records the observed native BP runtime.**

## Performance

- **Completed:** 2026-09-22T01:27:03Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Added `pyproject.toml` with `src` namespace discovery and pytest configuration.
- Added six collectable test modules for evidence, manifests, CSS algebra, sampling, native decoding, and ledger accounting.
- Recorded interpreter, package versions and paths, node identity, and a direct `ldpc.BpDecoder` syndrome probe in `docs/environment-pins.md`.

## Task Commits

1. **Evidence and manifest contracts:** `183ee7c`
2. **CSS, sampling, native, ledger contracts and runtime probe:** `f745d27`

## Decisions Made

- Existing installed packages were probed. No package was installed; Plan 02 gates new installations.

## Deviations from Plan

None. The tests intentionally only collect at this stage; implementation arrives in later plans.

## Issues Encountered

- The compiled `BpDecoder` type has no `inspect.signature`; the documented constructor was verified by an actual decode call.

## Self-Check: PASSED

- `python -m pytest --collect-only -q` collected 19 tests from all six modules.
- All planned files exist and both task commits are present.

## Next Phase Readiness

- Plan 02 can review exact package identities before any new installation.
