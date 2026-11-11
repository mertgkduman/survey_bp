---
quick_id: 261110-sic
status: in_progress
date: 2026-11-10
implementation_commit: 25c6c1f
verification: partial
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

Slurm arrays `61550993`, `61550994`, and `61550995` contain all 77 points.
Dependent job `61550996` audits the terminal ledgers and refreshes the local
catalog. Jobs can resume the same frozen shot stream from the last committed
compressed checkpoint. The dispatch receipt and raw evidence are in
`data/reproductions/yao-2312-10950-bpgd-completion/results/`.

The committed snapshot verifies 42/77 terminal points, each with exactly
20 block failures. It adds eight multi-rate curves, including the first C2
BPGD and Q-BP results. At the latest scheduler check, 47 point jobs had
completed and 30 were running. The workbench hides superseded B1/C2 bounded
BPGD cohorts. The historical measurements, matrix references, and archived v1
remain available. The public projection changed from 63 curves and 319 points
to 53 curves and 262 points before adding the replacement measurements.
With the new snapshot, the active workbench has 61 curves and 304 points
across six public codes and zero public circuits.

Verification covered 124 research and campaign tests, four real-decoder
checkpoint and replay cases across both codes and channels, and 17 Chromium
workflow checks. The collector recomputes terminal counts and hashes and
deterministically replays the first and last shots of each point.
