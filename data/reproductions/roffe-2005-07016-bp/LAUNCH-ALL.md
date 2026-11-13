# User-authorized scheduling override

The user requested: "Move to Roffe with a CPU for every point."

Use `launch_all.py --submit` to launch the existing218 frozen points as an array
with218 available one-CPU slots. Every point still has one simulation worker;
OMP/OpenBLAS/MKL each use one thread. Slurm places tasks subject to availability.
The prior16-task cap and serial wait described in frozen README.md are
superseded by this explicit scheduling instruction. Frozen scientific files
remain unchanged, including the original run.py used by every worker.

This launcher uses the same dispatch lock and `dispatch.json` array/collect
keys as the original submitter. The still-active MacKay continuation will reuse
these jobs when it finishes auditing/publishing its own results; it will not
create another Roffe array. MacKay's remaining four-CPU job stays running.

The complete-array collector requires all218 points and performs the existing
full-ledger validation and publication. Source-specific rates, min-sum rule,
alpha schedule, T=n, seeds and20-failure/100M stopping remain exactly as frozen.
Launch receipts do not establish completed measurements or paper agreement.

```
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-bp/launch_all.py --test-only
PYTHONPATH=src .venv/bin/python data/reproductions/roffe-2005-07016-bp/launch_all.py --submit
```
