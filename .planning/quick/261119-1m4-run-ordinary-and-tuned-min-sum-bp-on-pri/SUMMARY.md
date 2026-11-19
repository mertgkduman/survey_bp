---
status: complete
workflow: gsd-quick
---

The PriorTilt follow-up has 28 evaluations. Each of the 13 released XZ
strata and one released XYZ stratum gets ordinary min-sum and tuned BP.
Each decoder point uses 20 CPUs across its X- and Z-memory streams. Both
variants use an 18,080-sweep cap and stop at 20 observable errors or 100M
shots per memory basis.

The four tuning jobs select damping, scaling and offset at p=.003 using
separate shots. BB70 and GB102 use training-only circuits rescaled from
the released noise model, with verification against every released rate
in both bases. Evaluation uses the released circuits and sealed Stim
streams. The tuning procedure prioritizes logical errors and uses
iterations to select among finalists within one error of the minimum.

Initial array 62119759 had ordinary BP overflow on GB102 at p=.001 and
p=.002. Its results are archived under the campaign's local
`results/attempt-v1/`, including one fully audited point. The replacement
scales the messages, priors and offset together by a power of two when
their magnitude threatens float64 range. Each shot records its number
of rescale events. The replacement applies one numeric profile to all
28 points and uses the same immutable evaluation samples.

The overflow stress test passed the full cap for both variants. The
replacement also passed 24 bitwise neutral checks, a spawned-process
pilot for training, exact stopping, full ledger audits, resume and
publication. The original 84 regression cases passed. Pilot measurements
are separate from production.

Slurm replacement array 62119937 runs ordinary BP. Tuning jobs
62119938, 62119940, 62119942 and 62119944 select the settings before
tuned arrays 62119939, 62119941, 62119943 and 62119945. Collector
62119946 writes the audited report. Slurm verified 20 CPUs for each
of the 28 evaluation tasks. The original PriorTilt and RelayBP-5 XYZ
jobs continued on 50 CPUs each.

See [launch verification](verification.json), [the campaign guide](../../../data/reproductions/priortilt-2611-13373-bp/README.md)
and [the replacement dispatch receipt](../../../data/reproductions/priortilt-2611-13373-bp/dispatch.json).
