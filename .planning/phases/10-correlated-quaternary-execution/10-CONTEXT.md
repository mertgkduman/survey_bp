# Phase 10: Correlated Quaternary Execution - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a public, canonical four-state Pauli BP execution path for joint X/Z code-capacity decoding. It must accept general stabilizer codes and compiled existing CSS artifacts; sample declared joint channels; independently classify outcomes; and execute only mathematically qualified quaternary policies. Phase 10 includes source-backed Q-BPGD, MBP4, and the full CSS affine subcode ensemble decoder (aSCED) requested during this discussion. Source-backed reference execution and bounded, replayable mechanism evidence belong here. Publication-curve assessment and controlled performance claims remain in Phase 11 after Phase 8's statistical gate. Phase 7 optional postprocessing remains paused.

The existing `10-RESEARCH.md` predates the aSCED decision. Research and planning must inspect the linked paper and author repository before treating aSCED's construction, overcomplete option, native execution, or source status as qualified.

</domain>

<decisions>
## Implementation Decisions

### Supported codes and evaluation
- **D-01:** The public quaternary path supports general stabilizer codes in Phase 10, including non-CSS Pauli check rows. Existing validated CSS artifacts can be supplied directly and compiled losslessly into that model, preserving their identity and an explicitly declared combined check/syndrome order. — **Reversibility:** costly — public artifact identity, manifests, and ledgers depend on this model boundary and ordering.
- **D-02:** A logical-operator basis is optional for running a general stabilizer code. The independent evaluator must use original-syndrome agreement and stabilizer-span membership to distinguish `invalid_syndrome`, `exact`, `stabilizer_equivalent`, and `logical_failure`. Without a supplied logical basis, the specific logical action is unavailable and must be marked as such; it is not inferred. — **Reversibility:** costly — changing this would invalidate stored outcome semantics and allowed code artifacts.
- **D-03:** Demonstrate the general path with at least one small non-CSS code through the public manifest, decoder, evaluator, and ledger, in addition to independent algebraic fixtures. This is an implementation check, not a statistical result.

### Joint Pauli channel
- **D-04:** Accept both a named depolarizing channel with physical rate `p` and an explicit `I/X/Y/Z` probability table. The explicit form may be one shared row or one row per qubit. Persist the resolved four probabilities for every qubit, channel identity, and declared ordering in manifests and ledgers. — **Reversibility:** costly — saved manifest and sample identities depend on these conventions.
- **D-05:** Physical sampling honors exact zeros. A log-domain decoder faced with any zero prior requires an explicitly configured and recorded smoothing rule; the smoothing changes decoder beliefs only, not the physical sampling distribution. Reject silent smoothing or silent normalization of malformed user channel tables.
- **D-06:** For a per-qubit table, report each physical non-identity rate as `1-P(I)`. Use a scalar `p` only when a named uniform channel defines it; do not label an average of heterogeneous rows as the experiment's physical `p`.

### Quaternary policy coverage
- **D-07:** Expose source-defined quaternary flooding and serial schedules, plus quaternary check-message normalization and offset as explicit policies with their own equations, order, and preflight compatibility checks. Existing binary policy names do not automatically qualify as quaternary policies.
- **D-08:** Implement source-defined MBP4 as a distinct quaternary recurrence after the required Q-BPGD path. It is not a port of the binary memory adapter.
- **D-09:** Individually source-backed quaternary policies may be combined when mathematical and lifecycle compatibility checks pass. If their combination is not source-defined, label the run a canonical adaptation and record its effective order and semantics. Unsupported combinations fail preflight; no source-fidelity claim follows merely from source-backed components.

### Affine subcode ensemble decoding
- **D-10:** Add the full paper aSCED method in Phase 10 for CSS codes: splitter-row construction/qualification, batches and all declared virtual-syndrome paths, original-syndrome-valid candidate selection by the paper's rule, and the overcomplete-check option. Keep the original code and measured syndrome immutable; attribute each path's graph, virtual syndrome, candidate, work, and termination. — **Reversibility:** costly — ensemble lineage, candidate selection, and work are persisted evidence contracts.
- **D-11:** The aSCED source-backed profile is CSS-specific. The general stabilizer kernel remains available for ordinary quaternary BP, but non-CSS aSCED is rejected until a separate splitter derivation and compatibility qualification exists. Do not generalize the paper's concrete CSS construction by name alone.
- **D-12:** Pin and run the authors' public `kit-cel/quantum_asced` repository as a bounded executable native reference and source guide. Keep its implementation, environment, numerical settings, instrumentation limits, and results distinct from canonical aSCED. It does not replace canonical policy execution.
- **D-13:** Run a bounded, prespecified, shot-matched Pauli-sample comparison of canonical aSCED and standalone BP4, with the qualified native aSCED reference on matched inputs where its interface permits. Retain every admitted shot, path-level work, and unavailable native counters with reasons. Label this evidence `not_assessed`; it cannot establish paper-curve reproduction or a performance ranking.

### Q-BPGD interpretations
- **D-14:** Continue committed Q-BP edge messages across decimation rounds while updating the chosen qubit's prior. Record this as a canonical interpretation of source-ambiguous buffer handling, subject to authoritative author-code findings; do not call it proven source-literal behavior.
- **D-15:** Preserve the paper's literal fixation weights `(1-ε, ε, ε, ε)` with the leading weight at the chosen Pauli. Record the raw vector, divide all four entries by their common sum for the probability interface, and record that ratio-preserving interpretation. Do not silently change the leading term to `1-3ε`.
- **D-16:** Resolve equal Q-BPGD reliability by lowest qubit index, and equal Pauli posterior components by `I < X < Y < Z`. Persist this deterministic interpretation for replay.
- **D-17:** Keep the depolarizing Q-BPGD setup as the source-backed profile. Q-BPGD with an arbitrary declared joint or per-qubit prior is permitted as a separately labeled canonical adaptation after compatibility checks.

### Planner and researcher discretion
- Select exact combined CSS syndrome row order, manifest/schema version, numerical profile and saturation, positive-prior smoothing options, finite fixture sizes, aSCED path caps, bounded run size, and paper-linked demonstration code before collecting evidence. Persist the chosen conventions; verify them independently. The user did not prescribe numerical values or a particular paper curve.
- Inspect aSCED's paper and pinned author revision for splitter generation, overcomplete matrices, BP4 settings, candidate tie behavior, reference entry points, and license/packaging constraints. Resolve source ambiguities explicitly; preserve missing native instrumentation as missing.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** Repository references use full relative paths; external primary sources use direct links.

### Scope and inherited contracts
- `.planning/PROJECT.md` — canonical kernel families, provenance, reproduction and comparison contracts.
- `.planning/REQUIREMENTS.md` — QBP-01 through QBP-04 and later QEV-01/QEV-02 boundaries.
- `.planning/ROADMAP.md` — Phase 10 goal, success criteria, sequence, and Phase 11 statistical boundary.
- `.planning/STATE.md` — current Phase 10 priority and paused Phase 7 status.
- `.planning/phases/10-correlated-quaternary-execution/10-RESEARCH.md` — existing quaternary mathematical and validation research; **refresh for aSCED and the now-required MBP4 scope**.
- `.planning/phases/06-beam-search-ensembles-and-candidate-selection/06-CONTEXT.md` — prior matched-sample and ensemble lineage decisions.
- `.planning/phases/07-optional-postprocessing/07-CONTEXT.md` — paused fallback scope and source-vs-controlled evidence rules.

### Existing public and mathematical surfaces
- `src/bp_registry/canonical/kernel.py` — binary kernel lifecycle and numerical operations to reuse only where mathematically justified.
- `src/bp_registry/canonical/execution.py` — canonical execution, original-problem evaluation boundary, and structural ledger integration.
- `src/bp_registry/canonical/problems.py` — immutable binary problem/candidate contracts requiring distinct Pauli types.
- `src/bp_registry/canonical/contracts.py` — closed policy kinds and preflight compatibility pattern.
- `src/bp_registry/canonical/budgets.py` — typed work, scopes, and reservation pattern.
- `src/bp_registry/sampling.py` — current separate X/Z sampler and truth/observation separation.
- `src/bp_registry/evaluator.py` — existing four outcome meanings and independent CSS checks.
- `src/bp_registry/manifests.py` — strict versioned public experiment schema.
- `src/bp_registry/cli.py` — public preflight, run, and verification entry points.

### External primary sources requested or governing the selected policies
- [Lai and Kuo, scalar LLR-BP4](https://arxiv.org/html/2104.00304) — source equations and commutation messages.
- [Yao et al., Q-BPGD](https://arxiv.org/html/2312.10950v2) — Algorithm 3 and fixation weights.
- [Kuo and Lai, MBP4](https://arxiv.org/html/2104.13659) — distinct modified quaternary recurrence.
- [Wursthorn et al., quantum aSCED v2](https://arxiv.org/html/2605.06547v2) — splitter theorem, CSS ensemble construction, overcomplete option, and reported setup; explicitly supplied by the user.
- [kit-cel/quantum_asced](https://github.com/kit-cel/quantum_asced) — public author repository, to pin and qualify as a native reference; explicitly identified during this discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The binary canonical engine already owns lifecycle, work scopes, lineage, candidate freezing, and independent original-problem evaluation. Quaternary execution can reuse those contracts while defining a separate four-state kernel and Pauli problem types.
- The current numerical layer has ordered stable box-plus primitives, but its binary numerical profile cannot silently identify a quaternary run.
- Strict manifest preflight, seeded shot identities, ledger verification, and source/evidence labels already provide the public integration pattern.
- The existing evaluator's four outcome names can be retained while general stabilizer membership and optional logical-action identification are implemented independently.

### Established Patterns
- Policy implementations receive decoder-visible state only; hidden truth remains with the evaluator.
- Transformed working problems and ensembles preserve original observations, branch identities, all attempted work, and explicit selection before truth-aware evaluation.
- Native implementations are executable references with separate identity and qualified missingness, not engines hidden behind a shared adapter.
- Bounded demonstrations remain `not_assessed`; Phase 8 prespecifies statistical campaign rules before Phase 11 reproduction claims.

### Integration Points
- Add a general Pauli artifact/compiler and lossless CSS import at the artifact/manifest boundary, with a separate Pauli sampler and original-problem evaluator.
- Add a quaternary compatibility registry and source-linked policy files to the existing public preflight/CLI route.
- Connect Q-BPGD, MBP4, and aSCED to the shared lifecycle, ledger, budgets, and candidate selection while preserving each policy's specific recurrence and working graph.
- Isolate the pinned author aSCED environment from canonical execution and connect its results to the same identified physical samples where qualified.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly requested the affine decoder at `https://arxiv.org/html/2605.06547v2#S4` and pointed to the public author repository. The selected scope is the **full paper method**, including its overcomplete option, not only one virtual-syndrome branch.
- For Q-BPGD, source-literal fixation ratios, continued messages, and stable ties are deliberately recorded as separate choices; unresolved source details must remain visible.
- The non-CSS end-to-end example proves the general kernel boundary, whereas paper-faithful aSCED remains CSS-specific.

</specifics>

<deferred>
## Deferred Ideas

- Non-CSS aSCED awaits a separate source/compatibility derivation; Phase 10 must reject it explicitly.
- Statistical quaternary reproduction and controlled comparisons remain in Phase 11 after Phase 8. Circuit decoding remains in Phases 12–13.

### Reviewed Todos (not folded)
- `.planning/todos/pending/literature-policy-toml-provenance-and-cli.md` — previously assigned to paused Phase 7; Phase 10 reuses the established policy-file route without absorbing that paused task.
- `.planning/todos/pending/phase6-css-literature-vertical-slice.md` — the bounded CSS literature gate was assigned to Phase 6; no new Phase 10 scope follows from its keyword match.

</deferred>

---

*Phase: 10-Correlated Quaternary Execution*
*Context gathered: 2026-10-06*
