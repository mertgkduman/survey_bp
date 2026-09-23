---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-23"
---

# Phase 02 — Security

> ASVS L1 verification of the plan-time STRIDE register against implemented controls and the green Phase 2 validation suite.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Persisted inputs → preflight | Untrusted manifests, matrices, policy bindings, and paths enter strict validation. | Scientific configuration and filesystem references |
| Runner → canonical engine → evaluator | Decoder-visible observations cross into policy execution while hidden truth remains outside until frozen selection. | Syndrome/prior data; hidden truth only at evaluation |
| Policy registry → lifecycle | Persisted policy kinds resolve to closed implementations with scoped capabilities and owned state. | Typed policy decisions and private state |
| Numerical kernel → scheduler/budgets | Message updates consume bounded numerical inputs and atomic work reservations. | Float64 messages, work vectors, termination evidence |
| Execution → ledger/sidecars/results | Runtime state becomes durable, hash-linked, queryable evidence. | Events, lineage, metrics, traces, outcomes |
| Profiling/tracing → research claims | Selected measurements and diagnostics become researcher-facing evidence. | Runtime/resource facts, cohorts, semantic digests |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------|--------|
| T-02-01 | Information disclosure | Policy views | high | mitigate | Frozen copied capability views and hostile reachability tests in `test_truth_boundary.py`. | closed |
| T-02-02 | Tampering | Manifest/numerical inputs | medium | mitigate | Strict extra-forbid schemas plus finite, binary, and dimension validation in manifest/canonical tests. | closed |
| T-02-03 | Repudiation | Ledger ownership/replay | high | mitigate | Content identity, ownership locking, idempotency, conflict rejection, flush/fsync, and concurrency tests. | closed |
| T-02-04 | Denial of service | BP iterations/input sizes | medium | mitigate | Bounded manifests and iterations with typed nonfinite termination. | closed |
| T-02-05 | Elevation of privilege | Policy registry | high | mitigate | Closed discriminated registry rejects import paths, arbitrary callables, and unknown policy kinds. | closed |
| T-02-06 | Tampering | Policy decisions/state | high | mitigate | Frozen views, typed decision validation, lifecycle ownership checks, and private engine state. | closed |
| T-02-07 | Information disclosure | Policy capabilities | high | mitigate | Decoder-visible copied values only; inherited hostile reachability coverage remains green. | closed |
| T-02-08 | Denial of service | Composition graph | medium | mitigate | Preflight bounds and rejection of cycles, duplicates, unknown hooks, and unsatisfied capabilities. | closed |
| T-02-09 | Tampering | Numerical profile | medium | mitigate | Strict finite inputs and fully materialized resolved numerical evidence. | closed |
| T-02-10 | Denial of service | Box-plus/messages | medium | mitigate | Stable bounded arithmetic, scoped floating exceptions, and typed `NumericalFailure`. | closed |
| T-02-11 | Repudiation | Backend/order behavior | medium | mitigate | Profile, precision, backend, edge order, ties, and buffer phases are recorded and golden-tested. | closed |
| T-02-12 | Tampering | Schedule mutation | high | mitigate | Immutable old-message snapshots, separate buffers, finiteness checks, and atomic sweep commits. | closed |
| T-02-13 | Denial of service | Hierarchical budgets | high | mitigate | Bounded integer limits and ancestor-wide reserve-before-work checks. | closed |
| T-02-14 | Tampering | Reservation state | high | mitigate | One-shot tokens, exception-safe rollback, and no-partial-mutation invariant tests. | closed |
| T-02-15 | Repudiation | Work summaries | high | mitigate | Unique leaf deltas and lineage-derived ancestor reductions prevent double counting. | closed |
| T-02-16 | Spoofing | Runtime/resource metrics | medium | mitigate | Method, scope, unit, precision, context, and explicit unavailable reasons are persisted. | closed |
| T-02-17 | Tampering | Lineage/event identity | high | mitigate | Canonical content IDs, typed parent validation, append-only conflicts, and replay tests. | closed |
| T-02-18 | Tampering / Information disclosure | Trace paths | high | mitigate | Absolute/parent/symlink rejection, confined roots, content addressing, and digest verification. | closed |
| T-02-19 | Denial of service | Trace/candidate payloads | high | mitigate | Record, byte, and payload caps with observational truncation independent of kernel control. | closed |
| T-02-20 | Information disclosure | Evaluation annotations | high | mitigate | Truth-aware annotations append only after immutable selection and remain absent from policy views. | closed |
| T-02-21 | Spoofing | Native work metrics | high | mitigate | Observed facts require qualification; opaque work is explicit null-plus-reason, never inferred. | closed |
| T-02-22 | Tampering | Metric serialization | medium | mitigate | Strict tagged validation and round-trip tests preserve availability variants. | closed |
| T-02-23 | Repudiation | Aggregate comparison | high | mitigate | Availability denominators are separate and unavailable facts cannot enter numeric reductions. | closed |
| T-02-24 | Denial of service | Malformed metric payload | low | accept | Strict bounds/type/finite validation and existing local record-size limits constrain impact. | closed |
| T-02-25 | Information disclosure | Profiler environment | high | mitigate | Explicit machine/thread/backend allowlist excludes environment values, secrets, and raw paths. | closed |
| T-02-26 | Tampering | Profile replay | high | mitigate | Deterministic identity links and semantic agreement checks bind paired measurements. | closed |
| T-02-27 | Repudiation | Cohort claims | high | mitigate | Stratum, inclusion probability, reason, and representative/diagnostic status are persisted. | closed |
| T-02-28 | Denial of service | Deep profile/trace | medium | mitigate | Cohort quotas, bounded levels, and explicit adapter missingness limit resource use. | closed |
| T-02-29 | Tampering / Information disclosure | Artifact/output paths | high | mitigate | Root confinement, traversal/symlink rejection, bounded reads, and content identity preflight. | closed |
| T-02-30 | Information disclosure | Runner truth boundary | high | mitigate | Hidden truth remains in the runner; only copied original problems enter the engine before selection. | closed |
| T-02-31 | Tampering / Repudiation | Result reconstruction | high | mitigate | Results rebuild from validated terminal rows and verified hashes/identities; conflicting reruns fail. | closed |
| T-02-32 | Denial of service | CLI resource controls | high | mitigate | Matrix, record, byte, and count limits validate before work; hierarchical budgets enforce execution. | closed |
| T-02-33 | Spoofing / Repudiation | Reproduction/novelty claims | high | mitigate | Documentation tests enforce evidence maturity, checked links, provisional status, and forbidden promotion. | closed |
| T-02-34 | Tampering | Tutorial drift | medium | mitigate | Documented commands execute against checked manifests/results and compare semantic fields. | closed |
| T-02-35 | Information disclosure | Profiling documentation | medium | mitigate | Examples use allowlisted fields and exclude secrets/private paths; digests are identity-only. | closed |
| T-02-36 | Denial of service | Tutorial/profile defaults | low | accept | Checked development inputs and bounded quotas are used; campaign budgets remain a later preregistration decision. | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-02-01 | T-02-24 | Local research inputs plus strict validation and record-size bounds make residual malformed-metric resource impact low. | Phase 2 plan | 2026-09-23 |
| AR-02-02 | T-02-36 | Development tutorial/profile defaults are bounded and explicitly not publication-scale campaign settings. | Phase 2 plan | 2026-09-23 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-23 | 36 | 36 | 0 | GSD ASVS L1 verification |

## Verification Evidence

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 126 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` — checked result verified.
- `02-VALIDATION.md` maps each task and threat reference to a green automated command.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-23 at ASVS level 1.
