---
phase: 11-quaternary-reproduction-and-comparisons
plan: "03"
subsystem: quaternary source reproduction
tags: [mbp4, deterministic-replay, source-target, provenance, pytest]
requires:
  - phase: 11-02
    provides: Q-BPGD source-target qualification and source-study command surface
provides:
  - Frozen MBP4 Figures 8-9 five-qubit source target and source-only manifest
  - Deterministic alpha=1 oscillation and alpha=1.5 convergence assessment with typed work
  - Independent target/original-problem/replay regression coverage and blocked Figure 6 metadata
affects: [phase-11-source-reproduction, QEV-01]
actuals:
  tokens: 12296
  tasks: 2
  commits: 2
plan_head_before: 18302ddbad2b120abc8e04f03cbcaeb4a6f380b2
tech-stack:
  added: []
  patterns: ["Source-target receipts bind finite deterministic trajectories separately from statistical curves", "Independent evaluator checks frozen MBP4 candidates against the immutable original problem"]
key-files:
  created:
    - data/source-targets/phase11-mbp4-figures8-9-five-qubit.json
    - data/manifests/phase11-mbp4-figures8-9-five-qubit.json
    - data/results/phase11-mbp4-figures8-9/assessment.json
    - tests/canonical/quaternary/test_phase11_mbp4_target.py
  modified:
    - scripts/run_phase11_source_studies.py
key-decisions:
  - "Use the paper's five-qubit Figures 8-9 mechanism as finite deterministic evidence, not a curve reproduction."
  - "Freeze a 20-sweep horizon for alpha=1 and retain Figure 6 as blocked until its statistical metadata is resolved."
patterns-established:
  - "Bind source target, manifest, ledger, and assessment with receipt and deterministic replay digests."
requirements-completed: [QEV-01]
coverage:
  - id: D1
    description: "The selected MBP4 Figures 8-9 mechanism replays an alpha=1 oscillation with an independent trajectory oracle."
    requirement: QEV-01
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_phase11_mbp4_target.py (tracer selection)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The alpha=1.5 path converges to IIIYI under original-problem evaluation while Figure 6 remains blocked metadata."
    requirement: QEV-01
    verification:
      - kind: unit
        ref: "tests/canonical/quaternary/test_phase11_mbp4_target.py (convergence/blocked selection)"
        status: pass
    human_judgment: false
duration: 11m
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 03: MBP4 Figures 8-9 Mechanism Summary

**Frozen five-qubit MBP4 evidence reproduces the finite alpha=1 oscillation and alpha=1.5 exact convergence without making a curve, threshold, or ranking claim.**

## Performance

- **Duration:** 11m
- **Started:** 2026-10-14T20:40:00Z
- **Completed:** 2026-10-14T20:51:46Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added a receipt-bound Figures 8-9 target for the `IIIYI` five-qubit mechanism with epsilon `0.003`, parallel flooding, beta `0`, and a fixed 20-sweep observation horizon.
- Recorded alpha=1 oscillatory and alpha=1.5 exact-convergence paths with sweep candidates, belief digests, typed work, independent original-problem outcomes, and byte-identical replay evidence.
- Preserved Figure 6 as `blocked_metadata` because its iteration cap, denominator, stopping rule, coordinates, and interval method remain unresolved.

## Task Commits

1. **Task 1: Replay the alpha=1 oscillation from target receipt to assessment** - `c49e0b1` (feat)
2. **Task 2: Verify alpha=1.5 convergence and preserve curve metadata gaps** - `ee8a876` (feat)

## Files Created/Modified

- `scripts/run_phase11_source_studies.py` - validates and runs the bounded MBP4 study, then byte-compares regenerated assessment evidence.
- `data/source-targets/phase11-mbp4-figures8-9-five-qubit.json` - freezes source parameters and independent expected trajectories.
- `data/manifests/phase11-mbp4-figures8-9-five-qubit.json` - binds source-only scope, digests, and Figure 6 blockers.
- `data/results/phase11-mbp4-figures8-9/assessment.json` - stores deterministic ledger, replay digest, typed work, and claim limits.
- `tests/canonical/quaternary/test_phase11_mbp4_target.py` - independently checks candidate syndromes, expected beliefs, replay, work, and metadata scope.

## Decisions Made

- Treated the Figures 8-9 example as deterministic mechanism evidence only; it cannot support a paper-performance, threshold, or decoder-ranking claim.
- Held the problem, injected error, epsilon, schedule, beta, numerical profile, and observation horizon constant between paths; alpha is the only contrast field.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the identity lineage edge used for independent candidate evaluation**
- **Found during:** Task 1
- **Issue:** The first assessment run constructed `LineageEdge` arguments in the wrong order, so the independent working problem rejected the candidate lineage.
- **Fix:** Constructed the typed identity edge as relation, original parent, then working child.
- **Files modified:** `scripts/run_phase11_source_studies.py`
- **Verification:** Source-study run and replay succeeded; all focused target tests pass.
- **Committed in:** `c49e0b1`

**Total deviations:** 1 auto-fixed (1 Rule 1 bug).
**Impact on plan:** The correction was necessary to preserve independent original-problem evaluation; scope remains the selected deterministic mechanism.

## Issues Encountered

None after the lineage correction.

## Known Stubs

None.

## Self-Check: PASSED

- Found all five plan artifacts and task commits `c49e0b1` and `ee8a876`.

## Next Phase Readiness

The source-study command now has a bounded MBP4 mechanism target. Figure 6 remains unavailable for statistical assessment until its missing metadata is source-qualified.

---
*Phase: 11-quaternary-reproduction-and-comparisons*
*Completed: 2026-10-14*
