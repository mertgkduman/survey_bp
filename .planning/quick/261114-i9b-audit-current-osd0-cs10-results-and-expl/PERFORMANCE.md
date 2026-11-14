# Why this OSD-CS implementation is faster

This is a source-derived implementation specialized to the uniform binary channels used in the Roffe toric campaign. It preserves the same CS10 candidate search. It does not demonstrate a faster paper-CS60 decoder or a faster implementation for arbitrary LDPC matrices.

The [pinned public C++ source](https://github.com/quantumgizmos/ldpc/blob/d3429964cd4ffe1abfc041c6ec8b8425cb174f40/src_cpp/osd.hpp) already factorizes once per decode. For each trial pattern it still constructs a modified syndrome, solves the triangular system, fills the free variables, and scans the resulting vector to score it. Our change reuses the response to each free-variable flip as well as the factorization.

For a base solution x0 and precomputed nullspace directions z_j, the same candidate is x(u) = x0 XOR (XOR over selected z_j). Singles reuse the directions; pairs are assembled from the base and two stored singles with wordwise XOR. No Gaussian elimination or triangular solve is needed for each pair.

GF2 rows and candidates are packed into uint64 words. XOR updates64 bits at once, and population counts score candidates. For the qualified uniform channel the native sum of log(1/p) over selected bits is a positive constant times Hamming weight, so population counts preserve its ordering and first-minimum rule. This specialization is not an admitted nonuniform-channel scoring implementation. The n=450 candidates occupy eight machine words.

Numba compiles the loops. Packed contiguous storage also avoids repeated sparse-pointer traversal and temporary syndrome/solution allocations in this small/moderate matrix regime. The separate compiled BP outer loop is another optimization, with the existing canonical arithmetic unchanged; its speedups are not included in the OSD-only claim.

## Matched benchmark check

The original qualification used unmodified C++ built with -O3 and reported2.13–3.41x CS10 ratios. The follow-up enables -march=native as well, verifies64 matched selected outputs, then alternates twelve warmed timing rounds on the same64 fixtures and CPU affinity. Both include selected-output syndrome validation. The optimized interface additionally returns all candidates, work counters and a set digest; the native timed interface returns the selected output. Constructor/JIT/BP/ledger I/O are excluded. Rank-equivalent inputs control unspecified native ties before either timed call. Exclusive physical-core occupancy is not asserted; these are observed medians under the recorded host conditions.

| Code length | Native CS10, microseconds/call | Optimized CS10, microseconds/call | Ratio |
| ---: | ---: | ---: | ---: |
| 162 | 116.2 | 50.0 | 2.32x |
| 242 | 210.9 | 75.6 | 2.79x |
| 338 | 361.2 | 114.6 | 3.15x |
| 450 | 600.1 | 170.0 | 3.53x |

The source revision, compiler command, library and implementation hashes, affinity and individual trials are retained in native-target-benchmark.json. The frozen original qualification is unchanged. Its404 complete candidate-set comparisons against native and independent GF2 oracles remain the deeper correctness evidence. This follow-up tests the host-target compiler confound; it is not an ablation assigning an exact percentage of the gain to each optimization. OSD0 has less repeated work to remove and was slower on length162 in the original measurements; no universal OSD0 speedup is claimed.

Current scientific results are in [COMPARISON.md](COMPARISON.md), with explicit summary/endpoint versus interior-ledger audit status.
