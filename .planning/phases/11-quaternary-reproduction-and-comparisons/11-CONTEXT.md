# Phase 11: Quaternary Reproduction and Comparisons - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Qualify selected correlated code-capacity publication results, assess canonical quaternary reproduction against identified source targets with declared uncertainty, and compare joint Pauli inference with separate binary inference on identical physical samples. The phase also runs source-qualified quaternary policy ablations and matched complete-method comparisons with explicit work and resource evidence. Source-specific reproduction and controlled comparisons are separate evidence views. Circuit-level decoding belongs to Phases 12–13; paused optional postprocessing is not a prerequisite.

</domain>

<decisions>
## Implementation Decisions

### Publication targets and native reference
- **D-01:** Start with aSCED. Identify one exact reported paper result and reproduce its code, channel, decoder settings, stopping rule, denominator, and figure or table target. Assess ordinary and overcomplete aSCED separately when that result contains both; do not broaden the first target into an unspecified collection of curves.
- **D-02:** Use the pinned author repository to resolve canonical aSCED equations, construction, selection, and numerical details. Prioritize an independently qualified way to feed the *same injected Pauli errors* to native and canonical aSCED while preserving the author's algorithm. Record any input or instrumentation changes and maintain separate native and canonical identities. The existing Phase 10 native evidence is aggregate-only; it does not supply matched shots. If a faithful matched-input route is unavailable, record that gap rather than infer pairing.
- **D-03:** After the first aSCED target, qualify at least one reported result for each of Q-BPGD and MBP4 in Phase 11. Keep source gaps, failed assessments, and inconclusive assessments visible. The Phase 10 continued-message Q-BPGD and project-constructed aSCED runs remain canonical adaptations until source fidelity is established; apparent curve agreement alone cannot change their label.
- **D-04:** Apply the existing source-target receipt, manifest, uncertainty, and discrepancy rules to each selected result. Freeze target extraction, eligibility, tolerances, stopping, and resource bounds before assessment. Published settings and controlled-study settings remain distinct.

### Separate binary inference
- **D-05:** For the main controlled comparison, give the binary X and Z decoders the exact per-qubit marginals of the sampled joint channel: `q_X=P(X)+P(Y)` and `q_Z=P(Z)+P(Y)`. Neither binary decoder receives the within-qubit X/Z dependence. Persist the physical joint row and both derived priors so the inference difference is inspectable. — **Reversibility:** costly — changing the baseline beliefs would invalidate comparison identities and interpretation of saved paired results.
- **D-06:** Anchor the inference comparison with ordinary quaternary BP versus two ordinary canonical binary BP decoders. Add binary counterparts of named policies only when their semantics are independently qualified; do not claim every quaternary policy has a faithful binary port.
- **D-07:** Establish the matched comparison on the existing GB46 CSS artifact, then qualify a second CSS code before generalizing a finding beyond GB46. Keep code identity and observation mapping exact within every paired comparison.
- **D-08:** If one binary component does not satisfy its syndrome, combine all available terminal X/Z guesses and evaluate the resulting Pauli candidate against the immutable original problem. Keep each component's convergence, missing guess, and work separate from the pair's original-problem outcome; do not silently discard a partially nonconverged pair. — **Reversibility:** costly — terminal, denominator, and outcome semantics are stored in shot evidence.

### Correlation study
- **D-09:** Make the primary controlled channel sweep hold the X and Z marginals fixed while varying `P(Y)`, so the binary decoder priors remain unchanged. Record that the total non-identity rate `1-P(I)` can change across the sweep; never label the points as a fixed-`p` experiment.
- **D-10:** Include the independent X/Z channel as an anchor and valid channels with both less and more Y co-occurrence. Choose numerical points within the feasible four-probability bounds and prespecify them before running.
- **D-11:** Use one uniform I/X/Y/Z row across qubits in the primary sweep. A heterogeneous per-qubit check may be separately labeled if source qualification and measured resources support it; it is not part of the primary contrast.
- **D-12:** Make the prespecified lead analysis the *change in the paired logical-failure difference* between joint and separate inference as correlation changes. Report each arm's logical failure, convergence, denominator/uncertainty, work, and runtime separately. Do not presume the sign or size of the effect. — **Reversibility:** costly — changing the primary contrast after data collection would undermine the assessment plan.

### Policy ablations and fair work
- **D-13:** In the controlled policy study, change one mathematically compatible, source-qualified policy from ordinary quaternary BP at a time. Keep aSCED ordinary versus overcomplete construction as its own comparison. Unsupported combinations fail qualification; source-backed components alone do not make a new composition source-faithful.
- **D-14:** Run the policy ablations at three prespecified channel anchors: independence, one feasible lower-Y point, and one feasible higher-Y point at the same X/Z marginals. Avoid an unplanned all-policy-by-all-channel grid.
- **D-15:** Present two effort views: prespecified algorithmic work limits and measured runtime under the same declared hardware and time conditions. Retain typed work by algorithm and do not equate a four-state message update with a binary update without a qualified conversion. Include all attempted work, including decimation rounds and ensemble paths. — **Reversibility:** costly — budget definitions and work measures determine which results are comparable.
- **D-16:** After one-change ablations, compare complete, qualified BP4, Q-BPGD, MBP4, and aSCED configurations on matched samples at shared channel points and declared resources. Preserve their differing mechanisms and actual cost; keep this controlled comparison distinct from each paper's source-specific reproduction.

### Planner and researcher discretion
- Select the precise aSCED figure or table result, Q-BPGD and MBP4 targets, second CSS code, feasible channel probabilities, qualified policy swaps, numerical work definitions, sample sizes, uncertainty procedures, and campaign stopping rules from source evidence and measured resources. Prespecify these choices and retain inconclusive evidence.
- Determine whether the pinned native aSCED interface can accept externally supplied errors without altering algorithm semantics. The earlier approval covered a bounded isolated build/run; any materially changed native source or rights scope requires its own qualification. Do not treat the previous aggregate receipt as matched-shot evidence.
- Start with bounded profiling and replay checks. Phase 8's verified campaign infrastructure does not grant publication-scale HPC dispatch while site ceilings and scheduler accounting remain unmeasured.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** Repository references use full relative paths; primary paper and author-code references use direct links.

### Scope, statistical rules, and prior decisions
- `.planning/PROJECT.md` — canonical family architecture, source fidelity, provenance, and dual evaluation views.
- `.planning/REQUIREMENTS.md` — QEV-01 and QEV-02.
- `.planning/ROADMAP.md` — Phase 11 goal, dependencies, and success criteria.
- `.planning/STATE.md` — current phase, paused Phase 7, deferred Phase 5 review, and production gate status.
- `.planning/phases/10-correlated-quaternary-execution/10-CONTEXT.md` — quaternary semantics, aSCED scope, policy compatibility, and source interpretations.
- `.planning/phases/10-correlated-quaternary-execution/10-VERIFICATION.md` — verified Phase 10 kernel/evidence boundaries.
- `.planning/phases/10-correlated-quaternary-execution/10-15-SUMMARY.md` — exact bounded native aSCED build/run and aggregate-only observability.
- `.planning/phases/09-css-reproduction-and-controlled-comparisons/09-CONTEXT.md` — source qualification, honest adaptation labels, and separate reproduction/comparison views.
- `.planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-VERIFICATION.md` — paired campaign capabilities and denied production dispatch.
- `docs/campaigns.md` — existing campaign planning, assessment, and replay contract; qualify extensions for Pauli samples.

### Existing source and executable evidence
- `data/native/phase10-asced-source-spec.json` — pinned author revision, Pauli ordering, native interface limitations, and source discrepancies; its earlier approval status is superseded by the completed Phase 10 build/run record above.
- `data/native/phase10-asced-build-receipt.json` and `data/native/phase10-asced-run-receipt.json` — bounded isolated native evidence.
- `data/manifests/quaternary-gb46-asced.json` and `data/manifests/quaternary-gb46-bp4.json` — Phase 10 public GB46 manifest examples.
- `data/results/phase10-quaternary-b1-gate/study-receipt.json` — bounded canonical mechanism evidence; not a reproduction assessment.
- [Wursthorn et al., quantum aSCED v2](https://arxiv.org/html/2605.06547v2) and [kit-cel/quantum_asced](https://github.com/kit-cel/quantum_asced) — first source experiment and pinned author-code guide.
- [Yao et al., Q-BPGD](https://arxiv.org/html/2312.10950v2) — source target and decimation semantics.
- [Kuo and Lai, MBP4](https://arxiv.org/html/2104.13659) — source target and modified recurrence.

### Implementation surfaces to inspect
- `src/bp_registry/quaternary/sampling.py`, `evaluator.py`, `execution.py`, `compatibility.py`, `asced.py`, `qbpgd.py`, and `mbp4.py` — existing Pauli sample, outcome, policy, and ledger boundaries.
- `src/bp_registry/quaternary/native_asced.py` and `scripts/qualify_phase10_native_asced.py` — isolated native adapter, Pauli translation, and receipt verification.
- `src/bp_registry/campaigns/contracts.py`, `planning.py`, `execution.py`, `statistics.py`, and `targets.py` — paired CSS campaign pattern to qualify for quaternary use.
- `src/bp_registry/manifests.py` and `src/bp_registry/runner.py` — strict public quaternary manifest and run/replay entry points.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 10 has a canonical four-state Pauli kernel, joint sampler, independent original-problem evaluator, compatible Q-BPGD/MBP4 policies, ordinary/overcomplete aSCED, public manifests, and deterministic replay.
- Phase 8 has immutable paired physical samples, exact merge/resume, source-target receipts, statistical assessment, and profiling gates. Its current controlled execution is CSS-specific and needs a qualified Pauli path.
- The pinned native aSCED revision has an isolated build and verified aggregate receipt, plus an explicit I/X/Y/Z versus I/X/Z/Y translation. Its current binding does not expose shot identities or injected errors.

### Established Patterns
- Paper-specific settings, native references, and canonical adaptations have distinct identities and evidence labels.
- Hidden physical truth stays outside decoder policies; an independent evaluator judges terminal candidates against the original problem.
- Missing native instrumentation is recorded as unavailable, not zero. All attempted branches, paths, and interrupted work remain in evidence.
- Bounded mechanism studies and verified transport do not establish source-curve agreement or decoder superiority.

### Integration Points
- Extend campaign sample identity, manifest, shot ledger, merge/replay, and assessment to Pauli errors and paired quaternary/binary arms while retaining Phase 8 invariants.
- Derive exact binary marginals from each declared joint channel row and route the same sampled Pauli error to both inference families.
- Qualify paper targets and a native matched-input route against pinned source evidence before promoting any fidelity or statistical claim.

</code_context>

<specifics>
## Specific Ideas

- The user selected aSCED first because its author repository can help align the canonical implementation with the source, and requested matched native/canonical injected errors as a priority.
- The controlled dependence sweep deliberately permits physical `p` to change while binary X/Z priors stay fixed.
- The first inference comparison uses GB46; a second qualified CSS code is required before generalizing.
- Complete named-method results are desired alongside one-policy-at-a-time ablations, with every aSCED path and Q-BPGD round included in cost.

</specifics>

<deferred>
## Deferred Ideas

- A heterogeneous per-qubit channel check is optional and separately labeled after the primary uniform study; it does not expand the primary design.
- Circuit-level decoding and curves remain in Phases 12–13. Optional postprocessing remains paused in Phase 7, and Phase 5 human review remains deferred.

### Reviewed Todos (not folded)
- `.planning/todos/pending/literature-policy-toml-provenance-and-cli.md` — already addressed as a Phase 9 starting contract; its keyword match does not create new Phase 11 work.
- `.planning/todos/pending/phase6-css-literature-vertical-slice.md` — the CSS literature gate was previously assigned and reviewed; it is not a quaternary target.

</deferred>

---

*Phase: 11-Quaternary Reproduction and Comparisons*
*Context gathered: 2026-10-12*
