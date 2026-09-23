# Phase 2: Canonical CSS Execution and Policy Contracts - Research

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- Full CPU/GPU profiler-adapter coverage and production GPU kernel optimization are later performance capabilities; Phase 2 defines their contracts and may demonstrate only locally practical instrumentation.
- Source-faithful implementations of RelayBP, BPGD, impulse decoding, branching/search methods, and additional schedules remain in their assigned later phases. Phase 2 only ensures the lifecycle can express them.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENG-01 | “A researcher can run a canonical binary sum-product BP decoder end to end from a CSS manifest through evaluated outcomes and provenance without delegating its update loop to a third-party decoder.” [VERIFIED: `.planning/REQUIREMENTS.md:34`] | Project-owned LLR kernel, canonical manifest variant, CLI/runner integration, original-problem evaluator boundary. |
| ENG-02 | “A researcher can compose explicit update, schedule, state/memory, intervention, stopping, selection, and postprocessing policies under typed lifecycle and compatibility contracts that reject undefined combinations.” [VERIFIED: `.planning/REQUIREMENTS.md:35`] | Seven explicit discriminated policy specs, capability views, typed decisions, static compatibility plus runtime invariants. |
| ENG-03 | “A researcher can configure stopping and budgets at attempt, branch/leg, search, and shot scope and inspect the actual scope and reason that ended execution.” [VERIFIED: `.planning/REQUIREMENTS.md:36`] | Hierarchical reserve-before-work budget tree and typed termination evidence. |
| ENG-04 | “A researcher can inspect and reproduce numerical conventions including probability/LLR encoding, precision, clipping, initialization, normalization, tie-breaking, and message read/write order.” [VERIFIED: `.planning/REQUIREMENTS.md:37`] | Materialized numerical profile, stable box-plus, finite-boundary checks, deterministic ties, double-buffered flooding. |
| ENG-05 | “Policy execution cannot access sampled hidden truth, and every candidate transformed from a working problem is lifted and evaluated against the immutable original observation and constraints.” [VERIFIED: `.planning/REQUIREMENTS.md:38`] | Narrow decoder-visible views, identity-lift Phase 2 implementation, selection freeze, evaluator-only truth. |
| ENG-06 | “Each implemented policy has source-linked equations or a precise declared procedure plus deterministic small-case/invariant checks independent of aggregate curve matching.” [VERIFIED: `.planning/REQUIREMENTS.md:39`] | Equation registry fields, analytic fixtures, invariants, and source anchors. |
| SCH-01 | “A researcher can select flooding with explicit old/new-message semantics and defined sweep/edge-work counts.” [VERIFIED: `.planning/REQUIREMENTS.md:49`] | Two message buffers, phase barriers, canonical edge order, exact work-vector assertions. |
| LED-02 | “Canonical runs record linked control-flow events for attempts, interventions, branches/pruning, relay transfers, candidates, fallback, and selection; per-edge message tracing can be selectively enabled without removing required shot/control-flow evidence.” [VERIFIED: `.planning/REQUIREMENTS.md:95`] | Versioned structural event vocabulary plus bounded content-addressed trace sidecars. |
| LED-03 | “A researcher can jointly analyze iterations, BP calls/message work, branch/relay work, candidate checks, fallback work, runtime, and parallel-resource context, without equating them to one universal iteration count.” [VERIFIED: `.planning/REQUIREMENTS.md:96`] | Leaf-emitted atomic work vector, derived ancestor summaries, qualified iteration metric, timing and resource contexts. |
| LED-04 | “Native-reference results explicitly mark unavailable internal events or counters and their reasons; missing instrumentation is never reported as zero or reconstructed as observed fact.” [VERIFIED: `.planning/REQUIREMENTS.md:97`] | Preserve the Phase 1 `None` + reason contract and add shared missingness types. |
| DOC-01 | “A researcher can follow an install/run tutorial and inspect mathematical conventions, policy contracts, compatibility, and executable small examples as the canonical engine develops.” [VERIFIED: `.planning/REQUIREMENTS.md:142`] | Installable canonical command, deterministic fixtures, conventions/reference docs, required strategy and novelty register. |
</phase_requirements>

**Researched:** 2026-09-22  
**Domain:** deterministic binary LLR sum-product BP, typed policy execution, hierarchical accounting, and scientific event provenance  
**Confidence:** HIGH for in-repo contracts and BP equations; MEDIUM for proposed Phase 2 naming/defaults and profiling design

## Summary

Phase 2 should be planned as a contract-first vertical slice, not merely a decoder loop. Build one project-owned binary LLR sum-product kernel and run the simplest explicit composition: sum-product update + flooding schedule + identity state/memory + identity intervention + syndrome-or-budget stopping + deterministic first-eligible selection + identity postprocessing. The engine—not individual policies—must own lifecycle order, scoped views, invariant checks, lineage, budget reservation, work emission, selection freeze, and evaluator handoff. This gives every later policy phase a stable seam without prematurely implementing its algorithms. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:12-48`; VERIFIED: `.planning/REQUIREMENTS.md:34-39`]

Numerically, implement exact binary SPA in the LLR domain using a stable pairwise box-plus fold, deterministic edge order, explicit finite saturation, and double-buffered flooding. The standard check update is `2 atanh(product tanh(m/2))`; traditional flooding updates all messages of one direction from the prior state before the next direction. [CITED: https://arxiv.org/abs/cs/0702111] NumPy’s `logaddexp`, `isfinite`, and scoped `errstate` provide the required stable correction and failure checks. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.isfinite.html; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.errstate.html]

The other half of the phase is evidence architecture. Extend—not rewrite—the strict frozen manifests, truth-separated samples, independent evaluator, durable ledger, and explicit native-counter missingness already present. The existing source defines `ConfigDict(extra="forbid", strict=True, frozen=True)`, separates `DecoderObservation` from `HiddenTruth`, defines outcome values `"invalid_syndrome", "exact", "stabilizer_equivalent", "logical_failure"`, and reports native edge work as `None` with a reason. [VERIFIED: `src/bp_registry/manifests.py:27-30`; VERIFIED: `src/bp_registry/sampling.py:16-40`; VERIFIED: `src/bp_registry/evaluator.py:13`; VERIFIED: `src/bp_registry/reference.py:10-16`] Version the richer ledger instead of widening v1 ambiguously: v1 accepts exactly `"begin"` and `"terminal"`. [VERIFIED: `src/bp_registry/ledger.py:21-22,73-90`]

**Primary recommendation:** implement and test the immutable contract graph first, then the stable flooding kernel, then integrate manifest → canonical execution → selection freeze → independent evaluation → sparse ledger/sidecars; finish with tutorial and the two locked research-method documents.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Canonical binary SPA updates | API / Backend (research kernel) | — | Project-owned deterministic mathematical execution belongs in the kernel, never the CLI or native adapter. [VERIFIED: `.planning/REQUIREMENTS.md:34`] |
| Policy composition and lifecycle | API / Backend (execution engine) | Storage | The engine validates composition, owns hooks, and persists resolved policy identity. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:12-25`] |
| Budgets and work accounting | API / Backend (execution engine) | Storage | Reservations must precede atomic work; append-only leaf deltas and summaries are evidence. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:36-40`] |
| Original/working problem and candidate lineage | API / Backend (execution engine) | Storage | Identity/lift/selection rules are semantic state; durable graph records make them auditable. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:51-55`] |
| Truth-aware outcome evaluation | API / Backend (independent evaluator) | — | Hidden truth stays outside decoder execution. Existing evaluator consumes original code and truth only after selection. [VERIFIED: `src/bp_registry/evaluator.py:33-47`] |
| Sparse ledger and trace blobs | Database / Storage (filesystem JSONL/content store) | API / Backend | The engine emits typed evidence; storage owns durable append, hashing, bounds, and retrieval. Existing append is flush + `fsync`. [VERIFIED: `src/bp_registry/ledger.py:111-118`] |
| Researcher command/tutorial | Browser / Client equivalent (CLI/docs) | API / Backend | CLI resolves a manifest and invokes the engine; it must not contain numerical semantics. Existing commands are `"validate-evidence", "preflight", "pilot", "reconcile", "verify-run"`. [VERIFIED: `src/bp_registry/cli.py:276-305`] |

## Project Constraints (from AGENTS.md)

- Do not automatically select or spawn GPT-6 Astra; keep the configured GSD role models/efforts and ask before introducing Astra into automatic selection or fallback. [VERIFIED: active project instruction supplied for this session, 2026-09-22]
- Own one canonical execution engine per mathematically compatible BP family; native decoder adapters remain executable references. [VERIFIED: `AGENTS.md:59-60`]
- Implement BP-internal policies before substantial optional OSD/LSD-style postprocessing and preserve the sequence CSS → correlated quaternary → circuit-level. [VERIFIED: `AGENTS.md:13-15,45-49`]
- Keep original problems immutable, deny policies hidden truth, and use independent evaluators; record numerical conventions, scoped stopping, candidate lineage, and all work. [VERIFIED: `AGENTS.md:59-63`]
- Cite primary sources for algorithms, record interpretive decisions, independently check algebra/policy semantics, prespecify campaign rules, and retain failed/inconclusive evidence. [VERIFIED: `AGENTS.md:45-47`]
- Preserve both source-faithful and controlled configurations, manifests, per-shot/control-flow evidence, optional fine traces, and explicit missing native instrumentation. [VERIFIED: `AGENTS.md:16-18,63-64`]
- Preserve the approved autonomous mode, fine phases, parallel independent work, and saved role model/effort settings; this research did not alter `.planning/config.json`. [VERIFIED: `AGENTS.md:48`; VERIFIED: `.planning/config.json:2-4,92-170`]
- Deliver open software and detailed documentation, but do not invent a license, packaging/interface promise, compute allocation, journal, or deadline that the project has not selected. [VERIFIED: `AGENTS.md:19-21`]
- The GSD workflow must precede repo edits; this research was initialized through the Phase 2 GSD phase operation. [VERIFIED: `AGENTS.md:77-87`]

## Standard Stack

No new runtime package is needed. Preserve the exact Phase 1 pins for this phase; upgrading NumPy/SciPy/pytest would mix dependency migration with semantic contract work. The project source quotes `requires-python = ">=3.12"` and `dependencies = ["numpy==2.2.6", "scipy==1.17.1", "ldpc==2.4.1", "pydantic==2.13.5"]`. [VERIFIED: `pyproject.toml:9-10`]

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | `>=3.12` | Typed engine, stdlib clocks/profilers/hashing/JSON | Existing declared runtime; `.venv` currently runs Python 3.12.2. [VERIFIED: `pyproject.toml:9`; VERIFIED: local `.venv/bin/python --version`, 2026-09-22] |
| NumPy | `2.2.6` | `float64` message arrays, stable `logaddexp`, finite checks, GF(2) fixtures | Exact project pin and documented stable primitives. [VERIFIED: `pyproject.toml:10`; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html] |
| Pydantic | `2.13.5` | Strict versioned manifest/event/trace-plan schemas | Existing exact pin; official config supports strict/frozen/extra-forbid and discriminated unions. [VERIFIED: `pyproject.toml:10`; CITED: https://docs.pydantic.dev/latest/api/config/; CITED: https://docs.pydantic.dev/latest/concepts/unions/] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SciPy | `1.17.1` | Existing scientific environment compatibility | Keep installed/pinned, but do not make the baseline kernel depend on a SciPy primitive. [VERIFIED: `pyproject.toml:10`] |
| `ldpc` | `2.4.1` | Phase 1 native-reference comparator only | Never call it from the canonical update loop. Existing adapter imports `BpDecoder`. [VERIFIED: `pyproject.toml:10`; VERIFIED: `src/bp_registry/reference.py:1-7,28-57`] |
| pytest | `9.0.3` installed | Unit/integration/golden-contract tests | Existing suite runner; project config sets `testpaths = ["tests"]` and `pythonpath = ["src"]`. [VERIFIED: `pyproject.toml:16-18`; VERIFIED: local `.venv` probe, 2026-09-22] |
| stdlib `time`, `resource`, `tracemalloc`, `hashlib`, `json` | Python 3.12 | Wall/CPU/RSS/Python-allocation measurements, content identity, durable serialization | Use behind typed adapters so method/scope/unit/missingness are explicit. [CITED: https://docs.python.org/3.12/library/time.html; CITED: https://docs.python.org/3.12/library/resource.html; CITED: https://docs.python.org/3.12/library/tracemalloc.html] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Project-owned NumPy SPA | `ldpc.BpDecoder` | Rejected for canonical execution: it hides update-loop semantics/work and would violate ENG-01; retain only as reference. [VERIFIED: `.planning/REQUIREMENTS.md:34`] |
| Stable box-plus fold | direct `2*atanh(prod(tanh(x/2)))` | Mathematically canonical but less robust near saturated magnitudes; keep the direct expression as an oracle on safe small values, not production arithmetic. [CITED: https://arxiv.org/abs/cs/0702111] |
| stdlib measurement adapters | new profiler dependency | Adds environment risk without improving the Phase 2 contract; full profiler coverage is explicitly deferred. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:110-112`] |
| JSON/JSONL + content-addressed binary/NPZ payloads | pickle | Pickle adds executable-deserialization risk and weak cross-version evidence; strict portable encodings match existing practice. [VERIFIED: `src/bp_registry/ledger.py:93-118`; ASSUMED] |

**Installation:** use the already approved environment; do not reinstall during this phase unless a human approves the package gate.

```bash
.venv/bin/python -m pip install -e .
OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q
```

The environment record says `.venv` was created with `python -m venv --system-site-packages .venv`, with Pydantic installed locally and NumPy/SciPy/ldpc/pytest inherited from Anaconda. [VERIFIED: `docs/environment-pins.md:48-66`]

## Package Legitimacy Audit

The mandated legitimacy seam returned `SUS` for every package because PyPI download data was unavailable, several repository URLs were unavailable to the seam, and the latest NumPy/Pydantic releases were classified as too new. This is a conservative tooling verdict, not evidence that the already approved pinned artifacts are malicious. [VERIFIED: local `gsd_run query package-legitimacy check --ecosystem pypi ...`, 2026-09-22]

| Package | Registry | Installed/Pin | Age / Pin Publish Date | Registry Latest | Downloads / Source Signal | Verdict | Disposition |
|---------|----------|---------------|------------------------|-----------------|---------------------------|---------|-------------|
| `numpy` [WARNING: flagged as suspicious — verify before using.] | PyPI | `2.2.6` | ~16 months / 2025-05-17 [CITED: https://pypi.org/pypi/numpy/2.2.6/json] | `2.5.3` | downloads/repo unavailable to seam | SUS | Existing approved pin only; checkpoint before reinstall/upgrade |
| `scipy` [WARNING: flagged as suspicious — verify before using.] | PyPI | `1.17.1` | ~7 months / 2026-02-23 [CITED: https://pypi.org/pypi/scipy/1.17.1/json] | `1.18.1` | downloads/repo unavailable to seam | SUS | Existing approved pin only; checkpoint before reinstall/upgrade |
| `pydantic` [WARNING: flagged as suspicious — verify before using.] | PyPI | `2.13.5` | 25 days / 2026-08-28 [CITED: https://pypi.org/pypi/pydantic/2.13.5/json] | `2.13.5` | downloads unavailable; `github.com/pydantic/pydantic` | SUS | Existing approved pin only; checkpoint before reinstall/upgrade |
| `pytest` [WARNING: flagged as suspicious — verify before using.] | PyPI | `9.0.3` | ~5.5 months / 2026-04-07 [CITED: https://pypi.org/pypi/pytest/9.0.3/json] | `9.1.1` | downloads unavailable; `github.com/pytest-dev/pytest` | SUS | Existing installed test tool; checkpoint before reinstall/upgrade |
| `ldpc` [WARNING: flagged as suspicious — verify before using.] | PyPI | `2.4.1` | ~9.5 months / 2025-12-08 [CITED: https://pypi.org/pypi/ldpc/2.4.1/json] | `2.4.1` | downloads/repo unavailable to seam | SUS | Existing approved native-reference pin only; checkpoint before reinstall/upgrade |

Versions above were queried against PyPI with `.venv/bin/python -m pip index versions` on 2026-09-22; package-name legitimacy cannot be upgraded to VERIFIED because the legitimacy verdict was not `OK`.

**Packages removed due to SLOP verdict:** none.  
**Packages flagged as suspicious (SUS):** NumPy, SciPy, Pydantic, pytest, ldpc. The planner must add `checkpoint:human-verify` before any install/reinstall/upgrade; ordinary execution should reuse `.venv`.

## Architecture Patterns

### System Architecture Diagram

```text
canonical manifest + immutable CSS artifact + identified shot
                         |
                         v
              preflight / composition
      (schema -> static compatibility -> resolved profile)
                         |
                         v
 decoder-visible OriginalProblem --identity transform--> WorkingProblem
                         |                         |
                         |                  engine lifecycle
                         |         shot -> search -> member/leg/branch
                         |                    -> attempt -> iteration -> message
                         |                         |
                         |        +----------------+----------------+
                         |        |                                 |
                         |  policy capability views            budget tree
                         |        |                                 |
                         |  typed decisions ----------------> validate/apply
                         |        |                                 |
                         |        +----------> binary SPA kernel ---+
                         |                         |
                         |                         v
                         |                 candidate + leaf work
                         |                         |
                         |        lineage + decoder-visible selection
                         |                         |
                         |                  freeze selection
                         |                         |
 hidden truth -----------+-----> independent original-problem evaluator
                                                   |
                         +-------------------------+------------------+
                         |                                            |
                         v                                            v
              sparse durable event ledger               bounded trace/profile blobs
                + derived summaries                    (content-addressed sidecars)
```

The evaluator boundary is already independently expressed: `ShotSample` contains both `hidden: HiddenTruth` and `observation: DecoderObservation`, so the canonical runner must pass only the latter-side problem view into engine construction. [VERIFIED: `src/bp_registry/sampling.py:16-40`] The evaluator’s documented boundary is “original checks and hidden truth only.” [VERIFIED: `src/bp_registry/evaluator.py:33-47`]

### Recommended Project Structure

The following names are initial design recommendations under the user-delegated naming discretion, not existing paths. [ASSUMED]

```text
src/bp_registry/
├── canonical/
│   ├── contracts.py       # versioned specs, capabilities, decisions, compatibility
│   ├── problems.py        # immutable OriginalProblem/WorkingProblem and identity lift
│   ├── numerics.py        # numerical profile, saturation, stable box-plus
│   ├── kernel.py          # project-owned binary SPA message update primitives
│   ├── schedules.py       # flooding state machine; later schedules plug in here
│   ├── budgets.py         # hierarchical reservations and typed termination evidence
│   ├── execution.py       # engine lifecycle/orchestration and selection freeze
│   ├── lineage.py         # stable entities/typed edges/content identities
│   ├── tracing.py         # sparse events, bounded sidecar sink, truncation
│   └── profiling.py       # clean/profile pairing and local metric adapters
├── manifests.py           # add version-dispatched canonical manifest variant
├── runner.py              # native and canonical execution routes
├── ledger.py              # retain v1 reader; add versioned canonical event reader/writer
└── cli.py                 # add canonical run/inspect commands, retain Phase 1 commands
tests/
├── canonical/             # analytic kernel/contract/budget/lineage tests
├── fixtures/              # tiny deterministic CSS manifests and expected traces
└── test_canonical_cli.py  # full manifest-to-evaluated-ledger slice
docs/
├── canonical-engine.md
├── profiling-and-tracing-strategy.md
└── research-novelty-and-depth-register.md
```

### Component Responsibilities

| Component | Owns | Must Not Own |
|-----------|------|--------------|
| Manifest/preflight | persisted policy specs, resolved numerical profile, static compatibility, all defaults materialized | runtime state, hidden truth, evaluator result |
| Engine | lifecycle order, scoped views, validation/application of decisions, budgets, lineage, selection freeze | policy-specific private state interpretation, truth-aware scoring |
| Policy | its declared private state and typed decision procedure at named bindings | engine mutation, filesystem I/O, arbitrary policy ordering, hidden truth |
| Schedule | within-attempt message order and snapshot/freshness semantics | search members, branches, restarts, relay legs |
| Intervention/search | future diversity/branch/restart/relay structure | in-attempt edge ordering, arbitrary predecessor internals |
| Kernel | pure update calculations and work deltas over supplied state | stopping, selection, ledger I/O, native decoder calls |
| Budget tree | reservations, consumption, ancestor checks, binding termination evidence | estimating unperformed work as consumed |
| Lineage/evidence sink | append-only entities/edges/events, hashes, sidecar references, missingness | decoder decisions or feedback from evaluator annotations |
| Evaluator | truth-aware outcome annotation against original problem | candidate selection or any policy input |

This responsibility split is directly constrained by D-03–D-07. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:19-23`]

### Pattern 1: Versioned Composition Spec + Runtime Policy Objects

**What:** Persist only strict, data-only specs; resolve them through a registry into runtime policy objects. Every manifest contains all seven roles, including explicit identity/no-op specs. Use discriminated unions and model-level compatibility validation, then repeat live invariants in the engine before applying every decision. Pydantic recommends discriminated unions as more predictable than untagged unions, and `model_validator` supports whole-model validation. [CITED: https://docs.pydantic.dev/latest/concepts/unions/; CITED: https://docs.pydantic.dev/latest/concepts/validators/]

**When to use:** At manifest load/composition and at every hook boundary. Never serialize Python import paths or callable objects as the scientific meaning.

**Contract details:**

- Base persisted schemas should extend the established `ConfigDict(extra="forbid", strict=True, frozen=True)` pattern and additionally set `allow_inf_nan=False` for numerical fields; Pydantic otherwise permits infinities/NaN by default. [VERIFIED: `src/bp_registry/manifests.py:27-30`; CITED: https://docs.pydantic.dev/latest/api/config/]
- Each binding records stable binding ID, policy family/version, role, hook, owned state lifetime, required/provided capabilities, parameters, procedure/equation source, and implementation revision. [ASSUMED]
- Static composition verifies role completeness, unique binding IDs, hook compatibility, capability satisfaction, numerical-profile compatibility, and source-defined parameter domains. Runtime checks verify current scope, shape, finiteness, ownership, remaining budgets, and decision legality. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:17-23`]
- Policy-facing types should be separate frozen views, not a large context object with “private” attributes. Do not include `HiddenTruth`, `ShotSample`, evaluator, ledger writer, filesystem path, or mutable NumPy buffers in any view. [VERIFIED: `src/bp_registry/sampling.py:16-40`; ASSUMED]
- Keep `ManifestV1` and ledger v1 replayable; add explicit canonical schema/version dispatch rather than changing old meanings in place. Existing v1 ledger accepts only `"begin"` and `"terminal"`. [VERIFIED: `src/bp_registry/ledger.py:21,73-90`]

### Pattern 2: Stable LLR Sum-Product + Double-Buffered Flooding

**What:** Define LLR as `L = log(P(x=0)/P(x=1))`. Initialize every variable-to-check edge to the channel prior. For a check with observed parity `s`, multiply the outgoing sign by `(-1)^s`. Fold incoming messages in canonical edge order using stable box-plus; variable updates and beliefs are channel LLR plus incoming check messages. [CITED: https://arxiv.org/abs/cs/0702111; CITED: https://arxiv.org/html/2312.10950v2]

Use the equivalent pair operation below instead of a product followed by `atanh`:

```text
boxplus(a, b) = sign(a) sign(b) min(|a|, |b|)
                + log(1 + exp(-|a + b|))
                - log(1 + exp(-|a - b|))
```

Compute each correction as `np.logaddexp(0.0, -abs(...))`; NumPy documents `logaddexp(x1, x2)` as `log(exp(x1)+exp(x2))` for values represented in the log domain. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]

**When to use:** The Phase 2 `float64` CPU profile and as the semantic oracle for later optimized backends.

**Required Phase 2 semantics:**

1. Store one stable bipartite edge table ordered by `(check_index, variable_index)` and map every message to an edge ID. [ASSUMED]
2. Initialize old variable-to-check messages from the prior; an iteration reserves a full sweep, computes all new check-to-variable messages from the old variable buffer, computes all new variable-to-check messages from the completed check buffer, assembles beliefs, and checks a candidate. Swap buffers only after a successful full sweep. This enforces old/new flooding semantics. [CITED: https://arxiv.org/abs/cs/0702111]
3. Count one full flooding iteration as exactly `|E|` check-to-variable updates, `|E|` variable-to-check updates, `n` belief assemblies, and one candidate check; count the BP attempt once separately. This is the proposed schedule-qualified Phase 2 work definition. [ASSUMED]
4. Saturate channel priors, outgoing messages, and assembled beliefs at every named profile boundary; handle degree-one check output as the parity-signed saturation value rather than generating infinity. Run `np.isfinite` before/after named calculations and turn any unexpected nonfinite into a typed terminal numerical failure. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.isfinite.html]
5. Execute vulnerable operations inside `np.errstate(over="raise", invalid="raise", divide="raise")`; NumPy documents these as supported exception treatments in a scoped context. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.errstate.html]
6. Hard decision rule: `belief < 0` maps to bit 1; exact zero maps to bit 0. Edge and candidate ties use ascending canonical IDs. Random resolution is unavailable in the baseline profile. [ASSUMED]

**Initial numerical profile recommendation:** name it `binary-spa-flooding-f64-v1`; use IEEE/NumPy `float64`, natural-log LLRs, prior `log((1-p)/p)`, symmetric saturation `K=25`, the boundaries above, and the deterministic zero/index tie rules. `K=25` has an explicit primary-source precedent in the BPGD experiments and was preferred there over infinite messages because of numerical issues; this does not make it universal, so the full value remains materialized and overridable only through another named profile. [CITED: https://arxiv.org/html/2312.10950v2; ASSUMED]

### Pattern 3: Hierarchical Reservation and Leaf-Only Work

**What:** Represent `shot → search → member/leg/branch → attempt` as budget accounts. Before an atomic sweep or candidate operation, reserve its whole declared count vector at the leaf and every ancestor. If any scope would exceed a hard count cap, reject the reservation and terminate at that binding scope without partial message writes. On completion, commit one leaf work delta; derive all ancestor totals by folding descendants. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:32-35`]

**When to use:** Every kernel sweep, candidate validation/check, intervention, branch, relay transfer, and later fallback call.

The atomic work record should remain a vector, initially: check-to-variable updates, variable-to-check updates, belief assemblies, residual/priority evaluations, BP calls, candidate checks, intervention actions, branch expansions/prunes, relay transfers, and fallback calls. Unsupported operations are observed zero only when the canonical engine can know none occurred; unavailable native counters remain missing with a reason. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:34-35`; VERIFIED: `src/bp_registry/reference.py:10-16`]

Wall-clock limits are different: sample `perf_counter_ns()` only at declared sync boundaries (attempt start, iteration boundary, candidate/selection, attempt end), terminate at the next boundary, and record the boundary and overshoot. Python documents that this clock includes sleep; `process_time_ns()` is process CPU and excludes sleep. [CITED: https://docs.python.org/3.12/library/time.html]

### Pattern 4: Append-Only Lineage + Sparse Ledger + Bounded Sidecars

**What:** Emit stable entity IDs and typed parent edges for original/working problems, transforms, search/member/attempt scopes, candidates, lift, validation, selection, and evaluation. Stable IDs should be content/logical-path derived—not timestamp or append-position derived—so future concurrency does not change identity. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:43-47`; ASSUMED]

**When to use:** Every canonical shot, including failures before a candidate exists.

Recommended structural event families are scope open/close, policy action, work delta, candidate emitted/retained, lift, decoder-visible validation, selection frozen, truth-aware evaluation, termination, trace truncation, and profile link. Exact identifiers are proposed under agent discretion. [ASSUMED]

Keep the durable JSONL sparse; iteration and message data go to content-addressed sidecars referenced by digest, schema version, content type, byte count, record count, filter, and explicit truncation state. Reuse the existing confined-path pattern: it rejects absolute/`..` paths, symlink traversal, root escape, and non-files. [VERIFIED: `src/bp_registry/artifacts.py:70-91`]

Recommended configurable local defaults (not publication-campaign targets): [ASSUMED]

| Item | Phase 2 default |
|------|-----------------|
| Production trace level | structural ledger only |
| Iteration-summary sidecar | 1,024 records and 1 MiB per shot |
| Edge-message sidecar | opt-in; 50,000 records and 8 MiB per shot |
| Fully retained rejected candidates | at most 32 candidates and 4 MiB per shot; metadata/digests remain for all |
| Representative paired profile cohort | deterministic 1%, minimum 8 and maximum 128 per prespecified stratum |
| Targeted rare/tail replay quota | at most 16 per declared reason/stratum |

On reaching either a record or byte cap, write one structural truncation event with attempted/retained counts and bytes, then stop sidecar emission without changing decoder execution. Never truncate the structural ledger. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:43-46`; ASSUMED]

### Pattern 5: Clean/Profile Pairing, Not Profiling Everywhere

**What:** Full clean runs own reported outcomes and runtimes. Select the representative profile cohort deterministically from manifest/sample identity before outcomes are known; replay exactly the same sample, manifest, decoder-local randomness/order, and selection conditions with instrumentation; link clean/profile IDs and record semantic agreement. Tail replays are a separate biased diagnostic cohort. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:36-40`]

Use low-overhead always-available adapters for `perf_counter_ns`, `process_time_ns`, and platform-normalized `resource.getrusage(RUSAGE_SELF).ru_maxrss`. Use `tracemalloc` only in profiled replays and label it “Python allocator bytes,” not whole-process/native NumPy memory; the module documents that it traces Python memory blocks and that storing more frames increases CPU and memory overhead. [CITED: https://docs.python.org/3.12/library/tracemalloc.html; CITED: https://docs.python.org/3.12/library/resource.html]

Continuous/probabilistic and stratified profiling are established approaches for controlling overhead and improving representativeness, but the project’s three-cohort contract is a locked scientific design, not inferred from those systems. [CITED: https://research.google/pubs/google-wide-profiling-a-continuous-profiling-infrastructure-for-data-centers/; CITED: https://minds.wisconsin.edu/handle/1793/11182]

### Anti-Patterns to Avoid

- **One mutable “decoder context” passed to every policy:** capability names become documentation only and hidden truth/state leakage becomes untestable. Use role/hook-specific frozen views and engine-applied decisions. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:19-23`]
- **A generic ordered list of policies:** schedule, intervention, stopping, and selection do not share interchangeable ordering semantics. Bind each to a named lifecycle hook and reject unsupported orderings. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:20-23`]
- **In-place flooding updates:** later edges see fresher messages than earlier edges, silently turning flooding into a serial/layered hybrid. Use old/new buffers and a phase barrier. [CITED: https://arxiv.org/abs/cs/0702111]
- **Compute `atanh(prod(tanh()))` and clip the result:** overflow/roundoff may happen before clipping. Use stable log-domain box-plus and defined finite boundaries. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]
- **Replace NaN/inf with a clipped number:** this hides a numerical defect. Expected endpoint/degree-one saturation is an explicit branch; unexpected nonfinite state is terminal evidence. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:26-29`]
- **Count ancestor work and leaf work independently:** aggregate analysis double-counts. Emit once at the leaf and derive ancestors. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:32-35`]
- **Call a partial sweep “one iteration”:** if budget exhaustion can stop mid-sweep, headline iteration semantics become ambiguous. Reserve a whole sweep and either commit it or do none of it. [ASSUMED]
- **Emit every edge update into durable JSONL:** production evidence becomes the bottleneck and crash-recovery surface. Keep structural JSONL and bounded trace sidecars. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:43-44`]
- **Use evaluator annotations in candidate scoring:** even an indirect callback or shared object violates selection freeze and biases the decoder. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:47`]
- **Treat missing native counters as zero:** preserve `None` and a reason; the current adapter explicitly quotes `edge_updates: None = None` and `"ldpc.BpDecoder does not expose edge-update counts"`. [VERIFIED: `src/bp_registry/reference.py:10-16`]
- **Mix clean and profiled wall times:** profiler overhead contaminates algorithm runtime. Report clean population timings and paired overhead separately. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:36-40`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Strict tagged schema parsing | ad hoc nested-dict/default logic | Pydantic strict/frozen discriminated models | Rejects extras/coercion and supports structured validation/errors. [CITED: https://docs.pydantic.dev/latest/concepts/strict_mode/; CITED: https://docs.pydantic.dev/latest/concepts/unions/] |
| Stable log correction | manual threshold branches around `exp`/`log` | `numpy.logaddexp` | Handles log-domain addition with a documented primitive. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html] |
| Nonfinite detection/error scope | global warning filters or string checks | `numpy.isfinite` + local `numpy.errstate` | Explicit, vectorized, scoped behavior. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.isfinite.html; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.errstate.html] |
| Timing clocks | wall timestamps/date arithmetic | `time.perf_counter_ns`, `time.process_time_ns` | Monotonic/high-resolution elapsed time and explicit process CPU semantics. [CITED: https://docs.python.org/3.12/library/time.html] |
| Python allocation profiling | custom allocator bookkeeping | `tracemalloc` adapter | Provides current/peak traced bytes and snapshots, with known scope and overhead. [CITED: https://docs.python.org/3.12/library/tracemalloc.html] |
| Content identity | random UUID as semantic identity or custom digest | canonical serialization + stdlib SHA-256 | Existing code already uses SHA-256 identities and durable JSON; reuse the established convention. [VERIFIED: `src/bp_registry/sampling.py:60-73`; VERIFIED: `src/bp_registry/ledger.py:37-39,111-118`] |
| Artifact/path sandboxing | string-prefix path checks | extend existing resolved-root/symlink confinement | Prevents absolute path, `..`, symlink, and resolved-root escapes. [VERIFIED: `src/bp_registry/artifacts.py:70-91`] |
| A universal “cost” score | weighted sum of iteration, messages, branches, runtime | typed atomic work vector + qualified iteration count | Weights would bake a contestable scientific choice into evidence. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:34-36`] |

**Key insight:** the binary SPA kernel itself must be project-owned; validation, numerically stable primitives, clocks, hashing, and profiling primitives should not be reinvented. The research contribution is the explicit behavioral contract and evidence, not replacements for mature general-purpose machinery.

## Common Pitfalls

### Pitfall 1: A Numerically “Correct” Formula That Is Operationally Unstable

**What goes wrong:** extreme messages yield `atanh(1)`, infinities, cancellation, or platform-sensitive differences before clipping.  
**Why it happens:** direct textbook algebra is evaluated in floating point as though real-arithmetic equivalence guaranteed operational equivalence.  
**How to avoid:** define a named profile, stable box-plus, exact saturation points, degree-one handling, local floating-error behavior, finiteness checks, and terminal failure evidence. Compare stable and direct formulas only on safe analytic fixtures. [CITED: https://arxiv.org/abs/cs/0702111; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html]  
**Warning signs:** runtime warnings, values equal to ±inf/NaN, outcome differences when edge order changes, or `nan_to_num` in production kernel code.

### Pitfall 2: Flooding Accidentally Becomes Sequential

**What goes wrong:** updating one shared message array makes later edge updates depend on the current sweep.  
**Why it happens:** in-place arrays are simpler and appear equivalent on tiny symmetric graphs.  
**How to avoid:** immutable read snapshot + distinct write buffer for each message direction, with buffer swap only at the defined phase/sweep boundary. [CITED: https://arxiv.org/abs/cs/0702111]  
**Warning signs:** reversing edge order changes a deterministic result, or a trace shows an edge reading an event from the same directional phase.

### Pitfall 3: Capability Views Are Types but Not Boundaries

**What goes wrong:** a policy receives an object that references the sample, engine, evaluator, or mutable state and can recover hidden truth or mutate unowned data.  
**Why it happens:** Python privacy/type hints do not enforce runtime object reachability.  
**How to avoid:** construct narrow frozen values containing copies/read-only arrays of only visible facts; test with hostile probe policies; keep evaluator construction after selection freeze. Existing source explicitly separates `DecoderObservation` and `HiddenTruth`. [VERIFIED: `src/bp_registry/sampling.py:16-40`]  
**Warning signs:** policy signatures mention `ShotSample`, `HiddenTruth`, runner, evaluator, or ledger writer.

### Pitfall 4: Budget Exhaustion Produces Ambiguous Partial Work

**What goes wrong:** half an edge sweep mutates state, consumes work, and is later reported as an iteration or silently discarded.  
**Why it happens:** limits are checked only after operations or at only one scope.  
**How to avoid:** reserve the declared atomic vector against leaf and all ancestors before mutation; full-sweep iteration is the Phase 2 atomic unit; wall limits remain explicit boundary checks. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:32-35`]  
**Warning signs:** consumed work exceeds a configured cap, a parent total is smaller than a child, or a terminal row cannot say which scope/resource bound.

### Pitfall 5: Work Is Accurate Locally but Double-Counted Globally

**What goes wrong:** the attempt, member, search, and shot each emit the same counters.  
**Why it happens:** every layer tries to be self-contained.  
**How to avoid:** append only leaf deltas; compute summaries by lineage reduction; include an invariant that the root total equals the sum of unique leaf events. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:33-35`]  
**Warning signs:** total messages scale with number of hierarchy levels or differ depending on query grouping.

### Pitfall 6: Trace Limits Quietly Change Decoder Semantics

**What goes wrong:** trace overflow raises inside the kernel, slows selected executions unpredictably, or halts decoding.  
**Why it happens:** tracing is implemented inline as required storage rather than an observation sink.  
**How to avoid:** the sink accepts/drops records under explicit record+byte quotas, emits one truncation event, and cannot affect kernel decisions. Test identical candidates/work with tracing off, full, and truncated. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:43-44`]  
**Warning signs:** output changes with trace level, no truncation record, or structural terminal evidence disappears when sidecar writing fails.

### Pitfall 7: Stable IDs Depend on Execution Order

**What goes wrong:** enabling future concurrency changes candidate/attempt IDs and breaks clean/profile pairing.  
**Why it happens:** IDs use event sequence or timestamps.  
**How to avoid:** derive IDs from run/shot identity + typed logical ancestry + binding/local ordinal + content digest, and keep append sequence only as transport metadata. [ASSUMED]  
**Warning signs:** replaying the same manifest/sample changes lineage IDs or sidecar paths.

### Pitfall 8: Profiling Evidence Is Selection-Biased

**What goes wrong:** only slow/failing shots are profiled, then their bottlenecks are presented as population estimates.  
**Why it happens:** rare cases are scientifically interesting but not representative.  
**How to avoid:** prespecify representative selection before outcomes, keep paired clean/profile runs, measure overhead, and label tail replays diagnostic. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:38-40`]  
**Warning signs:** profile cohort has no inclusion probabilities/strata, lacks clean pair IDs, or contains only failures.

### Pitfall 9: Phase 2 Quietly Implements Later Algorithms

**What goes wrong:** generic lifecycle work expands into BPGD, RelayBP, impulse, residual scheduling, or fallback algorithms before their source semantics are resolved.  
**Why it happens:** lifecycle fixtures are mistaken for algorithm implementations.  
**How to avoid:** implement identity/no-op policies and synthetic contract probes only; preserve expressibility fields/events without naming probes as published algorithms. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:9,123-124`]  
**Warning signs:** Phase 2 acceptance depends on a later named decoder’s performance.

### Pitfall 10: The Right Suite Command Is Not Used

**What goes wrong:** twelve existing tests fail at environment preflight, masking actual regressions.  
**Why it happens:** checked-in manifests require `OMP_NUM_THREADS=1`; the variable is not set by default on this shell. `_verify_environment` compares `os.environ.get("OMP_NUM_THREADS")` to the manifest value and raises on mismatch. [VERIFIED: `src/bp_registry/manifests.py:329-336`]  
**How to avoid:** always invoke the full suite as `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`. This produced “71 passed” on 2026-09-22. [VERIFIED: local test run, 2026-09-22]  
**Warning signs:** failures say `OMP_NUM_THREADS does not match the manifest requirement`.

## Code Examples

These are implementation skeletons, not existing API. Proposed identifiers and exact Phase 2 defaults are [ASSUMED]; the mathematical and library operations are source-linked.

### Stable Pairwise Box-Plus and Check Update

```python
# Sources:
# - exact SPA check equation: https://arxiv.org/abs/cs/0702111
# - stable log correction: https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html
# - finite/error handling: NumPy 2.2 isfinite and errstate docs
from __future__ import annotations

import numpy as np


def _finite_f64(value: float, *, where: str) -> np.float64:
    out = np.float64(value)
    if not bool(np.isfinite(out)):
        raise NumericalFailure(where)  # proposed typed terminal path
    return out


def boxplus(a: float, b: float, *, saturation: float) -> np.float64:
    a64 = np.clip(_finite_f64(a, where="boxplus.input.a"), -saturation, saturation)
    b64 = np.clip(_finite_f64(b, where="boxplus.input.b"), -saturation, saturation)
    sign = np.copysign(1.0, a64) * np.copysign(1.0, b64)
    core = sign * min(abs(a64), abs(b64))
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        correction = (
            np.logaddexp(0.0, -abs(a64 + b64))
            - np.logaddexp(0.0, -abs(a64 - b64))
        )
    return np.clip(
        _finite_f64(core + correction, where="boxplus.output"),
        -saturation,
        saturation,
    )


def check_to_variable(incoming: np.ndarray, *, syndrome_bit: int, saturation: float) -> np.float64:
    if incoming.size == 0:  # degree-one check: empty product has parity sign
        return np.float64(saturation if syndrome_bit == 0 else -saturation)
    value = np.float64(incoming[0])
    for item in incoming[1:]:  # canonical edge order, never set iteration order
        value = boxplus(value, float(item), saturation=saturation)
    signed = value if syndrome_bit == 0 else -value
    return np.clip(_finite_f64(signed, where="check.output"), -saturation, saturation)
```

The code should use a real declared `NumericalFailure` type whose ledger representation includes numerical profile ID, named boundary, scope IDs, and no hidden-truth content. [ASSUMED]

### Strict Explicit Seven-Role Composition

```python
# Source patterns:
# https://docs.pydantic.dev/latest/concepts/unions/
# https://docs.pydantic.dev/latest/api/config/
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, allow_inf_nan=False
    )


class SumProductUpdateV1(ContractModel):
    kind: Literal["sum_product_v1"]


class IdentityStateV1(ContractModel):
    kind: Literal["identity_state_v1"]


UpdateSpec = Annotated[SumProductUpdateV1, Field(discriminator="kind")]
# Define equally explicit discriminated specs for schedule, state/memory,
# intervention, stopping, selection, and postprocessing.


class CompositionV1(ContractModel):
    update: UpdateSpec
    schedule: ScheduleSpec
    state_memory: StateMemorySpec
    intervention: InterventionSpec
    stopping: StoppingSpec
    selection: SelectionSpec
    postprocessing: PostprocessingSpec

    @model_validator(mode="after")
    def statically_compatible(self) -> "CompositionV1":
        validate_capability_graph(self)
        return self
```

The persisted string values in this skeleton (`"sum_product_v1"`, `"identity_state_v1"`, `"kind"`) are proposed rather than verified in-repo values. [ASSUMED]

### Reserve-Before-Work Flooding Step

```python
# Proposed engine protocol; the full-sweep work definition is [ASSUMED].
def flooding_iteration(engine: EngineState, schedule: FloodingPolicy) -> Candidate:
    planned = WorkVector(
        check_to_variable_updates=engine.graph.edge_count,
        variable_to_check_updates=engine.graph.edge_count,
        belief_assemblies=engine.problem.variable_count,
        candidate_checks=1,
    )
    reservation = engine.budgets.reserve(planned, leaf=engine.attempt_id)
    if not reservation.accepted:
        raise BudgetTermination.from_reservation(reservation)

    old_v2c = engine.messages.variable_to_check
    new_c2v = schedule.all_check_updates_from(old_v2c)
    new_v2c = schedule.all_variable_updates_from(new_c2v)
    beliefs = engine.kernel.assemble_beliefs(new_c2v)
    candidate = engine.kernel.hard_decision(beliefs)

    engine.assert_finite(new_c2v, new_v2c, beliefs)
    engine.messages.commit(new_c2v=new_c2v, new_v2c=new_v2c)
    reservation.commit_once()
    engine.events.append_leaf_work(planned)
    return candidate
```

Implementation must define rollback/no-commit behavior for exceptions between reservation and commit; no work may be both committed and re-emitted on recovery. [ASSUMED]

### Truth-Sealed Execution and Frozen Selection

```python
# Existing source boundary:
# DecoderObservation and HiddenTruth are distinct in sampling.py:16-40.
sample = sampling.sample_shot(...)
original = OriginalProblem.from_observation(
    code=resolved.code,
    observation=sample.observation,
)

execution = canonical_engine.run(
    original=original,              # no ShotSample / HiddenTruth reachability
    composition=resolved.composition,
    decoder_rng=resolved.decoder_rng,
)
selection = execution.freeze_selection()  # decoder-visible evidence only

for emitted in execution.original_space_candidates():
    evaluation = evaluator.evaluate_candidate(
        resolved.code,
        true_x=sample.hidden.x,
        true_z=sample.hidden.z,
        candidate_x=emitted.candidate_x,
        candidate_z=emitted.candidate_z,
    )
    execution.record_evaluation_annotation(
        candidate_id=emitted.candidate_id,
        evaluation=evaluation,
    )  # post-selection annotation, no feedback

selected_evaluation = execution.evaluation_for(selection.candidate_id)
```

This preserves the existing exact outcome vocabulary `"invalid_syndrome", "exact", "stabilizer_equivalent", "logical_failure"`. [VERIFIED: `src/bp_registry/evaluator.py:13`]

## State of the Art

| Old/Insufficient Approach | Current Recommended Approach | Evidence / When Changed | Impact for Phase 2 |
|---------------------------|------------------------------|-------------------------|--------------------|
| Direct `tanh` product + `atanh` with implicit infinities | stable LLR box-plus with explicit finite saturation and failure boundaries | Exact equation is classical; BPGD source explicitly clips LLRs and reports numerical issues with infinite values. [CITED: https://arxiv.org/abs/cs/0702111; CITED: https://arxiv.org/html/2312.10950v2] | Numeric semantics become reproducible and testable. |
| “Parallel” as a string without read/write semantics | double-buffered flooding with qualified iteration/work counts | Scheduling literature distinguishes simultaneous stale-state updates from serial/residual behavior. [CITED: https://arxiv.org/abs/cs/0702111] | Prevents accidental algorithm drift and supports later schedules. |
| Adapter-level common API | project-owned kernel + explicit policy/lifecycle contracts | Locked project architecture. [VERIFIED: `AGENTS.md:7,13,59-64`] | Enables interpretable controlled comparison. |
| One terminal row only | sparse structural lifecycle + optional bounded trace sidecars | Phase 1 ledger v1 accepts only `"begin"` and `"terminal"`; Phase 2 requires linked nested control flow. [VERIFIED: `src/bp_registry/ledger.py:73-90`; VERIFIED: `.planning/REQUIREMENTS.md:95`] | Preserves provenance without making per-edge traces mandatory. |
| Iteration count as universal effort | schedule-qualified iterations plus atomic work vector and runtime/resource context | Locked D-14–D-16. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:34-36`] | Comparisons remain meaningful as schedules/search diversify. |
| Profile only “interesting” failures | clean full population + prespecified paired representative profile cohort + labeled tail replays | Locked D-18–D-19; sampling profiling has established precedent. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:38-39`; CITED: https://minds.wisconsin.edu/handle/1793/11182] | Separates unbiased overhead estimates from diagnostic depth. |

**Deprecated/outdated for this phase:**

- Mutating `ManifestV1` meanings in place: preserve its native-reference replay and add explicit version/kind dispatch. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:87-104`]
- Calling `ldpc.BpDecoder` inside canonical execution: retain only as an external reference. [VERIFIED: `.planning/REQUIREMENTS.md:34`]
- Global NumPy error-mode changes: use a local `errstate` scope, which restores prior behavior on exit. [CITED: https://numpy.org/doc/2.2/reference/generated/numpy.errstate.html]
- Reporting profiled wall time as baseline runtime: clean population owns runtime estimates. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:38-39`]

## Planning Implications

Plan this phase as dependency-ordered slices with tests written at each contract boundary:

1. **Wave 0 — executable specifications:** add tiny parity-graph fixtures, analytic message/candidate expectations, trace golden records, hostile truth-access probe, and test skeletons. Do not begin runner integration until these fail for the intended reason.
2. **Contracts — persisted and runtime:** add the canonical manifest variant, seven explicit policy specs, compatibility/capability graph, lifecycle scope types, typed decisions, numerical profile, budget/work/termination schemas, and lineage/event/trace/profile schemas. Preserve Phase 1 schema readers.
3. **Pure primitives (parallelizable after contracts):** (a) stable numerical/kernel/flooding state machine; (b) hierarchical budget reservation + leaf-work aggregation; (c) lineage IDs + bounded sidecar sink; (d) timing/memory adapters. Each can be unit-tested without the runner.
4. **Engine vertical slice:** instantiate the baseline seven-role composition, run the full hierarchy even for one member/attempt, freeze selection, identity-lift the candidate, then invoke the independent evaluator outside the engine.
5. **Evidence/CLI slice:** versioned canonical ledger writer/reader, summaries, canonical manifest resolution, CLI command, deterministic tutorial fixture, and a documented command whose output is verified from durable rows.
6. **Profiling and documentation gate:** paired clean/profile replay, missing counter handling, semantic-agreement check, tutorial/conventions/compatibility docs, `docs/profiling-and-tracing-strategy.md`, and `docs/research-novelty-and-depth-register.md`.

Do not split “budgets” from “work vector” or “selection” from “truth boundary” into unrelated late tasks; each pair has a shared invariant and should be reviewed together. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:32-35,45-47`]

### Documentation Deliverables

| Document | Minimum Phase 2 Content | Verification |
|----------|-------------------------|--------------|
| `docs/canonical-engine.md` [ASSUMED path] | install/run tutorial; LLR convention/equations; graph/edge ordering; init; `float64`; saturation/failure boundaries; ties; flooding old/new buffers; seven roles; lifecycle hooks; compatibility; budgets; work vector; lineage; selection/evaluation boundary; deterministic small examples | Execute every command in a docs smoke test; compare resolved profile and semantic trace to checked-in fixture. |
| `docs/profiling-and-tracing-strategy.md` | scientific value/cost; sparse vs iteration/edge levels; record+byte caps; truncation; clean/representative/tail cohorts; pairing/overhead/semantic agreement; plotting; missing counters; retention | Required verbatim by D-20. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:40`] |
| `docs/research-novelty-and-depth-register.md` | potential contribution; executable evidence; closest precedents; unresolved searches; claim maturity; initial profiling and selective-tracing entries; explicit “provisional” novelty status | Required verbatim by D-26. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:48`] |

The tutorial must present the canonical run as `canonical-implemented`/development evidence, not as a statistically assessed reproduction unless a later assessment meets its manifest criterion. [VERIFIED: `AGENTS.md:16-18,64`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Proposed module names, hook/event identifiers, binding fields, policy discriminator values, and typed numerical-failure fields are suitable initial public contracts. | Project Structure; Patterns 1/4; Code Examples | Medium — names become persisted/API meanings; choose once in contract plan and version thereafter. |
| A2 | Local defaults of 1,024/1 MiB iteration trace, 50,000/8 MiB edge trace, 32/4 MiB rejected payloads, 1% (8–128) representative cohort, and 16 tail replays are practical for Phase 2 fixtures. | Pattern 4 | Low for Phase 2, high if mistaken for publication targets — all must be configurable and campaigns must prespecify new values. |
| A3 | One Phase 2 flooding iteration should atomically count `|E|` check-to-variable updates, `|E|` variable-to-check updates, `n` belief assemblies, and one candidate check, with the BP call counted at attempt scope. | Pattern 2; Code Examples | High — changes historical work semantics; lock with golden tests and documentation before emitting durable runs. |
| A4 | Stable IDs should derive from typed logical ancestry plus content, and traces/candidates should use a content-addressed run-local layout. | Pattern 4; Pitfall 7 | Medium — affects replay, merge, deduplication, and future concurrency. |
| A5 | Initial profile `binary-spa-flooding-f64-v1`, symmetric `K=25`, exact-zero→bit-0, and ascending-index ties are appropriate baseline conventions. | Pattern 2; Code Examples | High — numerical profile IDs are durable meanings; verify analytic/extreme fixtures and materialize every field. |
| A6 | Portable strict JSON/JSONL plus bounded NumPy-compatible payloads should be preferred to Python pickle. | Standard Stack Alternatives | Low — alternate portable payload formats may be chosen, but executable deserialization must remain out. |
| A7 | A full sweep should be reserved and committed atomically; no partial-sweep state is useful in Phase 2. | Anti-Patterns; Code Examples | Medium — later chunked/parallel backends may require a versioned atomic-unit extension, which D-13 already anticipates. |
| A8 | The Phase 2 local CLI has no application authentication/session/access-control boundary; a closed policy registry is sufficient; SHA-256 is identity/integrity rather than authenticity. | Security Domain | Medium — must be revisited before loading external plugins, accepting remote users, or publishing signed releases. |

All assumed choices fall under the explicit agent-discretion areas in CONTEXT.md; none changes a locked decision. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:50-53`]

## Open Questions

1. **What exact persisted schema/version identifiers should the canonical manifest and richer ledger use?**
   - What we know: v1 manifest/ledger meanings must remain replayable; ledger v1’s event kinds are exactly `"begin"` and `"terminal"`. [VERIFIED: `src/bp_registry/ledger.py:21,73-90`]
   - What is unclear: whether project convention prefers a top-level v2 schema or an execution-kind-dispatched sibling schema.
   - Recommendation: choose explicit new versions in the first contracts plan; never make a v1 record conditionally mean canonical execution.

2. **Should `K=25` remain the first canonical profile after analytic fixture review?**
   - What we know: finite clipping is locked and BPGD uses 25 with a numerical rationale. [CITED: https://arxiv.org/html/2312.10950v2]
   - What is unclear: whether a selected binary reference experiment requires a different source-faithful clip.
   - Recommendation: keep `K=25` for the canonical baseline profile; represent any paper-specific value as a separately named profile/explicit adaptation, not an invisible override.

3. **What exact RSS normalization should be recorded on non-Linux hosts?**
   - What we know: `resource.ru_maxrss` means maximum resident set size, but Python directs users to platform documentation for field details. [CITED: https://docs.python.org/3.12/library/resource.html]
   - What is unclear: future macOS/other POSIX units and whether process children should be included.
   - Recommendation: Phase 2 adapter records platform, `RUSAGE_SELF`, raw value/unit, normalized bytes, and method version; unsupported normalization is missing, not guessed.

4. **What publication-scale trace/profile quotas and retention policy will be used?**
   - What we know: the phase must provide explicit configurable local defaults and three separate cohorts. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:38-40,50-53`]
   - What is unclear: HPC allocation, campaign size, retention budget, and target journal requirements remain undecided. [VERIFIED: `AGENTS.md:19-21`]
   - Recommendation: mark Phase 2 defaults “development only”; require preregistered campaign values in later manifests.

No open question blocks Phase 2 planning.

## Environment Availability

| Dependency | Required By | Available | Version / Observation | Fallback |
|------------|-------------|-----------|-----------------------|----------|
| Approved `.venv` Python | all Phase 2 code/tests | ✓ | Python 3.12.2; project import works | none; base Python is not approved |
| NumPy | kernel/numerics | ✓ | 2.2.6 | none |
| Pydantic | manifests/contracts | ✓ | 2.13.5 | none |
| SciPy | inherited research stack | ✓ | 1.17.1 | baseline kernel does not require it |
| `ldpc` | native reference only | ✓ | 2.4.1 | canonical execution remains independent |
| pytest | validation | ✓ | 9.0.3 | none |
| `perf_counter_ns`, `process_time_ns` | wall/CPU timing | ✓ | Python 3.12 stdlib, local probe passed | explicit missing metric if unavailable |
| `resource.getrusage`, `/proc/self/status` | RSS/resource context | ✓ | Linux 5.14 x86_64, local probe passed | `tracemalloc` only for Python allocations; do not label as RSS |
| `tracemalloc` | representative profiled cohort | ✓ | Python 3.12 stdlib, local probe passed | profile adapter reports unavailable |
| Linux `perf` CLI/counters | optional deep profiling | ✗ | command absent; `perf_event_paranoid=2` observed | stdlib timing/memory adapters; explicit missing reason |
| `OMP_NUM_THREADS=1` | deterministic/test environment identity | ✓ when set per command | unset by default | prefix every run/test command explicitly |

The `.venv` provenance and inherited-package limitation are documented in-repo. [VERIFIED: `docs/environment-pins.md:48-66`] A local import/version probe and `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` succeeded with 71 tests on 2026-09-22. [VERIFIED: local execution, 2026-09-22]

The base `/hpc/home/mg551/miniconda3/bin/python` lacks the approved Pydantic/project environment and produced dependency/import failures during the audit; do not use it for the plan. [VERIFIED: local execution, 2026-09-22]

**Missing dependencies with no fallback:** none.  
**Missing dependencies with fallback:** Linux `perf`/hardware counters; use stdlib adapters and persist the unavailability reason.  
**Install warning:** because all package legitimacy results are `SUS`, any reinstall or upgrade requires a planner `checkpoint:human-verify`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 [VERIFIED: local `.venv` probe, 2026-09-22] |
| Config file | `pyproject.toml`; exact entries are `testpaths = ["tests"]`, `pythonpath = ["src"]`. [VERIFIED: `pyproject.toml:16-18`] |
| Existing suite | 71 collected/executed tests pass with required environment prefix. [VERIFIED: local execution, 2026-09-22] |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <target-test-file>` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` (22.41 s observed) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| ENG-01 | manifest → project-owned canonical kernel → selected/lifted candidate → independent outcome → durable provenance | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py` | ❌ Wave 0 |
| ENG-02 | seven roles required; identities explicit; invalid capability/hook/state combinations rejected statically/runtime | unit/adversarial | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py` | ❌ Wave 0 |
| ENG-03 | child/ancestor hard caps; no overrun/partial commit; terminal names scope/resource/limit/consumption/reason | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py` | ❌ Wave 0 |
| ENG-04 | LLR encoding/init, stable extreme/degree-one values, clipping, nonfinite failure, ties, old/new order | analytic/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py` | ❌ Wave 0 |
| ENG-05 | hostile policy cannot reach hidden truth; identity lift returns original-space candidate; evaluation occurs after frozen selection | adversarial/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_truth_boundary.py` | ❌ Wave 0 |
| ENG-06 | every implemented policy declares source/procedure and deterministic invariants | schema/unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_policy_evidence.py` | ❌ Wave 0 |
| SCH-01 | reverse edge-order probe cannot alter flooding result; each full sweep records exact proposed vector | unit/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_flooding.py` | ❌ Wave 0 |
| LED-02 | all required structural events remain; filtered sidecars link/hash; record/byte truncation explicit; tracing never changes output | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py` | ❌ Wave 0 |
| LED-03 | unique leaf deltas equal ancestor/root summaries; qualified iteration and runtime/resource context queryable | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_work_accounting.py` | ❌ Wave 0 |
| LED-04 | native edge updates remain `None` with exact reason and never become zero | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py` | ✅ extend existing |
| DOC-01 | documented install/run command executes deterministic fixture and referenced conventions match resolved manifest | docs smoke/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial` | ❌ Wave 0 |

### Required Kernel Test Oracles

- Zero-syndrome/no-error fixed point.
- Single parity check with degree 1 (expected finite signed saturation) and degree 2 (analytic outgoing LLR).
- Symmetric graph where reordering the stable edge table must not alter flooding output.
- Safe-magnitude agreement between direct `2*atanh(prod(tanh(m/2)))` oracle and stable box-plus.
- Extreme positive/negative LLRs, probability endpoints, exact-zero belief tie, and injected NaN/inf.
- A two-iteration case that distinguishes old-buffer flooding from in-place fresh-message updates.
- Exact work vector for success, max-iteration stop, pre-sweep budget stop, numerical failure, and trace truncation.
- Re-run identity: same manifest/sample/decoder stream yields the same candidate, lineage IDs, work, and semantic trace digest; timing fields may differ and must be excluded from semantic identity. [ASSUMED]

### Sampling Rate

- **Per task commit:** targeted file command above, normally under 30 seconds.
- **Per wave merge:** `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`.
- **Phase gate:** full suite green; documented tutorial executed; a ledger reconciliation/verification reconstructs the deterministic canonical result; no unresolved nonfinite, missingness, or lineage invariant.

### Wave 0 Gaps

- [ ] `tests/canonical/conftest.py` — tiny graph/CSS fixtures, analytic message helpers, manifest builders.
- [ ] `tests/canonical/test_contracts.py` — ENG-02/ENG-06.
- [ ] `tests/canonical/test_numerics.py` and `test_flooding.py` — ENG-04/SCH-01.
- [ ] `tests/canonical/test_budgets.py` and `test_work_accounting.py` — ENG-03/LED-03.
- [ ] `tests/canonical/test_truth_boundary.py` — ENG-05.
- [ ] `tests/canonical/test_tracing.py` — LED-02.
- [ ] `tests/test_canonical_cli.py` — ENG-01/DOC-01 vertical slice.
- [ ] `tests/fixtures/` canonical manifest and golden semantic events/traces.
- Framework install: none; reuse approved pytest environment.

## Security Domain

Security enforcement is active: the config quotes `"security_enforcement": true` and `"security_asvs_level": 1`. [VERIFIED: `.planning/config.json:48-49`] This is a local research CLI rather than a networked multi-user application, so apply ASVS controls to the real trust boundaries: manifests, artifacts, trace destinations, policy registry, resource use, and evidence integrity.

OWASP ASVS 5.0 is the current project reference used here. Its file-handling controls require accepted file constraints, size/content validation, and safe paths; use the tagged primary repository/PDF rather than legacy category numbering as the control authority. [CITED: https://github.com/OWASP/ASVS/tree/v5.0.0; CITED: https://github.com/OWASP/ASVS/releases/tag/v5.0.0]

### Applicable ASVS Categories

| ASVS Category (planning template) | Applies | Standard Control |
|-----------------------------------|---------|------------------|
| V2 Authentication | no | No user/account boundary in the Phase 2 local CLI. Reassess if a service is later exposed. [ASSUMED] |
| V3 Session Management | no | No browser/session/token state. Reassess on service deployment. [ASSUMED] |
| V4 Access Control | no at application layer | Rely on OS/HPC filesystem permissions; code still confines artifact/sidecar roots. [ASSUMED] |
| V5 Input Validation | yes | Pydantic strict/frozen/extra-forbid/finite schemas; matrix/record/byte/count limits; root-resolved path and symlink rejection. [VERIFIED: `src/bp_registry/manifests.py:27-30`; VERIFIED: `src/bp_registry/artifacts.py:16-18,70-91`] |
| V6 Cryptography | limited integrity use | stdlib SHA-256 for content identity; never imply an unauthenticated digest proves authorship or prevents malicious replacement. Existing identities require lowercase 64-hex SHA-256. [VERIFIED: `src/bp_registry/artifacts.py:31-34`] |

The no/limited applicability decisions above are architecture assumptions to revisit when remote services, external policy plugins, or signed releases are introduced. [ASSUMED]

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Manifest/artifact/trace path traversal or symlink escape | Tampering / Information disclosure | Resolve against an approved root, reject absolute and `..` parts, reject symlinks, verify resolved containment, and generate content-addressed leaf names. Reuse the existing path implementation. [VERIFIED: `src/bp_registry/artifacts.py:70-91`] |
| Oversized matrix, ledger event, trace, or candidate payload | Denial of service | Enforce pre-parse bytes, dimensions/cells, per-sidecar records+bytes, rejected-payload caps, and hierarchical execution budgets. Existing artifact limits quote `1_000_000`, `10_000`, and `2_000_000`. [VERIFIED: `src/bp_registry/artifacts.py:16-18`] |
| NaN/inf/coercive numeric input | Tampering / Denial of service | `allow_inf_nan=False`, strict schemas, `np.isfinite`, local floating exceptions, terminal numerical failure. [CITED: https://docs.pydantic.dev/latest/api/config/; CITED: https://numpy.org/doc/2.2/reference/generated/numpy.isfinite.html] |
| Dynamic import of arbitrary policy implementation from manifest | Elevation of privilege | Phase 2 uses a closed, versioned in-code registry mapping known data specs to implementations; no eval/exec/import path from untrusted JSON. [ASSUMED] |
| Hidden-truth or evaluator leakage into policy views | Information disclosure / scientific integrity failure | Construct narrow frozen/copy/read-only capability views; adversarial reachability tests; selection freezes before evaluator creation. [VERIFIED: `src/bp_registry/sampling.py:16-40`; VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:19,47`] |
| Ledger truncation, partial writes, duplicate ownership, or lineage tampering | Tampering / Repudiation | Preserve per-shot ownership, canonical JSON, flush+fsync, append-only typed events, content hashes, reconciliation, and summary reconstruction. Existing append calls `flush()` and `os.fsync()`. [VERIFIED: `src/bp_registry/ledger.py:111-118`] |
| Digest treated as authenticity | Spoofing | Describe SHA-256 as content identity/integrity only; signed release provenance is a separate later control. [ASSUMED] |
| Profiling leaks environment/path details or changes results | Information disclosure / Tampering | Schema allowlisted environment fields, no secrets/env values, bounded sidecars, clean/profile separation, semantic-agreement check. [VERIFIED: `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md:36-40`] |

### Security Verification Tasks for the Plan

- Fuzz/negative-test extras, wrong types, NaN/inf, huge budgets, unknown policy kinds, duplicate binding IDs, and incompatible capabilities.
- Attempt absolute path, `..`, symlink, over-limit sidecar, and content-hash mismatch writes.
- Run a hostile policy that introspects every supplied object and prove `ShotSample`, `HiddenTruth`, evaluator, filesystem handles, and mutable engine state are unreachable.
- Interrupt writes and simulate duplicate ownership; reconcile to exactly one terminal record with explicit incomplete/missing facts.
- Assert trace/profile settings cannot change candidate, work vector, lineage IDs, or terminal semantic fields.

## Sources

### Primary (HIGH confidence)

- `src/bp_registry/manifests.py`, `sampling.py`, `evaluator.py`, `reference.py`, `ledger.py`, `runner.py`, `artifacts.py`, `cli.py` — source-of-truth Phase 1 contracts opened with line numbers this session.
- `.planning/phases/02-canonical-css-execution-and-policy-contracts/02-CONTEXT.md` — locked phase decisions, discretion, boundaries, and deferred ideas.
- `.planning/REQUIREMENTS.md` — ENG-01–06, SCH-01, LED-02–04, DOC-01 exact acceptance statements.
- [Vila Casado et al., “Informed Dynamic Scheduling for Belief-Propagation Decoding of LDPC Codes”](https://arxiv.org/abs/cs/0702111) — LLR SPA equations, flooding/message scheduling, and schedule-sensitive work.
- [Yao et al., “Belief Propagation-Guided Decimation for QLDPC Codes”](https://arxiv.org/abs/2312.10950) — syndrome-aware binary BP rounds, finite clipping precedent, and convergence structure.
- [OWASP ASVS 5.0.0 tagged source](https://github.com/OWASP/ASVS/tree/v5.0.0) — security control reference.

### Secondary (MEDIUM confidence)

- [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/), [strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/), [unions](https://docs.pydantic.dev/latest/concepts/unions/), and [validators](https://docs.pydantic.dev/latest/concepts/validators/) — strict/frozen/finite models and tagged composition validation.
- [NumPy 2.2 `logaddexp`](https://numpy.org/doc/2.2/reference/generated/numpy.logaddexp.html), [`isfinite`](https://numpy.org/doc/2.2/reference/generated/numpy.isfinite.html), and [`errstate`](https://numpy.org/doc/2.2/reference/generated/numpy.errstate.html) — stable log arithmetic and explicit numerical failure checks.
- [Python 3.12 `time`](https://docs.python.org/3.12/library/time.html), [`resource`](https://docs.python.org/3.12/library/resource.html), and [`tracemalloc`](https://docs.python.org/3.12/library/tracemalloc.html) — timing/memory measurement semantics and scope.
- [Google-Wide Profiling](https://research.google/pubs/google-wide-profiling-a-continuous-profiling-infrastructure-for-data-centers/) and [Rapid Profiling via Stratified Sampling](https://minds.wisconsin.edu/handle/1793/11182) — profiling sampling/overhead precedents.
- PyPI index queries and the GSD package-legitimacy seam on 2026-09-22 — package-version availability and conservative SUS audit.

### Tertiary (LOW confidence / design choices requiring lock-in)

- Initial module/type/event names, numerical profile identifier, hard-decision tie, full-sweep work definition, content-addressed layout, trace/retention quotas, and profile cohort sizes — all listed in the Assumptions Log.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH for current pins/environment; MEDIUM for future registry freshness because all legitimacy verdicts are conservatively SUS.
- Numerical architecture: HIGH for exact SPA/flooding sources and NumPy primitives; MEDIUM for `K=25`, tie rule, and exact atomic work convention until fixtures lock them.
- Policy/lifecycle architecture: HIGH for locked responsibilities/boundaries; MEDIUM for proposed names and schema version layout.
- Ledger/profiling architecture: HIGH for locked sparse/sidecar/cohort semantics; MEDIUM for exact event vocabulary, storage layout, and local quota values.
- Pitfalls/security: HIGH where demonstrated by existing code/contracts; MEDIUM for future plugin/service threats that Phase 2 does not yet expose.
- Validation architecture: HIGH for current pytest infrastructure/suite command; MEDIUM for proposed test-file decomposition.

**Research date:** 2026-09-22  
**Valid until:** architecture/source guidance 2026-10-22; package-version/legitimacy observations 2026-09-29
