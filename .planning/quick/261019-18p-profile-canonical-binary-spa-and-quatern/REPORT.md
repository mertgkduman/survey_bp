# Canonical BP profiling and compiled prototype — 2026-10-19

## Decision

The common-kernel design can be made competitive while keeping project-owned numerical and policy semantics. This task delivered an immediate **2.68×** improvement to the active Python BP4 sweep and opt-in compiled plain-kernel prototypes that reduce per-shot time by hundreds to over a thousandfold on the measured codes. The compiled paths remain development-only until budget reservation, event-ledger emission, and the wider policy family have differential qualification.

## Measurement method

All new timing batches ran on one Intel Xeon Gold 6248R node with `taskset -c 46`, `OMP_NUM_THREADS=1`, and OpenBLAS/MKL thread counts of 1. Each result retains three batch repetitions; the BP4 component experiment has 20 setup/sweep samples. The node was shared, so these are local engineering timings. Native graphs and compiled graphs were constructed before repeated decode timing; Numba's first-call latency and graph setup were measured separately. The reference binary row reuses its `EdgeTable` and `FloodingSchedule`; the reference BP4 row includes per-shot problem/session construction. Candidate and iteration comparisons use the same seeded syndromes and caps within each family. Raw records are linked below.

| Workload and rule | Cached Python, median ms/shot | Compiled, median ms/shot | Native, median ms/shot | Compiled speedup over Python | Native comparison |
|---|---:|---:|---:|---:|---|
| BB72 `hz`, SPA, 24 shots, cap 10 | 201.164 | 0.3078 | `ldpc` 0.0822 | 654× | 3.74× native; 24/24 project/native candidates and iterations agree |
| BB72 `hz`, min-sum, same shots | 57.788 | 0.0420 | `ldpc` 0.0276 | 1,376× | Project/native decisions differ at zero and near-zero LLRs |
| HGP225 `hz`, SPA, 8 shots, cap 10 | 1,350.266 | 2.2056 | `ldpc` 0.4853 | 612× | 4.54× native; all eight project/native candidates and iterations agree |
| HGP225 `hz`, min-sum, same shots | 233.114 | 0.1227 | `ldpc` 0.0965 | 1,900× | Project/native decisions differ; no strict native ratio |
| GB46 H44, BP4, 8 shots, early stop, cap 8 | 607.330 | 0.5874 | aSCED C++ 0.2007 | 1,034× | 2.93× native; 8/8 candidates agree |
| GB46 H44, BP4, eight forced sweeps | 1,082.529 | 1.0254 | aSCED C++ 0.3046 | 1,056× | Only 4/8 native final candidates agree; no strict native ratio |

The compiled prototypes matched their Python reference candidates, success flags, and iteration counts on every timed case. The tests also compare intermediate C2V, V2C, belief, and marginal buffers within `1e-12`. For BB72 SPA, 9 of 27 sampled floating buffers were byte-identical and the largest absolute difference was `1.78e-15`; terminal decisions were identical. The native C++ BP4 cap counter reports 9 after eight sweeps, a source loop-counter convention noted in the earlier [benchmark report](../261019-0po-benchmark-canonical-python-bp-kernels-ag/REPORT.md).

## Where the time went

- The original GB46 Python sweep median was **337.669 ms**, versus **125.926 ms** after preindexing immutable check/variable neighbors and computing each edge's commute/anticommute LLR once per sweep. `commutation_llr` calls fell from **2,464 to 352** per sweep. Setup rose from **3.946 to 4.341 ms** in these samples because it now builds neighbor indexes. All 20 before/after candidate, C2V, V2C, and belief hashes match. See [before](./qbp4-before.json) and [after](./qbp4-after.json) records, including `cProfile` call counts.
- Pure Python numerical primitives dominate the remaining reference time. A separate five-batch microcheck measured median BP4 Python syndrome evaluation at about **90 µs**, against a **126 ms** sweep. Binary Python syndrome evaluation was about **9 µs**, against roughly **200 ms** per BB72 SPA shot. Input validation for the unbound compiled binary call cost about **32 µs**; binding the fixed physical error rate once per batch reduced BB72 compiled SPA from **0.344 to 0.308 ms/shot** and min-sum from **0.0755 to 0.0420 ms/shot**. See [component overheads](./component-overheads.json), [unbound BB72](./compiled-binary.json), and [bound BB72](./compiled-binary-bound.json).
- With an empty Numba cache, the first BB72 compiled call took **2.18 s** and the first GB46 BP4 compiled call **2.86 s**; subsequent calls took 0.224 and 0.381 ms in those single-shot checks. Graph/prior preparation took 0.82 and 1.94 ms. JIT startup must be included in short jobs and amortized for campaign throughput. See [binary startup](./cold-start.json) and [BP4 startup](./bp4-cold-start.json).

## Numerical boundaries

The BB72 min-sum mismatch is substantive for exact-output benchmarking. On the 24 original syndromes after one sweep, all **288** project/native candidate disagreements had native posterior LLR exactly zero: the project decodes exact zero as 0, while `ldpc` chooses 1. Later iteration behavior also differs around numerical zero and early stopping; changing only the tie choice did not make all final candidates equal. The project tie rule remains explicit and unchanged. The opt-in compiled min-sum path matches the project rule, not the native `ldpc` rule.

The GB46 BP4 early-stop candidates match the pinned aSCED C++ driver on eight shots. For forced sweeps, four final candidates differ; targeted cap scans first found disagreements at sweep 4–6 on affected cases, without exact-zero project beliefs at the divergent positions. The precise native recurrence/numerical cause remains open. No forced-sweep native efficiency ratio or source-reproduction claim follows from these timings.

## Implementation and next gate

The active Python BP4 engine now caches graph incidence and edge quantization while preserving its session, work reservation, and ledger-facing behavior. The optional `performance` extra pins Numba 0.64.0. [Binary compiled](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/canonical/compiled.py) exposes plain SPA/min-sum with graph and error-rate binding; [BP4 compiled](/hpc/group/pfisterlab/mg551/storage/survey_bp/src/bp_registry/quaternary/compiled.py) exposes plain four-state flooding with fixed priors. Neither prototype is selected by production manifests or claims policy coverage beyond those plain rules.

The next engineering gate is to express normalization, damping, scheduling, and other named policies as validated compiled inputs under each canonical family, then add budget admission, per-sweep work accounting, event-ledger boundaries, and replay checks. Qualify numerical edge cases and more code families before selecting the compiled backend for publication campaigns. Retain reference Python as an independent oracle. The unresolved min-sum and forced-BP4 native differences should be audited at intermediate messages before using those native rows as equivalence benchmarks.

## Reproduction and checks

- [BB72 bound timings](./compiled-binary-bound.json), [HGP225 bound timings](./compiled-hgp225-bound.json), [GB46 compiled/native timings](./compiled-bp4.json); prior unbound [BB72](./compiled-binary.json) and [HGP225](./compiled-hgp225.json) timing records are retained.
- Drivers: [binary benchmark](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/benchmark_compiled_binary.py), [BP4 benchmark](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/benchmark_compiled_bp4.py), [BP4 component profile](/hpc/group/pfisterlab/mg551/storage/survey_bp/scripts/benchmark_qbp4_components.py). The native C++ driver still requires the pinned aSCED checkout/build under `/tmp/phase10-asced-native/`.
- `pytest tests/canonical/quaternary tests/canonical/test_compiled_binary.py -q`: **197 passed**. Python compilation and `git diff --check` passed. The eight original GB46 early-stop and fixed-sweep trajectories retained their pre-optimization decisions and iteration counts.

These runs did not dispatch a production campaign and do not alter Phase 11's native aSCED `preserve_unavailable` decision.
