---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "14"
subsystem: evaluation
tags: [mbbp, list, vote, shared-members]
status: complete
dependency_graph:
  requires: [09-11, 09-19]
  provides: [bounded MBBP list-vote matched assessment]
  affects: [09-15]
key_files:
  created: [data/studies/phase9-mbbp-list-vote-control-v1.json, tests/test_phase9_mbbp_list_vote_control.py]
actuals:
  tasks: 2
---

# Phase 09 Plan 14: Shared-Member MBBP List and Vote

## Delivered

- Executed both frozen B1 p=0.000001 matched samples through one ordered two-member MBBP set per sample. List and vote decisions reference the same member receipt and do not rerun members. Member, decision, and original-validation work and resource leaves remain separate.
- Public merge, assessment, and verify passed for both complete pairs. The paired table has 2 joint successes, zero discordant pairs, risk difference 0, and interval [-0.8882, 0.8882]. The bounded family is not rejected and supplies no publication superiority claim.
- Per-member iterations are typed unavailable because the canonical MBBP terminal does not expose them; convergence status, member work/runtime, and missingness reasons remain explicit.

## Verification

- `tests/test_phase9_mbbp_list_vote_control.py`: 2 passed.
- The public six-verb synthetic lifecycle and actual two-pair merge/assess/verify succeeded; shared receipt bytes were stable across list and vote.

## Self-Check: PASSED

The frozen positive N and shared-member evidence were completed and independently replayed.
