---
phase: 04-memory-policies-and-relay-bp
plan: "06"
subsystem: canonical-relay-evidence
tags: [relay, ledger, provenance, tracing, verification]
requires:
  - 04-05
provides:
  - versioned Phase 4 Relay transfer and work-leaf grammar
  - independent Relay work and terminal reconstruction
  - hash-verified bounded trace sidecars
affects: [phase-04-relay, canonical-execution, public-evidence]
tech-stack:
  added: []
  patterns: [unique leaf reduction, content-addressed sidecars, typed unavailable facts]
key-files:
  created: []
  modified:
    - src/bp_registry/canonical/budgets.py
    - src/bp_registry/canonical/lineage.py
    - src/bp_registry/ledger.py
    - src/bp_registry/canonical/verification.py
    - tests/canonical/test_relay.py
    - tests/canonical/test_phase4_evidence.py
decisions:
  - "Phase 4 manifests automatically select ledger V4, preserving historical V2/V3 event semantics."
  - "Relay work reconstructs only from unique typed leaves; any disagreement with its declared total fails closed."
metrics:
  duration: "417 seconds"
  completed: "2026-09-25"
  tasks: 2
  commits: 4
plan_head_before: a63c9296d9b548e56a2e83e7aa2b8034845bea54
status: complete
actuals:
  tokens: 7624
  tasks: 2
  commits: 4
---

# Phase 04 Plan 06: Relay Evidence and Work Reconstruction Summary

Relay V4 evidence now binds posterior handoffs, unique work leaves, terminal totals, candidate selection, and bounded trace sidecars into independently verifiable shot records.

## Completed Tasks

1. **Accounted for Relay legs, transfers, candidates, and selection once**
   - Added idempotent `RelayWorkAccounting` with conflict rejection and per-leg summaries.
   - Added typed `RelayLegAncestry` and a V4 Relay ledger grammar with stable transfer leaf IDs.
   - V4 work events materialize a unique leaf reduction whose total must equal the recorded work vector.

2. **Verified Phase 4 ledgers and bounded state traces independently**
   - Added `reconstruct_relay_work` and `validate_phase4_shot`.
   - Verified V4 begin/terminal boundaries, candidate-to-selection lineage, transfer leaves, typed missingness, and terminal work equality.
   - Rehashed and confined linked traces, enforcing record, byte, and truncation agreement.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_relay.py tests/canonical/test_work_accounting.py -k 'lineage or leaf or transfer or candidate or selection or duplicate'` — 5 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'ledger or reconstruct or trace or truncation or tamper or unavailable'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py tests/canonical/test_relay.py tests/canonical/test_phase4_evidence.py tests/test_ledger.py` — 38 passed, 1 skipped.

## TDD Gate Compliance

| Task | RED | GREEN | Result |
| --- | --- | --- | --- |
| Task 1: Relay leaf accounting | `11c9a49` | `17ab54b` | Passed |
| Task 2: Phase 4 evidence verification | `c58403c` | `acc73cf` | Passed |

Both RED records passed `gsd_run check tdd-red-evidence` with `RED_EVIDENCE_OK` before production implementation.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Materialized V4 leaves for live Relay runner output**
   - **Found during:** Task 2 integration verification.
   - **Issue:** Existing Relay runs emitted a transfer and aggregate work but had no durable leaf reduction or terminal work vector for independent reconstruction.
   - **Fix:** The ledger upgrades V4 manifests, adds transfer-balanced work leaves, and binds the work vector into the terminal event.
   - **Files modified:** `src/bp_registry/ledger.py`, `tests/canonical/test_relay.py`.
   - **Commit:** `acc73cf`.

## Self-Check: PASSED

- Confirmed all six modified files exist.
- Confirmed task commits `11c9a49`, `17ab54b`, `c58403c`, and `acc73cf` exist in git history.
