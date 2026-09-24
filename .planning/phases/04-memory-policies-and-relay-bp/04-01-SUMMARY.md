---
phase: 04-memory-policies-and-relay-bp
plan: "01"
subsystem: canonical-relay-memory
tags: [relay-bp, memory-policy, css, provenance, tdd]
requires:
  - phase: 03
    provides: canonical CSS structural engine, budgets, and frozen candidate selection
provides:
  - strict V4 ordered affine-memory and Relay topology manifest
  - finite posterior-only two-leg Relay controller through the structural engine
  - Wave 0 Phase 4 memory, Relay, differential, and evidence test targets
affects: [04-02, 04-03, 04-04, 04-05, 04-06, 04-07, 04-08, 04-09, 04-10, 04-11, 04-12, 04-13, 04-14, 04-15]
tech-stack:
  added: [strict Pydantic V4 contracts, NumPy float64 posterior transfers]
  patterns: [proposal-then-commit memory state, posterior-only relay handoff, decoder-visible selection before evaluation]
key-files:
  created:
    - src/bp_registry/canonical/memory.py
    - src/bp_registry/canonical/relay.py
    - tests/canonical/test_memory_policies.py
    - tests/canonical/test_memory_composition.py
    - tests/canonical/test_relay.py
    - tests/canonical/test_relay_differential.py
    - tests/canonical/test_phase4_evidence.py
  modified:
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
decisions:
  - "V4 alone carries explicit contiguous ordered affine-prior bindings, leaving V2 and V3 parsing unchanged."
  - "Relay legs reconstruct V2C, message, iteration, convergence, and RNG-local state; a checked LLR posterior is the sole handoff."
  - "The first successful decoder-visible candidate is frozen before hidden truth reaches evaluation."
metrics:
  duration: "31m"
  completed_date: "2026-09-24"
  tasks_completed: 2
  tests: "8 passed, 5 skipped"
status: complete
plan_head_before: cde71d16a714d6bd93c06b1daab2aaf5e9eba8e0
commits: 5
actuals:
  tokens: 9037
  tasks: 2
  commits: 5
---

# Phase 04 Plan 01: Relay tracer and Wave 0 validation targets Summary

Implemented a strict V4 CSS Relay-BP adaptation that applies ordered affine prior memory between fresh canonical legs and records a digest-bound float64 posterior transfer.

## Accomplishments

- Added V4 manifest admission for contiguous ordered memory bindings and explicit Relay leg counts without changing V2/V3 parsing.
- Added an affine-prior proposal/commit primitive with finite-vector validation and binding-owned state.
- Routed a real two-leg Relay controller through `run_canonical_structural_shot`; it transfers only a finite `llr_log_p0_over_p1` posterior and emits a `relay_transfer` ledger event.
- Added all five Wave 0 test targets; focused tests collect 13 cases and run 8 passing cases.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py -k 'tracer or posterior_transfer or historical_manifest'` — passed (1 test).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest --collect-only -q tests/canonical/test_memory_policies.py tests/canonical/test_memory_composition.py tests/canonical/test_relay.py tests/canonical/test_relay_differential.py tests/canonical/test_phase4_evidence.py` — passed (13 collected).
- Focused Phase 4 modules — passed (8 passed, 5 explicitly skipped).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q -x tests/canonical/test_update_rules.py tests/test_manifest.py tests/test_canonical_cli.py` — 58 passed, then blocked by an existing editable-install issue: subprocess `.venv/bin/python` cannot import `bp_registry`. Recorded in `deferred-items.md` and `WINDOWS.md`.

## TDD Gate Compliance

The public tracer test was committed before production code. The final RED evidence record passed `gsd-tools check tdd-red-evidence`, then the implementation commit made the target pass. Two preliminary evidence-format correction commits preceded the final valid RED record; the final evidence is committed at `28997af`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the V4 manifest parser instance branch**
- **Found during:** Task 1 focused tracer verification.
- **Issue:** `parse_canonical_manifest` accepted V2/V3 instances but treated a V4 instance as a raw mapping.
- **Fix:** Added `CanonicalManifestV4` to the accepted immutable manifest instance tuple.
- **Files modified:** `src/bp_registry/canonical/contracts.py`
- **Commit:** `eb65289`

**2. [Rule 1 - Bug] Corrected the ordered-affine composition fixture**
- **Found during:** Task 2 focused validation.
- **Issue:** The fixture expected same-target affine compositions to differ by order, although their shared-base coefficients commute.
- **Fix:** Replaced it with an explicit commutativity proof and retained the persisted-order rationale for future noncommuting targets.
- **Files modified:** `tests/canonical/test_memory_composition.py`
- **Commit:** `385c89a`

## Known Stubs

| File | Line | Reason |
|---|---:|---|
| `tests/canonical/test_memory_policies.py` | 31 | Source-qualified damping, PDBP, PD′BP, and momentum equations are Wave 1 work. |
| `tests/canonical/test_memory_composition.py` | 30 | Seeded assignments, schedule compatibility, and denial rollback fixtures are Wave 1 work. |
| `tests/canonical/test_relay_differential.py` | 8 | Pinned author v0.2.2 differential requires a reviewed external environment and observer patch. |
| `tests/canonical/test_relay_differential.py` | 13 | Observer patch equivalence requires the reviewed external author build. |
| `tests/canonical/test_phase4_evidence.py` | 19 | B1 reconciliation and bounded notebook reuse evidence are Wave 1 work. |

All entries are also open in `.planning/WINDOWS.md` for the ship gate.

## Files Created or Modified

- `src/bp_registry/canonical/contracts.py`
- `src/bp_registry/canonical/memory.py`
- `src/bp_registry/canonical/relay.py`
- `src/bp_registry/canonical/execution.py`
- `tests/canonical/test_memory_policies.py`
- `tests/canonical/test_memory_composition.py`
- `tests/canonical/test_relay.py`
- `tests/canonical/test_relay_differential.py`
- `tests/canonical/test_phase4_evidence.py`

## Self-Check: PASSED

The V4 contracts, memory primitive, Relay controller, structural-engine wiring, and all five Phase 4 targets exist. Production and test commits `6efb85b`, `17f6b7f`, `28997af`, `eb65289`, and `385c89a` are present.
