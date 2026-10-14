---
phase: 11-quaternary-reproduction-and-comparisons
plan: "11"
subsystem: publication dispatch authorization
tags: [quaternary, authorization, default-deny, provenance, atomic-write]
requires:
  - phase: 11-10
    provides: two-code default-deny production authorization package
provides:
  - Digest-bound sealed Phase 11 authorization receipt
  - Explicit preserved denial for all four publication campaigns
  - Atomic receipt publication with receipt reload validation
affects: [11-12, 11-13, 11-15, production-dispatch]
tech-stack:
  added: []
  patterns: [explicit-human-decision-transport, sealed-receipt, atomic-deny-publication]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/profiling_gate.py
    - scripts/run_phase11_controlled.py
    - data/results/phase11-production-authorization.json
    - tests/test_phase11_resource_gate.py
key-decisions:
  - "The verified project-owner response preserves denial for all four Phase 11 publication campaigns because site ceilings, account/partition, quota/cost, persisted runtime profiles, and source-route eligibility are absent."
  - "The semantic package digest 4f53f8ce6af2961831830105dde34b4050632751960c9e8c475e9cc7ac16334a remains bound into the sealed denial receipt; no allow token is issued."
patterns-established:
  - "Authorization changes are accepted only through explicit runner arguments, revalidated against frozen package evidence, atomically written, reloaded, and digest-checked."
requirements-completed: [QEV-01, QEV-02]
metrics:
  duration: 18m
  completed: 2026-10-14
status: complete
actuals:
  tokens: 9312
  tasks: 2
  commits: 2
commits: 2
plan_head_before: ff704d2964853b20ab5110c3bd92da1f1176a641
coverage:
  - id: D1
    description: Sealed default-deny receipt records the reviewed decision and prevents dispatch.
    requirement: QEV-01
    verification:
      - kind: integration
        ref: tests/test_phase11_resource_gate.py::test_record_authorization_preserve_deny_seals_the_verified_package
        status: pass
      - kind: integration
        ref: scripts/run_phase11_controlled.py verify-authorization --package data/results/phase11-production-authorization.json
        status: pass
    human_judgment: false
  - id: D2
    description: Exact allow requests remain digest-scoped and fail closed when eligibility evidence is absent.
    requirement: QEV-02
    verification:
      - kind: unit
        ref: tests/test_phase11_resource_gate.py::test_exact_digest_allow_subset_requires_every_gate_and_keeps_other_campaigns_denied
        status: pass
      - kind: integration
        ref: tests/test_phase11_resource_gate.py::test_record_authorization_ineligible_allow_request_is_sealed_as_deny
        status: pass
    human_judgment: false
---

# Phase 11 Plan 11: Reviewed Publication Authorization Summary

**Sealed the project-owner's reviewed decision to deny every Phase 11 publication campaign while retaining the verified package identity and all missing external evidence.**

## Accomplishments

- Added `record-authorization`, which transports only explicit review arguments, validates them against the frozen package, atomically publishes a receipt, reloads it, and verifies its digest.
- Recorded the selected `preserve_deny` decision from `chat_user`. The receipt binds package semantic SHA-256 `4f53f8ce6af2961831830105dde34b4050632751960c9e8c475e9cc7ac16334a`, names all four campaigns as denied, and contains no dispatch token.
- Added coverage for preserve-deny, an ineligible allow attempt, stale review input, interrupted publication, and exact eligible-subset validation.

## Checks Run

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py::test_phase11_proposal_is_decision_ready_but_default_deny tests/test_phase11_resource_gate.py::test_phase11_resource_gate_rejects_client_only_stale_or_allowing_packages tests/test_phase11_resource_gate.py::test_checked_in_phase11_authorization_package_is_valid_and_deny_only tests/test_phase11_resource_gate.py::test_public_cli_verifies_only_the_exact_default_deny_authorization_package -x` — passed (6 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py::test_record_authorization_preserve_deny_seals_the_verified_package tests/test_phase11_resource_gate.py::test_record_authorization_ineligible_allow_request_is_sealed_as_deny -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py::test_record_authorization_stale_digest_rewrites_a_sealed_deny tests/test_phase11_resource_gate.py::test_record_authorization_interrupted_write_leaves_existing_package_intact -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py::test_exact_digest_allow_subset_requires_every_gate_and_keeps_other_campaigns_denied -x` — passed.
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase11_controlled.py verify-authorization --package data/results/phase11-production-authorization.json` — passed after receipt publication.

## Task Commits

1. `eb4f91b` — `test(11-11): add sealed authorization receipt regressions`
2. `9c1be31` — `feat(11-11): seal reviewed authorization decisions`

## Files Modified

- `src/bp_registry/campaigns/profiling_gate.py` — sealed receipt contract, eligibility checks, validation, and atomic publication.
- `scripts/run_phase11_controlled.py` — explicit `record-authorization` command.
- `data/results/phase11-production-authorization.json` — recorded reviewed denial receipt.
- `tests/test_phase11_resource_gate.py` — receipt, stale-input, failure-atomicity, and exact-allowlist tests.

## Decisions Made

- Preserve denial for GB46 and BB72 controlled and source campaigns until measured site ceilings, allocation/accounting, quota or cost, persisted runtime profiles, and source-route eligibility exist.
- Retain a future exact-digest allow path, but require all gates and reviewed account/partition evidence before it can seal an allow receipt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added receipt validation and atomic publication in the profiling gate.**

- **Found during:** Task 2
- **Issue:** The existing runner could validate only the default package; it could not validate, reload, or protect a durable reviewed receipt.
- **Fix:** Added the sealed receipt contract, evidence binding, future exact-allowlist validation, and atomic replacement with revalidation.
- **Files modified:** `src/bp_registry/campaigns/profiling_gate.py`
- **Verification:** Focused receipt, stale-input, and interrupted-write tests passed.
- **Committed in:** `9c1be31`

**Total deviations:** 1 auto-fixed (Rule 2).

## Known Stubs

None. The null site, allocation, quota, and forecast values are evidence of unavailable prerequisites and are the reason the receipt is denied; they do not feed a user-facing placeholder or a dispatch path.

## Next Phase Readiness

Plans 11-12 and later can read the sealed deny receipt rather than infer authorization from a checkpoint. Publication-scale dispatch remains blocked; bounded or inconclusive Phase 11 work can continue under its existing controls.

## Self-Check: PASSED

- Confirmed all four implementation, data, and regression files exist.
- Confirmed `eb4f91b` and `9c1be31` exist in Git history.
- Reloaded and validated the sealed deny receipt through the public verifier.
