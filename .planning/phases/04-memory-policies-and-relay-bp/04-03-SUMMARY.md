---
phase: 04-memory-policies-and-relay-bp
plan: "03"
subsystem: canonical-memory
tags: [memory-policy, compatibility, replay, atomicity, tdd]
requires: [04-02]
provides: [ordered-memory-composition, closed-compatibility-admission, decoder-local-memory-assignment]
affects: [canonical-manifests, policy-execution, budget-accounting]
tech-stack:
  added: []
  patterns: [immutable-proposal-then-commit, purpose-separated-seed-identities, single-owner-lifecycle]
key-files:
  created: [src/bp_registry/canonical/compatibility.py]
  modified: [src/bp_registry/canonical/contracts.py, src/bp_registry/canonical/memory.py, tests/canonical/test_memory_composition.py]
decisions:
  - "Memory bindings are stored in their declared contiguous execution order and retain disjoint history owners."
  - "Compatibility admission is closed over concrete update-rule, schedule, target, and boundary operands."
  - "Memory assignment draws derive from decoder-local identities and complete replay identities, never from physical sampling state."
metrics:
  duration: "18m"
  completed: "2026-09-24"
status: complete
actuals:
  tokens: 17414
  tasks: 2
  commits: 5
plan_head_before: a7d12cf430ef0a5d80c077fef8557e5d4091fd13
---

# Phase 04 Plan 03: Memory Composition and Replay Summary

Ordered, repeated memory policies now have versioned ownership, closed compatibility admission, and deterministic decoder-local assignment lifecycle semantics.

## Completed Tasks

1. **Admit all defined ordered and repeated memory bindings**
   - Added `MemoryBindingSpec`, `MemoryCompositionSpec`, boundary enums, and a V5 canonical manifest contract.
   - Added `MemoryCompatibilityDecision` and strict pre-sampling validation for supported update-rule, schedule, target, and commit-boundary operands.
   - Added immutable ordered affine composition proposals with binding-private histories.

2. **Replay seeded disordered memory and commit refreshes atomically**
   - Added fixed, vector, and uniform memory-assignment declarations tied to graph and purpose-separated decoder identities.
   - Uniform intervals accept finite negative values without clipping, including the Relay interval used by the Phase 4 source procedure.
   - Added immutable lifecycle results: rejected reservations preserve assignment state, history, cursor, and committed work; duplicate complete identities replay the single committed result.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_memory_composition.py -k 'order or repeated or compatibility or local_boundary or reject'` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_memory_composition.py tests/canonical/test_budgets.py -k 'seed or assignment or refresh or rollback or idempotent or owner'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_memory_composition.py tests/canonical/test_budgets.py tests/canonical/test_schedule_semantics.py tests/canonical/test_work_accounting.py` — 33 passed.

## TDD Gate Compliance

| Task | RED commit | GREEN commit | Result |
| --- | --- | --- | --- |
| Ordered composition admission | `de4a01a` | `e44a6fe` | RED evidence verified; targeted tests pass. |
| Replayable atomic lifecycle | `60ea6e5` | `5137292` | RED evidence verified; targeted tests pass. |

The final rollback test commit (`5350209`) replaced the phase's deferred skipped fixture with executable denial coverage.

## Decisions Made

- Binding order is persisted and must match the contiguous declared order; history owners cannot alias.
- Undefined operands reject with a stable `memory.target_boundary_unsupported` reason before sampling.
- Replay identity is part of the decoder-local seed domain; a lifecycle lock permits one owner to reserve and commit each complete transition.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All declared source and test files exist, and all five Task 1/Task 2 TDD commits are present in git history.
