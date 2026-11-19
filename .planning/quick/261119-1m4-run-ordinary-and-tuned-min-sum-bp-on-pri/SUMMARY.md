---
status: complete
workflow: gsd-quick
---

The PriorTilt BP follow-up has 28 submitted evaluations. Each of the 13
released XZ strata and one released XYZ stratum gets ordinary min-sum and a
tuned variant, with 20 CPUs for each decoder point and an 18,080-sweep cap.
The cap and observable stopping rules apply to both variants. The X and Z
memories share each allocation and retain their own exact stopping prefixes.

The four tuning jobs select damping, scaling and offset at p=.003 using
separate training samples. BB70 and GB102 use training-only rate rescaling
verified against every released rate in both bases. The evaluation circuits
and sealed Stim evaluation streams match the parent studies. The tuning
procedure retains the neutral setting, prioritizes logical errors and uses
iterations to select among finalists within one error of the minimum.

Twenty-four probes match the existing ordinary canonical decoder bitwise for
candidates and posterior values, with the same stopping and iteration work.
The spawned-process pilot exercised tuning, evaluation, exact error prefixes,
full ledger audit, resume and audited-only publication. All 84 existing
regression cases passed. Pilot measurements are separate from production.

Slurm submitted ordinary array 62119759, tuning jobs 62119760, 62119762,
62119764 and 62119766, tuned arrays 62119761, 62119763, 62119765 and 62119767,
and collector 62119768. The launch check found 13 ordinary XZ points running
at 20 CPUs each, with sealed progress observed. The ordinary XYZ point and
tuning jobs were queued at the account CPU limit. Tuned points depend on
their own group's selection job. The two previously launched XYZ jobs
continued on 50 CPUs each. Audited production measurements were pending at
the launch check.

See [verification](verification.json), [the campaign guide](../../../data/reproductions/priortilt-2611-13373-bp/README.md)
and [the dispatch receipt](../../../data/reproductions/priortilt-2611-13373-bp/dispatch.json).
