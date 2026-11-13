# MacKay reference with an inferred short iteration budget

The historical paper does not state its numeric iteration cap. Retrospective
alignment against all five source points favors **100 iterations per unicycle
hypothesis** among 11 tested values (2 through 1,000); 50 is also plausible.
This is an inferred setting, not an explicit author/paper specification.

The calibration uses existing large-budget ledgers. Final exact-success cases
have a known first-convergence time on the true-extra-bit branch: before that
time, another branch cannot return the transmitted classical word. Existing
failure cases and skipped-competitor ambiguities were replayed with at most
1,000 iterations per branch. All original ledger hashes were checked. Because
the bank originally stopped at 20 large-budget quantum failures, projected
counts are descriptive calibration; no confidence interval from that stopping
rule is transferred to the new cutoffs. See ../mackay-0304161-budget-calibration/.

Fresh validation keeps both existing codes, original five binary rates and
1.5x matched-marginal depolarizing rates, SP float64-v2, no extra check cap and
matched priors. Ordinary BP and Q-BP each use **T=100**. The source unicycle
controller uses **100 per conditioned hypothesis, at most 200 total**; this
extra branch work is explicitly counted and is not called a 100-total-sweep
controller. It uses the previously qualified exact candidate certificate.

Every point stops at 20 quantum block failures or 100 million shots using new
seed 2026111317. Source classical block errors are retained separately. Only
length-274 unicycle results are compared directly to the source curve. A
classical confidence interval is not borrowed when quantum/classical counts
differ. All event ledgers, independent original-code outcomes, work averages,
hashes and endpoint replays persist. The older 88,200 curves remain public
and are never pooled with these configurations.

The final audit publishes this separate inferred-budget dataset, then submits
the new T=100 damping grid. Its fresh confirmation later submits the unchanged
Roffe T=n study. The former oversized damping array and advance job are canceled
and retain STOPPED.json. A failure or missing point prevents advancement.
Maximum concurrent allocation here: 60 CPUs (12 one-CPU, four four-CPU and two
16-CPU tasks). No canonical message-update implementation has changed.

Commands, with PYTHONPATH=src and OMP/BLAS threads=1:

```
.venv/bin/python data/reproductions/mackay-0304161-inferred-budget/run.py --freeze
.venv/bin/python data/reproductions/mackay-0304161-inferred-budget/run.py --test-only
.venv/bin/python data/reproductions/mackay-0304161-inferred-budget/run.py --submit
.venv/bin/python data/reproductions/mackay-0304161-inferred-budget/run.py --collect
```

Do not alter a frozen plan or merge retrospective calibration with independent
validation. Inspect scheduler receipts and audits before claiming completion.
