---
phase: 10
plan: 16
subsystem: correlated-quaternary-execution
tags: [quaternary, asced, gb46, reproducibility, evidence]
requires:
  - 10-15 native aSCED `native_success` receipt
provides:
  - digest-bound 256-shot matched canonical mechanism evidence
  - independently verified all-path ledger and qualified native aggregate
affects: [phase-10-closure, phase-11-comparisons]
tech-stack:
  added: []
  patterns: [run-once ledger, deterministic sample reconstruction, receipt-bound verification]
key-files:
  created:
    - data/results/phase10-quaternary-b1-gate/canonical-ledger.jsonl
    - data/results/phase10-quaternary-b1-gate/study-receipt.json
  modified:
    - scripts/run_phase10_quaternary_gate.py
    - tests/canonical/quaternary/test_asced_evidence.py
decisions:
  - Keep aSCED execution and fixtures labelled canonical_adaptation while retaining the native aggregate as a separate unavailable-shot-identity evidence lane.
  - Retain every canonical terminal and every aSCED virtual path with not_assessed labels; do not rank or claim curve reproduction.
metrics:
  duration: 3h 23m bounded run plus verification
  completed: 2026-10-08
  artifacts: 2
status: complete
plan_head_before: 413a3c4a7c11b86c24de87da90b0689f84552629
commits: 4
actuals:
  tokens: 924039
  tasks: 2
  commits: 4
---

# Phase 10 Plan 16: Quaternary Mechanism Evidence Summary

Retained and independently verified the frozen GB46 p=0.05 seed-10 canonical mechanism study, including every matched canonical path and the separate exact native aSCED aggregate.

## Results

- The single frozen execution retained **2,816** ledger events: 768 canonical arm terminals (256 each for BP4, ordinary aSCED, and overcomplete aSCED) and 2,048 aSCED path terminals (1,024 per aSCED arm).
- All 256 physical samples reconstructed from the frozen seed and shot IDs; all canonical and path records are labelled `not_assessed`.
- The verifier replays event IDs, sample digests, original and typed extended syndromes, LSB virtual bits, candidates, outcomes, work, exact splitter/map identities, and qualified native aggregate facts.
- The separate verified native receipt remains aggregate-only: 160 trials and 10 logical errors. Its shot identity is explicitly `unavailable_aggregate_only`; no matched-native-shot claim is made.
- Native and canonical aSCED evidence remain `canonical_adaptation`/native-reference lanes. No source-faithful promotion, curve claim, or Phase 11 performance ranking was made.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase10_quaternary_gate.py verify ...`: passed with 768 canonical terminals, 2,048 paths, and native 160/10 aggregate.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'phase10 or native_run' -x`: **5 passed**.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`: **1021 passed, 1 skipped, 6 warnings** in 744.58s. The warnings are existing Python multiprocessing fork deprecations from the beam-relay campaign tests.

## Decisions Made

- Preserve the complete all-path canonical evidence ledger as bounded mechanism evidence only.
- Bind the exact native `native_success` aggregate separately while preserving its unavailable per-shot matching fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Compiled the CSS graph before calculating canonical physical syndromes.**
- **Found during:** Task 2 execution.
- **Issue:** `CssCode` has no quaternary `syndrome` method.
- **Fix:** Compile the immutable CSS artifact to its `PauliCode` representation before creating each original problem.
- **Files modified:** `scripts/run_phase10_quaternary_gate.py`
- **Commit:** `f73635d`

**2. [Rule 3 - Blocking performance] Reused the preflighted overcomplete search receipts.**
- **Found during:** Task 2 execution.
- **Issue:** Reconstructing map-search receipts per path made the bounded run impractically expensive.
- **Fix:** Cache the exact deterministic searches reconstructed during preflight and pass them to the overcomplete arm; each path still independently validates the receipt chain.
- **Files modified:** `scripts/run_phase10_quaternary_gate.py`
- **Commit:** `f73635d`

**3. [Rule 1 - Bug] Hardened persisted-ledger verification against real output semantics.**
- **Found during:** Task 2 independent verification.
- **Issue:** The first hardened verifier had an incorrect local binding and assumed overcomplete checks must form a commuting stabilizer code.
- **Fix:** Bind reconstructed receipt objects explicitly and calculate working-graph syndromes with the quaternary syndrome function, matching the decoder's derived-graph semantics.
- **Files modified:** `scripts/run_phase10_quaternary_gate.py`, `tests/canonical/quaternary/test_asced_evidence.py`
- **Commit:** `f73635d`

## Known Stubs

None.

## Self-Check: PASSED

- Found retained ledger and study receipt.
- Found task commits `4b51bb6`, `563ccaf`, and `f73635d`.
