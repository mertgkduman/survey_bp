# Phase 2: Canonical CSS Execution and Policy Contracts - Context

**Gathered:** 2026-09-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a project-owned binary sum-product BP engine with flooding, explicit typed policy composition, reproducible numerical semantics, scoped budgets, trustworthy outcome evaluation, queryable computational attribution, and researcher-facing documentation. Phase 2 establishes contracts that later update, scheduling, memory, intervention, search, and postprocessing policies extend; it does not implement the later named policy families themselves.

</domain>

<decisions>
## Implementation Decisions

### Policy composition and lifecycle
- **D-01:** Persisted canonical manifests explicitly name all seven policy roles: update, schedule, state/memory, intervention, stopping, selection, and postprocessing. Inactive roles use explicit identity/no-op policies; user-facing helpers may supply defaults. — **Reversibility:** costly — changing omission/default semantics later would require a manifest migration and could make saved experiments resolve differently.
- **D-02:** Enforce compatibility in layers: reject statically known incompatibilities during manifest validation or composition, then enforce live-state invariants at runtime.
- **D-03:** Policies receive capability-scoped, decoder-visible views, own only their declared private state, and return typed decisions or mutations for the engine to validate and apply. Policies never receive sampled hidden truth.
- **D-04:** Use an engine-owned hierarchical lifecycle with named hooks at shot, search, member/leg/branch, attempt, iteration, and message scopes. — **Reversibility:** costly — the lifecycle becomes the shared contract for later policy families, ledger lineage, budgets, and external documentation.
- **D-05:** The schedule policy owns message ordering within an attempt. The intervention/search policy owns independent diversity members, branches, restarts, and sequential relay legs. Relationship (`independent`, `restarted`, `branched`, `relayed`), execution topology (`sequential`, `concurrent`, `batched`), state transfer, and budget scope are separate declared dimensions.
- **D-06:** Diversity members start as siblings from a declared problem state and may run in parallel. Relay-style legs are sequentially attributable attempts and may transfer only a named, typed, source-defined payload; they do not inherit arbitrary predecessor internals.
- **D-07:** A policy family may bind at multiple named hooks only through distinct binding IDs with declared hook, state lifetime, ownership, and event attribution. Unsupported source semantics require a versioned lifecycle extension or documented composite controller, not arbitrary global policy ordering.

### Numerical reproducibility
- **D-08:** A run selects a versioned named numerical profile, while its resolved manifest and ledger materialize every effective convention and override. — **Reversibility:** costly — profiles become durable meanings referenced by saved experiments.
- **D-09:** The Phase 2 reference profile uses deterministic CPU `float64`, stable LLR-domain sum-product formulas, and explicit clipping. Reduced precision, fixed point, and alternative backends are separately named profiles rather than silently equivalent implementations.
- **D-10:** Apply finite, profile-defined saturation at named calculation boundaries. Unexpected `NaN` or infinity is a recorded numerical failure and terminal event, not a silently propagated value.
- **D-11:** Every tie class has an explicit deterministic profile rule, normally canonical index/order. Random tie resolution is permitted only through a declared randomized policy with replayable decoder-local randomness independent of physical-error sampling.

### Budgets, work, runtime, and profiling
- **D-12:** Count-based budgets are hard hierarchical caps at attempt, member/leg, search, and shot scope. A child can consume only remaining ancestor allowance; termination records the binding scope, resource, configured limit, consumption, and reason.
- **D-13:** Record work once at its leaf source and derive ancestor totals through lineage, avoiding double counting. Phase 2 uses simple CPU boundary checks; later parallel backends may reserve bounded work chunks under the same semantic contract. Wall-clock limits are operational controls checked at declared synchronization boundaries.
- **D-14:** Conventional iteration count remains a prominent, easily queried headline metric because it is common in the literature. Every count carries schedule-qualified semantics; iterations from different schedules are not silently equated.
- **D-15:** Retain an atomic work vector beneath iteration counts, including check-to-variable and variable-to-check updates, belief assemblies, residual/priority evaluations where applicable, BP calls, candidate checks, and other separately meaningful work. Do not collapse these into a universal cost scalar.
- **D-16:** Record same-machine measurements alongside algorithmic work: wall time, process CPU time, peak host memory, concurrency/thread context, machine/environment identity, and backend-specific device time and memory when observable.
- **D-17:** Profiling is optional but enabled by default and can be turned off. Unavailable or permission-blocked counters are explicit missing data unless a strict profiling plan required them.
- **D-18:** Benchmark profiling uses three cohorts: the full clean population for outcomes and runtime; a prespecified representative paired clean/profiled cohort for unbiased profiling and overhead estimation; and targeted rare-event/tail replays for deep diagnosis. Outcome-conditioned profiles cannot stand in for population estimates without explicit selection probabilities and weighting.
- **D-19:** Profile replays link clean/profile run IDs, manifest and sample identity, decoder randomness/order identity, selection stratum/reason, and semantic agreement. Divergent replays remain diagnostic but cannot be presented as measuring the original clean execution. Low-overhead bounded traces cover rare race-sensitive behavior that cannot be replayed.
- **D-20:** Phase 2 must create `docs/profiling-and-tracing-strategy.md`, explaining scientific value, costs, trace/profiling levels, cohorts, overhead, replay, plotting, missingness, and retention. Representative examples and rare events are the primary targets for detailed profiling and plotting.

### Ledger, traces, and candidate lineage
- **D-21:** The default durable ledger is sparse and structural: shot and nested control-flow lifecycle, meaningful policy actions, interventions, relay transfers, candidates, terminations, aggregate iterations/work/runtime, and explicit missingness. Routine per-iteration or per-message records are not emitted for every production shot.
- **D-22:** Iteration summaries and edge/message traces are budgeted, filterable, linked sidecars for representative examples, rare events, profiling cohorts, and deterministic fixtures. Every trace plan declares record/byte limits; truncation is explicit and never silent.
- **D-23:** Represent original/working problems, transformations, attempts, members/legs/branches, candidates, lifts, validations, and selections as an immutable append-only lineage graph with stable IDs and typed parent edges. — **Reversibility:** costly — later intervention and search policies depend on these identities for lifting, attribution, and auditability.
- **D-24:** Use tiered content-addressed candidate retention. Persist selected candidates fully; retain stable identity, hashes, decoder-visible scores, validations, lineage, and reasons for every candidate; preserve full rejected payloads only when required by a trace plan, rare-event cohort, or bounded candidate policy.
- **D-25:** Freeze and record selection using decoder-visible evidence before truth-aware evaluation. The independent evaluator may then annotate every emitted candidate for research analysis, but those annotations can never feed back into decoder policies or selection.
- **D-26:** Phase 2 must create `docs/research-novelty-and-depth-register.md` as a living register of potential methodological contributions, executable evidence, closest known precedents, unresolved searches, and claim maturity. Profiling and selective per-iteration tracing are initial entries. Recheck precedents as the mapping study matures and before manuscript novelty claims are finalized.

### the agent's Discretion
- Choose exact Python type/module names, hook identifiers, event field names, and the initial numerical-profile identifier while preserving the locked semantics above.
- Choose practical default trace budgets, representative-cohort fractions, rare-event replay quotas, and locally available profiler adapters; all choices must be explicit and configurable.
- Choose content-addressed storage layout and bounded rejected-candidate retention thresholds without weakening lineage or missingness guarantees.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase contract
- `.planning/PROJECT.md` — canonical-engine architecture, hidden-truth boundary, reproduction meaning, and evaluation views.
- `.planning/REQUIREMENTS.md` — Phase 2 requirements ENG-01–06, SCH-01, LED-02–04, and DOC-01.
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, research focus, and boundary from later policy phases.
- `.planning/phases/01-evidence-registry-and-native-css-baseline/01-CONTEXT.md` — prior decisions on source identity, pilot labeling, independent evaluation, and provenance.

### Research safeguards
- `.planning/research/ARCHITECTURE.md` — proposed immutable original problem, working-state, evaluator, policy, and evidence separation.
- `.planning/research/PITFALLS.md` — numerical, outcome, source-identity, accounting, and instrumentation hazards.
- `.planning/research/FEATURES.md` — named BP mechanisms and source/implementation leads.
- `.planning/research/SUMMARY.md` — reconciled research findings and unresolved source questions.

### Existing implementation contracts
- `src/bp_registry/manifests.py` — strict frozen manifest/preflight and environment/artifact identity patterns to extend.
- `src/bp_registry/sampling.py` — current separation of decoder-visible observations from hidden truth.
- `src/bp_registry/evaluator.py` — independent original-problem outcome evaluation.
- `src/bp_registry/ledger.py` — durable begin/terminal ownership, reconciliation, missingness, and summary patterns.
- `src/bp_registry/runner.py` — current manifest-to-sampling-to-native-reference-to-evaluator integration path that canonical execution will complement.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ManifestV1` and strict frozen Pydantic models provide the preflight pattern for a versioned canonical manifest without changing historical native manifests in place.
- `ShotSample`, `DecoderObservation`, and `HiddenTruth` already separate decoder inputs from evaluator-only truth; the canonical engine should accept a narrower observation/problem boundary rather than a full `ShotSample`.
- `evaluate_candidate` independently judges candidates against the original CSS code and hidden errors and can remain outside the policy boundary.
- `LedgerWriter` provides durable append, per-shot ownership, explicit missingness, and interrupted-run reconciliation that the richer event vocabulary can extend or version.
- CSS artifact loading and semantic hashes already provide immutable matrix/logical identities for original and working-problem lineage.

### Established Patterns
- Persisted schemas are strict, frozen, version-dispatched, and reject extras rather than coercing or silently defaulting.
- Physical sampling is deterministic from manifest identity and shot ID; decoder-local randomness must remain independently identified.
- Outcomes are reconstructed from terminal evidence and independently checked rather than trusted from decoder self-report.
- Unavailable native counters are `null` with reasons, never reconstructed as observed fact or reported as zero.

### Integration Points
- Add canonical policy and execution modules beside the native `reference.py` path; do not delegate the canonical update loop to `ldpc.BpDecoder`.
- Extend manifest resolution to distinguish native-reference and canonical-policy execution while preserving replay of Phase 1 records.
- Feed canonical terminal candidates into the existing independent evaluator through the original-problem boundary.
- Version or extend the ledger for nested IDs, typed events, work deltas, lineage, trace sidecars, profiling links, and queryable summaries.
- Extend the CLI/runner with an installable tutorial path and small deterministic fixtures while retaining the Phase 1 pilot command.

</code_context>

<specifics>
## Specific Ideas

- Message scheduling is algorithmic, not arbitrary cross-policy ordering: flooding, sequential/layered, and residual schedules differ in stale/fresh-message semantics and convergence. Primary leads: [Vila Casado et al.](https://arxiv.org/abs/cs/0702111) and [Elidan et al.](https://robotics.stanford.edu/~koller/Papers/Elidan%2Bal%3AUAI06.pdf).
- BPGD supplies the source pattern for BP rounds separated by convergence checks and decimation rather than freely reordered hooks: [Yao et al.](https://arxiv.org/abs/2312.10950).
- Impulse decoding motivates independent parallel diversity members whose transformed candidates are lifted to the immutable original problem: [Bhatnagar et al.](https://arxiv.org/abs/2606.18240).
- RelayBP motivates sequential legs with disordered memory, candidate accumulation, and typed posterior relay rather than arbitrary shared state: [Müller et al.](https://arxiv.org/abs/2506.01779).
- Profiling design should account for sampling blind spots and intrusive GPU replay/serialization; useful methodological leads include the [HPCToolkit manual](https://hpctoolkit.org/manual/HPCToolkit-users-manual.pdf), [Google-Wide Profiling](https://research.google/pubs/google-wide-profiling-a-continuous-profiling-infrastructure-for-data-centers/), [NVIDIA Nsight Compute guidance](https://docs.nvidia.com/nsight-compute/ProfilingGuide/), and [Rapid Profiling via Stratified Sampling](https://minds.wisconsin.edu/handle/1793/11182).
- Any later novelty claim about profiling, selective tracing, candidate-lineage analysis, or algorithmic bottleneck attribution remains provisional until checked against the evolving systematic mapping corpus.

</specifics>

<deferred>
## Deferred Ideas

- Full CPU/GPU profiler-adapter coverage and production GPU kernel optimization are later performance capabilities; Phase 2 defines their contracts and may demonstrate only locally practical instrumentation.
- Source-faithful implementations of RelayBP, BPGD, impulse decoding, branching/search methods, and additional schedules remain in their assigned later phases. Phase 2 only ensures the lifecycle can express them.

</deferred>

---

*Phase: 2-Canonical CSS Execution and Policy Contracts*
*Context gathered: 2026-09-22*
