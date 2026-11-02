# B1/C2 under depolarizing noise

This extension adds plain binary BP v2 and joint QBP v2 to B1 [[882,24]] and
C2 [[1922,50]] under depolarizing noise at p=0.04,0.05,...,0.10. It retains
the earlier X-only study as a separate channel experiment and combines its
new results with the audited A5/B2 depolarizing results for a four-code view.
There are no paper reference points for these new B1/C2 depolarizing curves.

Both arms use float64 flooding sum-product, no damping, T=100, first completed
syndrome-valid stopping, and the frozen v2 tanh-product numerical profile.
QBP receives P=(1-p,p/3,p/3,p/3) in I/X/Y/Z order. Separate binary decoders
receive q_X=q_Z=2p/3. The physical p is never replaced by a binary marginal
inside the noise sampler. Both arms decode every identical sampled error.

`decoders.json` uses the strict `paired-depolarizing-plain-bp-v1` schema,
consumed by `study.policies()` and `run.py`; it is not a file for the general
`bp-registry --decoder` command. The campaign manifests pin policy and source
hashes. Existing policy files and X-only manifests remain unchanged.

## Sampling and precision

`pilot.json` freezes 2,000 paired shots per code/rate point. Only pilot data
choose the follow-up size: min(1,000,000,max(20,000,ceil(400,000/k))), where k
is the smaller arm's pilot failure count. Zero pilot failures select one
million shots. `campaign.json` fixes every fresh cohort before it runs, with
separate pilot/follow-up seed namespaces and disjoint 50,000-shot shards.
Pilot samples never enter final estimates or confidence intervals.

The fixed denominator admits exact Clopper–Pearson 95% intervals, including
the exact one-sided upper bound 1-0.05^(1/N) for zero failures. Estimates with
1–99 failures remain labeled `low_count_estimate`; zero failures remain an
upper bound, not a plotted nonzero rate or a completed 100-failure estimate.
The one-million-shot ceiling fixes the achievable rare-point resolution in
advance. No local curve point is replaced by a source value or interpolation.

## Execution and evidence

`run.py` emits a manifest, line-buffered shot ledger and hashed summary for
each shard, then losslessly compresses the completed ledger. Timing order
rotates between the two arms. Corrections are independently checked against
the original code, using separate X/Z logical signatures. Type I denotes an
inconsistent syndrome; Type II denotes a matching syndrome with a nontrivial
logical residual. Exact and stabilizer-equivalent recovery are successes.
Zero-syndrome samples and every nonconverged output enter the denominator.

`assess.py` verifies all hashes, requested/resolved priors, shot counts,
disjoint boundaries, physical errors and syndromes. Its independent syndrome
evaluation uses a sparse column traversal checked against dense Pauli algebra.
Boundary/fixed-stride corrections and all Type II events are replayed with a
separate logical-signature evaluator. Counts, iterations and times are
recomputed from every shot. Existing A5/B2 CSV hashes are checked against
their completed independent audit before importing those rows.

Run from the repository root in a compute allocation:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/campaign.py pilot
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/campaign.py followup
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/depolarizing/assess.py
PYTHONPATH=src pytest -q tests/test_yao_b1c2_depolarizing.py
```

Freeze/dispatch commands refuse an existing plan. Wait for every pilot to
finish before freezing the follow-up. To rerun one frozen shard into an
absent output directory, use `run.py --plan <absolute-plan-path> --index N`.
The two dispatch receipts record Slurm arrays, one CPU and 4 GiB per task,
three-hour wall limits and at most 24 simultaneous tasks. These commands do
not overwrite existing evidence.

Final artifacts live under `results/`: `all_depolarizing.csv` covers both
plain decoders on all four codes; `performance.csv` contains new B1/C2 rates,
failure types, precision labels, mean/p99 iterations, work and timing;
`paired.csv` contains rescues/losses and conservative paired intervals;
`REPORT.md`, `comparison.png` and `comparison.pdf` summarize the experiment.
The fixed-N rate intervals and paired difference intervals answer different
questions. Timing comparisons between historical A5/B2 and new B1/C2 campaigns
do not isolate hardware-independent decoder speed.
