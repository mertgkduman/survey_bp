---
phase: 03-update-rules-and-scheduling
plan: "02"
subsystem: canonical-update-rules
tags: [normalized-min-sum, nms, parameter-assignment, manifest-schema, verification]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: V3 min-sum local-step tracer and immutable canonical EdgeTable ordering
provides:
  - graph-bound scalar, source-iteration, check, and edge normalization assignments
  - public normalized-min-sum execution with independently reconstructed assignment evidence
  - generated V3 schema and executable NMS documentation while retaining V2 serialization
affects: [03-update-rules-and-scheduling, offset-min-sum, parameter-generation, scheduling]
plan_head_before: c37cf914d384c3f1a37efdf3d6b7a367508d84b6
commits: 4
actuals:
  tokens: 15440
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - V3-only persisted extensions preserve V2 manifest serialization and sampling identities
    - explicit parameter assignments resolve against immutable check-major EdgeTable identities before execution
key-files:
  created:
    - data/manifests/schema-canonical-v3.json
  modified:
    - src/bp_registry/canonical/updates.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/runner.py
    - docs/canonical-engine.md
    - tests/canonical/test_update_rules.py
    - tests/test_manifest.py
    - tests/test_canonical_cli.py
key-decisions:
  - "NMS accepts one explicit tagged assignment rather than implicit scalar/vector broadcasting."
  - "The NMS policy contract is V3-only so historical V2 payloads, identity digests, and SPA results remain unchanged."
requirements-completed: [UPD-01, UPD-02]
coverage:
  - id: D1
    description: "Strict scalar, source-iteration, check, and canonical-edge normalization assignment resolution with numerical boundaries."
    requirement: UPD-02
    verification:
      - kind: unit
        ref: "tests/canonical/test_update_rules.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Public V3 normalized-min-sum preflight, execution, generated schema, documentation, and independent verify-run replay."
    requirement: UPD-02
    verification:
      - kind: integration
        ref: "tests/test_manifest.py and tests/test_canonical_cli.py"
        status: pass
    human_judgment: false
duration: 14m
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 02: Normalized Min-Sum Contract Summary

**Normalized min-sum now uses strict graph-bound assignments with independently replayed evidence, a generated V3 public schema, and executable documentation.**

## Performance

- **Duration:** 14m
- **Started:** 2026-09-24T09:33:24Z
- **Completed:** 2026-09-24T09:46:58Z
- **Tasks:** 2/2
- **Files modified:** 12

## Accomplishments

- Added `NormalizedMinSumUpdate` and one tagged `ParameterAssignment` model for scalar, source-iteration, check, and canonical-edge alpha values; invalid, nonfinite, mismatched, and implicitly broadcast assignments are rejected.
- Bound check and edge assignments to a stable immutable EdgeTable hash, recorded declared/resolved values and conventional-versus-exploratory provenance, and replayed those facts through public `verify-run`.
- Generated the V3 schema and documented the NMS equations, numerical boundaries, assignment shapes, public commands, and V2 compatibility boundary.

## Task Commits

1. **Task 1: Run scalar and graph-indexed normalized min-sum end to end** — `675ed76` (RED tests), `f1816fe` (implementation).
2. **Task 2: Export and document the executable min-sum/NMS contract** — `5d203f0` (RED tests), `5a285da` (implementation, schema, and documentation).

## Verification

- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/test_manifest.py tests/test_canonical_cli.py -k 'normalized or assignment or alpha'` — 10 passed.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py tests/test_canonical_cli.py -k 'canonical_v3 or min_sum or normalized or tamper or documented'` — 13 passed.
- Full plan suite was run in bounded groups: 54 core tests, 18 terminal/provenance tests, and 16 remaining public-CLI tests all passed.
- Generated-schema equality, temporary-directory NMS CLI `preflight`/`canonical`/`verify-run`, and `git diff --check` passed.

## Decisions Made

- Keep `parameter_assignment` exclusively in V3 policy models; extending the shared V2 model changes old manifest digests and would alter matched sample identities.
- Classify `0 < alpha <= 1` as conventional and finite `alpha > 1` as exploratory; negative or nonfinite alpha is invalid.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Compatibility] Kept V2 policy serialization isolated from V3 parameter assignments.**
   - **Found during:** Task 2 verification.
   - **Issue:** Adding `parameter_assignment` to the shared policy model modified V2 manifest digests and changed its sampled fixture outcomes.
   - **Fix:** Introduced V3-only update/composition models and restored byte-stable V2 serialization.
   - **Files modified:** `src/bp_registry/canonical/contracts.py`, `src/bp_registry/manifests.py`, `src/bp_registry/runner.py`.
   - **Verification:** Historical V2 flooding checks and the complete selected plan suite passed.
   - **Committed in:** `5a285da`.

2. **[Rule 3 - Worktree environment] Scoped generation and verification to the active worktree source.**
   - **Found during:** Task 2 verification.
   - **Issue:** The editable environment resolved `bp_registry` from the main checkout, not this worktree.
   - **Fix:** Ran schema generation and verification with `PYTHONPATH="$PWD/src"`.
   - **Files modified:** None.
   - **Verification:** Generated schema equals the active V3 model and all listed suites passed.
   - **Committed in:** N/A (execution environment only).

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3). The changes preserve the plan's compatibility and reproducibility boundaries without broadening its feature scope.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The V3 NMS contract is ready for Plan 03-11's offset-min-sum, seeded parameter generation, and configurable refresh extensions. The V2 SPA/flooding public evidence remains unchanged.

## Self-Check: PASSED

- All listed created and modified artifacts exist in this worktree.
- All four task commits are reachable from the plan base.
- No stubs, skipped tests, unrun verifications, or unplanned network/auth/schema trust surface remain.

---
*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
