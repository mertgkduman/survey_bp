---
phase: "10"
slug: "correlated-quaternary-execution"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-08"
---

# Phase 10 — Security

## Trust Boundaries

| Boundary | Control |
| --- | --- |
| Manifest and physical sample → canonical decoder | Closed policy registry, immutable problem identity, truth-hidden decoder input, finite work budgets. |
| Constructed splitter/map → canonical aSCED | Exact `H_ext` bytes and row origins, constructed receipt pair, `canonical_adaptation` labels, all-path work. |
| Approved external source/packages → disposable native reference | Exact source-spec SHA-256, user-attested collaborator-author verbal permission for bounded use, approved root/CMake/wheel/overlay hashes, algorithm guard, primary environment freeze. No formal repository license or written grant is claimed. |
| Native run and canonical ledger → Phase 10 evidence | Pinned native run receipt SHA-256, full native receipt chain, source-qualified missingness, deterministic 256-shot canonical replay. |

## Threat Register

The auditor verified all 58 planned mitigations at ASVS level 1. The 12 planned low-severity dependency risks are recorded below as accepted, closing the audit register. Repeated `T-10-SC` and `T-10-40` identifiers are disambiguated by plan number.

| Plan / Threat ID | Category | Component | Severity | Disposition | Mitigation and evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 10-01 / T-10-01 | Tampering | public manifest and Pauli artifact | high | mitigate | Strict frozen schema, finite/shape/enum checks, preflight before sampling, content and semantic hashes. Evidence: `manifests.py`, `sampling.py`, `execution.py`. | closed |
| 10-01 / T-10-02 | Information Disclosure | sampler/kernel boundary | high | mitigate | Distinct decoder-visible and hidden-truth types plus truth-sealing mutation tests. Evidence: `manifests.py`, `sampling.py`, `execution.py`. | closed |
| 10-01 / T-10-03 | Repudiation | ledger/replay | high | mitigate | Exact ordered event grammar, recomputed work/candidate/outcome identities, and tamper tests. Evidence: `manifests.py`, `sampling.py`, `execution.py`. | closed |
| 10-01 / T-10-04 | Denial of Service | bounded QBP tracer | medium | mitigate | Manifest iteration/work caps and reserve-before-mutation accounting. Evidence: `manifests.py`, `sampling.py`, `execution.py`. | closed |
| 10-01 / T-10-SC | Tampering | dependency supply chain | low | accept | This plan installs no package and uses the existing pinned canonical environment. Evidence: `manifests.py`, `sampling.py`, `execution.py`. | closed |
| 10-02 / T-10-05 | Tampering | Pauli artifact/compiler | high | mitigate | Strict value/shape/algebra checks, owned read-only arrays, row-role hashes, CSS round-trip tests. Evidence: `algebra.py`, `problems.py`. | closed |
| 10-02 / T-10-06 | Repudiation | semantic identity | high | mitigate | Canonical bytes include order, labels, optional-basis status, source identity, and transform witnesses. Evidence: `algebra.py`, `problems.py`. | closed |
| 10-02 / T-10-07 | Elevation of Privilege | working transform | medium | mitigate | Only identity or certified transform/lift edges can create working problems. Evidence: `algebra.py`, `problems.py`. | closed |
| 10-02 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `algebra.py`, `problems.py`. | closed |
| 10-03 / T-10-08 | Tampering | candidate/outcome classification | high | mitigate | Recompute original syndrome and spans in evaluator-owned code; reject malformed candidate shape/encoding. Evidence: `evaluator.py`. | closed |
| 10-03 / T-10-09 | Information Disclosure | evaluator boundary | high | mitigate | Evaluator is called only after candidate freeze; policy APIs omit evaluation and truth fields. Evidence: `evaluator.py`. | closed |
| 10-03 / T-10-10 | Repudiation | logical-action missingness | medium | mitigate | Typed observed/unavailable status with reason is included in terminal evidence. Evidence: `evaluator.py`. | closed |
| 10-03 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `evaluator.py`. | closed |
| 10-04 / T-10-11 | Tampering | probability tables | high | mitigate | Strict shape/finiteness/range/sum checks, no silent normalization, immutable persisted rows. Evidence: `sampling.py`. | closed |
| 10-04 / T-10-12 | Information Disclosure | shot sample | high | mitigate | Separate hidden truth and observation types; truth-sealing tests. Evidence: `sampling.py`. | closed |
| 10-04 / T-10-13 | Repudiation | seed/channel identity | medium | mitigate | Domain-separated seed, resolved-table hash, precision/tie convention, and replay checks. Evidence: `sampling.py`. | closed |
| 10-04 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `sampling.py`. | closed |
| 10-05 / T-10-14 | Tampering | numerical inputs/state | high | mitigate | Finite shape/profile checks, immutable inputs, deterministic ordered reductions, terminal numerical failures. Evidence: `numerics.py`, `kernel.py`. | closed |
| 10-05 / T-10-15 | Information Disclosure | kernel API | high | mitigate | Kernel signatures omit hidden truth and tests hold decoder inputs fixed while truth varies. Evidence: `numerics.py`, `kernel.py`. | closed |
| 10-05 / T-10-16 | Denial of Service | iterations/work | medium | mitigate | Typed bounded iterations, reserve-before-mutation work caps, retained capped terminal. Evidence: `numerics.py`, `kernel.py`. | closed |
| 10-05 / T-10-SC | Tampering | dependency supply chain | low | accept | Existing pinned NumPy is reused; no install occurs. Evidence: `numerics.py`, `kernel.py`. | closed |
| 10-06 / T-10-17 | Tampering | schedule freshness/order | high | mitigate | Closed classes, stable edge/node identities, snapshot assertions, exact evidence. Evidence: `schedules.py`. | closed |
| 10-06 / T-10-18 | Tampering | normalization/offset parameters | medium | mitigate | Strict finite positive validation and operand-scoped direct tests. Evidence: `schedules.py`. | closed |
| 10-06 / T-10-19 | Denial of Service | schedule work | medium | mitigate | Unit counts, reserve-before-step budgets, bounded iterations. Evidence: `schedules.py`. | closed |
| 10-06 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `schedules.py`. | closed |
| 10-07 / T-10-20 | Spoofing | source/adaptation identity | high | mitigate | Closed registry, pinned source fields, explicit combination classification, replayed procedure basis. Evidence: `compatibility.py`, `contracts.py`, `runner.py`. | closed |
| 10-07 / T-10-21 | Tampering | manifest/composition | high | mitigate | Strict extra-forbid schema, pre-artifact resolution, content/semantic hashes. Evidence: `compatibility.py`, `contracts.py`, `runner.py`. | closed |
| 10-07 / T-10-22 | Information Disclosure | policy/evaluator boundary | high | mitigate | Decoder-visible capability views omit truth and evaluator fields; mutation tests. Evidence: `compatibility.py`, `contracts.py`, `runner.py`. | closed |
| 10-07 / T-10-23 | Repudiation | ledger/replay | high | mitigate | Exact event grammar, unique-leaf work reconstruction, terminal digest and tamper suite. Evidence: `compatibility.py`, `contracts.py`, `runner.py`. | closed |
| 10-07 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `compatibility.py`, `contracts.py`, `runner.py`. | closed |
| 10-08 / T-10-24 | Tampering | fixation transition | high | mitigate | Typed propose/reserve/commit, raw and resolved weights, stable IDs, independent replay. Evidence: `qbpgd.py`. | closed |
| 10-08 / T-10-25 | Information Disclosure | reliability/selection | high | mitigate | Controller accepts only marginals, observations, eligibility, and budgets; truth mutation tests. Evidence: `qbpgd.py`. | closed |
| 10-08 / T-10-26 | Spoofing | source fidelity | high | mitigate | Separate source-component IDs and run-level canonical-adaptation label, with unresolved author-code status retained. Evidence: `qbpgd.py`. | closed |
| 10-08 / T-10-27 | Denial of Service | rounds/iterations | medium | mitigate | Exactly T per round, at most n rounds, typed work caps. Evidence: `qbpgd.py`. | closed |
| 10-08 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `qbpgd.py`. | closed |
| 10-09 / T-10-28 | Tampering | recurrence/alpha | high | mitigate | Direct equation tests, strict alpha validation, persisted recurrence identity, replay. Evidence: `mbp4.py`. | closed |
| 10-09 / T-10-29 | Spoofing | source versus adaptive/binary identity | high | mitigate | Closed fixed-alpha kind, explicit AMBP4/binary rejection, combination classification. Evidence: `mbp4.py`. | closed |
| 10-09 / T-10-30 | Denial of Service | MBP4 iterations | medium | mitigate | Existing iteration/work caps and reserve-before-mutation leaves. Evidence: `mbp4.py`. | closed |
| 10-09 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `mbp4.py`. | closed |
| 10-10 / T-10-31 | Tampering | splitter rows/search/qualification witnesses | high | mitigate | Deterministic bounded construction, independent rank/detectability/type/weight/cycle checks, receipt binding, and semantic hashes. Evidence: `asced.py`. | closed |
| 10-10 / T-10-32 | Spoofing | CSS/canonical-fixture fidelity | high | mitigate | Explicit CSS gate, separated component/run fidelity, exact input-H digest, typed constructed receipt, immutable T/H_ext, and non-CSS rejection. Evidence: `asced.py`. | closed |
| 10-10 / T-10-33 | Denial of Service | path cardinality | medium | mitigate | Preflight computes L*2^Delta and rejects over-cap manifests before sampling. Evidence: `asced.py`. | closed |
| 10-10 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `asced.py`. | closed |
| 10-11 / T-10-34 | Tampering | overcomplete matrices/constructed binding | high | mitigate | Exact constructed H_ext digest equality, deterministic bounded M witnesses, GF(2) equations, shape/rank/order validation, bound content hashes, and tamper tests. Evidence: `asced_overcomplete.py`, `asced.py`. | closed |
| 10-11 / T-10-35 | Repudiation | derived syndrome lineage | high | mitigate | Persist original/extended/overcomplete identities and M mapping for replay. Evidence: `asced_overcomplete.py`, `asced.py`. | closed |
| 10-11 / T-10-40 | Spoofing | source comparison map | high | mitigate | Bind each source M/H_oc only to its own pinned H_ext and reject it from the canonical map receipt and runtime. Evidence: `asced_overcomplete.py`, `asced.py`. | closed |
| 10-11 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `asced_overcomplete.py`, `asced.py`. | closed |
| 10-12 / T-10-36 | Tampering | virtual paths/validity | high | mitigate | Exact cardinality/order, certified graph/syndrome maps, dual independent validity, replay. Evidence: `asced.py`, `run_phase10_quaternary_gate.py`. | closed |
| 10-12 / T-10-37 | Information Disclosure | candidate selection | high | mitigate | Selection receives only decoder-visible path results; truth-sealing and completion-order tests. Evidence: `asced.py`, `run_phase10_quaternary_gate.py`. | closed |
| 10-12 / T-10-38 | Repudiation | all-path work/selection | high | mitigate | Unique path leaves, complete origin freeze, recomputed pool/tie/terminal. Evidence: `asced.py`, `run_phase10_quaternary_gate.py`. | closed |
| 10-12 / T-10-39 | Denial of Service | path explosion | high | mitigate | Preflight path cardinality/cap before sampling and per-path/ensemble work caps. Evidence: `asced.py`, `run_phase10_quaternary_gate.py`. | closed |
| 10-12 / T-10-SC | Tampering | dependency supply chain | low | accept | No package install occurs in this plan. Evidence: `asced.py`, `run_phase10_quaternary_gate.py`. | closed |
| 10-13 / T-10-40 | Spoofing | native repository/package/CMake publishers | high | mitigate | Official URLs, exact commit/versions/artifacts, hashes, allowed executable identity, and human review. Evidence: `qualify_phase10_native_asced.py`. | closed |
| 10-13 / T-10-41 | Tampering | overlay/driver scope | high | mitigate | Algorithm-file digest allowlist and out-of-tree build-only changes. Evidence: `qualify_phase10_native_asced.py`. | closed |
| 10-13 / T-10-42 | Repudiation | license/discrepancy record | medium | mitigate | Explicit unresolved facts and immutable proposal status; no inferred license conclusion. Evidence: `qualify_phase10_native_asced.py`. | closed |
| 10-13 / T-10-SC | Tampering | pip packages, pybind11 overlay, and CMake tool | high | mitigate | All five packages, overlay, and exact CMake bytes remain inert until blocking Plan 10-14 human approval. Evidence: `qualify_phase10_native_asced.py`. | closed |
| 10-14 / T-10-43 | Spoofing | publisher/package/source identity | high | mitigate | Human verifies official pages and exact digest-bound proposal. Evidence: `qualify_phase10_native_asced.py`, `10-14-SUMMARY.md`. | closed |
| 10-14 / T-10-44 | Tampering | approval/build handoff | high | mitigate | Summary binds decision to source-spec SHA-256 and exact five-package/overlay/CMake artifact and executable hashes. Evidence: `qualify_phase10_native_asced.py`, `10-14-SUMMARY.md`. | closed |
| 10-14 / T-10-45 | Repudiation | license/use decision | medium | mitigate | Record evidence, unresolved facts, decision, reviewer signal, and bounded scope. Evidence: `qualify_phase10_native_asced.py`, `10-14-SUMMARY.md`. | closed |
| 10-14 / T-10-SC | Tampering | pip packages, pybind11 overlay, and CMake tool | high | mitigate | Blocking-human gate covers every `[SUS]` package plus exact overlay/CMake bytes and executable identity; auto-advance cannot bypass it. Evidence: `qualify_phase10_native_asced.py`, `10-14-SUMMARY.md`. | closed |
| 10-15 / T-10-46 | Tampering | native source/build/CMake | high | mitigate | Approval precondition, exact five-package/overlay/CMake artifact and executable hashes, disposable prefix, algorithm before/after guard, receipts. Evidence: `qualify_phase10_native_asced.py`, `native_asced.py`. | closed |
| 10-15 / T-10-47 | Spoofing | native/canonical identity | high | mitigate | Distinct typed identity/result, tested Pauli translation, no canonical fallback. Evidence: `qualify_phase10_native_asced.py`, `native_asced.py`. | closed |
| 10-15 / T-10-48 | Repudiation | native missingness/failure | high | mitigate | Retained stdout/stderr/commands/digests and observed/unavailable metric facts. Evidence: `qualify_phase10_native_asced.py`, `native_asced.py`. | closed |
| 10-15 / T-10-49 | Denial of Service | native build/run | medium | mitigate | Bounded build command, aggregate trial cap, timeout, typed failure. Evidence: `qualify_phase10_native_asced.py`, `native_asced.py`. | closed |
| 10-15 / T-10-SC | Tampering | pip packages, pybind11 overlay, and CMake tool | high | mitigate | Install/invoke only exact human-approved artifacts and the allowed CMake executable path/digest in the disposable environment. Evidence: `qualify_phase10_native_asced.py`, `native_asced.py`. | closed |
| 10-16 / T-10-50 | Tampering | study/sample/arm/fixture-map identity | high | mitigate | Pre-run design digest, exact constructed splitter/full-H_ext/map receipt pair, shared sample hashes, immutable output, and cardinality checks. Evidence: `run_phase10_quaternary_gate.py`, `native_asced.py`. | closed |
| 10-16 / T-10-51 | Repudiation | path/work/outcome evidence | high | mitigate | Independent ledger reconstruction and all-terminal unique-leaf accounting. Evidence: `run_phase10_quaternary_gate.py`, `native_asced.py`. | closed |
| 10-16 / T-10-52 | Spoofing | native matched evidence | high | mitigate | Independently verified exact commit/source/build/CMake/native_success receipt and explicit unavailable shot/counter facts. Evidence: `run_phase10_quaternary_gate.py`, `native_asced.py`. | closed |
| 10-16 / T-10-53 | Denial of Service | bounded gate | medium | mitigate | Exactly 256 samples, four paths per aSCED arm, 25/12 iteration caps, fixed work/path caps, and run-once refusal. Evidence: `run_phase10_quaternary_gate.py`, `native_asced.py`. | closed |
| 10-16 / T-10-SC | Tampering | dependency supply chain | medium | mitigate | Canonical environment remains pinned; native execution consumes only Plan 10-15's verified receipt. Evidence: `run_phase10_quaternary_gate.py`, `native_asced.py`. | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Acceptance basis | Date |
| --- | --- | --- | --- | --- |
| P10-01-SC | 10-01 / T-10-SC | This plan installs no package and uses the existing pinned canonical environment. Residual use of the existing pinned canonical environment is low severity. | Plan 10-01 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-02-SC | 10-02 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-02 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-03-SC | 10-03 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-03 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-04-SC | 10-04 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-04 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-05-SC | 10-05 / T-10-SC | Existing pinned NumPy is reused; no install occurs. Residual use of the existing pinned canonical environment is low severity. | Plan 10-05 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-06-SC | 10-06 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-06 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-07-SC | 10-07 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-07 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-08-SC | 10-08 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-08 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-09-SC | 10-09 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-09 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-10-SC | 10-10 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-10 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-11-SC | 10-11 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-11 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |
| P10-12-SC | 10-12 / T-10-SC | No package install occurs in this plan. Residual use of the existing pinned canonical environment is low severity. | Plan 10-12 `accept` disposition under the approved Phase 10 execution workflow. | 2026-10-08 |

## Security Audit Trail

| Audit Date | Threats Total | Mitigations Verified | Planned Low Risks Documented | Blocking Open | Run By |
| --- | ---: | ---: | ---: | ---: | --- |
| 2026-10-08 | 70 | 58 | 12 | 0 | `gsd-security-auditor`, ASVS L1 |

## Sign-Off

- [x] All planned threats have a disposition.
- [x] Planned accepted risks are documented.
- [x] `threats_open: 0` at the configured high-severity threshold.
- [x] `status: verified`.

**Approval:** Verified 2026-10-08. Full decoder replay remains a separate Phase 10 evidence gate.
