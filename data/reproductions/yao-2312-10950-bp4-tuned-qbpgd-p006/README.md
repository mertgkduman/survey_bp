# Tuned BP4 inside four-state Q-BPGD at physical p = 0.06

This controlled development study applies the selected A5 and B2 BP4
profiles from the [BP4 tuning study](../yao-2312-10950-bp4-tuning-p006/README.md)
inside the persistent-message four-state Q-BPGD controller. The decoder sees
only the syndrome and its configured prior; an independent CSS evaluator uses
the sampled physical error to classify exact, stabilizer-equivalent, Type I,
and Type II outcomes. The result is a **canonical adaptation**, not a
source-faithful claim about an unpublished author implementation.

## Decoder files

The data-only [A5](decoders/a5.json) and [B2](decoders/b2.json) policy files
pin the selected BP4 file hashes and the Q-BPGD parameters. These files are
consumed by this study's `run.py`; they are not public `bp-registry --decoder`
files. Each run manifest records effective numerical profiles and hashes of
the selected BP4 file and implementation sources.

| Code | Arm | Decoder prior p0 | Float64 BP4 | Old V2C weight d | Q-BPGD |
| --- | --- | ---: | --- | ---: | --- |
| A5 | control | 0.06 | v2 SPA, no check cap | 0 | 10 sweeps/round, epsilon 1e-10, at most 180 rounds |
| A5 | tuned | 0.005 | v2 SPA, no check cap | 0.2 | same |
| B2 | control | 0.06 | v2 SPA, no check cap | 0 | 10 sweeps/round, epsilon 1e-10, at most 882 rounds |
| B2 | tuned | 0.15 | v2 SPA, no check cap | 0.1 | same |

Both BP4 profiles use product-unity safeguard `1e-10`, strict I/X/Z/else-Y
hard decisions, and full float64 message resolution. V2C damping is
`d * old + (1-d) * fresh`. Q-BPGD continues the committed V2C buffer after
each one-qubit prior fixation. The selected standalone BP4 iteration caps
(A5 10,000; B2 5,000) do not apply: Q-BPGD fixes its own ten-sweep blocks and
checks the original syndrome after each block. A final fixation at the round
limit is not followed by an extra block, matching the current controller.

## Fixed-shot results

Physical errors were sampled independently for each code using PCG64 seed
`20261030`; both arms of a code decoded identical errors. The separate
1,000-shot seed `20261029` pilots remain in `results/` and are not pooled into
this table. Intervals are two-sided exact 90% binomial intervals for each
block-failure rate.

| Code | Arm | Type I | Type II | Failures / 10,000 | 90% interval | Mean BP4 sweeps | Mean fixations |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A5 | control | 12 | 0 | 12 | [0.000693, 0.001944] | 13.445 | 0.3457 |
| A5 | tuned | 6 | 1 | 7 | [0.000329, 0.001314] | 11.561 | 0.1567 |
| B2 | control | 2 | 0 | 2 | [0.0000355, 0.000629] | 14.409 | 0.4411 |
| B2 | tuned | 1 | 1 | 2 | [0.0000355, 0.000629] | 12.191 | 0.2192 |

A5 has 8 paired rescues and 3 losses; the exact two-sided paired sign test
gives `p=0.2266`. B2 has no discordant failures. Thus these data establish
lower mean sweep and fixation counts, while the accuracy difference remains
unresolved. The A5 Type I failures all reached the 180-round cap after 180
fixations; the tuned A5 Type II failure had a valid syndrome. Both B2 failures
are shared, although their Type I/II classification differs between arms.
Elapsed time is retained per shot but may reflect simultaneous jobs on the
shared HPC node; sweep counts are the stable work comparison.

## Run and inspect

```bash
OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python \
  data/reproductions/yao-2312-10950-bp4-tuned-qbpgd-p006/run.py \
  --code a5 --shots 10000 --seed 20261030 \
  --output /path/to/new/a5-result
```

Use `--code b2` for B2. The runner refuses to overwrite an existing output.
Each result directory has a manifest, per-shot JSONL event ledger, and summary.
The ledger contains error and syndrome hashes, both arm outcomes, correction
hashes, sweep and fixation counts, and paired rescue/loss status. The
`CompiledBp4Graph.run_qbpgd` development backend is parity-tested against the
canonical `QbpgdController` for v2 profiles, damping, round counts, fixations,
and candidate decisions on a two-qubit fixture. This is a local controlled
comparison; it does not close the separate Figure 7 source-review or
publication campaign gates.
