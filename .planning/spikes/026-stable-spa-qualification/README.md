---
spike: 026
idea: canonical-kernel-audit
name: stable-spa-qualification
type: standard
validates: "Given audited counterexamples, when corrected, then a new stable log-domain policy agrees with independent exact inference"
verdict: VALIDATED
related: [019, 020, 021, 022]
tags: [fixes, contracts, numerics]
---

# Stable SPA qualification

## Research
Reuses the independent oracles and pinned primary-source investigation in spikes 019–022. No new dependencies.

## Investigation Trail
Started from boundary audit at 02d165e; historical evidence is retained unchanged.

## What This Validates
A separately versioned stable SPA policy implements the finite-input parity equations across binary and Pauli flooding, explicit rounding boundaries, stopping and CPU batching. Existing profile defaults are unchanged; qualification does not silently migrate public manifests.

## Research and alternatives
The primary-source references in spikes 019–020 distinguish exact parity equations, source-specific numerical safeguards and adaptation choices. Existing scalar box-plus already passes the independent envelope. We compared a per-output compiled box-plus fold with a prefix/suffix compiled reduction. The latter performs linear work in check degree; its changed floating reduction order is declared in the new policy's evidence. Whole-product epsilon clipping remains available only under its historical version.

## How to Run
See benchmark.py, qualify.py and verify.py in this directory, and the commands in ../CANONICAL-KERNEL-BOUNDARY-FIXES.md. Run benchmarks separately from correctness tests. Use an empty NUMBA_CACHE_DIR to include compilation in first-call measurements.

## Investigation Trail
- 107 initial tests failed because the new policy did not yet exist; red.log retains that evidence.
- The initial stable implementation passed the 100-case high-confidence envelope and exact binary tree counterexample.
- A bounded small-magnitude tanh branch avoids cancellation in box-plus near zero; four additional relative-accuracy cases exercise both scalar helper and compiled sweep down to 1e-100 inputs.
- Added exhaustive Pauli tree marginals, repeated scalar/compiled buffers, all six resolution formats and three scopes, and CPU stopping/work controls.
- The first broad integration run found ten Relay adapter-profile omissions. The adapter fix retains shared admission and passes 19 focused tests. integration-first.log/xml retain that failure evidence.
- The final broad run used a fresh Numba cache: 1,368 passed, one existing notebook-related skip. No production edits followed that run.
- All 14 independent post-fix probes pass, retaining two 840-row CPU control matrices. Historical upstream checks remain classified by their original correspondence scope.

## Results
The opt-in `STABLE_SPA_F64` policy is qualified for the stated matrix. It uses version `bp-flooding-policy-v3`, canonical prefix/suffix reductions, explicit finite unary messages, boundary rounding and old-weight damping. Old numerical profiles and public schemas retain their existing meanings. See ../../../docs/canonical-stable-spa.md for use and compatibility boundaries.

## Performance
Matched 512-shot, 20-iteration-cap, seven-repeat measurements: four-worker batches deliver median **1.49× binary BB72** and **1.46× Pauli GB46** throughput versus the same compiled policy in bound-prior/single-shot calls. These are local host measurements, not scaling guarantees. First calls are recorded separately from warmed timings; graph binding and ledger I/O are excluded. Four benchmark ledgers retain 2,048 rows and match single-shot candidates, convergence and iterations.

Compiled linear-versus-quadratic stable check speed ratios by check degree: 4: 0.92×, 16: 5.26×, 64: 23.07×, 256: 102.74×. This isolates reduction cost and is not a whole-decoder speedup. Raw times and host/affinity details are in benchmark.json.

## Provenance
Production commit: `be7286ec919488dced1330dbb5913b1a3d23bf15`. Source hashes in results.json and benchmark.json identify the tested code even where a run started before the commit. verification.json independently binds those hashes, test receipts, historical evidence and ledger contents.
