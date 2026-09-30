# Phase 5: Guided and Perturbative BP Interventions - Context

**Gathered:** 2026-09-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the canonical binary CSS code-capacity engine with source-linked BPGD, impulse decoding, freezing, syndrome flipping, sign flipping, and restarting. A researcher must be able to run these interventions through the public manifest and CLI, inspect every attempt and its cost, and validate selected recoveries against the immutable original problem. Phase 5 includes a small, matched B1 mechanism pilot and deterministic fixtures on other codes. It does not establish a decoder ranking or reproduce a published curve; statistical campaigns and CSS reproduction remain in Phases 8–9.

The preparatory `05-DESIGN.md` supplies proposed scientific and execution contracts. Its unresolved source details remain research questions. A proposed interpretation is not a verified source behavior merely because this context uses the design as input.

</domain>

<decisions>
## Implementation Decisions

### Matched CSS pilot
- **D-01:** Use B1 as the one primary code for matched Phase 5 physical-sample pilots. Use deterministic algebraic and policy fixtures for BB-144, HGP, and other eligible codes rather than running three code-wide comparison pilots. Confirm B1 artifact and logical-operator identity before sampling. — **Reversibility:** costly — changing the primary code would require new matched samples, manifests, and evidence rather than relabeling B1 results.
- **D-02:** Compare one common B1 baseline with each of the six Phase 5 intervention kinds separately: BPGD, impulse, freezing, syndrome flip, sign flip, and restarting. Use the same identified physical samples across eligible arms. Do not add intervention-pair arms to this pilot. This limits pilot coverage, not the canonical engine's compatibility contract. Source-unresolved or ineligible arms retain explicit availability/qualification status; no substitute is silently called source-faithful.
- **D-03:** Size the B1 pilot for mechanistic inspection: small, prespecified finite sample and work caps, visible attempts and bounded traces, original-problem outcomes, and complete cost attribution. Preserve inconclusive results and all admitted shots. Do not choose settings from this pilot to make a decoder ranking, and do not treat these outcomes as a publication-curve assessment.

### Researcher execution and inspection
- **D-04:** The public entry point is a versioned saved manifest with CLI preflight, execution, and verification. Provide a compact Phase 5 notebook to inspect the produced evidence; it is not the primary configuration or execution surface. Preserve historical manifest and ledger meanings. — **Reversibility:** costly — persisted manifest and evidence semantics become dependencies for later experiments and replay.
- **D-05:** Lead the notebook with a matched shot-by-shot path: baseline result, chosen intervention's attempts, candidate origins, selected candidate, original validation, and work. Keep the same physical sample in view while switching intervention arms. Show every failed, contradictory, invalid, and budget-denied attempt as a visible row with status, candidate origin, and work; make details expandable. Summaries complement these rows rather than hiding them.
- **D-06:** Include interactive outcome-category, attempt-count, and work-distribution plots in the notebook and a shareable HTML export. A legend click shows or hides an arm/series without modifying evidence. Initially show the baseline and one selected arm; the other arms remain available. Keep arm visibility synchronized across the outcome and work plots. Timing plots are not required in this first plot set.
- **D-07:** The HTML export includes plot hover details, manifest and source identities, assessment labels, and references or links to the saved evidence. A full per-shot attempt drilldown is required in the notebook, not in the HTML export. Preserve source, adaptation, unavailable, and not-assessed qualifications in tables and plot context even when a series is hidden.

### Research and planner discretion
- Resolve the source-defined BPGD, impulse, syndrome-flip, and sign-flip variants against primary papers, supplements, and available code. The user did not select preferred flip papers or settle paper/code ambiguities in this discussion. Record unresolved behavior and native-code availability explicitly; use separately labeled interpretations only under the project's existing source-qualification rules.
- Choose exact B1 noise point(s), finite shot/attempt/work/time/trace caps, display library, HTML packaging, and plot details consistent with D-01–D-07. Benchmark representative work and declare caps before collecting pilot outcomes. Do not turn the pilot into the oversized Phase 4 campaign that was cancelled.
- Choose module names, schema fields, and CLI command names while preserving canonical policy execution, original-problem validation, deterministic replay, and leaf-level work accounting.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** Repository references use full relative paths.

### Project and phase scope
- `.planning/PROJECT.md` — canonical-engine architecture, reproduction standards, provenance, and staged decoding regimes.
- `.planning/REQUIREMENTS.md` — MOD-02, MOD-03, and INT-01–04.
- `.planning/ROADMAP.md` — Phase 5 goal, five success criteria, dependencies, and boundary from later campaigns.
- `.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN.md` — proposed intervention, session, lift, validation, restart, and evidence contracts; unresolved source details.
- `.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md` — task map and acceptance checks for the six requirements.
- `docs/evidence/phase5-source-status-20260926.json` — dated BPGD and impulse source-availability record; recheck rather than treating it as final.

### Inherited scientific and pilot decisions
- `.planning/phases/04-memory-policies-and-relay-bp/04-CONTEXT.md` — composition, source qualification, pilot evidence, and the Phase 4 scale correction in D-30.
- `.planning/phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md` — cancelled oversized campaign and retained partial evidence.
- `.planning/phases/04-memory-policies-and-relay-bp/04-VERIFICATION.md` — completed Phase 4 capability gate and qualified missingness.
- `.planning/phases/03-update-rules-and-scheduling/03-CONTEXT.md` — schedule and update semantics inherited by interventions.
- `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md` — canonical lifecycle, immutable lineage, budgets, truth separation, and replay contracts.

### Existing public and algebraic surfaces
- `src/bp_registry/canonical/problems.py` — immutable original/working-problem and candidate types to extend for transformations and lifts.
- `src/bp_registry/canonical/kernel.py` — binary BP prior, belief, and candidate operations; session continuation needs a deliberate extension.
- `src/bp_registry/canonical/execution.py` — engine-owned lifecycle and attempt execution.
- `src/bp_registry/canonical/budgets.py` — reservation and work-limit patterns.
- `src/bp_registry/manifests.py` — strict versioned public manifest definitions.
- `src/bp_registry/cli.py` — public preflight, execution, and verification entry points.
- `tools/validate_intervention_design.py` — independent finite GF(2) shortening/lifting oracle.
- `notebooks/phase4-memory-relay-analysis.ipynb` — existing evidence-inspection notebook pattern; Phase 5 needs a compact shot-first view.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OriginalProblem`, `WorkingProblem`, and `OriginalSpaceCandidate` in `src/bp_registry/canonical/problems.py` establish immutable decoder-visible values and stable candidate selection, but current working problems only admit identity mapping.
- `BinarySpaKernel` in `src/bp_registry/canonical/kernel.py` already accepts a vector prior for belief assembly; deliberate BP session and round continuation are still needed.
- Canonical budgets, lineage, verification, and sparse ledgers already provide reservation, original-problem evaluation, stable identities, and work attribution.
- Existing CLI preflight/run/verification and Phase 4 notebook/report tooling provide public execution and evidence-inspection patterns.

### Established Patterns
- Persisted manifests are versioned, strict, and preflighted; historical records are not silently reinterpreted.
- Engine-owned policies receive decoder-visible state, while hidden truth remains with the independent evaluator.
- Work is reserved before mutation, committed at leaf scope, and aggregated once; denied and failed attempts remain visible.
- Phase 4's cancelled large campaign is retained as evidence with missing assessment, not resumed as a prerequisite to Phase 5.

### Integration Points
- Extend the canonical engine with transformed working views, session state, intervention proposals, lifts, and original validation while retaining the immutable original observation.
- Add a new manifest/ledger version for intervention identity and control flow, and expose it through CLI preflight, execution, and verification.
- Feed the Phase 5 notebook and exported plots from verified evidence, preserving matched sample identity, arm status, candidate lineage, work, and assessment labels.

</code_context>

<specifics>
## Specific Ideas

- The user selected B1 over BB-144 and HGP for the primary Phase 5 pilot despite its inconclusive Phase 4 low-noise selection. The new pilot gets its own prespecified question and caps.
- The user requested click-based legend controls that turn plotted series on and off. Those controls should synchronize arm visibility across outcome and work plots, with baseline plus one arm initially visible.
- The shareable HTML view should retain manifest/source identities and assessment labels alongside interactive plots. The notebook remains the place for full shot and attempt inspection.

</specifics>

<deferred>
## Deferred Ideas

- Multi-code pilot comparisons and intervention-pair arms are outside the selected Phase 5 pilot. Generic composition support remains governed by the roadmap and compatibility contract, not by the pilot's arm list.
- Statistical ranking and publication-curve claims remain in Phases 8–9. Quaternary and circuit behavior remain in Phases 10–13.

</deferred>

---

*Phase: 05-Guided and Perturbative BP Interventions*
*Context gathered: 2026-09-30*
