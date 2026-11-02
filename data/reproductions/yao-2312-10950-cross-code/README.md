# Missing plain-decoder baselines for the Yao codes

This controlled study supplies plain binary BP on A5/B2 and plain quaternary
BP (QBP/BP4) on B1/C2, which are absent from
[Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2).
The same paper's existing plain decoder on each code supplies the iteration
limit: **T=100 for all four codes**. Guided-decimation block lengths are not
standalone iteration caps. All runs use undamped float64 flooding sum-product.

| Code | Physical channel | Missing arm | Prior supplied to that arm |
|---|---|---|---|
| A5 [[180,10]] | Depolarizing p | Separate binary BP | q_X=q_Z=2p/3 |
| B2 [[882,48]] | Depolarizing p | Separate binary BP | q_X=q_Z=2p/3 |
| B1 [[882,24]] | X-only p | Joint QBP | (1-p,p,0,0) |
| C2 [[1922,50]] | X-only p | Joint QBP | (1-p,p,0,0) |

The rates p=0.04,0.05,...,0.10 match each code's paper grid. Channels are
preserved, so the study does not isolate code quality across different channels.
There is no published reference point for the missing arm. Existing source
curves and new controlled measurements retain separate labels.

## Executable policies and design

`decoders.json` is a strict data-only policy file read by `common.policies()`.
It records the check rule, schedule, resolution, damping, numerical safeguards,
iteration cap, and X-only prior representation. This study-specific schema is
not accepted by the public `bp-registry --decoder` command. See
[decoder-files.md](../../../docs/decoder-files.md) for that separate interface.
Changing a policy requires a fresh campaign identity; existing output folders
are never overwritten.

The B1/C2 `run.py` executes the full joint Tanner graph through the existing
compiled QBP v2 kernel. Because its public prior interface requires positive
probabilities, the experiment installs identity-relative coordinates directly:
lambda_X=log((1-p)/p), lambda_Y=lambda_Z=M, where
M=1024+abs(lambda_X)+128*maximum_joint_degree. Every C2V has magnitude below
64, including the closest representable tanh product below one. This bound
keeps excluded states over 1024 log units below I and X throughout every sweep;
their contribution to the float64 projections is zero. This is a numerical
representation of exact X-only support, not a depolarizing epsilon prior.
The property test checks repeated full-graph projections against binary
updates and verifies zero Y/Z marginal mass.

On this channel, QBP's active equations mathematically reduce to binary BP.
The third paired arm, `binary_paper`, exposes the prior reproduction's ±25
outgoing V2C clipping and zero-belief hard decision, while `binary_v2` uses
unbounded V2C. QBP v2 selects X on an I/X tie; binary v2 selects I on an exact
zero LLR. These numerical differences remain explicit.

`campaign.json` freezes the B1/C2 samples before results: at least 5,000 per
point, or ceil(400/published_BP_rate), whichever is larger. Every error is
decoded by all three arms. Their timing order rotates between shots. Each
manifest records policies, implementation hashes, code identity, prior, host,
sample stream and stopping rule. Each shot records candidate/error digests,
iterations, elapsed time and independent outcome classes. Completed ledgers
are losslessly zstd-compressed and verified before plaintext is removed.

A5/B2 reuse complete fixed-shot paired binary v2/QBP v2 cohorts from the
[vanilla campaign](../yao-2312-10950-vanilla/README.md). At B2 p=0.05 the
independent completed 200,000-shot follow-up replaces its first cohort. At
B2 p=0.04 the new `b2-p004-followup.json` freezes ten independent 50,000-shot
two-arm shards, excluding the earlier pilot and the interrupted four-arm run.
`run_depolarizing.py` evaluates logical X and Z signatures separately.

## Audit and rerun

`assess.py` reconstructs every physical sample, verifies manifest and ledger
hashes, recomputes aggregates, and audits paired rescues/losses. The historical
study helper XOR-combined X/Z logical signatures, potentially hiding a logical
Y error. The new assessor replays every historical nonexact converged v2
correction and checks the two signatures independently. Fixed-stride and
boundary shots from new runs also receive independent candidate replay.
Any changed logical classification is retained in a separate audit ledger;
raw historical evidence is immutable.

Run from the repository root in an eligible compute allocation:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/run.py --index 0
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/run_depolarizing.py --index 0
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/assess.py
PYTHONPATH=src python data/reproductions/yao-2312-10950-cross-code/assess.py --render
PYTHONPATH=src pytest -q tests/test_yao_cross_code.py
```

Use the frozen task index from the appropriate plan. Slurm receipts are
`dispatch.json` and `b2-dispatch.json`. Their arrays reserve one CPU and 4 GiB
per task, at most 14 and 10 simultaneous tasks respectively, with a three-hour
wall limit. `--smoke` runs 20 shots into separate smoke directories and is
excluded from analysis. Do not overwrite or append to a completed ledger.

Outputs live in `results/`: `REPORT.md`, `performance.csv`, `paired.csv`,
`comparison.png`, `comparison.pdf`, `audit.json` and the logical-outcome replay
ledger. Rates use the full fixed denominator; Clopper–Pearson 95% intervals,
Type I/II counts, directed edge-update counts, iteration depth and runtime
remain separately inspectable. Runtime comparisons between historical A5/B2
and new B1/C2 hosts are not controlled speed comparisons.

`--render` rebuilds the report and figures from the audited CSVs after checking
their hashes. The full command without that flag independently rechecks all
ledgers and candidate replays. `--wait` allows that audit to overlap pending
frozen runs, waiting for complete compressed ledgers at each stage.
