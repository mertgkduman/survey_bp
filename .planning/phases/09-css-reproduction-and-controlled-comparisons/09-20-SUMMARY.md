---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "20"
subsystem: canonical-resource-guard
tags: [canonical, resource-caps, interruption, complete]
status: complete
plan_head_before: 4dbe834
dependency_graph:
  requires: [09-08, 09-16]
  provides: [derived canonical resource profiles, guarded materialized execution, typed interruptions]
  affects: [09-17, 09-18]
key_files:
  modified:
    - src/bp_registry/ledger.py
    - src/bp_registry/runner.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/phase5.py
    - src/bp_registry/canonical/relay.py
    - src/bp_registry/canonical/mbbp.py
    - src/bp_registry/canonical/tracing.py
    - tests/canonical/test_resource_guard.py
    - tests/canonical/test_resource_profiles.py
    - tests/canonical/test_resource_boundaries.py
actuals:
  tasks: 3
---

# Phase 09 Plan 20: Canonical Resource Guard Summary

## Delivered

- Independently derives digest-bound event, work, artifact, and control-reserve maxima for registered baseline, local, Relay, Phase 5, and V7 list/vote routes. Unknown routes fail closed. Local bounds cover all V4 WorkVector fields; Phase 5 uses its admission-validated fieldwise caps, which BudgetTree checks before producer commits.
- Binds versioned, engine-enforced 262,144-byte framed event and artifact ceilings. Exact byte reservations precede durable ledger and artifact writes. A separate 32,768-byte reserve permits one interruption control receipt after scientific caps are exhausted.
- Implements strict and interruptible one-unit authorizations, digest verification, permanent cap latching, named monotonic work boundaries, positive wall overshoot, and producer-committed cumulative WorkVector snapshots. A guarded materialized shot returns a typed terminal or interruption with no decoder outcome on interruption.
- Covers flooding, local/residual, guided/Phase 5 branches, Relay legs/transfers, V7 list/vote members, and trace sidecars. The unguarded interface remains source compatible.

The byte ceilings are protocol limits because canonical event payloads contain open nested structures; they are not claims of naturally exact maximum payload sizes. Plan 09-17 owns campaign sample/result artifact writes and partial-attempt receipt publication.

## Verification

- Combined focused guard, profile, boundary, Relay, tracing, V7, ledger, and CLI suite: 164 passed in 112.88 seconds.
- Real strict guarded Hsu local and damped guided-decimation materialized shots both reached terminal; retained as a regression in `test_resource_profiles.py`.
- V7 list/vote guarded terminal regression and producer-boundary tests: 59 focused tests passed in the boundary agent's run.

## Commits

`10b2ada`, `d938b8a`, `1e3731f`, `4f7d142`, `47d406b`, `f6e5503`, `e9df161`, `d8b5bf2`, and `dd9bed3` contain the implementation and focused tests. Interleaved Plan 09-20 documentation commits specify the enforced ceilings and committed-work contract.

## Self-Check: PASSED

The listed routes derive bounded profiles, guarded execution stops before unauthorized mutation, and the focused regressions pass. Wave 5 full-suite validation is recorded separately in `09-VALIDATION.md`.
