---
phase: 04-memory-policies-and-relay-bp
plan: "13"
subsystem: cancelled production reconciliation and retained evidence inventory
tags: [relay-bp, cancellation, provenance, bounded-evidence]
requires:
  - phase: 04-12
    provides: audited terminal calibration and frozen selections
provides:
  - Terminal user-cancelled production manifest with automatic resume disabled
  - Hash-linked inventory of retained calibration, auxiliary pilots and interrupted prefix
  - Explicit absent fresh evaluation, native-pair and factorial status
affects: [04-14, phase-4-verification, phase-8, phase-9]
key-files:
  created:
    - .planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md
    - data/evidence/phase4-retained-evidence-inventory.json
  modified:
    - .planning/async-jobs/04-13-production-v1.json
    - docs/phase4-memory-relay.md
decisions:
  - "The user stopped the comprehensive Phase 4 experiment because its size was premature; later CSS campaign sizing must be planned afresh."
  - "Retain 159 completed and one interrupted B1 baseline receipts without promoting this prefix to a completed evaluation."
requirements-completed: []
status: complete
metrics:
  completed: 2026-09-30
  verification: "30 passed, 1 skipped in tests/canonical/test_phase4_evidence.py; async manifest schema valid; job process absent"
---

# Plan 04-13: cancelled production reconciled

The old production process group 3156090 was terminated at the user's direction. The shared Slurm allocation 55938300 was left running. The async manifest has terminal `cancelled` status, records the user's reason and receipt hash, and its resume command exits without launching the former sequence.

The B1 baseline receipt contains 159 completed and one `incomplete_interrupted` attempt. Its SHA-256 is `eae6f33f402dff75673148eb486b9278a289445f9c929b34dc788a2debe77ebe`. No complete fresh evaluation, fresh native-pair or factorial result exists. The inventory identifies completed calibration and separate auxiliary evidence with hashes, and labels the cancelled stages unavailable. B1 tuning remains inconclusive under its frozen cap.

Phase 4's remaining work is an availability-aware notebook, guide and phase verification under revised Plan 04-14. The stopped production experiment is not a Phase 4 completion gate. This plan establishes no decoder performance ranking or paper-curve reproduction result.
