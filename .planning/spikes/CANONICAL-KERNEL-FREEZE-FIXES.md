# Canonical kernel freeze findings — ordered fixes

The three findings from the [freeze audit](CANONICAL-KERNEL-FREEZE-AUDIT.md) are closed in the approved order: **C03 → C01 → C02**. This qualifies the tested, versioned contracts; it does not promote stable SPA into historical public manifests or imply that every schedule/controller has a compiled implementation.

| Order | Finding and correction | Functional commit | Focused evidence |
|---|---|---|---|
| 1 | C03: validate the normalized float64 prior at construction, including direct/replacement binding and wide-dtype Pauli buffers, before shortcuts | `46a2c45` | [031](031-prior-state-fix/README.md): 21 pre-fix failures; 226 checks pass after correction |
| 2 | C01: guard BP4 live state independently of rounding scope; return failed shot indices from a compiled helper and reject the entire batch after restoring its thread mask | `c57bd32` | [032](032-bp4-failure-fix/README.md): 7 pre-fix failures; 169 checks pass after correction |
| 3 | C02: reject nonzero damping in conventional source-scoped residual BP; accept legacy v1 and explicitly undamped v2/v3 | `fb1d329` | [033](033-residual-admission-fix/README.md): 5 pre-fix failures; 18 admission/lifecycle checks pass |

These changes preserve ordinary finite arithmetic, reduction order, stopping, candidate decisions, work accounting and historical profile identities. Newly rejected configurations previously either stored nonfinite values, returned nonfinite state as an ordinary result, or silently ignored a declared policy setting.

## Verification

A fresh Numba cache was used for the broad regression run: **1,412 passed, one existing skip** across canonical, circuit and research tests. This includes **44 new regression cases**. The existing skip concerns Phase 4 notebook evidence reconciliation; it is unrelated to these fixes. See [regression.log](033-residual-admission-fix/regression.log) and [JUnit receipt](033-residual-admission-fix/regression.xml).

All **18 independent qualification groups pass** in [results.json](033-residual-admission-fix/results.json). They rerun exact multi-check tree inference, mixed-magnitude parity/permutation checks, Pauli-label covariance, 63 aligned native SPA cases, 84 native NMS controls, high-confidence oracle comparisons, pinned Relay inner-memory and aSCED zero classifications, schedule damping, residual budget denial, controller admission, CPU isolation and the original C01/C03 counterexamples. Native discrepancies remain explicitly classified. Sionna evidence is a source-operation transcription, not an executed Sionna decoder.

The new tests also cover all three BP4 resolution scopes, sweep/single/batch failure paths, mixed successful/failed batches, caller thread-mask restoration, unchanged caller buffers, and preservation of an existing ledger after failure. Marginal normalization still permits legitimate underflow from extreme **finite** beliefs. Batch failure reports identify failed shots but do not claim to preserve exception instances across Numba workers.

The independent [verifier](033-residual-admission-fix/verify.py) checks production source hashes, test counts, immutable tracked history in spikes 008–030, baseline source identity, and exact matched CPU ledger contents. Its receipt is [verification.json](033-residual-admission-fix/verification.json).

## CPU implementation and measured scope

Prior validation occurs once at construction or binding. BP4 guards stay inside the shared compiled sweep, without changing floating-point operations or enabling fastmath. An initial try/except inside `prange` disabled parallelization; a non-inlined compiled per-shot helper corrected that. Successful shots avoid the failure-result allocation. Numba's exception constraints are documented in [spike 032](032-bp4-failure-fix/README.md).

The benchmark compares pre-fix `729157f` with corrected `fb1d329` using identical retained BB72 binary and GB46 Pauli inputs, stable policy v3, 512 shots per family, a 20-iteration limit, and 15 paired warm repetitions per worker setting. First-call/JIT-inclusive times are recorded separately. Construction and ledger I/O are excluded from warm timings. Both versions retain candidate, iteration, convergence and work ledgers for workers 1, 2 and 4.

The allocation exposes CPUs 56 and 120, which are sibling threads on **one physical core**. One-worker timing is the primary guard-overhead comparison. Two/four-worker results establish matched behavior and compiled scheduling, not multicore scaling. Both revisions remain compiled in isolated persistent processes; timed runs alternate order, with only one process measuring at a time. Shared-host measurements are descriptive and do not establish statistical performance bounds.

| Family | Workers | Baseline shots/s | Corrected shots/s | Throughput change | Corrected batch / single speedup |
|---|---:|---:|---:|---:|---:|
| binary_bb72 | 1 | 3710 | 3721 | +0.28% | 1.03× |
| binary_bb72 | 2 | 5367 | 5323 | -0.81% | 1.48× |
| binary_bb72 | 4 | 5340 | 5326 | -0.26% | 1.47× |
| pauli_gb46 | 1 | 2130 | 2125 | -0.22% | 1.03× |
| pauli_gb46 | 2 | 3026 | 3021 | -0.18% | 1.46× |
| pauli_gb46 | 4 | 3048 | 3032 | -0.53% | 1.45× |

One-worker throughput differs by +0.28% for binary and −0.22% for BP4; all measured worker settings remain within 1% of baseline. No material guard regression is established by the paired run. The largest batch/single speedup is 1.48× on this one-core allocation, not a multicore scaling claim.

The initial sequential run made both BP4 and the unchanged binary control appear about 17% slower. That result prompted alternating warm measurements instead of an unsupported code optimization. The [preliminary evidence](033-residual-admission-fix/preliminary-sequential/cpu-comparison.json) is retained, alongside the [final paired comparison](033-residual-admission-fix/cpu-comparison.json), raw timings, and [parallel diagnostics](033-residual-admission-fix/current/parallel-diagnostics.txt). All 6,144 baseline/current CPU ledger rows match exactly in paired source/input configurations.


## Contracts available to later HTML work

- Compiled binary and joint-Pauli flooding and CPU batches retain their explicitly qualified policy versions and numerical scopes.
- Conventional syndrome-residual BP requires an undamped profile. Calling it with the generic damped default now fails immediately; callers must explicitly select a compatible profile.
- Local serial/layered schedules and interventions retain their separately qualified interfaces. Stable flooding support does not imply stable-policy BPGD/Q-BPGD or compiled residual support.
- Historical public manifests and numerical defaults remain versioned as before. Stable policy v3 is still rejected by the frozen research-manifest contract. Any public exposure/default change needs an explicit new contract and qualification; UI labels must reflect the existing capability boundaries.

Phase 11 remains at plan 17 of 25. Publication evidence gates and the three-regime scope are unchanged. No source-faithful curve reproduction or universal mathematical freeze is claimed by these fixes.

## Reproduce

From the repository root, with the project virtual environment:

```bash
NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 NUMBA_CACHE_DIR=/tmp/bp-freeze-repeat-tests .venv/bin/python -m pytest -q tests/canonical tests/circuit tests/research --junitxml=.planning/spikes/033-residual-admission-fix/regression.xml
NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 NUMBA_CACHE_DIR=/tmp/bp-freeze-repeat-oracles .venv/bin/python .planning/spikes/033-residual-admission-fix/qualify.py
.venv/bin/python .planning/spikes/033-residual-admission-fix/compare_cpu.py
.venv/bin/python .planning/spikes/033-residual-admission-fix/paired_cpu.py
.venv/bin/python .planning/spikes/033-residual-admission-fix/verify.py
```

Run measurements after the tests finish. The native oracle harness uses the pinned native sources/binaries documented in spikes 013 and 028. The comparison harness extracts only baseline source into an owned temporary directory and never checks out or rewrites the working tree.
