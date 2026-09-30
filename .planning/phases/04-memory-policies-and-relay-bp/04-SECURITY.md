---
phase: "04"
slug: "memory-policies-and-relay-bp"
status: verified
threats_open: 0
asvs_level: 1
register_authored_at_plan_time: true
created: "2026-09-30"
---

# Phase 04 — Security

ASVS L1 audit of the 31 distinct threats authored in Phase 4 plans. The block threshold is high. The same T-04-SC source-authenticity threat appears in Plans 04-07 and 04-08 and is counted once. Every listed mitigation has implementation or recorded manual-gate evidence; no threat remains open.

## Trust Boundaries

| Boundary | Data crossing |
|---|---|
| Manifest and source claims into canonical execution | Policy kinds, order, parameters, version, artifact and source identity |
| Decoder-visible controller into independent evaluator | Candidate, syndrome and prior without hidden physical truth |
| Native source into isolated reference | Approved author tag, immutable commit/tree and observer patch |
| Engine and stage outputs into evidence readers | Events, work, sidecars, receipts, hashes and stage identity |
| Scheduler entitlement into pilot runner | Worker count and finite shot, work and runtime caps |

## Threat Register

| Threat | Category | Severity | Mitigation evidence | Status |
|---|---|---|---|---|
| T-04-01 | Tampering | high | Strict V4 model, finite/digest preflight and V2/V3 regression tests in `manifests.py`, `test_manifest.py`. | closed |
| T-04-02 | Information Disclosure | high | Truth-blind selection in `canonical/relay.py`; metamorphic tests in `test_truth_boundary.py`. | closed |
| T-04-03 | Denial of Service | medium | Hierarchical work reservation in `canonical/budgets.py`. | closed |
| T-04-04 | Tampering | high | Separate source equations and hand/endpoint fixtures in `canonical/memory.py`, `test_memory_policies.py`. | closed |
| T-04-05 | Repudiation | medium | Typed source, translation and discrepancy evidence in `manifests.py`, `canonical/contracts.py`. | closed |
| T-04-06 | Tampering | high | Closed kinds, IDs, owned state and target checks in `canonical/contracts.py`. | closed |
| T-04-07 | Repudiation | high | Graph/seed identity and persisted assignment evidence in `runner.py`, `canonical/relay.py`. | closed |
| T-04-08 | Denial of Service | medium | Reservation rollback and no-history-mutation test in `canonical/budgets.py`, `test_memory_composition.py`. | closed |
| T-04-09 | Tampering | high | Frozen V4 schema and pre-sampling rejection in `manifests.py`, `test_manifest.py`. | closed |
| T-04-10 | Repudiation | medium | Ordered bindings and composition digest in `canonical/contracts.py`. | closed |
| T-04-11 | Tampering | high | Frozen presets and ablation nonmutation in `canonical/relay.py`, `test_relay.py`. | closed |
| T-04-12 | Information Disclosure | high | Decoder-visible score and truth-change tests in `canonical/relay.py`, `test_truth_boundary.py`. | closed |
| T-04-13 | Denial of Service | medium | Finite leg/solution limits and nested budgets in `canonical/relay.py`, `canonical/budgets.py`. | closed |
| T-04-14 | Repudiation | high | Unique leaf work and independent lineage reconstruction in `canonical/budgets.py`, `canonical/verification.py`. | closed |
| T-04-15 | Tampering | high | Confined, hashed, byte-capped finite sidecars in `canonical/tracing.py`, `canonical/verification.py`. | closed |
| T-04-16 | Denial of Service | medium | Trace byte/record caps with truncation facts in `canonical/tracing.py`, `test_tracing.py`. | closed |
| T-04-17 | Tampering | high | Exact-base observer patch and bounded terminal equivalence in `native/relay_v022.py`, `qualify_relay_v022.py`. | closed |
| T-04-18 | Information Disclosure | medium | Decoder-visible native adapter and explicit unavailable fields in `native/relay_v022.py`. | closed |
| T-04-19 | Tampering | high | Independent artifact algebra and B1 fail-closed qualification in `qualify_phase4_artifacts.py`, `test_phase4_evidence.py`. | closed |
| T-04-20 | Tampering | high | Three-code matrix/resolution/preset identities and preflight in `manifests.py`, `test_phase4_evidence.py`. | closed |
| T-04-21 | Tampering | high | Full stage identity and mismatch rejection in `run_phase4_pilots.py`, `test_phase4_evidence.py`. | closed |
| T-04-22 | Repudiation | high | Common sample with separate native/canonical stage identities in `run_phase4_pilots.py`, `test_phase4_evidence.py`. | closed |
| T-04-23 | Denial of Service | medium | Closed stages, confined paths and finite caps in `run_phase4_pilots.py`. | closed |
| T-04-24 | Repudiation | high | Scheduler allocation and benchmark identity in `run_phase4_active_campaign.py`, `run_phase4_pilots.py`. | closed |
| T-04-25 | Denial of Service | high | One-worker entitlement and category caps in `run_phase4_pilots.py`. | closed |
| T-04-26 | Tampering | medium | Versioned amendments, distinct namespaces and terminal cap tests in `run_phase4_pilots.py`, `test_phase4_calibration_verification.py`. | closed |
| T-04-27 | Tampering | high | Frozen calibration surface and retained-attempt ledger audit in `run_phase4_pilots.py`, `verify_phase4_calibration.py`. | closed |
| T-04-28 | Repudiation | high | Deterministic selection and explicit inconclusive status in `run_phase4_pilots.py`, `test_phase4_evidence.py`. | closed |
| T-04-29 | Denial of Service | medium | Work/runtime caps and terminal audit in `run_phase4_pilots.py`, `verify_phase4_calibration.py`. | closed |
| T-04-36 | Repudiation | medium | Frozen presampling design, matched samples and amendment tests in `run_phase4_pilots.py`, `test_phase4_evidence.py`. | closed |
| T-04-SC | Tampering | high | Blocking author-pin approval in `04-07-SUMMARY.md`; immutable tag/commit/tree in `relay-v0.2.2-source.json`, `qualify_relay_v022.py` and `native/relay_v022.py`. | closed |

Paths in the table refer to `src/bp_registry/`, `scripts/`, `tests/canonical/`, `tests/`, `data/evidence/`, or this phase directory as applicable. The Plan 04-07 threat flag is the same T-04-SC and was carried into Plan 04-08.

## Accepted Risks Log

No accepted security risks. The full native `decode_144_12_12` test timed out and remains `inconclusive_timeout` in the source record. This is an explicit fidelity-coverage limit; it did not bypass the author-pin approval or source identity gate. The isolated exact-source build compiled all test targets and passed a bounded fixture.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-09-30 | 31 | 31 | 0 | GSD security auditor, ASVS L1 |

## Sign-Off

- [x] All threats have a disposition and implementation or manual-gate evidence.
- [x] No accepted security risk is hidden in the register.
- [x] `threats_open: 0` at the high threshold.
- [x] `status: verified` set.

**Approval:** verified 2026-09-30.
