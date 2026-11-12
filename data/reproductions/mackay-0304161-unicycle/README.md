# MacKay Construction U BP campaign

The foundational paper is MacKay, Mitchison and McFadden,
[Sparse Graph Codes for Quantum Error-Correction](https://arxiv.org/abs/quant-ph/0304161v3)
(IEEE TIT, 2004). `source.json` pins its source archive and identifies the
construction and decoder passages. This initial campaign covers deterministic
Construction U, not every construction in the paper.

Frozen CSS inputs are [[74,18]] and [[274,110]], with every redundant cyclic
check retained and the extra all-one column. The smaller difference set is
explicit in the paper; the larger has a project-generated Singer ordering.
Ordered paired logicals are project derived. The published classical distances
are not claimed as quantum distances.

Three arms use the existing canonical float64 sum-product kernels:

- Ordinary binary BP on the full check graph, with undamped messages.
- The source's unicycle mechanism: fix the extra bit to each of 0 and 1,
  decode each conditioned syndrome, and select a syndrome-valid candidate by
  full error-pattern likelihood. Ties choose extra bit zero. Both branches'
  work is counted, including failed branches.
- Joint Q-BP, with V2C damping 0.1, no check cap, and p0=p.

Binary arms use X-only rates .04–.10 in steps of .01. Q-BP uses depolarizing
rates .060–.150 in steps of .015, matching either X/Z marginal, not the full
channel. Each shot allows at most 88,200 total sweeps: the unicycle arm divides
that budget into two caps of 44,100. Equal sweep ceilings do not equalize edge
work. This cap and our numerical conventions are controlled settings; they
are not specified by the source. The paper also studies independent X/Z noise
and classical block errors. Our results count quantum block failure including
syndrome mismatch and either nontrivial logical signature; there is no
paper-curve reproduction claim.

Every point stops at the contiguous iid prefix ending at 20 block failures or
100,000,000 shots. Both binary arms share physical samples at each rate.
Branch iterations, directed edge updates (both directions), decode runtime,
truth/syndrome/candidate hashes and outcomes are retained per shot. Logical
checks cover all 110 logical qubits for the larger code. Failure-target intervals
invert the negative-binomial stopping time; shot-cap intervals are exact
binomial. Zero failures retain their upper bound.

From the repository root:

```bash
export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
study=data/reproductions/mackay-0304161-unicycle
.venv/bin/python "$study/run.py" --list
.venv/bin/python "$study/submit.py" --test-only
.venv/bin/python "$study/submit.py"
```

An existing frozen plan refuses changed implementation or software. Dispatch is
idempotent, and each point resumes its checked gzip chunks under a file lock.
The dependent collector verifies every retained terminal ledger and replays
its first and last shot before publishing `verified.json` and `catalog.json`.
`results/` remains on HPC storage. To refresh terminal results during a run:

```bash
.venv/bin/python "$study/run.py" --collect
.venv/bin/python "$study/publish.py"
.venv/bin/python "$study/refresh_catalog.py"
```

The normalized catalog extension uses the workbench's shared multi-rate
filter. A new curve needs two distinct terminal rates to become visible.
