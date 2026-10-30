---
status: in_progress
date: 2026-10-30
---

# Complete the Yao BP/BPGD reproduction

Keep only BP and BPGD curves from Figures 2–8, excluding BP-OSD and imported BP-SI. Preserve the original pinned source extraction as an archive receipt while making the comparison table and plot strictly about locally implemented BP/BPGD methods.

1. Audit missing and low-count points, source settings, current runtime, and scheduler capacity. Prespecify the precision and stopping standard for each target, including a defensible treatment of rare-event points.
2. Improve restartable, parallel execution where needed without changing decoder semantics. Qualify any speed optimization against the frozen runner on matched shots.
3. Run the remaining BP/BPGD source points and sharpen measured points to the prespecified precision; retain complete per-shot or exact sufficient-statistic evidence with manifests and interruption recovery.
4. Verify all results, regenerate tables/plots/report, document any source ambiguity and irreducible gap, update repo instructions and GSD state, and commit atomically.
