---
phase: 04-memory-policies-and-relay-bp
plan: "14"
status: preparatory_pending_production_evidence
workflow: gsd-execute-phase
date: 2026-09-27
---

# Notebook preparation while calibration runs

Independent Plan 04-14 preparation is in the existing isolated
`gsd/phase4-memory-integration-20260926` checkout. Its 13-section source notebook,
confined executor, identity/snapshot support and public guide are implemented.
The source notebook and all executed cells label fixture execution as
`development_fixture` / `not_assessed` and never start simulation.

Nine focused tests cover source/sample/cap/selection identity binding,
preservation of mismatched snapshots, predecessor gating before producer
invocation, payload and source drift, missing executable source/selection,
symlink/traversal confinement, unavailable evidence, complete sections and actual
cleared-output fixture execution, and rejection of a digest-valid index that
files a baseline identity under evaluation. Both fixture and availability notebooks execute
top-to-bottom with 14 code cells and 14 outputs. Availability mode retains all
13 absent qualified stages explicitly. Analysis versions match the qualified
primary checkout venv; the worktree executor derives this venv from git common
directory identity rather than accepting an arbitrary interpreter override.

The snapshot helpers check current referenced input bytes and complete executable
source coverage. Originating execution qualification remains a separate producer
obligation. They do not retroactively qualify earlier ordinary-memory executions
as memory evidence. Snapshot generation uses exclusive creation and cannot
replace an existing record. Arbitrary notebook Python is trusted project code;
path checks do not imply a code sandbox.

Remaining Plan 04-14 work: implement production campaign snapshot adapters and
complete quantitative tables/figures after terminal calibration, frozen selection,
fresh evaluation and factorial gates; inspect the rendered notebook visually.
No notebook viewer/HTML exporter was available during this preparation, so only
executed output structure and labels were inspected. Do not write the completion
SUMMARY or mark Plan 04-14/Phase 4 complete from these infrastructure checks.

The source notebook also validates its interpreter and pinned environment when
executed manually, and every section exposes fixture and assessment labels.
The focused command passed nine tests after these changes.

Final stable-source validation: the complete project regression suite passed
**478 tests, with one existing skip**, in 299.52 seconds. Both saved notebook
artifacts were refreshed from cleared outputs; each executed all 14 code cells
with 14 outputs and zero errors. This validates the scaffold and current source,
not the outstanding production analysis or rendered visual inspection.

The frozen V4 cap does not admit fresh shared-settings evaluation; a versioned
presampling cap amendment is still required for that planned view. Local-memory
schedule/lifetime coverage remains partial: layered/check-node/variable-node
PDBP and damping execute; other local operands/schedules and retained lifetimes
remain separate kernel gaps. These limitations
remain visible in the notebook and public guide.
