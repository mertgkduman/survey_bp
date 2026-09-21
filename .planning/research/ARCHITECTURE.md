# Architecture Research: Policy-Based BP for QLDPC Decoding

**Domain:** Scientific decoding platform and executable literature registry  
**Researched:** 2026-09-21  
**Confidence:** MEDIUM overall (primary papers and official implementations support the mathematical boundaries; lifecycle, data schemas, and build order below are explicit design proposals that still need validation).

## Architectural decision

Build a **shared experiment and evidence plane** around **one canonical execution engine per compatible BP kernel family**. The first engine handles binary parity constraints on binary error variables. It serves separate CSS code-capacity components and, later, independent-fault circuit detector models when their assumptions match. The second engine handles four-state Pauli variables with commutation constraints and joint X/Z priors. Both implement the same *policy lifecycle and trace vocabulary*, but their message types, factor rules, candidate types, and outcome semantics remain typed. A third kernel should be added only when a source-defined circuit correlation or factorization cannot be represented faithfully by either. This is a proposal, not a claim that all published methods are interchangeable. Rigby et al. explicitly contrast separate binary CSS decoding with GF(4) decoding because the former loses X/Z error correlation; Stim defines a circuit detector error model in terms of detector symptoms and observable frame changes of independent error mechanisms. [Rigby et al.](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.100.012330) [Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md)

### System overview

    Literature map ──> paper / claim / figure registry ──> versioned reproduction manifests
                                                        │
    Code + logical operators ──> model compiler ────────┼──> experiment planner
    Circuit + detector model ──> model compiler ─────────┘            │
                  │                                                    │
                  ├── binary parity BP engine <── typed policies ─────┤
                  └── quaternary Pauli BP engine <─ typed policies ────┤
                                                                       │
    Pinned third-party decoder adapters <── identical sample stream ──┤
                  │                                                    │
                  └──────────────> candidate / prediction events <────┘
                                          │
                              regime-specific evaluator
                                          │
                        shot ledger + optional batched trace store
                                          │
                 statistical reproduction + controlled comparison
                                          │
                             tables, figures, manuscript links

The top-level runner owns sampling, budget, provenance, and evaluation. Engines own mathematically valid message passing and emit candidates and events. Reference adapters own calls into pinned third-party implementations; they do not become the canonical engine by satisfying a common API. This preserves published baselines while letting policy compositions be inspected. The official LDPC package exposes BP+OSD and BP+LSD decoders, while the Relay-BP repository exposes its Rust/Python implementation and optional Stim/Sinter integration. [LDPC documentation](https://software.roffe.eu/ldpc/quantum_decoder.html) [Relay-BP repository](https://github.com/trmue/relay)

## Mathematical and semantic boundaries

| Regime / representation | Observation and latent variable | Canonical engine | Candidate and success contract |
|---|---|---|---|
| CSS code capacity, first | For a Pauli error (eX,eZ), measured sZ = HZ eX and sX = HX eZ over GF(2); start with bit flips and perfect checks. | Binary parity BP, run once per selected component. | Estimated Pauli recovery (cX,cZ); validate against the *original* checks, then classify residual error by stabilizer and logical action. |
| Correlated quaternary code capacity, second | Each qubit has I/X/Y/Z prior; a stabilizer check reports Pauli commutation parity. X and Z components of a Y event share one variable and one joint prior. | Four-state Pauli BP with an explicit commutation factor and four-state messages. | Estimated Pauli recovery; same stabilizer/logical classification as code capacity. A binary CSS run on marginalized priors is a comparison arm, not a faithful quaternary realization. |
| Circuit level, third | Noisy syndrome-extraction circuit produces detection events d; a supported independent-fault detector model maps fault vector f to detector flips d = HD f and observable flips o = HO f. | Binary parity BP only for the declared independent-fault factorization; retain a typed circuit problem and output contract. | Prediction of observable flips, optionally with a fault candidate. Judge logical prediction against sampled observable truth. Detector fit is defined only when a fault candidate exists. Static Pauli recovery and stabilizer degeneracy labels do not automatically apply. |

CSS construction must check HX HZ-transpose = 0 and record which rows detect which Pauli component. A matching syndrome is necessary but not sufficient for logical success: with true error e and proposed recovery c, the residual e+c can commute with all checks yet be a nontrivial logical operator. For code-capacity shots, define mutually exclusive final classes: **invalid syndrome**, **exact recovery** (residual identity), **degenerate recovery** (nonidentity residual in the stabilizer), and **logical failure** (syndrome-valid residual with nontrivial logical action). Keep raw BP convergence separate from the final class. This algebraic classification is a proposed contract to test against small codes and independent linear algebra. [Roffe et al.](https://arxiv.org/abs/2005.07016) [Poulin and Chung](https://authors.library.caltech.edu/records/fgska-n5w47)

For circuit shots, the ground truth is an observable-flip vector produced by the sampled circuit or fault model; a decoder may return only its predicted vector. If it also returns f-hat, record whether HD f-hat equals d and whether HO f-hat equals the prediction. Exact fault match may be recorded when the simulator exposes f, but is not the same as exact data-Pauli recovery. Circuit “degenerate recovery” stays **not applicable** until a circuit-specific equivalence relation is defined and validated. Stim's DEM documentation and the BP+LSD paper support the detector/observable distinction; the detailed ledger schema is our inference. [Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md) [Hillmann et al.](https://www.nature.com/articles/s41467-025-63214-7)

**Circuit-model caveat:** a DEM represents independent error mechanisms. A circuit channel with exclusive or otherwise dependent faults may require a documented approximation or a new factor representation. Record Stim extraction flags, fault decomposition, correlations lost, and any graph augmentation as part of the model identity. A detector graph built from a simplified code-capacity circuit does not establish circuit-level noise coverage. [Stim command reference](https://github.com/quantumlib/Stim/blob/main/doc/usage_command_line.md) [Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md)

## Components and ownership

| Component | Owns | Contract / boundary |
|---|---|---|
| Literature registry | Paper identifiers, publication version, mechanisms, claims, figures/tables, source code links, ambiguity notes | A paper can map to multiple experiment manifests; each claimed reproduction links back to a precise source item. |
| Model compiler | Ordered sparse checks, Pauli factors, priors, logical basis, or circuit and detector/observable maps | Reject invalid CSS commutation and shape mismatches; produce a typed immutable model with semantic hashes. |
| Compatibility checker | Kernel capabilities and policy preconditions | Resolve composition before a run; reject unsupported transforms or explicit combinations with conflicting state ownership. |
| Canonical kernel | Edge/factor message math, numerical domain, hard decisions | No experiment sampling or paper-specific defaults hidden inside. Binary and quaternary kernels are separate. |
| Policy controller | Schedule, memory/state, intervention, stopping, candidate selection, postprocessing hooks | Explicit lifecycle, reset/branch/relay behavior, random substreams, and provenance events. |
| Reference adapters | Pinned third-party decoders such as LDPC BP+OSD/BP+LSD and Relay-BP | Translate inputs/outputs and report observability limits; reference runs do not imply mechanism equivalence. |
| Experiment runner | Deterministic sample allocation, pairing, budgets, checkpoints, HPC batching | Same observation/truth stream for eligible controlled arms; faithful runs keep published settings. |
| Evaluator and ledger | Validity, exact/degenerate/logical outcomes, termination, work, timing, post-selection | Evaluate against the original problem, not an internally flipped/shortened/branched surrogate. |
| Analysis layer | Intervals, curve/tolerance checks, paired contrasts, figure generation | Never infer algorithmic identity from finite performance agreement. |

## Common execution lifecycle: a proposed contract

1. **Compile and validate.** Bind a typed problem, immutable original constraints, priors, observables/logical basis, numerical precision, and declared factorization. Run the compatibility checker before sampling.
2. **Allocate shot.** Receive immutable observation, hidden truth for evaluation only, shot ID, a decoder-local random substream, work budget, and trace policy. The decoder cannot inspect truth.
3. **Initialize attempt.** Create per-attempt messages, beliefs, scheduler state, policy memory, and intervention state. Record attempt, parent branch, and origin. “Warm” state inheritance must be explicit.
4. **Schedule updates.** A scheduler chooses current edges/checks/variables or a cluster using its declared stale/fresh-message semantics. The kernel computes updates; state transforms such as damping, mixing, momentum, or iteration memory apply in a documented order. A single owner commits each message write.
5. **Intervene at declared hooks.** Decimation/freezing may restrict variables or priors; syndrome or sign flips may modify a working problem; restart may reset state; branch/beam/impulse may fork work; relay may transfer selected posterior state. Each intervention declares whether it changes only beliefs, the working constraints, or the search tree, and what it invalidates (residual priorities, cluster partitions, cached checks).
6. **Emit candidate and validate.** On specified hooks, form a hard decision or source-defined candidate. Check it against the *unmodified* observation and original constraints, score it under a declared objective, and record its origin. A candidate from a flipped working syndrome is not accepted just because it fits that temporary syndrome.
7. **Stop at a named scope.** Attempt, relay leg, branch, search, and shot have distinct iteration/work/valid-candidate limits. Stop reason records the scope and trigger. A branch exhausting its budget must not silently terminate the shot if siblings remain.
8. **Select.** Choose from original-problem-valid candidates using a declared rule (first, score, list, vote, paper-specific). Define tie breaks and whether votes must be projected back onto valid candidates. Keep rejected/invalid candidates in the trace.
9. **Optional fallback and evaluate.** Only when the declared BP/search convergence condition fails, optionally invoke OSD/LSD-style algebraic postprocessing with its own budget and parameters. Keep its result and work separate from the BP-only result. Evaluate the selected final output using regime-specific truth and record one final shot ledger row.

The source-backed reason for separating attempt and shot scopes is concrete: Relay-BP runs a preliminary leg and multiple ensemble legs, can stop after a target number of converged solutions, and may choose among them; its repository documents a worst-case iteration bound across legs. Guided decimation fixes reliable qubits sequentially, while BeamSearch uses a tunable beam width. Those are distinct control flows over BP, not synonyms for a single maximum-iteration setting. [Relay-BP paper](https://arxiv.org/abs/2506.01779) [Relay-BP implementation](https://github.com/trmue/relay) [Yao et al.](https://arxiv.org/abs/2312.10950) [Ye et al.](https://journals.aps.org/prxquantum/abstract/10.1103/6k5x-ztqt)

### Policy compatibility, not a free Cartesian product

| Policy dimension | Interface and examples | Compatibility gate |
|---|---|---|
| Message update | Sum-product, min-sum, normalized/offset min-sum | Bind update equations to binary or four-state message algebra; a binary min-sum function is not a quaternary update merely because both are called BP. |
| Schedule | Flooding, layered, serial, residual, randomized, cluster-sequential | Declare atomic update unit, fresh/stale reads, priority invalidation, deterministic tie break, and whether clusters overlap. Residual selection requires comparable residual definition for the kernel and state transform. |
| State/memory | Damping, mixing, momentum, iteration memory, disordered memory | Define storage lifetime, transform order, reset/relay semantics, numeric bounds, and whether multiple transforms are mathematically composed or mutually exclusive. |
| Intervention | Decimation, freezing, syndrome/sign flip, graph augmentation, restart, relay, branch/beam, impulse | Declare trigger (iteration, oscillation, BP failure), working-problem transformation, candidate lift back to original variables, and whether factor updates are still valid. Failure-triggered impulse shortening is an internal BP/search controller, not automatically OSD/LSD postprocessing. |
| Candidate / stop | First valid, minimum declared cost, list selection, voting; per-scope caps | Validate against original constraints and only compare scores on identical objective/noise model. Define eligibility for “converged”, target number of valid solutions, and tie breaks. |
| Nonconvergence recovery | OSD/LSD algebraic solvers; SI inactivation followed by message passing and a small solve; OTF graph pruning followed by BP | Independent enable flag, trigger, and budget per method. These methods share a failure hook but do not share one mathematical operation or output contract. |

Published names need *source-specific specifications*, not generic switches. Relay-BP combines disordered memory, ensembling, and relaying. BPGD changes beliefs by guided fixation. The 2026 impulse paper presents parallel decoder-side shortening after BP failure; the architecture should preserve that trigger and the lift back to the original problem. BeamSearch needs search-tree/beam accounting and a source-defined ranking. SI is explicitly called a postprocessing method by its authors, but it inactivates variables, reruns message passing, and solves a small linear system; OTF prunes to a forest and reruns BP. Both therefore need controller events as well as fallback accounting. These are policy compositions to research one by one; finite benchmark agreement cannot prove that a canonical realization implements the same algorithm. [Müller et al.](https://arxiv.org/abs/2506.01779) [Yao et al.](https://arxiv.org/abs/2312.10950) [Bhatnagar et al.](https://arxiv.org/abs/2606.18240) [Ye et al.](https://journals.aps.org/prxquantum/abstract/10.1103/6k5x-ztqt) [BeamSearch implementation](https://github.com/ionq-publications/BeamSearchDecoder) [du Crest et al., SI](https://arxiv.org/abs/2205.06125) [deMarti iOlius et al., OTF](https://arxiv.org/abs/2409.01440)

## Data and provenance flow

### Registry and manifest

A versioned manifest should bind **one paper experiment/figure item** to the model, code/logical identity, exact decoder specification, noise model and rates, sample and decoder seed policies, stop/budget rules, software/backend versions, expected outputs, statistical/numerical tolerances, and known interpretive decisions. Registry entries connect paper → mechanism → source implementation → faithful manifest → canonical hypothesis → produced run IDs. Missing published parameters remain marked unresolved rather than silently defaulted.

**Proposed hashing contract:** serialize matrices with shape, GF(2) bit packing/endian, row and column order, Pauli X/Z convention, and generator order; hash the bytes with SHA-256. Separately hash an ordered, paired logical basis and its sign/convention metadata. Equivalent row spaces or logical bases can have different hashes, which is desirable for exact reproduction; record any explicit basis transform when comparing them. For circuits hash the exact annotated circuit/noise schedule, DEM extraction options and output, detector/observable index map, and round/window definition. Hash source artifacts separately from software and decoder-version identifiers. Verify hash stability with round-trip fixtures before declaring the format canonical. These serialization choices are design proposals, not paper-established standards.

### Deterministic samples and reference runs

Give every shot a stable identity (campaign, model hash, noise point, shot index). Derive its **physical error/fault sample** independently of decoder, worker count, batching, and branch count, preferably through counter-based keyed streams or materialized sample shards. Derive intervention randomness from a separate decoder-local stream keyed by shot, policy, attempt, and branch. This permits paired controlled comparisons without perturbing error sampling when a decoder changes its internal random draws. For a third-party simulator whose seeded batching is not guaranteed to be invariant, store the actual observation plus truth/sample fingerprint, and pin simulator version and batch settings. Stim's command documentation explicitly warns that a seed may not reproduce across all flags and modes; the sample-file strategy is a proposed mitigation. [Stim CLI reference](https://github.com/quantumlib/Stim/blob/main/doc/usage_command_line.md)

Run faithful reproductions under published settings and controlled comparisons under shared eligible models, observations, and explicit budgets. Reference adapters normalize *outputs and metadata*, not internal policy events they cannot expose. Mark unknown work counters as unavailable, never zero. Preserve reference version/commit, command/config, environment, numerical precision, and adapter translation. A reference result can validate empirical curve reproduction; policy-level mechanism claims additionally require equations, source inspection, and focused invariants.

### Event ledger and traces

Write a compact **one-row-per-shot final ledger** even when a run stops early, is post-selected, or errors. Include run/manifest/model hashes; regime; shot/sample IDs; decoder and policy graph IDs; raw BP convergence and first-valid iteration; final validity/outcome fields with explicit not-applicable values; selected candidate ID and source (BP, branch, relay, fallback); stop scope/reason; post-selection eligibility/discard reason; budgets consumed; work counters; walltime and hardware/process context. Reference adapters may omit inaccessible intermediate counters with a documented missingness reason.

Store **append-only event records** for attempt start/end, policy intervention, branch fork/prune, relay transfer, candidate emission/validation, fallback call, and final selection. Parent IDs make attribution possible: a candidate and its work belong to a branch/relay leg, while the shot totals all attempts. Full per-edge message traces should be opt-in, batched/compressed, and sampled or failure-triggered; do not make them mandatory at HPC scale. The ledger remains mandatory for every shot.

Report computational work as a **vector**, not a single “iteration” count: variable-to-check and check-to-variable updates, factor/edge visits, syndrome validations, branch expansions, belief recomputations, and fallback operations (e.g. elimination work), with backend-specific precision and parallelism. Record wall-clock decode latency and throughput separately, including timing boundary, warm-up, batching, hardware, and queueing policy. A flooding sweep, residual update, and beam expansion are not equal-cost “iterations”. A calibrated aggregate cost may be added later only alongside raw counters.

### Statistical reproduction contract

Persist shot counts, error counts, exclusions/post-selection denominators, and the stopping rule per point. For fixed-shot binomial logical-error estimates report an interval with declared method/level; for zero observed failures report an upper bound rather than zero error rate. If collection stops on an error count or other adaptive rule, choose an interval or likelihood procedure valid for that stopping rule rather than treating the final sample size as fixed without review. A paper curve match needs predeclared per-point or family-level tolerance, treatment of digitized figures and unknown counts, and enough power at the rare-error tail. Controlled arms on the same samples should analyze paired outcomes (e.g. paired difference with uncertainty), while faithful reproduction may require unpaired comparison. Post-selection must remain visible in the denominator. These are proposed analysis requirements, motivated by Sinter's documented shot/error caps and postselection fields; they are not a claim that any cited paper uses the same acceptance test. [Sinter CLI](https://github.com/quantumlib/Stim/blob/main/doc/sinter_command_line.md) [Sinter API](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md)

## Proposed project structure

    src/
      domain/          immutable CSS, Pauli, circuit, and outcome types
      models/          matrix/circuit import, validation, canonical serialization
      kernels/         binary and quaternary BP engines
      policies/        typed schedule, state, intervention, stop, selection contracts
      controllers/     decimation, relay, branch/beam, impulse orchestration
      postprocess/     optional algebraic fallback modules
      references/      pinned third-party decoder adapters
      simulation/      sample streams, runner, work accounting, checkpoints
      evidence/        registry, manifests, ledger, statistics, reports
    experiments/       machine-readable faithful and controlled manifests
    tests/             algebraic invariants, policy composition, sample replay
    docs/              mathematical conventions and discrepancies

The split follows mathematical ownership. Kernels never choose paper defaults; policies never decide logical success; adapters never claim to be canonical; the evaluator never changes a candidate. A monolithic decoder class would hide precisely the distinctions the project aims to study.

## Dependency-aware build order

1. **Evidence and algebra foundation:** literature/figure registry, manifest schema, CSS matrices and logical-basis validation, canonical hashes, deterministic sample identity, outcome oracle, ledger schema. Use small exact cases to test syndrome, stabilizer, and logical classifications before any performance result.
2. **Binary CSS vertical slice:** canonical binary BP, baseline updates and flooding/serial scheduling, raw convergence and work counters, optional OSD/LSD fallback, pinned LDPC reference adapter, bit-flip curves. Extend to residual/randomized/cluster schedules and state policies only after lifecycle invariants are tested.
3. **Intervention and search slice:** source-specific BPGD, Relay-BP, impulse, and BeamSearch contracts/compositions, reference execution where available, branch/relay attribution, controlled paired comparison. Some named methods have circuit-first evidence; code-capacity adaptations must be labeled as adaptations and not faithful reproduction.
4. **Quaternary code-capacity slice:** four-state Pauli/commutation kernel, joint-prior sampling, correlated X/Z checks, compatible policies, source-backed quaternary reproductions, and comparisons to separate CSS decoding. Do not implement it as two coupled binary decoders without proving the exact factorization.
5. **Circuit slice:** annotated extraction circuits, detector/observable model and hashes, original-model outcome evaluator, Stim/Sinter integration, reference adapters and source-defined circuit experiments. Validate independent-fault assumptions and approximation choices before claiming circuit-level reproduction.
6. **Publication evidence gate:** every required paper item has a pinned manifest and discrepancy report; all three regimes have validated experiments, uncertainty, work/timing definitions, archived ledger, and traceable manuscript figures. The first journal milestone requires all three regimes; the sequence is a dependency order, not permission to omit later stages.

## Concrete risks and unresolved semantics

| Risk / open decision | Consequence | Phase gate or resolution |
|---|---|---|
| Compatibility overclaim across binary, quaternary, and circuit factors | “Same policy” can mean different equations or approximations. | Type capabilities and source-derive each kernel-specific rule; test allowed and rejected compositions. |
| Schedule and state ordering changes a named method | Flooding vs layered reads, damping location, and memory reset alter trajectories. | Specify read/write and reset contracts and compare source equations plus small deterministic traces; curves alone are insufficient. |
| Working-syndrome or shortening intervention leaks into validation | False “convergence” against altered constraints. | Original problem remains immutable; candidate lift and original validation are mandatory. |
| Branch/restart/relay work disappears from metrics | Unfair cost comparison and wrong stop attribution. | Parent-linked event ledger and per-attempt work accounting. |
| Circuit DEM discards channel exclusivity/correlation | Misleading physical-noise claim. | Preserve circuit and DEM generation options; document approximation or use richer factors. |
| Observable prediction is labeled static recovery | Incorrect exact/degenerate/logical classification. | Regime-specific outcome schema with not-applicable fields; circuit truth is observable flips. |
| Rare logical failures and stopping rules distort a curve comparison | Spurious reproduction agreement/disagreement. | Predeclare tolerance, denominators, confidence method, shot/error caps, and treatment of zero counts. |
| Acronym or trigger details are guessed | Wrong canonical mechanism. | SI and OTF are identified in their papers, but pin paper versions, source implementations, and exact trigger/output contracts; distinguish BP reruns from algebraic solves. |
| No verified original impulse implementation identified yet | Adapter cannot establish source-code parity. | Treat paper equations as source; record lack of reference implementation as an explicit gap. |

## Sources and confidence

The **mathematical boundary and circuit observation claims** are cross-checked against primary papers and official formats and carry **MEDIUM** confidence under the configured websearch confidence classifier with verification. The **component split, lifecycle, hashing, ledger, and phase gates** are reasoned architecture proposals with **MEDIUM** design confidence, pending algebraic and empirical validation. Specific per-method policy equivalence remains **LOW** until paper equations and original source code are pinned and tested; finite benchmark matching does not raise that to mathematical equivalence.

- [Rigby et al., modified GF(4)/binary CSS BP (2019)](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.100.012330)
- [Poulin and Chung, iterative sparse quantum decoding (2008)](https://authors.library.caltech.edu/records/fgska-n5w47)
- [Roffe et al., BP+OSD QLDPC landscape (2020)](https://arxiv.org/abs/2005.07016) and [LDPC official documentation](https://software.roffe.eu/ldpc/quantum_decoder.html)
- [Kuo and Lai, quaternary memory BP (2022)](https://www.nature.com/articles/s41534-022-00623-2)
- [Yao et al., guided decimation (2023/2024)](https://arxiv.org/abs/2312.10950)
- [Hillmann et al., BP+LSD and detector fault matrix (2025)](https://www.nature.com/articles/s41467-025-63214-7)
- [Müller et al., Relay-BP (2025)](https://arxiv.org/abs/2506.01779) and [original implementation](https://github.com/trmue/relay)
- [deMarti iOlius et al., BP+OTF (2024)](https://arxiv.org/abs/2409.01440)
- [du Crest et al., stabilizer inactivation (2022/2023)](https://arxiv.org/abs/2205.06125)
- [Bhatnagar et al., impulse decoding (2026 preprint)](https://arxiv.org/abs/2606.18240)
- [Ye et al., BeamSearch (2026)](https://journals.aps.org/prxquantum/abstract/10.1103/6k5x-ztqt) and [original implementation](https://github.com/ionq-publications/BeamSearchDecoder)
- [Stim detector error model specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md), [Stim command reference](https://github.com/quantumlib/Stim/blob/main/doc/usage_command_line.md), and [Sinter collection reference](https://github.com/quantumlib/Stim/blob/main/doc/sinter_command_line.md)

---
*Architecture research for the policy-based BP QLDPC platform; reviewed 2026-09-21.*
