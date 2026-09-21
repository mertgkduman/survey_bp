# Project Research Summary

**Project:** Policy-Based BP Research Platform for QLDPC Decoding
**Domain:** Scientific decoder software, systematic literature mapping, and executable reproduction
**Researched:** 2026-09-21
**Confidence:** MEDIUM overall; source identities and broad mechanisms are grounded in primary papers and official projects, while exact policy contracts, numerical settings, and publication experiment selection require phase research.

## Executive Summary

Build an inspectable, installable research package with a common experiment and evidence layer, plus a canonical execution engine for each mathematically compatible BP kernel family. The initial binary parity engine serves separate CSS X/Z decoding. A subsequent four-state Pauli engine preserves joint X/Z priors. Circuit-level support introduces explicit circuit, detector, fault, and logical-observable contracts; reuse the binary kernel only where the declared factorization permits it. Sharing a lifecycle does not make all equations or policies interchangeable.

Prioritize source-defined BP modifications: Relay-BP, BPGD, impulse decoding, and BeamSearch. Published implementations remain independently executable references. The canonical implementation must expose the source-linked transitions, reset and inheritance rules, candidate selection, and stopping scopes of each mechanism. Curve agreement is the reproduction standard, but it does not establish policy correctness by itself. OSD/LSD and the source-resolved SI/OTF methods remain configurable additional processing, with BP-only outcomes and costs preserved.

Develop CSS code-capacity, correlated quaternary code-capacity, and circuit-level evidence in that order, with all three required for the first journal milestone. Start the mapping protocol, manifests, sample identity, correctness oracle, and ledger in the first working slices; complete the systematic map and publication campaigns later. This research is an initial source-backed scoping pass, not a completed systematic mapping study or any reproduced result.

## Key Findings

### Recommended Stack

Use Python with NumPy/SciPy for the first interpretable kernels and orchestration, versioned JSON manifests with schema validation, and typed per-job columnar ledgers for scalable analysis. Keep reference environments separate where dependencies or versions differ. Add Stim/Sinter at the circuit stage, preserving the platform's own shot/event ledger. Add compiled kernels only after profiling shows the need and the same behavioral contract can be verified. These are implementation recommendations to validate on the HPC environment, not installed or locked dependencies. See [STACK.md](STACK.md).

The `ldpc` package is a candidate reference for BP, BP-OSD, and BP-LSD. Its documentation and release/API versions need explicit alignment; an integrated BP-plus-postprocessor object must not be assumed to expose a standalone postprocessor suitable for canonical BP beliefs. Pin the chosen artifact and inspect/test its exact interface. [LDPC source](https://github.com/quantumgizmos/ldpc), [quantum-decoder documentation](https://software.roffe.eu/ldpc/quantum_decoder.html).

### Expected Features and Source Anchors

| Mechanism | Source-established anchor | Planning consequence |
|---|---|---|
| Relay-BP | [Paper](https://arxiv.org/abs/2506.01779), [original repository](https://github.com/trmue/relay) | Represent disordered memory, ensemble legs, transferred beliefs, solution count, and selection explicitly. |
| BPGD | [Paper, including binary and quaternary algorithms](https://arxiv.org/html/2312.10950v2) | Represent guided fixation, inner BP rounds, variable eligibility, and reset semantics; original repository remains unverified. |
| Impulse | [2026 preprint](https://arxiv.org/html/2606.18240v1) | Preserve failure-triggered shortening/parallel attempts and lifting/selection; original repository remains unverified. |
| BeamSearch | [Paper](https://arxiv.org/html/2512.07057v2), [original repository](https://github.com/ionq-publications/BeamSearchDecoder) | Represent beam width, branching, masked BP, pruning and scores, with work across all paths. |
| BP-OSD / BP-LSD | [OSD paper](https://arxiv.org/abs/2005.07016), [LSD paper](https://arxiv.org/abs/2406.18655), [implementation](https://github.com/quantumgizmos/ldpc) | Preserve both native composite references and independent optional canonical postprocessing contracts. |
| SI / OTF | [Stabilizer inactivation](https://arxiv.org/abs/2205.06125), [ordered Tanner forest](https://arxiv.org/abs/2409.01440) | These are source-supported interpretations, not interchangeable algebraic solvers; pin variants and document any different intended meaning. |

All requested update rules, schedules, memory/state modifications, interventions, and candidate processing remain in scope. Each needs a precise equation or procedure, trigger, state ownership, kernel-compatibility condition, and verification fixture. Voting semantics, generic mixing/iteration-memory definitions, and exact cluster-sequential variants remain specification work, not implicit defaults. Detailed source inventory: [FEATURES.md](FEATURES.md).

The features report distinguishes verified original repositories from third-party implementations and unlocated code. Its verified Relay-BP and BeamSearch repository links refine the earlier open repository list in STACK.md. Missing original code must remain an explicit evidence limitation; do not relabel an independent implementation as the original reference.

### Architecture Approach

The runner owns samples, budgets, provenance, and hidden truth. The decoder sees only the observation, prior, permitted metadata, and decoder-local randomness. The engine owns mathematical updates; policies own declared transitions; an independent evaluator judges candidates against the original problem. Branches, restarts, relay legs, fallback calls, and selected candidates receive linked IDs. Source-defined modifications to a working syndrome or graph must not redefine the final validity test. See [ARCHITECTURE.md](ARCHITECTURE.md).

Use a compact mandatory shot ledger and mandatory control-flow/candidate events, with detailed per-edge traces enabled selectively. The storage policy must retain the required outcome and work evidence for every shot while avoiding an unconditional full-message trace at Monte Carlo scale. Native references may expose fewer internal events: mark unavailable metrics as missing with a reason, never as zero or invented observations.

For CSS/code-capacity outcomes, independently distinguish invalid syndrome, exact recovery, non-exact stabilizer-equivalent recovery, and syndrome-valid logical error. Declare how each contributes to any reported aggregate failure rate. For circuit results, score predicted logical-observable flips against simulator truth and validate detector fit when a fault candidate is available. Static recovery/degeneracy fields are explicitly not applicable unless a circuit-specific definition is available and tested. [BPGD](https://arxiv.org/html/2312.10950v2), [Stim DEM specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md).

### Critical Pitfalls

1. **Correct curve, wrong mechanism:** similar aggregate performance cannot verify update order, memory carryover, intervention triggers, or candidate selection. Use source-linked specifications and deterministic fixtures as well as statistical reproduction.
2. **Incorrect outcome labels:** syndrome satisfaction and exact error equality are each insufficient as universal logical-success tests. Test an independent algebraic oracle before performance claims.
3. **Misleading computational comparisons:** one reported iteration can hide many branch/relay BP executions or fallback elimination. Retain raw work counters, serial depth where defined, runtime and parallel resources separately.
4. **Weak statistical reproduction:** tolerances, uncertainty, curve-point families, stopping rules, zero-failure handling, source-data precision, and inconclusive outcomes must be specified before result inspection.
5. **Biased samples and denominators:** shared root seeds do not guarantee shared samples across implementations; preserve immutable sample IDs and account for nonconvergence, timeouts, partial jobs, and post-selection.
6. **Model drift across regimes:** joint Pauli priors and circuit detector models have distinct correlation assumptions. Record any decomposition or approximation in the experiment identity.

Mitigations, warning signs, and phase gates are detailed in [PITFALLS.md](PITFALLS.md). Statistical anchors include [NIST binomial intervals](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/propconf.htm), [time-uniform confidence sequences](https://arxiv.org/abs/1810.08240), and [Sinter's stopping/postselection API](https://github.com/quantumlib/Stim/blob/main/doc/sinter_api.md). The final procedure is a phase-level decision, not a claim that all these sources use a single method.

## Implications for Roadmap

Use fine-grained phases that each deliver an executable research capability. Establish the literature protocol early and maintain extraction alongside each decoder implementation; do not spend the whole first stage building disconnected abstractions or claim the mapping study is already complete.

| Suggested slice | Concrete deliverable | Main dependency / exit gate |
|---|---|---|
| Evidence and native baseline | Search/extraction protocol, seed registry, full manifest contract, one reproducible reference run and ledger | Source identity, canonical code/logical hashing, sample identity, and outcome checks |
| Canonical CSS baseline | Binary engine, policy lifecycle, bit-flip/separate-XZ model, independently validated outcomes | End-to-end run from manifest through ledger and small result |
| Update and scheduling policies | All requested binary update rules and schedules under explicit read/write semantics | Small deterministic traces and comparable raw work counters |
| Memory and relay | State modifications and source-linked Relay-BP composition | Reset/inheritance and leg accounting |
| Guided and perturbative interventions | BPGD, impulse, freezing, syndrome/sign interventions, restarting | Original-problem validation, attempt work, and source/adaptation labeling |
| Search and candidate processing | BeamSearch, branching, ensembles, lists and defined voting | Candidate eligibility, beam/prune accounting, deterministic ties |
| Optional fallback | OSD/LSD/SI/OTF with independent triggers and BP-only result preservation | Adapter boundary and separate fallback cost |
| CSS reproduction and comparisons | Declared statistical protocol, faithful runs, paired controlled ablations, resumable sweeps | Tolerances and denominator/work audits before large campaigns |
| Correlated quaternary | Four-state engine, joint Pauli channel, eligible policies and reproduction/comparison evidence | Y/correlation fixtures and no implicit universal policy portability |
| Circuit model and engine integration | Noisy extraction, detector/observable contracts, eligible kernels and reference adapters | Known-fault tests and explicit factorization/approximation decisions |
| Circuit reproduction and comparisons | Source-faithful and controlled circuit campaigns | Observable correctness, stopping validity, full work and provenance |
| Publication evidence | Completed systematic map, cross-regime analysis, reproducible figures, documentation and manuscript | Evidence from all three regimes; no unverified result promoted to success |

This is a suggested dependency structure, to refine into numbered requirements and phases. The user has prioritized BP modifications over additional OSD/LSD implementation. A native BP-OSD/BP-LSD baseline early is acceptable as a reference, but substantial canonical fallback work follows the BP interventions. Source-faithful runs occur in the regime used by the cited experiment: a CSS adaptation of a circuit experiment is labeled an adaptation, and its original reproduction remains scheduled for the circuit stage.

### Research Flags

- Mapping phase: research questions, search sources/cutoff, screening/adjudication, extraction taxonomy, supported-experiment selection, and exact versions/identities.
- Policy phases: mixing and iteration-memory equations, cluster scheduling, source-specific candidate voting, trigger and state-order semantics, and standalone fallback interfaces.
- Statistical comparison phase: precision/power and tolerances for each paper, missing source counts/data, digitization uncertainty, sequential stopping, multiple comparisons, censoring and paired estimates.
- Quaternary phase: message parameterization, normalization/clipping, correlated channel conventions, eligible source algorithms, and ports requiring new derivation.
- Circuit phases: syndrome-extraction circuits, rounds/boundaries, correlated/exclusive faults, detector/observable mapping, reference settings, and work/latency definitions.
- Publication phase: systematic-search update, full evidence audit, manuscript claims, reproducible release packaging, and journal-specific formatting.

## Confidence Assessment

| Area | Confidence | Basis / limit |
|---|---|---|
| Stack | MEDIUM | Official packages/docs checked; no installed environment, dependency lock, or target-HPC compatibility validation yet |
| Features | MEDIUM | Primary papers and several original repositories identified; not an exhaustive review or final supported corpus |
| Architecture | MEDIUM | Mathematical boundaries grounded; lifecycle and schemas are proposals awaiting execution tests |
| Pitfalls | MEDIUM | Primary algorithm and statistical sources; exact acceptance thresholds and inference procedures remain to be selected |

### Gaps to Address

- BPGD and impulse original implementation identities are not verified; search absence is not proof of nonexistence.
- SI and OTF source interpretations are recorded; exact intended variants and generic voting/mixing terms need explicit specifications.
- Exact code families/sizes, publication experiment set, target numerical precision, resource budget, and journal venue are not fixed yet.
- Native-reference internal instrumentation may be limited. Compare only available work measures honestly and retain externally measurable runtime with its environment.
- Source package versions, paper revisions, and licenses need pinned records before integration; stack recommendations are not dependency locks.
- Finite reproduction supports a particular statistical result, not a proof of universal equivalence or decoder superiority.

## Sources

Primary paper, original repository, and official documentation links are attached to the findings above. The four dimension reports retain the detailed source inventories. For systematic-map methodology, consult [Petersen et al.'s mapping-study guidelines](https://www.sciencedirect.com/science/article/pii/S0950584915000646) and [PRISMA reporting resources](https://www.prisma-statement.org/prisma-2020); select applicable practices in the study protocol rather than assuming an initial web search constitutes the study.

---
*Research completed: 2026-09-21 (initial scoping)*
*Ready for roadmap: yes; unresolved items are explicit phase-research inputs.*
