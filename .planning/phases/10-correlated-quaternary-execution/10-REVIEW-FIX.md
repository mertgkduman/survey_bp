---
phase: 10
fixed_at: 2026-10-08T00:51:43-04:00
review_path: .planning/phases/10-correlated-quaternary-execution/10-REVIEW.md
iteration: 2
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
verification_environment: main checkout
---

# Phase 10: Code Review Fix Report

**Fixed at:** 2026-10-08T00:51:43-04:00

**Source review:** `.planning/phases/10-correlated-quaternary-execution/10-REVIEW.md`  
**Iteration:** 2 (remediation re-review)

## Summary

- Findings in scope: 1
- Fixed: 1
- Skipped: 0
- Verification ran in the main checkout using its existing `.venv`; implementation edits were made and committed in an isolated worktree before fast-forwarding this branch.

## Fixed Issues

### CR-01: Public scalar-policy compositions were recorded without execution

**Files modified:** `src/bp_registry/quaternary/execution.py`, `src/bp_registry/quaternary/qbpgd.py`, `src/bp_registry/runner.py`, `tests/canonical/quaternary/test_public_execution.py`  
**Commit:** `29310d6`

Public V2 scalar and Q-BPGD runs now construct typed flooding or variable-serial schedules and typed C2V transforms from the manifest. Missing transform parameters fail closed. MBP4 and aSCED reject transforms they do not execute.

### CR-02: V2 multi-shot budget exceeded supported shot behavior

**Files modified:** `src/bp_registry/manifests.py`, `tests/canonical/quaternary/test_public_execution.py`  
**Commit:** `a358fe0`

V2 now declares only `shot_budget: 1`, matching its single immutable observation and supported shot-zero execution.

### CR-03: Canonical evidence verification accepted fabricated decoder records

**Files modified:** `scripts/run_phase10_quaternary_gate.py`, `tests/canonical/quaternary/test_asced_evidence.py`  
**Commit:** `47669b0`

Verification now fails closed unless `--replay` is supplied. The explicit replay regenerates the complete frozen batch through the ordinary and overcomplete controllers, then byte-compares the canonical ledger and study receipt. This fix requires the coordinated full replay before Phase 10 decoder output can again be reported as verified.

### CR-04: Native-success receipt did not verify build/run provenance or arithmetic

**Files modified:** `src/bp_registry/quaternary/native_asced.py`, `tests/canonical/quaternary/test_asced_evidence.py`  
**Commits:** `d1c4f4f`, `9d17715`

Native verification binds the actual build receipt, validates pinned source digests and successful checkout/build/install/run command records, and checks aggregate counters, failure-class arithmetic, rate arithmetic, and approved probe configuration. The remediation re-review found that a coherent aggregate could still be forged. Phase 10 evidence admission now also requires the exact SHA-256 content digest of the retained native run receipt. Generic structural receipt validation remains available for structural checks, but the gate and `run_native_asced_reference()` require the endorsed retained observation before treating a receipt as Phase 10 native evidence.

### WR-01: MBP4 aSCED execution could exceed the preflight work cap

**Files modified:** `src/bp_registry/quaternary/asced.py`, `tests/canonical/quaternary/test_asced_ensemble.py`  
**Commit:** `089c5f1`

An MBP4 aSCED kernel must use the controller iteration cap; the controller also guards against completed sweeps beyond that cap.

### WR-02: Ordinary test execution invoked a destructive network build

**Files modified:** `scripts/qualify_phase10_native_asced.py`, `tests/canonical/quaternary/test_asced_evidence.py`  
**Commits:** `282e7b9`, `70e888b`

Native builds now require `--integration-network`, an explicit integration mode, and a caller-supplied work root. `approved_native` evidence remains restricted to the exact source-spec disposable root and approved CMake location. A `development_integration` root must be new and unique, but its receipt is rejected from native-evidence verification. Ordinary tests do not download, build, or reuse a shared `/tmp` tree.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'native_run_receipt or native_receipt_rejects or coherent_forged or gate_rejects_design' -x` — **6 passed, 12 deselected in 5.55s**. The regression copies the genuine build receipt, coherently changes `logical_errors`, failure classes, rate, and matching metric fact, confirms generic structural validation accepts that self-consistent record, then confirms Phase 10 evidence admission rejects it by content digest.
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase10_quaternary_gate.py freeze --study data/studies/phase10-quaternary-b1-gate.json --native-receipt data/native/phase10-asced-run-receipt.json` — **passed** for the exact retained receipt.
- Retained immutable inputs were re-hashed and unchanged: `phase10-asced-source-spec.json` is `55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e`; `phase10-asced-run-receipt.json` is `c13a5cd8a511e2619da07089fae31ed4948115599a590d5e7c285273dca0240d`.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` — **168 passed in 14.75s**.
- Focused syntax checks passed for each modified Python module with `.venv/bin/python -m py_compile`.
- Focused receipt, replay-gating, schedule, public-execution, and aSCED-cap tests passed before their respective commits.
- The full Phase 10 decoder replay was intentionally not started. Run:

  ```bash
  OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase10_quaternary_gate.py verify \
    --study data/studies/phase10-quaternary-b1-gate.json \
    --native-receipt data/native/phase10-asced-run-receipt.json \
    --output data/results/phase10-quaternary-b1-gate \
    --replay
  ```

  This is the required human-coordinated verification for CR-03 and does not alter the frozen design, source-spec digest, or retained ledger before it runs.

---

_Fixed: 2026-10-08T00:51:43-04:00_

_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 2_
