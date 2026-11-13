# MacKay BP and Q-BP damping

Ordinary binary SP and joint Q-BP SP on both [[74,18]] and [[274,110]] codes.
The unicycle two-hypothesis decoder stays a separate source reference. Retain
88,200 total iterations per shot, the existing float64-v2 profiles, no check cap,
matched prior, and binary rates .010/.013/.020/.030/.040. Q-BP depolarizing rates
are exactly 1.5 times those rates, preserving marginal X/Z error probability.
These channels answer different questions; their block LERs are not identical
metrics on the same noise model.

Damping d is old-message weight: new = d*old + (1-d)*proposal. Prespecified grid:
0, .1, .3, .5, .7, .85, .95. Every setting receives the same 1,024 fixed samples
per rate (shared across damping at that code/family/rate), seed 2026111307.
One damping is selected per code/family for the whole five-rate curve.

Primary score is mean block LER across five equally weighted rates. Secondary
score is mean actual executed iterations. The empirical minimum-LER candidate
is the reference. A faster candidate is eligible only if its paired risk-regret
upper bound is <=10% of the reference LER. Bounds use exact per-rate discordance
probability limits with Bonferroni coverage over all ordered candidate pairs,
four groups, five rates and both tails (familywise alpha .05). This remains
valid for the data-selected reference. Overlapping intervals do not establish
similarity. If no faster candidate qualifies, retain the empirical LER minimum;
that tuning choice is provisional. A zero-risk empirical reference has zero
similarity margin. All grid evidence and candidate scores remain available.

Fresh confirmation uses seed 2026111309, selected and original settings (binary
0, Q-BP .1), 20 quantum block failures or 100,000,000 shots at each rate. When
selection equals baseline, run one shared arm. No training data are pooled into
confirmation and no superiority is asserted by the selector. Holdout candidates
share physical streams but stopping prefixes may differ. Retain counts, exact
stopping intervals, both iteration and directed-edge averages, and full ledgers.

The frozen pipeline audits tuning, freezes selection and confirmation before
sampling, submits confirmation, audits/publicizes it, then submits the Roffe
standalone-BP/Q-BP study. Missing/failed points prevent automatic advancement.
Each stage is resumable and refuses changed manifests. At most 16 tuning CPUs
or 32 confirmation CPUs are active. Workers retain ordered prefixes; unused
speculative rows are excluded. No kernel is modified.

Commands (PYTHONPATH=src and BLAS/OMP threads=1):

```
.venv/bin/python data/reproductions/mackay-0304161-damping/run.py --freeze
.venv/bin/python data/reproductions/mackay-0304161-damping/run.py --test-only
.venv/bin/python data/reproductions/mackay-0304161-damping/run.py --submit
.venv/bin/python data/reproductions/mackay-0304161-damping/run.py --collect
```

Do not edit a frozen study or reuse its output identity for a changed design.
