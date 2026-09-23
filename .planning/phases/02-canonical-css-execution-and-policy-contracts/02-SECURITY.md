---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: open_threats
threats_open: 2
asvs_level: 1
block_on: high
audited: "2026-09-23"
---

# Phase 02 — Security

## OPEN_THREATS

**Phase:** 02 — Canonical CSS Execution and Policy Contracts
**Closed:** 44/46 | **Open:** 2/46
**ASVS Level:** 1 | **Block threshold:** high

This update rechecks the six findings left open by the prior audit after
Plan 02-13. All twelve Phase 2 plan-time threat models remain represented in
the register. Four final public replay/profiling findings are closed, but two
structural-provenance findings remain open because rehashed non-wall-time
profile metadata is accepted by `verify-run`.

## Threat Verification

| Threat ID | Category | Severity | Disposition | Status | Evidence |
|---|---|---|---|---|---|
| T-02-01 | Information disclosure | high | mitigate | closed | Frozen copied capability values in `src/bp_registry/canonical/execution.py:55`; hostile reachability test at `tests/canonical/test_truth_boundary.py:26`. |
| T-02-02 | Tampering | medium | mitigate | closed | Strict frozen, extra-forbid models at `src/bp_registry/manifests.py:29`; bounded binary artifact parsing at `src/bp_registry/artifacts.py:37`. |
| T-02-03 | Repudiation | high | mitigate | closed | Domain-separated public identity includes the full manifest digest, artifact hashes, compact execution contract, sample, run/shot, check type, and syndrome at `src/bp_registry/canonical/verification.py:35`; public reuse calls `validate_canonical_shot` before accepting a terminal at `src/bp_registry/canonical/execution.py:343`. Changed-full-manifest replay rejects before result mutation in `tests/test_canonical_cli.py:102`. |
| T-02-04 | Denial of service | medium | mitigate | closed | Bounded canonical iteration/input fields at `src/bp_registry/manifests.py:252` and non-finite terminal path at `src/bp_registry/canonical/execution.py:463`. |
| T-02-05 | Elevation of privilege | high | mitigate | closed | Closed role-to-kind registry and rejection of unknown kinds at `src/bp_registry/canonical/contracts.py:52` and `:225`; import/callable rejection test at `tests/canonical/test_contracts.py:58`. |
| T-02-06 | Tampering | high | mitigate | closed | Frozen capability view and typed, binding-owned state updates at `src/bp_registry/canonical/execution.py:49` and `:90`; ownership test at `tests/canonical/test_contracts.py:104`. |
| T-02-07 | Information disclosure | high | mitigate | closed | Capability values are recursively copied/frozen at `src/bp_registry/canonical/execution.py:55`; hostile truth-boundary test at `tests/canonical/test_truth_boundary.py:26`. |
| T-02-08 | Denial of service | medium | mitigate | closed | Composition validation rejects duplicate bindings/state, invalid hooks, and undefined requirements at `src/bp_registry/canonical/contracts.py:225`; adversarial coverage at `tests/canonical/test_contracts.py:75`. |
| T-02-09 | Tampering | medium | mitigate | closed | Strict finite canonical rate and fixed profile at `src/bp_registry/manifests.py:336`; resolved profile materializes in public preflight at `src/bp_registry/runner.py:117` and is asserted at `tests/test_canonical_cli.py:20`. |
| T-02-10 | Denial of service | medium | mitigate | closed | Bounded stable arithmetic and scoped floating exceptions in `src/bp_registry/canonical/numerics.py:48` and `:91`; non-finite regression coverage at `tests/canonical/test_numerics.py:54`. |
| T-02-11 | Repudiation | medium | mitigate | closed | Public preflight records the complete resolved numerical profile at `src/bp_registry/runner.py:117`; canonical order/buffer and tie conventions materialize/test at `src/bp_registry/canonical/schedules.py:18`, `src/bp_registry/canonical/numerics.py:16`, and `tests/canonical/test_numerics.py:25`. |
| T-02-12 | Tampering | high | mitigate | closed | Flooding reads an immutable old snapshot, builds separate buffers, and validates finite values at `src/bp_registry/canonical/schedules.py:139`; atomic commit is at `src/bp_registry/canonical/execution.py:160`. |
| T-02-13 | Denial of service | high | mitigate | closed | Bounded `WorkVector` limits and all-ancestor reservation precede work at `src/bp_registry/canonical/budgets.py:34` and `:253`; public cap-denial test at `tests/canonical/test_budgets.py:160`. |
| T-02-14 | Tampering | high | mitigate | closed | One-shot reservation finalization and exception rollback at `src/bp_registry/canonical/budgets.py:193` and `:302`; no-mutation rollback test at `tests/canonical/test_budgets.py:144`. |
| T-02-15 | Repudiation | high | mitigate | closed | Unique leaf IDs and lineage-derived summaries at `src/bp_registry/canonical/budgets.py:253` and `:282`; reduction test at `tests/canonical/test_work_accounting.py:46`. |
| T-02-16 | Spoofing | medium | mitigate | closed | Typed observed/unavailable measurements preserve method, scope, unit, precision, and reason at `src/bp_registry/canonical/budgets.py:90`; coverage at `tests/canonical/test_work_accounting.py:68`. |
| T-02-17 | Tampering | high | mitigate | closed | Original, working, attempt, and candidate lineage IDs are rederived from the public execution identity and candidate content at `src/bp_registry/canonical/verification.py:227`, then checked in terminal, attempt, candidate, and selection facts at `:233`. Rehashed lineage tampering is rejected in `tests/test_canonical_cli.py:223`. |
| T-02-18 | Tampering / Information disclosure | high | mitigate | closed | Absolute, parent, symlink, root-escape, conflict, and digest checks at `src/bp_registry/canonical/tracing.py:83`, `:216`, and `:235`; adversarial sidecar test at `tests/canonical/test_tracing.py:166`. |
| T-02-19 | Denial of service | high | mitigate | closed | Record/byte limits and observer-only truncation are enforced at `src/bp_registry/canonical/tracing.py:120` and `:174`; cap tests at `tests/canonical/test_tracing.py:139` and `:154`. |
| T-02-20 | Information disclosure | high | mitigate | closed | Candidate is frozen and selected before evaluator access at `src/bp_registry/canonical/execution.py:449` and `:472`; selection/evaluation separation test at `tests/canonical/test_truth_boundary.py:84`. |
| T-02-21 | Spoofing | high | mitigate | closed | Native facts require observed qualification or explicit unavailable reason at `src/bp_registry/canonical/metrics.py:19`; opaque-zero rejection at `tests/test_reference_smoke.py:46`. |
| T-02-22 | Tampering | medium | mitigate | closed | Exact tagged metric-fact validation and portable round trip at `src/bp_registry/canonical/metrics.py:91` and `src/bp_registry/ledger.py:96`; round-trip test at `tests/test_ledger.py:77`. |
| T-02-23 | Repudiation | high | mitigate | closed | Availability denominators are counted separately and unavailable values are not reduced at `src/bp_registry/ledger.py:342` and `:369`; coverage at `tests/test_ledger.py:112`. |
| T-02-24 | Denial of service | low | accept | **Documented accepted risk:** `AR-02-01` below. Strict metric validation is additionally present at `src/bp_registry/canonical/metrics.py:32`. |
| T-02-25 | Information disclosure | high | mitigate | closed | Profiling accepts only numeric thread-count allowlist entries at `src/bp_registry/canonical/profiling.py:27`, `:78`, and `:304`; coverage at `tests/canonical/test_profiling.py:25`. |
| T-02-26 | Tampering | high | mitigate | closed | Replay compares candidate, termination, work, lineage, and semantic digest at `src/bp_registry/canonical/profiling.py:179`; identity binding is enforced at `:209` and tested at `tests/canonical/test_profiling.py:140`. |
| T-02-27 | Repudiation | high | mitigate | closed | Cohort, stratum, inclusion probability, reason, and pre-outcome status are typed at `src/bp_registry/canonical/profiling.py:107`; cohort claims test at `tests/canonical/test_profiling.py:122`. |
| T-02-28 | Denial of service | medium | mitigate | closed | Canonical preflight rejects every public profile plan except `clean`/`low_overhead` before sampling, ledger creation, or kernel work at `src/bp_registry/manifests.py:529`; representative and non-clean variants are proven ledger-free in `tests/test_canonical_cli.py:314`. |
| T-02-29 | Tampering / Information disclosure | high | mitigate | closed | The public identity binds resolved raw and semantic artifact hashes at `src/bp_registry/canonical/verification.py:35`, and every persisted structural event must match the current preflighted identity at `:179`; preflight resolves and verifies the artifact before sampling at `src/bp_registry/manifests.py:529`. |
| T-02-30 | Information disclosure | high | mitigate | closed | Runner samples outside the engine at `src/bp_registry/runner.py:171`; the engine evaluates only after frozen selection at `src/bp_registry/canonical/execution.py:469`; integration coverage at `tests/test_canonical_cli.py:235`. |
| T-02-31 | Tampering / Repudiation | high | mitigate | **open — blocking** | `verify-run` does invoke semantic reconstruction (`src/bp_registry/cli.py:275`), but its profile control is incomplete. `ProfileMeasurement.from_evidence` requires only the wall-time method (`src/bp_registry/canonical/profiling.py:105`); the underlying `Measurement` accepts arbitrary nonempty method/scope/unit/precision values (`src/bp_registry/canonical/budgets.py:90`). An adversarial edit of both runtime and terminal `process_cpu_time.method`, with every event ID and `ledger_sha256` recomputed, is accepted by `verify-run`. |
| T-02-32 | Denial of service | high | mitigate | closed | Matrix/record/byte/count limits are validated in `src/bp_registry/artifacts.py:16`, `src/bp_registry/manifests.py:252`, and atomic reservations in `src/bp_registry/canonical/execution.py:415`; public cap test at `tests/canonical/test_budgets.py:160`. |
| T-02-33 | Spoofing / Repudiation | high | mitigate | closed | Evidence-maturity and no-promotion documentation contracts are checked at `tests/canonical/test_policy_evidence.py:33`; checked evidence labels are verified in `tests/test_canonical_cli.py:180`. |
| T-02-34 | Tampering | medium | mitigate | closed | The documented preflight/canonical/reconcile/verify commands execute in `tests/test_canonical_cli.py:20`, including resolved semantic profile and policy identity assertions. |
| T-02-35 | Information disclosure | medium | mitigate | closed | Documentation and profile evidence use the environment allowlist at `src/bp_registry/canonical/profiling.py:27`; documentation contract coverage is at `tests/canonical/test_policy_evidence.py:33`. |
| T-02-36 | Denial of service | low | accept | **Documented accepted risk:** `AR-02-02` below; the checked development manifest has finite work/trace limits. |
| T-02-10-01 | Tampering | high | mitigate | closed | Public preflight admits exactly the implemented seven-role baseline at `src/bp_registry/manifests.py:375`; alternate kinds reject before sampling in `src/bp_registry/manifests.py:529` and test at `tests/test_canonical_cli.py:293`. |
| T-02-10-02 | Denial of service | high | mitigate | closed | BP-call reservation and complete-sweep reservation occur before mutation at `src/bp_registry/canonical/execution.py:415` and `:153`; public no-sweep denial test at `tests/canonical/test_budgets.py:160`. |
| T-02-10-03 | Repudiation | high | mitigate | closed | Work and termination facts reduce from the same committed attempt summary at `src/bp_registry/canonical/execution.py:398`; BP-call evidence test at `tests/test_canonical_cli.py:365`. |
| T-02-11-01 | Spoofing | high | mitigate | closed | Every non-begin append requires the live owner and lifecycle kinds are reserved at `src/bp_registry/ledger.py:489` and `:535`; multi-writer test at `tests/test_ledger.py:224`. |
| T-02-11-02 | Tampering | high | mitigate | closed | Candidate payload validates original rank, integer dtype, non-boolean type, and binary values before hashing at `src/bp_registry/canonical/lineage.py:167`; rejection test at `tests/canonical/test_tracing.py:81`. |
| T-02-11-03 | Elevation of privilege | high | mitigate | closed | Engine requires the current `WorkingProblem` object and recomputes candidate ID from current working/attempt ancestry before evaluation at `src/bp_registry/canonical/execution.py:243`; hostile selector test at `tests/canonical/test_truth_boundary.py:84`. Shared checked-shot candidate IDs are safe semantic content IDs: durable event identity and writer ownership remain scoped to `(run_id, shot_id)` at `src/bp_registry/ledger.py:489`. |
| T-02-12-01 | Tampering | medium | mitigate | closed | Enabled profile controls materialize in `src/bp_registry/canonical/execution.py:455`; unsupported trace levels fail before a ledger at `src/bp_registry/manifests.py:529`; public tests at `tests/test_canonical_cli.py:102` and `:132`. |
| T-02-12-02 | Denial of service | medium | mitigate | closed | Profiler-owned `tracemalloc` cleanup is in the outer `finally` at `src/bp_registry/canonical/profiling.py:411`; exceptional cleanup tests at `tests/canonical/test_profiling.py:88` and `:106`. |
| T-02-12-03 | Repudiation | high | mitigate | **open — blocking** | The validator does enforce ordered stream grammar, numerical-failure qualification, and trace-off at `src/bp_registry/canonical/verification.py:159`, but it does not validate the full typed profile contract claimed by the mitigation. The same rehashed `process_cpu_time.method` tamper accepted by `verify-run` changes a persisted structural provenance fact without detection; therefore the checked-result structural sequence is not fully validated. |
| T-02-12-04 | Information disclosure | medium | mitigate | closed | Typed profile environment evidence rejects non-allowlisted fields at `src/bp_registry/canonical/profiling.py:78` and only gathers allowlisted thread variables at `:304`. |

## Open (blocking — severity at or above high)

| Threat ID | Severity | Missing mitigation | Files searched |
|---|---|---|---|
| T-02-31 | high | Public verification does not constrain all profile measurement method/scope/unit/precision fields to the admitted local profiler contract. Rehashed non-wall-time profile metadata verifies. | `src/bp_registry/canonical/profiling.py`, `src/bp_registry/canonical/budgets.py`, `src/bp_registry/canonical/verification.py`, `src/bp_registry/cli.py`, `tests/test_canonical_cli.py` |
| T-02-12-03 | high | The required full structural provenance grammar remains incomplete because typed profile facts can be altered and rehashed without rejection. | `src/bp_registry/canonical/profiling.py`, `src/bp_registry/canonical/verification.py`, `src/bp_registry/cli.py`, `data/results/canonical-three-qubit-development` |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-02-01 | T-02-24 | Local research inputs plus strict validation and record-size bounds make residual malformed-metric resource impact low. | Phase 2 plan | 2026-09-23 |
| AR-02-02 | T-02-36 | Development tutorial/profile defaults are bounded and explicitly not publication-scale campaign settings. | Phase 2 plan | 2026-09-23 |

## Unregistered Flags

None. No Phase 2 summary contains a `## Threat Flags` entry.

## Verification Evidence

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_public_replay_rejects_same_run_changed_full_manifest_before_result tests/test_canonical_cli.py::test_public_execution_identity_binds_manifest_code_sample_and_shot tests/test_canonical_cli.py::test_verify_run_rejects_rehashed_work_and_policy_tampering tests/test_canonical_cli.py::test_verify_run_rejects_rehashed_structural_provenance_tampering tests/test_canonical_cli.py::test_verify_run_rederives_budget_and_numerical_terminal_semantics tests/test_canonical_cli.py::test_public_preflight_rejects_unbounded_profile_cohorts_before_ledger` — **12 passed**.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` — **2 checked terminal rows semantically verified** against the present preflighted manifest and artifact.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — **157 passed**.
- Adversarial temporary output: changing both runtime and terminal `profile.runtime.process_cpu_time.method` to `attacker-controlled-method`, recomputing every canonical `event_id` and `result.json` `ledger_sha256`, then running `verify-run` — **incorrectly accepted**. This is the blocking evidence above; checked artifacts were not modified.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open Blocking | Open Non-blocking | Run By |
|---|---:|---:|---:|---:|---|
| 2026-09-23 | 36 | 36 | 0 | 0 | Prior ASVS L1 audit (superseded; Plans 02-10–12 absent) |
| 2026-09-23 | 46 | 40 | 5 | 1 | ASVS L1 re-audit after Plans 02-10–12 |
| 2026-09-23 | 46 | 44 | 2 | 0 | ASVS L1 re-audit after Plan 02-13 / Wave 11 |

**threats_open:** 2
