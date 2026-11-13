# BP and Q-BP damping at inferred T=100

This replaces the canceled 88,200-iteration damping study. All ordinary binary
SP and joint Q-BP SP decodes have a **100-iteration ceiling**, on both MacKay
codes and all five source / 1.5x depolarizing rates. The budget is inferred from
curve alignment, not recovered from an explicit historical source setting.
It is recorded in ../mackay-0304161-inferred-budget/budget.json.

Old-message damping grid: 0/.1/.3/.5/.7/.85/.95. Every candidate receives the
same 1,024 fixed physical samples per rate, new tuning seed 2026111321. Select
one damping per code/family across the five-rate curve. Primary score is equally
weighted mean block LER; exact score ties choose ascending damping for the
reference. A faster candidate is eligible only when simultaneous paired
risk-regret bounds are within 10% of the reference empirical LER. Bounds use
exact positive/negative discordance tails per rate with Bonferroni coverage over
all ordered pairs, groups, rates and tails (alpha=.05). Overlapping intervals
never prove similarity; zero empirical reference risk gives zero margin.

Fresh confirmation (seed 2026111323) evaluates the selected and original
settings (binary 0/Q-BP .1), each at T=100, with 20 quantum block failures or
100 million shots. Identical selected/baseline configurations are run once.
No training data are pooled or published as independent results. Mean actual
iterations and directed edge updates are both retained. Selection is provisional
and holdout summaries do not automatically assert superiority.

The preceding fresh inferred-budget baseline audit submits this study. Tuning
audit freezes confirmation before sampling; successful confirmation audit then
submits the already-frozen Roffe T=n study. Missing or failed evidence prevents
advancement. At most 16 tuning CPUs or 32 confirmation CPUs execute. All
manifests, contiguous ledgers, work, outcomes, hashes and endpoint replays are
audited. Canonical kernels and all historical evidence remain unchanged.

Commands (PYTHONPATH=src, OMP/BLAS=1):

```
.venv/bin/python data/reproductions/mackay-0304161-damping-t100/run.py --freeze
.venv/bin/python data/reproductions/mackay-0304161-damping-t100/run.py --test-only
.venv/bin/python data/reproductions/mackay-0304161-damping-t100/run.py --submit
.venv/bin/python data/reproductions/mackay-0304161-damping-t100/run.py --collect
```

Do not submit separately while the preceding pipeline is active. Repeated
submissions use the existing locked scheduler receipts.
