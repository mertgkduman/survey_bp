---
status: complete
implementation_status: verified
campaign_status: complete
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

All arrays **61703094–61703096** and collector **61703097** completed with
exit 0:0. The collector audited and published all **30/30 points**, **6,403,005
shots**, **600 quantum block failures** and **6,367,969 certified skipped branches**.
Every point reached 20 failures. The previous 29 audited records are unchanged;
the final .010 point's summary matches the collector receipt and frozen pins.

The earlier .04–.10 campaign completed **42/42 points**, **2,366 shots** and
**840 failures**; its array and collector exited COMPLETED (0:0). Its complete
results remain in the raw catalog and historical files. A validated
`public_retired_dataset_ids` declaration removes that interval from all public
v2 views through the existing shared projection.

Counts of active curves / points / codes / circuits:

- Complete old-grid view before retirement: **70 / 381 / 8 / 0**.
- Existing evidence after retiring the old interval: **64 / 339 / 6 / 0**.
- Current audited paper-rate snapshot: **70 / 369 / 8 / 0**.
- Planned complete paper-rate view: **70 / 369 / 8 / 0**, subject to normal
  evidence and two-distinct-rate eligibility checks.

The current view contains five-rate [[74,18]] curves and complete ordinary
binary/Q-BP curves for [[274,110]]. Its five-point unicycle-SP curve
qualifies for public display; all simulations are complete.
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

The final collector verified every complete ledger, counts, work, hashes and
endpoint replay and refreshed the workbench. Final evidence is in verified.json;
old/new controllers and sampling roles remain separate.

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

The final .010 rate is 20/5,803,778 = 3.4460e-6, with pointwise 95% interval
[2.1049e-6, 5.1123e-6], below the source approximate 6.6987e-6. It has one
Type I and nineteen Type II failures and no stabilizer successes. The two lowest
rates are below their source ordinates; the other three are consistent within
individual intervals. Full source-curve agreement is not established. See
PROGRESS-2026-11-13.md for the final audit status.
