# Phase 3: Update Rules and Scheduling - Context

**Gathered:** 2026-09-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the canonical binary CSS engine with min-sum, normalized min-sum, and offset min-sum, alongside sum-product; add layered, check-node serial, variable-node serial, residual, randomized, and source-defined cluster-sequential schedules. Researchers configure these policies without editing the engine for each experiment, inspect their semantics and work, and run bounded matched pilots with tables, plots, and a runnable analysis notebook.

This phase implements UPD-01–03 and SCH-02–06. It inherits Phase 2's policy lifecycle, numerical reproducibility, independent evaluation, immutable problem identity, provenance, and work-budget contracts. It prepares parameter diversity but does not implement ensemble execution, BPGD interventions, or statistical reproduction campaigns.

</domain>

<decisions>
## Implementation Decisions

### Update-rule parameters and diversity
- **D-01:** Support fixed scalar, iteration-dependent, and check-/edge-specific normalization and offset parameters. The user's motivation is decoder diversity. Effective assignments and their application semantics must be explicit and recorded.
- **D-02:** Accept both explicit parameter assignments and seeded generation from declared distributions. Preserve generator specification, seed identity, graph association, and resolved assignments with sufficient evidence for replay.
- **D-03:** Parameter refresh is configurable: fixed per decoder configuration across shots, fresh per attempt, or fresh per iteration. Define the iteration boundary for each schedule rather than assuming flooding semantics apply universally.
- **D-04:** Keep parameter-generation randomness, schedule-order randomness, and physical-error sampling independently identified. Changing decoder policies must not change matched physical-error samples.
- **D-05:** Allow exploratory parameter ranges and assignment rules beyond published variants, subject to mathematical and numerical validity checks. Keep source-defined presets and exploratory configurations separately labeled; exploratory flexibility does not establish source-faithful reproduction.

### Schedule order and convergence
- **D-06:** Implement both check-node serial and variable-node serial as distinct declared schedules. Each specifies its update unit, traversal order, and fresh/stale-message visibility. Individual-message serial was not selected for this phase.
- **D-07:** Layered scheduling accepts source-defined or user-supplied explicit partitions and a deterministic graph-based automatic construction. Record construction rules, actual layer membership, and order; validate compatibility with the declared update semantics. Generic layer construction must not be mislabeled as a published cluster-sequential algorithm.
- **D-08:** Randomized traversal supports an order fixed per configuration, redrawn per attempt, or reshuffled per sweep. Persist the refresh rule and independently replayable randomness identity.
- **D-09:** Check convergence after every completed local update unit: each layer, serial node update, or residual-selected update. Flooding retains its complete-sweep boundary. Research must define the selected cluster schedule's local unit and resulting stopping boundary explicitly. This is the selected behavior, not an optional sweep-only default.
- **D-10:** Count every convergence check and enforce hard work budgets independently of convergence-check cadence. Preserve schedule-qualified iteration counts, local progress, and actual work so stopping partway through a traversal is interpretable. If source stopping differs from the selected cadence, disclose the adaptation rather than claiming unchanged source semantics.

### Residual and cluster-sequential source choices
- **D-11:** Research primary sources and select one well-specified, source-linked baseline for residual scheduling and one for cluster-sequential scheduling. Document why each was chosen, its exact procedure, and unresolved source details. The user delegated these source selections to research.
- **D-12:** Residual scheduling implements only the pinned baseline and its source-defined parameters in Phase 3. Do not add exploratory priority scoring, tie-breaking, or selection-rule variants. Explicitly define residuals, cache/priority invalidation, selection, and their work costs.
- **D-13:** If the selected cluster source uses learned or optimized parameters, load pinned parameter artifacts only. Reproducing the training or optimization procedure is deferred. This does not assume that every cluster schedule requires learning, nor does it waive the source-defined construction/order requirement. Research must establish artifact availability and compatibility with the intended code before claiming support.
- **D-14:** Report schedule setup costs and decoding costs separately, without assumed amortization across shots. Costs of producing imported parameter artifacts remain explicitly unknown if unavailable; they are not zero.

### Pilot comparison design and outputs
- **D-15:** Use focused comparisons: vary update rules under flooding, vary schedules under sum-product, then exercise selected compatible combinations and parameter-diversity examples. The full Cartesian product is not required. Maintain explicit rejection of undefined combinations and matched physical-error samples.
- **D-16:** Provide both budget views: common check-to-variable message-update caps, and schedule-qualified iteration limits. Retain the full atomic work vector and measured runtime in both views; separately expose scheduling, residual evaluation/priority maintenance, and convergence-check work. Neither equal iteration limits nor equal message-update caps imply equal total cost.
- **D-17:** Beyond small deterministic correctness fixtures, pilot coverage includes the existing pinned BB-144 artifact, an HGP example from the user's requested classical LDPC construction family, and B1. The user specified HGP constituents with degree (3,4) or constructed using PEG, pointed to the BPGD paper, and explicitly added B1. Research must trace the construction, exact instances, ordering, and logical operators; matching dimensions or a family label does not establish artifact identity.
- **D-18:** Deliver tables, diagnostic plots, and a runnable analysis notebook. Cover evaluated outcomes, convergence, schedule-qualified iterations, raw work, setup/decoding runtime, and selected convergence traces. Preserve underlying evidence and use bounded representative traces under the inherited tracing contract.
- **D-19:** Keep Phase 3 results labeled as pilots/adaptations as appropriate, with assessment status explicit. Small pilots do not establish statistical curve reproduction or justify decoder rankings beyond the observed evidence. Independent algebraic and policy-semantics checks remain required.

### Agent's Discretion and Research Responsibilities
- Select and justify the residual and cluster source baselines under D-11–13.
- Resolve exact equations, parameter-validity domains, graph-parameter application points, iteration/refresh boundaries for irregular schedules, residual invalidation semantics, and cluster compatibility from primary sources. These technical details remain research tasks rather than user-specified formulas.
- Choose concrete module/schema extensions, bounded pilot sample counts and error-rate points, parameter-diversity examples, and presentation details consistent with the decisions above. No large campaign or compute allocation was authorized by this discussion.
- Resolve and validate the requested HGP and B1 artifacts. C2 is a source lead, not a confirmed match to the user's (3,4)-regular/PEG construction preference. Record any unresolved artifact gap explicitly; do not silently replace a requested code or claim exact paper identity for a generated substitute.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and inherited decisions
- `.planning/PROJECT.md` — canonical engines, research priority, independent evaluation, and reproduction meaning.
- `.planning/REQUIREMENTS.md` — UPD-01–03, SCH-02–06, and inherited engine/evidence requirements.
- `.planning/ROADMAP.md` — Phase 3 success criteria and boundaries from subsequent policy and campaign phases.
- `.planning/phases/01-evidence-registry-and-native-css-baseline/01-CONTEXT.md` — source and artifact identity, pilot labeling, and initial code-family preferences.
- `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md` — policy ownership, numerical profiles, random tie rules, budgets, work vectors, profiling, and trace/lineage contracts.

### Source research and code identity
- `data/evidence/seed-records.json` — pinned BPGD v2 experiment records and primary-source anchors, including B1 and C2.
- `data/evidence/code-inventory.json` — verified BB-144 identity and unresolved B1/C2 artifact status at discussion time.
- `.planning/phases/01-evidence-registry-and-native-css-baseline/01-RESEARCH.md` — prior artifact investigations; B1 and C2 must not be conflated.
- `.planning/research/FEATURES.md` — update/scheduling mechanism leads and source qualifications.
- `.planning/research/SUMMARY.md` — reconciled source findings and unresolved details.

The user specifically referenced the external [BPGD paper, arXiv:2312.10950v2](https://arxiv.org/html/2312.10950v2), especially the code examples in Section 4.5. Its local source records are listed above; read the primary source and follow its construction references during research.

### Existing canonical implementation
- `src/bp_registry/canonical/contracts.py` — typed policy roles, closed supported-policy registry, and evidence contracts to extend.
- `src/bp_registry/canonical/numerics.py` — historical CPU float64 LLR profile, saturation, degree-one and tie semantics; preserve existing profile meanings.
- `src/bp_registry/canonical/kernel.py` — inspectable SPA primitives and deterministic hard decisions.
- `src/bp_registry/canonical/schedules.py` — canonical edge table, flooding buffers, kernel protocol, and work proposal.
- `src/bp_registry/canonical/execution.py` — lifecycle execution, atomic flooding reservations, candidate evaluation, and terminal accounting.
- `docs/canonical-engine.md` — public execution, numerical, policy, and measurement contracts.
- `docs/profiling-and-tracing-strategy.md` — representative and rare-event traces, cohort interpretation, replay, and explicit missingness.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EdgeTable` supplies stable check-major/variable-minor edge identities for graph-indexed parameters and schedule order.
- `BinarySpaKernel` exposes separate prior, check-message, belief, variable-message, and candidate operations. These provide concrete boundaries for additional update rules.
- `FloodingSchedule` and `FloodingSweep` define the existing double-buffered baseline and proposed directional-message/belief/check work.
- The current engine already provides truth-separated evaluation, lineage, finite numerical checks, typed policy evidence, budget reservations, and bounded tracing/profiling infrastructure.
- The BB-144 artifact and evidence inventory supply a verified pilot baseline and documented leads for the additional requested codes.

### Established Patterns
- Persisted configurations use explicit closed policy bindings and versioned numerical meanings. New schedule names need actual registered semantics and evidence, not label substitution.
- Canonical execution owns lifecycle traversal; policies receive bounded decoder-visible views. Hidden truth remains outside selection and scheduling.
- Atomic work is reserved before state mutation, committed at leaf scope, and aggregated without double counting. Native iterations and canonical work are not interchangeable.
- Historical floating-point/clipping and flooding semantics must remain reproducible when introducing new profiles or scheduling behavior.

### Integration Points
- The current execution path explicitly constructs `FloodingSchedule` and `AtomicFloodingExecutor` and emits flooding-specific iteration metadata. Planning must generalize these integration points within the canonical engine for the new schedules and local stopping units.
- Extend strict policy/composition validation and numerical profiles for parameterized update rules and compatible schedules.
- Preserve one canonical execution path per compatible family while adding source-defined scheduling state, invalidation, work reporting, and replay identities.
- Extend pilot configuration and analysis around the existing evidence/evaluator flow; link notebook outputs and bounded diagnostic traces back to their inputs and ledgers.

</code_context>

<specifics>
## Specific Ideas and Source Qualifications

- User rationale: "We may try decoder diversity" motivated check-/edge-specific and varying normalization/offset parameters.
- User code preference: "the family is HGP of 3,4 regular degree or PEG classical LDPC codes. BPGD paper has these"; subsequent addition: "also B1".
- The [BPGD v2 performance-comparison section](https://arxiv.org/html/2312.10950v2#S4.SS5) reports B1 `[[882,24,18<=d<=24]]` and C2 HGP `[[1922,50,16]]`. The requested (3,4)-regular/PEG constituent construction was not established by the discussion's source check; trace the original construction references during research rather than asserting C2 satisfies that preference.
- At discussion time the local inventory marks exact B1 and C2 matrices and ordered logicals unresolved. This is a concrete research task, not evidence that these codes are already runnable.
- Existing Phase 2 context contains residual-scheduling source leads. They are starting points for the delegated baseline selection, not newly approved exact variants.

</specifics>

<deferred>
## Deferred Ideas

- Ensemble execution remains in Phase 6; Phase 3 supplies replayable parameter diversity and comparison examples.
- Reproducing learning or optimization for imported cluster parameters is deferred; Phase 3 loads pinned artifacts only.
- Exploratory residual selection rules and individual-message serial scheduling were not selected for Phase 3.
- BPGD intervention execution remains in Phase 5; using its code examples here does not implement BPGD.
- Statistical campaigns and paper-curve reproduction remain in Phases 8–9 for CSS experiments.

</deferred>

---

*Phase: 03-Update Rules and Scheduling*
*Context gathered: 2026-09-23*
