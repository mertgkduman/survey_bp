---
phase: 03-update-rules-and-scheduling
plan: "13"
subsystem: canonical-public-contract
tags: [canonical-decoder, policy-matrix, scheduling, verification, json-schema]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: local schedule engines, V3 schedule evidence, and public manifest preflight
provides:
  - Strict public admission and independent verification for every implemented noncluster Phase 3 policy
  - Generated V3 schema and executable documentation for the focused update/schedule matrix
  - Pre-sampling rejection of undefined policy and randomized-base combinations
affects: [phase-03-verification, pilot-experiments, reproduction-manifests]
actuals:
  tokens: 13371
  tasks: 2
  commits: 7
plan_head_before: 2ee24548f80ecbde9102b4e1dd06fe43d151e666
tech-stack:
  added: []
  patterns:
    - Closed V3 manifest compatibility registry checked before sampling or ledger creation
    - Independent terminal reconstruction for each admitted local scheduling policy
key-files:
  created:
    - .planning/phases/03-update-rules-and-scheduling/03-13-task-1-red-evidence.json
    - .planning/phases/03-update-rules-and-scheduling/03-13-task-2-red-evidence.json
  modified:
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/manifests.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - data/manifests/schema-canonical-v3.json
    - docs/canonical-engine.md
    - tests/test_manifest.py
    - tests/test_canonical_cli.py
key-decisions:
  - "Public V3 admits only the explicitly implemented SPA local schedules; randomized traversal is currently layered-base only."
  - "Unsupported policy combinations fail at strict manifest validation/preflight, before sampling or ledger emission."
requirements-completed: [UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05]
coverage:
  - id: D1
    description: "Every supported noncluster SPA schedule completes public run, ledger, result reconstruction, and verify-run round-trips."
    requirement: SCH-02
    verification:
      - kind: integration
        ref: "tests/test_canonical_cli.py#test_public_noncluster_spa_schedules_round_trip_and_reconstruct"
        status: pass
    human_judgment: false
  - id: D2
    description: "Closed compatibility rules reject undefined update, schedule, partition, refresh, and randomized-base combinations before sampling."
    requirement: SCH-05
    verification:
      - kind: unit
        ref: "tests/test_manifest.py#test_v3_public_schedule_matrix_admits_only_the_implemented_spa_local_schedules"
        status: pass
    human_judgment: false
  - id: D3
    description: "Generated schema and canonical-engine documentation expose the same focused policy and evidence contract as the strict runtime."
    requirement: UPD-03
    verification:
      - kind: integration
        ref: "tests/test_manifest.py and tests/test_canonical_cli.py (-k 'schema or documented or compatibility')"
        status: pass
    human_judgment: false
duration: 19 min
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 13: Complete Public Noncluster Policy Matrix Summary

**Strict public V3 execution, evidence reconstruction, schema, and documentation for all implemented noncluster BP update and scheduling policies.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-24T10:45:39Z
- **Completed:** 2026-09-24T11:05:07Z
- **Tasks:** 2/2
- **Files modified:** 10
- **Verification:** 106 focused contract, manifest, CLI, and ledger tests passed in three bounded batches.

## Accomplishments

- Exposed serial check-node, serial variable-node, residual, and randomized SPA schedules through the strict V3 manifest, public canonical runner, ledger/result reconstruction, and `verify-run` paths.
- Kept the matrix focused: only registered compatible compositions run, while undefined kernels, updates, schedules, partitions, refresh controls, and randomized bases reject before sampling.
- Regenerated the V3 schema and expanded the canonical-engine guide with local units, work/budget views, evidence, replay boundaries, and compatibility reasons.

## TDD Evidence

- Task 1 RED evidence: `03-13-task-1-red-evidence.json` validates with `RED_EVIDENCE_OK`; the target strict policy-matrix test initially failed because the schedule kind was not admitted.
- Task 2 RED evidence: `03-13-task-2-red-evidence.json` validates with `RED_EVIDENCE_OK`; the target documentation contract initially failed because the required public policy text was absent.
- GREEN and full acceptance verification passed after implementation.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: public schedule-matrix contract** - `753af3e` (test)
2. **Task 1 RED evidence correction** - `e476edb` (test)
3. **Task 1 GREEN: public schedules and verification** - `6a4cc09` (feat)
4. **Task 1 follow-up: reject unsupported randomized bases before sampling** - `1921f5d` (fix)
5. **Task 2 RED: policy-documentation contract** - `1bf1840` (test)
6. **Task 2 GREEN: schema and canonical-engine guide** - `50fd381` (docs)

## Files Created/Modified

- `src/bp_registry/canonical/contracts.py` - V3 schedule controls and pre-sampling randomized-base validation.
- `src/bp_registry/manifests.py` - Closed public SPA/min-sum compatibility admission with stable rejection text.
- `src/bp_registry/canonical/execution.py` - Public local-schedule factory and schedule-specific terminal evidence.
- `src/bp_registry/canonical/verification.py` - Independent reconstruction for all admitted local schedule families.
- `data/manifests/schema-canonical-v3.json` - Schema generated from the strict public models.
- `docs/canonical-engine.md` - Complete executable policy matrix, units, evidence, replay, and rejection guidance.
- `tests/test_manifest.py`, `tests/test_canonical_cli.py` - Strict matrix, preflight, documented-contract, round-trip, and replay coverage.

## Decisions Made

- Kept public composition admission closed and explicit rather than implying that every update and schedule combination is interchangeable.
- Restricted public randomized traversal to an implemented layered base and made other bases fail before sampling, preserving the no-partial-evidence guarantee.
- Preserved V2 behavior and its historical compatibility diagnostic while adding V3 local-schedule support.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Preserved the established V2 compatibility diagnostic**
- **Found during:** Task 2
- **Issue:** The new strict rejection wording caused the historical V2 compatibility assertion to lose its expected stable wording.
- **Fix:** Retained the historical `executable canonical baseline` and `flooding/layered` terms in the stricter compatibility diagnostic.
- **Files modified:** `src/bp_registry/manifests.py`
- **Verification:** Full focused suite passed.
- **Committed in:** `50fd381`

**2. [Rule 2 - Missing critical functionality] Rejected unimplemented randomized bases at preflight**
- **Found during:** Task 1 follow-up validation
- **Issue:** A randomized serial base could pass the generic V3 model and reach factory selection after the no-sampling boundary.
- **Fix:** Restricted public randomized traversal to its implemented layered base in the V3 schedule contract and added an explicit preflight test.
- **Files modified:** `src/bp_registry/canonical/contracts.py`, `tests/test_manifest.py`
- **Verification:** Target matrix test passed; all 106 focused tests passed.
- **Committed in:** `1921f5d`

---

**Total deviations:** 2 auto-fixed (1 regression, 1 missing critical compatibility gate).
**Impact on plan:** Both fixes tighten the stated public contract without expanding its supported policy surface.

## Issues Encountered

The full suite exceeds the command runner's 30-second output window, so it was verified as three non-overlapping batches: 29 CLI tests, 29 CLI tests, and 48 contract/manifest/ledger tests. All batches passed.

## Known Stubs

None.

## Next Phase Readiness

The focused noncluster Phase 3 public contract is executable and independently verifiable. Later pilots can select only the documented compatible policy compositions and retain pre-sampling rejection evidence for all unsupported combinations.

## Self-Check: PASSED

All nine listed implementation, schema, documentation, test, and summary files exist. All six task commits are reachable; the seventh measured commit is this summary metadata commit.

---
*Phase: 03-update-rules-and-scheduling*
*Plan: 13*
*Completed: 2026-09-24*
