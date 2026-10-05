---
status: complete
quick_id: 261005-fze
date: 2026-10-05
---

# Matched BB72 BeamSearch and RelayBP campaign published

Prespecified BB72 X-only CSS selection and evaluation used separate sample namespaces. Both methods shared the initial BP result per shot, then ran across three extra-iteration profiles and damping gamma 1.0/0.5 under an 8,640 additional C2V cap. Selection used 128 physical shots per noise rate; evaluation used 512 shots at p=0.05 and 1,280 at p=0.08. All six selection shards, the selection lock, all six evaluation shards, deterministic evaluation replay, and package verification passed.

The source-sealed report and all 12 compressed shot ledgers are in `data/results/fair-beam-relay-css-v2/`. GitHub `main` contains the package at `3db441ec8048317b966db21c4d40b46f43cda5c1`; the merged checkout passed `verify-package` and the focused end-to-end test.

At gamma 1.0, selected RelayBP had fewer failures than BeamSearch: 96 versus 232 of 512 at p=0.05, and 643 versus 1,030 of 1,280 at p=0.08. Both paired Holm-adjusted tests passed 0.05. At gamma 0.5, selected failure counts were 81 versus 82 of 512 and 584 versus 590 of 1,280 (RelayBP versus BeamSearch); both paired comparisons were inconclusive. These are controlled CSS adaptations, not circuit-paper reproductions. Phase 6 replanning and broader code/circuit comparisons remain open.
