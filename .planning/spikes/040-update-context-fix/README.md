---
spike: 040
idea: canonical-kernel-audit
name: update-context-fix
type: standard
validates: "Close D01 with retained regressions"
verdict: VALIDATED
related: [034, 035, 036, 037]
tags: [fixes, completeness]
---

# D01 correction

Baseline 6f68961. Historical evidence is retained unchanged. Fixes execute D03 → D04 → D01 → D02 → D05.

Default dispatch is explicitly versioned `source-iteration-v2`. Standalone `BinarySpaKernel.run` and layered/check/variable local schedules now pass the completed source-traversal count, canonical check ID and canonical edge ID. Randomized traversal only changes order. Scalar and resolved graph assignments are unchanged. Indexed assignment exhaustion rolls back the local mutation and budget reservation.

Historical standalone/local replay is available with `BinarySpaKernel(..., update_context_version="legacy-zero-v1")`; it reproduces the previous implicit zero. Explicit flooding and AtomicFloodingExecutor already used correct indices and retain their original behavior under both modes. KernelResult and local schedule evidence identify the chosen context version. Numerical profile identifiers and public manifest schemas/defaults are unchanged. To reproduce historical complete evidence byte-for-byte, use the pinned baseline source 6f68961; old evidence is never rewritten or silently relabeled.

Hsu overlapping groups remain source-qualified plain SPA with existing numerical-profile selection. Direct unsupported update-rule compositions are now rejected before execution. Extending that separate source procedure requires its own numerical qualification.

Red: 23 failed / 2 passed. Green: 116 passed in 7.06s, including actual NMS/OMS arithmetic, every local schedule, shuffled context, resolved edge assignments, legacy replay, atomic denial/exhaustion, and public memory replay. Test environment: OMP_NUM_THREADS=1, NUMBA_NUM_THREADS=4. An initial expanded run omitted the manifest-required OMP setting; rerunning with the declared environment passed.

Full integration caught an overbroad first Hsu guard that rejected the existing v1 profile. The follow-up narrows rejection to update-rule overlays and explicitly preserves both historical and current plain-SPA construction. The failed integration receipt is retained under 042/initial-integration; guarded-route-green.log records the correction.
