# Phase 9: CSS Reproduction and Controlled Comparisons - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Mode:** Autonomous discussion from locked project and prior-phase decisions; no new user choices were solicited.

<domain>
## Phase Boundary

Qualify and assess selected published CSS code-capacity experiments, then compare eligible canonical BP mechanisms on matched samples and declared budgets. Finish the public voting policy-file, execution, original-problem validation, and replay path. Phase 8 supplied campaign machinery; this phase must supply source-specific evidence, scientific design, and CSS results.

</domain>

<decisions>
## Implementation Decisions

### Source experiment qualification
- **D-01:** Start from the user-approved three-paper CSS gate: Yao BPGD, Bhatnagar impulse, and Rabeti–Mahdavifar MBBP-LD. The 14 source specifications and three selected runnable adaptations are the inventory, not evidence of source-faithful reproduction. Research may prioritize points within this set by source completeness and feasible cost; retain an explicit status for every selected variant and target.
- **D-02:** Before a source-faithful label, check the ordered paper-experiment code and logical identities, original implementation and settings, noise/denominator/stopping rules, and exact figure/table target. Unresolved facts remain typed gaps. A canonical adaptation may be assessed as an adaptation but never promoted by apparent numerical agreement alone.
- **D-03:** Extract or digitize paper targets with pinned source revisions, figure or table identity, extraction precision, and target uncertainty; freeze tolerances and acceptance rules before assessing simulation output. Record discrepant and inconclusive outcomes as well as passes.

### Controlled comparisons
- **D-04:** Use Phase 8's paired campaign and exact replay contracts. Keep paper-specific reproductions separate from cross-paper controlled comparisons. Fix code, noise, physical samples, eligibility, work limits, and outcome denominators for each comparison before evaluation; report actual work and runtime, not just configured limits.
- **D-05:** Stage a focused question-driven design around update/schedule, memory/intervention, and search/selection mechanisms. Carry forward Phase 6's matched initial BP and distinct extra-work accounting for BeamSearch and RelayBP; do not revive the cancelled Phase 4 448-shot/14-arm grid. Qualify optional fallback methods independently before interpreting their effects.

### Compute and evidential scope
- **D-06:** The user set no fixed HPC limits and directed measurement first. Use bounded development and profiling runs to obtain actual wall time, cores, memory, storage, and scheduler facts. Do not infer site ceilings or authorize publication-scale Slurm dispatch while the Phase 8 production gate is denied. Predefine feasible sample-size and precision calculations before any larger campaign.
- **D-07:** Retain every attempted shard, interruption, failed/inconclusive assessment, and resource receipt. A small operational gate establishes execution and replay only; it cannot establish a paper curve or decoder ranking.

### Voting
- **D-08:** Expose an explicitly declared eligible ballot set and voting object in a public decoder file. Execute the existing Phase 6 coordinate-majority primitive only with compatible candidates; retain every ballot and lineage; independently validate the aggregate against the original syndrome; make the terminal ledger replayable.
- **D-09:** Compare voting to list-selection controls on the same physical samples and declared work budgets. Keep ties, abstentions, invalid ballots, and no eligible candidate visible in the ledger and assessment.

### Agent's Discretion
- Select the first feasible B1 source point and a smaller algebraic fixture for vertical tracer verification, provided source qualification gates and adaptation labels remain explicit.
- Choose concrete statistical precision, family correction, and stopping parameters from a prespecified power/cost analysis and source evidence. Do not represent these as prior user decisions.

### Folded Todos
- **Make literature TOML a native policy-file input:** Complete the remaining source-variant qualification and use the existing public TOML route, including the Phase 9 voting policy. The earlier Phase 6 gate established bounded execution for selected adaptations.
- **Execute first CSS literature gate in Phase 6 replan:** Treat the completed three-paper gate as the Phase 9 starting inventory, without rerunning it as a substitute for curve assessment.

</decisions>

<canonical_refs>
## Canonical References

**Downstream research, planning, and execution must read these before making reproduction claims.**

### Scope and prior decisions
- `.planning/PROJECT.md` — research scope, evidence labels, and two evaluation views.
- `.planning/REQUIREMENTS.md` — EVAL-01–03 and CAN-02.
- `.planning/ROADMAP.md` — Phase 9 goal, success criteria, dependencies, and cancelled-grid carry-forward.
- `.planning/notes/css-literature-policy-gate.md` — approved initial paper set, policy-file path, and B1 identity warning.
- `.planning/phases/06-beam-search-ensembles-and-candidate-selection/06-CONTEXT.md` — matched initial BP, Relay/Beam extras, and explicit adaptation semantics.
- `.planning/phases/06-beam-search-ensembles-and-candidate-selection/06-LITERATURE-GATE.md` — user-approved three-paper CSS gate.
- `.planning/phases/08-reproducible-campaigns-and-statistical-assessment/08-VERIFICATION.md` — verified campaign capabilities and denied production authorization.

### Registry and source-gap records
- `literature_policies/README.md` — source-specification versus runnable-adaptation status path.
- `literature_policies/qualification-v1.json` — current per-variant blockers and qualification.
- `literature_policies/yao-2024-guided-decimation/paper_reproduction/PAPER.md` — Yao target inventory and unresolved code/implementation/curve facts.
- `literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/PAPER.md` — impulse target inventory and unresolved settings.
- `literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/PAPER.md` — MBBP-LD target inventory and missing source partition details.
- `docs/campaigns.md` — installed campaign planning, run, replay, assessment, and profiling contract.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bp_registry/campaigns/` — strict identities, target receipts, planning, immutable shards, statistical assessment, reports, and profiling gate.
- `src/bp_registry/literature.py` and `scripts/run_css_literature_gate.py` — public policy-file compilation and prior three-paper B1 execution path.
- `src/bp_registry/canonical/` — policy execution, candidate lineage, independent verification, and Phase 6 voting primitive.

### Established Patterns
- Source `.spec.toml` records are non-runnable; qualified `.toml` files are labeled canonical adaptations until exact source identities are resolved.
- The Phase 8 two-sample BB-144 gate is a development fixture with verified paired delivery and replay, zero accepted shots, and no source-curve verdict.
- Hidden simulation truth stays outside decoder policies; the independent evaluator judges original-problem output.

### Integration Points
- Paper-specific reproduction manifests and target receipts connect to `campaigns/` without changing the canonical execution engine's truth boundary.
- The public decoder-file parser and canonical candidate selection/voting execution need a complete voting and replay contract.
- Publication reports consume verified ledgers and assessment receipts, preserving evidence labels and resource context.

</code_context>

<specifics>
## Specific Ideas

- First candidate targets are B1 code-capacity figures identified in the three paper folders. Their common `B1` name does not prove identical ordered matrices or logical bases.
- The bounded three-paper gate produced two rows per paper and public replay receipts; those rows are command/mechanism evidence only.
- First campaign sizing should use measured representative resource use and explicit precision/power, per the user's “No fixed limits yet; measure first.”

</specifics>

<deferred>
## Deferred Ideas

- Correlated quaternary source-curve reproduction belongs to Phase 11 and circuit-level curves to Phase 13.
- Phase 5 notebook/HTML human review remains pending and is not marked passed by Phase 9 work.

</deferred>

---

*Phase: 9-CSS Reproduction and Controlled Comparisons*
*Context gathered: 2026-10-11*
