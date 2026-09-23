---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "08"
subsystem: canonical-css-execution
tags: [canonical-bp, css, manifest, cli, ledger, reproducibility]
requires:
  - phase: 02
    provides: canonical policy, budget, lineage, tracing, and profiling contracts from plans 02-02 through 02-07
provides:
  - Strict public canonical experiment manifest and generated schema
  - Public canonical run/preflight/verification CLI with v2 structural evidence
  - Checked deterministic three-qubit canonical development result
affects: [phase-02-plan-09, canonical-results, experiment-registry]
actuals:
  tokens: 17818
  tasks: 3
  commits: 6
plan_head_before: c77478715efd93fd3c4f9100e893869055c61c82
tech-stack:
  added: []
  patterns: [strict version-dispatched canonical manifests, terminal-row result reconstruction, owned structural event evidence]
key-files:
  created: [data/manifests/schema-canonical-v2.json, data/manifests/canonical-three-qubit-development.json, data/results/canonical-three-qubit-development/events.jsonl, data/results/canonical-three-qubit-development/result.json]
  modified: [src/bp_registry/manifests.py, src/bp_registry/runner.py, src/bp_registry/ledger.py, src/bp_registry/cli.py, src/bp_registry/canonical/execution.py, tests/test_canonical_cli.py]
key-decisions:
  - "Public canonical experiments use CanonicalExperimentV2, while the compact CanonicalManifestV2 remains available for direct kernel contracts."
  - "Canonical results are reconstructed from hash-linked v2 terminal evidence and retain canonical_implemented/development_fixture/not_assessed labels."
  - "Canonical CPU runtime is measured per attempt; unavailable device time is recorded explicitly rather than represented as zero."
patterns-established:
  - "Preflight artifact, environment, matrix identity, and closed policy composition before sampling, ownership, or kernel work."
  - "Keep hidden truth in the runner and evaluate only after a decoder-visible candidate is frozen."
requirements-completed: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, SCH-01, LED-02, LED-03, LED-04]
coverage:
  - id: D1
    description: Strict canonical manifest schema and immutable preflight
    requirement: ENG-01
    verification:
      - kind: integration
        ref: tests/test_manifest.py and tests/test_canonical_cli.py
        status: pass
    human_judgment: false
  - id: D2
    description: Public canonical execution with structural terminal evidence and independently evaluated outcomes
    requirement: ENG-02
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py#test_public_canonical_command_reconstructs_verified_structural_evidence
        status: pass
      - kind: integration
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-09-23
status: complete
---

# Phase 02 Plan 08: Canonical CSS Public Execution Summary

**Strict canonical CSS manifests now preflight immutable inputs, execute project-owned flooding BP, and reconstruct a checked two-shot development result from durable structural evidence.**

## Performance

- **Duration:** 8 min
- **Tasks:** 3/3
- **Files modified:** 10
- **Verification:** 63 passed; checked `verify-run` succeeded with `OMP_NUM_THREADS=1`.

## Accomplishments

- Added `CanonicalExperimentV2`, a strict persisted schema requiring seven explicit policy roles, numerical profile, nested budgets, trace/profile plans, environment, artifact identities, randomness, and honest evidence labels.
- Added canonical preflight, run, and verification paths without changing historical native pilot semantics.
- Checked in an idempotent v2 event ledger and terminal-row-derived result for the canonical three-qubit development fixture.

## Task Commits

1. **Task 1: Export and preflight the runnable canonical manifest contract** — `2871426`, `3a26782`
2. **Task 2: Route the public CLI through canonical execution and rich evidence** — `7edee78`, `f67cf05`
3. **Task 3: Execute and check the deterministic canonical development result** — `5a31764`
4. **Runtime evidence correction** — `d315072`

## Decisions Made

- Strict full persisted manifests are distinct from the existing compact in-memory kernel contract, preserving the Phase 2 unit-test API while making all public experiments explicit.
- The public result reports `canonical_implemented`, `development_fixture`, and `not_assessed`; it makes no source-faithful or statistical-reproduction claim.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Added explicit runtime and device-metric missingness evidence.**
- **Found during:** Task 3
- **Issue:** Structural terminal evidence had work and lineage but did not retain the required CPU runtime context or explicitly mark unavailable device timing.
- **Fix:** Recorded a per-attempt `runtime` event using `time.perf_counter_ns` and a `missingness` event for the CPU profile's unavailable device timer; regenerated and reverified the checked result.
- **Files modified:** `src/bp_registry/canonical/execution.py`, `data/results/canonical-three-qubit-development/events.jsonl`, `data/results/canonical-three-qubit-development/result.json`, `tests/test_canonical_cli.py`
- **Committed in:** `d315072`

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

The canonical public path now supplies verified manifest, execution, ledger, and result evidence for the remaining Phase 2 integration work.

## Self-Check: PASSED

- Confirmed all four checked canonical schema/manifest/result artifacts exist.
- Confirmed all six task commits are present in Git history.
