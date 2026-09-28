---
phase: 04-memory-policies-and-relay-bp
workflow: gsd-execute-phase
status: independent-progress-audit-verified-calibration-running
date: 2026-09-28
source_commit: 532324fc6dafff91a0c7edd22008afffc84a4f80
---

# Read-only progress audit while calibration continues

Phase 4 remains at 12/15 completed plans. Plan 04-12 is waiting on the original
calibration producer in Slurm allocation 55938300, PID 2702938. Plans 04-13/14
still depend on its terminal verification. No campaign source, caps, result,
allocation, sample namespace or selection was changed.

Commit `532324f` extends the isolated `scripts/verify_phase4_calibration.py`
with `--progress`. It checks exact cap bytes and plan/amendment identities,
frozen configuration and shot subsets, each retained terminal's public receipt,
deterministic sample identity, bounded work, completed configuration summaries
and reconstructed wall charge. An in-flight placeholder is reported without
claiming terminal verification or a current aggregate. The original strict
terminal mode is unchanged. Both modes return `selection_permitted: false`:
public ledger verification is a separate prerequisite.

At **2026-09-28T02:09:36Z**, the read-only audit of the live result passed with
digest `3d2a8df0cd08827bc3216292396fe67fccf04ecb8dc68c1c018c754449b688e0`:
**140/182 configurations observed**, **4466/5824 attempts retained (76.7%)**,
including **4013 completed** and **453 budget-exhausted**. The report scope is
`partial_surface_integrity_only`, producer status `running`, assessment
`not_assessed`, and selection not permitted. These are execution counts, not a
decoder-performance estimate. Evaluation namespaces remain untouched; no
`selected-settings.json`, fresh evaluation or factorial result exists.

The completed exact-author agreement diagnostic was independently reread by
`summarize_phase4_author_runtime(...)`: its result digest and all 384 individual
matched shots reconstruct. It retains 128 pairs per code. Exact-candidate
disagreements are 37/128 for B1, 16/128 for BB-144 and 65/128 for generated
HGP. This is a controlled CSS implementation agreement diagnostic, not an
evaluation of calibrated settings or source circuit-curve reproduction.
Separate lower-noise runs report `completed_precision`, but cannot replace the
prespecified calibration and fresh evaluation gates.

Verification: 23 progress/terminal-audit tests passed; the related
calibration/evaluation/notebook set passed 50 tests. The full isolated-branch
suite passed **562 tests, one pre-existing skip**, in 440.89 seconds with
`OMP_NUM_THREADS=1 PYTHONPATH=src` and the qualified main `.venv` interpreter.
The full-suite output is retained in
`04-PROGRESS-AUDIT-REGRESSION-20260927.log`. Main's campaign producer remains
frozen at the earlier source identity; this branch is not merged into it.

Resume by checking the existing async manifest and live result. When terminal,
run the strict surface audit and independently verify every public canonical
terminal before freezing settings or launching fresh evaluation. Any recovery
charge discrepancy must be documented against retained historical bytes rather
than silently repaired. No Plan 04-12/13/14 summary or Phase 4 completion claim
is justified yet.
