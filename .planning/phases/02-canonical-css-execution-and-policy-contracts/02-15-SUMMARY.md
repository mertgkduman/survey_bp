---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "15"
subsystem: canonical-css-public-verification
tags: [canonical-bp, structural-verification, provenance, numerical-failure, profiling, tdd]
requires:
  - phase: 02-14
    provides: exact public terminal grammars and profile producer contracts
provides:
  - replay-safe verification of persistent numerical-failure terminals
  - trusted manifest provenance and exact lineage/status binding for every admitted terminal class
  - exact Linux/Darwin raw-RSS-to-byte validation without replaying nondeterministic measurements
affects: [phase-02-review, phase-02-security, canonical-results]
tech-stack:
  added: []
  patterns: [trusted-public-context, terminal-specific-lineage-reconstruction, same-ledger-nondeterministic-observations]
key-files:
  created: []
  modified: [src/bp_registry/canonical/verification.py, src/bp_registry/canonical/profiling.py, src/bp_registry/runner.py, tests/test_canonical_cli.py, tests/canonical/test_profiling.py]
key-decisions:
  - "Numerical-failure terminals are validated through their strict persisted envelope before any deterministic replay is attempted."
  - "Manifest-owned code, evidence, fixture, assessment, and decoder-seed labels are verifier inputs, never ledger trust roots."
  - "RSS is internally normalized from a platform-qualified raw source; all other valid profiling measurements remain nondeterministic observations."
metrics:
  duration: 31 min
  completed: 2026-09-23
status: complete
plan_head_before: 8f417e467439cb21416d30b9e14752c05e1631cc
commits: 6
actuals:
  tokens: 6322.75
  tasks: 3
  commits: 6
---

# Phase 02 Plan 15: Public Verification Closure Summary

**Public canonical verification now independently binds numerical-failure, terminal, lineage, manifest-provenance, and RSS claims while retaining nondeterministic measurements as same-ledger observations.**

## Accomplishments

1. Validated a final `numerical_failure` terminal before attempting deterministic replay, preserving strict missingness/work grammar and `not_independently_reproduced_numerical_failure` for an active persistent failure.
2. Delivered all five preflighted scientific labels through `PublicShotContext`, reconstructed attempt ancestry for completed, numerical, denial, and maximum-iteration streams, and exact-checked completed selection/convergence plus all admitted runtime records.
3. Enforced Linux kilobyte and Darwin byte RSS normalization against the recorded raw source fact; profile values remain intentionally un-compared with a fresh measurement.

## Task Commits

1. Task 1 — `96c59c3` RED persistent-numerical reuse regression; `ee9cce0` replay-safe numerical verification.
2. Task 2 — `d4e7f65` RED rehashed terminal/provenance inventory; `244340b` trusted context and terminal semantic binding.
3. Task 3 — `9b1bba6` RED Linux/Darwin RSS contract tests; `5c103a0` exact RSS source normalization.

## Verification

- Task 1 focused numerical tests: `2 passed`.
- Task 2 rehashed inventory and terminal-class positive controls: `2 passed`.
- Task 3 focused profiling/RSS/nondeterministic tests: `3 passed`.
- Checked evidence: `python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` verified 2 terminal rows.
- Checked artifact remained byte-identical to tracked HEAD across both ledger and result files.
- Complete suite: `178 passed`.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## TDD Gate Compliance

- RED/green commits are present for each task: `96c59c3`/`ee9cce0`, `d4e7f65`/`244340b`, and `9b1bba6`/`5c103a0`.
- Each RED target produced its expected red assertion before the matching implementation was added.

## Self-Check: PASSED

The summary and all six task commits are present in Git history; the plan-owned files contain no tracked stub markers.
