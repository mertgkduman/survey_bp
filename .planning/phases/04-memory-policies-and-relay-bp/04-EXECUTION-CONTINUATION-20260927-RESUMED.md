---
phase: 04-memory-policies-and-relay-bp
workflow: gsd-execute-phase
status: independent-continuation-verified-calibration-waiting
date: 2026-09-27
source_commit: eb16e22
source_checkout: /hpc/group/pfisterlab/mg551/storage/survey_bp_memory_integration_20260926
---

# Resumed Phase 4 execution

Phase 4 remains at 12/15 completed plans. Plan 04-12 has a live external
calibration prerequisite; Plans 04-13 and 04-14 retain their scientific wave
dependencies. The main kernel, scripts, frozen caps and design remain unchanged
from `101a01b`. No job was relaunched, cancelled, merged or tuned from partial
results. Evaluation namespaces remain untouched.

The existing isolated checkout now contains these additional implemented slices:

- `3a3bb8c`: disordered affine-prior execution on layered, check-node serial and
  variable-node serial schedules. Each source-iteration assignment/history
  commits only with a complete traversal; denied or numerical-failure prefixes
  retain honest local work and discard uncommitted assignments. Public execution
  and replay use the same shot identity independently of tracing.
- `6747e90`, corrected in `a44f270`: terminal calibration surface audit over
  exact cap/plan/amendment identity, complete configuration/shot coverage,
  namespace/shot-derived samples, bounded work and reconstructed aggregates.
  Its verdict is `surface_integrity_only`; public ledger verification remains
  a separate prerequisite. Isolated recovery fixes preserve terminal identities
  and replace prior wall charges by delta rather than counting them twice.
- `eb16e22`: legacy selection freezing and shared preparation require the
  surface audit. A versioned, finite shared-settings supplement and manifest-only
  validation API preserve the legacy three-arm cap. Shared source/canonical
  views use matched samples and memory settings with distinct min-sum/SPA
  kernels. No supplemental amendment is published, allocation funded or fresh
  sample executed.

The bounded calibration review found three defects and independently rechecked
all three corrections in `a44f270`; no full-phase clean verdict is inferred.
The executor's branch-name guard prevented one worker from committing in the
pre-existing integration branch; the orchestrator retained that checkout and
committed its verified owned files. No new isolation protocol or branch rewrite
was introduced.

Focused verification: 22 local-memory tests; 21 calibration-audit tests; combined
calibration/evaluation gate 36 tests. Existing main evidence/evaluation gate:
40 passed, one pre-existing skip. Full regression on source `eb16e22` passed **560 tests, one pre-existing skip**,
in **454.56 seconds**, with `OMP_NUM_THREADS=1 PYTHONPATH=src` and the main
qualified interpreter. Source/scripts/tests remained unchanged throughout.
The retained log and scoped validation are in the isolated phase directory:
`04-CONTINUATION-REGRESSION-20260927.log` and
`04-RESUMED-CONTINUATION-VALIDATION.md`; artifact head **ce1c22d**.
These are implementation fixtures, not production performance evidence.

Latest calibration snapshot: **3846/5824 (66.0%)** retained attempts at
2026-09-27T18:59:32Z; status `running`, evaluation namespaces unaccessed. PID2702938 and
allocation55938300 were observed running. This is execution progress only.

## Remaining gates

1. Wait for terminal calibration, verify retained terminals and the complete
   surface, and freeze per-preset/shared settings from that evidence only.
   Inspect any historical recovery-accounting discrepancy; preserve original
   evidence and document requalification instead of rewriting history.
2. Release source isolation only after that gate. Integrate the verified source
   while preserving historical source/result identities.
3. Publish an appropriate finite shared-evaluation amendment under verified
   entitlement, then run the required fresh evaluation, native diagnostics,
   factorial and actual trace evidence. Preparation does not qualify those stages.
4. Populate the prepared notebook with verified production inputs, address
   retained-history/additional-lifetime, other local-schedule and Relay-trace
   gaps, and run remaining phase goal/code/security/validation gates. Refresh
   stale earlier verification reports without rerunning their completed plans.

The isolated scoped records are `04-LOCAL-DISORDERED-AFFINE-CONTINUATION.md`,
`04-CALIBRATION-SURFACE-AUDIT.md`, `04-CALIBRATION-AUDIT-REVIEW.md`, and
`04-13-SHARED-EVALUATION-PREPARATION.md` in its Phase 4 directory. The public
guide there is `docs/phase4-memory-relay.md`.

No Phase 4 completion summary, requirement-release verdict or Phase 5
advancement is produced while these prerequisites remain outstanding.
