---
phase: "1"
slug: "evidence-registry-and-native-css-baseline"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-22"
---

# Phase 1 — Security

## Trust Boundaries

| Boundary | Data crossing | Control |
|---|---|---|
| Approved package source to local environment | Python distributions and native decoder dependency | Exact-version human approval and environment identity record |
| External paper/code to evidence registry | Claims, source revisions, extraction artifacts | Pinned revisions, anchors, hashes, and registry cross-references |
| Manifest/artifact to simulation | Parameters, matrix paths, and numerical arrays | Strict schema, bounded resources, root confinement, raw and semantic hashes |
| Sampler to decoder | Syndrome observation | Separate evaluator truth and decoder-visible observation |
| Simulation to durable ledger | Shot attempts, events, and outcomes | Typed records, locks, fsync, reload validation, and reconciliation |
| Ledger to CLI result | Counts, labels, and provenance | Recomputed counts, source link checks, and maturity restrictions |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation evidence | Status |
|---|---|---|---|---|---|---|
| T-01-SC | Tampering | Package supply chain | high | mitigate | `01-02-SUMMARY.md`; `docs/environment-pins.md` | closed |
| T-01-01 | Repudiation | Native probe | medium | mitigate | `docs/environment-pins.md` | closed |
| T-01-02 | Tampering | Manifest preflight | high | mitigate | `src/bp_registry/manifests.py`; `src/bp_registry/runner.py` | closed |
| T-01-03 | Information disclosure | Decoder boundary | medium | mitigate | `src/bp_registry/reference.py`; `src/bp_registry/runner.py` | closed |
| T-01-04 | Repudiation | Ledger | medium | mitigate | `src/bp_registry/runner.py`; `src/bp_registry/ledger.py` | closed |
| T-01-05 | Information disclosure | Artifact resolver | high | mitigate | `src/bp_registry/artifacts.py` | closed |
| T-01-06 | Tampering | CSS artifact | high | mitigate | `src/bp_registry/artifacts.py`; `src/bp_registry/manifests.py` | closed |
| T-01-07 | Denial of service | Matrix loading | medium | mitigate | `src/bp_registry/artifacts.py` | closed |
| T-01-08 | Information disclosure | Sample truth | medium | mitigate | `src/bp_registry/sampling.py`; `src/bp_registry/runner.py` | closed |
| T-01-09 | Tampering | JSONL journal | high | mitigate | `src/bp_registry/ledger.py` | closed |
| T-01-10 | Repudiation | Unsuccessful shots | high | mitigate | `src/bp_registry/runner.py`; `src/bp_registry/ledger.py` | closed |
| T-01-11 | Denial of service | Concurrent writers | medium | mitigate | `src/bp_registry/ledger.py` | closed |
| T-01-12 | Tampering | Source claims | high | mitigate | `src/bp_registry/evidence.py`; `tests/test_evidence.py` | closed |
| T-01-13 | Repudiation | Screening decisions | medium | mitigate | `src/bp_registry/evidence.py` | closed |
| T-01-14 | Tampering | Concurrent import | medium | mitigate | `src/bp_registry/evidence.py` | closed |
| T-01-15 | Tampering | Manifest fields | high | mitigate | `src/bp_registry/manifests.py` | closed |
| T-01-16 | Information disclosure | Artifact path | high | mitigate | `src/bp_registry/runner.py`; `tests/test_manifest.py` | closed |
| T-01-17 | Denial of service | Budget fields | medium | mitigate | `src/bp_registry/manifests.py`; `src/bp_registry/runner.py` | closed |
| T-01-18 | Tampering | Source checkout | high | mitigate | `tools/freeze_css_source.py` | closed |
| T-01-19 | Repudiation | Candidate choice | medium | mitigate | `docs/phase1-source-decisions.md`; `tests/test_source_artifact.py` | closed |
| T-01-20 | Denial of service | CLI pilot | medium | mitigate | `src/bp_registry/cli.py`; `src/bp_registry/runner.py` | closed |
| T-01-21 | Tampering | Result summary | high | mitigate | `src/bp_registry/cli.py` | closed |
| T-01-22 | Repudiation | Evidence maturity | high | mitigate | `src/bp_registry/manifests.py`; `src/bp_registry/cli.py` | closed |
| T-01-23 | Tampering | Reconciliation | high | mitigate | `src/bp_registry/ledger.py` | closed |

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-09-22 | 24 | 23 | 1 | `gsd-security-auditor`, initial audit |
| 2026-09-22 | 24 | 24 | 0 | `gsd-security-auditor`, after T-01-12 fix |

The final audit checked the registered threat controls against code and tests. The full suite passed 68 tests; public preflight, evidence validation, and run verification passed. The audit found no unregistered threat flags in the phase summaries. T-01-12 was closed by commits `50261cc` and `08d4ce7`, which reject claims naming an unknown work or a revision other than that work's pinned revision.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks documented.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-22.
