# Phase 2: Canonical CSS Execution and Policy Contracts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-22
**Phase:** 2-Canonical CSS Execution and Policy Contracts
**Areas discussed:** Policy composition surface, Numerical reproducibility, Budgets and work accounting, Ledger and candidate lineage

---

## Policy Composition Surface

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Persisted role declaration | Explicit persisted roles with helper defaults; active policies only; explicit everywhere | Explicit persisted roles with helper defaults ✓ |
| Compatibility enforcement | Layered preflight/runtime; preflight only; runtime-capable | Layered preflight/runtime ✓ |
| Policy state access | Capability-scoped views; shared context; read-wide/write-narrow | Capability-scoped views ✓ |
| Ordering model | Engine lifecycle; manifest global order; dependency-computed order | Refined hierarchical engine lifecycle ✓ |

**User's choice:** Explicit, capability-scoped policy composition with layered enforcement and named hierarchical lifecycle hooks.

**Notes:** A literature check distinguished schedule-local reordering from cross-policy ordering. The user specifically required support for Impulse-style diversity and RelayBP-style sequential legs. The final model separates semantic relationship, execution topology, typed transfer, budget scope, and lineage.

---

## Numerical Reproducibility

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Convention declaration | Versioned profile plus resolved values; all values explicit; pinned defaults | Versioned profile plus resolved values ✓ |
| Canonical baseline | CPU `float64`; multiple equal precisions; high-precision oracle | CPU `float64` ✓ |
| Numerical extremes | Explicit finite saturation; IEEE infinities; adaptive stabilization | Explicit finite saturation ✓ |
| Tie behavior | Deterministic profile rules; seeded random by default; backend-native order | Deterministic profile rules ✓ |

**User's choice:** A versioned deterministic `float64` reference profile with materialized conventions, explicit clipping/failure semantics, and deterministic tie rules.

**Notes:** Random tie behavior remains possible only as an explicit replayable decoder policy, independent of physical sampling.

---

## Budgets and Work Accounting

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Nested limits | Hard hierarchy; let local work finish; one shared pool | Hard hierarchy with boundary/chunk enforcement ✓ |
| Portable work | Atomic work vector; directed-edge total only; equivalent sweeps | Atomic vector plus prominent schedule-qualified iterations ✓ |
| Machine telemetry | Portable core; runtime only; profiler-grade every run | Portable core plus default-on optional profiling ✓ |
| Profiling campaign | Three cohorts; paired sample only; rare events only | Clean population + representative pairs + rare-event replay ✓ |

**User's choice:** Preserve literature-standard iteration reporting while adding raw work vectors and same-machine accounts. Profiling is valuable and enabled by default, but users can disable it.

**Notes:** The user raised CPU/GPU runtime efficiency, implementation/reporting complexity, profiler overhead, and rare-event omission. The chosen design uses leaf-originated counters, derived parent totals, later quota reservation for parallel backends, explicit profiler missingness, semantic replay checks, and stratified rare-event analysis.

---

## Ledger and Candidate Lineage

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Default event detail | Sparse structural ledger; per-iteration summaries; full messages | Sparse structural ledger ✓ |
| Lineage | Immutable graph; immediate parent links; independent snapshots | Immutable graph ✓ |
| Candidate retention | Tiered content-addressed; retain all payloads; selected only | Tiered content-addressed ✓ |
| Truth-aware evaluation | After selection frozen; selected only; oracle-assisted selection | Evaluate candidates after selection is frozen ✓ |

**User's choice:** Keep production ledgers compact while making representative and rare-event traces first-class; preserve complete typed lineage and isolate truth-aware evaluation from selection.

**Notes:** The user required the cost/value rationale, representative plotting strategy, and profiling decisions to be documented in `docs/profiling-and-tracing-strategy.md`. Potential novelty and depth features must be maintained separately in `docs/research-novelty-and-depth-register.md` and checked for precedents as the study matures.

---

## the agent's Discretion

- Exact code-level type and hook names.
- Practical initial trace quotas, profiling fractions, and rare-event replay caps.
- Profiler adapters available in the eventual execution environment.
- Content-addressed storage layout and bounded rejected-candidate retention thresholds.

## Deferred Ideas

- Comprehensive CPU/GPU profiler integrations and production accelerator optimization.
- Implementation of later named policies and decoders; Phase 2 establishes their lifecycle contracts only.
