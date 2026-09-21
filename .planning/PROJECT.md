# Policy-Based BP Research Platform for QLDPC Decoding

## What This Is

An open, accessible, and interpretable research platform for BP-family quantum low-density parity-check (QLDPC) decoders, paired with a systematic mapping study of the literature and an executable registry of published experiments. Within each mathematically compatible BP kernel family, one canonical execution engine expresses decoder behavior through explicitly defined modular policies rather than merely wrapping unrelated implementations behind a shared API. The platform, literature study, and experiments will support a journal paper covering CSS code-capacity decoding, correlated quaternary code-capacity decoding, and circuit-level decoding, developed in that order.

## Core Value

Make BP decoder differences explicit, reproducible, and fairly comparable by expressing compatible algorithms as policy compositions in a canonical execution engine and linking their measured behavior to published evidence.

## Requirements

### Validated

(None yet — the workspace is new. Existing third-party implementations are reference sources, not capabilities already delivered by this project.)

### Active

- [ ] Develop a systematic mapping study of BP-family QLDPC decoding literature, connecting papers, algorithmic mechanisms, experimental settings, implementations, and reported findings.
- [ ] Define a common execution model with explicit policies for message updates, scheduling, state and memory modification, interventions, stopping, candidate selection, and postprocessing.
- [ ] Provide one canonical engine within each mathematically compatible BP kernel family, with compatibility boundaries documented rather than assuming every policy combines with every kernel.
- [ ] Cover message-update rules: sum-product, min-sum, normalized min-sum, and offset min-sum.
- [ ] Cover schedules: flooding, layered, serial, residual, randomized, and cluster-sequential.
- [ ] Cover state modifications: damping, mixing, momentum, iteration memory, and disordered memory.
- [ ] Cover interventions: decimation, freezing, syndrome flipping, sign flipping, branching, restarting, relaying, and ensembling.
- [ ] Prioritize policy-based realizations of RelayBP, BPGD, impulse decoding, and BeamSearch, grounding each specification in its source paper and implementation.
- [ ] Support candidate-processing mechanisms including OSD, LSD, SI, OTF, list selection, and voting where their source-defined semantics and compatibility permit. Resolve ambiguous abbreviations and mechanisms during research rather than inventing definitions.
- [ ] Make OSD/LSD-style postprocessing an optional addition for nonconvergence, independently configurable so the effects of the BP modifications can be evaluated.
- [ ] Import or integrate published third-party implementations as executable references, including BP-OSD, BP-LSD, and RelayBP, and evaluate corresponding canonical policy compositions against published results.
- [ ] Begin with CSS code-capacity decoding using separate X/Z decoding and support for a bit-flip noise model.
- [ ] Extend to code-capacity quaternary BP that decodes correlated X/Z errors jointly.
- [ ] Extend to circuit-level decoding after the code-capacity stages; define its noise, observation, and decoding semantics during dedicated research and planning.
- [ ] Associate every supported paper with a machine-readable reproduction manifest and an executable experiment entry.
- [ ] Validate reproduction of reported curves within documented statistical tolerances, with numerical tolerances specified where applicable to other outputs.
- [ ] Produce a provenance-preserving event ledger for every simulation that supports joint analysis of iteration count, computational work, syndrome validity, exact recovery, degenerate recovery, logical failure, termination reason, and post-selection.
- [ ] Provide both faithful reproductions under published settings and controlled comparisons under shared codes, noise, error samples, and explicit computational budgets.
- [ ] Report logical performance, convergence, iterations, computational work, and runtime separately, retaining enough provenance to interpret each measure.
- [ ] Deliver detailed documentation of mathematical definitions, policy semantics and compatibility, reference integration, experimental procedures, and known discrepancies or interpretive decisions.
- [ ] Produce a journal manuscript with evidence from all three decoding stages and traceable links to the software, mapping study, manifests, and experiment outputs.

### Out of Scope

- A shared API around unrelated decoders as the sole unification mechanism — the core contribution requires canonical policy-driven execution within compatible kernel families.
- Universal interchangeability of all policies across all BP kernels — combinations require mathematical compatibility and explicit semantics.
- Mandatory bitwise identity or identical decision trajectories between reference and canonical implementations — agreement with reported curves within statistical tolerances is the accepted reproduction standard.
- Treating OSD/LSD postprocessing as the primary contribution or an always-enabled component — modifications inside BP take priority, and postprocessing must be independently switchable.
- Implementing all decoding regimes at once — development proceeds through CSS code-capacity, correlated quaternary code-capacity, and then circuit-level decoding.
- Omitting quaternary or circuit-level decoding from the first journal paper — both are in the agreed publication scope, even though they come in later development stages.

## Context

### Research intent and audience

The intended users are researchers studying, reproducing, and comparing BP-family QLDPC decoders. The platform should make algorithmic differences interpretable and experimentally testable, connecting literature claims to executable specifications and observed behavior. A narrower set of scientific hypotheses and the exact publication experiments will be developed from the mapping study and comparative results; no hypothesis or performance advantage is assumed in advance.

### Existing work and reference implementations

The user identified existing BP-LSD, BP-OSD, and RelayBP implementations as important references. No repositories, versions, paper identifiers, local code, experiment results, or manuscript drafts have been supplied yet. Research must identify and pin authoritative sources before implementation-specific claims or reproduction configurations are treated as established.

Reference execution and canonical execution are complementary: the first preserves access to published implementations, and the second exposes behavior through common policy semantics for controlled comparison. Neither access to a reference implementation nor a superficial API match alone establishes successful reproduction.

### Reproduction manifest contract

Each supported paper's machine-readable reproduction manifest must contain:

- The exact decoder specification, including policy choices and parameters.
- Code and logical-operator hashes.
- Noise model.
- Physical-error rates.
- Random-seed policy.
- Simulation budget and stopping rule.
- Software and backend versions.
- Expected table, curve, or scalar outputs.
- Statistical and numerical reproduction tolerances.
- Links to the source paper and original implementation.
- Known discrepancies or interpretive decisions.

Here, code and logical-operator identity must be represented explicitly; software versions are a separate provenance requirement. Concrete hashing and serialization conventions remain to be specified.

### Evaluation contract

Two evaluation views are required:

1. **Faithful reproduction:** use each paper's settings and compare with its reported results within declared statistical tolerances. Document missing information, numerical differences, and interpretive choices.
2. **Controlled comparison:** compare eligible decoder configurations using shared codes, noise, error samples, and explicit computational budgets. Report logical performance, convergence, iteration counts, computational work, and runtime separately.

Every simulation must retain the provenance needed to relate decoding outcomes to work and termination behavior. The ledger must support distinctions among syndrome validity, exact recovery, degenerate recovery, and logical failure, as well as the effects of post-selection. Exact mathematical outcome definitions, ledger schemas, work-accounting units, and statistical acceptance procedures will be specified and validated in subsequent work.

### Development and publication sequence

1. CSS code-capacity, separate X/Z decoding, including the bit-flip model.
2. Correlated quaternary BP at code capacity.
3. Circuit-level decoding.

All three stages belong to the same intended journal-paper scope. The literature mapping, experiment registry, documentation, and provenance model should develop alongside the software, so later stages extend an evidence-backed foundation.

## Constraints

- **Architecture**: One canonical execution engine per mathematically compatible kernel family — scientific interpretability and fair comparison require more than adapter-level integration.
- **Priority**: BP-internal policies and named BP modifications before optional OSD/LSD-style postprocessing — this is the user's principal research focus.
- **Sequence**: CSS code-capacity before correlated quaternary code-capacity before circuit-level decoding — complexity must be introduced in stages without shrinking the publication scope.
- **Reproduction**: Statistical agreement with published curves is sufficient — bit-for-bit identity is not required, but discrepancies must be documented.
- **Provenance**: Every simulation must emit an event ledger, and every supported paper must have a reproduction manifest — evidence must remain traceable through analysis and publication.
- **Comparison**: Preserve both paper-specific and controlled configurations — reproduction and fair cross-decoder comparison answer distinct research questions.
- **Accessibility**: Deliver open software and detailed documentation — exact license, packaging, interface, implementation languages, and backend choices remain undecided.
- **Resources**: The current workspace is on an HPC filesystem — concrete compute allocations, runtime budgets, and scheduling requirements have not yet been specified.
- **Publication**: The journal paper includes all three decoding regimes — target journal, submission date, and manuscript format remain undecided.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Canonical policy-driven execution within compatible BP kernel families | Make algorithmic differences explicit and experimentally comparable | — Pending |
| Preserve third-party implementations as executable references | Establish traceable reproduction baselines alongside canonical realizations | — Pending |
| Prioritize RelayBP, BPGD, impulse decoding, and BeamSearch | Focus first on mechanisms acting inside BP | — Pending |
| Make OSD/LSD optional for nonconvergence | Isolate the contributions of BP modifications and postprocessing | — Pending |
| Develop CSS code-capacity, then correlated quaternary code-capacity, then circuit-level decoding | Build complexity in stages | — Pending |
| Include all three regimes in the first journal paper | Keep the agreed scientific scope intact across development stages | — Pending |
| Accept reproduction through statistical agreement with reported curves | Meet the research objective without requiring identical numerical trajectories | — Pending |
| Maintain faithful and controlled evaluation views | Support both literature reproduction and fair comparison | — Pending |
| Require manifests, event ledgers, and detailed discrepancy documentation | Preserve provenance and make results interpretable and auditable | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. Is "What This Is" still accurate? Update if it has drifted.

**After each milestone:**
1. Review all sections.
2. Check whether Core Value is still the right priority.
3. Audit Out of Scope and its reasons.
4. Update Context with the current software, evidence, and research state.

---
*Last updated: 2026-09-21 after project-definition approval*
