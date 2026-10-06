---
phase: 07-optional-postprocessing
plan: "01"
subsystem: canonical postprocessing contracts
tags: [lsd, postprocessing, manifest, tracer]
status: complete
key-files:
  created:
    - src/bp_registry/canonical/postprocessing/__init__.py
    - src/bp_registry/canonical/phase7.py
    - tests/test_phase7_public_execution.py
  modified:
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - src/bp_registry/cli.py
decisions:
  - Phase 7 accepts only explicit LSD_0, LSD_E, or LSD_CS bindings with finite natural-log-odds input.
  - Controller selection uses only decoder-visible failed-attempt fields and invokes one closed adapter.
---

# Phase 07 Plan 01: Optional LSD Tracer Summary

Added immutable failure-handoff contracts, a closed released-LSD adapter, and additive V8 manifest admission for independently attributed optional processing.

## Completed Work

- Frozen full-length finite posterior LLRs and original-space candidates before optional processing.
- Ranked failed attempts by residual, channel NLL, declared ordinal, and lineage ID.
- Routed magnitude LLRs with explicit `bits_per_step=1`, method, and order to `LsdDecoder`, then independently original-validated its candidate.
- Added disabled/qualified V8 postprocessing admission and the initial truth-free Phase 7 projection.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase7_public_execution.py -x`

Result: 5 passed, including the installed `preflight` → `canonical` → `verify-run` path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Added a versioned structural ledger route for V8.**

The existing engine sealed a terminal before optional processing could be recorded. The V8 handler now owns the flooding attempt and writes BP-only, fallback, final, work, and terminal records in order; the ledger accepts the additive version-seven grammar and CLI replay checks that the BP-only and final records stay distinct.

**Files modified:** `src/bp_registry/canonical/execution.py`, `src/bp_registry/ledger.py`, and `src/bp_registry/cli.py`.

## Self-Check: PASSED

Created and modified files listed above exist and focused tracer tests pass.
