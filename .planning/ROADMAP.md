# Roadmap: Policy-Based BP Research Platform for QLDPC Decoding

## Overview

Build a provenance-preserving research platform from paper evidence through native references and canonical policy execution to statistically qualified experiments. The first journal milestone contains CSS code-capacity with separate X/Z decoding, correlated quaternary code-capacity, and circuit-level decoding, in that order. The systematic map, documentation, and experiment registry grow alongside the software and are completed with the manuscript and release evidence.

**Milestone:** v1.0 — platform and first journal-paper evidence.
**Structure:** End-to-end capability slices (`mvp` mode), fine granularity. Fourteen phases are used because the three required regimes each need distinct implementation and experimental qualification; phase counts are not a reason to merge those gates or defer publication scope.
**Planning status:** Phases 1–4, 6, and 10 are complete. Phase 5 implementation is technically verified with human visual review still open. Phase 7 is paused at 6/15 completed plans by user direction to prioritize BP variants; its failed OSD qualification remains recorded. Campaign and reproduction work remains in the first journal milestone. Later plan counts remain TBD.

## Phases

- [x] **Phase 1: Evidence Registry and Native CSS Baseline** — Trace a paper experiment to validated inputs, a pinned native decoder run, and an outcome ledger. (completed 2026-09-22)
- [x] **Phase 2: Canonical CSS Execution and Policy Contracts** — Run inspectable binary BP through the complete policy and evidence lifecycle. (completed 2026-09-23)
- [x] **Phase 3: Update Rules and Scheduling** — Compare the requested message rules and schedules with explicit semantics and work counters. (completed 2026-09-24)
- [x] **Phase 4: Memory Policies and Relay-BP** — Implement state/history policies and the source-defined relay composition. (completed 2026-09-30)
- [ ] **Phase 5: Guided and Perturbative BP Interventions** — Implement BPGD, impulse, freezing, syndrome/sign flips, and restarting.
- [x] **Phase 6: Beam Search, Ensembles, and Candidate Selection** — Expose branching, pruning, lists, and voting as auditable policies, and qualify the first three-paper CSS policy-file gate. (completed 2026-10-05)
- [ ] **Phase 7: Optional Postprocessing** — Paused by user after 6/15 plans to prioritize BP variants; retain the isolated OSD qualification failure and completed LSD/SI/OTF work for later resumption.
- [x] **Phase 8: Reproducible Campaigns and Statistical Assessment** — Run paired, resumable campaigns with prespecified statistical criteria. (completed 2026-10-11)
- [ ] **Phase 9: CSS Reproduction and Controlled Comparisons** — Qualify selected source results and isolate policy contributions in CSS decoding.
- [x] **Phase 10: Correlated Quaternary Execution** — Add joint Pauli inference and explicitly compatible policy compositions. (completed 2026-10-08)
- [ ] **Phase 11: Quaternary Reproduction and Comparisons** — Qualify correlated decoding and compare it with separate binary inference.
- [ ] **Phase 12: Circuit Models and Canonical Integration** — Decode noisy extraction circuits with validated detector/observable semantics.
- [ ] **Phase 13: Circuit Reproduction and Comparisons** — Qualify source-faithful circuit experiments and controlled policy comparisons.
- [ ] **Phase 14: Completed Mapping Study and Journal Evidence** — Complete the literature map, reproducible artifacts, documentation, and manuscript.

## Cross-Phase Contracts

- Every phase delivers a runnable or inspectable research capability with documentation and verification. Large reproduction claims wait until the statistical campaign gate in Phase 8; earlier runs are fixtures or pilots with their assessment status explicit.
- Source transcription, policy qualification, code/circuit artifact collection, and bounded mechanism pilots may continue alongside implementation phases. These feed later reproduction manifests; they do not bypass the Phase 8 statistical gate or the CSS, quaternary, circuit sequence.
- Native reference execution and canonical implementation are distinct. A paper's reported circuit experiment is reproduced in the circuit stage; earlier CSS demonstrations of its mechanisms are adaptations if their settings differ.
- One canonical engine is used within each compatible mathematical family. Circuit problems may reuse binary updates when justified; quaternary or richer correlated factors are not coerced into that kernel.
- All implemented policy compositions validate original-problem outputs and preserve provenance, work attribution, and source/interpretation status. Later phases inherit and extend these contracts.
- Statistical discrepancy and inconclusive statuses preserve evidence but never count as passing reproduction. A manuscript can report failed attempts honestly; a released claim of successful reproduction must meet its preregistered criterion.
- Supported papers/experiments are selected transparently from the mapping corpus. Missing code/settings remain documented gaps, and do not turn the entire corpus into a claimed reproduction registry.
- Numerical precision, source versions, exact code sizes, curve targets, statistical thresholds, and resource budgets are resolved before the dependent experiments, not silently guessed during execution.

## Phase Details

### Phase 1: Evidence Registry and Native CSS Baseline

**Goal:** As a researcher, I want to trace a source-linked paper record to a validated native CSS experiment, so that I can inspect its outcomes and provenance.
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** MAP-01, MAP-02, MAP-03, REG-01, REG-02, REG-03, REG-04, CSS-01, CSS-02, CSS-03, CSS-04, LED-01
**Success Criteria:**

1. A versioned search/screening/extraction protocol and seed records expose inclusion decisions, source revisions, taxonomy, and unresolved identities without claiming a completed systematic map.
2. A complete manifest schema resolves exact decoder settings, artifact hashes, noise/rates, seeds, budgets/stopping, versions, expected outputs, tolerances, sources, and discrepancies; malformed or changed inputs are rejected before execution.
3. Small CSS fixtures validate check/logical algebra, stable ordered hashes, separate X/Z and bit-flip conventions, and independently distinguish exact, degenerate, logical, and syndrome-invalid outcomes.
4. A documented local command runs a pinned native binary BP baseline on identified shots and writes linked outcomes/provenance, including nonconvergence and termination; no pilot is mislabeled statistically reproduced.
5. Registry evidence statuses distinguish mapped records, executable references, canonical implementations, and assessed results, including unavailable original code or missing source settings.

**Research focus:** Mapping protocol and initial corpus; exact source/reference selection and installation; CSS code/logical serialization; mathematical oracle; manifest/ledger contracts.
**Plans:** 9/9 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Wave 0 Python tests and observed environment identity
- [x] 01-02-PLAN.md — Blocking package legitimacy gate before new installs

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03-PLAN.md — End-to-end source-linked CSS native tracer

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-04-PLAN.md — CSS algebra, artifact hashes, sampling, and outcome oracle
- [x] 01-06-PLAN.md — Mapping protocol and BPGD/impulse CSS evidence extraction

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-05-PLAN.md — Durable per-shot ledger and interruption reconciliation
- [x] 01-08-PLAN.md — Candidate inventory and verified source-artifact freeze

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-07-PLAN.md — Strict manifest and immutable-input preflight

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 01-09-PLAN.md — Pinned 32-shot native CSS pilot and linked results

### Phase 2: Canonical CSS Execution and Policy Contracts

**Goal:** As a researcher, I want to inspect and run a canonical binary BP policy composition, so that I can trust its outcomes and computational attribution.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, SCH-01, LED-02, LED-03, LED-04, DOC-01
**Success Criteria:**

1. A manifest runs project-owned sum-product BP with flooding from CSS observations through the independent evaluator, a ledger, and a small result artifact.
2. The policy lifecycle defines typed interfaces, composition compatibility, original-problem preservation, hidden-truth isolation, numerical conventions, message order, and scoped stopping; invalid compositions and truth access are prevented by the execution boundary.
3. Deterministic small cases verify the update equation and policy transitions independently of curves; the source-to-specification and fixture pattern is reusable by later policies.
4. Canonical control-flow/candidate events and work/runtime counters are queryable by shot and attempt; native reference counters that cannot be observed carry explicit missingness reasons.
5. A researcher can install the package, run the tutorial, and inspect mathematical conventions, lifecycle contracts, and compatibility examples.

**Research focus:** Numerical stability, trace vocabulary, policy ownership, scoped budgets, and kernel-level work definitions.
**Plans:** 16/16 plans complete

Plans:

**Wave 1**

- [x] 02-01-PLAN.md — End-to-end canonical CSS manifest, BP, evaluator, and ledger tracer

**Wave 2** *(after Wave 1)*

- [x] 02-02-PLAN.md — Seven-role composition, lifecycle, compatibility, and policy evidence
- [x] 02-03-PLAN.md — Stable sum-product numerics and double-buffered flooding semantics

**Wave 3** *(after Wave 2)*

- [x] 02-05-PLAN.md — Candidate lineage, sparse control-flow events, and bounded traces

**Wave 4** *(after Wave 3 lineage contracts)*

- [x] 02-04-PLAN.md — Hierarchical budgets, atomic work, and qualified resource accounting

**Wave 5** *(after Wave 4)*

- [x] 02-06-PLAN.md — Honest native instrumentation missingness and summaries
- [x] 02-07-PLAN.md — Local profiling, representative cohorts, and replay agreement

**Wave 6** *(after Waves 2–5)*

- [x] 02-08-PLAN.md — Official canonical manifest, CLI integration, and verified result artifact

**Wave 7** *(after Wave 6)*

- [x] 02-09-PLAN.md — Executable tutorial, profiling strategy, and novelty/depth register

**Wave 8** *(verification gap closure)*

- [x] 02-10-PLAN.md — Executable baseline admission, scoped work budgets, and honest BP-call accounting

**Wave 9** *(after Wave 8)*

- [x] 02-11-PLAN.md — Structural ledger ownership and current-attempt candidate lineage

**Wave 10** *(after Waves 8–9)*

- [x] 02-12-PLAN.md — Profiling, trace admission, native isolation, tutorial correction, and fresh evidence

**Wave 11** *(after Wave 10)*

- [x] 02-13-PLAN.md — Full replay identity, structural verification, bounded profiling, and refreshed evidence

**Wave 12** *(after Wave 11)*

- [x] 02-14-PLAN.md — Exhaustive terminal-evidence grammar, budget reconstruction, and profile provenance

**Wave 13** *(after Wave 12)*

- [x] 02-15-PLAN.md — Complete provenance binding, persistent numerical verification, and RSS consistency

**Wave 14** *(after Wave 13)*

- [x] 02-16-PLAN.md — Closed RSS-unavailable producer and verifier grammar

### Phase 3: Update Rules and Scheduling

**Goal:** A researcher can vary requested message-update and scheduling policies without changing the canonical engine or losing semantic and cost visibility.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05, SCH-06
**Success Criteria:**

1. Min-sum, normalized min-sum, and offset min-sum have explicit parameters/equations and pass small-graph reference calculations alongside sum-product.
2. Layered and serial schedules expose their update unit, partition/traversal order, and fresh/stale-message semantics in executable fixtures.
3. Residual scheduling records residual definition, priority invalidation and selection work; randomized scheduling replays without modifying physical-error samples.
4. Cluster-sequential scheduling implements a pinned source-defined construction/order and records any learned/fixed parameters rather than substituting an unspecified clustering heuristic.
5. Researchers can run matched pilot comparisons of supported update/schedule combinations with raw work counters and explicit rejection of undefined combinations.

**Research focus:** Source definitions for offset min-sum and cluster sequencing, residual/cache semantics, and intervention-sensitive schedule state.
**Plans:** 17/17 plans complete

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Complete public min-sum tracer and schedule-neutral atomic local-step engine
- [x] 03-07-PLAN.md — Exact B1, generated (3,4) Gallager HGP, and BB-144 reuse

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Public normalized min-sum plus generated schema and documentation
- [x] 03-03-PLAN.md — Layered, CN/VN serial, and randomized schedule semantics
- [x] 03-04-PLAN.md — Huang–Ueng conventional sRBP cache, selection, and work

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-11-PLAN.md — Offset min-sum, generated assignments, refresh, and RNG replay

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-05-PLAN.md — Atomic local convergence, dual budgets, and versioned work/progress evidence

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-06-PLAN.md — First non-flooding public tracer through layered SPA
- [x] 03-12-PLAN.md — Full terminal reconstruction and bounded local-convergence traces

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 03-13-PLAN.md — Complete noncluster public policy admission and compatibility matrix

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 03-14-PLAN.md — Strict Moradi artifact loader, qualifier, and unavailable state

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 03-08-PLAN.md — Focused matched pilots with durable verified evidence

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 03-15-PLAN.md — Runnable notebook, tables, and diagnostic plots from retained pilots

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 03-09-PLAN.md — Pin and qualify Hsu non-disjoint group source construction for binary CSS adaptation

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 03-10-PLAN.md — One Hsu overlapping check-group update through the public engine

**Wave 12** *(blocked on Wave 11 completion)*

- [x] 03-16-PLAN.md — Complete Hsu group traversal, work, and reconstruction

**Wave 13** *(blocked on Wave 12 completion)*

- [x] 03-17-PLAN.md — Retained Hsu CSS-adaptation pilot and final SCH-06 gate

### Phase 4: Memory Policies and Relay-BP

**Goal:** As a QLDPC decoding researcher, I want to inspect state and history effects and execute a source-linked Relay-BP policy composition with faithful state transfer and accounting, so that I can distinguish policy behavior using bounded evidence with clear provenance.
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** MEM-01, MEM-02, MEM-03, MEM-04, MEM-05, MOD-01
**Success Criteria:**

1. Damping, mixing, momentum, iteration memory, and disordered memory each have a precise equation/procedure, application order, state lifetime, reset semantics, and deterministic verification fixtures.
2. Relay-BP explicitly records leg/member identity, disordered-memory draws, transferred posterior state, scoped stopping, and selected solutions.
3. A pinned original Relay-BP reference and canonical realization can run eligible pilot inputs with documented configuration translations, numerical differences, and native instrumentation limits.
4. A researcher can inspect memory/relay effects in deterministic fixtures and bounded retained pilots, recover leg work from their ledgers, and see missing or interrupted comparisons explicitly labeled. A comprehensive factorial is not a Phase 4 gate.

**Research focus:** Exact mixing/memory definitions, source equations and code defaults, warm-state inheritance, and candidate stopping/selection.
**Plans:** 15/15 plans complete

Plans:
**Wave 0**

- [x] 04-01-PLAN.md — End-to-end two-leg Relay tracer and Wave 0 test targets

**Wave 1** *(blocked on Wave 0 completion)*

- [x] 04-02-PLAN.md — Source-defined memory equations and independent history fixtures

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-03-PLAN.md — Ordered, repeated, seeded memory composition and compatibility

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-04-PLAN.md — Public memory manifest and CLI admission

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04-05-PLAN.md — Complete Relay lifecycle, controls, presets, and selection
- [x] 04-07-PLAN.md — Pinned author-source legitimacy gate

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 04-06-PLAN.md — Relay transfer, lineage, ledger, trace, and work reconstruction
- [x] 04-08-PLAN.md — Isolated author reference, translation, and observer equivalence

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 04-09-PLAN.md — Source-backed B1 identity reconciliation and versioned repair

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 04-15-PLAN.md — Identity-gated three-code pilot design and manifests

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 04-10-PLAN.md — Identified public execution path for matched pilots and stages

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 04-11-PLAN.md — Compute entitlement, benchmark, and finite cap freeze

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 04-12-PLAN.md — Finite per-code Relay memory tuning on calibration samples

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 04-13-PLAN.md — Reconcile cancelled production and qualify retained bounded evidence

**Wave 12** *(blocked on Wave 11 completion)*

- [x] 04-14-PLAN.md — Availability-aware notebook and evidence-backed research guide

**Review update (2026-09-26):** [Current gate and implementation review](../docs/phase4-plan-review-and-next-design.md)
records the isolated ordinary-memory correction, factorial order supplement,
trace gaps and pending evidence. Earlier plan summaries do not close these
follow-up gates. Phase 4 remains executing.

**Scope update (2026-09-30):** The user stopped the comprehensive Plan 04-13
experiment because its size was premature. The interrupted evaluation prefix
is preserved; the fresh evaluation/native/factorial sequence will not be
restarted to close Phase 4. Plans 04-13/14 now finish with retained evidence,
deterministic checks and explicit missingness. Phase 5 can begin once these
bounded Phase 4 verification and documentation gates pass. See the
[cancellation record](phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md).

**Completion (2026-09-30):** The revised four criteria and six requirements
passed [goal verification](phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md),
validation and security checks. The cancelled grid did not resume. Later CSS
campaigns must be sized from a new question, precision target, stop rule and
measured budget.

### Phase 5: Guided and Perturbative BP Interventions

**Goal:** As a QLDPC decoding researcher, I want to run and inspect guided fixation, impulse attempts, and perturbative BP interventions against the original decoding problem, so that I can study their behavior and assess their recoveries on the original problem.
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04
**Success Criteria:**

1. Canonical BPGD implements source-defined reliability selection, decimation/fixation, BP rounds, and state transitions, with fixtures and an explicit original-code availability record.
2. Impulse decoding preserves its source-defined failure trigger, shortening attempts, budgets, candidate lift, and selection; per-attempt work and unavailable native references remain visible.
3. Freezing, syndrome flipping, sign flipping, and restarting have explicit eligibility/trigger, changed versus preserved state, and source-linked semantics.
4. Constructed cases show that convergence on a modified working syndrome/graph cannot bypass validation against the original observation, and every restart/attempt is included in resource totals.
5. Researchers can enable/disable these interventions on eligible CSS pilots and inspect pre-intervention, attempted, and selected outcomes without claiming new settings reproduce a source curve.

**Research focus:** Original BPGD/impulse code discovery; perturbation semantics; lifting; random-stream and cache invalidation rules.
**Plans:** 14/14 plans implemented and technically verified; Phase 5 human notebook/HTML review remains open.

**Preparatory design (2026-09-26):** [Intervention contracts](phases/05-guided-and-perturbative-bp-interventions/05-DESIGN.md)
and [bounded next tasks](phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md)
are available, with independently checked finite shortening/lifting fixtures.
The Phase 4 dependency is complete. Phase 5 planning passed independent
verification on 2026-09-30; implementation is complete. Source ambiguities
retain explicit implementation dispositions and qualification labels.

Plans:

**Wave 0**

- [x] 05-01-PLAN.md — End-to-end BPGD tracer and first test targets

**Wave 1** *(blocked on Wave 0 completion)*

- [x] 05-02-PLAN.md — Source qualification and transformed-problem algebra
- [x] 05-03-PLAN.md — BP sessions, reset, ownership, and atomic work

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-04-PLAN.md — Complete guided decimation
- [x] 05-05-PLAN.md — Bounded impulse attempts and selection
- [x] 05-06-PLAN.md — Freezing, syndrome flips, and sign flips
- [x] 05-07-PLAN.md — Bounded Restart Belief branches
- [x] 05-09-PLAN.md — Plotly package identity and legitimacy gate

**Wave 3** *(blocked on Wave 2 controller completion)*

- [x] 05-08-PLAN.md — Versioned public manifest, CLI, ledger, and verifier
- [x] 05-12-PLAN.md — Deterministic BB-144 and HGP algebra and policy fixtures

**Wave 4** *(blocked on public execution)*

- [x] 05-10-PLAN.md — B1 entitlement, calibration, and sealed cap freeze

**Wave 5** *(blocked on cap freeze)*

- [x] 05-14-PLAN.md — Bounded matched B1 evaluation

**Wave 6** *(blocked on verified pilot evidence and package gate)*

- [x] 05-11-PLAN.md — Shot-first notebook and synchronized plots

**Wave 7** *(blocked on executed notebook)*

- [x] 05-13-PLAN.md — Standalone HTML export and documentation

### Phase 6: Beam Search, Ensembles, and Candidate Selection

**Goal:** A researcher can execute branching/ensemble searches and inspect how candidate generation, pruning, selection, and voting affect outputs and cost.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** MOD-04, INT-05, CAN-01. The voting kernel is available through Python; public policy-file voting is carried to Phase 9 as CAN-02.
**Success Criteria:**

1. The controlled CSS BeamSearch/RelayBP comparison has a shared initial BP run, declared damped branch/leg semantics, masked BeamSearch branches, ranking/pruning, width/budgets, candidate selection, source-linked fixtures, and verified work evidence. The original BeamSearch circuit procedure and native reference remain Phase 12–13 targets.
2. Generic branching/ensemble compositions declare member identity, inherited versus independent state, resource limits, and work aggregation without double-counting or hiding discarded paths.
3. List selection preserves candidate origin and eligibility with declared scores/ties. Coordinate-majority voting has an independently checked importable kernel primitive; its public manifest fails closed until Phase 9 adds end-to-end execution and replay.
4. Researchers can replay a small search tree and account for accepted, rejected, pruned and budget-exhausted paths through the ledger.
5. The first CSS literature set (Yao BPGD, Bhatnagar impulse, and Rabeti–Mahdavifar MBBP-LD) has source-grounded paper-level policy files with explicit runnable/unsupported status. At least one qualified variant per paper runs through the common policy-file command on a bounded CSS study with verified provenance and original-problem checks; full curve assessment remains in Phases 8–9.

**Research focus:** Controlled CSS BeamSearch/RelayBP semantics, ensemble/list selection, search work versus parallel latency, and a small B1 literature-policy execution gate; original circuit reference integration follows in Phases 12–13.
**Plans:** 9/9 plans complete; public voting remains fail-closed pending CAN-02 in Phase 9.

- [x] 06-01-PLAN.md
- [x] 06-02-PLAN.md
- [x] 06-03-PLAN.md
- [x] 06-04-PLAN.md
- [x] 06-05-PLAN.md
- [x] 06-06-PLAN.md
- [x] 06-07-PLAN.md
- [x] 06-08-PLAN.md
- [x] 06-09-PLAN.md

### Phase 7: Optional Postprocessing

**Goal:** A researcher can attach independently configurable additional processing to canonical BP nonconvergence while retaining clear BP-only evidence.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** POST-01, POST-02, POST-03, POST-04, POST-05
**Success Criteria:**

1. Canonical BP reliability/output state can feed optional OSD and LSD through verified interfaces with explicit order/method, trigger, and separate work accounting.
2. Source-resolved SI and OTF implementations preserve their actual inactivation/graph/BP/solve procedures, candidate reconstruction, and kernel compatibility, with acronym choices documented.
3. Disabling additional processing yields BP-only results; enabling declared nonconvergence fallback preserves those results plus final outcome, fallback origin, and cost.
4. Pinned native BP-OSD/BP-LSD composites run as references with tested APIs and metadata; their internal BP does not replace the canonical engine under an adapter label.

**Research focus:** Standalone fallback interfaces, reliability conventions, exact SI/OTF variants, and source numerical/API drift.
**Parallel literature work:** Continue adding source-grounded paper folders and runnable policy files for compatible CSS decoders while Phase 7 is built. Preserve source specifications and blockers in `paper_reproduction/`; use bounded pilots to expose missing kernel or manifest support. Any larger paper-curve assessment waits for Phase 8 campaign controls.
**Plans:** 6/15 plans complete; remaining work paused by user. Plan 07-03 qualification is failed and non-runnable.
**Pause decision:** On 2026-10-06, the user froze optional postprocessing and prioritized BP variants. No OSD source patch or reduced evidence contract is authorized by this decision.

Plans:

**Wave 1**

- [x] 07-01-PLAN.md — Run the public canonical BP-to-LSD tracer with ledger replay.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md — Verify the official standalone OSD source identity before any build.
- [x] 07-04-PLAN.md — Implement source-anchored SI mechanics as a labeled CSS adaptation.
- [x] 07-06-PLAN.md — Add pinned native BP-OSD/BP-LSD composite references.
- [x] 07-11-PLAN.md — Preserve real failed-attempt posterior snapshots for supported compositions.

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 07-03-PLAN.md — Qualify and integrate standalone OSD through an isolated worker. Qualification halted: the approved source lacks the required candidate-evidence API.

**Wave 4** *(OTF mechanics completed independently while 07-03 is halted)*

- [x] 07-05-PLAN.md — Implement ordered Tanner forest mechanics as a labeled CSS adaptation.

**Wave 5** *(blocked on Wave 4 and snapshot completion)*

- [ ] 07-07-PLAN.md — Admit qualified fallback methods and snapshot-capable compositions in strict public manifests.

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 07-12-PLAN.md — Emit and independently replay Phase 7 fallback evidence.

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 07-13-PLAN.md — Expose Phase 7 preflight, run, results, and verify-run through the public CLI.

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 07-08-PLAN.md — Compile complete literature policy files and resolve controlled fallback arms.

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 07-14-PLAN.md — Publish complete runnable OSD and LSD policy variants.
- [ ] 07-15-PLAN.md — Publish SI/OTF faithful specifications and named CSS adaptations.

**Wave 10** *(blocked on Wave 9 completion)*

- [ ] 07-09-PLAN.md — Run and verify the bounded matched B1 mechanism view.

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 07-10-PLAN.md — Publish the digest-bound shot-first notebook and HTML evidence view.

### Phase 8: Reproducible Campaigns and Statistical Assessment

**Goal:** As a researcher, I want to run, resume, and statistically assess paired experiments, so that I can preserve sample identity and stopping semantics while reporting uncertainty.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** LED-05, SIM-01, SIM-02, SIM-03, STAT-01, STAT-02, STAT-03, STAT-04, STAT-05
**Success Criteria:**

1. Matched comparison arms consume identical identified samples regardless of worker/branch count, or replay persisted samples when the backend cannot provide that invariance.
2. The same manifest runs locally and in bounded parallel/HPC jobs; checkpoint/resume and shard merging detect duplicates, incomplete work, and changed configurations/versions.
3. Before launch, the manifest fixes targets, tolerances, interval procedures, comparison families, stopping rules, and pass/fail/inconclusive criteria; imported/digitized targets retain their uncertainty and provenance.
4. Synthetic assessment fixtures cover zero/rare failures, fixed-shot and justified adaptive stopping, batch overshoot, insufficient precision, and paired comparisons.
5. Reports explicitly account for timeout, nonconvergence, partial runs and post-selection, including acceptance probability, conditional denominators, actual work, and environment/timing context.

**Research focus:** Paper-specific precision and budgets, sequential inference, digitization, multiplicity, sample replay, durable shard protocol, and site execution limits.
**Operational gate:** Profile decoder and replay throughput, ledger size, and HPC shard cost on representative nontrivial CSS samples before approving large campaigns; choose resource and storage budgets from measured evidence.
**Scope carry-forward:** Design future CSS campaigns from a newly prespecified question, precision target, stopping rule and measured budget. The cancelled Phase 4 grid is historical evidence, not a required or automatically funded Phase 8 run.
**Plans:** 20/20 plans complete

Plans:

- [x] 08-15-PLAN.md
- [x] 08-16-PLAN.md
- [x] 08-17-PLAN.md
- [x] 08-18-PLAN.md
- [x] 08-19-PLAN.md
- [x] 08-20-PLAN.md

**Wave 1**

- [x] 08-01-PLAN.md — Prove one fixed-shot campaign from preflight through immutable evidence and reconstruction.

**Wave 2**

- [x] 08-02-PLAN.md — Freeze campaign, stopping, assessment, resource, and denominator contracts.

**Wave 3**

- [x] 08-03-PLAN.md — Preserve source targets and plot-digitization precision.
- [x] 08-04-PLAN.md — Freeze arm-neutral samples, atomic unit keys, and disjoint shards.
- [x] 08-07-PLAN.md — Implement exact fixed-shot and finite-look inference.

**Wave 4**

- [x] 08-05-PLAN.md — Seal, validate, replay, and merge immutable shard evidence.
- [x] 08-08-PLAN.md — Implement paired comparisons, multiplicity, acceptance, and denominators.

**Wave 5**

- [x] 08-06-PLAN.md — Resume by verified set subtraction and reject identity drift.
- [x] 08-09-PLAN.md — Run bounded matched campaigns locally with topology-independent science.

**Wave 6**

- [x] 08-10-PLAN.md — Map the frozen shard plan to bounded Slurm transport.
- [x] 08-11-PLAN.md — Reconstruct explicit statistical and resource reports from verified evidence.

**Wave 7**

- [x] 08-12-PLAN.md — Expose the full campaign lifecycle through an installed command.
- [x] 08-13-PLAN.md — Measure representative costs and authorize or deny larger work.

**Wave 8**

- [x] 08-14-PLAN.md — Run and retain the bounded BB-144 operational gate and final verification.

### Phase 9: CSS Reproduction and Controlled Comparisons

**Goal:** A researcher can assess the selected published CSS results and compare BP mechanisms under shared conditions with trustworthy uncertainty and cost attribution.
**Mode:** mvp
**Depends on:** Phase 8
**Requirements:** EVAL-01, EVAL-02, EVAL-03, CAN-02
**Success Criteria:**

1. The selected CSS source experiments have pinned faithful configurations and native assessment reports, with original-code/settings gaps retained rather than silently defaulted.
2. Canonical CSS realizations are assessed against declared published targets; source-faithful passes, discrepancies, inconclusive points, and adaptations are distinguishable in the registry.
3. Controlled experiments and ablations share codes/noise/samples and explicit budgets, isolating update/schedule, memory/intervention, and search/selection effects across eligible compositions; optional-fallback effects enter only after their methods are independently qualified.
4. Generated results report outcome classes and aggregate denominators, convergence, iterations, work, runtime and resource context separately, without asserting superiority beyond the observed evidence.
5. Eligible CSS ensembles can select a declared public voting policy from a decoder file, execute it with complete ballots and lineage, validate the aggregate against the original syndrome, and replay the ledger. Voting comparisons use the same matched samples and budgets as list-selection controls.

**Research focus:** Final CSS paper/code/rate grid, faithful parameter extraction, meaningful ablation design, precision/power, and cost calibration.
**Scope carry-forward:** Reconsider memory/Relay comparisons alongside other CSS policies only after Phase 8 campaign rules are ready. Size a focused comparison from its scientific question and available compute; do not inherit the cancelled Phase 4 448-shot/14-arm grid by default.
**Plans:** 10/20 complete

**Wave 1**

- [x] 09-01-PLAN.md
- [x] 09-04-PLAN.md
- [x] 09-07-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md
- [x] 09-05-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-03-PLAN.md
- [x] 09-16-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 09-08-PLAN.md

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 09-20-PLAN.md — independently derived canonical resource limits and guarded execution.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 09-17-PLAN.md — guarded bounded batches, partial resume, and cap-censored replay complete.

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 09-06-PLAN.md — local controller committed; public lifecycle remains incomplete.

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 09-09-PLAN.md
- [ ] 09-18-PLAN.md

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 09-10-PLAN.md
- [ ] 09-11-PLAN.md

**Wave 10** *(blocked on Wave 9 completion)*

- [ ] 09-19-PLAN.md

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 09-12-PLAN.md
- [ ] 09-13-PLAN.md
- [ ] 09-14-PLAN.md

**Wave 12** *(blocked on Wave 11 completion)*

- [ ] 09-15-PLAN.md

### Phase 10: Correlated Quaternary Execution

**Goal:** As a researcher, I want to decode joint Pauli errors through a canonical quaternary BP kernel, so that correlation semantics and policy compatibility are verified.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** QBP-01, QBP-02, QBP-03, QBP-04
**Success Criteria:**

1. A source-defined four-state Pauli kernel uses commutation factors, declared message/numerical conventions, and joint X/Z inference through the shared execution lifecycle.
2. Joint I/X/Y/Z sampling and analytical/small-code fixtures verify Y errors, correlation, prior normalization, and physical-error-rate conventions.
3. The independent code-capacity evaluator correctly classifies quaternary candidates and produces the same outcome meanings as the CSS foundation.
4. Compatible source-backed policy compositions, including quaternary BPGD, execute with traceable semantics; unsupported ports are rejected and new adaptations are labeled.

**Research focus:** Quaternary factor equations, scalar/vector message representations, memory/numeric choices, and policy-specific compatibility derivations.
**Priority decision:** Begin this phase next, ahead of campaign infrastructure and reproduction, while Phase 7 optional postprocessing remains paused. Reuse the verified CSS execution lifecycle where mathematically compatible; keep correlated quaternary factors in their own canonical kernel family.
**Plans:** 16/16 plans complete

Plans:

**Wave 1**

- [x] 10-01-PLAN.md — Run and replay the public non-CSS joint-Pauli tracer.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 10-02-PLAN.md — Define Pauli algebra and immutable general/CSS problems.
- [x] 10-13-PLAN.md — Audit pinned native aSCED and freeze its build proposal.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 10-03-PLAN.md — Classify Pauli candidates independently.
- [x] 10-04-PLAN.md — Validate and sample joint Pauli channels.
- [x] 10-05-PLAN.md — Implement and independently check scalar LLR-BP4.
- [x] 10-10-PLAN.md — Construct, qualify, and identify CSS aSCED splitters.
- [x] 10-14-PLAN.md — Resolve the exact native source and build trust gate.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 10-06-PLAN.md — Add quaternary schedules, normalization, and offset.
- [x] 10-11-PLAN.md — Bind and verify overcomplete aSCED maps.
- [x] 10-15-PLAN.md — Build and run the pinned native aSCED reference.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 10-07-PLAN.md — Admit compatible compositions through public execution.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 10-08-PLAN.md — Execute and replay quaternary BPGD.

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 10-09-PLAN.md — Execute and replay fixed-alpha MBP4.

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 10-12-PLAN.md — Run every aSCED path and select original-valid candidates.

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 10-16-PLAN.md — Run and verify bounded matched mechanism evidence.

### Phase 11: Quaternary Reproduction and Comparisons

**Goal:** A researcher can qualify selected correlated code-capacity results and compare joint versus separate inference on identical physical samples.
**Mode:** mvp
**Depends on:** Phase 8 and Phase 10
**Requirements:** QEV-01, QEV-02
**Success Criteria:**

1. Selected quaternary publication experiments have exact source settings, manifests, reference availability records, and canonical reproduction assessments with declared uncertainty/tolerances.
2. Joint quaternary and separate binary decoders receive the same sampled joint Pauli channel and explicit work/resource budgets; differing inference assumptions remain documented.
3. Source-backed compatible policy ablations produce replayable results, outcome/work analysis and discrepancy records, with no forced assumption that every binary policy has a faithful quaternary counterpart.

**Research focus:** Quaternary paper targets and native-code availability, matched baseline priors, correlated-noise ablations, and kernel-aware cost comparisons.
**Plans:** TBD

### Phase 12: Circuit Models and Canonical Integration

**Goal:** A researcher can run eligible native and canonical decoders on noisy extraction circuits and evaluate detector and logical-observable behavior correctly.
**Mode:** mvp
**Depends on:** Phase 11
**Requirements:** CIR-01, CIR-02, CIR-03, CIR-04, CIR-05
**Success Criteria:**

1. Circuit manifests identify and hash the noisy circuit, rounds/boundaries, detector/fault representation, observables, extraction/conversion options, and any correlation approximations.
2. Known injected-fault fixtures verify detector and logical-observable maps; a detector-fitting candidate with wrong logical prediction fails the appropriate observable check.
3. Eligible canonical policies execute using mathematically compatible factors, with binary reuse justified and richer representations introduced only when required by the selected model.
4. Pinned circuit references, including the original BeamSearch implementation for its selected circuit target, consume matched observations through documented transforms and expose any instrumentation limits.
5. The ledger distinguishes detector fit and observable correctness and explicitly marks static exact/degenerate recovery fields not applicable when undefined; channel dependencies cannot be silently dropped.

**Research focus:** Extraction circuits, detector/fault factorization, exclusive/correlated mechanisms, rounds/windows, observables, and source reference settings.
**Plans:** TBD

### Phase 13: Circuit Reproduction and Comparisons

**Goal:** A researcher can qualify selected published circuit results and compare eligible policy compositions using shared circuit samples and explicit computational budgets.
**Mode:** mvp
**Depends on:** Phase 12
**Requirements:** CEV-01, CEV-02, CEV-03
**Success Criteria:**

1. Selected circuit source experiments run under pinned source-faithful conditions and produce native-reference assessments with complete model provenance.
2. Canonical circuit realizations are assessed against the source targets with declared tolerances, stopping/uncertainty procedures, and explicit pass/fail/inconclusive status.
3. Controlled policy comparisons share circuit samples and budgets and report observable failure, convergence, work, runtime distributions, resources, and post-selection separately.
4. Circuit-first paper claims deferred during CSS adaptation work, including the original BeamSearch target and pinned reference, are addressed in their original setting; remaining limitations are linked to experiment records and manuscript evidence.

**Research focus:** Circuit paper/figure selection, exact source settings, correlation sensitivity, native/canonical timing comparability, and rare-event precision.
**Plans:** TBD

### Phase 14: Completed Mapping Study and Journal Evidence

**Goal:** A reader can audit the full literature map and reproduce the paper's evidence across all three regimes from documented, versioned artifacts.
**Mode:** mvp
**Depends on:** Phase 13
**Requirements:** MAP-04, REG-05, DOC-02, PUB-01, PUB-02, PUB-03
**Success Criteria:**

1. The systematic map contains the final search update/cutoff, screening flow/counts, source-linked extraction dataset, data dictionary, and limitations.
2. The enumerated supported paper experiments all have complete manifests, executable entries, assessment/discrepancy reports, and honest evidence status; mapped-only exclusions remain identifiable.
3. Detailed installation, extension, reference-environment, manifest, sampling, ledger, statistical and HPC guides let a reader reproduce representative evidence through documented commands.
4. Manuscript tables/figures and quantitative claims regenerate from versioned analyses and linked manifests/ledgers, with uncertainty and failed/inconclusive attempts represented honestly.
5. A journal manuscript and accessible release bundle cover the canonical policy model, completed mapping study, reproduction evidence, and controlled results from CSS, quaternary, and circuit stages; artifact hashes and environment specifications are included.

**Research focus:** Final map completeness, claim-to-evidence audit, release usability, source/version freeze, and venue-specific manuscript requirements.
**Plans:** TBD

## Progress

**Execution order:** Phases 1–6 are complete or technically verified as recorded above. Phase 7 is paused, and Phase 10 quaternary BP is complete. Phase 8 campaign controls precede statistical assessment in Phases 9 and 11. The later circuit and journal phases retain their dependencies. Independent plans within a phase may execute in parallel once their dependencies are verified.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Evidence Registry and Native CSS Baseline | 9/9 | Complete    | 2026-09-22 |
| 2. Canonical CSS Execution and Policy Contracts | 16/16 | Complete    | 2026-09-23 |
| 3. Update Rules and Scheduling | 17/17 | Complete    | 2026-09-24 |
| 4. Memory Policies and Relay-BP | 15/15 | Complete    | 2026-09-30 |
| 5. Guided and Perturbative BP Interventions | 14/14 | Human review pending |  |
| 6. Beam Search, Ensembles, and Candidate Selection | 9/9 | Complete    | 2026-10-05 |
| 7. Optional Postprocessing | 6/15 | Paused by user; POST-01 qualification failed |  |
| 8. Reproducible Campaigns and Statistical Assessment | 20/20 | Complete    | 2026-10-11 |
| 9. CSS Reproduction and Controlled Comparisons | 10/20 | In Progress|  |
| 10. Correlated Quaternary Execution | 16/16 | Complete    | 2026-10-08 |
| 11. Quaternary Reproduction and Comparisons | 0/TBD | Not started | - |
| 12. Circuit Models and Canonical Integration | 0/TBD | Not started | - |
| 13. Circuit Reproduction and Comparisons | 0/TBD | Not started | - |
| 14. Completed Mapping Study and Journal Evidence | 0/TBD | Not started | - |

---
*Created: 2026-09-21 in approved autonomous mode. 84 requirements assigned to 14 phases; implementation has not started.*
