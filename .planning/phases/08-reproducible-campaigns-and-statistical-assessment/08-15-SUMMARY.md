---
phase: 08-reproducible-campaigns-and-statistical-assessment
plan: "15"
subsystem: campaign execution
tags: [canonical-bp, paired-sampling, immutable-receipts, cli, statistical-assessment]
requires:
  - phase: 08-14
    provides: frozen campaign work-plan, merge, resume, and report boundaries
provides:
  - strict multi-arm campaign work specification and deterministic frozen plan
  - one-time materialized physical sample replayed through canonical decoder arms
  - installed paired plan, run, verify, merge, resume, and assess lifecycle
affects: [phase-08, campaign-denominators, paired-statistics]
tech-stack:
  added: []
  patterns:
    - canonical events remain unchanged while campaign receipts bind paired evidence
    - physical sample identities are arm-neutral and decoder identities remain arm-scoped
key-files:
  created: []
  modified:
    - src/bp_registry/runner.py
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/planning.py
    - src/bp_registry/campaigns/execution.py
    - src/bp_registry/campaigns/cli.py
    - src/bp_registry/campaigns/__init__.py
    - tests/test_campaign_execution.py
key-decisions:
  - "Replay caller-supplied verified ShotSample objects through a dedicated canonical seam without changing canonical event fields."
  - "Bind materialized sample and realized-error hashes in campaign receipts, keeping sample seed identity separate."
  - "Translate only canonical logical_failure into the campaign terminal taxonomy; preserve all already named terminal statuses."
requirements-completed: [LED-05, SIM-01, SIM-02]
actuals:
  tokens: 14650
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 0a7eb2d2c91fb31c1eabbdab22fb30028adcba82
coverage:
  - id: D1
    description: "A compatible two-arm canonical campaign replays byte-identical physical errors and observations."
    requirement: SIM-01
    verification:
      - kind: integration
        ref: tests/test_campaign_execution.py#test_paired_canonical_replays_identical_error_bytes
        status: pass
    human_judgment: false
  - id: D2
    description: "The installed command completes the paired local evidence lifecycle."
    requirement: SIM-02
    verification:
      - kind: e2e
        ref: tests/test_campaign_execution.py#test_installed_paired_canonical_local_lifecycle
        status: pass
    human_judgment: false
duration: 40min
completed: 2026-10-11
status: complete
---

# Phase 08 Plan 15: Paired Canonical Campaign Lifecycle Summary

**A strict two-arm campaign now materializes one CSS error once, replays its exact bytes through canonical decoders, and carries the verified evidence through the installed lifecycle.**

## Accomplishments

- Added strict paired work, sampler, arm, coordinate, and materialized-sample contracts with bounded, content-addressed inputs.
- Added `run_canonical_materialized_one`, which validates a supplied sample and retains the existing canonical event schema.
- Added campaign attempt receipts that bind canonical-ledger, materialized-sample, and physical-error hashes before merge.
- Added installed plan, local run, verify, merge, exact resume, and assessment support for `campaign_work_spec_v1`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'public_paired_canonical_local_lifecycle or paired_canonical_replays_identical_error_bytes or paired_canonical_rejects_equal_labels_with_different_material or paired_canonical_rejects_attempt_or_ledger_tamper' -x` — passed (3 selected).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_paired_canonical_local_lifecycle or public_campaign_facade_exports_work_plan' -x` — passed (2 selected).
- Broader required regression — passed: 142 tests in 252.63 seconds.

## Task Commits

1. Task 1 RED test: `ed182c5` — `test(08-15): define paired work-plan facade`
2. Task 1: `3346b49` — `feat(08-15): replay paired canonical samples`
3. Task 2: `5f38975` — `feat(08-15): expose paired campaign lifecycle`
4. Follow-up correctness fix: `299cfe5` — `fix(08-15): normalize canonical terminal taxonomy`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Map canonical binary evaluator output into the frozen campaign taxonomy**

- **Found during:** Task 2 assessment integration.
- **Issue:** Canonical ledger events use `logical_failure`, while campaign assessment requires a declared terminal status.
- **Fix:** Campaign receipts translate only `logical_failure` to `wrong_logical_action`; named statuses remain unchanged and canonical event bytes are untouched.
- **Files modified:** `src/bp_registry/campaigns/execution.py`
- **Verification:** Installed lifecycle test and broader regression passed.
- **Commit:** `299cfe5`

## Known Stubs

None.

## Next Phase Readiness

Later denominator and statistical work can consume immutable paired receipts with distinct decoder identities and shared materialized physical-error evidence.

## Self-Check: PASSED

- All seven planned implementation/test files exist and the four plan commits are present in Git history.
