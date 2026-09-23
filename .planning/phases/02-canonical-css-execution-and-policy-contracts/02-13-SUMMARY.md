---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "13"
subsystem: canonical-css-public-provenance
tags: [canonical-bp, replay-validation, structural-evidence, profiling, tdd]
requires:
  - phase: 02-12
    provides: checked canonical CLI evidence with typed profiling
provides:
  - domain-separated complete public execution identity
  - deterministic semantic reconstruction before terminal reuse or result generation
  - bounded public profiling admission and regenerated checked evidence
affects: [phase-02-verification, phase-02-security, canonical-results]
tech-stack:
  added: []
  patterns: [full-preflight-shot-identity, semantic-replay-validation, typed-profile-parsing, transient-numerical-qualification]
key-files:
  created: [src/bp_registry/canonical/verification.py]
  modified: [src/bp_registry/canonical/execution.py, src/bp_registry/canonical/profiling.py, src/bp_registry/manifests.py, src/bp_registry/runner.py, src/bp_registry/cli.py, tests/test_canonical_cli.py, data/results/canonical-three-qubit-development/events.jsonl, data/results/canonical-three-qubit-development/result.json]
key-decisions:
  - "Public canonical identity binds the full preflighted manifest, artifact identities, compact composition, sample, run/shot, and observation; lineage roots derive from it."
  - "verify-run re-executes deterministic baseline semantics and treats runtime measurements as typed same-ledger observations, not replay-equality facts."
  - "A persisted numerical failure with a successful fresh replay remains structurally valid only with explicit not_independently_reproduced_numerical_failure status."
  - "Public profiling admits only clean low_overhead plans until a declared bounded cohort quota exists."
metrics:
  duration: 11 min
  completed: 2026-09-23
status: complete
plan_head_before: a13cef38664e43e4cb9048811e41e23bb2237853
commits: 8
actuals:
  tokens: 24566
  tasks: 3
  commits: 8
---

# Phase 02 Plan 13: Public Canonical Provenance Closure Summary

**Public canonical CSS evidence now binds full experiment identity, reconstructs deterministic semantics before reuse, and fails closed on unbounded profiling.**

## Accomplishments

1. Added a domain-separated public execution identity covering full manifest, resolved artifact, compact engine contract, deterministic sample, run/shot, check type, and syndrome; stale same-run terminals now conflict before result mutation.
2. Added shared semantic validation for reuse and `verify-run`: it replays the baseline to check candidate, work, policy effects, lineage, termination, profile typing, trace-off constraints, and independent evaluation rather than trusting rehashed event fields.
3. Restricted public profiles to clean low-overhead cohorts, regenerated the checked ledger/result through the CLI, and retained explicit structural qualification for transient numerical failures.

## Task Commits

1. **Task 1: Bind replay to complete public execution**
   - `8f635de` test RED
   - `fe08a49` feat GREEN
2. **Task 2: Reconstruct every structural claim independently**
   - `240b404` test RED
   - `d755a7c` feat GREEN
   - `eafedd8` feat: added the required budget/numerical terminal qualification regression discovered during acceptance verification.
3. **Task 3: Fail closed on unbounded profiling and regenerate evidence**
   - `5a1bdf2` test RED
   - `7216933` feat GREEN
   - `41036e4` docs: regenerated checked CLI artifacts.

## Verification

- Focused replay identity and structural tamper suites: `8 passed`.
- Budget and transient numerical terminal regression plus semantic tamper suites: `7 passed`.
- Public unbounded-profile admission rejection: `3 passed`.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` — passed with 2 terminal rows.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — `157 passed`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Verification grammar] Emitted runtime evidence before all measured terminal paths.**

- **Found during:** Task 2 semantic reconstruction.
- **Issue:** Count-exhausted attempts after an admitted BP call carried profile evidence but no runtime event, contradicting the termination-specific evidence contract.
- **Fix:** Emit the typed runtime record immediately after admitted profiling and validate it before work/termination.
- **Files modified:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`.
- **Verification:** Budget and semantic replay regression suite passes.

**2. [Rule 2 - Missing critical functionality] Added transient numerical-error qualification.**

- **Found during:** Task 2 acceptance verification.
- **Issue:** A historical numerical error would be rejected if a fresh deterministic replay succeeded, overstating reproducibility.
- **Fix:** Validate its rollback/missingness grammar and report explicit nonreproduction status.
- **Files modified:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`, `tests/test_canonical_cli.py`.
- **Verification:** `test_verify_run_rederives_budget_and_numerical_terminal_semantics` passes.

**Total deviations:** 2 auto-fixed issues. Both strengthen the plan's declared provenance contract.

## Known Stubs

None.

## TDD Gate Compliance

- Task 1 RED/GREEN commits: `8f635de` → `fe08a49`.
- Task 2 RED/GREEN commits: `240b404` → `d755a7c`; its late numerical-terminal acceptance regression is contained in `eafedd8`.
- Task 3 RED/GREEN commits: `5a1bdf2` → `7216933`.

## Self-Check: PASSED

All declared source, test, and checked-evidence artifacts exist; all eight implementation commits are present in Git history.
