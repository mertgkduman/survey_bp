---
quick_id: 261110-sic
status: complete
date: 2026-11-10
implementation_commit: 25c6c1f
verification: passed
completed_date: 2026-11-11
---

# B1 and C2 direct decoder sweeps

The frozen plan has 77 code, decoder, and rate combinations. B1 uses eight
distinct BPGD settings from Figures 3 and 6. The shared T=100, R=882 arm
carries both source references. C2 uses Figure 5's T=10, R=1922 BPGD arm.
The X-only grid is 0.04 to 0.10 in steps of 0.01. The Q-BP grid is 0.060 to
0.150 in steps of 0.015 and matches the X marginal. Q-BP uses SP float64
with d=0.1 and maximum iteration counts of 88,200 for B1 and 19,220 for C2.

Each point stops at the 20th block failure or 100,000,000 iid shots. Type I
syndrome mismatches and Type II nontrivial logical residuals are recorded
separately. The joint decoder checks both logical signatures independently.
The terminal estimate and interval use the ordered shot prefix.

Slurm arrays `61550993`, `61550994`, and `61550995` completed all 77 points.
Collector `61550996` completed the ledger, manifest, counter, stop-boundary,
and endpoint-replay checks and refreshed the workbench. The final portable
snapshot matches every planned point and every retained manifest and summary
hash.

The campaign retained 40,459,752 shots and 1,540 block failures. Every point
reached 20 failures. All eleven decoder curves contain all seven requested
rates. The final B1 T=100, R=882, p=0.04 point has 20 failures in 13,740,124
shots, a rate of 1.455590939353968e-6, and a 95% interval from
8.891129804247097e-7 to 2.1594305998424587e-6.

The active workbench contains 64 curves and 339 points across six public codes
and zero public circuits. Superseded bounded BPGD cohorts remain in the
historical catalog. The workbench provides adjacent mean iterations and mean
directed edge updates per shot, including the final campaign points.

The frozen plan, portable `verified.json`, and generated static catalog are
tracked. The dispatch receipt and compressed raw ledgers are retained under
`data/reproductions/yao-2312-10950-bpgd-completion/results/` on HPC storage.

Implementation verification covered 124 research and campaign tests and four
real-decoder checkpoint and replay cases across both codes and channels. The
final refresh passed 40 catalog and work-metric tests and 18 Chromium
workflow checks against all eleven complete curves.
