# Requirements: Policy-Based BP Research Platform for QLDPC Decoding

**Defined:** 2026-09-21
**Core Value:** Make BP decoder differences explicit, reproducible, and fairly comparable through canonical policy execution and published evidence.
**Milestone:** v1.0 — research platform and first journal-paper evidence across CSS code-capacity, correlated quaternary code-capacity, and circuit-level decoding.
**Scope authority:** User-approved PROJECT.md and autonomous workflow preferences. Research-derived safeguards make that scope testable; they do not claim completed implementations or reproduced results.

## v1 Requirements

### Literature mapping

- [x] **MAP-01**: A researcher can inspect a versioned mapping protocol specifying research questions, search sources/queries, date cutoff, inclusion/exclusion, screening/adjudication, snowballing, and extraction procedures.
- [x] **MAP-02**: A researcher can trace each corpus record through deduplication and screening decisions, with source identifiers, paper revisions, decisions, reasons, and search provenance.
- [x] **MAP-03**: A researcher can query a source-linked taxonomy covering kernel, update rule, schedule, state/memory, intervention, stopping, candidate processing, code/noise regime, metrics, implementation, and evidence type, with ambiguities distinguished from established facts.
- [ ] **MAP-04**: A reader can inspect the completed mapping dataset, selection flow/counts, extraction dictionary, limitations, and documented search update through the declared publication cutoff.

### Reproduction registry and reference execution

- [x] **REG-01**: A researcher can validate a machine-readable manifest containing the exact decoder specification; code and logical-operator hashes; noise model; physical-error rates; seed policy; simulation budget/stopping; software/backend versions; expected outputs; statistical/numerical tolerances; source paper/implementation links; and discrepancies or interpretive decisions.
- [x] **REG-02**: A researcher can resolve a versioned manifest to immutable input artifacts and detect schema errors, missing required settings, or mismatched hashes before simulation.
- [x] **REG-03**: A researcher can execute one pinned published binary BP reference from a manifest and obtain a linked ledger and result artifact through a documented local command.
- [x] **REG-04**: A researcher can distinguish mapped-only, reference-executable, canonical-implemented, and statistically assessed evidence for a paper experiment; unavailable original code and unassessed reproduction remain explicit.
- [ ] **REG-05**: Each paper experiment claimed as supported in the release has a complete manifest, executable entry, assessment report, and known-discrepancy record; the supported set and exclusions are explicitly enumerated.

### CSS mathematical and sampling foundation

- [x] **CSS-01**: A researcher can load CSS check matrices and an ordered logical basis, validate dimensions, binary entries, commutation, stabilizer/logical independence and pairing, and detect malformed inputs.
- [x] **CSS-02**: A researcher can reproduce code/logical artifact hashes from a documented serialization preserving matrix shape, ordering, field conventions, and logical-basis identity.
- [x] **CSS-03**: A researcher can generate identified bit-flip code-capacity shots and separate X/Z observations under explicit error-rate and check-orientation conventions, retaining hidden truth for evaluation.
- [x] **CSS-04**: An independent tested evaluator distinguishes syndrome invalidity, exact recovery, non-exact stabilizer-equivalent recovery, and syndrome-valid logical failure on constructed small-code cases.

### Canonical execution model

- [x] **ENG-01**: A researcher can run a canonical binary sum-product BP decoder end to end from a CSS manifest through evaluated outcomes and provenance without delegating its update loop to a third-party decoder.
- [x] **ENG-02**: A researcher can compose explicit update, schedule, state/memory, intervention, stopping, selection, and postprocessing policies under typed lifecycle and compatibility contracts that reject undefined combinations.
- [ ] **ENG-03**: A researcher can configure stopping and budgets at attempt, branch/leg, search, and shot scope and inspect the actual scope and reason that ended execution.
- [x] **ENG-04**: A researcher can inspect and reproduce numerical conventions including probability/LLR encoding, precision, clipping, initialization, normalization, tie-breaking, and message read/write order.
- [x] **ENG-05**: Policy execution cannot access sampled hidden truth, and every candidate transformed from a working problem is lifted and evaluated against the immutable original observation and constraints.
- [x] **ENG-06**: Each implemented policy has source-linked equations or a precise declared procedure plus deterministic small-case/invariant checks independent of aggregate curve matching.

### Additional message-update rules

- [ ] **UPD-01**: A researcher can select min-sum updates with a documented kernel-specific equation and verified small-graph behavior.
- [ ] **UPD-02**: A researcher can select normalized min-sum with explicit normalization parameters and verified small-graph behavior.
- [ ] **UPD-03**: A researcher can select offset min-sum with explicit offset/sign conventions and verified small-graph behavior.

### Scheduling

- [x] **SCH-01**: A researcher can select flooding with explicit old/new-message semantics and defined sweep/edge-work counts.
- [ ] **SCH-02**: A researcher can select layered scheduling with explicit layer membership, order, and fresh-message semantics.
- [ ] **SCH-03**: A researcher can select serial scheduling with a declared update unit, traversal order, and tie behavior.
- [ ] **SCH-04**: A researcher can select residual scheduling with a defined residual, priority invalidation, selection cost, and stopping/work accounting.
- [ ] **SCH-05**: A researcher can select randomized scheduling and replay its order from recorded decoder-local randomness without altering physical-error samples.
- [ ] **SCH-06**: A researcher can select a source-defined cluster-sequential schedule with recorded cluster construction/order and any learned parameters; arbitrary clustering is not mislabeled as a published variant.

### State and memory

- [ ] **MEM-01**: A researcher can enable damping with an explicit equation, parameter, application point, and reset behavior.
- [ ] **MEM-02**: A researcher can enable a precisely specified mixing policy with explicit operands, weights, and application order.
- [ ] **MEM-03**: A researcher can enable a source-defined momentum policy with explicit history state and initialization/reset semantics.
- [ ] **MEM-04**: A researcher can enable a source-defined iteration-memory policy with explicit retained state, lifetime, and update equation.
- [ ] **MEM-05**: A researcher can enable disordered memory with a declared sampling distribution, seed stream, update equation, and inheritance/reset behavior.

### Named BP modifications

- [ ] **MOD-01**: A researcher can execute a source-linked canonical Relay-BP composition with explicit memory, ensemble/relay legs, transferred state, stopping, and candidate selection, and run the pinned original implementation as a reference in eligible regimes.
- [ ] **MOD-02**: A researcher can execute source-defined BPGD as a canonical guided-decimation composition with reliable-variable selection, fixation, BP rounds, and recorded state transitions.
- [ ] **MOD-03**: A researcher can execute source-defined impulse decoding with its failure trigger, shortening attempts, branch budgets, candidate lifting, and selection represented explicitly in the canonical execution model.
- [ ] **MOD-04**: A researcher can execute a source-linked canonical BeamSearch composition with explicit branching, masked BP, beam ranking/pruning, width/budgets, and candidate selection, alongside the pinned original reference where available.

### Additional interventions

- [ ] **INT-01**: A researcher can apply an explicitly defined freezing policy with variable eligibility, fixed value, lifetime, and release/reset rules.
- [ ] **INT-02**: A researcher can apply a source-defined syndrome-flipping intervention while retaining the original syndrome and validating lifted candidates against it.
- [ ] **INT-03**: A researcher can apply a source-defined sign-flipping intervention with explicit target selection, magnitude/sign convention, trigger, and state consequences.
- [ ] **INT-04**: A researcher can configure restarting with explicit reset/preserved state, stopping budget, and independent replayable random streams.
- [ ] **INT-05**: A researcher can compose branching and ensembling with explicit parent/member identity, resource limits, shared versus independent state, and aggregated work.

### Candidate selection

- [ ] **CAN-01**: A researcher can select from a candidate list using declared eligibility, scoring, and deterministic tie rules, preserving rejected candidates and their origins.
- [ ] **CAN-02**: A researcher can apply a precisely defined voting policy over a declared object and eligible set, with final original-problem validity checked rather than assumed.

### Optional postprocessing

- [ ] **POST-01**: A researcher can enable OSD as an optional canonical-BP fallback with explicit reliability inputs, order/method, trigger, and separately recorded work.
- [ ] **POST-02**: A researcher can enable LSD as an optional canonical-BP fallback with explicit reliability inputs, method/order, trigger, and separately recorded work.
- [ ] **POST-03**: A researcher can execute the source-resolved SI procedure with explicit inactivation, BP rerun/solve, candidate reconstruction, and compatibility rules.
- [ ] **POST-04**: A researcher can execute the source-resolved OTF procedure with explicit graph construction/pruning, BP rerun, candidate reconstruction, and compatibility rules.
- [ ] **POST-05**: A researcher can independently disable additional processing or trigger it on declared nonconvergence, retaining BP-only and final outcomes and running pinned native BP-OSD/BP-LSD references without substituting their internal BP for the canonical kernel.

### Event ledger and computational work

- [x] **LED-01**: Every simulated shot produces an identified final record linking the manifest, input/sample, decoder configuration, versions, selected output, termination, outcome, and post-selection status, including unsuccessful and interrupted shots.
- [ ] **LED-02**: Canonical runs record linked control-flow events for attempts, interventions, branches/pruning, relay transfers, candidates, fallback, and selection; per-edge message tracing can be selectively enabled without removing required shot/control-flow evidence.
- [ ] **LED-03**: A researcher can jointly analyze iterations, BP calls/message work, branch/relay work, candidate checks, fallback work, runtime, and parallel-resource context, without equating them to one universal iteration count.
- [ ] **LED-04**: Native-reference results explicitly mark unavailable internal events or counters and their reasons; missing instrumentation is never reported as zero or reconstructed as observed fact.
- [ ] **LED-05**: A researcher can validate and merge durable ledger shards, detect incomplete or duplicate contributions, and reconstruct reported results from the preserved evidence.

### Simulation execution

- [ ] **SIM-01**: Controlled comparison arms receive the same identified physical-error/fault samples, with sample generation independent of decoder randomness, worker count, and branch count, or use persisted samples when a backend cannot guarantee that invariance.
- [ ] **SIM-02**: A researcher can run the same manifest locally or as bounded parallel/HPC jobs while recording resources, timing boundaries, environment, and actual work/budget consumption.
- [ ] **SIM-03**: A researcher can checkpoint and resume a campaign without double-counting shots or silently changing sample identity, stop rules, configuration, or dependency versions.

### Statistical assessment

- [ ] **STAT-01**: Before a campaign, a researcher can declare the output/curve points, effect/tolerance, uncertainty method and level, comparison family, and pass/fail/inconclusive rule in the manifest.
- [ ] **STAT-02**: Analysis retains actual shots and failures and reports valid rare-event uncertainty, including a positive upper bound for zero observed failures rather than an exact zero failure rate.
- [ ] **STAT-03**: Statistical assessment records planned and realized stopping, batch overshoot and partial runs, and uses an uncertainty procedure justified for fixed-shot or adaptive stopping as applicable.
- [ ] **STAT-04**: Reproduction targets preserve source figure/table/data identity and extraction precision, including plot-digitization uncertainty and missing published sample counts where relevant.
- [ ] **STAT-05**: Controlled analyses use paired outcomes where samples are shared and declare denominators/treatment for nonconvergence, timeout, discard and post-selection, reporting acceptance rate alongside conditional performance.

### CSS reproduction and comparison

- [ ] **EVAL-01**: A researcher can run the selected CSS publication experiments under their source settings and inspect native-reference assessments, with code/source gaps and discrepancies explicit.
- [ ] **EVAL-02**: A researcher can assess canonical CSS realizations against selected reported curves using the declared statistical criteria, with source-faithful reproduction distinguished from adaptation and unsupported results not labeled reproduced.
- [ ] **EVAL-03**: A researcher can compare and ablate eligible CSS policies on shared codes/noise/samples and explicit computational budgets, reporting logical outcomes, convergence, iterations, work, runtime, and optional-fallback effects separately.

### Correlated quaternary code-capacity

- [ ] **QBP-01**: A researcher can execute a canonical four-state Pauli BP kernel using source-defined commutation factors, message representation, numerical conventions, and joint X/Z inference.
- [ ] **QBP-02**: A researcher can sample a declared joint I/X/Y/Z channel, including correlated X/Z behavior, and verify priors, error-rate conventions, and Y-error fixtures.
- [ ] **QBP-03**: Quaternary outputs pass independent syndrome, exact/degenerate/logical-outcome checks against the common code-capacity mathematical conventions.
- [ ] **QBP-04**: A researcher can run source-backed compatible policy compositions in the quaternary kernel, including the published quaternary BPGD case, with unsupported ports explicitly rejected or labeled new adaptations.
- [ ] **QEV-01**: A researcher can execute selected quaternary source experiments and assess canonical reproduction within declared statistical tolerances, preserving reference availability and discrepancy records.
- [ ] **QEV-02**: A researcher can compare joint quaternary and separate binary decoding on the same sampled joint Pauli channel and declared budgets, with source-backed policy ablations and provenance.

### Circuit-level decoding

- [ ] **CIR-01**: A researcher can load and hash a noisy syndrome-extraction circuit, round/boundary conventions, detector/fault representation, observable map, and extraction settings as a typed circuit problem.
- [ ] **CIR-02**: An independent evaluator scores predicted logical-observable flips against circuit truth and separately checks detector fit when defined, using injected-fault fixtures and explicit not-applicable static-recovery fields.
- [ ] **CIR-03**: A researcher can execute eligible canonical policies on circuit problems through a kernel compatible with the declared factors, reusing binary parity updates only where mathematically justified.
- [ ] **CIR-04**: A researcher can execute pinned source circuit-decoder references on matched observation records with documented input/output translations and observability limits.
- [ ] **CIR-05**: Circuit manifests explicitly preserve or identify approximations to dependent/exclusive/correlated fault mechanisms; graph conversion cannot silently change the simulated noise claim.
- [ ] **CEV-01**: A researcher can run selected published circuit experiments and inspect native-reference reproduction assessments under source-faithful settings.
- [ ] **CEV-02**: A researcher can assess canonical circuit realizations against the selected published outputs within declared statistical tolerances, including discrepancies and inconclusive outcomes.
- [ ] **CEV-03**: A researcher can compare and ablate eligible circuit policies on shared samples and declared work/resources while reporting observable failure, convergence, work, runtime distributions, and post-selection separately.

### Documentation and publication

- [ ] **DOC-01**: A researcher can follow an install/run tutorial and inspect mathematical conventions, policy contracts, compatibility, and executable small examples as the canonical engine develops.
- [ ] **DOC-02**: A researcher can follow detailed reproduction and extension guides covering reference environments, manifests, sample/ledger schemas, statistical procedures, HPC execution, and known discrepancies.
- [ ] **PUB-01**: Every manuscript table/figure and quantitative claim links to versioned analysis, experiment manifests, result/ledger artifacts, uncertainty, and an explicit evidence status.
- [ ] **PUB-02**: The journal manuscript reports the completed systematic map, canonical policy model, reproducibility study, and controlled results from all three decoding regimes, including limitations and unsuccessful/inconclusive reproductions.
- [ ] **PUB-03**: An accessible release bundle contains the documented software, mapping dataset, supported experiment registry, environment specifications, analysis recipes, and artifact integrity inventory needed to reproduce the reported evidence.

## v2 Requirements

No user-requested decoder family or decoding regime is deferred beyond the first journal milestone. Future capabilities will be scoped separately; implementation order does not change publication scope.

## Out of Scope

| Feature or claim | Reason |
|------------------|--------|
| Shared API as the sole canonical abstraction | Does not expose comparable policy semantics |
| Arbitrary policy combinations across all kernels | Requires mathematical compatibility and source-grounded semantics |
| Mandatory bitwise/trajectory equality with native decoders | Statistical agreement with reported curves is the approved reproduction standard |
| Automatic claims that matching curves prove mechanism equivalence | Requires separate source-level and small-case validation |
| Always-on OSD/LSD | User requires optional processing for nonconvergence and BP-first attribution |
| All mapped papers automatically counted as executable reproductions | The supported set must be explicitly selected and qualified |
| Automatic journal submission or external publication | Deliver a reviewable manuscript/release bundle; venue and submission action are not yet specified |
| Mandatory GPU, immediate compiled rewrite, or hosted web service | No established requirement; optimize or add interfaces only when justified by the research workflow |

## Acceptance Criteria and Definition of Done

Requirements are complete only after implementation, relevant verification, and committed evidence. Curves are assessed using preregistered manifest criteria: a discrepancy report preserves scientific evidence but does not convert a failed or inconclusive reproduction into a pass. Any supported result promoted as reproduced must pass its stated criterion. Source-code absence or missing paper parameters must remain visible.

All named requested mechanisms require precise source-linked or explicitly declared specifications and eligible executable realizations; recording an unresolved name in the map does not satisfy an implementation requirement. Not every policy must run in every kernel. An adaptation is labeled and assessed separately from faithful reproduction. The final supported paper/experiment list, code families/sizes, numerical thresholds, and compute budgets are finalized before their corresponding campaigns, with changes versioned and justified.

Documentation, algebraic correctness checks, provenance, and evidence status accompany each working slice. The publication milestone requires completed experiments in all three regimes and a final mapping-study audit. Journal acceptance is an external outcome, not a software verification criterion.

## Traceability

Every v1 requirement has exactly one owning phase; later phases may use or strengthen it without changing ownership.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MAP-01 | Phase 1 | Complete |
| MAP-02 | Phase 1 | Complete |
| MAP-03 | Phase 1 | Complete |
| MAP-04 | Phase 14 | Pending |
| REG-01 | Phase 1 | Complete |
| REG-02 | Phase 1 | Complete |
| REG-03 | Phase 1 | Complete |
| REG-04 | Phase 1 | Complete |
| REG-05 | Phase 14 | Pending |
| CSS-01 | Phase 1 | Complete |
| CSS-02 | Phase 1 | Complete |
| CSS-03 | Phase 1 | Complete |
| CSS-04 | Phase 1 | Complete |
| ENG-01 | Phase 2 | Complete |
| ENG-02 | Phase 2 | Complete |
| ENG-03 | Phase 2 | Pending |
| ENG-04 | Phase 2 | Complete |
| ENG-05 | Phase 2 | Complete |
| ENG-06 | Phase 2 | Complete |
| UPD-01 | Phase 3 | Pending |
| UPD-02 | Phase 3 | Pending |
| UPD-03 | Phase 3 | Pending |
| SCH-01 | Phase 2 | Complete |
| SCH-02 | Phase 3 | Pending |
| SCH-03 | Phase 3 | Pending |
| SCH-04 | Phase 3 | Pending |
| SCH-05 | Phase 3 | Pending |
| SCH-06 | Phase 3 | Pending |
| MEM-01 | Phase 4 | Pending |
| MEM-02 | Phase 4 | Pending |
| MEM-03 | Phase 4 | Pending |
| MEM-04 | Phase 4 | Pending |
| MEM-05 | Phase 4 | Pending |
| MOD-01 | Phase 4 | Pending |
| MOD-02 | Phase 5 | Pending |
| MOD-03 | Phase 5 | Pending |
| MOD-04 | Phase 6 | Pending |
| INT-01 | Phase 5 | Pending |
| INT-02 | Phase 5 | Pending |
| INT-03 | Phase 5 | Pending |
| INT-04 | Phase 5 | Pending |
| INT-05 | Phase 6 | Pending |
| CAN-01 | Phase 6 | Pending |
| CAN-02 | Phase 6 | Pending |
| POST-01 | Phase 7 | Pending |
| POST-02 | Phase 7 | Pending |
| POST-03 | Phase 7 | Pending |
| POST-04 | Phase 7 | Pending |
| POST-05 | Phase 7 | Pending |
| LED-01 | Phase 1 | Complete |
| LED-02 | Phase 2 | Pending |
| LED-03 | Phase 2 | Pending |
| LED-04 | Phase 2 | Pending |
| LED-05 | Phase 8 | Pending |
| SIM-01 | Phase 8 | Pending |
| SIM-02 | Phase 8 | Pending |
| SIM-03 | Phase 8 | Pending |
| STAT-01 | Phase 8 | Pending |
| STAT-02 | Phase 8 | Pending |
| STAT-03 | Phase 8 | Pending |
| STAT-04 | Phase 8 | Pending |
| STAT-05 | Phase 8 | Pending |
| EVAL-01 | Phase 9 | Pending |
| EVAL-02 | Phase 9 | Pending |
| EVAL-03 | Phase 9 | Pending |
| QBP-01 | Phase 10 | Pending |
| QBP-02 | Phase 10 | Pending |
| QBP-03 | Phase 10 | Pending |
| QBP-04 | Phase 10 | Pending |
| QEV-01 | Phase 11 | Pending |
| QEV-02 | Phase 11 | Pending |
| CIR-01 | Phase 12 | Pending |
| CIR-02 | Phase 12 | Pending |
| CIR-03 | Phase 12 | Pending |
| CIR-04 | Phase 12 | Pending |
| CIR-05 | Phase 12 | Pending |
| CEV-01 | Phase 13 | Pending |
| CEV-02 | Phase 13 | Pending |
| CEV-03 | Phase 13 | Pending |
| DOC-01 | Phase 2 | Pending |
| DOC-02 | Phase 14 | Pending |
| PUB-01 | Phase 14 | Pending |
| PUB-02 | Phase 14 | Pending |
| PUB-03 | Phase 14 | Pending |

**Coverage:**

- v1 requirements: 84 total
- Mapped to phases: 84
- Unmapped: 0
- Duplicate phase owners: 0

---
*Requirements defined: 2026-09-21*
*Last updated: 2026-09-21 after roadmap traceability assignment; autonomous mode*
