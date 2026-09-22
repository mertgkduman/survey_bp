---
phase: 01-evidence-registry-and-native-css-baseline
plan: 04
subsystem: css-artifact-and-evaluation
tags: [css, gf2, sha256, sampling, evaluator, provenance]
requires:
  - {phase: 01-03, provides: native CSS tracer, strict fixture manifest, and JSONL ledger}
provides:
  - Validated CSS checks and ordered paired logical bases over GF(2)
  - Versioned semantic artifact identity and confined content loader
  - Deterministic decoder-visible samples and independent four-class outcomes
affects: [01-05, 01-06, 01-07, 01-08, 01-09]
tech-stack:
  added: []
  patterns: [GF(2) algebraic validation, version-dispatched artifact codecs, manifest-derived sampling, independent outcome evaluation]
key-files:
  created: [src/bp_registry/artifacts.py, src/bp_registry/sampling.py, src/bp_registry/evaluator.py]
  modified: [src/bp_registry/css.py, src/bp_registry/runner.py, tests/test_css_small.py, tests/test_sampling.py, tests/test_reference_smoke.py]
key-decisions:
  - "CSS semantic bytes preserve matrix role, shape, row order, bit order, ordered logical pair convention, and format version."
  - "The runner passes a decoder-visible observation to native BP and supplies hidden truth only to the independent evaluator."
patterns-established:
  - "Artifact readers dispatch by stored format version so v1 bytes remain readable when later codecs are added."
  - "CSS outcomes are derived from original syndrome, residual row spaces, and paired logical action, separate from native convergence."
requirements-completed: [CSS-01, CSS-02, CSS-03, CSS-04]
coverage:
  - id: D1
    description: Validated CSS algebra and role/order-sensitive artifact identities
    requirement: CSS-01
    verification:
      - {kind: unit, ref: tests/test_css_small.py, status: pass}
    human_judgment: false
  - id: D2
    description: Replayable X/Z samples keep named observations separate from hidden truth
    requirement: CSS-03
    verification:
      - {kind: unit, ref: tests/test_sampling.py, status: pass}
    human_judgment: false
  - id: D3
    description: Runner delegates every shot to sampling and independent evaluation
    requirement: CSS-04
    verification:
      - {kind: integration, ref: tests/test_reference_smoke.py::test_runner_uses_sampling_and_independent_evaluator, status: pass}
    human_judgment: false
actuals:
  tokens: 9164
  tasks: 2
  commits: 4
plan_head_before: b22474e177cb4fb8baebd55dfd8b9e7d9f7c2c57
duration: 8min
completed: 2026-09-22
status: complete
---

# Phase 01 Plan 04: CSS Artifact and Outcome Foundation Summary

**The native CSS tracer now relies on independently checked CSS algebra, immutable artifact identities, deterministic observations, and four-class outcome evaluation.**

## Accomplishments

- Added binary Gaussian elimination, row-space membership, paired-logical validation, and canonical v1 bytes that preserve role, shape, ordering, and little-endian bit packing.
- Added a bounded, symlink-safe, approved-root artifact loader that verifies raw file and semantic CSS SHA-256 identities before constructing a code.
- Moved physical sampling and outcome classification out of the tracer, retaining hidden X/Z errors for evaluation while native BP receives only the Z-check observation and prior.

## Task Commits

1. **Task 1 RED:** `565782b` (`test`) — CSS algebra and artifact identity contracts.
2. **Task 1 GREEN:** `ea2abac` (`feat`) — GF(2) validation, canonical bytes, and versioned loader.
3. **Task 2 RED:** `57b19da` (`test`) — sampling, outcomes, and runner delegation contracts.
4. **Task 2 GREEN:** `490f553` (`feat`) — sampling/evaluator modules and tracer delegation.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_sampling.py tests/test_css_small.py` — **18 passed**.
- The full suite was also run: 24 tests passed; 3 pre-existing `tests/test_evidence.py` contracts fail because `bp_registry.evidence` is not yet implemented by its later planned work. Those failures are outside this plan's owned modules and did not affect the plan verification.

## Decisions Made

- Semantic identity uses a fixed v1 byte contract rather than code parameters such as `[[n,k,d]]`, which cannot establish matrix or logical-basis identity.
- A stored artifact version selects a retained reader; later formats add a decoder instead of rewriting saved version 1 artifacts.
- Evaluator outcomes use `invalid_syndrome`, `exact`, `stabilizer_equivalent`, and `logical_failure`; native convergence remains a separate ledger field.

## Deviations from Plan

None - plan executed as specified. The approved isolated `.venv` was used for verification because it contains the Phase 2-approved Pydantic dependency required by the existing tracer manifest.

## TDD Gate Compliance

- Task 1: RED `565782b` preceded GREEN `ea2abac`.
- Task 2: RED `57b19da` preceded GREEN `490f553`.

## Known Stubs

None.

## Next Phase Readiness

Later artifact and pilot work can consume a retained version 1 loader, semantic identities, replayable samples, and outcome records without treating native decoder convergence as a recovery result.

## Self-Check: PASSED

All declared files exist and all four RED/GREEN task commits are present in git history.
