---
phase: 11-quaternary-reproduction-and-comparisons
reviewed: 2026-10-14T23:30:00Z
depth: deep
files_reviewed: 55
files_reviewed_list:
  - data/artifacts/gb46-h44.alist
  - data/artifacts/quaternary-a5.json
  - data/artifacts/quaternary-a5.provenance.json
  - data/manifests/phase11-asced-figure2-gb46.json
  - data/manifests/phase11-complete-methods.json
  - data/manifests/phase11-mbp4-figures8-9-five-qubit.json
  - data/manifests/phase11-qbpgd-figure7-a5.json
  - data/native/phase11-asced-injected-input-diff.patch
  - data/native/phase11-asced-injected-input-proposal.json
  - data/native/phase11-asced-matched-input-qualification.json
  - data/results/phase11-asced-figure2/assessment.json
  - data/results/phase11-assessment/assessment.json
  - data/results/phase11-assessment/verification.json
  - data/results/phase11-controlled-evaluation/bb72/evaluation-receipt.json
  - data/results/phase11-controlled-evaluation/gb46/evaluation-receipt.json
  - data/results/phase11-controlled-evaluation/verification.json
  - data/results/phase11-mbp4-figures8-9/assessment.json
  - data/results/phase11-policy-comparisons/verification.json
  - data/results/phase11-production-authorization.json
  - data/results/phase11-qbpgd-figure7/assessment.json
  - data/source-targets/phase11-asced-figure2-gb46.json
  - data/source-targets/phase11-mbp4-figures8-9-five-qubit.json
  - data/source-targets/phase11-qbpgd-figure7-a5.json
  - data/studies/phase11-bb72-joint-separate.json
  - data/studies/phase11-fixed-marginal-design.json
  - data/studies/phase11-gb46-joint-separate.json
  - data/studies/phase11-policy-comparisons.json
  - docs/campaigns.md
  - scripts/qualify_phase11_native_asced.py
  - scripts/run_phase11_controlled.py
  - scripts/run_phase11_controlled_evaluation.py
  - scripts/run_phase11_policy_comparisons.py
  - scripts/run_phase11_source_studies.py
  - src/bp_registry/campaigns/cli.py
  - src/bp_registry/campaigns/contracts.py
  - src/bp_registry/campaigns/controlled_evaluation.py
  - src/bp_registry/campaigns/controlled_execution.py
  - src/bp_registry/campaigns/profiling_gate.py
  - src/bp_registry/campaigns/sizing.py
  - src/bp_registry/campaigns/statistics.py
  - src/bp_registry/campaigns/targets.py
  - src/bp_registry/quaternary/problems.py
  - src/bp_registry/quaternary/qbpgd.py
  - tests/canonical/quaternary/test_phase11_mbp4_target.py
  - tests/canonical/quaternary/test_phase11_native_asced.py
  - tests/test_phase11_controlled_evaluation.py
  - tests/test_phase11_correlation_statistics.py
  - tests/test_phase11_final_assessment.py
  - tests/test_phase11_joint_separate.py
  - tests/test_phase11_policy_comparisons.py
  - tests/test_phase11_qbpgd_source.py
  - tests/test_phase11_quaternary_campaign.py
  - tests/test_phase11_resource_gate.py
  - tests/test_phase11_source_assessments.py
  - tests/test_phase11_source_targets.py
findings:
  critical: 4
  warning: 1
  info: 0
  total: 5
status: resolved
---

# Phase 11: Code Review Report

**Reviewed:** 2026-10-14T23:30:00Z
**Depth:** deep
**Files Reviewed:** 55
**Status:** resolved after fixes

## Summary

The review covered the Phase 11 source, scripts, schemas, immutable artifacts, and regressions, including cross-module traces from authorization through controlled execution and assessment. JSON artifacts parse successfully. The retained `preserve_unavailable` native route and `preserve_deny` publication authorization remain represented as denials, but four defects can accept altered scientific evidence, misclassify terminal evidence, or write through unsafe symlinks.

## Narrative Findings (AI reviewer)

The findings below were confirmed by direct execution in temporary output roots. They are independent of the checked-in zero-dispatch publication receipts, but block a future controlled campaign or source qualification from being evidence-safe.

## Critical Issues

### CR-01: BLOCKER — controlled verification accepts self-consistent fabricated pair outcomes

**File:** `src/bp_registry/campaigns/controlled_execution.py:869-884`, `src/bp_registry/campaigns/controlled_execution.py:956-998`, `src/bp_registry/campaigns/controlled_execution.py:1019-1027`

**Issue:** `_phase11_load_pairs()` only checks the pair's self-declared digest and duplicate physical identity. `verify_phase11_controlled()` then counts `all_shot` fields without binding each path to the deterministic materialized sample or independently checking candidates, terminal outcomes, and work. `assess_phase11_controlled()` uses that verifier directly. In a temporary six-pair run, changing `pairs/lower_y/0.json` from its produced joint terminal to `wrong_logical_action`, changing `all_shot` to `failure`, and recomputing `record_sha256` made `verify` return `status: ok` while changing the reported joint failures from 2 to 3.

**Fix:** Add a per-path verifier that derives the expected sample from `(point_id, sample_id, design digest)`, checks its physical-error and materialized hashes, and independently reconstructs the deterministic arm semantics before accepting the stored terminal fields. Invoke it from both `verify_phase11_controlled()` and `assess_phase11_controlled()`. A self-hash should remain an integrity check, not the sole provenance check.

### CR-02: BLOCKER — Q-BPGD verification trusts any qualification payload with a copied preflight

**File:** `scripts/run_phase11_source_studies.py:475-489`

**Issue:** For a Q-BPGD dictionary target, `verify()` returns success whenever `assessment["preflight"] == expected`; it never validates `assessment_sha256`, `admitted_shots`, or the nested `qualification` object. A temporary bounded Q-BPGD run was modified so `qualification.performance_verdict` became `fabricated_performance_claim` without updating any digest. The `verify` command still returned `{"status": "inconclusive", "admitted_shots": 1}`. This permits a corrupted qualification record to retain a verified status.

**Fix:** Give completed Q-BPGD qualifications a dedicated verifier. Require the assessment digest, exact immutable preflight, approved one-shot schema and claim limits, and independently reconstructed deterministic work/candidate evidence; validate elapsed time only as a cap rather than byte equality. Reject any additional or changed qualification fields.

### CR-03: BLOCKER — a timed-out binary component can be counted as a successful separate arm

**File:** `src/bp_registry/campaigns/controlled_execution.py:638-645`

**Issue:** The separate-arm status overrides component state only for `nonconvergence`. A component that returns `timeout`, `infrastructure_interruption`, `invalid_syndrome`, or another unsuccessful terminal while retaining a candidate is evaluated by `_arm_evaluation()` and can become `exact` and `success`. Directly invoking `run_joint_separate_unit()` with an exact recovery and an X component marked `timeout` produced `timeout exact success` for `(component terminal, separate terminal, separate all-shot)`. This changes the all-shot denominator and failure count.

**Fix:** Define a complete, tested precedence table for component terminal states. Before using the combined candidate evaluation, propagate every non-success component terminal to the separate arm (with `infrastructure_interruption` remaining incomplete), and only allow an evaluated success when both component terminals are successful.

### CR-04: BLOCKER — dangling symlinks can redirect bounded-output writes outside the selected root

**File:** `src/bp_registry/campaigns/controlled_execution.py:782-787`; `scripts/run_phase11_policy_comparisons.py:46-53`

**Issue:** `_phase11_safe_root()` calls `resolve()` before its symlink check and only checks `path.is_symlink()` when `path.exists()` is true. A dangling `--output-root` symlink therefore resolves to its external target and is created there. Separately, `_write_exact()` only checks `path.exists()`; for a dangling record symlink that is false, so `Path.write_bytes()` follows the link and writes the record to its target. Both routes permit a shared or untrusted output directory to redirect campaign writes.

**Fix:** Inspect the original path with `lstat` before resolving it, reject any symlink including a dangling link, and create/open output files relative to a verified root directory using no-follow semantics. Apply the same helper to policy comparison records and controlled-calibration outputs.

## Warnings

### WR-01: policy replay discards the stored record digest before validating it

**File:** `scripts/run_phase11_policy_comparisons.py:241-248`

**Issue:** `verify_policy_comparisons()` overwrites `observed["record_sha256"]` with a newly computed value before comparing it with the replay result. A tampered digest field therefore passes verification. The same normalization also hides changes to the stored timing payload rather than reporting that its sealed record no longer matches.

**Fix:** First validate the persisted `record_sha256` against the original unsigned stored record. Then compare a separate copy with only runtime fields normalized for nondeterministic timing. Do not mutate the object used for receipt-integrity validation.

---

_Reviewed: 2026-10-14T23:30:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_

## Resolution — 2026-10-14

| Finding | Disposition | Commit | Verification |
|---|---|---|---|
| CR-01 | Fixed: replay materialized samples and arm semantics before counting pair evidence | `372725b` | Controlled lifecycle and tamper regressions passed |
| CR-02 | Fixed: validate sealed Q-BPGD assessment, claim schema, and deterministic qualification evidence | `eea895b`, `8fc123c` | Q-BPGD tamper regression passed |
| CR-03 | Fixed: unsuccessful component terminals take precedence over candidate evaluation | `f994c4f` | Joint/separate focused suite: 15 passed |
| CR-04 | Fixed: reject symlinked output roots and records, including dangling links | `2819f02` | Controlled and policy symlink regressions passed |
| WR-01 | Fixed: validate persisted record digest before normalizing runtime fields | `c04c1cf` | Policy replay tamper regression passed |

The fixes preserve the sealed native-unavailable and production-denied decisions. The findings above remain as the original review record; all five have been addressed in the listed commits.
