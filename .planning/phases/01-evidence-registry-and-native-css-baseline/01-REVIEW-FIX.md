---
phase: 01
fixed_at: 2026-09-22T03:36:38Z
review_path: .planning/phases/01-evidence-registry-and-native-css-baseline/01-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-09-22T03:36:38Z
**Source review:** `.planning/phases/01-evidence-registry-and-native-css-baseline/01-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 8
- Fixed: 8
- Skipped: 0

## Fixed Issues

### CR-01: Fresh legacy manifests can run without immutable preflight

**Files modified:** `src/bp_registry/runner.py`, `tests/test_manifest.py`, `tests/test_reference_smoke.py`, `tests/test_ledger.py`
**Commit:** `9eae548`
**Applied fix:** Legacy manifests remain readable for historical inspection but `run_one` rejects them before a ledger is opened.

### CR-02: The one-shot entry point ignores the manifest shot budget

**Files modified:** `src/bp_registry/runner.py`, `tests/test_manifest.py`
**Commit:** `a940b6f`
**Applied fix:** `run_one` rejects every complete-manifest shot ID outside `0..max_shots-1` before simulation or ledger work.

### CR-03: `verify-run` accepts tampered or mixed terminal provenance

**Files modified:** `src/bp_registry/cli.py`, `tests/test_evidence.py`, `data/results/pilot_adaptation-not_assessed/events.jsonl`, `data/results/pilot_adaptation-not_assessed/result.json`
**Commit:** `ccb279e`, `5a536e0`
**Applied fix:** Verification now checks each begin/terminal lineage, immutable manifest and source identities, deterministic samples, native candidate linkage, and independently reconstructed outcome. The pilot ledger was regenerated under this contract with a manifest-stable artifact path.

### CR-04: Resource provenance always claims one OpenMP thread

**Files modified:** `src/bp_registry/manifests.py`, `src/bp_registry/cli.py`, `data/manifests/selected-css-pilot_adaptation-not_assessed.json`, `tests/test_manifest.py`
**Commit:** `9b9b504`
**Applied fix:** The manifest pins one OpenMP thread, preflight requires `OMP_NUM_THREADS=1`, and run verification validates immutable resource context.

### CR-05: Evidence validation permits arbitrary maturity promotion

**Files modified:** `src/bp_registry/evidence.py`, `tests/test_evidence.py`
**Commit:** `88919ca`
**Applied fix:** Seed-record validation now enforces work/revision/result anchors, reciprocal pilot links, pilot-only maturity semantics, and verified result/artifact identities.

### CR-06: Ledger source URI and source revision identify different sources

**Files modified:** `src/bp_registry/manifests.py`, `src/bp_registry/runner.py`, `src/bp_registry/ledger.py`, `data/manifests/selected-css-pilot_adaptation-not_assessed.json`, `tests/test_manifest.py`, `tests/test_reference_smoke.py`
**Commit:** `63df858`
**Applied fix:** The manifest and ledger retain distinct paper and implementation identities, including the implementation repository, commit, source path, and file hash.

### WR-01: Native adapter silently coerces nonbinary floating inputs

**Files modified:** `src/bp_registry/reference.py`, `tests/test_reference_smoke.py`
**Commit:** `53ad4b5`
**Applied fix:** Adapter inputs and native candidates must have integer or bool dtype and binary values before conversion to `uint8`.

### WR-02: Source evidence appends are not durable after reporting success

**Files modified:** `src/bp_registry/evidence.py`, `tests/test_evidence.py`
**Commit:** `df26ffb`
**Applied fix:** JSONL evidence writes call `fsync` after flush; a regression test verifies it runs before success is returned.

## Verification

Tier 1 re-reads and Tier 2 Python compilation were completed for each fix in the isolated review worktree. The final reproducible gate then ran in the main checkout after the review branch was fast-forwarded.

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 65 passed
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/selected-css-pilot_adaptation-not_assessed.json` — passed
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli validate-evidence data/evidence/seed-records.json` — passed
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/pilot_adaptation-not_assessed` — passed, 32 final rows

---

_Fixed: 2026-09-22T03:36:38Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
