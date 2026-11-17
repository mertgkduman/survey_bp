---
id: 261117-fdl
mode: quick
status: complete
---

# Ten CPUs per remaining Fig1 point

User explicitly overrides the earlier one-CPU execution allocation. Preserve the frozen scientific plan, seeded shared input bytes, global-shot policy RNG, stopping, raw committed prefixes and completed results.

1. Add a separately versioned/pinned ten-process continuation controller without editing any frozen source. Decode independent source batches concurrently, commit each basis in original order and trim at the exact error target. Preserve speculative work separately and label timing cohorts. Parallelize full original-DEM/work/endpoint audits and record inherited prefixes.
2. Verify sequential/parallel scientific identity, global RNG/order, exact stopping, crash reuse, old-prefix preservation and completed-result compatibility. Freeze the resource amendment and actual changed-source/test hashes before dispatch.
3. Submit ten-CPU replacements, then stop only the superseded live workers and pending collector. Resume sealed prefixes and replace collector dependency. Inspect actual Slurm allocations/worker activity, update GSD and commit/push. Other collectors' pre-existing modified outputs remain untouched and unstaged.

Execution is inline; no subagents.
