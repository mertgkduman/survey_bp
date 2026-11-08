---
spike: 043
idea: canonical-kernel-audit
name: circuit-cuda-mathematics
type: standard
validates: "Given admitted new paths, independently computed factors reproduce their messages, decisions and failure semantics."
verdict: PARTIAL
related: [034, 042]
tags: [mathematics, circuit, cuda]
---

# Circuit and CUDA mathematics

Baseline b598ad1. Continue the user's already approved mathematics → upstream →
policy → execution order. Production source and historical evidence are immutable
during this audit. This is CLI-verifiable numerical research, before HTML work.

## Research and approach

[Kschischang–Frey–Loeliger](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf)
defines local sum-product and tree inference. Compare with independently
enumerated probability factors/minimum costs; direct backend parity alone can
share errors. Tree enumeration establishes exactness only for undamped SPA
without active finite safeguards. Compare finite recurrences and stopping
separately, including heterogeneous signed priors.

Prespecified tolerance: atol=rtol=2e-12; seed 4301. Compare all four check rules,
three iteration caps and all four syndromes on a small two-check tree. Test CUDA
tree beliefs against joint assignment enumeration in the explicitly labelled
simulator; reuse, rather than relabel, the existing H200 hardware receipts.
Probe finite input causing intermediate overflow separately from ordinary-domain
correctness. No new GPU allocation or publication campaign is needed.

## Run

`OMP_NUM_THREADS=1 NUMBA_ENABLE_CUDASIM=1 .venv/bin/python .planning/spikes/043-circuit-cuda-mathematics/probe.py`

## Investigation trail

The prior 192 exact Pauli trees and 100 covariance cases remain qualified for
unchanged implementation bytes. New checks focus on the added execution paths.
Results and counterexamples will be recorded in results.json; process exit zero
means the audit ran, not that every invariant passed.

## Results

- 1,152 circuit/reference comparisons pass across SPA/MS/NMS/OMS, signed
  heterogeneous priors, all syndromes and zero/one/five-sweep caps. Maximum
  posterior discrepancy: 8.88e-16.
- Eight new CUDA-simulator tree marginal checks pass against full binary/Pauli
  probability enumeration (maximum error 1.67e-16). This is not new GPU timing.
- Prior Pauli mathematics is retained with verified identical source bytes:
  192 exact trees and 100 covariance cases.
- **E01, finite-failure parity:** NMS parameter=1e308 is admitted. Scalar raises
  NumericalFailure; compiled/auto clips an overflowing check message and returns
  a converged result. The problem is finite-state failure handling, not a
  demonstrated error at ordinary normalization coefficients.

Three groups pass, one fails. The counterexample is retained verbatim. Resolve by
consistent numerical failure or a shared justified admission restriction; do not
silently change the ordinary BP equations or old profile meanings.
