# Yao et al. non-OSD results

This folder maps Figures 2–8 and Tables 1–2 of [Yao et al., arXiv:2312.10950v2](https://arxiv.org/pdf/2312.10950v2), excluding BP-OSD. `source_points.json` is extracted from the pinned arXiv TeX; `codes.json` pins the four CSS constructions. The C2 construction uses the polynomial in [Panteleev and Kalachev, arXiv:1904.02703v3](https://arxiv.org/pdf/1904.02703v3).

For the repository's composable decoder-file schema, see [decoder-files.md](../../../docs/decoder-files.md). This reproduction runner fixes source-specific policies in code and records the resolved settings in every manifest; `codes.json` and `source_points.json` are evidence receipts, not decoder-policy files.

## Decoder and evidence files

- `run_point.py` defines the binary paper-style BP/BPGD policies and the A5/B2 Q-BPGD policy, noise generation, independent logical outcome classification, and per-shot ledger schema. Every run writes `manifest.json`, `events.jsonl`, and `summary.json` under its own directory in `results/`.
- `src/bp_registry/canonical/compiled.py` contains the binary compiled paper-style BP/BPGD kernel. A binary decoder instance is built from the Z-check matrix for X-only noise. Outgoing variable-to-check messages are clipped to ±25; BPGD fixes a variable's prior to ±25 after each T-sweep round and retains message state between rounds.
- `src/bp_registry/quaternary/compiled.py` contains the existing compiled BP4/Q-BPGD kernel used for A5/B2. Source-style Q-BPGD uses physical `p` as decoder prior `p0`, no damping, T=10, and the BP4 v2 numerical profile. This is a canonical adaptation, not a claim of identical author code.
- `campaign.py` enumerates bounded development subsets. `assess.py` verifies the new ledgers and generates `results/comparison.csv`, `results/comparison.png`, `results/comparison.pdf`, and `results/REPORT.md`. Prior QBP v2 curve results are linked from the earlier `yao-2312-10950-vanilla` campaign.
- `table2_surrogate.py` fixes a newly seeded weight-73 error and repeats top-gap randomized BPGD. It tests the behavior behind Table 2, while explicitly recording that the paper's fixed error is unavailable.

Example from the repository root:

```bash
PYTHONPATH=src python data/reproductions/yao-2312-10950-non-osd/run_point.py \
  --code b1 --method bpgd_t10 --p 0.06 --max-shots 2000 \
  --output data/reproductions/yao-2312-10950-non-osd/results/my-b1-run
python data/reproductions/yao-2312-10950-non-osd/campaign.py --tier bp_grid --workers 2
PYTHONPATH=src python data/reproductions/yao-2312-10950-non-osd/assess.py
```

`--target-failures` stops early after the specified block-failure count but never exceeds `--max-shots`. `--start-shot` and `--seed` define disjoint deterministic shards. The initial `smoke-*` and `pilot-*` folders only check execution; they are marked as pilots in the assessment. `bp_grid`, `guided_grid`, `quaternary_grid`, `ablation_p008`, and `full_bounded` have explicit per-point shot ceilings and at most four simultaneous workers. They do not grant access to the separate Phase 11 publication campaigns.

Runner revision `50d6371` flushed ledgers every 1,000 shots. After an external termination, `recover_interrupted.py` finalized only the complete C2 prefix; other interrupted runs had no flushed rows and retain `ABORTED.md`. The current runner uses line-buffered ledger output and prints progress every 100 shots. Manifests pin the exact runner hash, and `assess.py` accepts both the committed older revision and the current one while excluding superseded early smokes.

The paper supplies no physical-error bytes for Table 2, so its exact fixed-error experiment is unavailable. Its Table 1 prose and caption disagree on T; Figures 3 and 4 disagree on the nominally identical B1 T=10 curve. The source record preserves these differences. BP-SI coordinates in Figures 4 and 5 came from another paper and are source-only here.
