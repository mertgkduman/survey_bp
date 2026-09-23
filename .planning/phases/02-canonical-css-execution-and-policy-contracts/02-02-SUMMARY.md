---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "02"
subsystem: canonical-css-policy-contracts
tags: [css, belief-propagation, policy-contracts, lifecycle, provenance]
requires: [02-01-strict-canonical-manifest]
provides: [closed-policy-registry, typed-policy-lifecycle, policy-evidence-contract]
affects: [canonical-policy-expansion, CSS-evaluation, durable-shot-evidence]
tech-stack:
  added: []
  patterns: [closed-registry, strict-frozen-schema, engine-owned-state, typed-policy-decisions]
key-files:
  created:
    - tests/canonical/test_contracts.py
    - tests/canonical/test_policy_evidence.py
  modified:
    - src/bp_registry/manifests.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
    - tests/test_canonical_cli.py
decisions:
  - Persisted canonical policy compositions require seven explicit binding specifications resolved only through an in-code registry.
  - The engine owns lifecycle traversal and private policy state; policies can request only typed, binding-authorized state mutations.
  - Every resolved binding carries a procedure basis and deterministic ordered invariants.
metrics:
  duration: 17m
  completed: 2026-09-23
  tasks_completed: 2
  files_created: 2
status: complete
plan_head_before: 445f25f62c96d20677671a07d3c366a0f88b94d0
commits: 4
actuals:
  tokens: 6650
  tasks: 2
  commits: 4
---

# Phase 02 Plan 02: Canonical CSS Execution and Policy Contracts Summary

Strict seven-role canonical compositions now resolve through a closed policy registry with explicit lifecycle hooks, isolated private state, typed decisions, and adjacent procedural evidence.

## Completed Tasks

1. Added strict frozen policy-binding specifications, static graph validation, deterministic semantic identities, and schema-v2 dispatch without changing native v1 manifest behavior.
2. Added engine-owned shot/search/member/leg/branch/attempt/iteration/message lifecycle contracts, private-state isolation, typed relay/search dimensions, typed decision validation, and evidence requirements.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/canonical/test_policy_evidence.py tests/test_manifest.py`

Result: `28 passed`.

Full regression: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` → `85 passed`.

## Decisions Made

- Persisted composition data cannot name import paths, callables, or unregistered policy kinds; all seven roles must be present explicitly.
- Relationship, execution topology, and relay payload are separate typed concepts, preventing implicit state transfer between sibling executions.
- The initial closed registry recognizes the existing canonical CSS kernel's `binary_spa`, `flooding`, `stateless`, `syndrome_or_budget`, and `stable_first` procedures alongside explicit identity policies.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated the existing canonical tracer fixture for explicit policy bindings**
- **Found during:** Task 2 regression verification
- **Issue:** Its schema-v2 fixture still used the Plan 01 shorthand policy records, which the new mandatory explicit binding contract correctly rejected.
- **Fix:** Added binding IDs, lifetimes, ownership, and capability declarations; registered the tracer's already-supported policy kinds in the closed registry.
- **Files modified:** `tests/test_canonical_cli.py`, `src/bp_registry/canonical/contracts.py`
- **Commit:** `7857a55`

## Known Stubs

None.

## Self-Check: PASSED

All six planned source/test artifacts, the summary artifact, and the four measured TDD/task commits exist in the repository.
