---
phase: 02-canonical-css-execution-and-policy-contracts
reviewed: 2026-09-23T22:42:38Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - data/manifests/canonical-three-qubit-development.json
  - data/manifests/schema-canonical-v2.json
  - data/results/canonical-three-qubit-development/events.jsonl
  - data/results/canonical-three-qubit-development/result.json
  - docs/canonical-engine.md
  - src/bp_registry/canonical/budgets.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/lineage.py
  - src/bp_registry/canonical/problems.py
  - src/bp_registry/canonical/profiling.py
  - src/bp_registry/canonical/tracing.py
  - src/bp_registry/cli.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/reference.py
  - src/bp_registry/runner.py
  - src/bp_registry/sampling.py
  - tests/canonical/test_budgets.py
  - tests/canonical/test_policy_evidence.py
  - tests/canonical/test_profiling.py
  - tests/canonical/test_tracing.py
  - tests/canonical/test_truth_boundary.py
  - tests/test_canonical_cli.py
  - tests/test_ledger.py
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-23T22:42:38Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

The normal public path closes all findings from the previous review: the public boundary admits only the implemented baseline; scoped reservations include one BP call; canonical appends require the live writer owner; profiler cleanup and replay identity checks are in place; unsupported tracing fails closed; the tutorial uses the Z-check convention; candidate payload/current-working validation is strict; and native `ldpc` loading is lazy.

Two new blockers remain in the provenance path. An existing terminal can be reused for a different fully preflighted manifest, and `verify-run` accepts structurally falsified policy/work evidence. Both contradict the project's requirement that checked simulation evidence remain traceable and independently verifiable.

The repeated `candidate_lineage_id` in the checked shots is not an active finding. The two events have distinct `(run_id, shot_id)` and `sample_seed_identity` values, but identical decoder-visible syndrome, deterministic attempt ordinal, and candidate. The lineage IDs are deliberately semantic/content-addressed and cannot carry hidden truth; `_require_current_candidate()` additionally requires the current in-memory working object and derives the expected candidate ID before evaluation. Consumers that need an execution-instance key must use the ledger shot key, not a semantic candidate ID.

## Narrative Findings (AI reviewer)

The 11 prior findings (`CR-01`–`CR-04`, `WR-01`–`WR-07`) were rechecked against the current code and checked evidence and are closed. The active findings below were discovered while tracing the repaired public execution and verification paths.

## Critical Issues

### CR-01 [BLOCKER]: A changed canonical manifest can silently reuse a terminal from a different experiment

**File:** `src/bp_registry/canonical/execution.py:371`

**Issue:** `run_canonical_structural_shot()` derives its idempotency identity solely from the compact kernel manifest and observed syndrome, then returns an existing terminal at lines 371–375. The compact manifest constructed by [`runner.py:147`](../../../src/bp_registry/runner.py:147) excludes the full manifest digest, artifact identity, public work caps, profile plan, evidence/source data, and sample identity. `run_canonical()` similarly treats any terminal with the same run/shot as present at [`cli.py:253`](../../../src/bp_registry/cli.py:253), without first validating it against the manifest now being run.

This was reproduced in a disposable output: a valid manifest differing only in `evidence.procedure` was selected with the same shot-0 observed syndrome. `run_canonical_one()` returned the old terminal, whose `data.manifest_sha256` remained the original digest; `run_canonical()` then wrote a result for the changed manifest, and only a later `verify-run` rejected it as stale. Thus the command that claims to construct a run can return success with an invalid ledger/result pair.

**Fix:** Make terminal reuse conditional on the resolved full-manifest identity and deterministic sample identity, not the compact decoder contract alone. Pass the expected manifest SHA-256 and `sample_seed_identity` into `_existing_structural()` and reject a mismatch before returning a terminal. Before `run_canonical()` treats a shot as present, validate its terminal against the current manifest (or call the same helper), so it cannot write a result that immediately fails verification.

Acceptance regression: create a valid same-run manifest variant with the same observable syndrome but a different full digest; reuse of its output path must raise a conflict before result creation, and no stale terminal may be returned.

### CR-02 [BLOCKER]: `verify-run` does not verify the structural evidence it claims to verify

**File:** `src/bp_registry/cli.py:271`

**Issue:** `_verify_canonical_run()` checks the result labels/hash, terminal shot IDs, terminal manifest digest, and independent outcome only. It never verifies `sample_seed_identity`, policy composition/effects, `work_vector`, attempt/candidate lineage, profile presence/shape, or the required structural-event sequence. The generic reader at [`ledger.py:401`](../../../src/bp_registry/ledger.py:401) validates JSON/event IDs and open/terminal ordering, but deliberately permits arbitrary `data` objects and therefore cannot provide these missing guarantees.

The gap is reproducible without touching checked artifacts: in a disposable copy of the checked ledger, changing both terminal `work_vector.bp_calls` values to `0` and changing `policy_effects.update.effect` to `identity_only`, then recomputing the two event IDs and the result's `ledger_sha256`, made `verify_run()` return success. This means a result described as "verified" can contain false work and policy provenance—the exact classes of evidence Phase 2 is intended to protect.

**Fix:** Add a canonical-run ledger validator invoked by both `run_canonical()` (before accepting pre-existing terminals) and `verify-run()`. For every expected shot, derive the sample identity from the resolved manifest; require the expected begin/attempt/candidate/selection/runtime/work/termination structure and common manifest/artifact/composition facts; rederive deterministic candidate, lineage, termination, and work facts from the canonical engine contract; and validate the typed profile facts against the admitted profile plan. Reconstruct `result.json` only after that validator succeeds.

Acceptance regression: mutate a temporary ledger's BP-call count or policy effect, recompute the event/result hashes, and assert `verify-run` fails. Also reject missing or mismatched sample, profile, work, or lineage structural facts.

---

_Reviewed: 2026-09-23T22:42:38Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
