# Policy-composable BP4 execution profile

## Change and scope

The production Python quaternary paths now reuse immutable graph incidence for transformed flooding, transformed variable-serial, MBP4 flooding, and MBP4 variable-serial. Both flooding variants also quantize each edge's old V2C message once per complete snapshot before forming excluded-neighbor messages. Every C2V message still performs its own ordered check reduction, then the declared transform or fixed-alpha recurrence. Serial variants continue to evaluate each check against the V2C state visible at that variable's turn. Budget reservation, work accounting, snapshots, and ledger-facing interfaces are unchanged.

This optimization applies to the supported quaternary policy compositions. It does not add an unqualified compiled policy backend or assert compatibility across binary, quaternary, and future circuit kernels.

## Exact matched profile

`scripts/benchmark_quaternary_policy_sweeps.py` measured two successive sweeps for each path, three fresh-session repetitions each, on one seeded GB46 syndrome with 352 edges. The runs used host `dcc-core-ferc-u-ab39-5-6`, CPU 56 affinity, and one OMP/OpenBLAS/MKL thread. Medians exclude session construction and use the same code, syndrome, priors, α=1.5, and normalization-plus-offset transform before and after.

| Policy path | Before ms/sweep | After ms/sweep | Speedup |
|---|---:|---:|---:|
| Transformed BP4 flooding | 163.419 | 68.061 | 2.40× |
| Transformed BP4 variable-serial | 170.175 | 164.558 | 1.03× |
| MBP4 fixed-α flooding | 167.708 | 71.777 | 2.34× |
| MBP4 fixed-α variable-serial | 168.391 | 167.393 | 1.01× |

The retained [before](./before.json) and [after](./after.json) records match exactly on host, affinity, source and syndrome hashes, and every sweep's candidate, C2V, V2C, belief, marginal, terminal, convergence, and work record. Final session state digests also match. This is deterministic development evidence for one representative graph and policy setting, not a population performance estimate or a publication reproduction claim.

## Robustness checks

The new regression test compares each flooding C2V message against an independent per-edge exclusion calculation on a commuting mixed-Pauli graph with a disconnected variable. It also checks one quantization call per edge, unchanged named work, and MBP4 replay. Focused policy and public-execution tests passed **48/48**. The broader quaternary suite produced **188 passed, 7 failed**; all seven failures require missing external `/tmp` fixtures (`/tmp/phase11-mbp4.pdf` or `/tmp/phase10-asced-native/source/quantum_asced/CMakeLists.txt`) and occur before the changed execution paths. Python compilation and `git diff --check` passed.

The serial paths show little timing change because their current-message freshness prevents a whole-sweep quantization cache. Further acceleration should keep this distinction explicit; applying flooding cache semantics to serial schedules would change the algorithm. Whole-campaign throughput, other graph families, and HPC site resource ceilings remain separate qualification work.
