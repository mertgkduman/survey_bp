# Circuit BP integration: pinned fixtures and CPU baseline

## Source and scope

The [Relay-BP v0.2.2 fixture archive](../data/circuits/relay-v0.2.2/README.md) contains 672 exact `.stim` files from upstream commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, with per-file hashes. The four directly usable representatives cover bivariate bicycle, rotated surface, and color memory circuits. They are source circuit fixtures, not yet selected and qualified paper-curve experiments.

The [BeamSearch author archive](../data/circuits/beamsearch-084a475b/README.md) separately preserves 38 source `.stim` files at commit `084a475b05fb64308103317a1ce5a0c4b0be58aa`. That bundle carries its original CC BY-NC-SA 4.0 license. Neither archive is silently promoted to a paper-specific source manifest.

Install the optional circuit dependencies with `python -m pip install -e '.[circuit]'`. `CanonicalBpSinterDecoder(max_iterations=8, rule="min_sum")` implements the Sinter custom decoder interface. It accepts a `stim.DetectorErrorModel`, builds one binary fault variable per independent `error` instruction, and preserves that instruction's detector and observable parities. A `^` separator stays within its original Bernoulli event. Zero-probability faults are removed; probability-one faults become explicit detector and observable biases. Other faults retain their individual log-odds priors. The decoder returns observable predictions in Sinter's little-endian bit-packed format.

Stim supplies circuit samples and a detector error model; Sinter calls the decoder. This circuit adapter explicitly retains the historical binary float64 v1 saturation and check-update policy; the new plain code-capacity SPA v2 default does not silently alter this circuit experiment. The adapter supports plain flooding SPA and plain flooding min-sum in this circuit slice. Its compiled CPU check pass is linear in the number of row edges: prefix/suffix box-plus for SPA, and first/second minima for min-sum. The SPA regrouping can change floating-point rounding relative to the reference edge-by-edge fold; the min-sum path is tested against the reference policy. The explicit `tie_break="zero"` default retains the canonical kernel's zero-belief rule; `tie_break="one"` reproduces Relay Rust's zero-belief rule. A 4,096-shot surface-code diagnostic found one observable disagreement under the canonical tie rule, at shot 3660. Relay's tie rule removed it and made that shot converge at sweep 6. Memory, Relay, branching, and other interventions have not been wired into this Sinter adapter. They need their own circuit compatibility and lifecycle tests before use. See the [numerical-profile guide](numerical-profiles.md) for the version boundary.

For source-faithful circuit work, the exact circuit/noise schedule, DEM extraction flags, decoder settings, measurement basis, observable map, sample/stopping rule, and author implementation identity must be pinned. The present adapter uses `decompose_errors=False` for the benchmark. The independent-mechanism DEM is the declared decoding model; whether deriving it from an original circuit discards a source-important dependency must be checked for each paper target. Detector fit and observable correctness are separate outcomes. The benchmark below counts observable errors and convergence only as bounded diagnostic results.

## Bounded matched-input CPU profile

Run `PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/benchmark_circuit_bp.py --output reports/circuit-bp-cpu-profile-v1.json`. The [local-fork receipt](../reports/circuit-bp-cpu-profile-v1.json) records source circuit and DEM hashes, graph sizes, seeded sample counts, setup time, warm decode time, convergence, observable errors, native identity, and prediction disagreements. It uses the installed Relay fork at commit `8216aca3153642044e2cdccbaa41547d15551bb0`.

The [author-release receipt](../reports/circuit-bp-cpu-profile-author-v022.json) reruns the same method against a wheel built in isolation from the pinned v0.2.2 source commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`; wheel SHA-256 is `b53ebd1ab01fd2d023456065eac69986d1e5fe6e8b9092d0d1885d86c642620b`. Both native runs use the same DEM-derived matrix, fault priors, observable map, detector shots, and `tie_break="one"` as the canonical run. This is a controlled kernel-path profile, not an identical full-paper procedure claim.

| Circuit | Shots | Faults / parity edges | Canonical CPU decode | Relay v0.2.2 Rust decode | Prediction disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rotated surface d=3 X | 4,096 | 221 / 568 | 0.0206 s | 0.0402 s | 0 |
| Color d=3 Z | 2,048 | 358 / 1,224 | 0.0401 s | 0.0598 s | 0 |
| Relay bivariate bicycle 18 X | 1,024 | 1,818 / 8,874 | 0.2047 s | 0.3343 s | 0 |
| Relay bivariate bicycle 144 Z | 128 | 67,752 / 391,320 | 1.4449 s | 2.0946 s | 0 |
| BeamSearch bivariate bicycle 144 Z | 512 | 8,784 / 30,672 | 0.5779 s | 0.8533 s | 0 |

Times exclude Numba compilation and include CPU decoding after one warm-up shot. They are single-run local measurements, not stable cross-machine speed ratios. The 8-iteration Relay BB144 diagnostic converged on zero of 128 shots; BeamSearch BB144 converged on zero of 512 shots. Both decoders agreed on every prediction, including the high observable error counts. A representative paper-performance run therefore needs source settings, adequate iterations, and the Phase 12–13 validation and statistical gates.

## GPU status

All canonical and native measurements above used CPU. The login environment has Stim, Sinter, and Numba, but no GPU backend installed and no visible GPU device. Slurm advertises GPU partitions. A GPU prototype should first target batches of fixed-graph flooding sweeps; per-shot Relay/branch control and small graphs may remain CPU paths. GPU throughput must include host-to-device transfers, setup, batching, and semantic agreement. No GPU speed result is claimed here.
