---
phase: 04-memory-policies-and-relay-bp
date: 2026-09-26
status: coding-resumed-calibration-active
workflow: gsd-execute-phase
implementation_commit: fc214ef
implementation_branch: gsd/phase4-memory-integration-20260926
---

# Phase 4 coding continuation

The user requested coding continuation while the simulations run. Plan 04-13's
ablation runner exposed a prerequisite bug: ordinary-memory V4 manifests were
validated but projected to V3 without their memory bindings, executing plain
BP. Corrective code is committed as **fc214ef** in an isolated worktree:

`/hpc/group/pfisterlab/mg551/storage/survey_bp_memory_integration_20260926`

Branch: `gsd/phase4-memory-integration-20260926`, based on main commit `101a01b`.
Its detailed record is
`.planning/phases/04-memory-policies-and-relay-bp/04-MEMORY-INTEGRATION-REMEDIATION.md`.

## Implemented

Public memory-only V4 now dispatches compact V5 and executes all five ordinary
memory kinds at flooding boundaries. It commits private histories with whole
admitted sweeps, records their digests and separate memory work, retains failed
run diagnostic candidates, and reconstructs these claims in public semantic
verification. Momentum parameters are explicit alpha/gamma. Repeated binding
histories, budget/numerical rollback, reset isolation, min-sum dispatch and
source-iteration OMS are tested.

Verification: regression suite **356 passed, 1 existing skip**, followed by the
final memory/manifest gate **67 passed**. The generated V4 schema is unchanged
in JSON shape. These fixtures are implementation evidence, not performance
measurements or newly consumed campaign shots.

## Preserve the active campaign

At 2026-09-26 20:12 UTC, calibration PID **2702938** was active after about
23 h 13 min. It uses the main checkout's `run_phase4_pilots.py` and public CLI
source. Keep implementation changes isolated until campaign source identities
are safely finalized. This handoff changes planning files only in main.

The correction does not affect live Relay runs, which use the separate V4
Relay projection. Older ordinary-memory V4 ledgers retain their historical
meaning as plain-BP executions; they cannot support memory-effect claims.

## Next coding actions

1. Continue in the isolated worktree while calibration remains active. Add the
   focused ablation runner with matched sample identities, finite caps, all
   five diagnostic outcome cells, and candidate origins.
2. Before sampling, record outcome-independent coefficients and resolve a
   documented design discrepancy: frozen interaction arrays list damping or
   momentum before affine prior, while the executable operand dependency is
   prior -> fields -> V2C. Use a versioned execution supplement/amendment and
   retain the frozen original design and caps.
3. Implement bounded trace hooks and the ordinary disordered-affine assignment
   path needed by Plan 04-13. Local memory schedules, retained histories,
   additional lifetimes and per-iteration NMS remain explicit execution gaps.
4. Reconcile terminal calibration and freeze selected settings before fresh
   evaluation/native pairing. Existing `run_phase4_evaluation.py` provides the
   guarded execution path. Merge the isolated correction once source identity
   preservation permits it, then run final Phase 4 gates.

Phase 4 and Plan 04-13 remain incomplete. Do not advance the roadmap to
quaternary or circuit execution from this implementation correction.
