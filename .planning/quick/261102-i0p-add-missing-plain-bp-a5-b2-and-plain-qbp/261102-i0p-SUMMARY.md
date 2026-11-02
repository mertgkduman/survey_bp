---
status: complete
date: 2026-11-02
---

# Missing plain-decoder baselines completed

Delivered `data/reproductions/yao-2312-10950-cross-code/` with executable
decoder policies, frozen campaigns, runners, full event ledgers, independent
audit, 70 arm measurements in 28 code/rate cells, paired analysis, Markdown
report, CSVs, and PNG/PDF plots. Data commit: `a95a898`; code: `9633f10` and
subsequent focused audit/report commits. The general decoder-file guide links
the experiment's explicit study-specific schema.

- T=100 for every plain decoder, as in the paper's per-code plain baselines.
  Undamped float64 flooding sum-product; no decimation or tuning.
- A5/B2 retain depolarizing p with exact binary marginals q_X=q_Z=2p/3.
  B1/C2 retain X-only p and QBP prior (1-p,p,0,0). The full joint kernel uses
  a proven degree-based excluded-state guard; repeated-sweep tests establish
  zero Y/Z float64 mass and active-message equivalence to binary updates.
- All 28 cells cover p=0.04,...,0.10. Each main arm has at least 100 failures.
  The comparison uses 1,583,664 paired physical samples, including 74,217
  newly sampled B1/C2 errors and a fresh independent 500,000-shot paired B2
  p=0.04 stage. Complete existing A5/B2 cohorts are reused without combining
  the adaptively selected pilot with the follow-up estimate.
- QBP and binary v2 have identical terminal corrections on all 74,217 X-only
  samples, zero paired rescues/losses, and equal LER/iteration counts. The
  full QBP graph is 1.79–2.14 times slower in these same-run comparisons.
- Under depolarizing noise, QBP's observed LER is lower at every p: BP/QBP
  ratios 3.14–20.19 for A5 and 9.01–13.02 for B2. At p=0.06: A5
  1935/39570 versus 131/39570; B2 1432/48658 versus 110/48658.
- The C2 numerical control contradicts universal improvement from v2:
  p=0.04 paper-style BP has 390/5000 failures, v2 has 561/5000. Differences
  in V2C clipping and exact-zero decisions remain explicit; this task makes
  no further default changes.
- Found the historical helper XOR-combines X/Z logical signatures. The
  independent evaluator preserves both. Replayed all 22,863 retained
  nonexact converged historical corrections; zero classifications changed.
  A synthetic physical logical-Y test demonstrates the cancellation bug.
  Immutable historical ledgers and separate replay evidence are retained.

Verification: all 112 included run/shard ledgers were independently checked
against manifests, hashes, reconstructed physical samples and aggregate
counts. New boundary and fixed-stride shots were replayed with the independent
logical evaluator. Seven focused tests passed. All 24 Slurm tasks completed
with exit code zero. The plot was visually inspected. Compressed original
ledgers reconstruct byte-identically; the historical analyzer was verified
on a compressed shard after adding its shared ledger reader. CSV output uses
LF line endings and render-only rebuilds verify audited CSV hashes.

The earlier BP/BPGD rare-event completion task remains open. Its pending
scientific results are not relabeled by this completed cross-code analysis.
