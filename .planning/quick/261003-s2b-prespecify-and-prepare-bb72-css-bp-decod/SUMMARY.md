---
status: complete
quick_id: 261003-s2b
date: 2026-10-04
---

# BB72 CSS BP comparison completed

The user confirmed the first cohort: SPA, min-sum, normalized min-sum, offset min-sum, BPGD, and BP-SF. The frozen X-only BB72 CSS design screened 17 configurations at each of p=0.03, 0.05, and 0.08 on 128 matched selection samples per rate. The selection lock chose one setting per family and kept undamped SPA as a fixed reference. Seven arms then ran on 512 new matched physical samples per rate. All 51 selection and 21 evaluation arms completed public replay verification; the aggregate report and source-status view were generated from those ledgers.

The prespecified paired assessment found one directional contrast: the canonical BP-SF adaptation had 252/512 failures versus 268/512 for undamped SPA at p=0.08, with 20 newly valid and 4 lost valid matched shots (Holm-adjusted p=0.02779). All other family-by-rate contrasts were inconclusive. This result applies only to the controlled BB72 X-only CSS study. The Bravyi circuit experiment and source BP-SF implementation are not reproduced.

The offline HTML, report, frozen selection lock, per-arm manifests/results, and deterministic compressed ledgers were packaged with SHA-256 bindings. The first automated publication attempt failed only on trailing whitespace inside Plotly's generated JavaScript; the publication check was narrowed to the other files while the HTML remained digest-checked. The verified 223-file package was pushed to GitHub main at `a23899cb1e8bbe8db503964f171cdb2f31528f51` and the remote tree was confirmed. Raw uncompressed ledgers and Slurm logs remain on the HPC filesystem.

Verification: 11 targeted tests passed; the prior full suite had 713 passes, one skip, and one outdated documentation assertion that passed after its wording fix. All Slurm stages through the aggregate report and packaging completed with exit code 0. The publication retry passed its package and Git checks and pushed successfully.
