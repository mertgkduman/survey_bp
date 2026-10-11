---
phase: "08"
slug: "reproducible-campaigns-and-statistical-assessment"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-11"
---

# Phase 8 — Security

## Trust Boundaries

| Boundary | Data Crossing | Control |
|---|---|---|
| Campaign input to frozen plan | Manifest, target, assessment, identities | Strict models, hash and path verification, bounded expansion |
| Worker to evidence | Unit receipts, ledgers, sidecars, observed resources | Private staging, immutable publication, independent replay |
| Evidence to inference | Merged terminals and target decisions | Exact coverage, matched samples, frozen outcome matrix and denominator rules |
| Campaign to scheduler | Array task, allocation and site facts | Literal validated argv, exact task selection, deny on missing ceilings |

## Threat Register

The initial 45 plan-time threats and 26 gap-closure threats were checked against the implemented boundaries at ASVS Level 1. Evidence paths below are relative to `src/bp_registry/campaigns/`.

| Threat ID | Category | Component | Severity | Disposition | Planned mitigation | Evidence | Status |
|---|---|---|---|---|---|---|---|
| T-08-01A | Tampering | shard seal | high | mitigate | Hash one byte snapshot, validate event lifecycle, fsync, atomically publish, and reject receipt mismatch. | contracts.py; shards.py | closed |
| T-08-01B | Information disclosure | campaign paths | medium | mitigate | Accept confined relative paths and reject traversal or symlink escape before reads. | contracts.py; shards.py | closed |
| T-08-01C | Denial of service | campaign bounds | medium | mitigate | Strictly bound arms, shots, events, and bytes before allocation or execution. | contracts.py; shards.py | closed |
| T-08-01SC | Tampering | dependencies | low | accept | No install occurs; only pinned existing dependencies and stdlib are used. | contracts.py; shards.py | closed |
| T-08-02A | Tampering | manifest preflight | high | mitigate | Frozen exact-field models, canonical digest, and cross-field validators reject rule drift. | contracts.py; planning.py | closed |
| T-08-02B | Denial of service | nested plans | medium | mitigate | Bound counts, arms, looks, families, strings, and serialized bytes. | contracts.py; planning.py | closed |
| T-08-02C | Repudiation | denominator policy | medium | mitigate | Require a total persisted mapping and rule identifier for every terminal class. | contracts.py; planning.py | closed |
| T-08-03A | Tampering | target bytes | high | mitigate | Hash immutable source/project snapshots and reject digest or calibration drift. | targets.py | closed |
| T-08-03B | Information disclosure | target paths | medium | mitigate | Confine paths and reject absolute, parent, and symlink escape. | targets.py | closed |
| T-08-03C | Spoofing | source identity | low | accept | Receipts distinguish content integrity from author authenticity and preserve source claims verbatim. | targets.py | closed |
| T-08-04A | Tampering | unit/shard planner | high | mitigate | Content-address exact sorted keys and require disjoint exhaustive coverage. | identity.py; planning.py; execution.py; shards.py; slurm.py | closed |
| T-08-04B | Repudiation | sample matching | high | mitigate | Persist identity derivations and compare sample hashes across arms. | identity.py; planning.py; execution.py; shards.py; slurm.py | closed |
| T-08-04C | Denial of service | work-plan expansion | medium | mitigate | Validate product sizes and byte bounds before materializing keys. | identity.py; planning.py; execution.py; shards.py; slurm.py | closed |
| T-08-05A | Tampering | shard input | high | mitigate | Validate bounded immutable byte snapshots, content hashes, lifecycle, replay, and expected keys. | shards.py | closed |
| T-08-05B | Repudiation | attempt lineage and duplicate contribution | high | mitigate | Retain all parent-linked attempt/stop receipts, accept interrupted-to-terminal recovery once, record identical terminal redundancy, and reject conflicts. | shards.py | closed |
| T-08-05C | Information disclosure | sidecar paths | medium | mitigate | Enforce relative confined paths and reject symlink traversal. | shards.py | closed |
| T-08-05D | Denial of service | shard size | medium | mitigate | Cap files, bytes, events, sidecars, and units before parse/allocation. | shards.py | closed |
| T-08-06A | Tampering | resume identity | high | mitigate | Require exact scientific/source/environment/dependency digests before reuse. | shards.py; execution.py | closed |
| T-08-06B | Repudiation | retry attempts and early stop | medium | mitigate | Parent-linked attempts plus deterministic decision reconstruction and atomic stop-receipt recovery preserve retry and authorized-undispatched evidence across the publication crash window. | shards.py; execution.py | closed |
| T-08-06C | Denial of service | repeated retry | low | mitigate | Bound attempts and reject already-complete or undeclared units. | shards.py; execution.py | closed |
| T-08-07A | Tampering | assessment inputs | high | mitigate | Bind procedure, alpha, target, tolerance, look, and count receipt hashes before calculation. | statistics.py | closed |
| T-08-07B | Repudiation | adaptive stopping | high | mitigate | Persist every completed look, alpha allocation, stop predicate result, and overshoot. | statistics.py | closed |
| T-08-07C | Denial of service | numeric inputs | low | mitigate | Bound counts/looks and reject nonfinite values before SciPy calls. | statistics.py | closed |
| T-08-08A | Tampering | pair join | high | mitigate | Require identical campaign/cohort/point/sample identities and reject partial or duplicate arms. | statistics.py; reporting.py | closed |
| T-08-08B | Repudiation | multiplicity family | medium | mitigate | Freeze full m; retain unavailable p*=1 sentinels, conservative ranks/multipliers, adjusted values, and inconclusive family/member verdicts. | statistics.py; reporting.py | closed |
| T-08-08C | Information disclosure | terminal details | low | accept | Reports contain scientific outcomes and allowlisted resource facts only, with no arbitrary environment dump. | statistics.py; reporting.py | closed |
| T-08-09A | Tampering | worker inputs | high | mitigate | Workers receive one frozen shard ID and verify campaign/plan digest before execution. | execution.py; planning.py | closed |
| T-08-09B | Denial of service | local concurrency | medium | mitigate | Bound processes, shards, threads, shots, and bytes before pool creation. | execution.py; planning.py | closed |
| T-08-09C | Information disclosure | environment receipt | medium | mitigate | Record only allowlisted thread/runtime facts and never arbitrary environment variables. | execution.py; planning.py | closed |
| T-08-09D | Repudiation | stop receipt publication crash | high | mitigate | Reconstruct complete-look decisions from immutable verified evidence and recover the deterministic stop receipt before any resumed dispatch. | execution.py; planning.py | closed |
| T-08-10A | Elevation of privilege | scheduler argv | high | mitigate | Construct argv arrays from bounded validated scalars; never invoke shell interpolation. | slurm.py | closed |
| T-08-10B | Tampering | array mapping | high | mitigate | Bind array index to one digest-checked frozen shard and reject out-of-range values. | slurm.py | closed |
| T-08-10C | Information disclosure | scheduler context | medium | mitigate | Allowlist recorded scheduler/environment fields and omit commands/environment secrets. | slurm.py | closed |
| T-08-11A | Tampering | report input | high | mitigate | Accept only validated receipts and recompute all summaries from terminal evidence. | reporting.py; statistics.py | closed |
| T-08-11B | Repudiation | verdict | high | mitigate | Persist exact rule, inputs, hashes, interval, target band, and reason. | reporting.py; statistics.py | closed |
| T-08-11C | Information disclosure | environment output | medium | mitigate | Serialize allowlisted non-secret context only. | reporting.py; statistics.py | closed |
| T-08-12A | Elevation of privilege | CLI scheduler command | high | mitigate | Route through validated argv adapter; never evaluate campaign text in a shell. | cli.py; slurm.py | closed |
| T-08-12B | Tampering | CLI input/output | high | mitigate | Verify hashes before mutation, confine output roots, and publish receipts atomically. | cli.py; slurm.py | closed |
| T-08-12C | Denial of service | CLI bounds | medium | mitigate | Apply contract limits before expanding or launching work. | cli.py; slurm.py | closed |
| T-08-13A | Tampering | profiling evidence | high | mitigate | Bind verified clean/profile, replay, merge, and site-capability hashes and require semantic agreement. | profiling_gate.py | closed |
| T-08-13B | Denial of service | resource projection | high | mitigate | Deny designs above measured ceilings and bound all arithmetic and shard sizes. | profiling_gate.py | closed |
| T-08-13C | Repudiation | authorization choice | medium | mitigate | Persist measurements, safety factor, ceilings, projections, decision, and reasons. | profiling_gate.py | closed |
| T-08-14A | Denial of service | bounded gate | high | mitigate | Hard-cap shots, shards, array tasks, concurrency, CPU, memory, wall time, and output bytes. | cli.py; execution.py; profiling_gate.py | closed |
| T-08-14B | Tampering | retained receipts | high | mitigate | Seal inputs, hash all evidence, independently replay, and byte-verify the report. | cli.py; execution.py; profiling_gate.py | closed |
| T-08-14C | Repudiation | assessment claim | medium | mitigate | Label not_assessed and retain target, rule, denominator, and authorization reasons. | cli.py; execution.py; profiling_gate.py | closed |

### Gap-closure audit (Plans 08-15–08-20)

The following groups cover every additional threat ID in the six gap plans. Each plan retains its individual category, severity, disposition, and mitigation text. The evidence column names the implementation and adversarial checks reviewed at closure.

| Threat IDs | Evidence reviewed | Status |
|---|---|---|
| T-08-15A–D | `contracts.py`, `execution.py`, `cli.py`; exact arm compatibility, immutable sample replay, unchanged canonical ledger, outer attempt hashes and tamper regression | closed |
| T-08-16A–D | `slurm.py`, `planning.py`, `cli.py`; literal bounded argv, selected shard identity, typed unavailable accounting, exact merge/resume and route tests | closed |
| T-08-17A–D | `reporting.py`, `statistics.py`; recomputed merge/report hashes, total denominator/treatment table, named nonnegative work, typed observations and zero-acceptance tests | closed |
| T-08-18A–E | `cli.py`, `reporting.py`; installed assessment/report/route reconstruction, bounded JSON, exact indexed receipt-to-attempt binding and tamper tests | closed |
| T-08-19A–D | New matched manifests, strict study/work plan, no-write preflight and `docs/campaigns.md`; four-unit cap and explicit `development_fixture` / `not_assessed` classification | closed |
| T-08-20A–D | Retained local and direct selected-shard ledgers, samples, attempts, merges, reports, route receipt, adversarial regression, measured process use and production denial | closed |
| T-08-SC | Existing locked virtual environment; no package installation, exact dependency/environment lock checks in the frozen work specification | closed |

The selected-shard route used direct execution, with no Slurm submission. Its typed scheduler/accounting fields explicitly say the allocation is a declared harness request and accounting is unavailable. Process wall time and cumulative RSS upper bounds are retained separately. This evidence does not establish safe site ceilings.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| R-08-01 | T-08-01SC | No new installation occurs; existing pinned dependencies and the standard library are used. | Plan 08-01 register | 2026-10-11 |
| R-08-02 | T-08-03C | Content integrity receipts do not prove author identity; source claims are preserved verbatim. | Plan 08-03 register | 2026-10-11 |
| R-08-03 | T-08-08C | Reports expose scientific outcomes and allowlisted resource facts, without arbitrary environment dumps. | Plan 08-08 register | 2026-10-11 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-10-11 | 45 | 45 | 0 | Initial GSD security audit |
| 2026-10-11 | 71 | 71 | 0 | Gap-closure boundary and retained-evidence audit |

## Sign-Off

- [x] All 71 unique planned threats have a disposition and implementation or accepted-risk evidence.
- [x] All accepted risks are logged above.
- [x] No high or critical threat remains open; `threats_open: 0`.
- [x] The bounded gate retains `production_authorization: deny` while site ceilings are unknown.

**Approval:** verified 2026-10-11.
