# Plan review and next design work

Snapshot: 26 September 2026. Active execution remains Phase 4, Plan 12.

## What the plans require

The roadmap records Phases 1–3 complete and 12 of 15 Phase 4 plan summaries.
The remaining work is correctly sequenced: terminal calibration and selection
(04-12), fresh evaluation plus memory/Relay ablations and traces (04-13), then
the executable notebook and public research guide (04-14). Completed low-noise
estimation and native diagnostics are separate evidence; they do not close
these three plans.

| Plan or prerequisite | Current evidence | Remaining gate |
| --- | --- | --- |
| 04-12 calibration | Running, evaluation namespace untouched | Terminal reconstruction and frozen selections |
| Ordinary-memory execution | Corrected in isolated commit fc214ef | Integrate after preserving campaign source identity |
| 04-13 selected evaluation | Guarded runner exists, commit 43dafb5 | Terminal selection, admitted views and fresh sampling |
| 04-13 factorial | Frozen design; corrected flooding primitives | Versioned order supplement, runner, missing bindings and traces |
| 04-14 notebook | Planned sections and identity rules | Implement and execute against completed upstream evidence |
| Phase 5 | Preparatory contracts and algebra checks in this update | Source resolution and Phase 4 completion before phase execution |

## Findings that change the next steps

**A validated memory binding did not guarantee executed memory.** The main
V4 ordinary-memory path projected to V3 and dropped memory bindings. The
isolated correction uses the full compact V5 dispatch. Older ordinary-memory
ledgers remain plain-BP executions and cannot demonstrate a memory effect.
The separate Relay path is unaffected. See
`.planning/phases/04-memory-policies-and-relay-bp/04-CODING-RESUME-HANDOFF.md`.

**The correction has a defined scope.** It executes all five ordinary memory
families at flooding boundaries, commits histories atomically, retains
diagnostic candidates and verifies their semantics. It does not complete
local memory schedules, additional history lifetimes, retained history across
legs, the ordinary disordered-affine assignment path or per-iteration NMS.
Scalar/graph NMS and per-iteration OMS are covered. An unsupported binding must
be rejected explicitly rather than silently simplified.

**The factorial order needs an outcome-independent supplement.** The frozen
interaction arrays put damping or momentum before affine-prior memory. The
executable operand dependency is prior -> belief/posterior -> V2C. Preserve
the frozen design and caps; add a versioned execution interpretation, explicit
coefficients and stable binding order before sampling. The design cannot be
changed in response to favorable outcomes.

**Shared settings are not automatically an admitted evaluation arm.** The
runner guards terminal calibration, cap hashes and source pins, but an
additional shared-settings view needs an explicit caps/design amendment.
Report per-preset reproduction-oriented views separately from controlled
settings. Native comparisons must name the Rust reference and its translation.

**Plan coverage is a promise of future evidence.** The coverage table in
04-14 describes its intended implementation. It is not an execution audit.
The skipped notebook identity test in `test_phase4_evidence.py` is still a
placeholder; its old B1-digest explanation is stale after reconciliation.
Replace it with executable stage-reuse checks when the notebook exists.

**Ledger transformation slots are not an executable transformed problem.**
`canonical/lineage.py` already names transformations and lifts, but
`canonical/problems.py` accepts only identity `WorkingProblem` graphs and
syndromes. Phase 5 needs a typed transformation contract and independent
original-problem validation before interventions can run.

## Work that can proceed while results are pending

The following work depends on contracts and sources, not measured LER:

1. Define immutable working views, fixation maps and certified candidate lifts.
2. Specify BP round continuation, prior-vector changes and cache invalidation.
3. Resolve source variants and native-code availability for BPGD and impulse.
4. Specify rollback, restart streams, work reservation and original validation.
5. Prepare deterministic algebra fixtures and future implementation acceptance
   checks. The exhaustive shortening checks delivered here are design evidence.
6. Design equal-boundary runtime collection and honest missing instrumentation.

The detailed proposal is
`.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN.md`;
bounded next tasks are in `05-DESIGN-TASKS.md`. These documents do not mark
Phase 5 implemented or relax the Phase 4 dependency.

## Execution order after this update

Keep the active campaign's code identity stable. Continue Phase 4 coding in
the isolated correction worktree, finish the ablation/trace prerequisites,
then reconcile terminal calibration and freeze settings. Run admitted fresh
evaluation and native pairs, complete the notebook and verification gates,
and then turn the Phase 5 design into checked execution plans. Preserve
failed, incomplete and inconclusive evidence throughout.

Quaternary execution remains in Phases 10–11 and circuit execution in 12–13.
Their inclusion in the journal milestone is unchanged. A prospective research
idea recorded in the earlier novelty PDF is not implementation evidence.
