# Direct B1 and C2 BPGD and Q-BP sweeps

[Figures 3, 5, and 6 of Yao et al.](https://arxiv.org/html/2312.10950v2)
define the BPGD reference curves and their seven X-only rates from 0.04 to
0.10. B1 uses T=100 with R=2, 5, 10, 50, and 882, plus T=1, 10, and 70
with R=882. C2 uses T=10 and R=1922. The T=100, R=882 B1 results link
to both figures. These runs use the existing compiled paper-style sum-product
BPGD interpretation.

Plain sum-product Q-BP uses float64 v2 with d=0.1, no check cap, and p₀=p.
The depolarizing rates are 0.060, 0.075, 0.090, 0.105, 0.120, 0.135, and
0.150. At depolarizing rate p, either marginal has error probability 2p/3.
The per-shot iteration caps are 88,200 for B1 and 19,220 for C2. Equal sweep
caps can entail different amounts of work across the two decoder families.

Each point retains the contiguous iid prefix ending at 20 block failures or
100,000,000 shots. Block failures include syndrome mismatches and
syndrome-valid residuals that act nontrivially on at least one logical qubit.
Q-BP checks the two logical signatures separately. BPGD arms at the same
code and rate use the same shot stream. Parallel workers on rare points may
evaluate batches ahead of the terminal shot. The estimate and its confidence
interval use the ordered prefix, and all requested shot indices stay below the
cap. The frozen plan pins source figures, code hashes, runner and kernel hashes,
decoder settings, rates, seed, and stopping thresholds.

From the repository root:

```bash
export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
study=data/reproductions/yao-2312-10950-bpgd-completion
.venv/bin/python "$study/run.py" --list
.venv/bin/python "$study/submit.py" --test-only
.venv/bin/python "$study/submit.py"
```

Dispatch receipts and Slurm logs are in `results/`. After a task exits, its
same index can resume from committed gzip chunks. The dependent collection job
checks the shot sequence, ledger hash, counts, stop condition, and endpoint
replay, and builds a new workbench catalog. It collects terminal points even if
a different point failed. To refresh before the array finishes, run
`run.py --collect` and `refresh_catalog.py` in the same environment.
`results/verified.json` carries the summary digests and retained counts.
The raw ledgers stay on HPC storage.
