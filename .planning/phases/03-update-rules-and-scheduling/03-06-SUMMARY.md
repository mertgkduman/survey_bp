---
phase: 03-update-rules-and-scheduling
plan: "06"
subsystem: canonical-css-public-execution
tags: [layered-schedule, binary-spa, canonical-executor, public-cli, provenance]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: V3 local-step work accounting, schedule semantics, and public update-rule contracts
provides:
  - Strict V3 binary-SPA/layered public manifest admission with explicit partitions and provenance
  - Public preflight, run, and verify-run traversal through CanonicalLocalStepExecutor
  - Reconstructed layered schedule progress, work, budget views, and realized ordering evidence
affects: [phase-03-pilot-comparisons, schedule-policy-admission, canonical-results]
actuals:
  tokens: 62110
  tasks: 1
  commits: 4
plan_head_before: 85d2d976174f417cf75a156a4b4784f012501e87
tech-stack:
  added: []
  patterns:
    - V3 public policy admission binds a closed update/schedule composition before factory creation.
    - Layered public terminals retain a nested V3 schedule evidence record while historical V2 flooding fields remain byte-stable.
key-files:
  created:
    - .planning/phases/03-update-rules-and-scheduling/03-06-task-1-red-evidence.json
  modified:
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - data/manifests/schema-canonical-v3.json
    - tests/test_manifest.py
    - tests/test_canonical_cli.py
    - docs/canonical-engine.md
key-decisions:
  - "Layered public admission is closed to binary SPA with cpu-float64-spa-v1; min-sum remains flooding-only until separately promoted."
  - "Layered terminals preserve explicit schedule evidence, a V3 full work vector, and distinct budget views without changing V2 flooding records."
requirements-completed: [SCH-02]
coverage:
  - id: D1
    description: "Strict public V3 layered-SPA manifest preflights, runs through the local-step executor, and verifies through the CLI."
    requirement: SCH-02
    verification:
      - kind: integration
        ref: "tests/test_canonical_cli.py#test_layered_spa_public_manifest_preflights_runs_and_verifies_through_local_executor"
        status: pass
    human_judgment: false
  - id: D2
    description: "Layered schedule policy requires explicit partitions/provenance and rejects unimplemented min-sum/layered combinations."
    requirement: SCH-02
    verification:
      - kind: unit
        ref: "tests/test_manifest.py#test_v3_layered_spa_admission_requires_explicit_partitions_and_rejects_unimplemented_pairs"
        status: pass
    human_judgment: false
  - id: D3
    description: "Historical V2 flooding manifests and V3 schema generation remain valid alongside layered admission."
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/test_manifest.py tests/test_canonical_cli.py -k 'layered or canonical_v3 or historical'"
        status: pass
    human_judgment: false
duration: 14 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 06: Public Layered SPA Tracer Summary

**A strict V3 layered-SPA composition now runs through the canonical local-step executor and independently verifies its public schedule evidence without changing historical flooding behavior.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-24T10:26:59Z
- **Completed:** 2026-09-24T10:40:53Z
- **Tasks:** 1/1
- **Files modified:** 10

## Accomplishments

- Admitted the first public non-flooding policy pair: binary SPA plus a manifest-defined layered schedule with explicit partitions and provenance.
- Routed the public runner through `CanonicalLocalStepExecutor`, retained realized layer order/progress/work/budget evidence, and independently replayed it in `verify-run`.
- Preserved historical V2 binary-SPA/flooding dispatch and regenerated the strict V3 JSON schema from its authoritative model.

## Task Commits

1. **Task 1 RED: failing layered-SPA public tracer** — `74f4bbf` (`test`)
2. **Task 1 GREEN: public layered SPA execution and verification** — `d4b0079` (`feat`)
3. **Task 1 documentation closure** — `bef5121` (`docs`)

## Verification

- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py -k layered_spa_public_manifest` — **1 passed**.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/test_manifest.py tests/test_canonical_cli.py -k 'layered or canonical_v3 or historical'` — **3 passed**.
- `tests/test_canonical_cli.py` split into bounded groups — **53 passed**.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/test_manifest.py tests/test_ledger.py` — **43 passed**.
- `git diff --check` — **passed**.

## Files Created/Modified

- `src/bp_registry/canonical/contracts.py` — V3 layered schedule policy contract with persisted partitions/provenance.
- `src/bp_registry/manifests.py` and `src/bp_registry/runner.py` — closed layered-SPA admission and public factory selection.
- `src/bp_registry/canonical/execution.py` and `src/bp_registry/canonical/verification.py` — executor-backed layered run and independent terminal reconstruction.
- `data/manifests/schema-canonical-v3.json` — generated strict public schema.
- `tests/test_manifest.py`, `tests/test_canonical_cli.py`, and `docs/canonical-engine.md` — admission, real CLI, historical-compatibility, and public-contract coverage.

## Decisions Made

- Layered public execution is a closed binary-SPA/cpu-float64-spa-v1 pair, keeping unsupported min-sum/layered combinations out of the executable registry.
- Layered schedule progress and full V3 work remain explicit evidence beside historical V2 public fields; neither budget view is converted into an aggregate cost.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical documentation] Documented the expanded V3 public policy surface.**
- **Found during:** Task 1 acceptance review.
- **Issue:** The canonical-engine guide still described V3 as min-sum-only after layered-SPA admission.
- **Fix:** Documented the layered composition, explicit partition/provenance contract, and retained schedule evidence; added a documentation regression assertion.
- **Files modified:** `docs/canonical-engine.md`, `tests/test_canonical_cli.py`.
- **Verification:** Documentation and layered CLI tests passed.
- **Committed in:** `bef5121`.

**Total deviations:** 1 auto-fixed (1 Rule 2). **Impact:** Keeps the public scientific contract aligned with executable and schema-backed behavior.

## Issues Encountered

The full CLI regression file exceeds the terminal's 30-second streaming window, so it was run in two bounded groups; together they passed all 53 tests.

## Known Stubs

None.

## Next Phase Readiness

Later schedule families can use the same public V3 admission, factory, and nested schedule-evidence pattern. Layered min-sum remains deliberately unavailable until separately promoted with its own compatibility evidence.

## Self-Check: PASSED

- Confirmed all declared source, schema, documentation, tests, and RED-evidence artifacts exist.
- Confirmed task commits `74f4bbf`, `d4b0079`, and `bef5121` are reachable from the recorded plan base.
- No stubs, skipped tests, unrun verification, or newly introduced trust boundary remains.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
