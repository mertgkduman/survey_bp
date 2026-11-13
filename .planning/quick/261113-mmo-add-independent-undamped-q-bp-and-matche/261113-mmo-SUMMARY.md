---
status: complete
implementation_status: verified
campaign_status: controls_complete
source_extraction_status: requested_five_ordinates_not_reported_in_inspected_sources
continuation_status: waiting_for_prior_confirmation
implementation_commit: bd08a80
---

# Isolated Q-BP and length74 source evidence

Implemented, froze, executed and audited **20/20** undamped controls:
**13,641 retained decoder shots / 400 block failures**. New array61781770 and
collector61781771 completed0:0. Joint Q-BP d=0 and separate-X/Z binary BP d=0
use identical depolarizing realizations on both existing codes at all five
rates, T100, canonical float64 SP,20 failures/100M stop, and confirmation
seed2026111323 independent of training. Explicit paired/component/joint work
avoids treating binary component sweeps as full-graph iterations. No equations
or canonical kernels changed.

Within-point method comparisons now isolate Q-BP under one channel. At p=.015
both undamped methods have identical observed LER (length274 .0135135;
length74 .0112740). At p=.060, length274 separate BP has LER .298507 and
undamped Q-BP .133333. These descriptive point estimates show that the earlier
orders-of-magnitude low-rate gains arise in the damping comparison; they are
not demonstrated gains from switching to undamped Q-BP alone. Twenty failures
per point do not establish simultaneous superiority or equivalence.

All four new curves are published. Active view **76→80 curves,399→419 points,
8→8 codes,0→0 circuits**. Every preexisting raw series and its points remain
structurally identical. Source registration makes rebuilds/imported results use
the same eligibility projection. Public labels distinguish separate X/Z,
full depolarizing noise, marginal priors and d=0. Work units remain explicit in
CSV and saved settings. The new RESULTS.md and80-row results-table.csv compare
matched methods/damping and separately retain original-paper values. All five
unreported N74 paper ordinates remain blank with not_reported status, not zero.

The requested N74 five-rate curve is absent from inspected arXiv source
versions1–3 and the current PDF. Extracted the actual Figure17 summary reference:
marginal p≈.00681824 at the paper's fixed target convention (quantum1e-4,
constituent classical5e-5). This single threshold cannot supply the requested
five ordinates. Figure11 is the N74 matrix; Figure16 is the N274 curve.
Archive/member hashes and vector calibration are in paper-evidence.json;
PAPER-EVIDENCE.md describes the scope and unavailable publisher/author routes.
This completes the source check with an explicit unavailable-data outcome.

Validation:165 regression checks, final10 label checks, and54 measured-catalog
checks passed (overlapping suites). Three isolated-control Chromium workflow
groups and seven measured-public groups passed without page errors or browser
simulations. Checks include actual canonical executions, common Y/Z samples,
Z logical failure, real work and cap validation, serial/parallel equality,
resume/endpoint audit, incomplete-gate rejection, exports, all public selectors,
empty/stale state, custom matrix/Stim and retained v1. Browser receipts:
.git/mackay-isolation-browser/verification.json and
.git/mackay-isolation-measured-browser/verification.json.

Canceled only old pending advance61773603; prior rare confirmation61773602_10
continues. Replacement advance61781772 waits on completed new audit61781771
and the entire old confirmation array61773602, then requires20/20 and40/40
complete-ledger audits before submitting unchanged Roffe T=n. Roffe remains
unsubmitted. No old frozen plan, source record, ledger, canonical or v1 file
was changed. New plan40 pins SHA256:
1981707650adf4b9a04730a2bd58594bd016dd67695252086d3391aacc2bf1bb.
The old baseline/tuning/confirmation/Roffe plans retain their verified hashes.

The new controls and source-review deliverables are complete. The larger
MacKay confirmation campaign still has one live point and is not declared
complete; source-faithful numerical identity or full-curve reproduction is not
asserted. The replacement continuation preserves that outstanding work.


Subsequent user scheduling override: quick261113-oan launches Roffe immediately
with one CPU for every point, preserving frozen science. Shared Roffe dispatch
receipts ensure this task's eventual MacKay continuation reuses those existing
jobs after its own audits. Its former serial-launch description is superseded
by roffe-2005-07016-bp/LAUNCH-ALL.md; MacKay's live worker remains unchanged.
