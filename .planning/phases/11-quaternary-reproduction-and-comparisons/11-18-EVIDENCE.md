# aSCED Figure 2 supplemental evidence

This is a non-authorizing supplement to candidate `a5b9c6eb0bbe8a07743f5be093cc937c50759a07d5f60f8cebc3be557f4b49b5`. The candidate and source target remain unchanged, pending scientific review. The [machine-readable extraction](../../../data/source-targets/phase11-asced-figure2-extraction-evidence.json) has digest `a3535d550b695c42da1520cc5cbf00f6606364b9b704285d7b24158fe44d5b31`.

## Provenance and method

- Primary [arXiv:2605.06547v2 PDF](https://arxiv.org/pdf/2605.06547v2), SHA-256 `0eec129dde3026f8225ec7d5f2884dbefe37566c9f71d105cae0195e4e4abca5`, page 4, Figure 2. The pinned crop SHA-256 is `e9f8ddb7d2d65ffd4deee1d0eec0d874fd38c011e0ac3783c9ca5b62b5e6abb0`.
- Public [author results repository](https://github.com/kit-cel/quantum_asced) at commit `816772071486615dfc7d71d1e15df597edc58a26`. The JSON pins SHA-256 for each selected `LER.json`, `stats.json`, and `meta.txt` file.
- [Extractor](../../../scripts/extract_phase11_asced_figure2_evidence.py) uses PyMuPDF 1.28.2 to read PDF vector paths and tick anchors. It maps PDF `x=343.655548` to `p=.03`, `x=539.762451` to `p=.10`, `y=64.239990` to LER 1, and `y=217.836472` to LER 1e-5. It interpolates path centerlines at the eight requested p slots. The ±1 PDF-point ordinate interval covers vector reading only; it is not a Monte Carlo confidence interval or acceptance tolerance.
- `stats.json` supplies each raw result's `logical_errors` and `trials`; each quotient independently reproduces its `LER.json` value. The repository's relationship to the published figure is assessed by comparing those values with the vector extraction, not assumed.

## Cross-check

| Figure 2 curve | Author `target_errors` | Raw values outside PDF reading interval | Other discrepancy |
|---|---:|---|---|
| BP4 baseline | 4000 | all eight p=.03–.10 | Author/PDF LER ratio 0.293–0.809; upper dotted PDF path has no markers at most requested p slots. |
| BP4-aSCED K=16, Δ=2, L=4 | 2000 | none | Author's stopping target differs from the paper's stated 400 errors. |
| OBP4 baseline | 400 | p=.07 | `trials` at p=.03 is 1,224,872, above `max_trials=1,000,000`. |
| OBP4-aSCED K=16, Δ=2, L=4 | 400 | p=.09 and .10 | `trials` at p=.03 is 1,739,591, above `max_trials=1,000,000`. |

The upper dotted BP4 path also matches **all ten** values in the pinned author repository's `Results/Toric_128_2/BP4/LER.json`: the transformed vector x coordinates match its p values, and the largest relative ordinate difference is below 0.0002. That file's metadata identifies `n=128`, while the Figure 2 panel is labeled GB46 (`n=46`). This is strong numerical evidence of a cross-code provenance discrepancy; it does not establish how the published figure was assembled or which series the authors intended. The machine-readable evidence retains each of the ten comparisons and hashes the Toric files.

The paper states runs stop after at least 400 logical errors or 10^6 trials, but the repository metadata for ordinary BP4 and BP4-aSCED states 4000 and 2000 target errors respectively. The cause of these differences, including whether files correspond to the exact published run and whether parallel execution explains trial-cap overshoots, is unresolved.

The Figure 2 source denominator, source-curve statistical intervals, numerical agreement tolerance, and reviewer signoff remain blocked. No source shots were admitted. Native matched-input availability remains `declined_unavailable`; canonical fidelity remains `canonical_adaptation`.

## Reproduce

Check out author commit `816772071486615dfc7d71d1e15df597edc58a26`, obtain the pinned PDF, and run:

```bash
python scripts/extract_phase11_asced_figure2_evidence.py --pdf /path/to/2605.06547v2.pdf --author-repo /path/to/quantum_asced --output /tmp/asced-figure2-evidence.json
```

The extractor requires PyMuPDF and validates the PDF SHA-256 and repository commit before producing output. Compare its `evidence_sha256` with the value above.
