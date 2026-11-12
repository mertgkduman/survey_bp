# MacKay BP at the paper's error rates

This replaces the earlier .04–.10 interval in the active workbench with the
five measured rates of the paper's length-274 unicycle plot:
**.010, .013, .020, .030, .040**. `source_points.json` pins the source archive,
PostScript figure and its integer plotting coordinates. Approximate extracted
ordinates are comparison targets, not raw author counts.

Both existing Construction U codes and the three BP arms are retained. Binary
arms use those five X-only probabilities. Joint Q-BP uses matched-marginal
depolarizing probabilities **.015, .0195, .030, .045, .060**. Each of the 30
points stops at 20 quantum block failures or 100,000,000 shots. Numerical
settings and the maximum 88,200 total sweeps are unchanged. The prior experiment
and its data remain immutable and available as historical evidence.

The source comparison is the length-274 unicycle-SP arm. Other arms are
controlled comparisons. Ledgers also count classical block errors: quantum
failures plus stabilizer-equivalent recoveries. A classical confidence interval
is not inferred from the quantum-failure stopping rule if these counts differ.

## Certified branch bound

The cyclic matrix C is the incidence matrix of a projective plane of order
q=8 or 16: columns have weight q+1 and distinct columns overlap once. With
the extra all-one column, every nonzero word in ker([C,1]) has weight >=q+2:

- If its extra bit is zero, choose any support point. Each of the q+1 lines
  through it needs another support point for even parity. Each other point
  covers one of those lines, so at least q+2 points are needed.
- If its extra bit is one, every line contains a support point. Counting
  incidences gives at least ceil((q²+q+1)/(q+1))=q+1 support points, plus the
  extra bit.

The majority of the observed syndrome chooses the first hypothesis. The two
branches have independent state, so their execution order cannot change either
branch's output. For a pattern of total weight <=q/2, incidence counting also
shows that this majority identifies the actual extra bit. No hidden truth is
used. Branch counters always retain [extra=0, extra=1] order.

Thus the distance lower bounds are 10 and 18. If the first hypothesis returns
a valid candidate of weight w with 2w below the bound, any other valid
candidate must have weight at least d_min-w>w. For p<1/2 it cannot have greater
likelihood. Only then may the second hypothesis be skipped. Otherwise both
branches execute, including the distance-bound boundary and ties.

This preserves the selected correction of the original two-hypothesis decoder.
The skipped branch records zero iterations and zero directed updates; all
executed work is retained. The controller identity declares the optimization
and its work is never pooled with the old unpruned arm. No BP kernel changes.

## Execute and audit

```bash
export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
study=data/reproductions/mackay-0304161-paper-rates
.venv/bin/python "$study/run.py" --list
.venv/bin/python "$study/submit.py" --test-only
.venv/bin/python "$study/submit.py"
```

The frozen plan refuses implementation/software changes. Process workers
evaluate bounded batches of independent shot indices. Only the contiguous
prefix ending at the stopping condition contributes to the estimate and work
averages. In-flight speculative rows can be discarded; indices remain below
the cap. Atomic gzip chunks, manifest checks and locks support safe resume.

The dependent collector checks all terminal ledgers, work counters, counts,
digests and endpoint replay before publication. For a manual refresh:

```bash
.venv/bin/python "$study/run.py" --collect
.venv/bin/python "$study/publish.py"
.venv/bin/python "$study/refresh_catalog.py"
```

Paper-rate evidence has its own dataset and sampling role. The old interval is
retired from public v2 plots, selectors, tables, exports and availability through
the same active-view projection. The two-measured-rate eligibility rule still
applies. Raw catalogs, historical ledgers and archived v1 remain intact.
