---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "16"
subsystem: profiling-validation
tags: [python, profiling, rss, provenance, ledger-verification]
requires:
  - phase: 02-15
    provides: "Public profile evidence and semantic ledger verification"
provides:
  - "Closed producer and validator grammar for unavailable peak-RSS evidence"
  - "Rehashed end-to-end rejection coverage for impossible unavailable RSS claims"
affects: [phase-02-verification, canonical-ledger, profiling]
tech-stack:
  added: []
  patterns:
    - "Unavailable evidence reasons select one exact producer method and raw-context shape."
key-files:
  created:
    - .planning/phases/02-canonical-css-execution-and-policy-contracts/02-16-SUMMARY.md
  modified:
    - src/bp_registry/canonical/profiling.py
    - tests/canonical/test_profiling.py
    - tests/test_canonical_cli.py
key-decisions:
  - "Canonicalize caught adapter exceptions to the first matching base category: AttributeError, OSError, ValueError, then TypeError."
  - "Treat empty or non-string platform adapter outputs as base-method ValueError unavailable evidence, never as unsupported-platform normalization."
  - "Permit unsupported RSS normalization only with an exact nonempty, non-Linux/Darwin platform context and unknown raw unit."
patterns-established:
  - "Persisted nondeterministic resource observations are structurally validated from their own evidence, not compared to a fresh replay."
requirements-completed: [LED-02, LED-03]
coverage:
  - id: D1
    description: "Unavailable LocalProfiler RSS branches emit only their exact canonical evidence grammar."
    requirement: LED-03
    verification:
      - kind: unit
        ref: tests/canonical/test_profiling.py#test_public_profile_rss_unavailable_contract_matches_each_producer_branch
        status: pass
    human_judgment: false
  - id: D2
    description: "Rehashed runtime and terminal profiles reject impossible unavailable RSS provenance."
    requirement: LED-02
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py#test_verify_run_rejects_rehashed_rss_unavailable_grammar_matrix
        status: pass
      - kind: other
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development
        status: pass
    human_judgment: false
actuals:
  tokens: 3007
  tasks: 1
  commits: 2
commits: 2
plan_head_before: c41f630f03c7b30424d582a447074b15bc04ee49
duration: 10min
completed: 2026-09-24
status: complete
---

# Phase 02 Plan 16: RSS Unavailable Evidence Grammar Summary

**Canonical unavailable RSS records now retain a producer-reachable reason, method, and raw-context grammar that survives fully rehashed-ledger validation.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-24T00:46:28Z
- **Completed:** 2026-09-24T00:56:28Z
- **Tasks:** 1/1
- **Files modified:** 3 production/test files

## Accomplishments

- Closed the unavailable peak-RSS vocabulary: adapter absence and four canonical adapter exception categories use the base resource method and no raw context; negative RSS uses the raw RSS method and no raw context.
- Canonicalized `PermissionError` to the `OSError` evidence category and invalid platform adapter results to the `ValueError` category.
- Constrained unsupported normalization to exactly `rss_platform`, `rss_raw_value`, and `rss_raw_unit`, rejecting supported platforms, malformed values, and extraneous context after event and ledger rehashing.

## TDD Gate Compliance

- **RED:** `f1f027c` added direct producer and fully rehashed verifier tests; both intentionally failed before the grammar implementation (`PermissionError` retained its subclass reason and the forged unavailable profile verified).
- **GREEN:** `7a69819` canonicalized producer output and enforced exact validator branches; both focused tests passed.
- **REFACTOR:** No additional refactor was needed; the explicit branch map directly mirrors the producer contract.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_profiling.py::test_public_profile_rss_unavailable_contract_matches_each_producer_branch tests/test_canonical_cli.py::test_verify_run_rejects_rehashed_rss_unavailable_grammar_matrix` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` — 2 checked terminal rows verified.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical tests/test_canonical_cli.py` — 101 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_css_small.py tests/test_evidence.py tests/test_ledger.py tests/test_manifest.py tests/test_phase1_cli.py tests/test_reference_smoke.py tests/test_sampling.py tests/test_source_artifact.py` — 79 passed.
- The checked ledger and result files remained byte-identical to tracked HEAD.

## Task Commits

1. **Task 1: Lock unavailable RSS evidence to exact producer grammars** - `f1f027c` (test), `7a69819` (feat)

## Files Created/Modified

- `src/bp_registry/canonical/profiling.py` - Canonical producer categories and strict unavailable-RSS structural validation.
- `tests/canonical/test_profiling.py` - Direct branch-positive contract coverage.
- `tests/test_canonical_cli.py` - Fully rehashed runtime/terminal unavailable-RSS rejection matrix.

## Decisions Made

- Exception-subclass names are not durable evidence vocabulary; the fixed ordered base categories are.
- Unsupported platforms remain explicitly unavailable rather than receiving a guessed RSS conversion.
- Dynamic timing and resource values remain excluded from fresh replay equality checks.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

CR-08, T-02-31, and T-02-12-03 now have direct producer and rehashed-ledger evidence for closure. The checked development artifact remains valid and unmodified.

## Self-Check: PASSED

- Found `src/bp_registry/canonical/profiling.py`, `tests/canonical/test_profiling.py`, and `tests/test_canonical_cli.py`.
- Found commits `f1f027c` and `7a69819` in repository history.
