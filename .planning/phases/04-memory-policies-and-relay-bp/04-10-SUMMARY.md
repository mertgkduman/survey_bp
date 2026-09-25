---
phase: 04-memory-policies-and-relay-bp
plan: "10"
subsystem: phase4-staged-relay-execution
tags: [relay-bp, memory-policies, native-reference, public-verification, provenance, tdd]
requires: [04-06, 04-08, 04-09, 04-15]
provides: [matched-three-arm-bb144-tracer, exact-stage-reuse, public-v4-relay-execution]
affects: [04-11, 04-12, 04-13, 04-14, phase4-pilots]
tech-stack:
  added: []
  patterns: [stage-local-exact-author-build, public-decoder-visible-observation, immutable-incomplete-stage-retention]
key-files:
  created:
    - scripts/run_phase4_pilots.py
  modified:
    - data/manifests/phase4-memory-relay-bb144.json
    - data/manifests/phase4-memory-relay-b1.json
    - data/manifests/phase4-memory-relay-hgp.json
    - src/bp_registry/cli.py
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - tests/canonical/test_phase4_evidence.py
    - tests/test_canonical_cli.py
    - data/manifests/schema-canonical-v4.json
decisions:
  - "Native Relay stages clone and build only trmue/relay v0.2.2 at 14cb31a18f9b9d7d099791b793e35b8a2951f8f3 in a durable stage-local checkout; the installed fork is rejected."
  - "Canonical and native arms share a public decoder-visible CSS observation and physical sample identity while retaining separate source, translation, configuration, and environment identities."
  - "Incomplete native stages are immutable evidence and require a new stage identity before retry."
  - "V4 memory-only manifests retain the historical compact V3 execution and verification representation; only a populated relay field selects the Phase 4 Relay kernel and verifier."
metrics:
  duration: "~1h 15m"
  completed: "2026-09-25"
  status: complete
plan_head_before: 0aa09229e4df12e8915eab25faa5288000b95d20
commits: 6
actuals:
  tokens: 14142
  tasks: 2
  commits: 6
---

# Phase 04 Plan 10: Staged Memory and Relay Pilot Execution Summary

Built a finite, identity-safe Phase 4 runner that publicly preflights, runs, and verifies canonical Relay arms alongside the exact author Relay v0.2.2 implementation.

## Completed Tasks

1. **Matched BB-144 canonical/native tracer**
   - Ran source-procedure canonical Relay, canonical-default Relay, and exact author v0.2.2 native Relay on the same public CSS observation.
   - Preserved separate manifest, policy, code, environment, source, translation, sample namespace, and stage identities.
   - The final bounded tracer is retained at `/tmp/tmp.BKWaTCCuuy/gross-bb-144-trace-227b7f53ff791224/stage.json` with status `completed`, shared sample identity `078d307bc6b5cf100d230b01439bafbac8757b56c95ee1b3a8452e1723bf9625`, and three completed arms. The native arm used the stage-local exact-author checkout and reported two aggregate iterations.

2. **Three-code stage reuse and retention**
   - Extended BB-144, B1, and HGP manifests with the finite two-leg Relay contract and one transfer budget.
   - Admitted benchmark, calibration, evaluation, factorial, native, and trace stage names through one identity protocol.
   - Completed records reuse only exact identities. Mismatches are archived; incomplete native evidence remains visible and cannot silently retry under the same identity.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'runner_tracer or matched_native or public_boundary or stage_identity'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'stage_reuse or mismatch or interrupted or three_codes or public_verify'` — 4 passed, 1 skipped.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py tests/canonical/test_relay.py tests/canonical/test_relay_differential.py` — 33 passed, 1 skipped.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py::test_canonical_v4_schema_is_generated_from_the_public_memory_contract tests/test_manifest.py::test_canonical_v4_preflight_admits_ordered_repeated_memory_compositions tests/test_manifest.py::test_canonical_v4_rejects_incompatible_memory_before_artifact_loading tests/test_canonical_cli.py::test_canonical_v4_memory_composition_preflights_runs_and_verifies_publicly tests/test_canonical_cli.py::test_retained_hsu_group_pilot_is_source_labeled_and_independently_verifiable tests/test_canonical_cli.py::test_checked_canonical_result_is_idempotent_and_honestly_labeled tests/canonical/test_phase4_evidence.py::test_public_verify_executes_phase4_relay_through_cli` — 7 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 361 passed, 1 skipped.
- Bounded temporary-directory BB-144 tracer — completed all three arms; both canonical outputs passed public `preflight`, `canonical`, and `verify-run`, with V4 Relay transfer evidence in each canonical ledger.

## TDD Gate Compliance

| Task | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| Task 1: matched BB-144 stage | `.gsd/tdd-evidence/04-10-task-1-red.json` (`RED_EVIDENCE_OK`) | `2513aa0` | Passed |
| Task 2: exact stage reuse | `.gsd/tdd-evidence/04-10-task-2-red.json` (`RED_EVIDENCE_OK`) | `f696ae6` | Passed |

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 2 - Public Relay continuity] Retained the preflighted V4 Relay contract through the public execution boundary.**
   - **Found during:** Task 1 public BB-144 tracer.
   - **Issue:** The existing public canonical runner converted V4 manifests to a compact V3 kernel manifest, silently dropping memory and Relay fields. Public preflight could therefore parse a Relay manifest while public run did not execute Relay.
   - **Fix:** Added the V4 Relay field to the complete public manifest, retained memory bindings and relay controls in the compact V4 kernel input, selected the V4 relay verifier for canonical results, and exposed a truth-blind public canonical observation command for native translation.
   - **Files modified:** `src/bp_registry/manifests.py`, `src/bp_registry/runner.py`, `src/bp_registry/cli.py`, `tests/canonical/test_phase4_evidence.py`.
   - **Verification:** Public CLI preflight/run/verify now emits and verifies `relay_transfer` evidence for the finite BB-144 manifest.
   - **Commit:** `2513aa0`.

2. **[Rule 1 - Backward-compatible V4 identity] Restored retained memory-only V4 and legacy canonical verification.**
   - **Found during:** Wave 8 full-suite regression gate.
   - **Issue:** Requiring `relay` in every V4 manifest rejected the earlier V4 memory-only public contract. Applying null stripping to every compact manifest also changed retained V2/V3 canonical identities, causing independent verification of historical evidence to fail.
   - **Fix:** Made `relay` optional in the V4 public schema and regenerated its checked schema. Memory-only V4 manifests keep the exact historical V3 compact kernel representation and canonical verifier; only V4 manifests with `relay` use the Phase 4 Relay kernel and structural verifier.
   - **Files modified:** `data/manifests/schema-canonical-v4.json`, `src/bp_registry/manifests.py`, `src/bp_registry/runner.py`, `src/bp_registry/cli.py`, `tests/test_canonical_cli.py`.
   - **Verification:** The three original manifest failures, three original CLI failures, and explicit Relay public preflight/run/verify regression all passed; full suite passed 361 tests with one expected skip.
   - **Commit:** `0f2dbf8`.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed `scripts/run_phase4_pilots.py` and all three Phase 4 manifests exist.
- Confirmed task commits `2a152ff`, `2513aa0`, `f696ae6`, and regression commit `0f2dbf8` exist.
- Confirmed the final bounded BB-144 stage record has three completed, separately identified arms.
