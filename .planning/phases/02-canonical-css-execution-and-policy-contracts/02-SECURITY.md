---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: open_threats
threats_open: 5
asvs_level: 1
block_on: high
audited: "2026-09-23"
---

# Phase 02 — Security

## OPEN_THREATS

**Phase:** 02 — Canonical CSS Execution and Policy Contracts
**Closed:** 40/46 | **Open:** 6/46
**ASVS Level:** 1 | **Block threshold:** high

This supersedes the prior 36/36 report, which predated Plans 02-10 through
02-12. All twelve Phase 2 plan-time threat models were re-read and checked
against the current implementation, tests, and checked canonical artifacts.

## Threat Verification

| Threat ID | Category | Severity | Disposition | Status | Evidence |
|---|---|---|---|---|---|
| T-02-01 | Information disclosure | high | mitigate | closed | Frozen copied capability values in `src/bp_registry/canonical/execution.py:55`; hostile reachability test at `tests/canonical/test_truth_boundary.py:26`. |
| T-02-02 | Tampering | medium | mitigate | closed | Strict frozen, extra-forbid models at `src/bp_registry/manifests.py:29`; bounded binary artifact parsing at `src/bp_registry/artifacts.py:37`. |
| T-02-03 | Repudiation | high | mitigate | **open — blocking** | Canonical replay identity is not complete: `_identity()` covers only compact manifest fields and syndrome (`src/bp_registry/canonical/execution.py:211`), while `_existing_structural()` accepts a prior terminal when that partial identity matches (`:342`). A changed full manifest/artifact/profile can therefore reuse a run/shot terminal rather than produce a conflict. |
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
| T-02-17 | Tampering | high | mitigate | **open — blocking** | Lineage/event replay is content-addressed only from the incomplete compact identity. `original`, `working`, and `attempt` IDs derive from `_identity()` (`src/bp_registry/canonical/execution.py:217` and `:223`), so a full-manifest change can retain stale lineage under a reused run/shot. The declared canonical-content/replay-conflict control is incomplete. |
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
| T-02-28 | Denial of service | medium | mitigate | **open — non-blocking** | Trace record/byte caps exist, but the required profile cohort quota does not. `CanonicalProfilePlanV2` admits `representative` at `src/bp_registry/manifests.py:309`, and public execution enables allocation profiling from that level at `src/bp_registry/canonical/execution.py:455`; no field, validation, counter, or test enforces a profile/cohort quota. |
| T-02-29 | Tampering / Information disclosure | high | mitigate | **open — blocking** | Artifact preflight verifies the new input, but structural replay uses only the partial canonical identity (`src/bp_registry/canonical/execution.py:211` and `:342`). It may accept an existing output terminal with stale artifact/profile context instead of binding the write/replay to the full preflighted artifact identity. |
| T-02-30 | Information disclosure | high | mitigate | closed | Runner samples outside the engine at `src/bp_registry/runner.py:171`; the engine evaluates only after frozen selection at `src/bp_registry/canonical/execution.py:469`; integration coverage at `tests/test_canonical_cli.py:235`. |
| T-02-31 | Tampering / Repudiation | high | mitigate | **open — blocking** | `verify-run` checks result/ledger hash, terminal manifest field, row IDs, and outcome (`src/bp_registry/cli.py:271`), but does not independently validate structural work, lineage, sample identity, profile facts, or sidecar claims. The required verified semantic identities and conflict-replay defense are therefore absent. |
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
| T-02-12-03 | Repudiation | high | mitigate | **open — blocking** | The checked artifacts are currently fresh, but the verifier does not validate the full structural sequence/provenance before deriving trust. It omits work, lineage, sample, profile, and sidecar checks (`src/bp_registry/cli.py:271`), so the declared validated-sequence reconstruction mitigation is not present. |
| T-02-12-04 | Information disclosure | medium | mitigate | closed | Typed profile environment evidence rejects non-allowlisted fields at `src/bp_registry/canonical/profiling.py:78` and only gathers allowlisted thread variables at `:304`. |

## Open (blocking — severity at or above high)

| Threat ID | Severity | Missing mitigation | Files searched |
|---|---|---|---|
| T-02-03 | high | Full canonical execution identity is not compared before reusing a structural terminal; stale changed-manifest replay is accepted. | `src/bp_registry/canonical/execution.py`, `src/bp_registry/runner.py`, `tests/test_canonical_cli.py` |
| T-02-17 | high | Original/working/attempt lineage derives from that incomplete replay identity, so stale lineage can be reused across a changed full manifest. | `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/lineage.py`, `tests/canonical/test_truth_boundary.py` |
| T-02-29 | high | Artifact/output preflight does not bind structural replay/write identity to the complete preflighted manifest/artifact context. | `src/bp_registry/artifacts.py`, `src/bp_registry/manifests.py`, `src/bp_registry/canonical/execution.py` |
| T-02-31 | high | `verify-run` does not reconstruct and validate structural work, lineage, sample, profile, or sidecar provenance claims. | `src/bp_registry/cli.py`, `src/bp_registry/ledger.py`, `data/results/canonical-three-qubit-development` |
| T-02-12-03 | high | Checked-result verification does not validate the full structural event sequence/provenance before accepting reconstructed result evidence. | `src/bp_registry/cli.py`, `src/bp_registry/canonical/execution.py`, `tests/test_canonical_cli.py` |

## Open (non-blocking — below the high threshold)

| Threat ID | Severity | Missing mitigation | Files searched |
|---|---|---|---|
| T-02-28 | medium | No configured profile/cohort quota is declared or enforced for `representative` public profiling. | `src/bp_registry/manifests.py`, `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/profiling.py`, `tests/canonical/test_profiling.py`, `tests/test_canonical_cli.py` |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-02-01 | T-02-24 | Local research inputs plus strict validation and record-size bounds make residual malformed-metric resource impact low. | Phase 2 plan | 2026-09-23 |
| AR-02-02 | T-02-36 | Development tutorial/profile defaults are bounded and explicitly not publication-scale campaign settings. | Phase 2 plan | 2026-09-23 |

## Threat Flags

No Phase 2 summary contains a `## Threat Flags` entry. No unregistered
implementation flag was recorded.

## Verification Evidence

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — **145 passed**.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/canonical-three-qubit-development.json` — admitted only the executable baseline and emitted exact work caps plus resolved numerical profile.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` — **2 current terminal rows verified** against the present ledger, manifest, and independent outcome. This does not close T-02-31 or T-02-12-03 because the current verifier omits the structural claims listed above.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open Blocking | Open Non-blocking | Run By |
|---|---:|---:|---:|---:|---|
| 2026-09-23 | 36 | 36 | 0 | 0 | Prior ASVS L1 audit (superseded; Plans 02-10–12 absent) |
| 2026-09-23 | 46 | 40 | 5 | 1 | ASVS L1 re-audit after Plans 02-10–12 |

**threats_open:** 5
