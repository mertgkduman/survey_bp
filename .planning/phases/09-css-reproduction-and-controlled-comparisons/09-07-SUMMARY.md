---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "07"
subsystem: canonical-mbbp-voting
tags: [css, mbbp, coordinate-majority, provenance]
status: complete
requires: [canonical-mbbp-member-terminals, coordinate-majority-vote]
provides: [public-mbbp-vote-decision, deterministic-vote-event-projection]
affects: [phase6-ledger-projection, canonical-v7-manifests]
tech-stack:
  added: []
  patterns: [immutable-member-terminals, content-derived-lineage, independent-original-syndrome-validation]
key-files:
  created: []
  modified:
    - src/bp_registry/manifests.py
    - src/bp_registry/canonical/phase6.py
    - tests/canonical/test_mbbp.py
    - tests/canonical/test_voting.py
decisions:
  - "A declared vote is a closed terminal: empty or original-invalid aggregates never substitute the list winner."
  - "Vote identity is derived from sorted admitted member lineage and canonical ballot content; completion order is excluded."
  - "Vote events state exclusions, ballots, aggregate lineage, original validity, and coordinates resolved by the declared tie bit."
metrics:
  duration: "16m"
  completed: "2026-10-11"
  tasks: 2
  files: 4
plan_head_before: 6a2fcbc123300ea42b56ff9d59f7599b692e546c
commits: 6
actuals:
  tokens: 5768
  tasks: 2
  commits: 6
---

# Phase 09 Plan 07: Public MBBP Coordinate Voting Summary

Executable coordinate-majority MBBP voting now retains all member terminals and exposes deterministic public vote evidence.

## Completed Tasks

1. Admitted complete V7 vote declarations and implemented a closed `PublicMbbpDecision` for list, valid-vote, empty-electorate, and invalid-aggregate terminals.
2. Projected deterministic vote electorate, exclusions, ballots, aggregate and validation lineage, tie coordinates, and terminal status.

## Decisions Made

- A member votes only when its frozen terminal is original-valid and admitted; budget denial, nonconvergence, original invalidity, and missing candidates remain visible exclusions.
- Vote aggregation validates against the immutable original syndrome through `CoordinateMajorityVote`; hidden physical truth is outside the controller.
- An invalid aggregate retains its correction and `original_valid=false`, with no selected candidate or list fallback.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py -k 'vote or electorate or exclusion or invalid or empty or list_regression' -x` — 6 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py tests/canonical/test_mbbp.py -k 'vote or tie or order or original_valid or lineage' -x` — 14 passed.

## TDD Gate Compliance

- RED evidence for the initial public vote decision and the projection classification/tie-visibility additions was verified with `RED_EVIDENCE_OK`.
- GREEN commits implement the public decision, nonconvergence exclusion, and tie-coordinate evidence; both focused verification commands pass.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 2 - Missing critical functionality] Added explicit `tie_coordinates` to vote aggregate evidence.
   - **Found during:** Task 2
   - **Issue:** The declared tie bit and resulting correction were visible, but the resolved coordinates were not.
   - **Fix:** Derived tied coordinate indices from the complete ordered ballots and emitted them with aggregate lineage.
   - **Files modified:** `src/bp_registry/canonical/phase6.py`, `tests/canonical/test_mbbp.py`
   - **Commit:** 09e914d

## Known Stubs

None.

## Self-Check: PASSED

Verified all four modified implementation/test files, this summary, and task commits `f9a65ad`, `b8efd9b`, `7f5fb89`, `772af60`, `f49cb87`, and `09e914d`.
