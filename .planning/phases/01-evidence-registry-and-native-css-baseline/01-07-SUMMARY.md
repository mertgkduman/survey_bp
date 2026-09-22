---
phase: 01-evidence-registry-and-native-css-baseline
plan: "07"
subsystem: evidence-registry
tags: [manifest, provenance, preflight, css, pydantic]
requires:
  - plan: 01-04
    provides: strict artifact loader and ordered CSS identity
  - plan: 01-05
    provides: durable begin-before-sample ledger lifecycle
provides:
  - strict versioned manifest schema and parser
  - immutable artifact and environment preflight
  - runner gate that resolves inputs before simulation
affects: [native-css-tracer, future-reproduction-manifests]
tech-stack:
  added: []
  patterns: [strict-pydantic-models, schema-version-dispatch, root-confined-artifact-resolution]
key-files:
  created: [data/manifests/schema-v1.json]
  modified: [src/bp_registry/manifests.py, src/bp_registry/runner.py, tests/test_manifest.py]
decisions:
  - "New manifests use a complete strict v1 schema; the original minimal v1 tracer remains readable only for replay."
  - "Preflight verifies whole-artifact and separate Hx, Hz, Lx, and Lz identities before sampling."
metrics:
  duration: 6m
  completed: 2026-09-22
  tasks_completed: 2
  files_changed: 4
status: complete
plan_head_before: 4399f66778ce80e4d925230d3fdd685d8149a802
commits: 5
actuals:
  tokens: 9293
  tasks: 2
  commits: 5
---

# Phase 1 Plan 07: Complete Manifest and Immutable Preflight Summary

Strict v1 manifests now pin full provenance, native BP settings, bounded execution, expected-output status, and immutable CSS inputs before any simulation begins.

## Tasks Completed

1. **Validate the complete manifest contract**
   - Added strict nested Pydantic v1 models with no coercion or extra fields.
   - Exported `schema-v1.json` from the same model and verified structural equivalence.
   - Kept the original minimal fixture record readable through explicit v1 dispatch while requiring every new record to use the complete contract.

2. **Preflight immutable inputs before simulation**
   - Confined artifact loading to the approved root and checked whole-file plus Hx, Hz, Lx, and Lz raw and semantic identities.
   - Checked the pinned Python, NumPy, SciPy, LDPC, backend, and decoder identity before runner work.
   - Changed `run_one` to consume only the resolved experiment before it opens the ledger, samples, or calls native BP.

## Verification

- `python -m pytest -q`: 56 passed.
- `python -m pytest -q tests/test_manifest.py tests/test_reference_smoke.py`: 20 passed.
- Exported `data/manifests/schema-v1.json` exactly matches `ManifestV1.model_json_schema()`.
- Spy tests confirm absent files, traversal, semantic-hash changes, unsupported versions, and unverified source evidence cannot reach sampling or native decode.

## Decisions Made

- Complete executable records use strict `ManifestV1`; legacy fixture manifests have a read-only replay path and are never rewritten.
- Matrix and logical evidence uses both whole-artifact identities and explicit ordered identities for Hx, Hz, Lx, and Lz.
- A `not_assessed` pilot must state why it has no curve criterion and cannot carry an output value, tolerance, or passing verdict.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Added per-matrix and per-logical identities**
- **Found during:** Final Task 2 contract review
- **Issue:** Whole-artifact hashes could detect a changed file but did not expose the required ordered identities for Hx, Hz, Lx, and Lz.
- **Fix:** Added strict raw and semantic hash fields for all four objects and recomputed them at preflight.
- **Files modified:** `src/bp_registry/manifests.py`, `data/manifests/schema-v1.json`, `tests/test_manifest.py`
- **Commit:** 291dc96

## TDD Gate Compliance

- RED: strict parser and immutable-runner tests failed before their corresponding implementations.
- GREEN: `tests/test_manifest.py` and the native tracer smoke tests pass with the complete contract.
- REFACTOR: removed the old fixture-code dependency from the runner after it began consuming the resolved experiment.

## Self-Check: PASSED

All four delivered files exist, all five implementation commits are reachable, the targeted suite passes, and the checked-in schema exactly equals the model export.
