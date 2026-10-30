# Yao et al. non-OSD results

This folder reproduces the BP and BPGD results in Figures 2–8 and Tables 1–2 of [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2). BP-OSD and BP-SI are excluded from comparisons. `source_points.json` is the unmodified extraction from the pinned arXiv TeX, including excluded curves as provenance; `codes.json` pins the four CSS constructions. The C2 construction uses the polynomial in [Panteleev and Kalachev, arXiv:1904.02703v3](https://arxiv.org/pdf/1904.02703v3).

For the repository's composable decoder-file schema, see [decoder-files.md](../../../docs/decoder-files.md). This reproduction runner fixes source-specific policies in code and records the resolved settings in every manifest; `codes.json` and `source_points.json` are evidence receipts, not decoder-policy files.

## Decoder and evidence files

- `run_point.py` defines the binary paper-style BP/BPGD policies and the A5/B2 Q-BPGD policy, noise generation, independent logical outcome classification, and per-shot ledger schema. Every run writes `manifest.json`, `events.jsonl`, and `summary.json` under its own directory in `results/`.
- `src/bp_registry/canonical/compiled.py` contains the binary compiled paper-style BP/BPGD kernel. A binary decoder instance is built from the Z-check matrix for X-only noise. Outgoing variable-to-check messages are clipped to ±25; BPGD fixes a variable's prior to ±25 after each T-sweep round and retains message state between rounds.
- `src/bp_registry/quaternary/compiled.py` contains the existing compiled BP4/Q-BPGD kernel used for A5/B2. Source-style Q-BPGD uses physical `p` as decoder prior `p0`, no damping, T=10, and the BP4 v2 numerical profile. This is a canonical adaptation, not a claim of identical author code.
- `campaign.py` enumerates bounded development subsets. `assess.py` verifies the new ledgers and generates `results/comparison.csv`, `results/comparison.png`, `results/comparison.pdf`, and `results/REPORT.md`. Prior QBP v2 curve results are linked from the earlier `yao-2312-10950-vanilla` campaign.
- `completion_direct.py` freezes and dispatches ordinary iid 100-failure points whose published rate is at least 0.01. `completion_mid.py` handles the additional feasible range 0.003–0.01. `completion_low_direct.py` covers selected lower-rate A5/B2/B1/C2 points that are still practical with direct sampling. `completion_importance.py` freezes 10,000-shot rare-event pilots below 0.01; its overlap with the direct tiers checks the estimator independently. All plans are in `results/`; their Slurm arrays use one CPU and 4 GiB per task, with at most 16 simultaneous tasks per main array.
- `run_importance.py` uses a defensive mixture: 10% of errors from the target physical `p`, 90% from a recorded higher proposal `q`. Every error is decoded with the target `p` and weighted by its exact target-to-mixture likelihood ratio. `importance_assess.py` independently reconstructs every proposal draw, checks its likelihood weight and ledger, and aggregates disjoint shards. Weighted effective failures must reach 100 and approximate 95% relative half-width must be at most 25% before the report calls a rare-event estimate resolved. The paper used ordinary iid sampling, so these estimates have a separate `mixture_importance` label.
- `extend_importance.py` reads completed pilot ESS values, freezes additional non-overlapping 50,000-shot shards, and skips points already assigned a direct iid run. Each extension stage has a 500,000-shot per-point ceiling and its own immutable plan. The assessor uses only the latest independently fixed stage for the displayed IS estimate; the pilot chooses its sample size but does not enter that estimate. The estimate remains preliminary until the precision gate is met.
- `compress_completed.py --all` verifies a completed ledger's original SHA-256, compresses it with zstd, checks byte-exact decompression, records `compression.json`, and removes the large plaintext file. `ledger_io.py` lets both assessors stream either plaintext or compressed ledgers. A running or unverified ledger is never compressed.
- `table2_surrogate.py` fixes a newly seeded weight-73 error and repeats top-gap randomized BPGD. It tests the behavior behind Table 2, while explicitly recording that the paper's fixed error is unavailable.

Example from the repository root:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-non-osd/run_point.py \
  --code b1 --method bpgd_t10 --p 0.06 --max-shots 2000 \
  --output data/reproductions/yao-2312-10950-non-osd/results/my-b1-run
python data/reproductions/yao-2312-10950-non-osd/campaign.py --tier bp_grid --workers 2
PYTHONPATH=src python data/reproductions/yao-2312-10950-non-osd/assess.py
```

The frozen completion plans can be inspected at `results/completion-direct-plan.json`, `results/completion-mid-plan.json`, `results/completion-low-direct-plan.json`, `results/completion-importance-plan.json`, and `results/completion-importance-extension-stage1.json` or `results/completion-importance-extension-stage2.json`. To rerun a single planned task in an eligible allocation, call the matching script with `--run-index N` (also pass the matching `--stage` for extension shards). Each task refuses to overwrite an existing result. The Slurm dispatch receipts are in `results/completion-dispatch.json`.

`--target-failures` stops early after the specified block-failure count but never exceeds `--max-shots`. `--start-shot` and `--seed` define disjoint deterministic shards. The initial `smoke-*` and `pilot-*` folders only check execution; they are marked as pilots in the assessment. `bp_grid`, `guided_grid`, `quaternary_grid`, `ablation_p008`, and `full_bounded` have explicit per-point shot ceilings and at most four simultaneous workers. They do not grant access to the separate Phase 11 publication campaigns.

Runner revision `50d6371` flushed ledgers every 1,000 shots. After an external termination, `recover_interrupted.py` finalized only the complete C2 prefix; other interrupted runs had no flushed rows and retain `ABORTED.md`. The current runner uses line-buffered ledger output and prints progress every 100 shots. Manifests pin the exact runner hash, and `assess.py` accepts both the committed older revision and the current one while excluding superseded early smokes.

The paper supplies no physical-error bytes for Table 2, so its exact fixed-error experiment is unavailable. Its Table 1 prose and caption disagree on T; Figures 3 and 4 disagree on the nominally identical B1 T=10 curve. The source record preserves these differences.
