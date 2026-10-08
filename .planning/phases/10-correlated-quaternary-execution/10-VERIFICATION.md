---
phase: 10-correlated-quaternary-execution
verified: 2026-10-08T09:12:00Z
status: passed
score: 8/8 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/phases/10-correlated-quaternary-execution/10-01-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-01-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-02-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-02-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-03-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-03-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-04-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-04-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-05-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-05-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-06-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-06-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-07-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-07-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-08-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-08-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-09-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-09-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-10-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-10-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-11-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-11-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-12-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-12-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-13-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-13-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-14-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-14-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-15-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-15-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-16-PLAN.md
  - .planning/phases/10-correlated-quaternary-execution/10-16-SUMMARY.md
  - .planning/phases/10-correlated-quaternary-execution/10-CONTEXT.md
  - .planning/phases/10-correlated-quaternary-execution/10-EXECUTION-DECISIONS.md
  - .planning/phases/10-correlated-quaternary-execution/10-REVIEW-FIX.md
  - .planning/phases/10-correlated-quaternary-execution/10-REVIEW.md
  - .planning/phases/10-correlated-quaternary-execution/10-SECURITY.md
  - .planning/phases/10-correlated-quaternary-execution/10-VALIDATION.md
  - AGENTS.md
  - data/fixtures/quaternary/asced-gb46-canonical-fixture.json
  - data/fixtures/quaternary/asced-gb46-canonical-overcomplete-map.json
  - data/manifests/quaternary-five-qubit-tracer.json
  - data/manifests/quaternary-gb46-asced.json
  - data/manifests/quaternary-gb46-bp4.json
  - data/native/phase10-asced-build-receipt.json
  - data/native/phase10-asced-run-receipt.json
  - data/native/phase10-asced-source-spec.json
  - data/results/phase10-quaternary-b1-gate/canonical-ledger.jsonl
  - data/results/phase10-quaternary-b1-gate/replay-verification.json
  - data/results/phase10-quaternary-b1-gate/study-receipt.json
  - data/studies/phase10-quaternary-b1-gate.json
  - scripts/qualify_phase10_native_asced.py
  - scripts/run_phase10_quaternary_gate.py
  - src/bp_registry/manifests.py
  - src/bp_registry/quaternary/__init__.py
  - src/bp_registry/quaternary/algebra.py
  - src/bp_registry/quaternary/asced.py
  - src/bp_registry/quaternary/asced_overcomplete.py
  - src/bp_registry/quaternary/compatibility.py
  - src/bp_registry/quaternary/contracts.py
  - src/bp_registry/quaternary/evaluator.py
  - src/bp_registry/quaternary/execution.py
  - src/bp_registry/quaternary/kernel.py
  - src/bp_registry/quaternary/mbp4.py
  - src/bp_registry/quaternary/native_asced.py
  - src/bp_registry/quaternary/numerics.py
  - src/bp_registry/quaternary/problems.py
  - src/bp_registry/quaternary/qbpgd.py
  - src/bp_registry/quaternary/sampling.py
  - src/bp_registry/quaternary/schedules.py
  - src/bp_registry/runner.py
  - tests/canonical/quaternary/__init__.py
  - tests/canonical/quaternary/conftest.py
  - tests/canonical/quaternary/fixtures/asced-overcomplete.json
  - tests/canonical/quaternary/fixtures/asced-splitters.json
  - tests/canonical/quaternary/test_algebra.py
  - tests/canonical/quaternary/test_asced_ensemble.py
  - tests/canonical/quaternary/test_asced_evidence.py
  - tests/canonical/quaternary/test_asced_overcomplete.py
  - tests/canonical/quaternary/test_asced_splitters.py
  - tests/canonical/quaternary/test_bpgd.py
  - tests/canonical/quaternary/test_evaluator.py
  - tests/canonical/quaternary/test_kernel.py
  - tests/canonical/quaternary/test_mbp4.py
  - tests/canonical/quaternary/test_public_execution.py
  - tests/canonical/quaternary/test_sampling.py
  - tests/canonical/quaternary/test_schedules.py
  - tests/canonical/quaternary/test_vector_oracle.py
covered_digest: "v1:sha256:dfa0ed3d28bbba8a70cc8eb84b8cdaeffcad86fc5a16a5a0e23b01a820d245dd"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 7/8
  gaps_closed:
    - "The complete 256-shot post-review decoder replay exited 0 and byte-matched the retained ledger and study receipt."
  gaps_remaining: []
  regressions: []
---

# Phase 10: Correlated Quaternary Execution Verification Report

**Phase Goal:** As a researcher, I want to decode joint Pauli errors through a canonical quaternary BP kernel, so that correlation semantics and policy compatibility are verified.
**Verified:** 2026-10-08T09:12:00Z
**Status:** passed
**Re-verification:** Yes — after the complete 256-shot decoder replay closed the prior behavior-verification item.

## User Flow Coverage

| Step | User action | Expected | Codebase evidence | Status |
| --- | --- | --- | --- | --- |
| 1 | Supply a strict joint-Pauli manifest and preflight it. | The public facade validates the I/X/Y/Z channel, immutable problem, numeric profile, budgets, and closed policy composition before sampling. | `QuaternaryExperimentV2`, `preflight_quaternary`, and `resolve_quaternary_composition`; public preflight/rejection tests pass. | ✓ VERIFIED |
| 2 | Decode the observed syndrome with the canonical four-state kernel. | The kernel uses source-defined commutation factors, scalar check messages, three identity-referenced LLRs, four-state beliefs, declared ties/saturation, and no hidden truth. | `algebra.py`, `numerics.py`, `kernel.py`; independent vector/exact-posterior named test passed. | ✓ VERIFIED |
| 3 | Inspect joint channel and outcome semantics. | One categorical I/X/Y/Z draw preserves Y and X/Z correlation; the independent evaluator reports invalid, exact, stabilizer-equivalent, or logical failure in original space. | `sampling.py`, `evaluator.py`; correlation/Y and exhaustive CSS evaluator-parity named tests passed. | ✓ VERIFIED |
| 4 | Select a compatible policy composition. | Source-backed flooding/serial/scalar-transform compositions execute; Q-BPGD, fixed-alpha MBP4, and CSS aSCED are traceable; unsupported binary, AMBP4, and non-CSS aSCED ports fail closed. | `compatibility.py`, `schedules.py`, `qbpgd.py`, `mbp4.py`, `asced.py`; public schedule/Q-BPGD/aSCED named tests passed. | ✓ VERIFIED |
| 5 | Replay evidence and inspect fidelity labels. | Public one-shot runs replay deterministically; source components remain distinct from run fidelity; project-generated GB46 T/H_ext and M/H_oc remain `canonical_adaptation`. | Public replay tests pass; fixture, manifest, and receipt digest chains agree; exact native receipt is separately pinned. | ✓ VERIFIED |
| 6 | Verify the retained bounded mechanism study. | All 2,816 retained events reproduce byte-for-byte from the complete frozen 256-shot execution. | The persisted replay receipt binds the exact runner, study, native receipt, ledger, and study-receipt hashes; exit 0 reported 768 terminals, 2,048 paths, 160 native trials, 10 native logical errors, and `verified: true`. | ✓ VERIFIED |

The complete researcher flow is implemented and exercised for kernel, correlation, evaluator, compatibility, public replay, and the full retained mechanism study.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | A researcher can invoke an installed public manifest path to preflight, execute, and replay a non-CSS joint-Pauli decode. | ✓ VERIFIED | `runner.py` dispatches V1/V2 quaternary manifests; public installed-path and full-manifest replay tests are collected and passed in the reported 169-test focused suite. |
| 2 | The canonical kernel owns source-defined four-state Pauli algebra, commutation factors, numerical conventions, joint X/Z inference, and a truth-sealed lifecycle. | ✓ VERIFIED | Substantive code in `algebra.py:16,64`, `numerics.py:23`, `kernel.py:105,168`; independent tree/vector/exact posterior test passed in 0.90s. |
| 3 | Joint I/X/Y/Z channel sampling preserves Y effects and correlated X/Z semantics without silently changing physical probabilities. | ✓ VERIFIED | `JointPauliChannel` and immutable shot types in `sampling.py`; named single-Y and covariance tests passed, 2 tests in 0.54s. |
| 4 | Quaternary candidates are independently classified in original problem space with CSS-compatible outcome meanings. | ✓ VERIFIED | Evaluator has local symplectic/GF(2) logic and no production algebra import; exhaustive CSS parity named test passed in 3.40s. |
| 5 | The compatibility boundary executes supported kernel/schedule/transform compositions and rejects unsupported ports before sampling. | ✓ VERIFIED | Closed contracts and resolver are wired through public preflight/run; scalar serial plus normalization public test passed. |
| 6 | Q-BPGD and fixed-alpha MBP4 execute as traceable quaternary policies with honest component/run fidelity and deterministic reconstruction. | ✓ VERIFIED | Persistent Q-BPGD, literal fixation, continued-message adaptation, fixed-alpha recurrence, budgets, and replay are implemented and covered by focused tests; public Q-BPGD fidelity/replay test passed. |
| 7 | CSS aSCED executes every ordinary/overcomplete path with exact constructed receipt binding, original-space selection, separate exact native evidence, and `canonical_adaptation` labeling. | ✓ VERIFIED | All-path controller and map/splitter digest chain are wired; public all-path replay test passed. Native build/run receipt is content-pinned at the Phase 10 boundary and records 160 trials/10 logical errors without claiming shared shots. |
| 8 | The retained 256-shot Phase 10 ledger and study receipt reproduce byte-for-byte through the complete post-review decoder replay. | ✓ VERIFIED | `replay-verification.json` records exit 0 and `verified: true` after the fail-closed implementation at `run_phase10_quaternary_gate.py:232-353` regenerated and byte-compared the complete ledger and receipt. All receipt-bound hashes match current artifacts. |

**Score:** 8/8 truths verified (0 behavior-unverified)

## Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/bp_registry/quaternary/algebra.py`, `problems.py` | Immutable Pauli semantics and original/working problem lineage | ✓ VERIFIED | Explicit I/X/Y/Z encoding, commutation, multiplication, syndrome, CSS compilation, hashes, and certified transform/lift boundaries. |
| `src/bp_registry/quaternary/numerics.py`, `kernel.py` | Canonical scalar-LLR BP4 engine | ✓ VERIFIED | Stable float64 profile, scalar C2V/three-LLR V2C, four-state marginals, immutable snapshots, work caps, and original-syndrome convergence. |
| `src/bp_registry/quaternary/sampling.py` | Joint Pauli channel and replayable sampler | ✓ VERIFIED | Strict probability validation, one categorical draw/qubit, separate smoothing identity, domain-separated replay identity. |
| `src/bp_registry/quaternary/evaluator.py` | Independent original-space outcome authority | ✓ VERIFIED | Local algebra/span implementation, complete outcome order, typed logical-action availability. |
| `src/bp_registry/quaternary/contracts.py`, `compatibility.py`, `schedules.py` | Closed policy surface and compatibility evidence | ✓ VERIFIED | Complete policy ownership, source/equation/lifecycle identity, supported schedule/transform execution, explicit rejections. |
| `src/bp_registry/quaternary/qbpgd.py`, `mbp4.py` | Published quaternary policies | ✓ VERIFIED | Persistent Q-BPGD and fixed-alpha MBP4 are substantive, budgeted, reconstructable, and publicly dispatched. |
| `src/bp_registry/quaternary/asced.py`, `asced_overcomplete.py` | Qualified CSS aSCED execution | ✓ VERIFIED | Deterministic splitter/map construction, all-path controller, original-space selection, exact receipt pair. |
| `src/bp_registry/manifests.py`, `runner.py` | Public manifest/preflight/run/replay wiring | ✓ VERIFIED | Strict V2 schema and actual dispatch to scalar, Q-BPGD, MBP4, and aSCED engines. |
| `data/fixtures/quaternary/asced-gb46-canonical-*.json` | Immutable constructed GB46 receipts | ✓ VERIFIED | Pinned input H digest `4bd60b...`, common H_ext digest `2a50c3...`, splitter receipt `d28362...`, map receipt `9f4026...`; labeled `canonical_adaptation`. |
| `data/native/phase10-asced-*-receipt.json` | Exact isolated native reference evidence | ✓ VERIFIED | Exact retained run receipt is separately content-pinned; aggregate says 160 trials and 10 logical errors. Verbal collaborator-author permission is accurately recorded without a written-grant or formal-license claim. |
| `data/results/phase10-quaternary-b1-gate/*` | Retained bounded mechanism evidence | ✓ VERIFIED | Ledger has 2,816 lines and its receipt declares 768 terminals plus 2,048 paths. Replay receipt SHA-256 `7cb93c...` records full decoder regeneration, byte equality, exit 0, and the expected result counts. |

All 16 `verify.artifacts` plan queries returned valid. No required artifact is missing or a stub.

## Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| Joint channel | immutable original problem | observed syndrome and decoder priors only | ✓ WIRED | Hidden Pauli truth is absent from kernel/controller signatures and supplied only to post-freeze evaluation. |
| Scalar kernel | flooding/serial schedules and C2V transforms | typed sessions, edge tables, freshness/commit rules | ✓ WIRED | Public serial plus normalization execution test passed. |
| Manifest resolver | runner dispatch | resolved closed composition before sampling | ✓ WIRED | Scalar, Q-BPGD, MBP4, ordinary aSCED, and overcomplete aSCED branches execute real engines. |
| Candidate | independent evaluator | frozen candidate plus separately supplied sealed truth | ✓ WIRED | Original syndrome and logical residuals are recomputed outside kernel code. |
| Pinned GB46 H | canonical splitter fixture | exact raw SHA-256 feeding deterministic construction | ✓ WIRED | Automated query treated the external source identifier as a missing relative file; manual inspection found the digest in code and `source_input.raw_sha256`. |
| Splitter fixture | overcomplete map fixture | common H_ext plus exact splitter/map receipt pair | ✓ WIRED | Automated query searched class-name spellings; actual lowercase JSON keys bind `constructed_splitter_receipt_sha256`, `h_ext_sha256`, and map `receipt_sha256`. Tests enforce equality. |
| Retained ledger | full decoder regeneration | `verify --replay` temp output and byte comparison | ✓ WIRED | The replay receipt binds runner SHA-256 `644035...`, records exit 0, and reports `verified: true`; the retained ledger remains SHA-256 `feab6c...`. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
| --- | --- | --- | --- | --- |
| Sampler | hidden Pauli vector, observed syndrome, decoder prior | validated manifest channel plus domain-separated seed/shot | Yes | ✓ FLOWING |
| BP4 kernel | C2V/V2C buffers, beliefs, marginals, candidate | immutable observed problem and decoder priors | Yes | ✓ FLOWING |
| Policy controllers | rounds/sweeps/paths/work/candidate | kernel snapshots, public policy config, typed budgets | Yes | ✓ FLOWING |
| Evaluator | outcome and logical action | frozen candidate, original code/syndrome, sealed truth after decoding | Yes | ✓ FLOWING |
| Public ledger | preflight, schedule/policy events, terminal | executed composition and evaluator result | Yes | ✓ FLOWING |
| Retained study ledger | 768 arm terminals and 2,048 path terminals | frozen 256-shot study run plus complete deterministic replay | Yes | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Canonical kernel agrees with independent vector and exact posterior oracles | `pytest -q ...test_kernel_tree_sweep_matches_independent_vector_and_exact_posteriors` | 1 passed in 0.90s | ✓ PASS |
| Y and correlated X/Z semantics survive joint sampling | two named `test_sampling.py` tests | 2 passed in 0.54s | ✓ PASS |
| Independent quaternary evaluator agrees with established CSS evaluator exhaustively | named CSS parity test | 1 passed in 3.40s | ✓ PASS |
| Public scalar transform, Q-BPGD fidelity, and all-path CSS aSCED execute and replay | three named `test_public_execution.py` tests | 3 passed in 1.88s | ✓ PASS |
| Focused Phase 10 regression suite | Executor/review evidence: `pytest -q tests/canonical/quaternary -x` | 169 passed | ✓ PASS (retained evidence) |
| Full post-review workspace suite | Executor/review evidence | 1030 passed, 1 skipped, 6 warnings in 1091.57s | ✓ PASS (retained evidence) |

## Probe Execution

| Probe | Command | Result | Status |
| --- | --- | --- | --- |
| Conventional `probe-*.sh` scripts | Discovery under `scripts/` and phase plans | None declared | N/A |
| Complete retained decoder replay | `scripts/run_phase10_quaternary_gate.py verify ... --replay` | Exit 0; `verified: true`; 768 canonical terminals, 2,048 aSCED paths, native 160 trials/10 logical errors; regenerated files byte-matched retained files | ✓ PASS |

## Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| QBP-01 | 01,02,05,06,07,09 | Canonical four-state Pauli BP with declared commutation, messages, numerics, joint inference | ✓ SATISFIED | Source kernel/numerics/schedules are substantive and wired; independent exact-posterior test passed. |
| QBP-02 | 01,04,07 | Declared joint I/X/Y/Z channel with correlated X/Z, priors, rates, and Y fixtures | ✓ SATISFIED | Strict joint channel and categorical sampler; named Y/covariance tests passed. |
| QBP-03 | 01,02,03,07 | Independent syndrome, exact/degenerate/logical checks aligned with common conventions | ✓ SATISFIED | Independent evaluator and exhaustive CSS parity test passed. |
| QBP-04 | 01,06-16 | Source-backed compatible policies, quaternary BPGD, rejection/adaptation labeling | ✓ SATISFIED | Closed compatibility surface, real public dispatch, Q-BPGD/MBP4/aSCED execution and replay tests, honest source/run fidelity. |

No Phase 10 requirement is orphaned: QBP-01 through QBP-04 appear in plan frontmatter and map to Phase 10 in `REQUIREMENTS.md`.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| Phase 10 implementation/tests | — | No unreferenced TBD/FIXME/XXX, placeholder, or disabled-test markers found | None | No blocker. |

The decision-coverage checker reported 17/17 trackable context decisions honored. Security reports 58 mitigations verified, 12 planned low risks documented, and no open threats. Source inspection also confirms the decoder boundary does not import hidden truth and the evaluator does not reuse kernel algebra.

## Gaps Summary

No failed truth, missing artifact, stub, broken production link, unmet QBP requirement, behavior-unverified item, or human-verification item remains. The persisted full replay receipt closes the prior evidence item, so the phase goal is achieved.

---

_Verified: 2026-10-08T09:12:00Z_
_Verifier: the agent (gsd-verifier)_
