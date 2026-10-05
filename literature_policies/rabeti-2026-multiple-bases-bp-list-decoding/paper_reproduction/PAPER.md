# Rabeti and Mahdavifar — MBBP-LD

## Primary source and status

- Paper: Sheida Rabeti and Hessam Mahdavifar, *Multiple-Bases Belief Propagation List Decoding for Quantum LDPC Codes*, [arXiv:2605.14170v1](https://arxiv.org/pdf/2605.14170v1), 13 May 2026.
- Anchors: Section III, Algorithms 1–2, Equation (4), and the frequency-weighted decision rule define the decoder; Section IV and Figure 5 describe the B1 experiment.
- Author implementation identity: unverified. `mbbp-ld.spec.toml` is **not runnable**; the canonical Phase 6 subtree ensemble and source-specific list selector do not yet exist.

## Requested decoder variant

| File in parent folder | Composition | Target |
| --- | --- | --- |
| `mbbp-ld.spec.toml` | Independently run BP on matrices made by appending each maximal-subtree check set, collect converged candidates, then select by frequency divided by weight plus one | Figure 5, B1 |

## Policy and experiment inventory

- The source describes normalized min-sum with factor `0.875`, serial check scheduling, and at most 100 iterations in Section IV. Its decision rule scores each distinct candidate by occurrence count divided by `Hamming weight + 1`; if no member converges, it declares failure and returns zero. The augmented matrix and its syndrome must be represented explicitly and independently validated against the original problem.
- Code/noise: Figure 5 uses B1 `[[882,24,18 ≤ d ≤ 24]]` over independent X-error binary-symmetric noise, with p approximately 0.04–0.10. Section IV says each point was collected after 100 decoding failures.
- Candidate repository artifact: `data/artifacts/b1-panteleev-kalachev-v3.npz`; exact paper-experiment matrix/logical identity has not been checked.
- Circuits: not applicable to the selected code-capacity Figure 5 target.
- Source gaps before a faithful run: exact check permutation/partition choices and seeds, augmented-syndrome notation, candidate score ties, original author-code identity, digitized points, full denominators, and uncertainty/tolerance rules. A declared canonical completion of these choices is an adaptation until source evidence resolves them.

## Reproduction path

Implement subtree construction and check/syndrome augmentation as a canonical problem transformation, independent BP member state and unique work leaves, source-defined candidate admission, and frequency-weighted selection. Run deterministic small-graph fixtures before a bounded B1 study. Match the paper's artifact and frozen experiment details before claiming Figure 5 agreement.
