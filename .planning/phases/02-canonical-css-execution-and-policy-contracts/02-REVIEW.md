---
phase: 02-canonical-css-execution-and-policy-contracts
reviewed: 2026-09-24T00:38:09Z
depth: deep
files_reviewed: 11
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
  - tests/canonical/test_profiling.py
  - tests/test_canonical_cli.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-24T00:38:09Z
**Depth:** deep
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Wave 13 closes CR-04 through CR-07. I independently rehashed each prior completed-status/candidate-lineage attack, all five uniform manifest-label attacks, numerical attempt-lineage evidence, and both Linux/Darwin raw-RSS mismatch variants; every one now rejects. A persistent `NumericalFailure` also verifies successfully while the failure remains active, without a replay sweep. The focused verification set passed (4 tests), and the unchanged checked artifact passed `verify-run`. The executor reports 178 passing tests; the parent suite was still running at this review.

One meaning-bearing profile branch remains unverified. It lets a rehashed ledger replace a recorded nonzero RSS observation with an impossible `RSS normalization semantics unavailable` record and have `verify-run` certify it. The issue hides resource evidence and violates the stated local-producer provenance contract, so Phase 02 remains **blocked**.

## Narrative Findings (AI reviewer)

### Public evidence inventory after Wave 13

“Bound” means the verifier reconstructs the value from trusted preflight/context or enforces the only producer grammar rather than accepting a self-consistent rehash.

| Persisted public evidence | Verification basis | Result |
|---|---|---|
| Result JSON: identity/labels, manifest/ledger paths and digests, shot IDs, outcome/termination denominators, policy identity, and claim text | `_canonical_result_from_terminal_events()` is reconstructed and compared as the entire result object | Bound |
| Every event: envelope, ledger version, run/shot, ordering, no sidecar, and exact per-kind field set | `_validate_event_envelopes()` and `_exact_data()` | Bound |
| Common manifest facts: digests, `code_id`, evidence relation, fixture, assessment status, decoder seed, execution/canonical identity, composition, policy effects | Direct `PublicShotContext` comparison from preflight | Bound |
| `shot_begin.sample_seed_identity` | Public resampling | Bound |
| Every terminal class `attempt.scope`, max iterations, and attempt lineage | Reconstructed attempt ancestry | Bound |
| Completed candidate, candidate lineage, selection lineages/status, terminal convergence/status, iteration/work, independent outcome | Deterministic BP reconstruction plus evaluator | Bound |
| Count-denial budget fact, work/qualified iterations, admitted runtime envelope, and unavailable selection/outcome | Budget reconstruction and exact grammar | Bound |
| Maximum-iteration work/qualified iterations, convergence/status, runtime/profile | Deterministic BP reconstruction and exact grammar | Bound |
| Numerical missingness, one-call work, zero qualified iterations, terminal status and diagnostic shape | Strict terminal grammar before replay | Bound; active persistent failure positive control passes |
| Profile enabled/level, environment, metric method/scope/unit/precision/status/value domains, runtime-terminal equality | Strict local low-overhead contract; nondeterministic values intentionally not replayed | Bound |
| Observed RSS raw platform/unit/value to normalized bytes | Exact Linux/Darwin relation | Bound |
| RSS unavailable because normalization is unsupported: raw source context | No producer-specific raw-context grammar | **Unbound; CR-08** |

The last row is deliberately narrow. A verifier cannot prove a dynamic RSS number or host availability by rerunning a different process, but it can reject a raw-context representation that `LocalProfiler` could never emit for the declared unavailable reason.

## Critical Issues

### CR-08 [BLOCKER]: Rehashed RSS-unavailable evidence can erase a real resource observation with an impossible source context

**File:** `src/bp_registry/canonical/profiling.py:175-187`

**Issue:** When `peak_host_memory` is unavailable with reason `RSS normalization semantics unavailable`, the validator intentionally skips the empty-raw-context check at line 186 but does not replace it with the grammar emitted by `LocalProfiler._peak_rss()` (`profiling.py:430-435`). That producer always records exactly `rss_platform`, nonnegative integer `rss_raw_value`, and `rss_raw_unit: "unknown"` for this reason (and does not emit `rss_normalized_unit`). The verifier instead accepts `{}` or arbitrary scalar raw context. A fully rehashed ledger can therefore downgrade a real nonzero RSS observation to unavailable, discard its required source facts, and still be certified by `verify-run`.

**Reproduction:** Starting with a disposable normal Linux canonical output, I changed both runtime and terminal profiles to this syntactically valid unavailable measurement:

```json
{"value": null, "method": "resource.getrusage:RUSAGE_SELF:ru_maxrss:v1", "scope": "process", "unit": "bytes", "precision": "unknown", "unavailable_reason": "RSS normalization semantics unavailable"}
```

I set both `raw_context` values to `{}`, recomputed every canonical event ID and `result.json.ledger_sha256`, and `verify_run()` accepted the output. The acceptance is impossible for this unavailable reason under `LocalProfiler`'s own producer grammar.

**Fix:** Add a distinct unavailable-normalization branch. Require `raw_context` to have exactly `rss_platform`, `rss_raw_value`, and `rss_raw_unit`; require a nonempty platform string other than `Linux`/`Darwin`, a non-boolean nonnegative integer raw value, and raw unit `"unknown"`. Continue to require empty raw context for adapter/negative-RSS failures. Add a direct unknown-platform producer positive test and an end-to-end rehashed rejection that transforms observed RSS into this malformed unavailable record. Do not introduce fresh-run equality for timing or observed resource values.

---

_Reviewed: 2026-09-24T00:38:09Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
