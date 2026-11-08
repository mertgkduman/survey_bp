---
spike: 042
idea: canonical-kernel-audit
name: batch-evidence-fix
type: standard
validates: "Close D05 with retained regressions"
verdict: VALIDATED
related: [034, 035, 036, 037]
tags: [fixes, completeness]
---

# D05 correction

Baseline 6f68961. Historical evidence is retained unchanged. Fixes execute D03 → D04 → D01 → D02 → D05.

CpuBatchResult validates structure and owns immutable candidate/iteration/convergence/syndrome buffers on every construction path. Version `numba-cpu-batch-v2` binds metadata, dimensions, inputs and outputs with `result_binding_sha256`; replacement with stale evidence is rejected. Export validates the binding before opening an output and atomically replaces the destination after successful serialization. This digest detects accidental mutation; it is not a signature or an independent scientific assessment.

`verify_cpu_batch_ledger(path, graph, error_rate=...)` replays single shots against caller-supplied graph/prior/numerics, independently recomputes binary or Pauli check parity, and checks iteration/work/termination fields. It reads v1 historical evidence without rewriting it. Empty JSONL contains no graph claim and returns graph_verified=False. Falsely recomputed digests do not bypass numerical replay. Assessment remains not_assessed.

Red: 34 failed. Green: 271 passed in 34.50s across evidence, stable SPA, corrected profile and failure atomicity; expanded evidence/replay suite: 36 passed. Full integration and paired CPU measurements are recorded separately below when complete. Compiled hot loops and numerical profile identities are unchanged.
