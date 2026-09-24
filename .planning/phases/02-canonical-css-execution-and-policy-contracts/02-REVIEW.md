---
phase: 02-canonical-css-execution-and-policy-contracts
reviewed: 2026-09-24T00:09:02Z
depth: deep
files_reviewed: 10
files_reviewed_list:
  - data/results/canonical-three-qubit-development/events.jsonl
  - data/results/canonical-three-qubit-development/result.json
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/profiling.py
  - src/bp_registry/canonical/verification.py
  - src/bp_registry/cli.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - tests/test_canonical_cli.py
findings:
  critical: 4
  warning: 0
  info: 0
  total: 4
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-24T00:09:02Z
**Depth:** deep
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Wave 12 materially improves verification. I reproduced the three former attacks and each now rejects after recomputing every event ID and `result.json` ledger digest: a numerical-failure work/policy forgery, a count-budget iteration/cap forgery, and a profile `process_cpu_time.method` forgery. The checked artifact also passes `verify-run`; the independently reported full suite is 173 passing tests.

Those checks do not establish semantic completeness. A verifier that accepts a fully rehashed ledger must independently derive every meaning-bearing fact, not merely accept an internally consistent event hash chain. I reproduced four remaining classes of accepted falsification, including the security audit's completed-path field set. Consequently, Phase 02 is **not ready to ship**.

## Narrative Findings (AI reviewer)

The former CR-01, CR-02, and CR-03 are closed by the Wave 12 reconstruction and strict profile contract. The findings below supersede them.

### Completed-path persisted-field inventory

This is the bounded inventory of the exact fields emitted for a completed shot. “Bound” means compared to an independently reconstructed preflight/context fact; “self-consistent” means a uniform rewrite of every event can still pass.

| Persisted event / fields | Verification basis | Result |
|---|---|---|
| Every event: `manifest_sha256`, raw/semantic artifact hashes, `canonical_identity`, `execution_identity` | `PublicShotContext` | Bound |
| Every event: `composition_identity`, `policy_effects` | `PublicShotContext` | Bound |
| Every event: `code_id`, `evidence_relation`, `fixture`, `assessment_status`, `decoder_seed_identity` | Compared only to the first ledger event | **Self-consistent; CR-06** |
| `shot_begin.sample_seed_identity` | Re-sampled public context | Bound |
| `attempt.scope`, `attempt.max_iterations` | Exact literal/context | Bound |
| Completed `attempt.attempt_lineage_id` | Reconstructed original/working/attempt lineage | Bound |
| `runtime.profile` and terminal `profile` | Equal copies plus admitted producer/value-domain contract | Mostly bound; raw-RSS normalization relation is not checked (**CR-07**) |
| `candidate.candidate`, `candidate.candidate_lineage_id` | Fresh deterministic reconstruction | Bound |
| `candidate.attempt_lineage_id` | Schema/type only; no comparison | **Unbound; CR-05** |
| `selection.original_lineage_id`, `working_lineage_id`, `attempt_lineage_id`, `candidate_lineage_id` | Reconstructed lineage | Bound |
| `selection.selection_status` | Schema only; no comparison | **Unbound; CR-05** |
| `work.qualified_iterations`, `work.work_vector` | Fresh deterministic reconstruction | Bound |
| Terminal candidate, iteration, work, lineages, outcome, and logical-action agreement | Fresh reconstruction and independent evaluator | Bound |
| Terminal `converged` and `selection_status` | Schema only; no comparison | **Unbound; CR-05** |

The same audit found two adjacent grammar gaps outside the completed row: numerical/non-completed `attempt_lineage_id` is only type-checked, and an admitted count-budget-exhausted `runtime` event is never passed through `_exact_data`. They belong in the CR-05 repair matrix so exact grammar does not regress by terminal branch.

## Critical Issues

### CR-04 [BLOCKER]: A persistent numerical failure makes valid evidence unverifiable

**File:** `src/bp_registry/canonical/verification.py:254`

**Issue:** `validate_canonical_shot()` calls `_expected_attempt(context)` before it examines the persisted terminal type. `_expected_attempt()` calls `FloodingSchedule.sweep()` and does not catch `NumericalFailure`. Therefore, when the original numerical failure is still present during verification, `verify-run` raises `NumericalFailure` instead of validating the intentionally non-reproduced numerical-failure grammar. This contradicts the recorded terminal status `not_independently_reproduced_numerical_failure`: an actual, persistent numerical defect makes its valid failure evidence unusable for replay and reuse.

**Reproduction:** In a disposable run, I forced shot 0 to raise `NumericalFailure("persistent")`, restored the normal schedule while writing the public output, then re-enabled the same failure for `verify_run()`. The command raised `NumericalFailure: persistent` rather than returning a verified numerical terminal.

**Fix:** Branch on a persisted `numerical_failure` terminal before deterministic schedule replay, validate its strict event grammar and facts that are derivable without replay, and deliberately retain the explicit “not independently reproduced” status. Add a regression where the same numerical failure remains active during `verify-run`.

### CR-05 [BLOCKER]: Exact completed-path grammar still accepts forged status and lineage semantics

**File:** `src/bp_registry/canonical/verification.py:263-265, 302-305, 322-330`

**Issue:** Exact field *sets* are now enforced, but several declared semantic values are never compared to their independently reconstructed values. The completed branch does not require terminal `converged is True`, terminal `selection_status == "frozen_decoder_visible_candidate"`, selection-event `selection_status == "frozen_decoder_visible_candidate"`, or candidate-event `attempt_lineage_id ==` the reconstructed attempt ID. It also accepts arbitrary string attempt IDs for numerical and other non-completed branches. Finally, the admitted count-budget-exhausted branch validates its terminal shape but never exact-validates the separate `runtime.data` field set.

**Reproduction:** For four separate normal completed outputs, I changed exactly one value (`termination.data.converged=False`; terminal `selection_status="forged"`; selection `selection_status="forged"`; candidate-event `attempt_lineage_id="attempt-forged"`), rehashed all events and the result ledger, and each `verify_run()` call succeeded. A forced numerical output with `attempt.attempt_lineage_id="attempt-forged"` also succeeded. An admitted count-budget-exhausted output with `runtime.data["forged_extra"]="secret"` also succeeded.

**Fix:** Derive the canonical attempt ID once from the public execution identity and enforce it on every attempt-bearing event. Require the completed terminal's `converged` and both completed selection statuses to their canonical literals. Call `_exact_data()` on `runtime` in every branch where a runtime event is admitted. Add a parameterized rehash/reject matrix for every row marked CR-05 in the inventory, across completed, numerical, count-denied, and max-iteration paths.

### CR-06 [BLOCKER]: Uniformly forged provenance labels are trusted from the ledger itself

**File:** `src/bp_registry/canonical/verification.py:188-205`

**Issue:** `_validate_common()` independently binds only hashes, canonical/execution identity, composition identity, and policy effects. The other common scientific provenance claims—`code_id`, `evidence_relation`, `fixture`, `assessment_status`, and `decoder_seed_identity`—are merely required to match the first event's attacker-controlled baseline. Because ledger event IDs and the result digest are public hashes rather than signatures, a uniformly rehashed false label passes as self-consistent but false evidence.

**Reproduction:** I changed `data.code_id` to `"forged-code"` on every event in a normal output, recomputed all event IDs and `result.json.ledger_sha256`, and `verify_run()` returned `verified_final_rows: 2` with the forged code ID present. The same baseline-only path applies to each other listed common field.

**Fix:** Extend `PublicShotContext` and `canonical_public_shot_context()` with the expected values from the preflighted manifest, then compare all five fields directly in `_validate_common()`. Keep cross-event equality as an additional invariant, never as the trust root. Add one uniform-rehash rejection test per field.

### CR-07 [BLOCKER]: Profile provenance accepts an incoherent raw-RSS source fact

**File:** `src/bp_registry/canonical/profiling.py:189-194`

**Issue:** The new profile validator checks raw RSS platform, unit, type, and non-negativity, but not the relationship between the raw source value and normalized `peak_host_memory`. On Linux the local profiler's normalized bytes must be `rss_raw_value * 1024`; on Darwin it must equal the raw byte value. A ledger can therefore claim a raw RSS observation of zero while also asserting a nonzero normalized peak, and `verify-run` certifies incompatible profiler provenance.

**Reproduction:** I changed both runtime/terminal profile copies' `raw_context.rss_raw_value` to `0` while retaining the observed normalized `peak_host_memory.value` of `483188736`, rehashed all events and the result ledger, and `verify_run()` succeeded.

**Fix:** In the observed-RSS branch, derive the normalized byte count from the declared supported platform and require exact equality with `rss.value` (Linux: `raw * 1024`; Darwin: `raw`). Add rehashed rejection tests for Linux and Darwin raw-value/normalized-value mismatches.

---

_Reviewed: 2026-09-24T00:09:02Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
