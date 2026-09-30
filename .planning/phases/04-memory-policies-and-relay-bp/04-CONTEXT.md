# Phase 4: Memory Policies and Relay-BP - Context

**Gathered:** 2026-09-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the canonical **binary CSS code-capacity** engine with source-linked damping, mixing, momentum, iteration-memory, and disordered-memory policies, and a canonical Relay-BP composition with a pinned original implementation as an executable reference. Researchers must be able to inspect equations and state/history behavior, run eligible memory combinations and matched Relay-BP CSS pilots, trace relay legs and transfers, and account for every leg's work. The Phase 4 pilots may include broad, finite, per-code memory-strength tuning, but they do not assess the Relay-BP paper's circuit-noise curves as reproduced results.

Quaternary I/X/Y/Z BP is Phase 10, its controlled comparisons are Phase 11, and noisy extraction circuits and detector/fault models are Phases 12–13. The possible effect of memory policies in a genuine quaternary Pauli kernel is a separate research question, not a Phase 4 implementation requirement.

</domain>

<decisions>
## Implementation Decisions

### Memory-policy composition and state
- **D-01:** Support all mathematically defined and compatibility-admitted combinations of the implemented Phase 4 memory variants with eligible Phase 3 update rules and schedules. Do not restrict execution to standalone policies or source pairings. An undefined combination is rejected with a reason rather than silently approximated. Pilot coverage is a focused subset, not a full Cartesian run. — **Reversibility:** costly — persisted compatibility and policy-graph semantics will govern later experiments.
- **D-02:** Every persisted composition explicitly declares the application order of memory bindings, including source presets. A source preset resolves to its published order; no hidden global ordering default changes what a saved manifest means. — **Reversibility:** costly — changing persisted order semantics would reinterpret existing manifests and evidence.
- **D-03:** An exploratory binding may target check-to-variable messages, variable-to-check messages, or beliefs when its equation is defined and independently verified at that target. Published presets retain their source target. Different targets or orderings are labeled adaptations, not source-equivalent runs.
- **D-04:** Each policy may expose fixed values and declared seeded assignments or refresh rules where mathematically valid. Persist the generator/distribution, decoder-local seed identity, resolved values, graph association, and refresh boundary for replay. Keep decoder randomness independent of physical-error sampling, as in Phase 3.
- **D-05:** Permit multiple instances of the same memory-policy kind in one composition. Each instance has a distinct binding ID, target, parameters, place in the order, owned history, lifetime, and event attribution. Existing private-state and typed-decision boundaries still apply. — **Reversibility:** costly — binding identity and ownership become part of the manifest and ledger contract.
- **D-06:** Explicitly validate compatibility with implemented Phase 3 updates and schedules. The range includes local-step schedules where semantics can be established; unsupported combinations remain visibly rejected.
- **D-07:** Each binding declares when its history advances, including local-update versus completed source-iteration boundaries for non-flooding schedules. Published presets use their source-defined boundary. This is distinct from convergence-check cadence and parameter-refresh cadence.
- **D-08:** For any parameter refresh during a shot, the manifest declares whether the binding retains or resets its history; source presets use the source procedure. Initial values, reset scope, and state lifetime must be explicit and verifiable.

### Source-defined variants and qualifications
- **D-09:** Implement several **genuinely distinct update or history rules** as separately named source-linked variants when well specified. Apply this principle to damping, mixing, momentum, iteration memory, and disordered memory; a changed coefficient or range alone is a configuration of one rule, not a new variant. This is not a request to implement every named paper uncritically.
- **D-10:** A classical-BP memory rule may be translated to binary CSS when the translation is mathematically justified and verified. Mark the CSS execution as an adaptation and never transfer a classical performance claim to quantum outcomes by implication.
- **D-11:** If a paper's equation and released code differ materially, preserve both as separate named behaviors or configurations, identify which each run used, and document the discrepancy. Do not silently prefer one as the other.
- **D-12:** If source details remain unresolved after checking primary paper, supplements, and code, a runnable **labeled interpretation** is permitted only with explicit assumptions and independent fixtures. Source fidelity remains unresolved; the interpretation cannot be presented as a faithful source implementation.
- **D-13:** Select variants first by clear, verifiable procedure and mechanistic diversity; use quantum-decoding relevance as a tie-breaker. Research must document the selected source set, rejected candidates, and unresolved details.
- **D-14:** Where an original implementation is available, pin it and run bounded **sanity checks** against the canonical rule. Missing original code is an explicit evidence limit, not a reason to invent a reference or expand these checks into a reproduction campaign.

### Relay-BP source, reference, and CSS adaptation
- **D-15:** Run the pinned original implementation and canonical Relay-BP on the **same eligible CSS code-capacity observations**. Label these as matched code-capacity pilots/adaptations of a circuit-focused paper; published circuit curves remain for Phase 13. Original and canonical runs retain separate identity and configuration translations.
- **D-16:** Offer two first-class, easy-to-run canonical Relay-BP presets: one following the paper's internal BP procedure and one using the canonical engine's default BP procedure. Both are visible presets, but their procedure labels and fidelity status remain distinct. A source-procedure CSS run is still a code-capacity adaptation, not a reproduction of circuit experiments.
- **D-17:** Expose source Relay controls and run component ablations that isolate one leg, posterior transfer on/off, uniform versus disordered memory, and selected source parameter sweeps. Preserve the source procedure as a named preset; changed components are labeled adaptations.
- **D-18:** Give BB-144, B1, and the Phase 3 HGP example **comparable** matched native/canonical CSS pilot coverage, plus small deterministic fixtures. Verify exact artifact and logical-operator identities before using a case; do not treat a generated family example as a paper-exact matrix.
- **D-19:** A small, pinned instrumentation patch to the original Relay-BP implementation is allowed when it can expose per-leg evidence without changing behavior. Check output equivalence on fixtures against the unmodified pinned reference. Record remaining inaccessible native fields as missing with reasons.
- **D-20:** Retain the existing canonical numerical profile and add a separately named source-matched precision/clipping profile if differences materially affect the native comparison. Numerical profiles and effective overrides are recorded; bit-for-bit agreement is not the project reproduction standard.
- **D-21:** Show both a controlled view with matched Relay settings and a view using each preset's separately declared settings. In the controlled view, leg/iteration/solution limits, transfer, and memory settings are matched to isolate the internal BP-procedure effect.
- **D-22:** Perform **broad per-code optimization** of first-leg memory strength and subsequent-leg disordered-memory distribution for BB-144, B1, and HGP. Choose settings using estimated logical failure on calibration samples under a declared decoder-work cap; retain uncertainty and every tested range. Hold leg count, iteration limits, and solution stopping fixed during that selection. Tune source-procedure and canonical-engine presets separately, then also compare them at shared memory settings.
- **D-23:** The planner must first benchmark representative work and identify the compute actually available, then **prespecify finite** per-code configuration, shot, and compute caps that make strong use of that allocation. Calibration and evaluation samples are separate. Retain insufficient-precision and inconclusive outcomes; do not extend a run silently until a preferred rank appears. Formal publication-curve assessment remains in later phases.

### Pilot ablations, evidence, and notebook
- **D-24:** Use a focused factorial subset on each code: a common baseline, each memory family alone, selected two-policy interactions, and Relay-BP component ablations. Research chooses the informative pairings after defining the variants; implementation support under D-01 is broader than pilot coverage.
- **D-25:** Use a small, prespecified informative noise grid per code spanning easy decoding, visible BP failures, and a harder region. Decoder arms at each point use the same identified physical samples. Keep source-specific and controlled configurations separate.
- **D-26:** Produce bounded representative traces linked to the shot/event ledger: beliefs and history changes, memory draws, relay leg transitions, candidates, and per-leg work. Routine full edge traces are not required for every shot; truncation and unavailable native instrumentation remain explicit.
- **D-27:** Provide **one step-by-step notebook** covering all three codes, tuning, ablations, diagnostics, and cross-code comparison. When a stage is run, it loads existing artifacts only if manifest, source/policy, code/environment, sample, and stage identities match; if missing or mismatched, it preserves old evidence and generates a new identified result under the declared budget. The notebook can generate the data it analyzes; it is not merely a static report.
- **D-28:** Show the full tuning search in the notebook: tested ranges, estimates and uncertainty, work, failed/inconclusive configurations, selection rule, and separate evaluation results. Show paired original/canonical outcome and termination disagreements with representative linked leg/memory traces when observable.
- **D-29:** Report raw work by leg and total, runtime and resource distributions including upper tails, and tuning/setup costs separately. Preserve outcome classes, denominators, candidate origins, and source/adaptation labels; pilot plots do not establish statistical reproduction or universal decoder rankings.
- **D-30 (2026-09-30, supersedes the Phase 4 execution scale in D-22–D-29):** The user stopped the comprehensive Phase 4 experiment because its size was premature. Preserve the completed calibration and all partial/cancelled receipts, but do not resume the 448-shot evaluation, native-pair production sequence, or 14-arm factorial as a Phase 4 completion gate. Finish Phase 4 with deterministic policy/source checks, existing bounded pilots, verified evidence inventory, and an availability-aware notebook/guide. Missing evaluation, ablation, and trace populations remain explicitly unavailable or not assessed. Later CSS campaign design in Phases 8–9 must choose a fresh scope, precision, stopping rule and compute budget; the old grid is historical, not a commitment. The circuit reproduction target remains in Phase 13. D-22–D-29 continue to describe the already-frozen historical design and reporting obligations for any evidence actually retained.

### Agent's Discretion and Research Responsibilities
- Find and justify the precise primary-source variant set, equations, parameter domains, initialization, reset/advance order, and compatibility proofs. Determine whether apparently different named methods are mathematically the same rule under reparameterization.
- Resolve the Relay-BP paper/repository revision and original-reference identity, including whether the locally frozen `mg551-duke/relay` fork is source-equivalent. Pin exact code and configuration; document paper/code drift and native instrumentation limits.
- Choose representative two-policy interactions, exact noise points, trace budgets, notebook sections, and plotting conventions consistent with D-24–29.
- Benchmark available compute and set finite tuning/sample budgets before the broad search. Specify uncertainty, selection, and stop rules before collecting assessment results; preserve search and failed-run evidence.
- Choose concrete schema/module extensions while preserving existing manifest versions, original-problem evaluation, policy state ownership, typed relay transfer, leaf work accounting, and ledger lineage.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** All repository references below are full relative paths.

### Project and inherited phase decisions
- `.planning/PROJECT.md` — canonical-engine family boundary, staged decoding regimes, reproducibility, and evidence labels.
- `.planning/REQUIREMENTS.md` — MEM-01–05, MOD-01, and inherited provenance/compatibility requirements.
- `.planning/ROADMAP.md` — Phase 4 scope and success criteria; Phases 10–13 own quaternary and circuit execution/comparisons.
- `.planning/STATE.md` — current milestone and phase position.
- `.planning/phases/01-evidence-registry-and-native-css-baseline/01-CONTEXT.md` — code/source identity, pilot adaptation labels, and native-reference principles.
- `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md` — typed lifecycle, state ownership, relay payload restriction, budgets, numerical profiles, tracing, candidate selection, and hidden-truth separation.
- `.planning/phases/03-update-rules-and-scheduling/03-CONTEXT.md` — parameter diversity, RNG separation, local-update semantics, matched pilots, code cases, and cost views.

### Source research, evidence, and novelty tracking
- `.planning/research/FEATURES.md` — damping, momentum, mixing/iteration-memory source leads and Relay-BP repository identity.
- `.planning/research/SUMMARY.md` — reconciled mechanism, reference, and evidence boundaries.
- `.planning/research/ARCHITECTURE.md` — canonical-versus-native roles, state transfer, stopping scopes, and ledger lineage.
- `.planning/research/PITFALLS.md` — source/procedure drift, circuit-vs-CSS claims, logical outcomes, and relay work hazards.
- `data/evidence/code-inventory.json` — code identity and artifact status; recheck against the completed Phase 3 fixtures.
- `docs/environment-freeze.txt` — currently frozen Relay-BP fork reference; provenance and equivalence to the author implementation must be verified.
- `docs/research-novelty-and-depth-register.md` — living provisional cross-kernel memory research question requested during discussion; authoritative source for the claim tracker.
- `docs/research-novelty-and-depth-register.pdf` — current generated reading copy of the same tracker, not separate evidence authority.

### Existing execution and analysis contracts
- `src/bp_registry/canonical/contracts.py` — seven-role composition, current state-memory placeholder, binding ownership, and typed relay/search contracts.
- `src/bp_registry/canonical/execution.py` — canonical CSS lifecycle and policy runtime integration.
- `src/bp_registry/canonical/schedules.py` — stable edge identities and scheduling interfaces.
- `src/bp_registry/canonical/updates.py` — seeded parameter assignments and refresh patterns.
- `src/bp_registry/canonical/budgets.py` — hierarchical budgets and relay/work counters.
- `src/bp_registry/manifests.py` — public executable-composition admission and schema versions.
- `src/bp_registry/ledger.py` — structural event grammar, including reserved relay-transfer event kind.
- `src/bp_registry/canonical/lineage.py` — leg, attempt, candidate, and selection identities.
- `src/bp_registry/evaluator.py` — independent original-problem CSS evaluation.
- `docs/canonical-engine.md` — current public engine, policy, numerical, lineage, and accounting contracts.
- `docs/profiling-and-tracing-strategy.md` — bounded representative and rare-event tracing/profiling rules.
- `notebooks/phase3-pilot-analysis.ipynb` — existing source-backed pilot notebook pattern to inspect before designing the Phase 4 notebook.

Primary external sources to verify and pin during research are [Müller et al., Relay-BP](https://arxiv.org/html/2506.01779) and the [author repository](https://github.com/trmue/relay). `.planning/research/FEATURES.md` links initial damping and momentum papers. Source equations, code defaults, and paper/code differences must be checked against their pinned revisions rather than assumed from this discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The canonical binary engine already exposes SPA/min-sum update rules, flooding and local-step schedules, stable edge identities, independent CSS evaluation, hierarchical work budgets, bounded trace sidecars, and deterministic parameter-generation patterns.
- `src/bp_registry/canonical/contracts.py` defines policy binding IDs, lifecycle hooks, state lifetimes, search relationships, and a typed relay payload concept. `src/bp_registry/canonical/lineage.py` and `src/bp_registry/ledger.py` already reserve leg and relay-transfer evidence vocabulary.
- The completed Phase 3 BB-144, B1, and HGP fixtures/pilots and `notebooks/phase3-pilot-analysis.ipynb` provide code and analysis starting points, subject to exact artifact-identity checks.

### Established Patterns
- Persisted manifests are versioned and closed; unknown policy kinds are rejected. Decoder-local randomness is independently identified from physical sampling. Candidate selection freezes before truth-aware evaluation.
- Work is recorded once at leaf scope and aggregated through lineage. A source-qualified iteration is not a universal cost unit. Detailed traces are bounded sidecars, not mandatory production records.
- Native references are executable comparisons with explicit instrumentation missingness; they cannot substitute for the canonical policy engine.

### Integration Points
- The public composition and manifest validators currently admit only `stateless`/identity state-memory effects. Planning must extend registered executable behavior and compatibility rather than only adding a label.
- The current `RelayPayload` placeholder carries binary values; the paper transfers **real-valued final marginals**. Planning must define a source-correct, typed, versioned posterior payload and its numerical conventions rather than reuse the binary placeholder as if equivalent.
- Local schedules have distinct atomic units and progress boundaries. Memory advancement, reset, refresh, and convergence must be coordinated through engine-owned lifecycle hooks while preserving verified Phase 3 schedule semantics.
- The existing ledger admits `relay_transfer`, and budgets include `relay_transfers`, but Phase 4 must make leg/member events, transfer contents/identity, scoped termination, candidate selection, and all leg work reconstructible and verifier-checked.
- The frozen environment lists a Relay-BP fork; the author repository and any instrumentation fork must remain separately identified. A native adapter should consume the same eligible CSS observations and preserve input/output translations and observability limits.

</code_context>

<specifics>
## Specific Ideas and Source Qualifications

- The user asked for **all valid memory-policy combinations**, including repeated bindings, rather than only a small preset catalog; the pilot comparison itself should remain a focused factorial subset.
- The user originally requested broad per-code Relay memory-strength optimization after benchmarking; the completed calibration and finite caps are historical evidence. D-30 supersedes the scale of further Phase 4 experiments.
- The user originally wanted one notebook that could run the full process step by step. Under D-30, the Phase 4 notebook reads retained evidence and uses bounded fixtures; cancelled production stages are shown unavailable and are not generated automatically.
- The user distinguished Relay-BP's circuit-level XYZ error-mode graph from a genuine four-state Pauli BP kernel and asked to track binary-versus-quaternary memory effects as a possible novelty. The provisional entry is present in both the Markdown register and its generated PDF. The mathematical and closest-precedent claims remain to be established in Phases 10–11.
- The Relay-BP paper specifies a binary check/action/prior representation, a min-sum-based disordered-memory update, final-marginal transfer between legs, bounded leg/solution stopping, and weighted selection among valid solutions. Its published performance examples are circuit-level; translating its procedure to CSS code capacity must be labeled accordingly. The paper's XYZ circuit representation is **not by itself** a quaternary Pauli BP kernel; this is an inference from its stated factorization, not a priority claim.

</specifics>

<deferred>
## Deferred Ideas

- Derive mathematically compatible memory and relay policies for a **joint four-state Pauli BP kernel** in Phase 10, then compare their effects with separate binary inference on matched physical samples and budgets in Phase 11. Track the closest precedents and any absent faithful counterpart; do not assume a scalar memory equation ports unchanged.
- Relay-BP's original circuit-noise XYZ/DEM setting, detector/observable semantics, and published circuit-curve assessment belong in Phases 12–13. The source's binary error-mode circuit graph and code-capacity quaternary Pauli kernel answer different questions.
- Full generic search/ensemble controller behavior remains in Phase 6; the Phase 4 relay ablations are source-linked or clearly labeled component adaptations.
- Formal statistical reproduction campaigns and publication-level precision remain in Phases 8–9 and 11/13 as appropriate. Phase 4's completed calibration, bounded pilots, and interrupted production prefix are retained and transparent, but do not establish a paper-curve reproduction or complete comparison.

</deferred>

---

*Phase: 04-Memory Policies and Relay-BP*
*Context gathered: 2026-09-24*
