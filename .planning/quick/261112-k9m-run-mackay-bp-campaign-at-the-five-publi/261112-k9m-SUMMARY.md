---
status: incomplete
implementation_status: verified
campaign_status: running
implementation_commit: fdbb98b
---

# Published-rate MacKay campaign

Corrected the campaign to use the paper's measured binary rates:
**.010, .013, .020, .030, .040**. Matched Q-BP depolarizing rates are
**.015, .0195, .030, .045, .060**. Both codes and three arms remain, for
30 planned points. The iteration ceiling, numerical profiles and 20 quantum
block failures / 100 million shots stopping rule are retained.

Implementation `fdbb98b` freezes the new plan and 29 file hashes, independently
qualifies the exact branch certificate, records both quantum and classical
error counts and actual executed work, and submits bounded independent-shot
workers. The optimization preserves the selected correction; skipped branches
record zero iterations and updates. It has an explicit controller identity and
is not pooled with the earlier unpruned work records. No canonical kernel or
old frozen implementation/plan is changed.

Slurm array **61703094** (16 CPUs) continues the remaining
unicycle-SP point (.010). Task **61703094_11** (.013) completed with exit 0:0 and its full ledger and endpoints passed audit. The ordinary binary and Q-BP
sweeps are complete on both codes. Dependent collector **61703097** audits
and publishes terminal evidence. Accepted commands are retained in `dispatch.json`.

Portable audited snapshot: **29/30 points**, **599,227 shots**, **580 quantum
block failures**, **575,727 certified skipped branches**. Every audited point
reached 20 failures. All 15 [[74,18]] points, all five [[274,110]] ordinary-binary
points, all five [[274,110]] Q-BP points and its p=.013/.02/.03/.04 unicycle-SP points are
verified. The remaining campaign is
still executing; no full-curve agreement claim is made.

The earlier .04–.10 campaign completed **42/42 points**, **2,366 shots** and
**840 failures**; its array and collector exited COMPLETED (0:0). Its complete
results remain in the raw catalog and historical files. A validated
`public_retired_dataset_ids` declaration removes that interval from all public
v2 views through the existing shared projection.

Counts of active curves / points / codes / circuits:

- Complete old-grid view before retirement: **70 / 381 / 8 / 0**.
- Existing evidence after retiring the old interval: **64 / 339 / 6 / 0**.
- Current audited paper-rate snapshot: **70 / 368 / 8 / 0**.
- Planned complete paper-rate view: **70 / 369 / 8 / 0**, subject to normal
  evidence and two-distinct-rate eligibility checks.

The current view contains five-rate [[74,18]] curves and complete ordinary
binary/Q-BP curves for [[274,110]]. Its four-point unicycle-SP curve
qualifies for public display; only p=.010 remains running.
No old interval is shown or mixed into the new curves. Other historical
decoders and custom matrix/Stim paths remain available.

Verification: **149 tests passed**, with **63 final focused checks** passing
after the initial 19-point refresh. The latest 29-point progress refresh
passed 41 focused checks and all seven public browser workflow groups. Chromium passed **26 workflow groups** across
paper-rate and historical-controller overlays, public results and plot/picker
workflows; the seven public workflow groups passed again on the final actual
snapshot. Checks include .0195 without rounding, proof prerequisites and
boundary/tie cases, real selected-candidate equivalence, parallel ordering and
resume, work counters, full input/selector/export consistency, empty states,
stale selections, mobile and archived v1. All 29 new and 27 old frozen file
hashes match. JavaScript syntax and Git whitespace checks pass.

Remaining work is automated. The dependent collector verifies complete
terminal ledgers, counts, hashes and first/last-shot replay, publishes the new
portable snapshot and refreshes a clean preview. Inspect actual collector
status before marking the campaign complete. The README provides safe manual
collection/publication commands and the proof; do not pool old/new evidence.

Latest results and validated running-prefix diagnostics are recorded in
[PROGRESS-2026-11-12.md](./PROGRESS-2026-11-12.md), including recovery of one
already-terminal checkpoint from unnecessary speculative-worker waiting.

The completed .020/.030/.040 source points each contain the paper's
approximate ordinate in their individual 95% intervals. At .013 the measured
20/468,516 = 4.2688e-5 has interval [2.6075e-5, 6.3329e-5], below the paper's
approximate 7.0747e-5. Both quantum and classical counts are 20 (four Type I,
sixteen Type II, zero stabilizer successes). The difference is mainly in
detected/Type I errors. Source iteration and numerical settings remain
unresolved; no full-curve agreement is established. See PROGRESS for diagnostics.
