---
status: complete
quick_id: 261027-qsa
date: 2026-10-27
description: Reproduce the vanilla Q-BP curves in Yao et al. Figures 7 and 8 with paired binary/BP4 v1/v2 numerical profiles.
---

# Vanilla BP reproduction on A5 and B2

1. Extract exact Q-BP Figure 7/8 coordinates from arXiv:2312.10950v2 TeX. Rebuild A5 and B2 from cited source constructions and verify dimensions, commutation, and logical basis.
2. Freeze four named, data-only decoder policies: binary and BP4, each in v1 and undamped v2 numerical form. Use sum-product, 100 iterations, depolarizing p with binary marginal q=2p/3, shared physical errors, and independent stabilizer-equivalence evaluation.
3. Run all seven plotted p points for both codes with per-shot ledgers, source-vs-local tables, uncertainty, plots, and method notes. Use HPC scheduling if needed and retain incomplete/censored evidence honestly.
4. Document how to create, inspect, and replay decoder policy files in the repository; add a study README and tests for source extraction and code construction.
