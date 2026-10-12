---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "19"
subsystem: campaigns
tags: [controlled, shared-initial, mbbp, paired, replay]
status: complete
dependency_graph:
  requires: [09-11, 09-18]
  provides: [typed shared-input controlled public lifecycle]
  affects: [09-12, 09-13, 09-14, 09-15]
key_files:
  created: [src/bp_registry/campaigns/controlled.py, src/bp_registry/campaigns/controlled_execution.py, src/bp_registry/campaigns/controlled_mbbp.py, src/bp_registry/campaigns/controlled_public.py]
  modified: [src/bp_registry/campaigns/cli.py, src/bp_registry/campaigns/reporting.py, src/bp_registry/canonical/fair_legs.py, tests/test_campaign_execution.py, tests/test_campaign_statistics.py]
actuals:
  tasks: 2
---

# Phase 09 Plan 19: Typed Controlled Execution

## Delivered

- Added closed typed component receipts for convergence, iterations, configured/actual work, runtime, RSS availability, events, evidence/storage bytes, interruption, and provenance. Reasoned unavailable and not-applicable values remain distinct from zero.
- The fair three-arm route seals one complete decoder-visible initial BP state per physical sample. Initial BP, Relay, and Beam reference its digest; Relay and Beam adopt the state without repeating initial BP. Common, continuation, and original-validation costs are separate. The initial-vs-Relay and initial-vs-Beam contrasts enter one frozen Holm family over complete groups.
- The MBBP route executes an ordered member set once per physical sample. List and vote derive their decisions from the same content-bound member receipt. Member work and runtime, selection, admission/exclusion, decision work, and validation are separate. A no-candidate terminal records zero actual original checks.
- Public `plan`, `run-local`, `merge`, `resume`, `assess`, and `verify` support shared-initial, shared-member, and ordinary schedule families. Partial merges retain completed arms and the exact missing set; assessment requires all frozen groups. Replay reconstructs terminals, paired tables, Holm results, shared-input lineage, and typed cost projections from sealed bytes without running decoders. Publication Slurm stays denied.

## Verification

- Synthetic public lifecycle tests exercised inside-group partial/resume, ordinary two-arm order, shared-initial/no-rerun, shared-MBBP/no-rerun, terminal assessment, independent byte replay, family membership, costs, and tamper rejection.
- The Plan 09-19 family selector passed 9 tests. The focused controlled selector passed 8 tests. Actual Phase 9 Relay/Beam and MBBP evaluations also passed public merge, assess, and verify.

## Deviation

Per-member MBBP iteration counts are absent from the canonical member terminal; their typed value is `unavailable` with a reason. Process RSS is retained at process scope where available; per-component RSS is reasoned unavailable.

## Self-Check: PASSED

Both planned tasks and the public controlled lifecycle are implemented and replayable.
