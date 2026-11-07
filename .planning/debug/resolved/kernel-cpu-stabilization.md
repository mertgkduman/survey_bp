---
status: resolved
trigger: "Fix these in the correct order, optimize for performance as well, compiled speeds. See if you can develop further for CPU use, maybe not all policies but the comptaible ones for sure"
created: 2026-11-07
resolved: 2026-11-07T05:29:19Z
---

# Canonical kernel stabilization and CPU execution

Workflow: gsd-debug, inline under the skill's Codex spawn restriction.

## Evidence and expected behavior

The completed spikes 008–011 and CANONICAL-KERNEL-AUDIT.md establish seven findings against revision 3aacb2c. Historical probes and receipts remain unchanged. Correct decisions must maximize posterior mass; terminal work must retain committed work; admitted policies must execute their declared numerics; scalar and compiled boundaries must agree.

## Current focus

1. Correct decision and cumulative accounting; preserve historical profile and receipt replay.
2. Correct schedule composition, initialization, numerical policy admission and stable priors under explicit contracts.
3. Add compiled CPU batch execution for qualified flooding policies with independent shot state; reject unsupported combinations.
4. Run invariant, historical replay, backend differential and regression tests; benchmark warmed execution separately from compilation.

## Resolution

Corrected numerical profiles and public migrations implemented; legacy identities and capped receipts retained. Plain/transformed flooding now share one loop. Compatible compiled flooding policies have explicit stabilization, shared primitives, reusable tanh factors, linear min-sum reductions, and bounded CPU batching.

Broad validation: 984 passed, 1 skipped (canonical and research suites). Final affected-path validation after the shared-loop refactor: 276 passed. Historical artifact integrity verified against 3aacb2c. Final legacy-guard validation: 87 passed. Both new public examples execute/replay. Independent artifact validation verifies source hashes and 2,048 CPU ledger rows against original check matrices and work equations. Test sets overlap.

Qualified benchmark (`kernel-cpu-benchmark-qualified/report.json`, revision dfe0306): optimized compiled SPA is 2.78× faster on BB72 and 2.27× on GB46 versus pinned 3aacb2c, using frozen v2 for both sides and exact buffer/output assertions. Four-thread corrected-profile/policy batches give 1.22–1.36× over optimized single-shot calls on this shared host. Five warm repeats; first-call timings and all per-shot evidence retained. Earlier pilot measurements are preserved separately and are not the final benchmark.

Implementation commits: b0c02d5 (migration, accounting, shared stages, CPU optimization/batching); dfe0306 (frozen initialization and signed-zero guards).

All seven audit findings are addressed within the documented qualified routes. Historical numerical profiles remain selectable, including their source-specific behavior. Serial/transform scalar routes are qualified; batch execution is limited to eligible flooding compositions. Publication/source-curve gates and the paused HTML work remain unchanged.

See `docs/kernel-stabilization-and-cpu.md` for contracts, usage, exclusions, measurements and reproduction commands.
