---
phase: 11-quaternary-reproduction-and-comparisons
plan: "16"
subsystem: controlled evaluation receipt contract
tags: [quaternary, receipt, authorization, provenance, typed-validation]
requires:
  - phase: 11-15
    provides: sealed GB46 and BB72 denial receipts and controlled verification
provides:
  - Strict ControlledEvaluationReceipt parser, canonical serializer, and digest validator
  - Public campaign export and typed validation on receipt construction and verification
affects: [11-24, controlled-evaluation, QEV-02]
actuals:
  tokens: 4500
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [strict receipt boundary, exact design and authorization identity]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/controlled_evaluation.py
    - src/bp_registry/campaigns/__init__.py
    - tests/test_phase11_controlled_evaluation.py
key-decisions:
  - "Keep phase11_controlled_evaluation_receipt_v1 and both checked denial digests unchanged."
  - "Reject all allow-shaped receipts until a qualified dispatcher defines bounded scheduler and reconciled complete-pair evidence."
requirements-completed: [QEV-02]
coverage:
  - id: D1
    description: Checked GB46 and BB72 denial receipts round-trip through the public typed contract without digest drift.
    requirement: QEV-02
    verification:
      - kind: unit
        ref: tests/test_phase11_controlled_evaluation.py::test_receipt_type_package_export_and_both_checked_denials
        status: pass
    human_judgment: false
  - id: D2
    description: Forged scope, cross-code, or incomplete allow evidence is rejected.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_controlled_evaluation.py::test_verified_receipt_rejects_resealed_manifest_identity
        status: pass
    human_judgment: false
metrics:
  duration: 30m
  completed: 2026-10-16
status: complete
---

# Phase 11 Plan 16: Controlled Receipt Contract Summary

**ControlledEvaluationReceipt now validates the checked denial evidence and all current receipt paths without changing the v1 wire schema.**

## Accomplishments

- Added strict top-level receipt fields, exact nested denial shape checks, canonical round-trip and digest validation.
- Routed both receipt constructors and the independent verifier through the type; exported it from `bp_registry.campaigns`.
- Bound verification to the exact manifest path, fixed marginal design digest, authorization fields, and sealed denial reason. Both current receipts still represent zero dispatch and zero complete pairs.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -x` — 15 passed.
- Checked GB46 and BB72 receipts round-trip semantically with their existing receipt digests.

## Task Commits

1. Task 1 — `bc5cd2f` (`feat(11-16): add typed controlled receipt boundary`).
2. Task 2 — `2f1ba2e` (`feat(11-16): validate and export controlled receipt contract`).

## Deviations from Plan

- The checked GB46 envelope omits optional request fields present on BB72. The type preserves that existing shape rather than synthesizing fields.
- A resealed manifest path initially passed the old verifier. The type integration now compares path and fixed-design identity to the authorized design.

## Next Phase Readiness

Plan 11-24 can extend this boundary for an authorized executed receipt. The current preserve-deny records remain the only accepted terminals and supply no assessment-ready pairs.

## Self-Check: PASSED

- The public export exists and the focused suite passes.
- Both task commits are present; no receipt artifact was rewritten.
