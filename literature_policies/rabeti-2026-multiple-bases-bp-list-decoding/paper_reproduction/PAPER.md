# Rabeti and Mahdavifar — MBBP-LD

## Primary source and status

- Paper: Sheida Rabeti and Hessam Mahdavifar, *Multiple-Bases Belief Propagation List Decoding for Quantum LDPC Codes*, [arXiv:2605.14170v1](https://arxiv.org/pdf/2605.14170v1), 13 May 2026.
- Anchors: Section III, Algorithms 1–2, Equation (4), and the frequency-weighted decision rule define the decoder; Section IV and Figure 5 describe the B1 experiment.
- Author implementation identity: unverified. `mbbp-ld.spec.toml` remains a **non-runnable source transcription**. The adjacent `mbbp-ld.toml` is a runnable, bounded **canonical adaptation** with two explicitly named redundant-check members; it does not reconstruct the paper's maximal-subtree ensemble.

## Requested decoder variant

| File in parent folder | Composition | Target |
| --- | --- | --- |
| `mbbp-ld.spec.toml` | Independently run BP on matrices made by appending each maximal-subtree check set, collect converged candidates, then select by frequency divided by weight plus one | Figure 5, B1 |
| `mbbp-ld.toml` | Two declared one-hot duplicate-row bases, independent serial normalized-min-sum BP, and the registered frequency/(weight+1) selector | Mechanism and command pilot only |

## Policy and experiment inventory

- The source describes normalized min-sum with factor `0.875`, serial check scheduling, and at most 100 iterations in Section IV. Its decision rule scores each distinct candidate by occurrence count divided by `Hamming weight + 1`; if no member converges, it declares failure and returns zero. The augmented matrix and its syndrome must be represented explicitly and independently validated against the original problem.
- Code/noise: Figure 5 uses B1 `[[882,24,18 ≤ d ≤ 24]]` over independent X-error binary-symmetric noise, with p approximately 0.04–0.10. Section IV says each point was collected after 100 decoding failures.
- Candidate repository artifact: `data/artifacts/b1-panteleev-kalachev-v3.npz`; exact paper-experiment matrix/logical identity has not been checked.
- Circuits: not applicable to the selected code-capacity Figure 5 target.
- Source gaps before a faithful run: exact check permutation/partition choices and seeds, augmented-syndrome notation, candidate score ties, original author-code identity, digitized points, full denominators, and uncertainty/tolerance rules. A declared canonical completion of these choices is an adaptation until source evidence resolves them.

## Reproduction path

The runnable policy duplicates original check rows 0 and 1 into two independent augmented members and duplicates the corresponding syndrome bits. It fixes the paper's reported normalized min-sum factor, serial check schedule, and 100-iteration limit, and maps the paper's no-convergence zero return to a typed failure with no selected correction. Its two members are a declared pilot choice; they are not asserted to be the source partition. Run deterministic fixtures and a bounded B1 command gate before a paper-scale study. Match the paper's ordered artifact, source partition and other frozen experiment details before claiming Figure 5 agreement.
