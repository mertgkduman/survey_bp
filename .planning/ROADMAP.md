# Roadmap: Policy-Based BP Research Platform for QLDPC Decoding

## Overview

Build a provenance-preserving research platform from paper evidence through native references and canonical policy execution to statistically qualified experiments. The first journal milestone contains CSS code-capacity with separate X/Z decoding, correlated quaternary code-capacity, and circuit-level decoding, in that order. The systematic map, documentation, and experiment registry grow alongside the software and are completed with the manuscript and release evidence.

**Milestone:** v1.0 — platform and first journal-paper evidence.
**Structure:** End-to-end capability slices (`mvp` mode), fine granularity. Fourteen phases are used because the three required regimes each need distinct implementation and experimental qualification; phase counts are not a reason to merge those gates or defer publication scope.
**Planning status:** Phases 1–4 are complete. Phase 5 implementation is technically verified with human review still open. Phase 6 is being replanned around the approved three-paper CSS policy gate and existing BeamSearch/RelayBP work; later plan counts remain TBD.

## Phases

- [x] **Phase 1: Evidence Registry and Native CSS Baseline** — Trace a paper experiment to validated inputs, a pinned native decoder run, and an outcome ledger. (completed 2026-09-22)
- [x] **Phase 2: Canonical CSS Execution and Policy Contracts** — Run inspectable binary BP through the complete policy and evidence lifecycle. (completed 2026-09-23)
- [x] **Phase 3: Update Rules and Scheduling** — Compare the requested message rules and schedules with explicit semantics and work counters. (completed 2026-09-24)
- [x] **Phase 4: Memory Policies and Relay-BP** — Implement state/history policies and the source-defined relay composition. (completed 2026-09-30)
- [ ] **Phase 5: Guided and Perturbative BP Interventions** — Implement BPGD, impulse, freezing, syndrome/sign flips, and restarting.
- [ ] **Phase 6: Beam Search, Ensembles, and Candidate Selection** — Expose branching, pruning, lists, and voting as auditable policies, and qualify the first three-paper CSS policy-file gate.
- [ ] **Phase 7: Optional Postprocessing** — Add independent OSD/LSD/SI/OTF processing with BP-only attribution preserved.
- [ ] **Phase 8: Reproducible Campaigns and Statistical Assessment** — Run paired, resumable campaigns with prespecified statistical criteria.
- [ ] **Phase 9: CSS Reproduction and Controlled Comparisons** — Qualify selected source results and isolate policy contributions in CSS decoding.
- [ ] **Phase 10: Correlated Quaternary Execution** — Add joint Pauli inference and explicitly compatible policy compositions.
- [ ] **Phase 11: Quaternary Reproduction and Comparisons** — Qualify correlated decoding and compare it with separate binary inference.
- [ ] **Phase 12: Circuit Models and Canonical Integration** — Decode noisy extraction circuits with validated detector/observable semantics.
- [ ] **Phase 13: Circuit Reproduction and Comparisons** — Qualify source-faithful circuit experiments and controlled policy comparisons.
- [ ] **Phase 14: Completed Mapping Study and Journal Evidence** — Complete the literature map, reproducible artifacts, documentation, and manuscript.

## Cross-Phase Contracts

- Every phase delivers a runnable or inspectable research capability with documentation and verification. Large reproduction claims wait until the statistical campaign gate in Phase 8; earlier runs are fixtures or pilots with their assessment status explicit.
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
**Plans:** 7/14 plans executed in 8 waves; ready to execute

**Preparatory design (2026-09-26):** [Intervention contracts](phases/05-guided-and-perturbative-bp-interventions/05-DESIGN.md)
and [bounded next tasks](phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md)
are available, with independently checked finite shortening/lifting fixtures.
The Phase 4 dependency is complete. Phase 5 planning passed independent
verification on 2026-09-30; execution is in progress. Source ambiguities
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
- [ ] 05-09-PLAN.md — Plotly package identity and legitimacy gate

**Wave 3** *(blocked on Wave 2 controller completion)*

- [ ] 05-08-PLAN.md — Versioned public manifest, CLI, ledger, and verifier
- [ ] 05-12-PLAN.md — Deterministic BB-144 and HGP algebra and policy fixtures

**Wave 4** *(blocked on public execution)*

- [ ] 05-10-PLAN.md — B1 entitlement, calibration, and sealed cap freeze

**Wave 5** *(blocked on cap freeze)*

- [ ] 05-14-PLAN.md — Bounded matched B1 evaluation

**Wave 6** *(blocked on verified pilot evidence and package gate)*

- [ ] 05-11-PLAN.md — Shot-first notebook and synchronized plots

**Wave 7** *(blocked on executed notebook)*

- [ ] 05-13-PLAN.md — Standalone HTML export and documentation

### Phase 6: Beam Search, Ensembles, and Candidate Selection

**Goal:** A researcher can execute branching/ensemble searches and inspect how candidate generation, pruning, selection, and voting affect outputs and cost.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** MOD-04, INT-05, CAN-01, CAN-02
**Success Criteria:**

1. The controlled CSS BeamSearch/RelayBP comparison has a shared initial BP run, declared damped branch/leg semantics, masked BeamSearch branches, ranking/pruning, width/budgets, candidate selection, source-linked fixtures, and verified work evidence. The original BeamSearch circuit procedure and native reference remain Phase 12–13 targets.
2. Generic branching/ensemble compositions declare member identity, inherited versus independent state, resource limits, and work aggregation without double-counting or hiding discarded paths.
3. List selection preserves candidate origin and eligibility with declared scores/ties; voting defines its object and electorate and validates its final output against original constraints.
4. Researchers can replay a small search tree and account for accepted, rejected, pruned and budget-exhausted paths through the ledger.
5. The first CSS literature set (Yao BPGD, Bhatnagar impulse, and Rabeti–Mahdavifar MBBP-LD) has source-grounded paper-level policy files with explicit runnable/unsupported status. At least one qualified variant per paper runs through the common policy-file command on a bounded CSS study with verified provenance and original-problem checks; full curve assessment remains in Phases 8–9.

**Research focus:** Controlled CSS BeamSearch/RelayBP semantics, voting, search work versus parallel latency, and a small B1 literature-policy execution gate; original circuit reference integration follows in Phases 12–13.
**Plans:** 5/9 plans executed across 6 waves, independently checked in `06-PLAN-CHECK.md`.

- [x] 06-01-PLAN.md
- [x] 06-02-PLAN.md
- [x] 06-03-PLAN.md
- [x] 06-04-PLAN.md
- [x] 06-05-PLAN.md
- [ ] 06-06-PLAN.md
- [ ] 06-07-PLAN.md
- [ ] 06-08-PLAN.md
- [ ] 06-09-PLAN.md

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
**Plans:** TBD

### Phase 8: Reproducible Campaigns and Statistical Assessment

**Goal:** A researcher can run, resume, and statistically assess paired experiments without losing samples, changing stopping semantics, or hiding uncertainty.
**Mode:** mvp
**Depends on:** Phase 7
**Requirements:** LED-05, SIM-01, SIM-02, SIM-03, STAT-01, STAT-02, STAT-03, STAT-04, STAT-05
**Success Criteria:**

1. Matched comparison arms consume identical identified samples regardless of worker/branch count, or replay persisted samples when the backend cannot provide that invariance.
2. The same manifest runs locally and in bounded parallel/HPC jobs; checkpoint/resume and shard merging detect duplicates, incomplete work, and changed configurations/versions.
3. Before launch, the manifest fixes targets, tolerances, interval procedures, comparison families, stopping rules, and pass/fail/inconclusive criteria; imported/digitized targets retain their uncertainty and provenance.
4. Synthetic assessment fixtures cover zero/rare failures, fixed-shot and justified adaptive stopping, batch overshoot, insufficient precision, and paired comparisons.
5. Reports explicitly account for timeout, nonconvergence, partial runs and post-selection, including acceptance probability, conditional denominators, actual work, and environment/timing context.

**Research focus:** Paper-specific precision and budgets, sequential inference, digitization, multiplicity, sample replay, durable shard protocol, and site execution limits.
**Scope carry-forward:** Design future CSS campaigns from a newly prespecified question, precision target, stopping rule and measured budget. The cancelled Phase 4 grid is historical evidence, not a required or automatically funded Phase 8 run.
**Plans:** TBD

### Phase 9: CSS Reproduction and Controlled Comparisons

**Goal:** A researcher can assess the selected published CSS results and compare BP mechanisms under shared conditions with trustworthy uncertainty and cost attribution.
**Mode:** mvp
**Depends on:** Phase 8
**Requirements:** EVAL-01, EVAL-02, EVAL-03
**Success Criteria:**

1. The selected CSS source experiments have pinned faithful configurations and native assessment reports, with original-code/settings gaps retained rather than silently defaulted.
2. Canonical CSS realizations are assessed against declared published targets; source-faithful passes, discrepancies, inconclusive points, and adaptations are distinguishable in the registry.
3. Controlled experiments and ablations share codes/noise/samples and explicit budgets, isolating update/schedule, memory/intervention, search/selection, and optional-fallback effects across eligible compositions.
4. Generated results report outcome classes and aggregate denominators, convergence, iterations, work, runtime and resource context separately, without asserting superiority beyond the observed evidence.

**Research focus:** Final CSS paper/code/rate grid, faithful parameter extraction, meaningful ablation design, precision/power, and cost calibration.
**Scope carry-forward:** Reconsider memory/Relay comparisons alongside other CSS policies only after Phase 8 campaign rules are ready. Size a focused comparison from its scientific question and available compute; do not inherit the cancelled Phase 4 448-shot/14-arm grid by default.
**Plans:** TBD

### Phase 10: Correlated Quaternary Execution

**Goal:** A researcher can decode joint Pauli errors through a canonical quaternary BP kernel with verified correlation semantics and explicitly compatible policies.
**Mode:** mvp
**Depends on:** Phase 9
**Requirements:** QBP-01, QBP-02, QBP-03, QBP-04
**Success Criteria:**

1. A source-defined four-state Pauli kernel uses commutation factors, declared message/numerical conventions, and joint X/Z inference through the shared execution lifecycle.
2. Joint I/X/Y/Z sampling and analytical/small-code fixtures verify Y errors, correlation, prior normalization, and physical-error-rate conventions.
3. The independent code-capacity evaluator correctly classifies quaternary candidates and produces the same outcome meanings as the CSS foundation.
4. Compatible source-backed policy compositions, including quaternary BPGD, execute with traceable semantics; unsupported ports are rejected and new adaptations are labeled.

**Research focus:** Quaternary factor equations, scalar/vector message representations, memory/numeric choices, and policy-specific compatibility derivations.
**Plans:** TBD

### Phase 11: Quaternary Reproduction and Comparisons

**Goal:** A researcher can qualify selected correlated code-capacity results and compare joint versus separate inference on identical physical samples.
**Mode:** mvp
**Depends on:** Phase 10
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

**Execution order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14. Independent plans within a phase may execute in parallel once their dependencies are verified.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Evidence Registry and Native CSS Baseline | 9/9 | Complete    | 2026-09-22 |
| 2. Canonical CSS Execution and Policy Contracts | 16/16 | Complete    | 2026-09-23 |
| 3. Update Rules and Scheduling | 17/17 | Complete    | 2026-09-24 |
| 4. Memory Policies and Relay-BP | 15/15 | Complete    | 2026-09-30 |
| 5. Guided and Perturbative BP Interventions | 7/14 | In Progress|  |
| 6. Beam Search, Ensembles, and Candidate Selection | 1/9 | In Progress|  |
| 7. Optional Postprocessing | 0/TBD | Not started | - |
| 8. Reproducible Campaigns and Statistical Assessment | 0/TBD | Not started | - |
| 9. CSS Reproduction and Controlled Comparisons | 0/TBD | Not started | - |
| 10. Correlated Quaternary Execution | 0/TBD | Not started | - |
| 11. Quaternary Reproduction and Comparisons | 0/TBD | Not started | - |
| 12. Circuit Models and Canonical Integration | 0/TBD | Not started | - |
| 13. Circuit Reproduction and Comparisons | 0/TBD | Not started | - |
| 14. Completed Mapping Study and Journal Evidence | 0/TBD | Not started | - |

---
*Created: 2026-09-21 in approved autonomous mode. 84 requirements assigned to 14 phases; implementation has not started.*
