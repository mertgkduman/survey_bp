---
phase: 03-update-rules-and-scheduling
plan: "09"
subsystem: group-shuffled-source
tags: [hsu-ndgsbp, cluster-schedule, source-provenance, replay]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: source revision and canonical binary BP engine
provides:
  - source-specific size-2/overlap-1 group constructor
  - purpose-separated replayable per-iteration check order
  - explicit classical-to-CSS adaptation and stopping disclosure
affects: [03-10, 03-16, 03-17, SCH-06]
key-files:
  created:
    - src/bp_registry/canonical/group_shuffled.py
    - tests/canonical/test_group_shuffled.py
    - docs/policies/group-shuffled.md
  modified: []
key-decisions:
  - "Implement only the source's worked size-2/overlap-1 construction because its general parameter notation is inconsistent."
  - "Retain Moradi artifact qualification separately as unavailable; the new policy is a Hsu CSS adaptation."
requirements-completed: []
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 09: Hsu Group Construction Summary

The published overlapping check-group example is pinned as an executable, replayable construction. A declared schedule root and attempt identity derive a purpose-specific PCG64 stream for each source iteration; the realized check order produces adjacent pairs with exact repeated membership evidence.

The documentation records source identity, classical AWGN versus CSS syndrome adaptation, post-group D-09 stopping adaptation, and the boundary from Moradi's unavailable learned policy. This plan does not claim SCH-06 completion; public execution remains in Plans 03-10, 03-16, and 03-17.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_group_shuffled.py` — 8 passed.
- Four revised PLAN.md files passed GSD plan-structure validation before execution.

## Commits

- `90f042f` — source construction, tests, and documentation.

## Deviations from Plan

- The source has inconsistent general group-parameter notation. The implementation is confined to its explicit worked example, as the revised plan specified.
- Tests were added with the implementation rather than committed as a separate TDD red step; no red-step evidence is claimed.
