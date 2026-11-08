---
quick_id: 261108-meg
status: complete
baseline: 2f29881
implementation_commits: [90ecfbc, dc43249]
---

# Compatible circuit policies and CUDA execution

User scope: skip release packaging (item 1); implement circuit-policy parity and
useful GPU code-capacity execution (items 2 and 3). No publication phase is marked
complete and no existing numerical default or historical result is changed.

## Implemented

- Circuit-policy-v1 runs heterogeneous independent DEM faults through the
  canonical binary schedules, ordered memory and Relay controller. It supports
  SPA, MS, scalar NMS/OMS, five existing memory primitives, Relay and bounded
  finite-prior guided/beam adaptations. These are explicitly circuit adaptations,
  not newly established paper reproductions. DEM affine detector/observable
  semantics and fault-space candidate selection are retained.
- Ordinary circuit attempts have a Numba CPU path and an independent scalar
  oracle. Memory/Relay remain scalar; unsupported compiled compositions reject.
  Sinter can persist each worker batch to an explicit ledger directory.
- CUDA executes binary and joint-Pauli float64 flooding with stable SPA v3 or
  min-sum v2, scalar normalization/offset, damping and declared decision/stopping
  rules. Graph buffers persist on-device; bounded workspace is reused across
  chunks. CUDA-unavailable, unsupported precision/policy and nonfinite execution
  fail explicitly.
- Both paths snapshot inputs, own immutable results, bind provenance, publish
  ledgers atomically without replacement, and support stored replay. GPU replay
  uses the canonical compiled CPU. GPU JSON export is deferred until requested,
  retaining immediate compact evidence/result binding.

## Validation

- Circuit regression: 145 passed; final circuit-specific checks after the input
  snapshot addition: 34 passed.
- CUDA simulator: 19 passed plus the subsequently added input-ownership check
  passed independently. Simulation is explicitly labelled, never counted as GPU
  timing evidence.
- Initial H200 qualification: 17 hardware tests passed and 4,096 benchmark shots
  matched CPU candidates, iterations and convergence exactly, with stored replay.
  The initial NMS end-to-end slowdown (0.605x versus one CPU worker) exposed JSON
  serialization overhead and motivated the export change. Initial timing receipts
  are retained in gpu-qualification.json and gpu-hardware.log.
- Final H200 qualification: **20 passed**; 4,096 shots agree exactly in candidate,
  stopping and convergence; all stored rows pass independent CPU replay. Numerical
  buffer comparisons use atol=rtol=2e-13. Final hardware ran the committed source,
  including the input-ownership test and both additional Pauli tie rules.
- Final compiled circuit qualification on the pinned Relay circuit: 54 detectors,
  1,818 faults, 8,874 edges; four shots, three sweeps maximum. Faults, predictions
  and iterations agree with the scalar oracle; stored replay passes. Warm timing
  is 49.6 ms compiled versus 2.29 s scalar (46.2x on this bounded fixture).
- Full repository regression: **2,285 passed, 17 skipped, 25 baseline fork
  warnings**, 1,374.79 seconds. Sixteen skips were CUDA cases on the CPU-only
  host; the remaining skip is pre-existing. Three additional CUDA edge cases
  and the final circuit input-ownership case were added after suite collection
  and passed in the final 20-case hardware and 34-case circuit runs.

Median warm decode performance on H200, 1,024 shots and cap 20, versus two
compiled CPU workers on the same allocation:

| Family / policy | CPU ms | GPU ms | Speedup |
|---|---:|---:|---:|
| B1 binary stable SPA | 1245.15 | 10.07 | 123.6x |
| B1 binary NMS | 255.44 | 6.71 | 38.1x |
| BB72 joint-Pauli stable SPA | 479.20 | 5.25 | 91.3x |
| BB72 joint-Pauli NMS | 202.74 | 3.26 | 62.1x |

Decode times include transfers/allocation/result binding, exclude JIT warmup and
JSON export. Each raw trial and first-call time is retained. JSON export is still
a separate material cost: about 0.60–0.66 seconds for binary ledgers and 0.09
seconds for Pauli ledgers. No whole-socket CPU or universal speedup claim is made.
Only gpu-final/ is the frozen current-contract qualification; earlier raw GPU
ledgers retain their development-stage layout for provenance.

## Resource and evidence boundaries

Slurm probe 61401203 completed on NVIDIA H200. Initial qualification 61402431
completed in 66 seconds. Final job 61402503 completed in **48 seconds**, with one
GPU, two CPUs, 8 GiB;
its time limit was reduced from ten to three minutes to improve backfill.
Account: pfisterlab. Partitions: gpu-common, scavenger-gpu, scavenger-h200.
The existing interactive allocation was not modified.
Reported hardware: NVIDIA H200, driver 615.71.09, compute capability 9.0; Numba
0.64.0, NumPy 2.2.6, Python 3.12.2. The job loaded the CUDA/12.8 module; Numba's
runtime query resolved CUDA 13.4 on the GPU node. Runtime identity is retained
verbatim, without relabelling it as the requested module version.

The first circuit regression invocation omitted the manifest-required
OMP_NUM_THREADS=1 and failed environmental admission; rerunning with the declared
environment passed. This was not a kernel regression. Low-occupancy warnings in
tiny GPU tests and deliberate overflow in the simulator failure test are expected.

Usage and exact support boundaries: docs/circuit-policies-and-gpu.md.
Historical spikes 008–042 and all source-curve publication gates remain unchanged.

## Outcome and limits

Items 2 and 3 are implemented, tested and committed. Item 1 (release packaging,
license/version and release CI) remains explicitly skipped. Existing CPU
defaults and the legacy Sinter adapter are unchanged. Phase 11 remains at 17/25;
Phase 12/13 publication studies are not marked complete. This task qualifies
the documented execution subsets and development timing, not universal policy
parity, new paper reproductions, or package-release readiness.
