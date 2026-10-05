# Bhatnagar et al. — code-capacity impulse decoding

## Primary source and status

- Paper: Shobhit Bhatnagar, Michele Pacenti, Nithin Raveendran, David Declercq, and Bane Vasić, *Impulse Decoding of Quantum LDPC Codes: Equivalence of Degeneracy and Code-Shortening*, [arXiv:2606.18240v1](https://arxiv.org/pdf/2606.18240v1), 16 June 2026.
- Anchors: Section IV and Algorithm 1 define the code-capacity impulse procedure and selection; Section V defines the 100-iteration, variable-to-check clipping, and stopping conventions; Figure 5 is the B1 target. Figure 2 uses BB-288 and can serve as a second-code check later.
- Author implementation identity: unverified. Source curve data are described as available from the authors on request; no numeric points have been imported into this registry.
- The three `.spec.toml` files remain non-runnable source records. `first-convergence-0.toml` is a runnable **canonical adaptation**, qualified against those records and the registered impulse controller; it is not a source-faithful Figure 5 reproduction. The other two requested variants have exact typed compiler mappings but no runnable paper-root TOML yet.

## Requested decoder variants

| File in parent folder | Shortened value | Candidate selection | Target |
| --- | ---: | --- | --- |
| `minimum-weight-1.spec.toml` | 1 | Minimum Hamming weight among converged attempts | Figure 5 |
| `first-convergence-0.spec.toml` | 0 | First converged coordinate in declared order | Figure 5 |
| `first-convergence-1.spec.toml` | 1 | First converged coordinate in declared order | Figure 5 |

The source also plots `Minimum_Weight/0`, but it was not among the requested decoder files and is not claimed here as a selected variant.

## Policy and experiment inventory

- Algorithm 1 runs an initial BP attempt and launches one fresh shortened BP attempt per variable only if that attempt fails. Setting an initial variable LLR to positive or negative infinity represents shortening to 0 or 1. The code-capacity plots use 100 BP iterations per call and limit variable-to-check messages to `[-25,25]`; the exact finite realization of an infinite forced prior must be independently checked.
- Code/noise: Figure 5 uses the B1 `[[882,24,18 ≤ d ≤ 24]]` lifted-product CSS code under independent X-error code-capacity noise. It reports failure rate over approximately p=0.05–0.10. Section V defines failure as nonconvergence or logical error and states at least 100 failures per plotted point.
- Candidate repository artifact: `data/artifacts/b1-panteleev-kalachev-v3.npz`. Exact equality to this paper's ordered experimental matrix and logical basis remains unverified.
- Circuits: the paper also contains circuit-level algorithms, but they are separate later targets. No circuit details are imported into these Algorithm 1 files.
- Published target points, uncertainty, per-point denominators, and author implementation revision: uncollected. Do not mark Figure 5 reproduced before they and the source manifest are resolved.

## Reproduction path

Qualify source versus canonical shortening and selection semantics, the BP update and schedule, an independent original-syndrome check, and full-attempt work accounting. The [bounded B1 policy-file gate](../../../docs/css-literature-gate.md) tests the interface on matched near-zero-noise samples during Phase 6. Published-curve assessment remains a separately prespecified CSS campaign.

For a compatible schema-v5 CSS study, the same public command computes or verifies and reuses the result:

```bash
bp-registry path/to/study.json --decoder literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.toml --results-root path/to/results
```

The study must pin the code artifact, physical sample identity, iteration and work budgets. The symbolic one-attempt-per-coordinate cap and ascending coordinate order resolve from the validated artifact block length before execution and cache identity are formed. The policy records flooding and a finite magnitude-25 forced LLR as declared interpretations; the paper's message schedule and exact infinity realization are unresolved.
