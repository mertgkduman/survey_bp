---
phase: 11-quaternary-reproduction-and-comparisons
plan: "09"
subsystem: controlled quaternary campaign execution
tags: [GB46, quaternary-BP, canonical-SPA, replay, calibration]
requires:
  - phase: 11-07
    provides: typed matched joint-versus-separate pair contract
  - phase: 11-08
    provides: fixed-marginal three-point correlation design and assessment
provides:
  - Public bounded GB46 controlled-calibration lifecycle with immutable paired evidence
  - Deterministic shard, replay, verification, and assessment receipts
affects: [11-10, 11-11, quaternary controlled comparisons]
actuals:
  tokens: 8304
  tasks: 2
  commits: 2
plan_head_before: 4d3e02d35226acedf279ad361723d397fea3b828
tech-stack:
  added: []
  patterns: [digest-bound raw code input, complete-pair-only assessment, explicit empty shard receipt]
key-files:
  created: [data/artifacts/gb46-h44.alist, data/studies/phase11-gb46-joint-separate.json, scripts/run_phase11_controlled.py]
  modified: [src/bp_registry/campaigns/controlled_execution.py, tests/test_phase11_quaternary_campaign.py]
key-decisions:
  - "Pin GB46 source check bytes and label every receipt as canonical-adaptation calibration evidence."
  - "Use the existing scalar four-state and canonical binary SPA kernels against one sealed sample per pair."
  - "Keep publication authorization at deny for every preflight, run, shard, verify, replay, and assessment receipt."
patterns-established:
  - "A controlled quaternary output may be assessed only after every declared point has complete replayable matched pairs."
requirements-completed: [QEV-02]
coverage:
  - id: D1
    description: Public GB46 bounded-calibration command exposes preflight, run, resume, merge, replay, verify, and assess.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_quaternary_campaign.py#test_installed_cli_exposes_phase11_controlled_lifecycle
        status: pass
    human_judgment: false
  - id: D2
    description: Three fixed-marginal points have disjoint deterministic ranges and reject an empty shard as an assessment.
    requirement: QEV-02
    verification:
      - kind: integration
        ref: tests/test_phase11_quaternary_campaign.py#test_gb46_three_point_design_has_disjoint_calibration_ranges
        status: pass
      - kind: integration
        ref: tests/test_phase11_quaternary_campaign.py#test_gb46_empty_shard_is_explicitly_incomplete
        status: pass
    human_judgment: false
duration: 34min
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 09: Bounded GB46 Controlled Calibration Summary

**Pinned GB46 paired joint-versus-separate BP calibration with digest-bound shards, replay, verification, and fixed-design assessment.**

## Performance

- **Duration:** 34 min
- **Completed:** 2026-10-14T21:18:43Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added the exact pinned GB46 H input and a calibration-only three-point manifest with two disjoint pairs per point.
- Shipped public preflight, run, resume, merge, replay, verify, and assess commands; output receipts keep production authorization at `deny`.
- Executed the bounded lifecycle against a temporary root: six complete pairs ran, replayed, verified, and assessed; altered pair evidence failed verification.

## Task Commits

1. **Task 1: Run and replay one public GB46 independence pair** - `4d3e02d` (test), `66f8804` (feat)
2. **Task 2: Execute disjoint bounded GB46 calibration shards at all three points** - `dcac191` (feat)

## Files Created/Modified

- `data/artifacts/gb46-h44.alist` - byte-pinned GB46 source check input.
- `data/studies/phase11-gb46-joint-separate.json` - bounded calibration identity, ranges, and limits.
- `scripts/run_phase11_controlled.py` - public lifecycle wrapper.
- `src/bp_registry/campaigns/controlled_execution.py` - sealed sampling, canonical decoding adapters, shard receipts, and assessment admission.
- `tests/test_phase11_quaternary_campaign.py` - public route, three-point, empty-shard, and full lifecycle integrity regressions.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py -k 'tracer or installed_cli or one_pair or replay or tamper or output_root' -x` — 1 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py -k 'gb46 and (three_point or shard or resume or merge or overlap or duplicate or empty or lane)' -x` — 2 passed.
- Direct temporary-root lifecycle run, replay, verify, and assess — passed with 6 complete pairs; tampered pair verification returned a structured error.

## Decisions Made

- The only imported source bytes are the pinned GB46 aList input. The derived execution is explicitly `canonical_adaptation`, never source reproduction.
- The joint arm uses the project scalar four-state kernel and separate arms use the existing canonical binary SPA kernel. Hidden errors remain outside decoder callback inputs and the independent evaluator owns classification.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Recovered the missing GB46 check artifact from the pinned Phase 10 source identity.**
- **Found during:** Task 1
- **Issue:** The planned raw GB46 input was not materialized in the repository, while the Phase 10 parser required exact bytes.
- **Fix:** Added the exact digest-validated aList source input and bound it in the calibration design.
- **Verification:** Parser and preflight accepted `4bd60bc22ccda388780ad2ad2a29b63143b3f024e599e57ef5bcb983f51cb9b2`.
- **Committed in:** `66f8804`

**2. [Rule 3 - Blocking] Implemented the lifecycle in the existing controlled execution module.**
- **Found during:** Task 1
- **Issue:** The plan referenced `public_execution.py`, but that module is absent; the repository's relevant typed matched-pair seam is `controlled_execution.py`.
- **Fix:** Kept the lifecycle beside that seam and exposed it through the requested public script.
- **Verification:** Installed CLI and bounded lifecycle tests pass.
- **Committed in:** `66f8804`

**Total deviations:** 2 blocking recovery deviations.

## Known Stubs

None.

## Next Phase Readiness

The controlled GB46 path is ready for bounded resource measurement. Its receipts cannot authorize a production or publication-scale dispatch; Plan 11-11 remains the required human decision boundary.

## Self-Check: PASSED

- Found all five code, design, artifact, script, and test files.
- Found task commits `4d3e02d`, `66f8804`, and `dcac191`.

---
*Phase: 11-quaternary-reproduction-and-comparisons*
*Completed: 2026-10-14*
