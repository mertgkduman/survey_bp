---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "01"
subsystem: canonical-css-execution
tags: [css, belief-propagation, policy-contracts, provenance, truth-boundary]
requires: [phase-01-evidence-registry-native-css]
provides: [strict-canonical-manifest, project-owned-spa-kernel, immutable-policy-views, stable-candidate-lineage]
affects: [canonical-policy-expansion, CSS-evaluation, durable-shot-evidence]
tech-stack:
  added: [NumPy, Pydantic]
  patterns: [strict-frozen-schema, float64-flooding-SPA, ledger-ownership, post-selection-evaluation]
key-files:
  created:
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/numerics.py
    - src/bp_registry/canonical/kernel.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/problems.py
    - src/bp_registry/canonical/lineage.py
    - src/bp_registry/canonical/__init__.py
    - tests/test_canonical_cli.py
    - tests/canonical/test_truth_boundary.py
decisions:
  - Canonical manifests require all seven explicit policy roles, including named identity roles.
  - Selection freezes a copied read-only original-space candidate before the independent evaluator receives hidden truth.
  - Candidate selection is stable by declared local order and lineage rather than event arrival.
metrics:
  duration: 18m
  completed: 2026-09-23
  tasks_completed: 2
  files_created: 9
status: complete
plan_head_before: 89eb7027f6a33aa4591b46822904f4fe1b7720aa
commits: 2
actuals:
  tokens: 6782
  tasks: 2
  commits: 2
---

# Phase 02 Plan 01: Canonical CSS Execution and Policy Contracts Summary

Strict seven-role manifests now drive a project-owned deterministic binary SPA tracer that freezes decoder-visible candidates before independent CSS evaluation and durable ledger evidence.

## Completed Tasks

1. Built a strict canonical manifest, finite float64 flooding SPA kernel, selection-freeze execution path, and replay-safe ledger terminal evidence.
2. Added immutable original/working/candidate values, typed stable lineage, hostile capability traversal checks, and explicit empty-selection behavior.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py tests/canonical/test_truth_boundary.py`

Result: `6 passed`.

## Decisions Made

- The first canonical numerical profile is `cpu-float64-spa-v1`, with explicit finite saturation and typed numerical failure termination.
- Canonical policy callbacks receive only immutable original/working problems and already-lifted candidates; hidden truth, evaluator state, ledger ownership, and kernel internals remain outside their reachable capability graph.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All nine planned source/test files and both task commits (`c78493a`, `925e5e5`) exist.
