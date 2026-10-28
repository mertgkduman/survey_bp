---
status: complete
quick_id: 261028-kvb
date: 2026-10-28
---

# Tune canonical BP4 on Yao A5 and B2 at p=0.06

Used the pinned A5 `[[180,10]]` and B2 `[[882,48]]` code identities,
depolarizing sampler, and independent Type I/II block-failure evaluator.
Screened 47 policies per code on paired prefixes ending at six baseline
failures, then ran independent fixed-shot refinement and successive local
neighborhoods. All 257 tasks and 8,904,576 decoder shots completed; all
stage audits verified policy/source hashes, manifests, event ledgers,
outcome counts, and shared physical-error streams.

Selected compiled BP4 float64 v2 SPA with no check cap and product epsilon
`1e-10`. A5 uses decoder prior `p0=0.005`, outgoing V2C damping `d=0.2`,
and `T=10,000`: 43/100,000 block failures (exact 90% CI
`[0.000328,0.000554]`, 42 Type I, 1 Type II). B2 uses `p0=0.15`, `d=0.1`,
and `T=5,000`: 30/100,000 (`[0.000216,0.000407]`, 26 Type I, 4 Type II).
The physical probability remained `p=0.06` throughout.

A5's local damping and prior neighbors failed the one-sided paired 90%
improvement criterion. Its T=20,000 arm rescued 4/100,000 with zero losses;
the exact one-sided 90% rescue upper bound `7.99e-5` was below the
incumbent's rate-to-lower-CI margin `1.02e-4`, satisfying the plan's
practical cap rule. B2's independent 100,000-shot confirmation favored
`p0=0.15` over `0.16` with 15 rescues and 6 losses (`p=0.0392`); adjacent
priors did not improve it. Its 5,000 cap satisfied the same practical rule
against 10,000 and 20,000 in the 80,000-shot cap stage.

Selected decoder JSON files, frozen registries/plans, manifests, summaries,
CSV/JSON paired results, PNG/PDF interval plots, exact stopping receipts,
and replay instructions are under
`data/reproductions/yao-2312-10950-bp4-tuning-p006/`. The final report is
`results/REPORT.md`. Raw event ledgers remain on the HPC filesystem and are
Git-ignored because of size; tracked manifests/summaries contain digests.
Both selected files passed 10-shot replay smoke checks. The rates and
unadjusted paired p-values remain conditional on sequential policy search;
the evidence supports the tested finite neighborhoods, not a global optimum
or transfer to other physical error rates.
