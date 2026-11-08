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

## Combined qualification

- Replayed audit: 32 passed, zero failures; all 19 former failures closed.
- Mathematical controls: 192 exact-inference cases and 100 covariance cases.
- Native alignment: 216 cases; installed native binary identity retained.
- Compiled grid: 432 configurations and 2,592 stored shot rows independently replayed.
- CPU receipts: 6,144 baseline/current rows replayed, including historical v1.
- Full suite: 2,251 passed, one existing skip, 25 baseline fork/multithread deprecation warnings in 1,390.32s. No observed deadlock.
- Paired CPU measurement: exact output hashes, throughput within 0.7% of baseline, about 1.45–1.48× repeated single-shot throughput with two/four workers on the available sibling hardware threads. No physical-multicore scaling claim.

See [the consolidated correction report](../CANONICAL-KERNEL-COMPLETENESS-FIXES.md), [verification.json](verification.json), [capability-contracts.json](capability-contracts.json), and [the user-facing contract guide](../../../docs/canonical-kernel-contracts.md). The integration follow-up 7b763d2 preserves the historical Hsu SPA profile; its change is outside the benchmarked compiled paths.

Commands (repository root, OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4): `.venv/bin/python .planning/spikes/042-batch-evidence-fix/qualify.py`; `.venv/bin/python -m pytest -q tests --junitxml=.planning/spikes/042-batch-evidence-fix/full-regression.xml`; `.venv/bin/python .planning/spikes/042-batch-evidence-fix/verify.py`. Run compare_cpu.py before paired_cpu.py to regenerate cold and warm CPU receipts. Historical spikes must not be run in-place when preserving their evidence.
