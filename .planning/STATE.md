---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: 04
current_phase_name: Memory Policies and Relay-BP
current_plan: 12
status: executing
stopped_at: Plan 04-12 external calibration running; independent continuation verified with 560 tests
last_updated: "2026-09-27T18:59:32Z"
last_activity: 2026-09-27
last_activity_desc: Calibration 3846/5824 (66.0%); isolated eb16e22 verified with 560 passed and one pre-existing skip
state_head: 789034ad680c933b604e73c117ef976208744691
progress:
  total_phases: 14
  completed_phases: 3
  total_plans: 57
  completed_plans: 54
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-22)

**Core value:** Make BP decoder differences explicit, reproducible, and fairly comparable through canonical policy execution and published evidence.
**Current focus:** Phase 04 — Memory Policies and Relay-BP

## Current Position

Phase: 04 (Memory Policies and Relay-BP) — EXECUTING
Plan: 12 of 15
Total Phases: 14
Current Plan: 12
Total Plans in Phase: 15
Status: Executing Phase 04; external calibration running; isolated continuation fully verified
Last activity: 2026-09-27 — Resumed Phase 4 and implemented independent corrections
Last Activity Description: Calibration 3846/5824 (66.0%); independent local memory/audit/recovery/shared preparation verified, 560 passed and one pre-existing skip; no plan counts advanced

Progress: 54/57 current plans have summaries; Phase 4 is 12/15. Fresh phase verification is 1/14: Phase 3 passed; Phase 1/2 previously passed reports are now flagged stale. Three phases were previously recorded complete; this freshness audit does not erase their completed plans.

## Performance Metrics

- Total plans completed: 54
- Average duration: N/A
- Total execution time: 0 hours
- Recent trend: Phase 1 completed 9 plans; Phase 2 completed 16 plans, including seven review-driven gap plans, and passed goal, code, security, and validation gates.

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 02 P01 | 18m | 2 tasks | 9 files |
| Phase 02 P02 | 17m | 2 tasks | 6 files |
| Phase 02 P03 | 7m | 2 tasks | 6 files |
| Phase 02 P05 | 13m | 2 tasks | 5 files |
| Phase 02 P04 | 7 min | 2 tasks | 4 files |
| Phase 02 P06 | 8 min | 2 tasks | 7 files |
| Phase 02 P07 | 10 min | 2 tasks | 3 files |
| Phase 02 P08 | 8 min | 3 tasks | 10 files |
| Phase 02 P09 | 16 min | 2 tasks | 7 files |
| Phase 04 P01 | 31m | 2 tasks | 10 files |
| Phase 04 P02 | 6m | 2 tasks | 3 files |
| Phase 04 P03 | 18m | 2 tasks | 4 files |
| Phase 04 P04 | 11m | 2 tasks | 9 files |
| Phase 04 P05 | 14m | 2 tasks | 4 files |
| Phase 04 P07 | 67s | 1 tasks | 1 files |
| Phase 04-memory-policies-and-relay-bp P06 | 417 seconds | 2 tasks | 6 files |
| Phase 04 P08 | 25m | 2 tasks | 5 files |
| Phase 04 P09 | 14m | 2 tasks | 5 files |
| Phase 04 P15 | 22m | 1 tasks | 5 files |
| Phase 04 P10 | 58m | 2 tasks | 8 files |
| Phase 04 P11 | 0 | 2 tasks | 73 files |

Phase 02 P10–P16 gap-closure metrics are recorded in their individual summaries.

## Accumulated Context

### Decisions

Full decisions are in PROJECT.md; workflow choices are in config.json.

- First journal milestone includes CSS code-capacity → correlated quaternary code-capacity → circuit level; none is deferred beyond the paper.
- Canonical engines are defined per compatible kernel family. BP modifications are primary; OSD/LSD is optional additional processing for nonconvergence.
- Reproduction requires declared statistical agreement, not bitwise identity; source semantics and outcome correctness require separate checks.
- Preserve faithful source configurations and controlled shared-sample/work-budget comparisons as separate evaluation views.
- Autonomous execution, fine phases, parallel independent agents, Git-tracked planning, full instructions, research/checking/verification enabled; saved Codex model/effort overrides retained.
- Phase 1 selected a source-pinned Bravyi BB-144 artifact and kept its 32-shot native BP pilot labeled `pilot_adaptation` and `not_assessed`.
- Phase 1 preserves ordered CSS matrix/logical identity, strict manifest preflight, and a durable shot ledger with independent outcome evaluation.
- [Phase 02]: Canonical manifests require seven explicit policy roles, including named identity roles.
- [Phase 02]: Canonical selection freezes immutable decoder-visible candidates before independent truth-aware evaluation.
- [Phase 02]: Persisted canonical compositions require seven explicit closed-registry policy bindings.
- [Phase 02]: The engine owns lifecycle traversal and binding-private state; policies return typed decisions only.
- [Phase 02]: Each resolved policy binding carries a procedure basis and deterministic ordered invariants.
- [Phase 02]: Phase 02: binary-spa-flooding-f64-v1 fixes CPU float64 natural-log odds, symmetric K=25 saturation, and deterministic zero/tie rules.
- [Phase 02]: Phase 02: flooding reads one complete old v2c snapshot, then commits a complete new v2c buffer after c2v and belief phases.
- [Phase 02]: Canonical lineage IDs derive from typed logical parents and canonical content, never timing or append order.
- [Phase 02]: Canonical structural evidence uses a separate v2 grammar; optional semantic sidecars are confined, hash-linked, and observational.
- [Phase 02]: Phase 02: count budgets reserve complete typed sweep work before mutation, while wall-clock limits remain distinct declared-boundary controls.
- [Phase 02]: Phase 02: canonical work is committed only as unique leaf vectors and ancestor totals are derived by typed scope ancestry.
- [Phase 02]: Phase 02: iteration, runtime, and resource measurements retain schedule, unit, precision, method, scope, and explicit missingness.
- [Phase 02]: Native SDK iterations remain qualified observations and are never equated with canonical flooding work.
- [Phase 02]: Opaque native internals serialize as unavailable metric facts with reasons and availability-only summaries.
- [Phase 02]: Local standard-library profiling is default-on but retains explicit missingness and separately measured adapter overhead.
- [Phase 02]: Only pre-outcome representative paired cohorts with inclusion probability and semantic agreement can support profiling population estimates.
- [Phase 02]: Replay semantics compare candidate, termination, work, lineage, and trace digest while excluding measurement timing.
- [Phase 02]: Phase 02: public canonical experiments use a strict persisted CanonicalExperimentV2 while compact kernel contracts remain direct-test APIs.
- [Phase 02]: Phase 02: canonical results reconstruct from hash-linked v2 terminal evidence and retain canonical_implemented/development_fixture/not_assessed labels.
- [Phase 02]: Phase 02: canonical CPU runtime is measured per attempt and unavailable device timing is explicit missingness.
- [Phase 02]: Phase 02: public preflight reports persisted and resolved numerical profiles separately; canonical reconcile queries v2 terminals without changing legacy v1 repair semantics.
- [Phase 02]: Phase 02: profiling and selective tracing remain provisional diagnostic evidence pending campaign preregistration and corpus recheck.
- [Phase 02]: Public execution rejects non-baseline policies and unbounded profiling plans before sampling; full manifest, artifact, sample, and shot identity bind replay.
- [Phase 02]: Public verification reconstructs deterministic terminal, budget, work, candidate, lineage, and outcome claims; transient numerical errors retain explicit nonreproduction status.
- [Phase 02]: Public low-overhead profile evidence has producer-backed metric and unavailable-RSS grammars; nondeterministic measurements are same-ledger observations, not replay-equality facts.
- [Phase 04]: Phase 04: V4 manifests alone persist contiguous ordered affine-prior bindings, preserving V2/V3 semantics.
- [Phase 04]: Phase 04: Relay legs transfer only a finite digest-bound posterior LLR and reset all leg-local execution state.
- [Phase 04]: Phase 04: PDBP field mixing and PD-prime delta mixing remain separate source-linked state machines.
- [Phase 04]: Phase 04: Uniform EWAInit and Relay affine memory share one primitive under gamma = 1 - alpha.
- [Phase 04]: Memory bindings persist contiguous explicit order with disjoint history ownership.
- [Phase 04]: Memory refreshes use decoder-local replay identities and one-owner commits.
- [Phase 04]: CanonicalExperimentV4 extends the full V3 public evidence contract with ordered memory bindings while preserving historical V2/V3 meanings.
- [Phase 04]: Public V4 preflight rejects incompatible memory operands before artifact loading and records resolved binding order and compatibility evidence.
- [Phase 04]: Phase 04: Relay source and canonical presets are immutable named CSS adaptations; modified controls receive a controlled-adaptation identity.
- [Phase 04]: Phase 04: Relay candidate selection uses decoder-visible syndrome/prior weights and stable earlier-leg ties.
- [Phase 04]: Use only trmue/relay tag v0.2.2 at immutable commit 14cb31a18f9b9d7d099791b793e35b8a2951f8f3 as the original Relay reference.
- [Phase 04]: Keep the PyPI relay-bp package and editable mg551-duke/relay fork outside the approved original-reference identity.
- [Phase 04]: Phase 04 Plan 06: V4 Relay evidence reconstructs only from unique typed leaves and preserves V2/V3 semantics.
- [Phase 04]: Phase 04 Plan 08: exact Relay v0.2.2 adapter uses only decoder-visible inputs and never imports the installed fork.
- [Phase 04]: Phase 04 Plan 08: comment-only Relay observer preserves a behavior-neutral boundary; gamma, edge work, and resource facts remain unavailable.
- [Phase 04]: Phase 04 Plan 09: B1 resolves to the frozen v3 artifact; only the inventory semantic digest was stale.
- [Phase 04]: Phase 04 Plan 09: Phase 4 B1 manifests bind v3 and preserve all Phase 3 B1 evidence byte-for-byte.
- [Phase 04]: Phase 04 Plan 15: freeze focused factorial arms, three-region noise grids, and matched sample namespaces before sampling.
- [Phase 04]: Phase 04 Plan 15: bind B1 to the Plan 04-09 resolution digest and keep generated HGP explicitly non-paper-exact.
- [Phase 04]: Phase 04 Plan 10: exact-author native Relay runs only from a stage-local verified v0.2.2 checkout; canonical and native arms share public observations but retain separate identities.
- [Phase 04]: Phase 4 caps use one worker and rate-specific representative Relay evidence; B1 p=.07 is bounded to a measured three-leg-equivalent work vector.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Current resumed execution: calibration 3846/5824 (66.0%) at 2026-09-27T18:59:32Z. Isolated source `eb16e22` is verified: 560 passed, one pre-existing skip, 454.56s; artifact head `ce1c22d`. No main source merge or new production stage. Earlier September 27 entries below are historical snapshots; see the resumed execution report for current scope and remaining gates.

- New-chat progress audit: calibration running with 3,716/5,824 retained attempts (63.8%) at 2026-09-27T17:20:42.542Z. See `.planning/HANDOFF.json` for the measured snapshot and async resume context. Phase 1/2 verification reports are now flagged stale by GSD and need refreshing; Phase 3 remains passed. No completed plans were rerun or removed.
- Phase 4 calibration remains `running` (PID 2702938); Plans 04-12/13/14 remain incomplete. Independent local PD-prime/momentum/affine execution, semantic failure-prefix traces, exact-byte terminal readers, immutable shot contexts and notebook views are verified in isolated source `62fe977`: 532 tests passed, one existing skip. Both notebooks execute all 14 cells without errors. The completed benchmark summary retains a real incomplete B1 p=.07 arm, so its rows remain explicitly unqualified. Fresh production evidence, retained histories/additional lifetimes, other local schedules, disordered local affine and Relay traces remain. Keep source changes separate from the live campaign. See [implementation continuation](phases/04-memory-policies-and-relay-bp/04-IMPLEMENTATION-CONTINUATION-20260927.md) and [coding handoff](phases/04-memory-policies-and-relay-bp/04-CODING-RESUME-HANDOFF.md).
- Phase 3 passed goal verification with 17/17 plans and all eight requirements complete. The Hsu source-defined group schedule has a retained, independently verified two-shot CSS pilot. The Moradi artifact remains unavailable and is not conflated with the Hsu policy.

Phase 2 is complete (16/16 plans; 5/5 goal criteria; clean review; 46/46 security threats closed). Remaining research concerns for later phases:

- Original BPGD/impulse code identities remain unverified; exact SI/OTF variants and generic mixing/memory/voting definitions need source specifications.
- Statistical targets and compute budgets for publication campaigns remain to be prespecified.
- The observed development environment is node-specific; recheck package and backend identity before interpreting runs elsewhere.
- Circuit fault correlations and observable semantics require dedicated qualification; a CSS adaptation does not reproduce a circuit paper.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260922-21z | Document Phase 1 ldpc SDK coverage and unblock UAT | 2026-09-22 | 4581389 | — | [260922-21z-document-phase-1-ldpc-sdk-coverage-and-u](./quick/260922-21z-document-phase-1-ldpc-sdk-coverage-and-u/) |
| 260923-nbn | Repair Phase 2 GSD verification metadata | 2026-09-23 | 15a9e8a | — | [260923-nbn-repair-phase-2-gsd-verification-metadata](./quick/260923-nbn-repair-phase-2-gsd-verification-metadata/) |
| 260923-ui8 | Create a reproducible PDF documentation snapshot through completed Phase 2 from existing Markdown; preserve existing Markdown and do not advance Phase 3 | 2026-09-23 | 30df961 | — | [260923-ui8-create-a-reproducible-pdf-documentation-](./quick/260923-ui8-create-a-reproducible-pdf-documentation-/) |
| 260924-max | Record prospective quaternary memory-policy novelty in Markdown and reproducible PDF | 2026-09-24 | 2a83502 | — | [260924-max-record-prospective-quaternary-memory-pol](./quick/260924-max-record-prospective-quaternary-memory-pol/) |
| 260926-ps2 | Review Phase 4 gates, design Phase 5 interventions and document development since the last PDFs | 2026-09-26 | b684cab | Verified | [260926-ps2-review-pending-phase-4-gates-design-phas](./quick/260926-ps2-review-pending-phase-4-gates-design-phas/) |

## Deferred Items

No requested decoding regime or named policy family is deferred beyond the first journal milestone.

## Session Continuity

Last session: 2026-09-27T18:59:32Z
Stopped at: Plan 04-12 external job running; isolated eb16e22 fully verified; artifact head ce1c22d
Resume file: .planning/phases/04-memory-policies-and-relay-bp/.continue-here.md
Structured handoff: .planning/HANDOFF.json
Next command: $gsd-execute-phase 4 after reconciling the existing async job

Design continuation: `.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md`.
Latest execution report: `.planning/phases/04-memory-policies-and-relay-bp/04-EXECUTION-CONTINUATION-20260927-RESUMED.md`.
The September 26 development PDF remains a historical snapshot. Phase 4
completion and Phase 5 execution remain pending; no plan counts advanced.
