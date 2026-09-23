---
phase: 02-canonical-css-execution-and-policy-contracts
reviewed: 2026-09-23T23:21:33Z
depth: deep
files_reviewed: 9
files_reviewed_list:
  - data/results/canonical-three-qubit-development/events.jsonl
  - data/results/canonical-three-qubit-development/result.json
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/profiling.py
  - src/bp_registry/canonical/verification.py
  - src/bp_registry/cli.py
  - src/bp_registry/manifests.py
  - src/bp_registry/runner.py
  - tests/test_canonical_cli.py
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-23T23:21:33Z
**Depth:** deep
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Wave 11 closes the former stale-full-manifest replay defect: reuse now binds the full manifest/artifact/sample/shot identity, and the changed-procedure regression rejects stale evidence before result mutation. It also makes `verify-run` re-execute the normal completed baseline path.

The structural verifier remains incomplete for failure and resource evidence. I independently rehashed three disposable ledgers and updated their `result.json` ledger digest; all then passed `verify_run()`. Therefore the command can still certify falsified policy, work, iteration, budget, and profiling-method provenance. The passing checked-artifact command and 157-test suite do not demonstrate tamper resistance for these paths.

## Narrative Findings (AI reviewer)

The previous CR-01 (reusing a terminal from a changed full manifest) is closed by `PublicShotContext.execution_identity` and validated reuse. The previous CR-02 (structural verification trusting attacker-rehashed facts) remains open in the termination-specific and profile-validation branches below.

## Critical Issues

### CR-01 [BLOCKER]: Numerical-failure evidence can claim false BP work and policy effects

**File:** `src/bp_registry/canonical/verification.py:201`
**Issue:** The numerical-failure branch returns at line 213 after inspecting only the terminal's own work vector and a five-kind grammar. It does not compare the separate `work` event to the terminal, require the expected `missingness` payload, or verify policy/composition facts on the attempt and work events. The common-event loop at lines 185-195 binds only manifest/artifact/execution identities.

Reproduction: in a disposable output, force shot 0 to raise `NumericalFailure`, restore the normal sweep, and let `run_canonical()` complete the run. Change the numerical shot's `work.data.work_vector.bp_calls` from `1` to `0` and its `attempt.data.policy_effects.update.effect` from `active` to `identity_only`; recompute every canonical event ID and `result.json.ledger_sha256`. `verify_run()` returned `final_row_count=2`.

**Fix:** Before returning from the numerical-failure branch, validate every event's composition identity and policy effects against `PublicShotContext`; require exactly one work event whose full `WorkVector` equals the terminal; require the exact candidate-missingness fact; and validate the zero-sweep qualified-iteration record. Add a rehashed numerical-failure test for each of these fields.

### CR-02 [BLOCKER]: Budget-denial iteration and configured-cap evidence is not reconstructed

**File:** `src/bp_registry/canonical/verification.py:214`
**Issue:** For every non-completed, non-numerical terminal, the verifier compares termination and work vector but never compares terminal `iterations`, the work event's `qualified_iterations`, or `budget_termination`. `_expected_attempt()` returns only the termination, work vector, and iteration count; the branch at lines 254-262 only checks candidate/outcome absence and event-kind order.

Reproduction: run a disposable manifest with `attempt.work_limits.check_to_variable_updates=0`. Then change shot 0's terminal `iterations` from `0` to `8`, its `budget_termination.configured_limit` from `0` to `999`, and the work event's `qualified_iterations.count` from `0` to `8`. After recomputing all event IDs and the result ledger digest, `verify_run()` again returned `final_row_count=2`.

**Fix:** Have deterministic reconstruction produce the complete expected denial object (scope, resource, configured cap, consumed amount, reason, and iterations). Compare it to both terminal and work facts for all count-exhausted/max-iteration paths, including `qualified_iterations` schedule and atomic-unit fields. Add rehashed denial/max-iteration tampering regressions.

### CR-03 [BLOCKER]: Profile verifier accepts forged instrumentation methods

**File:** `src/bp_registry/canonical/profiling.py:105`
**Issue:** `ProfileMeasurement.from_evidence()` checks exact field sets but only constrains the wall-clock method at line 121. `_validate_profile()` then only compares enabled/level to the plan (`src/bp_registry/canonical/verification.py:153-156`). Thus the CPU-time, RSS, concurrency, machine, device, overhead, and allocation method/scope/unit/precision claims are attacker-controlled if the runtime and terminal profile copies agree.

Reproduction: generate a normal disposable public output, change both copies of `profile.runtime.process_cpu_time.method` to `attacker-declared`, recompute event IDs and `result.json.ledger_sha256`, then call `verify_run()`. It returned `final_row_count=2`.

**Fix:** Add a public low-overhead profile-evidence validator that enforces the admitted method/scope/unit/precision and observed-versus-unavailable status for every measurement while deliberately not requiring nondeterministic values to equal a replay. Invoke it after parsing both runtime and terminal evidence, and cover rehashed tampering of every profile metric family.

---

_Reviewed: 2026-09-23T23:21:33Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
