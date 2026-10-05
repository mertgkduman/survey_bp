---
status: complete
quick_id: 261005-le8
date: 2026-10-05
---

# First CSS literature gate

Captured the approved three-paper gate in the roadmap, Phase 6 addendum, exploration note, and pending tasks. The selected source targets are Yao BPGD Figures 3/6, Bhatnagar impulse Figure 5, and Rabeti–Mahdavifar MBBP-LD Figure 5, all using B1 as a candidate shared code. The candidate repository B1 artifact is explicitly unqualified for source-faithful reproduction until each paper's experimental identity is checked.

Scaffolded 14 paper-root `.spec.toml` files with proposed kernel-readable policy roles, parameters, source/equation metadata, blockers, and non-runnable status. Each paper has a separate `paper_reproduction/PAPER.md` for experiment details and unresolved source choices. The gate calls for at least one qualified variant per paper through the common policy-file command on a bounded CSS study; full curve comparisons stay in later CSS campaign phases.

Implementation commit: `a6526e8`. Checks are recorded in `CHECK.md`.
