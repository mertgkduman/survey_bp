# Paper-budget correction review

User correction: 88,200 is not an appropriate MacKay reproduction/tuning cap.
Keep the completed curves, add source-budget results separately, and perform
no further 88,200-iteration damping. The previous carry-over was an orchestration
error; a source iteration cap was already unresolved in the original manifest.

Stopped advance job 61769654 first, then array 61769653. Expanded scheduler
accounting shows 28 completed tuning tasks and 112 canceled array tasks, plus
the canceled advance job. No dependent confirmation plan or Roffe dispatch
exists. No campaign task remains running or pending.

Archive check performed without running any decoder: the frozen plan still
loads, 44 initialized checkpoints pass contiguous-ledger/count/work validation,
28 terminal summaries match their ledgers/manifests exactly, and all partial
checkpoints remain untouched. Retained totals are 33,920 tuning shots / 876
failures. These were training observations and were never published. STOPPED.json
retains each checkpoint's digest and explicit cancellation reason. The original
frozen design is preserved; it must not be resumed as a valid tuning study.

Re-inspected primary arXiv v3 HTML, 42-page PDF, all TeX source members including
comments, and the bundled vector figures. Archive SHA-256:
`fad6f31421f0ef198009f1f75de482ddaab0e3b1c1c8b25a44344a640359030e`.
Section 3.1 defines a sum-product iteration; Section 4.6 explains independently
decoding two extra-bit hypotheses and selecting a valid maximum-likelihood
candidate; Section 6 describes error measurements. No numeric iteration cap was
found in these primary materials. The PDF has no match for the plural word
iterations; singular iteration occurs in the general message-passing description.
TeX matches in psfig.tex refer to figure formatting, not decoder iteration.
The bundle contains no experiment runner/configuration establishing the cap.
The historical author QECC page could not be fetched (HTTP 403); external search
did not yield a source-bound experiment cap. A generic decoder default or a later
paper's limit would not establish the limit for this figure.

Primary sources:
- https://arxiv.org/html/quant-ph/0304161v3
- https://arxiv.org/pdf/quant-ph/0304161v3
- https://arxiv.org/src/quant-ph/0304161v3

The numeric cap and its scope (per hypothesis or total controller work) remain
unresolved. Asked the user asynchronously for the intended count/source. Do not
invent a paper-budget value. Larger ceilings could alter detected/nonconvergent
failures, but the low-rate difference has not been causally established by a
source-matched paired experiment.

Existing public catalogs and completed receipts are byte-unchanged: 70 curves /
369 points / 8 codes / 0 circuits. A separate short-budget identity will retain
them side by side; max_iterations already participates in central evidence
identity. An additional regression checks that short-budget evidence cannot
supply a second measured rate to a retained large-budget curve.

Roffe's already-frozen plan uses its explicit source budget T=n: 162/242/338/450,
with the source min-sum alpha schedule and exact rate grids. Its implementation
is unchanged. Automatic dispatch from the canceled MacKay chain is disabled;
transfer the continuation only after the corrected campaign is specified.

## User-authorized inference and implemented replacement

The user asked whether the missing cap could be inferred from curve alignment.
Implemented a retrospective projection using first-convergence records, with
short-only replay for ambiguous original errors and skipped competitors. All
five original ledger digests were verified. The retained bank contains 6,284,026
source-arm shots. Only 148 branch replays at caps <=1,000 were needed. No long
budget decoding or damping was resumed. Mathematical projection and direct
short runs agree in qualification tests.

Compared eleven per-hypothesis cutoffs (2/3/5/10/20/25/50/100/200/500/1000).
The sum of squared log relative total-error discrepancies over the five source
points is smallest at 100: .0351, versus .0868 at 50 and .1823 at 200. At 100,
the source-arm projected classical errors are 33/5,803,778; 31/468,516;
26/11,156; 23/462; 20/114. The detected/undetected split becomes roughly
balanced. This supports a finite-cutoff contribution to the earlier discrepancy,
but cannot establish the historical setting. Fifty also fits reasonably.

The adaptive original stopping rule prevents transferring its confidence
interval to these projections. This is calibration only. Recorded cap=100 as
**curve inferred, not source specified**, and use a fresh independent seed for
new measurements. Ordinary BP and joint Q-BP each have T=100. Source unicycle
uses 100 per hypothesis, up to 200 total; branch work and units are explicit.
Keep all old 88,200 curves side by side. The compact labels state budget=inferred.

New baseline: 30 points, seed 2026111317, each stopping at 20 quantum block
failures or 100 million shots. Classical errors remain separate. The source
comparison does not borrow the quantum interval when observed counts differ.
New tuning: 140 fixed 1,024-shot points, seed 2026111321, all T=100. The previous
LER-first paired regret guard and secondary mean-iteration objective are kept.
Fresh confirmation uses seed 2026111323 and T=100 for both selected/original
settings, with 20-failure/100M stopping. Identical settings are run once.

Frozen inferred baseline: 40 pins, plan SHA-256
`a60f1906913f5ed2a58281463f7a90436a13ad60d31ce4e1582131428be73b3d`.
Frozen T100 tuning: 36 pins, plan SHA-256
`65ba3a1ab1c496efddf948c8cedaa339514242f3a911576808196b3b4845fb42`.
The Roffe and canceled large-budget plans still load with their original hashes.
No old frozen scientific file, canonical kernel or archived v1 file is changed.

Successful baseline audit publishes its separate inferred-budget catalog and
submits T100 tuning. Its successful audit freezes fresh T100 confirmation; its
successful audit submits the unchanged Roffe T=n campaign. Missing/failed
points stop advancement. The original canceled chain cannot trigger it.
