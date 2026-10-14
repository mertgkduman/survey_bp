---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: 11
current_phase_name: Quaternary Reproduction and Comparisons
current_plan: 12
status: executing
stopped_at: Completed 11-11-PLAN.md
last_updated: "2026-10-14T22:53:40.627Z"
last_activity: 2026-10-14
last_activity_desc: Phase 11 execution started
state_head: 9c1be3105bdcd0329ba75271f417d00b17ba8bc7
progress:
  total_phases: 14
  completed_phases: 8
  total_plans: 166
  completed_plans: 153
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-12)

**Core value:** Make BP decoder differences explicit, reproducible, and fairly comparable through canonical policy execution and published evidence.
**Current focus:** Phase 11 — Quaternary Reproduction and Comparisons

## Current Position

Phase: 11 (Quaternary Reproduction and Comparisons) — EXECUTING
Plan: 12 of 15
Total Phases: 14
Current Plan: 12
Total Plans in Phase: 15
Status: Ready to execute
Last activity: 2026-10-14 — Phase 11 execution started
Last Activity Description: Phase 11 execution started

Progress: 8 of 14 phases complete (57%); Phase 9 has 20 of 20 plans complete

## Performance Metrics

- Total plans completed: 143
- Average duration: N/A
- Total execution time: 0 hours
- Recent trend: Phase 9 completed 20 bounded CSS plans and passed goal, code, security, and validation gates; source-faithful EVAL-01/02 evidence remains pending.

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
| Phase 04 P12 | 4d | 2 tasks | 2 files |
| Phase 04 P13 | 2026-09-30 | 2 tasks | 4 files |
| Phase 05 P01 | 15min | 1 tasks | 5 files |
| Phase 05 P02 | 8min | 2 tasks | 6 files |
| Phase 05 P03 | 8min | 2 tasks | 7 files |
| Phase 05 P04 | 12min | 2 tasks | 2 files |
| Phase 05 P05 | 10min | 2 tasks | 2 files |
| Phase 05 P06 | 18min | 3 tasks | 3 files |
| Phase 05 P07 | 12min | 2 tasks | 2 files |
| Phase 06 P01 | 14m | 2 tasks | 5 files |
| Phase 10-correlated-quaternary-execution P01 | 482 seconds | 1 tasks | 7 files |
| Phase 10-correlated-quaternary-execution P02 | 10m | 2 tasks | 4 files |
| Phase 10-correlated-quaternary-execution P13 | 7m | 2 tasks | 3 files |
| Phase 10 P03 | 4m | 1 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P04 | 8m 14s | 2 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P05 | 8m 10s | 2 tasks | 4 files |
| Phase 10 P06 | 10m 14s | 2 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P07 | 33m | 2 tasks | 5 files |
| Phase 10 P08 | 7m | 2 tasks | 6 files |
| Phase 10-correlated-quaternary-execution P09 | 7m | 2 tasks | 6 files |
| Phase 10 P10 | 12m | 2 tasks | 4 files |
| Phase 10 P11 | 11m | 1 tasks | 4 files |
| Phase 10 P12 | 10m | 2 tasks | 7 files |
| Phase 10 P15 | 22m | 2 tasks | 5 files |
| Phase 10 P16 | 3h 23m bounded run plus verification | 2 tasks | 8 files |
| Phase 11 P01 | 3m 27s | 2 tasks | 6 files |
| Phase 11-quaternary-reproduction-and-comparisons P07 | 322s | 2 tasks | 3 files |
| Phase 11 P02 | 12m | 2 tasks | 8 files |
| Phase 11-quaternary-reproduction-and-comparisons P04 | 17m | 2 tasks | 4 files |
| Phase 11 P08 | 8m 38s | 2 tasks | 4 files |
| Phase 11 P03 | 11m | 2 tasks | 5 files |
| Phase 11 P09 | 34m | 2 tasks | 5 files |
| Phase 11 P10 | 31m | 3 tasks | 8 files |
| Phase 11-quaternary-reproduction-and-comparisons P05 | 4m | 1 tasks | 1 files |
| Phase 11 P11 | 1028s | 2 tasks | 4 files |

Phase 02 P10–P16 gap-closure metrics are recorded in their individual summaries.

## Accumulated Context

### Decisions

Full decisions are in PROJECT.md; workflow choices are in config.json.

- First journal milestone includes CSS code-capacity → correlated quaternary code-capacity → circuit level; none is deferred beyond the paper.
- Canonical engines are defined per compatible kernel family. BP modifications are primary; OSD/LSD is optional additional processing for nonconvergence.
- Reproduction requires declared statistical agreement, not bitwise identity; source semantics and outcome correctness require separate checks.
- Preserve faithful source configurations and controlled shared-sample/work-budget comparisons as separate evaluation views.
- [Phase 08]: Paired canonical CSS campaigns freeze one physical sample for both arms, verify local and direct selected-shard deliveries independently, and report exact denominator uncertainty and merge provenance.
- [Phase 08]: The two-sample BB-144 run is development evidence only; site ceilings and scheduler accounting are unavailable, so production authorization remains denied.
- [Phase 09]: The 14-variant CSS inventory and capped Yao B1 run preserve unavailable source/native facts; EVAL-01/02 remain pending, and timeout terminals never become a paper-rate estimate.
- [Phase 09]: Three prospectively frozen matched controls completed at N=3, 16, and 2 with separate profiles, typed shared-work costs, and no decoder-superiority claim.
- [Phase 09]: Public controlled retry reuses sealed initial/member receipts and recovers orphaned sealed units into merge envelopes; publication Slurm stays denied without site limits.
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
- [Phase 04]: Phase 04 Plan 12: terminal Relay-ledger verification releases BB-144/HGP selections while B1 remains inconclusive under the frozen cap.
- [Phase 04]: Phase 04 Plan 12: async calibration manifest reconciled from terminal evidence without campaign relaunch or result rewrites.
- [Phase 6]: Phase 06: executable policy identity excludes source prose while immutable request receipts retain provenance and raw TOML identity.
- [Phase 6]: The three-paper B1 gate verified the common policy-file command and portable cache for one Yao, Bhatnagar, and Rabeti adaptation; two p=0.000001 shots per policy are not a performance or source-curve assessment.
- [Phase 6]: Coordinate-majority voting is an importable, independently checked kernel primitive; CAN-02 public TOML execution and replay are assigned to Phase 9.
- [Phase 6]: Phase 5 human visual review remains open while Phase 7 planning proceeds, as directed by the user. Continue CSS paper intake and bounded pilots alongside Phase 7; Phase 8 owns campaign statistics and throughput profiling.
- [Phase 10]: Phase 10 Plan 01: Persist Pauli values as I=0, X=1, Y=2, Z=3 and sample each qubit from one categorical joint channel.
- [Phase 10]: Phase 10 Plan 01: Separate decoder smoothing from physical channel probabilities and expose unavailable logical action without a declared non-CSS basis.
- [Phase 10]: Phase 10: Persisted Pauli labels use I=0, X=1, Y=2, Z=3 with fixed symplectic pairs and owned read-only arrays.
- [Phase 10]: Phase 10: CSS compilation persists X rows then Z rows, giving [s_X,s_Z]=[H_x z,H_z x], with roles, row indices, logical availability, and source identity in semantic bytes.
- [Phase 10]: Phase 10: Derived quaternary working graphs require explicit transform and lift witnesses; identity edges cannot change graph or syndrome.
- [Phase 10]: Native aSCED source is fixed to kit-cel/quantum_asced commit 816772071486615dfc7d71d1e15df597edc58a26; the exact digest was approved, and the bounded isolated build and native run succeeded.
- [Phase 10]: Phase 10 Plan 03: evaluator-local symplectic and GF(2) routines are the authority for four-outcome Pauli classification.
- [Phase 10]: Phase 10 Plan 03: logical residual actions use immutable (x, z) coordinates, while absent bases yield explicit unavailable reasons.
- [Phase 10]: Phase 10 Plan 04: physical I/X/Y/Z rows remain unchanged after strict validation, while decoder smoothing is separately identified.
- [Phase 10]: Phase 10 Plan 04: inverse-CDF ties use decimal persisted-value thresholds with stable I<X<Y<Z ownership.
- [Phase 10]: Phase 10: quaternary-bp4-f64-v1 freezes float64 identity-referenced LLRs with symmetric +/-25 saturation and requires vector/exact oracle qualification before public evidence.
- [Phase 10]: Phase 10: canonical scalar BP4 retains I/X/Y/Z node beliefs and uses scalar commutation messages only on edges.
- [Phase 10]: Phase 10 Plan 06: Flooding retains a whole old V2C snapshot while serial makes each declared variable update visible to later variables.
- [Phase 10]: Phase 10 Plan 06: Normalization and offset are closed finite-positive transforms applied only to scalar C2V messages.
- [Phase 10]: Phase 10 Plan 07: component source fidelity is persisted separately from run fidelity; continued-message Q-BPGD runs are canonical adaptations.
- [Phase 10]: Phase 10 Plan 07: quaternary_experiment_v2 is additive; V1 tracer parsing and replay semantics remain stable.
- [Phase 10]: Q-BPGD records source-backed setup components separately from the D-14 continued-message canonical-adaptation run.
- [Phase 10]: Q-BPGD preserves raw literal fixation weights and records common-sum normalized decoder priors for replay.
- [Phase 10]: Phase 10 Plan 09: fixed-alpha MBP4 scales only posterior anticommuting sums; destination-edge inhibition remains unscaled.
- [Phase 10]: Phase 10 Plan 09: non-source-defined MBP4 transform combinations remain canonical_adaptation despite source-backed components.
- [Phase 10]: GB46 H is a pinned source input; deterministic T and H_ext are project-generated canonical_adaptation evidence.
- [Phase 10]: The extended aSCED factor graph retains immutable-original transform/lift lineage without claiming its noncommuting splitter rows are a stabilizer code.
- [Phase 10]: Phase 10 Plan 11: canonical GB46 M retains identity rows and appends deterministic X/Z pair images under a 1000-pair cap.
- [Phase 10]: Phase 10 Plan 11: typed [s_X,g_X,s_Z,g_Z] assembly and comparison-only source maps prevent block or source-map substitution.
- [Phase 10]: Phase 10 Plan 11: canonical overcomplete construction accepts only a reverified QualifiedAscedBatch, closing standalone receipt spoofing.
- [Phase 10]: aSCED executes every declared CSS virtual path in LSB order and selects only original-syndrome-valid minimum-weight candidates with stable batch/path ties.
- [Phase 10]: Canonical aSCED runs bind verified constructed splitter and overcomplete receipts and remain canonical_adaptation even when paper components are source-backed.
- [Phase 10]: Phase 10 Plan 15: isolated native aSCED aggregate evidence remains distinct from canonical execution and retains unavailable native instrumentation.
- [Phase 10]: Retained the 256-shot GB46 p=0.05 seed-10 all-path ledger as canonical_adaptation mechanism evidence; native 160/10 remains aggregate-only with unavailable matched-shot identity.
- [Phase 10]: Full 256-shot decoder replay exited 0 and byte-matched all retained events; the bounded mechanism evidence remains `not_assessed` for curve reproduction or ranking.
- [Phase 11]: Figure 2 GB46 aSCED targets remain blocked_metadata until reviewed digitization and native execution evidence exist.
- [Phase 11]: Ordinary and overcomplete aSCED source members remain separately receipted; canonical adaptation fidelity is not promoted by target agreement.
- [Phase 11]: D-05 binary callbacks receive only component priors, syndromes, and arm-neutral identities.
- [Phase 11]: D-08 maps retained separate-arm nonconvergence to all-shot failure without dropping paired evidence.
- [Phase 11]: A5 reconstructs from the published l=90 polynomial pair while its distance interval remains source reported.
- [Phase 11]: Figure 7 source settings remain frozen; the one-sweep canonical-adaptation probe cannot assess the Figure 7 curve.
- [Phase 11]: A5 reconstructs from the published l=90 polynomial pair while its distance interval remains source reported.
- [Phase 11]: Figure 7 source settings remain frozen; the one-sweep canonical-adaptation probe cannot assess the Figure 7 curve.
- [Phase 11]: Phase 11: pinned native aSCED aggregate evidence is not matched-shot evidence; a proposed injected-input derivative stays unapplied until rights and semantic review approve a separate identity.
- [Phase 11]: D-12 reports D_y first across three fixed-marginal channel rows with simultaneous six-arm exact bounds.
- [Phase 11]: Phase 11 paired precision is frozen from a pilot identity, two-contrast alpha family, fixed stopping rule, and 5,000-pair cap.
- [Phase 11]: Phase 11 Plan 03: Treat the MBP4 Figures 8-9 five-qubit alpha contrast as finite deterministic mechanism evidence; Figure 6 remains blocked without statistical metadata.
- [Phase 11]: Pinned the GB46 source check bytes and kept all controlled calibration receipts in the canonical-adaptation lane with publication authorization deny.
- [Phase 11]: Used one sealed Pauli sample for the scalar four-state joint arm and canonical binary SPA marginal arms, with independent evaluation after both arms finish.
- [Phase 11]: BB72 calibration retains source-reported distance 6 and project-derived logical qualifications; neither becomes a platform verification claim.
- [Phase 11]: Joint BP4 and separate binary arms report native named work beside callback-wall runtime without cross-unit conversion.
- [Phase 11]: The Phase 11 package is immutable deny-only: missing site capacity, accounting, quota/cost, source eligibility, or persisted profiles prevents a dispatch token.
- [Phase 11]: User selected preserve_unavailable for the verified Phase 11 aSCED derivative patch dd8a31965372ba8aa736134d71c66183c1d044b5ae6910dee48068e04cec2229; native matched-input evidence remains unavailable and canonical work continues.
- [Phase 11]: Preserved deny for all four Phase 11 publication campaigns after verified missing site ceilings, account/partition, quota/cost, persisted runtime profiles, and source-route eligibility.
- [Phase 11]: Sealed the human-reviewed denial against package semantic SHA-256 4f53f8ce6af2961831830105dde34b4050632751960c9e8c475e9cc7ac16334a with no dispatch token.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- [Phase 09] Exact author experiment artifacts, source settings, and executable native assessments are still unverified; EVAL-01/02 remain pending. The Yao B1 adaptation is cap censored. Site resource ceilings and scheduler accounting remain unavailable, so publication dispatch is denied.

- Current: Phase 4 passed goal verification (4/4 revised criteria; 6/6 requirements), validation and ASVS L1 security. The user stopped the oversized comprehensive experiment; its terminal manifest disables resume. B1 selection remains inconclusive, and the 159 completed plus one interrupted B1 records are receipts without a qualified performance denominator. Fresh evaluation, native-pair and factorial results remain absent. Phase 5 has 14 implemented and technically verified plans; human notebook/HTML review remains open. See the [cancellation record](phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md) and `04-VERIFICATION.md`. Entries below are historical checkpoints, not live progress.

- New-chat progress audit: calibration running with 3,716/5,824 retained attempts (63.8%) at 2026-09-27T17:20:42.542Z. See `.planning/HANDOFF.json` for the measured snapshot and async resume context. Phase 1/2 verification reports are now flagged stale by GSD and need refreshing; Phase 3 remains passed. No completed plans were rerun or removed.
- Phase 4 calibration remains `running` (PID 2702938); Plans 04-12/13/14 remain incomplete. Independent local PD-prime/momentum/affine execution, semantic failure-prefix traces, exact-byte terminal readers, immutable shot contexts and notebook views are verified in isolated source `62fe977`: 532 tests passed, one existing skip. Both notebooks execute all 14 cells without errors. The completed benchmark summary retains a real incomplete B1 p=.07 arm, so its rows remain explicitly unqualified. Fresh production evidence, retained histories/additional lifetimes, other local schedules, disordered local affine and Relay traces remain. Keep source changes separate from the live campaign. See [implementation continuation](phases/04-memory-policies-and-relay-bp/04-IMPLEMENTATION-CONTINUATION-20260927.md) and [coding handoff](phases/04-memory-policies-and-relay-bp/04-CODING-RESUME-HANDOFF.md).
- Phase 3 passed goal verification with 17/17 plans and all eight requirements complete. The Hsu source-defined group schedule has a retained, independently verified two-shot CSS pilot. The Moradi artifact remains unavailable and is not conflated with the Hsu policy.

Phase 2 is complete (16/16 plans; 5/5 goal criteria; clean review; 46/46 security threats closed). Remaining research concerns for later phases:

- Original BPGD/impulse code identities remain unverified; exact SI/OTF variants and generic mixing/memory/voting definitions need source specifications.
- Statistical targets and compute budgets for publication campaigns remain to be prespecified.
- Phase 11 must prespecify its quaternary comparison and statistical assessment; Phase 10 mechanism evidence and the native aggregate do not establish source-curve agreement or matched-shot performance.
- The observed development environment is node-specific; recheck package and backend identity before interpreting runs elsewhere.
- Circuit fault correlations and observable semantics require dedicated qualification; a CSS adaptation does not reproduce a circuit paper.
- Phase 07 POST-01 / Plan 07-03: approved standalone OSD commit builds in isolation but does not expose complete higher-order candidate solutions and scores; qualification receipt is failed/non-runnable. The user paused postprocessing, so no OSD source patch or reduced evidence contract is being pursued now.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 261012-kia | Defer Phase 5 human review and route to Phase 11 planning | 2026-10-12 | — | Verified | [261012-kia-defer-phase-5-human-review-and-route-to-](./quick/261012-kia-defer-phase-5-human-review-and-route-to-/) |
| 261005-le8 | Capture first three-paper CSS literature gate and source specs | 2026-10-05 | a6526e8 | Verified and published | [261005-le8-capture-three-paper-css-literature-gate-](./quick/261005-le8-capture-three-paper-css-literature-gate-/) |
| 261005-kkp | Place decoder TOML in paper folder and reproduction details below it | 2026-10-05 | 1ad21ba | Verified | [261005-kkp-place-decoder-toml-beside-paper-folder-a](./quick/261005-kkp-place-decoder-toml-beside-paper-folder-a/) |
| 261005-kcm | Scaffold literature policy registry and source status contract | 2026-10-05 | 660bdd8 | Verified | [261005-kcm-scaffold-literature-policy-registry-and-](./quick/261005-kcm-scaffold-literature-policy-registry-and-/) |
| 261005-jlz | Add importable policy-file study command with verified cache reuse | 2026-10-05 | 1f8b1c3 | Verified | [261005-jlz-add-importable-policy-file-study-command](./quick/261005-jlz-add-importable-policy-file-study-command/) |
| 261005-fze | Run matched BB72 BeamSearch/RelayBP parameter and evaluation campaign | 2026-10-05 | 3db441e | Verified and published | [261005-fze-run-matched-bb72-beamsearch-relaybp-para](./quick/261005-fze-run-matched-bb72-beamsearch-relaybp-para/) |
| 261005-2b9 | Merge fair damped BeamSearch/RelayBP after BB72 BP-SF v2 publication | 2026-10-05 | b84071e | Verified and published | [261005-2b9-merge-verified-fair-damped-beamsearch-re](./quick/261005-2b9-merge-verified-fair-damped-beamsearch-re/) |
| 261004-krc | Implement fair initial BP with damped BeamSearch branches and RelayBP memory legs | 2026-10-04 | 4955bff | Verified development implementation | [261004-krc-implement-fair-initial-bp-plus-damped-re](./quick/261004-krc-implement-fair-initial-bp-plus-damped-re/) |
| 261003-s2b | Prespecify, run, and publish the BB72 CSS BP comparison | 2026-10-04 | a23899c | Verified | [261003-s2b-prespecify-and-prepare-bb72-css-bp-decod](./quick/261003-s2b-prespecify-and-prepare-bb72-css-bp-decod/) |
| 261002-mjc | Parallelize Phase 5 v2 arm verification before publication | 2026-10-02 | b26d0c2 | Verified | [261002-mjc-parallelize-phase-5-v2-arm-verification-](./quick/261002-mjc-parallelize-phase-5-v2-arm-verification-/) |
| 261002-ldj | Pin and validate Bravyi BB72 CSS fixture | 2026-10-02 | 60679e4 | Verified | [261002-ldj-pin-and-validate-bravyi-bb72-css-fixture](./quick/261002-ldj-pin-and-validate-bravyi-bb72-css-fixture/) |
| 260922-21z | Document Phase 1 ldpc SDK coverage and unblock UAT | 2026-09-22 | 4581389 | — | [260922-21z-document-phase-1-ldpc-sdk-coverage-and-u](./quick/260922-21z-document-phase-1-ldpc-sdk-coverage-and-u/) |
| 260923-nbn | Repair Phase 2 GSD verification metadata | 2026-09-23 | 15a9e8a | — | [260923-nbn-repair-phase-2-gsd-verification-metadata](./quick/260923-nbn-repair-phase-2-gsd-verification-metadata/) |
| 260923-ui8 | Create a reproducible PDF documentation snapshot through completed Phase 2 from existing Markdown; preserve existing Markdown and do not advance Phase 3 | 2026-09-23 | 30df961 | — | [260923-ui8-create-a-reproducible-pdf-documentation-](./quick/260923-ui8-create-a-reproducible-pdf-documentation-/) |
| 260924-max | Record prospective quaternary memory-policy novelty in Markdown and reproducible PDF | 2026-09-24 | 2a83502 | — | [260924-max-record-prospective-quaternary-memory-pol](./quick/260924-max-record-prospective-quaternary-memory-pol/) |
| 260926-ps2 | Review Phase 4 gates, design Phase 5 interventions and document development since the last PDFs | 2026-09-26 | b684cab | Verified | [260926-ps2-review-pending-phase-4-gates-design-phas](./quick/260926-ps2-review-pending-phase-4-gates-design-phas/) |
| 260927-p0f | Add project README and push main plus isolated Phase 4 branch to GitHub | 2026-09-27 | 5a6377a | Verified | [260927-p0f-add-a-project-readme-and-push-to-git-git](./quick/260927-p0f-add-a-project-readme-and-push-to-git-git/) |
| 260929-qaa | Publish a verified 29 September development update in Markdown and PDF to GitHub | 2026-09-29 | 640b9c1 | Verified | [260929-qaa-publish-a-verified-29-september-developm](./quick/260929-qaa-publish-a-verified-29-september-developm/) |
| 260930-0vq | Stop Phase 4 comprehensive experiment and right-size plans | 2026-09-30 | db99a51 | Verified | [260930-0vq-stop-phase-4-comprehensive-experiment-an](./quick/260930-0vq-stop-phase-4-comprehensive-experiment-an/) |
| 260930-nuv | Create a source-backed study-design glossary in Markdown and color-coded PDF, then commit and push to GitHub | 2026-09-30 | 6ddf013 | Verified | [260930-nuv-create-a-source-backed-study-design-glos](./quick/260930-nuv-create-a-source-backed-study-design-glos/) |

### Roadmap Evolution

- Phase 10 reordered: User selected quaternary BP next: Phase 10 now depends on verified Phase 6 CSS foundation; Phase 8 can proceed independently of paused Phase 7, Phase 11 requires both Phase 8 statistical controls and Phase 10 engine, and optional fallback comparisons remain conditional on qualification.

## Deferred Items

No requested decoding regime or named policy family is deferred beyond the first journal milestone. The user deferred Phase 5's pending human notebook/HTML review while moving to Phase 11; Phase 5 is not marked complete. Phase 7 remains paused. The cancelled comprehensive Phase 4 CSS evaluation/factorial is deferred from Phase 4; Phase 8 supplied bounded campaign infrastructure and Phase 9 completed exploratory CSS controls. Source-faithful CSS publication assessments remain pending exact author evidence. Relay circuit-curve assessment remains in Phase 13.

## Session Continuity

**Resume file:** None

Last session: 2026-10-14T22:53:28.854Z
Stopped at: Completed 11-11-PLAN.md
Next command: $gsd-execute-phase 11; Phase 5 human review remains open and Phase 7 stays paused.

Design continuation: `.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md`.
Latest execution report: `.planning/phases/04-memory-policies-and-relay-bp/04-EXECUTION-CONTINUATION-20260927-RESUMED.md`.
Latest isolated terminal ledger audit: `gsd/phase4-memory-integration-20260926` at `263501e`, `.planning/phases/04-memory-policies-and-relay-bp/04-CALIBRATION-LEDGER-AUDIT-PREPARATION.md` in that branch.
The September 26 development PDF remains a historical snapshot. The September 29 update records the terminal calibration. Phase 4 is complete under the revised scope; Phase 5 implementation passed technical verification and awaits the human notebook/HTML review. The comprehensive production campaign was cancelled by the user and is no longer a Phase 4 gate.
