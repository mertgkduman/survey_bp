---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "16"
subsystem: campaigns
tags: [failure-count, prospective-policy, terminal-receipt, inverse-binomial]
requires:
  - phase: 09-04
    provides: failure-count contract baseline
  - phase: 09-05
    provides: exact inverse-binomial calculation baseline
provides:
  - prospective failure-count policies with checked executable maxima
  - sealed terminal receipts for target-reached and cap-censored outcomes
  - receipt-validated inverse-binomial inference
affects: [09-17, 09-18, failure-count execution]
actuals:
  tokens: 11000
  tasks: 2
  commits: 4
plan_head_before: cef20e6
tech-stack:
  added: []
  patterns: [prospective-policy-to-terminal-receipt, checked-executable-limits, boundary-observed-timeout]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/contracts.py
    - src/bp_registry/campaigns/statistics.py
    - tests/test_campaign_contracts.py
    - tests/test_campaign_statistics.py
key-decisions:
  - "Executable maxima are checked equations over manifest, decoder, ledger, serializer, artifact, and receipt-reserve dimensions."
  - "Terminal receipts bind the full frozen policy, while executable-limit receipts bind a stable prospective policy authorization digest to avoid a circular digest."
  - "Wall authorizations remain observed at canonical boundaries and retain overshoot as terminal evidence."
requirements-completed: [EVAL-02]
coverage:
  - id: D1
    description: Prospective failure-count policy and executable-limit contract
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_contracts.py
        status: pass
    human_judgment: false
  - id: D2
    description: Terminal-receipt inverse-binomial inference
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_statistics.py
        status: pass
    human_judgment: false
duration: 48min
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 16: Prospective Failure-Count Evidence Summary

Failure-count campaigns now separate their outcome-independent authorization from sealed observed terminal evidence, and inverse-binomial inference consumes that verified separation.

## Accomplishments

- Added prospective policy, procedure, cap, executable-limit, and batch-authorization records with checked resource and receipt-reserve calculations.
- Added target-reached and cap-censored terminal receipts that retain ordered prefix and tail identities, realized resources, and boundary-time overshoot.
- Routed new failure-count assessments through the prospective policy and rejected the legacy mixed stopping record for new assessment construction.
- Added receipt-bound inverse-binomial inference while preserving retained legacy statistical evidence parsing and fixed-shot/finite-look behavior.

## Task Commits

1. **Task 1: Separate prospective policy from terminal evidence** - `930c66d` (test), `65c3cb1` (feat)
2. **Task 2: Join verified terminal evidence to inverse-binomial inference** - `40aad9a` (test), `622074a` (feat)

## Verification

- `tests/test_campaign_contracts.py` focused prospective and terminal subset: 4 passed.
- `tests/test_campaign_statistics.py` focused receipt and inverse-binomial subset: 9 passed.
- Fixed-shot and finite-look regression subset: 5 passed.
- Combined contract and statistics modules: 63 passed.

## Decisions Made

- A receipt reserve is mandatory in both per-unit derivation and batch/campaign authorization, so partial or interruption evidence remains serializable within declared limits.
- Timeout limits authorize boundary checks and no further work after a deadline observation; a running indivisible step can overshoot and that overshoot is terminal evidence.

## Deviations from Plan

None - plan executed as specified. The legacy mixed record remains a typed parser for retained evidence, while new `CampaignAssessmentV1` construction rejects it.

## Self-Check: PASSED

All four task commits exist and the four modified implementation/test files are present. No stubs, skipped tests, or unrun required verification remain.
