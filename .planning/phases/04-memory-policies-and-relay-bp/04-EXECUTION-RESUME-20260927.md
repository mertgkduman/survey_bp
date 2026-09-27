---
phase: 04-memory-policies-and-relay-bp
workflow: gsd-execute-phase
status: prepared_external_job_waiting
date: 2026-09-27
---

# Phase 4 execution resumption

The manually invoked `$gsd-execute-phase 4` resumes Plan 04-12's external-job
reconciliation and independent prerequisite implementation for Plans 04-13/14.
No wave/evidence prerequisite was waived, no production sample was newly consumed,
and no completed-plan or phase count was advanced.

## Live external prerequisite

Calibration PID 2702938, allocation 55938300, remains active in the main
checkout with a nonterminal result. The original frozen cap/source and existing
async manifest remain authoritative. Do not relaunch, cancel, merge kernel
changes into this checkout, or select settings from its running partial result.

At 2026-09-27 03:14 UTC the partial result retained 2,228/5,824 attempts (38.3%):
1,775 completed and 453 budget-exhausted terminals. Its charged public-boundary
time was 104,739.31 seconds against the frozen 688,243-second cap. An earlier
2,022-attempt snapshot suggested roughly 52.5 hours remaining; this was a rough
extrapolation, not a stopping rule or guarantee. Exact counters change live.

Terminal benchmark, exact-author agreement and lower-noise jobs were reconciled
in commit `7459fc2`. See `04-12-RESUME-STATUS-20260927.md` for verified digests,
paired denominators, native import provenance and the retained failed monitor
status/replacement evidence. Auxiliary campaigns do not replace fresh evaluation.

## Isolated implementation

The existing branch `gsd/phase4-memory-integration-20260926` remains in
`/hpc/group/pfisterlab/mg551/storage/survey_bp_memory_integration_20260926`.
Final committed branch head: `639adef`; the isolated checkout is clean.

- `fc214ef`: public ordinary-memory V4 numerical execution and replay correction.
- `0986a0f` / `9e4c078`: confined, identity-aware 13-section notebook scaffold,
  fixture and availability execution, public research guide, strict stage/index
  binding and qualified interpreter/environment checks. Nine focused tests pass.
- `45a286e` / `5136b43`: ordinary disordered affine assignments,
  source-iteration NMS, full-history bounded observational traces and schema/
  remediation updates. Focused checks: 35 execution/trace tests plus two schema
  checks passed.
- `e90037b`: bounded layered/check-node/variable-node local PDBP and V2C damping,
  complete fresh beliefs, affected fresh V2C operands and atomic local commits.
- `3743d35`: public flooding-memory trace links; shot-specific decoder RNG
  identities independent of tracing; ordinary V3 NMS/OMS iteration dispatch,
  replay and early assignment admission; exact two-array memory-work counts.
  Ten focused checks pass. Historical affected evidence needs requalification.
- `fb44898` / `da341f6` / `8e2e52c`: corrected finite factorial preparation,
  five diagnostic proposal cells, separate command failures, matched observed
  samples, outcome-independent operand-order supplement and public trace index.
  `2a00572` adds shared per-cell/category deadlines, aggregate per-code trace
  quotas, actual elapsed time, fail-closed terminal-calibration/evaluation
  provenance and truthful incomplete status. Nine focused checks pass.
  No production factorial result is asserted.

The interim correction review found four blockers (RNG identity, iteration
assignment, notebook stage attribution and memory-work counts); its bounded
recheck in `cdd82b4` confirms all four resolved. This is not a full-phase gate.
The full isolated regression suite passed **478 tests, with one existing skip**,
in **299.52 seconds** against stable implementation `2a00572` (review document
`cdd82b4`). Command: `OMP_NUM_THREADS=1 PYTHONPATH=src` with the primary checkout's
qualified `.venv/bin/python -m pytest -q`. These are implementation fixtures,
not sampled production performance evidence.

Both refreshed notebook artifacts execute all 14 code cells with 14 outputs
and zero errors. Fixture output is explicitly `development_fixture/not_assessed`;
availability output preserves all 13 missing qualified production snapshots.

The notebook's fixture mode verifies plumbing only. Availability mode reports
all 13 qualified production snapshots as unavailable. Production adapters,
quantitative tables/figures and rendered visual inspection remain unfinished.
The snapshot helper does not qualify old ordinary-memory executions as memory
evidence merely by hashing them.

## Preserved completion gates

1. Verify terminal calibration and deterministically freeze settings.
2. Resolve fresh shared-setting evaluation admission with a versioned
   presampling cap amendment; current evaluation caps admit three arms only.
   The independently frozen factorial category already admits its 14 arms and
   does not require evaluation of those arms as a new predecessor condition.
3. Integrate the isolated correction once the live source can safely be released;
   preserve old ordinary-memory ledgers as their actual historical execution.
4. Complete and verify fresh evaluation, focused factorial, public linked
   traces, local/lifetime coverage and the production notebook evidence.
5. Run the remaining phase quality/goal gates before closing any incomplete
   plan or advancing the roadmap. Phase 5 preparation does not authorize
   skipping Phase 4 scientific prerequisites.

Plans 04-12/13/14 remain incomplete. No completion SUMMARY is generated while
their production evidence and external prerequisite are outstanding.
