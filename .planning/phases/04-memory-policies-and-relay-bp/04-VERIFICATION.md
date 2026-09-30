---
phase: 04-memory-policies-and-relay-bp
verified: 2026-09-30T05:21:34Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/async-jobs/04-13-production-v1.json
  - .planning/phases/04-memory-policies-and-relay-bp/04-01-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-01-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-02-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-02-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-03-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-03-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-04-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-04-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-05-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-05-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-06-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-06-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-07-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-07-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-08-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-08-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-09-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-09-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-10-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-10-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-11-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-11-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-12-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-12-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-13-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-13-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-14-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-14-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-15-PLAN.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-15-SUMMARY.md
  - .planning/phases/04-memory-policies-and-relay-bp/04-CONTEXT.md
  - data/evidence/code-inventory.json
  - data/evidence/phase4-b1-identity-resolution.json
  - data/evidence/phase4-factorial-execution-supplement-v1.json
  - data/evidence/phase4-pilot-design-amendment-v3.json
  - data/evidence/phase4-pilot-design-amendment-v4-active-memory.json
  - data/evidence/phase4-pilot-design.json
  - data/evidence/phase4-retained-evidence-inventory.json
  - data/evidence/relay-v0.2.2-source.json
  - data/manifests/phase4-memory-relay-b1.json
  - data/manifests/phase4-memory-relay-bb144.json
  - data/manifests/phase4-memory-relay-hgp.json
  - data/manifests/phase4-pilot-caps-v3-pre-active-memory.json
  - data/manifests/phase4-pilot-caps.json
  - data/manifests/schema-canonical-v4.json
  - data/results/phase4-memory-relay/author-v022-agreement-v1/result.json
  - data/results/phase4-memory-relay/benchmark-v2.json
  - data/results/phase4-memory-relay/benchmark-v3-b1-p07-bounded-three-leg.json
  - data/results/phase4-memory-relay/benchmark-v3-p05-bb-b1-amendment.json
  - data/results/phase4-memory-relay/benchmark-v3-p07-bb-b1-amendment.json
  - data/results/phase4-memory-relay/benchmark-v3-representative.json
  - data/results/phase4-memory-relay/benchmark.json
  - data/results/phase4-memory-relay/calibration/result.json
  - data/results/phase4-memory-relay/evaluation/b1-ghp-882/baseline/attempts.json
  - data/results/phase4-memory-relay/selected-settings.json
  - data/results/phase4-notebook/retained-cancelled-phase4.ipynb
  - docs/canonical-engine.md
  - docs/memory-policy-sources.md
  - docs/phase4-memory-relay.md
  - docs/phase4-plan-review-and-next-design.md
  - native/relay-v0.2.2-observer.patch
  - notebooks/phase4-memory-relay-analysis.ipynb
  - scripts/execute_phase4_notebook.py
  - scripts/phase4_notebook_campaign.py
  - scripts/phase4_notebook_presentation.py
  - scripts/phase4_notebook_support.py
  - scripts/phase4_shared_evaluation.py
  - scripts/preview_phase4_notebook.py
  - scripts/qualify_phase4_artifacts.py
  - scripts/qualify_relay_v022.py
  - scripts/run_phase4_active_benchmark.py
  - scripts/run_phase4_active_campaign.py
  - scripts/run_phase4_evaluation.py
  - scripts/run_phase4_factorial.py
  - scripts/run_phase4_pilots.py
  - scripts/summarize_phase4_author_runtime.py
  - scripts/verify_phase4_calibration.py
  - src/bp_registry/canonical/budgets.py
  - src/bp_registry/canonical/compatibility.py
  - src/bp_registry/canonical/contracts.py
  - src/bp_registry/canonical/execution.py
  - src/bp_registry/canonical/kernel.py
  - src/bp_registry/canonical/lineage.py
  - src/bp_registry/canonical/memory.py
  - src/bp_registry/canonical/memory_execution.py
  - src/bp_registry/canonical/relay.py
  - src/bp_registry/canonical/schedules.py
  - src/bp_registry/canonical/updates.py
  - src/bp_registry/canonical/verification.py
  - src/bp_registry/cli.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/native/relay_v022.py
  - src/bp_registry/phase4_analysis.py
  - src/bp_registry/runner.py
  - tests/canonical/test_local_memory_execution.py
  - tests/canonical/test_memory_composition.py
  - tests/canonical/test_memory_execution.py
  - tests/canonical/test_memory_policies.py
  - tests/canonical/test_memory_trace.py
  - tests/canonical/test_phase4_active_benchmark.py
  - tests/canonical/test_phase4_active_campaign.py
  - tests/canonical/test_phase4_analysis.py
  - tests/canonical/test_phase4_author_runtime.py
  - tests/canonical/test_phase4_calibration_ledgers.py
  - tests/canonical/test_phase4_calibration_verification.py
  - tests/canonical/test_phase4_evaluation.py
  - tests/canonical/test_phase4_evidence.py
  - tests/canonical/test_phase4_factorial.py
  - tests/canonical/test_phase4_notebook.py
  - tests/canonical/test_phase4_notebook_campaign.py
  - tests/canonical/test_phase4_notebook_presentation.py
  - tests/canonical/test_public_manifest_context.py
  - tests/canonical/test_relay.py
  - tests/canonical/test_relay_differential.py
  - tests/test_canonical_cli.py
  - tests/test_manifest.py
covered_digest: "v1:sha256:caea515eec265fc7d448dc5af3133d1a47d13ae7278a563a58146e13a89e762e"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 28
  total: 30
  not_honored: [D-27, D-28]
---

# Phase 4: Memory Policies and Relay-BP Verification Report

**Phase Goal:** As a QLDPC decoding researcher, I want to inspect state and history effects and execute a source-linked Relay-BP policy composition with faithful state transfer and accounting, so that I can distinguish policy behavior using bounded evidence with clear provenance.

**Verified:** 2026-09-30T05:21:34Z
**Status:** passed
**Re-verification:** No — initial verification

## User Flow Coverage

User story: “As a QLDPC decoding researcher, I want to inspect state and history effects and execute a source-linked Relay-BP policy composition with faithful state transfer and accounting, so that I can distinguish policy behavior using bounded evidence with clear provenance.”

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Inspect memory behavior | Equations, operands, order, state lifetime, reset semantics, and deterministic examples are visible for all five memory families. | `docs/memory-policy-sources.md`; executable primitives in `src/bp_registry/canonical/memory.py`; deterministic value and state tests in `tests/canonical/test_memory_policies.py` and `tests/canonical/test_memory_execution.py`. | ✓ |
| Execute source-linked Relay-BP | The public manifest/CLI path executes canonical Relay legs and separately identifies the exact author v0.2.2 reference. | `CanonicalExperimentV4` admission, `run_canonical_structural_shot`, `RelayController`, `RelayV022Adapter`; the public preflight/run/verify spot-check passed. | ✓ |
| Inspect transfer and accounting | The event ledger exposes leg identities, seeded memory realizations, posterior transfer, stopping, candidates, selection, and reconstructible per-leg work. | `src/bp_registry/canonical/execution.py`, `src/bp_registry/canonical/verification.py`; Relay and ledger reconstruction spot-checks passed. | ✓ |
| Distinguish behavior using bounded evidence | The notebook and guide read verified retained evidence, label cancelled stages unavailable, and never convert the 159+1 receipt prefix into a performance denominator. | `scripts/phase4_notebook_campaign.py`, `notebooks/phase4-memory-relay-analysis.ipynb`, `data/evidence/phase4-retained-evidence-inventory.json`; cancellation tests passed. | ✓ |
| Outcome | Bounded mechanism/source evidence has explicit identities and work; absent comparisons remain visibly absent, so policy behavior can be inspected without an unsupported ranking or reproduction claim. | Retained inventory, notebook, guide, and cancellation record agree on `not_assessed`; no fresh evaluation/native-pair/factorial result exists. | ✓ |

## Goal Achievement

### Observable Truths

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | Damping, mixing, momentum, iteration memory, and disordered memory each have a precise equation/procedure, application order, state lifetime, reset semantics, and deterministic verification fixtures. | ✓ VERIFIED | The five executable mechanisms are distinct classes/controllers with finite operand checks, explicit targets and advance boundaries, owned state, reset methods, ordered binding contracts, and seeded PCG64 assignment evidence. `test_memory_policies.py` plus the scalar-equation and disordered-replay spot-checks passed. |
| 2 | Relay-BP explicitly records leg/member identity, disordered-memory draws, transferred posterior state, scoped stopping, and selected solutions. | ✓ VERIFIED | The canonical execution emits attempts, transfers, work leaves, candidates, selection, and termination; Relay evidence retains per-leg memory applications and derived seed identities. Independent reconstruction validates lineage and work. Three Relay/ledger behavioral spot-checks passed. |
| 3 | A pinned original Relay-BP reference and canonical realization can run eligible pilot inputs with documented configuration translations, numerical differences, and native instrumentation limits. | ✓ VERIFIED | The adapter requires author tag v0.2.2 at commit `14cb31a…`, rejects the installed fork as the author reference, translates only decoder-visible inputs, requires explicit f32/f64, and types inaccessible facts as unavailable. The isolated build compiled all native test targets and passed a bounded terminal-equivalent observer fixture; the full `decode_144_12_12` test remains `inconclusive_timeout`. Retained three-code benchmark attempts bind native and canonical arms to matching sample identities. The public canonical CLI and exact-author record tests passed. |
| 4 | A researcher can inspect memory/relay effects in deterministic fixtures and bounded retained pilots, recover leg work from their ledgers, and see missing or interrupted comparisons explicitly labeled. A comprehensive factorial is not a Phase 4 gate. | ✓ VERIFIED | A retained benchmark shot independently verified as `completed`, and its Relay work is ledger-reconstructible. The cancellation inventory binds the B1 receipt SHA-256 and counts exactly 159 completed plus 1 interrupted receipt, sets the performance denominator to null, and records evaluation/native/factorial results as unavailable. The terminal job record disables automatic resume. Notebook cancellation and no-synthesis tests passed. |

**Score:** 4/4 truths verified (0 present but behavior-unverified)

The cancelled comprehensive evaluation was not run or resumed during verification. B1 selection remains inconclusive under its frozen cap. The 159 completed and one interrupted records are attempt receipts, not performance data.

### Required Artifacts

| Artifact group | Expected | Status | Details |
|---|---|---|---|
| `src/bp_registry/canonical/memory.py`, `memory_execution.py`, `contracts.py`, `compatibility.py` | Substantive executable memory mechanisms and public ordered composition | ✓ VERIFIED | Classes, contracts, compatibility decisions, source/local execution, seeded assignment, atomic proposal/commit, and reset behavior are implemented and used by public execution. |
| `src/bp_registry/canonical/relay.py`, `execution.py`, `ledger.py`, `verification.py` | Sequential Relay execution and independently reconstructible evidence | ✓ VERIFIED | Public execution constructs Relay, emits versioned evidence, and independent verification reconstructs transfers, terminal state, and leaf work. |
| `src/bp_registry/native/relay_v022.py`, `native/relay-v0.2.2-observer.patch`, `data/evidence/relay-v0.2.2-source.json` | Exact author reference, translation, patch identity, and qualification | ✓ VERIFIED | Exact repository/tag/commit/tree are enforced; fork/main/patch identities remain separate; unobservable native facts are explicit. |
| `data/artifacts/b1-panteleev-kalachev-v4.npz` (conditional Plan 04-09 branch) | A new artifact only if frozen v3 bytes or metadata were stale | ✓ NOT APPLICABLE | The measured resolution is `inventory_stale`: the source-matched v3 artifact remains valid and is preflighted. Active tests require the v4 artifact to remain absent in this branch. |
| Three Phase 4 manifests and retained benchmark/calibration evidence | Eligible, identity-gated bounded inputs and evidence | ✓ VERIFIED | BB-144, source-resolved B1, and generated-family HGP retain distinct qualifications; B1 inconclusive selection is preserved. |
| Availability-aware notebook, campaign reader, guide, and retained inventory | Inspect bounded evidence without fabricating missing stages | ✓ VERIFIED | Read-only campaign reconstruction checks hashes and paths; notebook code does not invoke evaluation or factorial producers. |

All GSD artifact checks passed except the conditionally absent B1 v4 artifact described above. All declared key-link checks passed.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| V4 manifest / CLI | memory execution | strict manifest projection and ordered binding admission | ✓ WIRED | Public CLI tests exercise preflight, run, and verification with memory enabled. |
| Canonical execution | Relay controller | `run_canonical_structural_shot` creates and runs `RelayController` | ✓ WIRED | Public Relay CLI spot-check emitted `relay_transfer` and verified the shot. |
| Relay controller | memory primitives | per-leg affine/disordered prior application before committed sweeps | ✓ WIRED | Active-memory test records first-leg and later-leg realized gamma evidence. |
| Ledger | independent Phase 4 verifier | hash-linked event stream and public manifest context | ✓ WIRED | Reconstruction tests reject tampered selection/work and reproduce terminal/work facts. |
| Pilot runner | public CLI and exact-author adapter | preflight/run/verify plus separately identified native translation | ✓ WIRED | Runner has no private `run_canonical` shortcut; stage identities preserve source and sample identity. |
| Retained inventory | notebook/campaign presentation | exact path, SHA-256, status, and denominator checks | ✓ WIRED | Real cancellation inventory and presentation tests passed; unqualified receipt rows produce no performance figure. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Public canonical run | terminal candidate, Relay legs, work vector | Manifest → canonical execution → Relay/memory controllers → event ledger | Yes; a retained benchmark ledger shot independently verifies | ✓ FLOWING |
| Exact-author adapter | native candidate/posterior/termination fields | Verified v0.2.2 source record → injected isolated native runner → typed result | Yes in retained qualification/benchmark evidence; unavailable per-edge fields remain typed missing | ✓ FLOWING |
| Notebook campaign views | stage status, counts, denominators, work | Retained inventory and producer artifacts, verified by path/hash/identity before presentation | Yes; missing result paths produce `cancelled_before_completion`, not fallback values | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Five memory equations and proposal state are deterministic | `pytest -q tests/canonical/test_memory_execution.py::test_two_steps_match_scalar_equations_and_proposals_do_not_mutate_history` | 5 passed | ✓ PASS |
| Source equations, resets, disordered replay, and B1 identity branch | `pytest -q tests/canonical/test_memory_policies.py ...::test_disordered_affine_prior_assignment_is_decoder_local_replayed_and_atomic ...::test_b1_inventory_only_repair_preserves_v3_and_preflights_resolved_phase4_manifest` | 18 passed | ✓ PASS |
| Relay transfer, seeded per-leg memory, and ledger reconstruction | Three named tests from `test_relay.py` and `test_phase4_evidence.py` | 3 passed | ✓ PASS |
| Pinned author record and public canonical CLI | Exact-author terminal record test plus `test_public_verify_executes_phase4_relay_through_cli` | 2 passed | ✓ PASS |
| Actual retained Relay ledger | `bp_registry.cli verify-canonical-shot .../gross-bb-144/canonical-relay-31/run --shot 0` | `termination: completed` | ✓ PASS |
| Cancellation status and no performance synthesis | Three named notebook/campaign/presentation tests | 3 passed | ✓ PASS |
| Public disordered assignment evidence across flooding/local schedules | Two named memory execution tests | 4 passed | ✓ PASS |

### Probe Execution

No Phase 4 probe scripts are declared or present. The phase exposes Python/CLI entry points, covered by the behavioral spot-checks above.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| MEM-01 | 04-02, 04-03, 04-04, 04-10, 04-13, 04-14, 04-15 | Explicit damping equation, parameter, application point, and reset behavior | ✓ SATISFIED | `V2CDamping`; source documentation; endpoint, boundary, reset, public execution tests. |
| MEM-02 | 04-02, 04-03, 04-04, 04-10, 04-13, 04-14, 04-15 | Precisely specified mixing operands, weights, and order | ✓ SATISFIED | Distinct PDBP field and PD-prime delta mixing; ordered composition and independent divergence fixtures. |
| MEM-03 | 04-02, 04-03, 04-04, 04-10, 04-13, 04-14, 04-15 | Source-defined momentum state and initialization/reset | ✓ SATISFIED | `PosteriorMomentum` retains posterior/velocity, initializes zero velocity, resets explicitly, and executes publicly. |
| MEM-04 | 04-01–06, 04-10, 04-12–15 | Source-defined iteration memory with retained state, lifetime, and update | ✓ SATISFIED | EWA/Relay affine primitive, owned state lifetimes, attempt/leg reset, proposal/commit atomicity, and replay tests. |
| MEM-05 | 04-01, 04-03–05, 04-10, 04-12–15 | Declared disordered distribution, seed, update, and inheritance/reset | ✓ SATISFIED | PCG64 seed derivation and replay identity, resolved vectors, per-leg drawn gamma evidence, and retained/reset contracts. |
| MOD-01 | 04-01, 04-05–15 | Source-linked canonical Relay composition plus pinned original reference in eligible regimes | ✓ SATISFIED | Canonical sequential posterior-only Relay, selection/stopping/accounting, exact-author v0.2.2 adapter and qualification, and identity-matched bounded pilots. |

No Phase 4 requirement is orphaned: all six roadmap requirement IDs appear in plan frontmatter and have executable evidence.

### Prohibition Enforcement

| Prohibition concern | Enforcement evidence | Verdict |
|---|---|---|
| Hidden truth must not influence memory, Relay control, scoring, or selection | Decoder-visible controller inputs exclude hidden truth; evaluation occurs only after selection; native translation rejects a hidden-truth argument. | ✓ ENFORCED |
| Classical/CSS adaptations and coefficient variants must not be presented as source-faithful quantum methods | Manifest relations/fidelity labels and source audit distinguish adaptations, interpretations, presets, and exact-source evidence. | ✓ ENFORCED |
| CSS pilots must not be presented as reproductions of Relay circuit curves | All three manifests and the guide use `not_assessed` and explicitly deny curve reproduction/ranking. | ✓ ENFORCED |
| Fork/main/observer identities must not substitute for unmodified author v0.2.2 | Adapter validates exact repository/tag/commit/tree; source record keeps all identities separate. | ✓ ENFORCED |
| Generated HGP and B1 identity must not be silently promoted | Active manifest tests require generated HGP discrepancy text and the reconciled B1 semantic identity. | ✓ ENFORCED |
| Cancelled production must not restart or yield a comparative claim | Terminal job record disables resume; notebook has no producer calls; interrupted receipts have no performance denominator or figure. | ✓ ENFORCED |

### Test Quality Audit

| Test group | Linked requirements | Active coverage | Skipped | Circular | Assertion level | Verdict |
|---|---|---:|---:|---|---|---|
| Memory policy/composition/execution | MEM-01–MEM-05 | Multiple active value and state-transition tests | 0 | No | Value + behavioral | Strong |
| Relay and differential source checks | MOD-01, MEM-04, MEM-05 | Active public-path, transfer, selection, identity, and reconstruction tests | 0 | No | Value + behavioral | Strong |
| Phase 4 evidence/notebook | MEM-01–MEM-05, MOD-01 | Active identity, retained evidence, cancellation, denominator, and presentation tests | 1 | No | Value + behavioral | Adequate; warning below |

One old reserved test, `test_notebook_stage_reuse_requires_matching_manifest_source_policy_and_sample_identities`, remains skipped with obsolete Wave 1 wording. It is not sole evidence: active stage-reuse, source-byte, sample-identity, mismatch-preservation, and cancellation tests cover the behavior. Test fixture writes are confined to temporary directories and compare against independent constants or retained external-source records; no circular expected-value generator was found.

**Disabled tests on requirements:** 1 → warning, with active replacement coverage  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `tests/canonical/test_phase4_calibration_verification.py` | 77, 114 | “placeholder” in test names | ℹ️ Info | Refers to typed incomplete cap records under test, not an implementation placeholder. |
| `tests/canonical/test_phase4_evaluation.py` | 33 | `fixture-only cap placeholder` test data | ℹ️ Info | Deliberately exercises missing/ineligible evidence handling. |

No unreferenced TBD, FIXME, or XXX marker and no user-visible stub was found in the Phase 4 implementation surface.

### Decision Coverage (warning)

The heuristic reports 28/30 context decisions as honored and misses D-27 and D-28. Those two decisions describe the pre-cancellation notebook generating the comprehensive campaign and displaying completed evaluation/factorial outputs. D-30 expressly supersedes that execution scale, and Roadmap success criterion 4 says a comprehensive factorial is not a Phase 4 gate. The shipped notebook instead satisfies the revised contract by showing the retained calibration and bounded pilots while labeling evaluation, native-pair, factorial, and trace populations unavailable. This warning does not change the verdict.

### Human Verification Required

None. This is an internal research-platform phase whose roadmap truths are exercised by deterministic tests and retained machine-verifiable evidence; no visual or external-service behavior remains unverified.

### Gaps Summary

No blocking gaps. The comprehensive evaluation/native-pair/factorial sequence is intentionally absent under the 2026-09-30 user cancellation and revised Roadmap contract. The interrupted B1 prefix remains `not_assessed`, and B1 calibration selection remains inconclusive. Neither absence is used as performance evidence.

---

_Verified: 2026-09-30T05:21:34Z_  
_Verifier: the agent (gsd-verifier)_
