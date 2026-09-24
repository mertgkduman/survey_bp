---
phase: 03-update-rules-and-scheduling
plan: "11"
subsystem: canonical-update-rules
tags: [offset-min-sum, parameter-generation, refresh, rng-provenance, schema]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: V3 min-sum assignments and schedule-qualified source iteration progress
provides:
  - strict public offset min-sum with float64 beta boundaries
  - replayable purpose-separated generated parameter assignments
  - atomic configuration, attempt, and source-iteration refresh contracts
affects: [pilot-comparisons, randomized-scheduling, policy-provenance]
plan_head_before: 5bec80c0d767b33f5d9cdb557825a1206e78853f
commits: 6
actuals:
  tokens: 47134
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns:
    - Generated parameter streams use an explicit parameter_assignment purpose identity distinct from sampling and schedule order.
    - Refresh reserves before cloning PCG64 state and commits assignment evidence and RNG advancement together.
key-files:
  created: []
  modified:
    - src/bp_registry/canonical/updates.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/manifests.py
    - data/manifests/schema-canonical-v3.json
    - docs/canonical-engine.md
    - tests/canonical/test_update_rules.py
    - tests/canonical/test_contracts.py
    - tests/test_manifest.py
    - tests/test_sampling.py
key-decisions:
  - "OMS subtracts finite beta from the raw float64 minimum, floors at zero, then applies the inherited named output saturation."
  - "Generated parameter values use only the parameter_assignment purpose stream and persist algorithm/version, bounds, graph, derivation, scope, and resolved assignment evidence."
requirements-completed: [UPD-03, SCH-05]
coverage:
  - id: D1
    description: "Public V3 offset min-sum admission and exact beta boundary semantics."
    requirement: UPD-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_update_rules.py#test_offset_min_sum_matches_independent_float64_boundary_oracle"
        status: pass
      - kind: integration
        ref: "run_canonical_one source-iteration OMS temporary-manifest smoke test"
        status: pass
    human_judgment: false
  - id: D2
    description: "Replayable generated scalar/check/edge assignments with configuration, attempt, and source-iteration boundaries."
    requirement: SCH-05
    verification:
      - kind: unit
        ref: "tests/canonical/test_update_rules.py#test_parameter_generation_replays_and_commits_only_after_admission"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_contracts.py#test_v3_generated_assignment_requires_closed_generator_and_refresh_models"
        status: pass
    human_judgment: false
  - id: D3
    description: "Parameter policy identity remains independent of the matched physical sample stream."
    requirement: SCH-05
    verification:
      - kind: integration
        ref: "tests/test_sampling.py#test_parameter_assignment_identity_does_not_consume_or_relabel_physical_samples"
        status: pass
    human_judgment: false
duration: 9m
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 11: Offset Min-Sum and Parameter Refresh Summary

**Offset min-sum, strict graph-bound beta assignments, and purpose-separated replayable parameter refresh now extend the V3 canonical update surface.**

## Performance

- **Duration:** 9m
- **Started:** 2026-09-24T09:55:34Z
- **Completed:** 2026-09-24T10:04:34Z
- **Tasks:** 2/2
- **Files modified:** 11

## Accomplishments

- Added `OffsetMinSumUpdate`, whose beta-zero/equality/adjacent/zero-floor/sign/saturation boundaries are independently tested and which remains graph-bound for check and edge assignments.
- Admitted OMS as a closed V3 update policy while preserving V2 meanings; source-iteration assignments now retain schedule iteration rather than collapsing to a local-unit count.
- Added `ParameterGeneratorSpec` and `ParameterRefreshPlan` for bounded uniform PCG64 generation, deterministic evidence, atomic denied-refresh rollback, and independent physical sampling.
- Regenerated the V3 schema and documented generated-assignment domains, scope boundaries, provenance labels, and replay evidence.

## Task Commits

1. **Task 1 RED: failing offset min-sum contract** — `129bd4d` (`test`)
2. **Task 1 GREEN: strict offset min-sum update** — `c95377e` (`feat`)
3. **Task 2 RED: failing generated assignment contract** — `f0ed81e` (`test`)
4. **Task 2 GREEN: replayable parameter generation** — `f211c07` (`feat`)
5. **Task 2 follow-up: source-iteration resolver correction** — `f0b79e1` (`fix`)

## Verification

- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/test_manifest.py -k 'offset or beta or iteration_assignment'` — 10 passed.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/canonical/test_contracts.py tests/test_manifest.py tests/test_sampling.py` — 64 passed.
- A temporary V3 OMS manifest using a `source_iteration` beta array completed `run_canonical_one` successfully.
- `git diff --check` passed.

## Decisions Made

- OMS computes the minimum from finite input before beta subtraction, then applies the zero floor and profile saturation; this keeps the subtraction and saturation boundaries independently visible.
- Only closed `numpy.PCG64` uniform generators are accepted. Generated values are labeled either `source_defined` with an anchor or `exploratory`; the latter cannot claim source-defined status.
- Generator, schedule-order, and physical-sampling randomness are separate purpose identities. A denied refresh never advances its PCG64 state or assignment evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Boundary oracle] Corrected the expected sign of a syndrome-negated adjacent-beta test value.**
- **Found during:** Task 1 GREEN verification.
- **Issue:** The hand oracle correctly retained the syndrome sign, but the new test expected the unsigned adjacent difference.
- **Fix:** Corrected the expected negative float64-adjacent value.
- **Files modified:** `tests/canonical/test_update_rules.py`
- **Verification:** Offset boundary suite passed.
- **Committed in:** `c95377e`

**2. [Rule 1 - Source-iteration resolution] Prevented graph resolution from flattening temporal assignments.**
- **Found during:** Task 2 integration review.
- **Issue:** Resolving a `source_iteration` assignment at construction would have frozen it at iteration zero.
- **Fix:** Retained temporal assignments in the update rule while continuing to resolve check/edge shapes against the immutable edge table.
- **Files modified:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`
- **Verification:** OMS source-iteration public smoke test and 64-test suite passed.
- **Committed in:** `f0b79e1`

**Total deviations:** 2 auto-fixed (2 Rule 1). **Impact:** Both corrections preserve the specified numerical and schedule-boundary semantics without widening the policy surface.

## Issues Encountered

The full CLI-inclusive regression invocation exceeded the execution terminal's 30-second streaming limit after reporting passing progress, so the plan-specific 64-test suite and direct public OMS smoke test were run to completion in bounded groups.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The V3 models and atomic refresh primitive are ready for public schedule admission and bounded parameter-diversity pilot examples. Later work must wire generated-refresh execution into each newly admitted non-flooding public schedule while retaining these persisted scope boundaries.

## Self-Check: PASSED

- All eleven listed implementation, schema, documentation, and test artifacts exist in this worktree.
- Task commits `129bd4d`, `c95377e`, `f0ed81e`, `f211c07`, and `f0b79e1` are reachable from the plan base.
- No intentional stubs, skipped tests, or new network/auth trust surface was introduced.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
