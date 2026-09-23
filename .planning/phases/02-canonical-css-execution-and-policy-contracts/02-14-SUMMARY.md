---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "14"
subsystem: canonical-css-public-provenance
tags: [canonical-bp, structural-verification, budget-reconstruction, profiling, tdd]
requires:
  - phase: 02-13
    provides: hash-linked public canonical terminal evidence
provides:
  - exact terminal-specific event grammar for all admitted Phase 02 paths
  - ledger-independent count-budget and qualified-iteration reconstruction
  - strict producer-backed clean low-overhead profile provenance validation
affects: [phase-02-review, phase-02-security, canonical-results]
tech-stack:
  added: []
  patterns: [exact-event-schemas, trusted-input-reconstruction, same-ledger-profile-equality]
key-files:
  created: []
  modified: [src/bp_registry/canonical/verification.py, src/bp_registry/canonical/profiling.py, tests/test_canonical_cli.py]
key-decisions:
  - "Terminal event fields and cardinality are terminal-class-specific, with required-null outcome distinct from absent fields."
  - "Count-budget denial objects are reconstructed solely from preflighted limits, topology, and reserve-before-work order."
  - "Profile values remain nondeterministic observations, while their producer metadata, availability state, bounds, and same-ledger copies are structural facts."
metrics:
  duration: 10 min
  completed: 2026-09-23
status: complete
plan_head_before: c118f319cc695436bb97535a3729aba4dd76904d
commits: 5
actuals:
  tokens: 8231
  tasks: 3
  commits: 5
---

# Phase 02 Plan 14: Exhaustive Terminal Evidence Summary

**Canonical verification now rejects rehashed terminal, budget, and profiler provenance claims through exact schemas and independent reconstruction.**

## Accomplishments

1. Added exact ordered grammar, exact data-key sets, identity/policy checks, and terminal-specific required/absent fields for completed, count-budget, maximum-iteration, and numerical-failure evidence.
2. Reconstructed call-admission and atomic-sweep denial facts from trusted inputs, including binding scope, resource, cap, prior consumption, committed work, and flooding qualified iterations.
3. Added a strict local-profiler validator for enabled and disabled clean low-overhead evidence, including metric provenance, availability, RSS context, environment bounds, and same-ledger-only nondeterministic values.

## Task Commits

1. Task 1 — `f9f3402` RED, `6ae7114` GREEN.
2. Task 2 — `10a04ee` adversarial grammar and budget matrix coverage; reconstruction shipped in `6ae7114`.
3. Task 3 — `edf69a3` profile provenance validator and all-metric matrix coverage.
4. `7be16cb` preserves trace-specific rejection diagnostics.

## Verification

- Focused exact grammar, budget, profile, and nondeterministic-value tests: `14 passed`.
- Unchanged checked artifact: `python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` verified 2 terminal rows.
- Complete suite: `173 passed`.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Restored the independently reconstructed proposed sweep work before committing a successful replay sweep.
   - Found during focused verifier testing.
   - The refactor initially referenced an undefined proposed vector.
   - Fixed in `6ae7114` and covered by the terminal reconstruction suite.

2. [Rule 1 - Diagnostic] Retained the established trace-specific validation error for a forbidden sidecar.
   - Found during full-suite compatibility testing.
   - Fixed in `7be16cb`.

## Known Stubs

None.

## TDD Gate Compliance

- RED evidence was captured by the initial adversarial regression commit `f9f3402`.
- GREEN implementation commits are `6ae7114` and `edf69a3`.

## Self-Check: PASSED

All declared source and test files are present, and all five plan commits are in Git history.
