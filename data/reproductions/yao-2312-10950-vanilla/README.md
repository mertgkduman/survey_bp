# Vanilla BP on Yao et al. A5 and B2 codes

This study compares the Q-BP points in [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2),
Figures 7 and 8, with four canonical, undamped, float64 sum-product decoders.
The exact plotted Q-BP coordinates were transcribed from the authors' TeX into
[`source_points.json`](source_points.json). The paper states a 100-iteration
limit and collection until 100 error cases; source denominators and the full
Q-BP numerical implementation are not given. These local curves are therefore
**canonical adaptations**, not bitwise replications.

To inspect the plotted numbers, download the versioned `source_tex` URL in
`source_points.json`, verify its archive SHA-256 there, and inspect `main.tex`
lines 1755–1765 (A5) and 1838–1848 (B2). The source archive and extracted
`main.tex` hashes are recorded with the rates.

## Codes and decoder policies

| Code | Parameters | Construction |
| --- | --- | --- |
| A5 | `[[180,10]]` | BB exponents in the source paper; see [`codes/a5.json`](codes/a5.json) |
| B2 | `[[882,48]]` | generalized bicycle matrix from [Panteleev and Kalachev](https://arxiv.org/pdf/1904.02703v3); see [`codes/b2.json`](codes/b2.json) |

The code receipts pin semantic and matrix hashes. Every run verifies
dimension, commutation, logical basis, and these hashes before decoding.

| File | Kernel | Numerical policy | Prior |
| --- | --- | --- | --- |
| [`decoders/bp4_v1.json`](decoders/bp4_v1.json) | joint Pauli BP4 | historical float64 v1 | `(1-p,p/3,p/3,p/3)` |
| [`decoders/bp4_v2.json`](decoders/bp4_v2.json) | joint Pauli BP4 | float64 v2, damping disabled | `(1-p,p/3,p/3,p/3)` |
| [`decoders/binary_v1.json`](decoders/binary_v1.json) | separate X/Z binary BP | historical float64 v1 | each marginal `q=2p/3` |
| [`decoders/binary_v2.json`](decoders/binary_v2.json) | separate X/Z binary BP | float64 v2, damping disabled | each marginal `q=2p/3` |

All four use flooding, sum-product, `T=100`, and first syndrome-valid stopping.
The historical BP4 v1 kernel can return on an initial syndrome match; BP4 v2
always completes at least one sweep. Binary X/Z components stop separately.
The physical error on each qubit is sampled as I/X/Y/Z with probabilities
`1-p,p/3,p/3,p/3`; all four decoders receive the same error syndrome on a
given shot. They receive no access to the actual error. An independent
evaluator classifies syndrome failures (Type I), syndrome-valid logical
failures (Type II), exact successes, and stabilizer-equivalent successes.
The reported failure rate is **block** failure `(Type I + Type II)/N`.

## Result

The completed campaign contains **1,216,144 paired shots** across all 14
code/rate points. BP4 v2's local exact 95% interval contains the published
Q-BP point at 6/7 A5 rates and 2/7 B2 rates. On B2 its observed rate is lower
than the published point at 6/7 rates, by factors of roughly 0.71–0.88 there;
at `p=0.07` it is 1.03 times the source rate. BP4 v1 and both separate-binary
arms are outside the local intervals at every point. Every BP4 v2 failure was
a syndrome failure (Type I). The complete counts, intervals, paired outcomes,
and curves are in [`results/report.md`](results/report.md),
[`results/merged.json`](results/merged.json), and
[`results/curve.pdf`](results/curve.pdf).

The published source rates have their own sampling uncertainty and no reported
denominators. The B2 offset is a documented discrepancy, not evidence of a
specific defect in the paper's decoder; its full numerical conventions are
not available in the source.

V1 and v2 are the pinned numerical profiles described in the
[profile guide](../../../docs/numerical-profiles.md). V2 removes the global
message cap and uses a product boundary at `1-10^-10`; damping is set to zero
here even though the repository's usual v2 default may differ. The binary
baseline treats X and Z marginals independently; it does not preserve their
depolarizing correlation. See the [decoder-file guide](../../../docs/decoder-files.md)
for the distinction between these strict study JSON files and the general
`bp-registry --decoder` format.

## Campaign and files

[`campaign.json`](campaign.json) fixes 14 code/rate points, one sample stream
per point, and 128 shards. Each point's shot count was chosen **before local
results** as `ceil(125 / plotted source Q-BP rate)` to yield roughly 125
failures if the source rate holds. This is a fixed-shot campaign: there is no
outcome-dependent stopping. Each shard records all four arms per shot.

From the repository root, with the qualified Python environment installed:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-vanilla/run_task.py --index 0
PYTHONPATH=src python data/reproductions/yao-2312-10950-vanilla/analyze.py
```

`run_task.py` refuses to overwrite a shard and checks the campaign's hashes of
the decoder files and implementation. On the lab cluster, submit all shards
with `bash data/reproductions/yao-2312-10950-vanilla/submit.sh`. The campaign
is generated once by `plan.py`; it refuses to replace an existing campaign.
To change a decoder or sampling plan, copy the study to a new identity before
regenerating and retain this campaign's evidence. `analyze.py --partial` is
only for progress inspection; final comparison requires every shard.

Shard paths are `results/shards/<code>_p<percent>_<first-shot>/`. Each contains
`manifest.json`, `events.jsonl`, and `summary.json`. The ledger has one row per
physical error and four decoder outcomes. [`analyze.py`](analyze.py) verifies
ledger hashes, counts, policy and campaign identity, and sample stream
boundaries before writing [`results/comparison.csv`](results/comparison.csv),
[`results/merged.json`](results/merged.json),
[`results/report.md`](results/report.md), and PNG/PDF curves. Exact binomial
95% intervals refer to **local** failure rates. Whether a plotted source point
falls inside one is descriptive because the paper does not give its
denominator. Plot error bars show those local intervals; a downward triangle
marks a one-sided 95% upper bound when zero failures were observed. Paired
rescue/loss counts compare local arms on identical errors.

Full event ledgers remain in this HPC study directory; they are large and
excluded from Git. Tracked shard manifests and summaries retain their SHA-256
digests. The canceled preliminary campaign is documented under
[`results/aborted-60250663/ABORTED.md`](results/aborted-60250663/ABORTED.md)
and is excluded from the assessment.

The separate [BP4 tuning study at physical p=0.06](../yao-2312-10950-bp4-tuning-p006/README.md)
screens numerical and policy settings on A5 and B2, then measures selected
settings on independent fixed-shot error streams. Its tuned rates are not part
of the vanilla source comparison above. For a controlled tuned-versus-untuned
effect estimate, see its [paired equal-cap and mean-work follow-up](../yao-2312-10950-bp4-tuning-p006/fairness_t100/REPORT.md).
