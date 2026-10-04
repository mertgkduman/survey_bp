# Quick-task implementation check (2026-10-04)

## Contract review

- The same `BPSegment` object from one min-sum initial run is passed to BeamSearch and RelayBP within each damping arm. Foreign initial states are rejected.
- `g1000` (off) and `g0500` (on) run on the same BB72 physical sample IDs. Both methods use the same initial numerical profile, schedule, stop check and damping at each gamma.
- Relay extra units use source-shaped per-variable disordered affine-prior memory, posterior-only transfer, and reset message/damping histories. The pinned native Relay source initializes subsequent-leg V2C messages from channel priors (`relay.rs` lines 333-342; `min_sum.rs` lines 270-279). The common plain initial BP stage is an explicit controlled adaptation of the paper's memory-BP first leg.
- Beam extra units use source-shaped min-sum masked branches with adjusted syndrome, surviving-edge warm start, cumulative LLR reliability and stable pruning. The CSS use and damping addition are controlled adaptations, not a circuit reproduction or pinned-C++ edge-case reproduction.
- Initial and extra typed work, unit statuses, original-syndrome candidates, independent CSS outcomes, and observed serial runtime are separate evidence fields. A common extra C2V cap is enforced before each run; actual spent work is reported.

## Verification

- 13 focused new tests pass; 46 combined new/Relay/memory tests pass after the damping-factorial runner revision.
- Eight BB72 matched physical samples run in four arms (Beam and Relay, each at gamma 1.0 and 0.5); both replay verification and fixed-denominator checks pass. The result is `not_assessed` and makes no ranking claim.
- Full worktree suite: 737 passed, 1 skipped, 1 failed solely because a historical untracked Phase 4 cancellation receipt is absent from the isolated checkout. The same receipt test passes in the original workspace (1 passed). No existing source file was modified by this quick task.

## Remaining integration

- Rebuild the full Phase 6 plans around `06-CONTEXT.md`; the former ten plans and their check/validation files are archived as superseded.
- The active BB72 BP-SF v2 source seal keeps this code in its feature worktree until the original run/publisher finish. Merge to main and publish the feature then.
- This eight-shot fixture is not a parameter-selection/evaluation study. A later study needs a separate selection cohort, powered evaluation cohort, multiple noise points, source-specific settings, and shared-work curves.
