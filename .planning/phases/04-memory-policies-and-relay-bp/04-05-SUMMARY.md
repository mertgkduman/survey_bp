---
phase: 04-memory-policies-and-relay-bp
plan: "05"
subsystem: canonical-relay
tags: [relay-bp, memory-policy, css, tdd]
requires: [04-04]
provides: [RelayPreset, RelayController, RelayCandidateScore]
affects: [canonical-v4-manifests, phase4-relay-ledger]
tech_stack:
  added: []
  patterns: [immutable-preset, posterior-only-transfer, decoder-visible-stable-selection]
key_files:
  created: []
  modified:
    - src/bp_registry/canonical/relay.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/contracts.py
    - tests/canonical/test_relay.py
decisions:
  - "Source and canonical Relay presets are immutable named CSS adaptations; changed components receive a controlled-adaptation identity."
  - "Relay candidate selection minimizes decoder-visible syndrome and prior weights, then uses leg order to preserve first-on-tie behavior."
  - "Absent an explicit solution limit in an existing V4 manifest, the limit resolves to the persisted total leg limit for compatibility."
metrics:
  duration: "unknown"
  completed: 2026-09-25
status: complete
plan_head_before: 6bb8c6d16889845cd18b29a806bdc3e76820fb80
commits: 4
actuals:
  tokens: 4760
  tasks: 2
  commits: 4
---

# Phase 04 Plan 05: Relay Presets and Controls Summary

Canonical Relay now exposes immutable source-procedure and canonical-default CSS configurations with explicit leg lifecycle, posterior-only transfer, bounded stopping, and stable truth-blind selection.

## Delivered

- Added `RelayPreset` for source internal BP v0.2.2 settings and a bounded canonical CSS default, with procedure, fidelity, memory, transfer, numerical-profile, leg, and solution controls persisted through `RelaySpecV4`.
- Relaxed V4 Relay to allow one-leg ablations while deriving omitted historic stopping and iteration controls into persisted resolved values.
- Added decoder-visible `RelayCandidateScore`; valid candidates are selected by minimum syndrome/prior-weight score and preserve earlier legs on exact ties.
- Reset leg-local memory history on every posterior-only handoff. Message state, iteration, convergence, and predecessor history stay inside their originating leg.
- Added component ablations for one-leg, transfer-off, uniform/disordered later-leg memory, source sweep, and numerical-profile control. These return distinctly named controlled adaptations without mutating source presets.
- Recorded procedure, fidelity, numerical profile, stopping reason, and candidate score in canonical Relay event data.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py -k 'source_preset or canonical_preset or leg_limit or stopping or score or tie'` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py -k 'ablation or no_transfer or one_leg or uniform or disordered or numerical_profile'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py tests/canonical/test_schedule_semantics.py` — 21 passed.

## TDD Gate Compliance

- Task 1 RED evidence: `.gsd/tdd-evidence/04-05-task-1-red.json` verified `RED_EVIDENCE_OK`; test commit `e9b5f57` precedes implementation `f4f6cc6`.
- Task 2 RED evidence: `.gsd/tdd-evidence/04-05-task-2-red.json` verified `RED_EVIDENCE_OK`; test commit `7db0260` precedes implementation `b6bd9dc`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Allowed controlled source-procedure configurations through the V4 manifest validator**
- **Found during:** Final preset-to-manifest smoke check
- **Issue:** `RelayPreset.source_procedure().ablation(...).as_spec()` carried the required controlled-adaptation label but `RelaySpecV4` accepted only the immutable source label.
- **Fix:** Allow the controlled-adaptation fidelity status for source-procedure configurations and assert that an ablation serializes into the strict V4 spec.
- **Files modified:** `src/bp_registry/canonical/contracts.py`, `tests/canonical/test_relay.py`
- **Commit:** `4dd67a8`

## Known Stubs

None.

## Self-Check: PASSED

All four declared implementation/test files, four TDD/task commits, and the inline Rule 1 fix commit are present. The empty runtime maps reported by the broad stub scan are established execution state, not Relay output placeholders.
