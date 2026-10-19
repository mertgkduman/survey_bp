# Compiled decode buffer qualification

## Change

The optional compiled plain binary SPA/min-sum and BP4 decoders now allocate their iteration scratch once per shot and alternate two variable-to-check buffers. Binary decode clips the initial edge message once; every subsequent edge message is already clipped at its update boundary. Plain BP4 decode computes candidates without normalizing four-state marginals; the public BP4 `sweep` continues to produce marginals and immutable, independent snapshot arrays. No publication, policy, budget, or ledger path uses these prototypes.

## Matched timing

`scripts/benchmark_compiled_decode_buffers.py` ran before and after on host `dcc-core-ferc-u-ac39-4-1`, pinned to CPU 46 with OMP, OpenBLAS, and MKL at one thread. Each warmed median is from five repetitions of 100 batches of the same 24 BB72 or 8 GB46 seeded syndromes. Setup and JIT are excluded from these per-shot figures; the previous profile measured their separate cost.

| Case | Before ms/shot | Final ms/shot | Before/final |
|---|---:|---:|---:|
| BB72 SPA, cap 10 | 0.30904 | 0.26696 | 1.16× |
| BB72 min-sum, cap 10 | 0.04189 | 0.04271 | 0.98× |
| GB46 BP4, early stop, cap 8 | 0.59890 | 0.58697 | 1.02× |
| GB46 BP4, fixed 8 sweeps | 1.04116 | 1.02007 | 1.02× |

The before, intermediate, and final artifacts are `before.json`, `after.json`, and `final.json`. Their host, affinity, workload hashes, 5/5 candidate hashes, iteration lists, and convergence lists match within each case. The small min-sum difference is a measured regression on this host, so this change should not be presented as a universal speedup. The BP4 gain is also small relative to timing variation.

## Semantic checks and limits

`pytest -q tests/canonical/test_compiled_binary.py tests/canonical/quaternary/test_compiled_bp4.py` passed 11 tests. These compare compiled and Python reference terminal decisions and intermediate buffers, exercise clipped initial binary messages at extreme priors, and verify public sweep snapshots survive later decode calls. `git diff --check` and Python compilation passed.

The prior matched native comparison measured about 0.082 ms/shot for `ldpc` BB72 SPA and 0.201 ms/shot for aSCED GB46 BP4 early stop. On those specific cases, the final compiled prototypes remain about 3.2× and 2.9× slower, respectively. These are development timings, not a source-fidelity or campaign-throughput assessment. A larger gain will likely require qualifying the check-neighbor reduction or a lower-level implementation; changing floating-point reduction order needs explicit numerical and decoder-output checks. Policy execution, ledger writing, and resource accounting still need separate whole-campaign profiling before backend promotion.
