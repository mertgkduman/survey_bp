# Phase 4: Memory Policies and Relay-BP - Discussion Log

> **Audit trail only.** Research, planning, and execution use `04-CONTEXT.md`; this log records alternatives and selections.

**Date:** 2026-09-24
**Phase:** 4 — Memory Policies and Relay-BP
**Areas discussed:** Memory policy scope, Mixing and iteration-memory source definitions, Relay-BP CSS adaptation, Pilot ablations

---

## Memory policy scope

| Question | Options presented | User selection or clarification |
| --- | --- | --- |
| How should researchers combine damping, mixing, momentum, and iteration memory in Phase 4? | Individual policies plus selected combinations; All valid combinations; Individual policies only | All valid combinations: support any compatible combination with an explicitly declared order. |
| When two memory policies act on the same messages or beliefs, how should their application order be set? | Source order for published configurations; declared order for exploratory ones; Declared order in every manifest; One canonical order | Declared order in every manifest, including published presets. |
| Where should an exploratory memory policy be allowed to act? | Validated choice of target; Source target only; One shared target | Validated choice of target: check-to-variable messages, variable-to-check messages, or beliefs where the equation is well-defined; published presets retain their source target. |
| How much parameter variation should Phase 4 expose for memory policies? | Explicit and seeded variation; Source-defined settings only; Fixed values plus Relay-BP draws | Explicit fixed values and declared seeded assignments or refresh rules where each policy permits them; record resolved values for replay. |
| Should one policy be usable more than once in the same decoder? | Yes, as separate bindings; One instance per policy kind; Only source-defined repetition | Yes, as separate bindings, each with its own target, parameters, history, and order. |
| Should memory policies be available with existing update rules and schedules wherever semantics can be verified? | Yes, across compatible Phase 3 policies; Start with flooding sum-product; Follow source pairings | Yes, across compatible Phase 3 policies; admit verified combinations explicitly and reject undefined ones. |
| For a layered or serial schedule, when should memory history advance? | Declared per binding; After each local update; After a full iteration | Declared per binding: after each local update or at a completed source iteration; published presets use source rules. |
| If a memory policy parameter changes during a shot, what happens to existing history? | Declare retain or reset; Always retain history; Always reset history | Manifest declares retain or reset for each refresh rule; source presets follow the published procedure. |

---

## Mixing and iteration-memory source definitions

| Question | Options presented | User selection or clarification |
| --- | --- | --- |
| How many definitions should Phase 4 implement for mixing and iteration memory? | One well-specified baseline each; Several named variants; Sources you specify | Several named variants with distinct, credible source definitions. |
| What should count as a separate variant? | A distinct update or history rule; Every named published procedure; Only variants tested on quantum codes | A distinct update or history rule; coefficients and parameter ranges are configurations of the same rule. |
| Should a well-specified classical BP rule be implemented when adaptable to binary CSS? | Yes, with a clear adaptation label; Quantum-decoding sources only; Only direct source settings | Yes, with verified translation and a clear adaptation label; do not conflate classical results with CSS claims. |
| If a paper equation and its released code perform different updates, how should they be represented? | Preserve both explicitly; Follow the paper; Follow the code | Preserve both explicitly as separate behaviors or configurations; document and attribute the difference. |
| What should happen when a source procedure remains partly unresolved? | Runnable, labeled interpretation; Mapped only; Exclude it from Phase 4 | A runnable, labeled interpretation is allowed only with explicit assumptions and independent checks; source fidelity remains unresolved. |
| What should research prioritize when choosing distinct variants? | Clear procedure and mechanistic diversity; Quantum relevance first; Published performance first | Clear, verifiable procedures and mechanistic diversity; quantum relevance is a tie-breaker. |
| How much native implementation comparison should Phase 4 seek beyond Relay-BP? | Use available original code; Equations and fixtures suffice; Require native code for every variant | Pin and run available original implementations for bounded sanity checks only; record unavailability otherwise. |
| Should the same multi-variant rule apply to damping, momentum, and disordered memory? | Yes, when genuinely distinct; No, only mixing and iteration memory; Document them for later | Yes, when a source variant is genuinely distinct rather than a parameterization. |

---

## Relay-BP CSS adaptation

| Question | Options presented | User selection or clarification |
| --- | --- | --- |
| What comparison should Phase 4 deliver between original and canonical Relay-BP? | Matched CSS pilots; Native sanity check plus canonical CSS pilots; Source circuit examples now | Matched original/canonical CSS code-capacity pilots on eligible observations, labeled separately from the paper's circuit-noise curves. |
| How closely should the canonical Relay-BP preset follow the paper's internal BP procedure? | Match the source procedure; Use current canonical defaults; Offer both as equal presets | Offer both the source procedure and the current canonical-engine procedure as first-class presets, each accurately labeled; only the former claims source-procedure fidelity. |
| How far should Relay-BP component ablations go? | Isolate the main mechanisms; Source parameters only | Isolate main mechanisms including one leg, no posterior transfer, and uniform versus disordered memory, alongside source parameter sweeps. |
| Which code cases should anchor matched Relay-BP CSS pilots? | BB-144 first, then broader checks; BB-144 only; BB-144, B1, and HGP equally | Give BB-144, B1, and HGP comparable pilot coverage. |
| How should Phase 4 handle original implementation per-leg instrumentation gaps? | Add bounded instrumentation if safe; Keep original untouched; Require full native leg traces | Pin a bounded instrumentation patch where safe, verify unchanged fixture outputs, and mark remaining native gaps as missing. |
| How should canonical Relay-BP handle numeric precision and conventions in matched pilots? | Offer named profiles when needed; Use existing profile only; Use source conventions only for Relay-BP | Retain existing named canonical profile and add a source-matched profile if differences materially affect comparison. |
| How should source-procedure and canonical-engine Relay settings be compared? | Both controlled and preset-specific views; Matched settings only; Preset-specific settings only | Provide both matched-settings controlled comparison and each preset under its declared settings. |
| How should CSS pilot memory ranges be chosen? | Bounded, recorded CSS calibration; Paper ranges unchanged; Broad per-code optimization | Broad per-code optimization for BB-144, B1, and HGP, with calibration distinct from evaluation. |
| What objective chooses a memory-strength range? | Logical outcome under a work cap; Syndrome convergence; Accuracy-work frontier | Estimated logical failure on calibration samples under a declared decoder-work cap; report uncertainty and tested ranges. |
| What should broad per-code search vary? | Memory strengths only; Distribution only; All Relay settings | First-leg and later-leg memory strengths broadly; hold leg count, iteration limits, and solution stopping fixed during selection. |
| Should source-procedure and canonical-engine presets get separate tuning? | Separate tuning plus a shared-setting comparison; Tune source procedure only; One joint setting | Tune each separately on calibration samples and also compare them with shared memory settings. |
| How should Phase 4 set a finite ceiling for broad search? | Planner sets it after a small benchmark; Use a budget you provide | Planner benchmarks first, discovers available compute, then prespecifies finite per-code caps that use the available allocation maximally; retain inconclusive outcomes if needed. |
| Does Phase 4 implement quaternary memory effects as well? | Open discussion | Phase 4 remains binary CSS only. Quaternary memory equations and effects are a distinct Phase 10-11 research question; Relay-BP's circuit XYZ binary error-mode treatment is not a four-state Pauli BP kernel. Track as provisional novelty in Markdown and PDF. |

---

## Pilot ablations

| Question | Options presented | User selection or clarification |
| --- | --- | --- |
| Which design should the pilot use to isolate effects? | Focused factorial subset; Full combination grid; Source configurations first | Focused factorial subset on each code: shared baseline, individual memory families, selected two-policy interactions, and Relay-BP component ablations. |
| What diagnostic evidence should accompany outcome and work tables? | Memory and relay traces; Relay timelines first; Aggregate plots first | Bounded representative traces of beliefs/history, memory draws, relay legs, candidates, and work linked to the ledger; one step-by-step notebook generates absent stages and uses present matching data. |
| How should noise points for BB-144, B1, and HGP pilots be chosen? | Small informative grid per code; One diagnostic point per code; Source-linked points | Small prespecified informative grid per code spanning easy decoding, visible BP failures, and harder region, with matched samples across arms. |
| How much of memory-strength tuning search should pilot notebooks show? | Full search evidence; Top candidates plus archive; Chosen setting only | Full tested search surface with estimates, uncertainty, work, failed/inconclusive configurations, selection rule, and separate evaluation results. |
| What should notebook do when an existing data file has a different identity? | Preserve and regenerate; Stop and explain; Use existing file | Reuse only identity-matching data; preserve mismatched evidence and generate a new identified result when stage runs. |
| How should original-versus-canonical Relay-BP disagreements be shown? | Paired diagnostics; Aggregate results only; Every differing shot in notebook | Paired outcome and termination diagnostics on matched shots with representative disagreement cases linked to leg and memory traces where available. |
| What cost and runtime view should be prominent? | Distributions and tails; Typical case first; Per-shot records first | Work by leg, total work, runtime distributions and upper tails, with tuning/setup costs separate. |
| How should step-by-step notebooks be organized? | Shared workflow plus per-code views; One notebook per code; One notebook for everything | One notebook for all three codes, tuning, ablations, diagnostics, and comparisons, with step-by-step sections and artifact reuse. |

---

## Agent discretion

- Research chooses and verifies exact source variants, equations, compatibility derivations, informative pairwise interactions, and finite compute caps within the recorded rules.
- Technical schema and notebook implementation details remain for planning, while the user-selected behavior and evidence boundaries are locked in `04-CONTEXT.md`.

## Deferred ideas

- Derive and compare memory/relay mechanisms in a genuine quaternary Pauli BP kernel in Phases 10-11; distinguish Relay-BP circuit XYZ binary error-mode decoding and assess original circuit claims in Phase 13.
- Circuit-curve assessment of the original Relay-BP experiments remains in Phases 12–13; the code-capacity pilots in Phase 4 are labeled adaptations.

