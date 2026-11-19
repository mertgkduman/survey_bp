# BP kernel tuning for PriorTilt, RelayBP and BeamSearch

The anchors are BB144 at p = 0.003 and BB70 and GB102 at p = 0.001. The
study has nine XZ points and two XYZ points. The XYZ points are the two
methods at the released BB144 Table 4 anchor. Each screen, tuning and
confirmation job requests 20 CPUs across its X and Z memories.

| Mode | Controller | Preserved budget |
|---|---|---:|
| XZ | PriorTilt | 60 + 3,000 × 6 = 18,060 |
| XZ | RelayBP-1 | 80 + 300 × 60 = 18,080 |
| XZ | BeamSearch | 40 + 10 × 30 = 340 per path, width 32 |
| XYZ | PriorTilt | 60 + 6,000 × 6 = 36,060 |
| XYZ | RelayBP-5 | 80 + 600 × 60 = 36,080 |

The study varies the old-message weight in V2C damping, min-sum scaling
and check offset. Each candidate uses the existing canonical float64
sweep and its paper controller with the source stopping, reset, memory,
perturbation, branching and candidate rules. A bound of 2^480 on extreme
outgoing messages preserves finite arithmetic during divergent sweeps.
The number of protected messages is recorded in a reserved per-shot trace
trailer. The bound retains the same units across branches, offsets and
relay legs. Neutral probes exercise the ordinary finite range.

Tuning starts with nine damping values from 0 to 0.70. It then tests
scaling from 0.75 to 1 and offsets 0 and 0.5 at the two leading damping
settings. The finalists and neutral reference share a disjoint third
round. Selection minimizes observable errors. Among finalists within one
error of the minimum, fewer directed edge updates takes precedence.

Screening draws samples from the exact released circuits at each anchor,
then selects syndromes on which a 40-sweep ordinary BP attempt fails to
converge. Each tuning round uses an equal number of X and Z memory shots,
with identical inputs and policy RNG seeds across candidates. Training
counts describe this hard cohort. The plan binds the screening limit,
random seeds, source circuits and deterministic quotas.

The chosen settings enter an independent unfiltered confirmation using
the sealed parent evaluation stream and parent policy seeds. Each memory
stops at 20 observable errors or 100 million shots. The report records
LER per syndrome cycle, pointwise intervals, nonconvergence and work.
The collector uses completed fresh audits. The original reference runs
keep their existing configurations and reports.

- [XZ reference results](../priortilt-2611-13373/RESULTS.md)
- [XYZ reference results](../priortilt-2611-13373-xyz/RESULTS.md)
- [Paper reference](https://arxiv.org/html/2611.13373v1)
