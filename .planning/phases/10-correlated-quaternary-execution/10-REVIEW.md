---
phase: 10-correlated-quaternary-execution
reviewed: 2026-10-08T04:43:04Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/qualify_phase10_native_asced.py
  - scripts/run_phase10_quaternary_gate.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - src/bp_registry/quaternary/asced.py
  - src/bp_registry/quaternary/execution.py
  - src/bp_registry/quaternary/native_asced.py
  - src/bp_registry/quaternary/qbpgd.py
  - tests/canonical/quaternary/test_asced_ensemble.py
  - tests/canonical/quaternary/test_asced_evidence.py
  - tests/canonical/quaternary/test_public_execution.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 10: Remediation Code Review Report

**Reviewed:** 2026-10-08T04:43:04Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This re-review covers remediation commits `a358fe0..70e888b` against the six findings recorded in the prior review. Five findings are resolved. Native receipt validation now catches several structural corruptions, but it still accepts a self-consistent, fabricated native aggregate because the claimed run output has no independent content anchor. The original report and the fixer report remain in Git history and [10-REVIEW-FIX.md](/hpc/home/mg551/storage/survey_bp/.planning/phases/10-correlated-quaternary-execution/10-REVIEW-FIX.md).

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` passed: **168 passed in 22.43s**. The full replay command was launched separately and was still running when this report was finalized; it is not claimed as completed verification here.

## Resolution Audit

- **CR-01 — resolved.** Public scalar and Q-BPGD paths construct typed schedules/transforms; MBP4 and aSCED reject transforms they cannot execute. Regression coverage checks a variable-serial normalized public run.
- **CR-02 — resolved.** `QuaternaryExperimentV2.shot_budget` is constrained to the single supported observation with `Literal[1]`.
- **CR-03 — resolved.** Verification requires `--replay`, regenerates all decoder output through `run()`, and byte-compares both the ledger and study receipt.
- **WR-01 — resolved.** aSCED rejects MBP4 kernels whose iteration cap differs from the controller cap before accounting path work.
- **WR-02 — resolved.** Native builds now require explicit network integration selection and a caller-owned root; normal tests exercise refusal paths only.
- **CR-04 — open.** The finding below remains a release blocker.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-04: BLOCKER — native aggregate receipts remain forgeable without an independent run-output anchor

**File:**
[`src/bp_registry/quaternary/native_asced.py:102`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/native_asced.py:102), [`src/bp_registry/quaternary/native_asced.py:141`](/hpc/home/mg551/storage/survey_bp/src/bp_registry/quaternary/native_asced.py:141), [`tests/canonical/quaternary/test_asced_evidence.py:175`](/hpc/home/mg551/storage/survey_bp/tests/canonical/quaternary/test_asced_evidence.py:175)

**Issue:** The new verifier validates receipt structure and binds a run receipt to an actual build-receipt file, but the run aggregate remains a mutable JSON assertion. It does not compare the aggregate to an immutable digest of the approved retained run receipt, an externally stored artifact, or a native-generated signed/output file. The successful-command checks also inspect self-reported command arrays.

This was reproduced without invoking the native executable: copy the committed build and run receipts into a temporary directory, retain the original `build_receipt_sha256`, then change only these run-receipt fields:

```json
{
  "aggregate.logical_errors": 1,
  "aggregate.failure_I": 1,
  "aggregate.failure_II": 0,
  "aggregate.logical_error_rate": 0.00625,
  "metric_facts[native_logical_errors].value": 1
}
```

`verify_native_asced_receipt()` accepted that forged receipt and `run_native_asced_reference()` returned `logical_errors=1` and `logical_error_rate=0.00625`, although the retained native receipt reports 10 errors in 160 trials. The aggregate arithmetic is valid, so the current tamper tests at lines 175-199 do not cover this attack.

**Fix:** Bind the approved Phase 10 native run receipt content to an immutable expected digest before accepting its aggregate, for example in the frozen study contract or a reviewed module constant:

```python
if sha256(receipt_path.read_bytes()).hexdigest() != APPROVED_PHASE10_NATIVE_RUN_RECEIPT_SHA256:
    raise ValueError("native run receipt differs from approved retained evidence")
```

Add a regression test that changes the internally consistent aggregate and matching metric fact above, while retaining the real build receipt, and assert rejection. A fixed digest closes this specific retained-evidence forgery; future native campaigns need a new approved digest or an external immutable/signature-backed result artifact before their output can be accepted as provenance.

---

_Reviewed: 2026-10-08T04:43:04Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
