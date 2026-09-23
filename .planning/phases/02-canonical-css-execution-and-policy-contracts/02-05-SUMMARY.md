---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "05"
subsystem: canonical-lineage-and-tracing
tags: [css, lineage, candidate-retention, ledger, semantic-tracing, provenance]
requires: [02-02-policy-lifecycle, 02-03-canonical-numerics]
provides: [typed-append-only-lineage, tiered-candidate-retention, canonical-ledger-v2, bounded-trace-sidecars]
affects: [interventions, relay, fallback, evidence-querying, profiling]
tech-stack:
  added: []
  patterns: [semantic-content-IDs, typed-parent-edges, frozen-selection, content-addressed-sidecars, observational-truncation]
key-files:
  created:
    - src/bp_registry/canonical/tracing.py
    - tests/canonical/test_tracing.py
    - tests/fixtures/canonical-semantic-events.json
  modified:
    - src/bp_registry/canonical/lineage.py
    - src/bp_registry/ledger.py
decisions:
  - "Canonical lineage IDs derive from typed logical parents and canonical content, never timing or append order."
  - "Selection retains every candidate's visible audit facts while only selected or policy-authorized candidates retain full payloads."
  - "Canonical structural evidence uses a separate v2 grammar; optional semantic sidecars are confined, hash-linked, and observational."
metrics:
  duration: 13m
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 5
status: complete
plan_head_before: 15b591067089570e05da4035a6c952a33b34ed69
commits: 5
actuals:
  tokens: 12800
  tasks: 2
  commits: 5
---

# Phase 02 Plan 05: Durable Lineage and Semantic Trace Evidence Summary

Canonical CSS execution now has semantic, typed append-only ancestry with tiered candidate retention, plus a separate sparse v2 structural ledger and bounded content-addressed trace sidecars.

## Completed Tasks

1. Implemented immutable lineage nodes and typed parent edges for original/working problems, transformations, execution scopes, candidates, lifts, validations, selections, and post-selection evaluations. Candidate records preserve identity, hash, score, validations, lineage, and reason while retaining selected payloads fully.
2. Added a version-two canonical event writer, reader, and query API that leaves the historical v1 ledger unchanged, alongside filtered UTF-8 typed-array semantic sidecars with path confinement, hashing, fsync, and explicit quota truncation.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/canonical/test_truth_boundary.py tests/test_ledger.py`

Result: `16 passed`.

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`

Result: `98 passed`.

## Decisions Made

- A lineage identity encodes logical parent IDs, relation, and canonical content; concurrent or reordered arrival cannot change it.
- Evaluations can only append after selection and cannot rewrite selected identity or candidate ordering.
- A non-off trace plan must reserve enough byte budget for a durable truncation record; if needed, optional records are discarded to retain that fact.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Reserved trace storage for explicit byte-cap overflow evidence**

- **Found during:** Task 2 post-implementation review
- **Issue:** A first optional record larger than the byte cap could set in-memory truncation without writing a sidecar fact.
- **Fix:** Require room for truncation metadata, write an empty-but-truncated sidecar when necessary, and drop optional records before omitting the required fact.
- **Files modified:** `src/bp_registry/canonical/tracing.py`, `tests/canonical/test_tracing.py`
- **Commit:** `f408f12`

## Known Stubs

None.

## Threat Review

- Typed semantic IDs and append-only conflict rejection mitigate lineage tampering.
- Sidecar paths reject absolute, parent, and symlink traversal; content digests are verified before use.
- Candidate and trace retention are bounded, and trace observation has no decoder-control interface.
- Evaluation annotations require an existing frozen selection node.

## Task Commits

- `d038dd1` test: failing lineage retention contracts
- `59eed04` feat: immutable candidate lineage graph
- `f01d5a7` test: failing semantic trace contracts
- `eb2aed5` feat: bounded canonical semantic traces
- `f408f12` fix: persisted trace-overflow evidence

## Self-Check: PASSED

All five planned source/test artifacts, the summary artifact, and all five measured task commits exist.
