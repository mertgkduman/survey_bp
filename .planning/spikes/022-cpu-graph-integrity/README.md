---
spike: 022
idea: canonical-kernel-audit
name: cpu-graph-integrity
type: standard
validates: "Given admitted boundary graphs, CPU batching preserves independent stopping, algebraic validity, work and graph identity"
verdict: PARTIAL
related: [018-public-summary-fix, 021-policy-entry-closure]
tags: [cpu, work, immutability, profiles]
---

# Spike 022: CPU boundary and graph integrity

## Approach

Reuse one-sweep numerical primitives but independently implement initial decisions, stopping and work-check counting. Compute syndrome validity from original binary/Pauli matrices without production syndrome helpers. Compare workers 1/2, caps 0/1/4, plain SPA and explicit SPA/min-sum/quantized policies. This is an independent control-flow/algebra audit, not another independent numerical oracle; spike 019 supplies that role.

## Run

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/022-cpu-graph-integrity/probe.py
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python -m pytest -q tests/canonical/test_kernel_contract_admission.py tests/canonical/test_schedule_semantics.py tests/canonical/quaternary/test_compiled_bp4.py
```

## Investigation and results

**840 ledger rows across 210 batches pass** output, independent validity, stopping, work-count, thread restoration and unchanged/read-only graph-buffer checks. Coverage includes binary empty graphs, unary checks, isolated variables, degree-two trees, first-valid/fixed-iteration Pauli stopping, and prior decisions that are not identity/zero. Identity-only Pauli rows are correctly rejected. The first harness accidentally treated that unsupported graph as admitted; `harness-first-results.json` retains the harness error, not a production finding. The final matrix explicitly verifies the exclusion.

**B03 — compiled BP4 ignores an accepted nondefault v1 saturation.** Through the normal factory, `replace(QBP4_F64_V1, saturation=1)` is accepted. Scalar beliefs honor the cap; compiled beliefs reach 1.6201145069582776. The compiled v1 update/decode calls use the constant default limit rather than the selected profile parameter. Default v1 and v3 are not implicated by this counterexample. Honor the selected parameter or reject it at admission; do not declare it effective while ignoring it.

A deliberately overflowing finite min-sum coefficient causes both single-shot and batch execution to fail without returning decoded results, and restores the thread mask. Single-shot raises ValueError; the parallel batch exposes Numba SystemError. This is an error-normalization limitation, not observed silent output corruption.

Selected existing regressions: **183 passed**. Those tests do not assert the newly discovered cap and alternate-entry counterexamples. The previous 1,162-pass broad qualification remains source-matched historical evidence; production was not edited in this audit.

## Evidence

`events.jsonl.gz` is deterministic gzip containing all 840 per-shot CPU ledger rows plus their original check matrices. `results.json` records counters, counterexamples, environment and source hashes. `regression.log`/XML retain the selected regression outcome. No timing or statistical decoding-performance claim is made.
