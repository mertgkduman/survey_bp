---
status: complete
workflow: gsd-quick
---

Add ordinary and tuned min-sum BP to the 13 XZ code/rate strata in Fig. 1 and the single XYZ stratum in Table 4. Each of the 28 decoder points gets 20 Slurm CPUs shared between its X- and Z-memory runs. Use 18,080 maximum sweeps for both tuning and evaluation.

Use identical released evaluation circuits and the observable LER metric. Tune damping, check scaling and check offset once per code and detector mode at p=.003. For BB70 and GB102, derive training-only circuits after checking that gate targets, circuit structure and per-instruction noise ratios agree across the released grid. Keep tuning seeds disjoint from evaluation. Use equal shot denominators for each candidate within a tuning round. Select by logical errors, with mean sweeps as the secondary criterion. Seal the selected policy before running the final points.

Reuse the canonical min-sum sweep and existing ordered evidence processing. Validate neutral BP against the existing ordinary sweep, verify all circuit bindings, and exercise the new worker, stop and reporting logic on bounded fixtures. Freeze the plan, launch baseline and tune jobs, queue the tuned evaluations and collectors, and verify dispatch and progress. Preserve both earlier studies and the unrelated worktree changes.

The initial ordinary BP rollout hit float64 overflow in the GB102 workers at
p=.001 and p=.002. Archive its progress and results and retry the whole new
campaign with the versioned range guard. Scale the current messages, original
prior contribution and offset by the same power of two, then continue the
canonical sweep. Verify the ordinary and tuned variants to the full requested
cap on a divergent fixture and repeat the existing neutral and worker checks.
Keep per-shot rescale counts for analysis. Start the replacement from the
same frozen Stim samples with no change to the stopping definitions.
