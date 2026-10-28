---
status: complete
quick_id: 261027-qsa
date: 2026-10-27
---

# Yao et al. vanilla BP reproduction

Extracted the exact Q-BP points in Figures 7 and 8 of
arXiv:2312.10950v2 from the versioned TeX archive. Reused the pinned A5
construction and added the B2 [[882,48]] source construction from
arXiv:1904.02703v3. B2's check matrices and ordered logical basis are
verified by dimensions, row/column weights, commutation, paired logical
relations, and semantic/matrix hashes.

Created four strict decoder JSON files for undamped float64 flooding
sum-product at T=100: BP4 v1, BP4 v2, separate-binary v1, and separate-binary
v2. Binary component priors are q=2p/3; BP4 uses the joint depolarizing
prior. Each physical error is shared by all arms. Independent syndrome and
logical evaluation includes stabilizer-equivalent success.

The frozen fixed-shot campaign ran 1,216,144 paired shots at seven p values
on each code. All 128 shard ledgers passed SHA-256, count, policy/campaign,
and sample-boundary audit. The first attempted array was canceled after a
policy-file schema change; its interrupted evidence is retained separately
and excluded from the final assessment. The completed array is 60251089.

BP4 v2's local exact 95% interval contains the published point at 6/7 A5
rates and 2/7 B2 rates. On B2 it is lower than the published rate at 6/7
points (local/source ratios 0.71–0.88) and close at p=.07 (ratio 1.03).
Every BP4 v2 failure is a syndrome failure. BP4 v1 and both separate-binary
arms have published points outside their local intervals at all 14 points.
The v1 failure is a local numerical-profile finding; the remaining B2 gap
cannot be assigned to a particular undocumented source implementation detail.
Source denominators are unavailable, so interval coverage is descriptive,
not a two-sample test.

Results, exact counts, intervals, paired rescues/losses, Type I/II outcomes,
work and time are under `data/reproductions/yao-2312-10950-vanilla/results/`.
The study README and `docs/decoder-files.md` explain policy files and replay.
Focused regression and algebra tests: 16 passed. The final merger audited
128/128 shards and rendered PNG/PDF curves.
