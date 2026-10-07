---
phase: 10-correlated-quaternary-execution
plan: "01"
subsystem: quaternary-public-execution
tags: [qbp, pauli, non-css, replay, ledger]
requires: []
provides: [QuaternaryExperimentV1, joint-pauli-tracer, deterministic-quaternary-replay]
affects: [phase-10-expansion-plans]
tech_stack:
  added: []
  patterns: [strict-pydantic-manifest, categorical-four-state-sampling, sealed-truth-evaluation, exact-ledger-replay]
key_files:
  created:
    - src/bp_registry/quaternary/execution.py
    - data/manifests/quaternary-five-qubit-tracer.json
    - tests/canonical/quaternary/test_public_execution.py
  modified:
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - src/bp_registry/cli.py
decisions:
  - "Persist Pauli values as I=0, X=1, Y=2, Z=3 and sample them as one categorical value per qubit."
  - "Keep decoder smoothing separate from physical channel probabilities and retain non-CSS logical action as unavailable without a declared basis."
metrics:
  duration: 482 seconds
  completed: 2026-10-07
  tasks: 1
status: complete
plan_head_before: 7db550ad5f6d51b3d3c5aeffb3fd7b9a39d8ae38
commits: 2
actuals:
  tokens: 8801
  tasks: 1
  commits: 2
---

# Phase 10 Plan 01: Public Quaternary Tracer Summary

Implemented a replayable joint-Pauli BP tracer for the non-CSS five-qubit development fixture, from strict public manifest through independent evaluation and verification.

## Delivered

- Added `QuaternaryExperimentV1` with strict non-null, shape, encoding, finite-probability, budget, and evidence-label validation.
- Added immutable Pauli problem handling, one categorical I/X/Y/Z draw per qubit, scalar commutation-message flooding, candidate freeze, and independent outcome classification.
- Routed quaternary preflight, execution, and verification through the existing `preflight`, `canonical`, and `verify-run` CLI commands.
- Added a source-linked five-qubit `IIIYI` depolarizing fixture labeled `canonical_implemented`, `development_fixture`, and `not_assessed`.
- Added focused coverage for installed command flow, non-CSS syndrome semantics, truth sealing, smoothing provenance, null/empty/invalid boundaries, one-qubit admission, deterministic replay, and ledger tampering.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'tracer or installed_cli or non_css or null or empty or one_qubit or encoding or truth_boundary or replay or tamper or assessment' -x` — passed (9 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary tests/test_sampling.py tests/test_css_small.py tests/test_phase6_public_execution.py` — passed (30 tests).
- `preflight` → `canonical` → `verify-run` completed successfully against the fixture.

## TDD Gate Compliance

- RED commit `5fa6e3d` added the missing-facade test and recorded `RED_EVIDENCE_OK` before production edits.
- GREEN commit `7771c65` implements the facade and passes the focused suite.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- Created tracer module, fixture, and test suite exist.
- Both TDD commits exist and no tracked files were deleted.
