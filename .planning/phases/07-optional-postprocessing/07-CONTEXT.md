# Phase 7: Optional Postprocessing - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Attach independently configurable OSD, LSD, source-resolved SI, and source-resolved OTF processing to canonical binary CSS BP after declared nonconvergence. Preserve the BP-only output and evidence, separately account for fallback work, and run pinned native BP-OSD/BP-LSD composites as distinct references. Extend the literature policy-file route to express and trace qualified fallback variants. Phase 7 produces verified interfaces and bounded mechanism evidence; statistical campaigns and published-curve assessment remain in Phases 8–9.

</domain>

<decisions>
## Implementation Decisions

### Fallback trigger and handoff
- **D-01:** Invoke optional processing only after the entire declared BP/search composition finishes without any original-syndrome-valid BP candidate. A failed branch, restart, relay leg, or ensemble member does not individually trigger fallback while the composition can continue.
- **D-02:** When several BP attempts fail, hand one attempt to the configured fallback. Select it by a prespecified deterministic ranking based only on decoder-visible information, before fallback execution. Research/planning defines the exact ranking and ties; do not use hidden simulation truth or completion arrival order.
- **D-03:** Each fallback method declares whether it receives the immutable original CSS problem with translated reliability or the chosen attempt's working problem and reconstruction map. In either case, reconstruct and independently validate every resulting candidate against the original problem. The exact reliability convention and mathematically compatible handoff for each method require source and interface research.
- **D-04:** Execution errors and absent or unusable reliability state do not trigger fallback. Retain the BP/search terminal status and record why fallback was skipped, distinct from ordinary nonconvergence.

### Method order and candidate choice
- **D-05:** A decoder configuration enables at most one of OSD, LSD, SI, or OTF. Compare methods in separate arms on matched physical samples; do not implicitly chain or race them. A source-defined SI/OTF procedure can still contain its own BP reruns, inactivation, graph work, and solve stages, all attributed within that method.
- **D-06:** If one fallback method yields multiple original-valid candidates, use its source-defined ranking for a source-faithful experiment. Use a prespecified common decoder-visible score and stable tie rule for controlled comparison, retaining the candidate set and provenance. Keep the two evaluation views explicitly labeled.
- **D-07:** If fallback yields no original-valid candidate, retain the chosen failed BP-only output as final. Record its original-problem validity and the unsuccessful fallback origin/status; never present the retained BP output as a fallback success.
- **D-08:** A fully reconstructed and original-validated fallback candidate remains eligible if later work in that fallback call reaches a cap. Retain the capped termination, partial work, and candidate lineage. Incomplete or unvalidated intermediate objects are not eligible.

### Literature TOML workflow
- **D-09:** Store each paper-linked runnable BP-plus-fallback variant as one complete seven-role TOML policy file, including its `[postprocessing]` binding. Keep one source-specific variant per file and preserve the existing strict preflight and executable/provenance identity separation. — **Reversibility:** costly — a changed public policy-file shape would require migration of saved variant files, resolved manifests, and replay receipts.
- **D-10:** When BP and fallback come from different sources, record separate component-level paper/revision and equation or algorithm anchors in the same file. Preserve the distinction between a source's complete composite and a canonical combination of components from different sources; prose cannot silently change executable numerical identity.
- **D-11:** Support both complete paper-linked variant files and controlled studies that derive fallback arms from one fixed BP policy plus declared registered fallback choices. Save a fully resolved manifest and provenance for every generated arm; no implicit runtime override should change an arm's identity.
- **D-12:** When SI or OTF source details remain unresolved, retain a non-runnable `.spec.toml` with explicit blockers. A separately named runnable canonical adaptation may coexist only after focused compatibility/equation/control-flow checks, with its adaptation and assessment status clear. Do not relabel that adaptation as source-faithful.

### Bounded Phase 7 evidence
- **D-13:** Keep the public CLI report and verified event ledger as durable evidence. Provide a compact shot-by-shot notebook for inspection, following the Phase 5 pattern. Display BP-only and final outcomes, fallback origin, candidate lineage, work, status, and native instrumentation missingness.
- **D-14:** Use the same prespecified, identified physical samples for a bounded B1 view with BP-only, each qualified runnable canonical fallback, and pinned native BP-OSD/BP-LSD composite arms. Native composite decoders retain distinct identities and their opaque internal work is marked unavailable where appropriate; they do not serve as the canonical BP engine.
- **D-15:** B1 is the primary matched demonstration code. Add focused deterministic fixtures on another suitable structure when a method's mechanism or compatibility requires it, without turning such fixtures into a cross-code performance ranking.
- **D-16:** Retain every prespecified B1 shot rather than selecting samples by observed BP outcome. Use separate deterministic fixtures to exercise both BP-success/no-fallback and BP-nonconvergence/fallback paths. Keep the sampled demonstration labeled as bounded, not a published-curve assessment.

### Researcher and planner discretion
- Resolve exact OSD/LSD standalone interfaces, reliability sign/order/method conventions, numerical behavior, source-revision/API drift, and method compatibility by primary-source and pinned-code investigation.
- Pin precise SI and OTF source variants and their inactivation/graph/BP/solve/reconstruction procedures; record paper/code discrepancies and any unavailable faithful path. Do not invent missing algorithm steps.
- Choose deterministic failed-attempt ranking, method-specific handoff contracts, finite B1 sample and work budgets, plot/table details, and module/schema names within D-01–D-16 and the project's existing truth-separation, evidence, and prespecification rules.

### Folded Todos
- **Make literature TOML a native policy-file input** (`.planning/todos/pending/literature-policy-toml-provenance-and-cli.md`, originally assigned to Phase 6): reconcile this todo with the already verified Phase 6 parser and public command, then extend that established route for fallback bindings, component-level source provenance, and controlled-study arm resolution. Do not redo completed Phase 6 behavior merely because the todo remains pending.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** Repository references use full relative paths.

### Scope and inherited decisions
- `.planning/PROJECT.md` — canonical-family architecture, BP-first priority, reproduction and provenance standards.
- `.planning/REQUIREMENTS.md` — POST-01–POST-05 and inherited ledger requirements.
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, dependencies, and Phase 8–9 boundary.
- `.planning/STATE.md` — current status, prior phase evidence, and open Phase 5 human visual review.
- `.planning/phases/06-beam-search-ensembles-and-candidate-selection/06-CONTEXT.md` — controlled search/relay candidate and matched-sample decisions.
- `.planning/phases/06-beam-search-ensembles-and-candidate-selection/06-VERIFICATION.md` — completed Phase 6 policy-file and three-paper gate status; native references remain separate.
- `.planning/phases/05-guided-and-perturbative-bp-interventions/05-CONTEXT.md` — bounded B1 pilot and shot-first notebook/evidence pattern.
- `.planning/research/ARCHITECTURE.md` — optional fallback boundary, SI/OTF interpretation, original-problem validation, and primary-source links.
- `.planning/research/SUMMARY.md` — standalone interface uncertainty, native composite distinction, and SI/OTF source starting points.

### Literature policy-file and source status
- `.planning/todos/pending/literature-policy-toml-provenance-and-cli.md` — folded todo; compare its requests with what Phase 6 already delivered before adding Phase 7 scope.
- `.planning/todos/pending/phase6-css-literature-vertical-slice.md` — reviewed but left with Phase 6.
- `literature_policies/README.md` — paper-folder, runnable-versus-specification, and qualification rules.
- `literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.toml` — existing seven-role runnable file with citations, equations, explanation, and unresolved-source provenance.
- `literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.spec.toml` — non-runnable source-specification pattern.
- `docs/researcher-study-command.md` — existing public policy-file and study command.
- `docs/css-literature-gate.md` — bounded matched CSS gate and provenance pattern.

### Execution and evidence contracts
- `src/bp_registry/literature.py` — current closed TOML parser, runnable/spec dispositions, executable/provenance identities, and source qualification.
- `src/bp_registry/canonical/contracts.py` — seven policy roles and currently identity-only postprocessing binding.
- `src/bp_registry/canonical/problems.py` — immutable original/working problems and candidate reconstruction boundary.
- `src/bp_registry/canonical/execution.py` — canonical attempt and policy lifecycle.
- `src/bp_registry/canonical/budgets.py` — leaf work vector, fallback-call counter, and scoped reservation pattern.
- `src/bp_registry/canonical/candidate_selection.py` — frozen candidate origins, eligibility, stable selection, and ranking patterns.
- `src/bp_registry/manifests.py` — strict versioned public composition admission and work limits.
- `src/bp_registry/ledger.py` — fallback event kind, structural replay, work, and terminal evidence.
- `src/bp_registry/reference.py` — current pinned native BP-only adapter and explicit opaque-counter missingness.
- `docs/canonical-engine.md` — public canonical semantics and evidence conventions.
- `docs/environment-freeze.txt` — current dependency freeze to check before pinning native BP-OSD/BP-LSD APIs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The canonical binary CSS engine has immutable original/working problems, intervention and search lineage, frozen candidate selection, hierarchical work limits, original-problem validation, and structural ledger replay.
- The seven-role composition already includes `postprocessing`, but only its `identity` kind is executable. `WorkVector` already reserves `fallback_calls`; ledger grammar already has a `fallback` event kind.
- The literature parser already retains citations, equations, explanations, and unresolved details separately from executable identity; runnable TOML and non-runnable `.spec.toml` files have established public meaning.
- A native `ldpc.BpDecoder` adapter reports observed SDK iterations and unavailable opaque internals; pinned BP-OSD/BP-LSD adapters can follow this reference/evidence distinction after their exact APIs are tested.

### Established Patterns
- Public policy files and manifests are closed, versioned, and preflighted. Source prose is provenance; it does not become executable code or alter numerical identity without changed controls.
- Search branches, relay legs, and ensemble members retain identities and leaf-level work; selection uses decoder-visible facts and freezes before independent truth-aware evaluation.
- Every shot keeps terminal evidence, including failure and interruption. Native internal metrics that the pinned API does not expose are reported unavailable with reasons, not zero.
- Earlier bounded B1 studies and Phase 5's shot-first notebook are inspectable mechanism evidence, not statistical reproduction.

### Integration Points
- Extend the postprocessing policy role, compatibility checks, public manifests/CLI, and literature compiler for one declared method per configuration.
- Transfer the selected failed BP state across an explicit reliability/problem interface; SI/OTF may perform method-internal transformed BP work, all linked under fallback lineage.
- Add method-specific fallback events, separate work leaves, original-space candidate validation, and BP-only/final outcomes to ledger verification and public inspection.
- Attach native composite references as independently identified arms on matched observations and samples, while preserving API limits and source/status labels.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly moved only the literature TOML/policy-file todo into Phase 7. The three-paper CSS gate todo remains with Phase 6, whose bounded gate is already verified.
- The selected fallback receives one best failed attempt after the complete search ends, not one fallback call per branch or relay leg.
- Source-faithful candidate ranking and controlled-study ranking are separate, as are paper-linked full TOML files and generated controlled arms.
- The B1 view is shot-matched and unfiltered; deterministic fixtures separately guarantee inspection of trigger and no-trigger paths.

</specifics>

<deferred>
## Deferred Ideas

- Publication-scale statistical campaigns, denominator rules, throughput profiling, and CSS paper-curve assessment remain in Phases 8–9. The bounded Phase 7 view must not claim method ranking or reproduction.
- Public policy-file voting remains assigned to Phase 9 per Phase 6 verification. Correlated quaternary and circuit compatibility remain in Phases 10–13.

### Reviewed Todos (not folded)
- **Execute first CSS literature gate in the Phase 6 replan** (`.planning/todos/pending/phase6-css-literature-vertical-slice.md`): left with Phase 6. Its bounded three-paper gate is verified; unresolved paper artifacts and full curve assessment follow the existing later-phase boundary.

</deferred>

---

*Phase: 07-Optional Postprocessing*
*Context gathered: 2026-10-05*
