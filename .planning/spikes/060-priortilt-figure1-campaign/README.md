---
spike: '060'
idea: priortilt-figure1
name: priortilt-figure1-campaign
type: standard
verdict: PARTIAL
related: ['057']
tags: [circuit, priortilt, figure1]
---

# One-CPU source-grid circuit campaign

User-authorized scope: review project goals and reproduce Fig1 with canonical BP-family decoders, one CPU per point. Source and mathematical qualification precede production dispatch. Preserve prior evidence and phase gates.

## Research

Primary paper: https://arxiv.org/html/2611.13373v1
Author artifact repository: https://github.com/ionq-publications/PriorTiltDecoder

## Investigation Trail

Initial source review finds exact circuit artifacts, raw Fig1 measurements and optimized three-phase parameters available. Circuit memory is evaluated through detector/observable semantics rather than a CSS code-capacity substitute. PriorTilt is 60+3000x6 sweeps, RelayBP-1 is 80+300x60, and beam32_340iters is width32 with40 initial and10x30 continuation sweeps per path. The figure metric is (X-memory errors/shots + Z-memory errors/shots)/cycles.

## Results

Source/controller qualification passed; production was submitted and is not yet complete.

## Frozen production launch

Source and mathematical qualification passed before dispatch. The final affected regression run passes348 tests; source/native checks cover72 PriorTilt+72 Beam/Relay controller cases and144 ordinary-BP numerical-order probes, plus624 independent full-budget circuit pilot events. A paired-memory recovery test caught and fixed a JSON tuple/list manifest mismatch before freezing. Tests cover exact failure prefixes, zero-error bounds, shared noise across methods, committed versus uncommitted crash output, stale/tampered sample/work receipts, independent logical failure versus nonconvergence, and audited-only/empty publication.

Frozen study: `data/reproductions/priortilt-2611-13373/plan.json`, SHA256 `3e466081790d913ae2fb0a477f654bd0218504a79e7d969b989b62043b7e829c`. All39 plotted points are thirteen code/rate combinations ×three methods. Every worker handles its X/Z memories sequentially/interleaved on **one CPU**,3GiB, with four-day walltime/requeue, private JIT caches, thread limits1, shared immutable packed samples and atomic columnar event chunks. The array is **61946754** (tasks0–38); all39 were observed RUNNING with CPUs1. Collector **61946755** is dependency-queued; Slurm allocates two CPUs for its12GiB request, which is a reporting job rather than a point simulation. Worker audits run in fresh Python interpreters within the same one-CPU allocations. Raw observations/candidates/path ledgers remain under ignored `results/` without deletion.

Local stopping is20 observable errors or100M decoded shots **per memory basis**, separately from the authors' larger precision. Paper metric, denominator and canonical/nonnative numeric differences remain explicit. Publish only a fully completed, audited X/Z pair, with summed component uncertainty; do not publish unfinished-shot provisional bounds. A source-only initial report/three-panel figure was generated and inspected with0/39 local points. The collector rehashes receipts, complete ledgers and samples before reporting.

Existing raw results, historical manifests and kernels, old jobs, public catalog/v1 and configured models are unchanged. No simulations from earlier studies were rerun and no phase gates/counters moved. The outstanding production task is to let the39 points finish, audit them, then assess each paper ordinate against its local interval. Future public catalog integration must represent paired-memory inputs and the figure metric honestly, not invent a single Stim circuit or pooled binomial denominator.

Evidence: [launch verification](verification.json), [dispatch commands/IDs](../../../data/reproductions/priortilt-2611-13373/dispatch.json), [campaign guide](../../../data/reproductions/priortilt-2611-13373/README.md), and [audited result report](../../../data/reproductions/priortilt-2611-13373/RESULTS.md).

Verdict: PARTIAL — implementation, freeze, qualification and one-CPU dispatch are complete; statistical reproduction remains running, with no source agreement claim yet.

## First production check — quick261116-rf9

Seven complete pairs passed worker full-ledger audits and are now published (345,963 decoded basis shots/280 observable errors). Source join, both denominators, capped stopping, figure metric, component intervals and work/latency independently reconcile. All seven source ordinates lie within local pointwise95% intervals; this does not establish simultaneous full-figure agreement. Thirty-two workers continue on one CPU each; collector61946755 remains dependency-queued. Full source/frozen identities remain unchanged. The updated three-panel figure was inspected and13 affected regressions pass. See the [check summary](../../quick/261116-rf9-check-priortilt-fig1-results-and-explain/SUMMARY.md) and its assessment.

## Second production check — quick 261116-ta4

Fourteen complete pairs are now audited and published (2,710,989 decoded basis shots/560 observable errors), including four PriorTilt points. All 14 paper ordinates remain within local pointwise 95% intervals. Independent source/count/interval/work and prior-point checks pass; all 63 frozen identities and all seven earlier point records are unchanged. PriorTilt has the lowest estimate at each of four complete three-method strata. At BB70/p=.002 the local estimate is about 1.89x below Relay and 2.84x below Beam at published settings; no matched-latency or simultaneous curve claim follows. Twenty-five one-CPU workers continue, with the collector queued. No code, simulations, source artifacts or phase gates were changed. See the [check summary](../../quick/261116-ta4-check-priortilt-completed-fig1-points-an/SUMMARY.md).

A late BB144 PriorTilt/p=.003 point completed before the second check's handoff: the final refreshed snapshot is15/39 audited points (2,838,888 shots/600 errors), including5 PriorTilt points and all three methods at five strata. All15 paper ordinates are within local pointwise intervals; all14 prior snapshot records are unchanged. Both assessments are retained. Twenty-four one-CPU workers continue, with no experiment changes.

## Third production check — quick 261117-077

Nineteen completed full-audited pairs are published (24,299,037 decoded basis shots/760 observable errors), with5 PriorTilt and7 each Relay/Beam points. The four new completions are Relay/Beam at BB144/p=.002 and BB70/p=.001; PriorTilt remains5/13 complete. All19 paper ordinates lie within corresponding local pointwise95% intervals, and all15 earlier point records/63 frozen file identities are unchanged. Independent source/count/stopping/CI/work checks pass and the scientific figure was inspected. Twenty one-CPU workers continue without reported failures; unfinished PriorTilt counts remain progress only. No experiment, execution, source or phase gates changed. See the [check summary](../../quick/261117-077-check-priortilt-fig1-progress-and-newly-/SUMMARY.md).

## Fourth production check — quick261117-exr

The refreshed snapshot has23/39 audited points (97,616,345 decoded basis shots/920 errors), including7/13 PriorTilt and8/13 each Relay/Beam. New PriorTilt results are BB144/p=.002 (2.723e-6 LER/cycle; source2.467e-6) and BB70/p=.001 (3.958e-7; source4.678e-7). All23 paper ordinates fall inside local pointwise95% intervals; PriorTilt has the lowest estimate at all seven fully compared strata. Full-worker audit receipts and bound ledgers/samples are rehashed, independent aggregate checks pass, and all19 previous rows/63 frozen file identities remain unchanged. Sixteen one-CPU workers continue without reported failures. No production code or simulation changes; other collectors' pre-existing modified outputs remain outside this task's staging. See the [check summary](../../quick/261117-exr-check-new-priortilt-fig1-results-and-sou/SUMMARY.md).

## Resource amendment — quick261117-fdl

The user requested10 processors per remaining point. All16 remaining points now resume under array61971019 with10 CPUs/24GiB each (all observed RUNNING;160 point CPUs total), with collector61971020. The original23 completed audit receipts and CSV are unchanged. The16 live original workers and pending old collector were intentionally cancelled only after replacement submission. Frozen parent plan/code remain unchanged; a separate resource amendment pins the concurrent controller. Ordered per-basis commits preserve exact global-shot inputs/RNG and stopping. Sealed speculative work and concurrent timing cohorts are separate. Initial inherited-prefix checks and final original-DEM/work/endpoint audits use ten spawned workers; ten real decoder PIDs per resumed point are observed. Qualification61970828 passes480 full-budget separate pilot events with bitwise sequential science-array equality, inherited-prefix and resume tests;51 regressions pass. Use `parallel_report.py` for later publication. See the [resource guide](../../../data/reproductions/priortilt-2611-13373/PARALLEL.md) and [migration summary](../../quick/261117-fdl-resume-remaining-priortilt-fig1-points-w/SUMMARY.md). This overrides the prior allocation only; statistical reproduction remains PARTIAL/running.

## First completed parallel point — quick261117-guy

The resource-aware snapshot is24/39 audited points (112,123,660 decoded basis shots/960 errors), with PriorTilt still7/13 complete. New GB102 Beam/p=.001 is6.145e-7 LER/cycle versus source5.8e-7, inside the local95% interval. All24 source ordinates remain within corresponding intervals; all23 earlier point records are unchanged. Independent stage accounting verifies142 sealed stages and1,642 inherited marker hashes:1,163,264 computed shots split into1,056,051 retained and107,213 speculative, with matching additive work totals and exact inherited+retained canonical counts. Worker full audits cover all candidates/stages and endpoint replay; extra speculative outcomes do not enter LER. Fifteen ten-CPU workers continue; next PriorTilt GB102/.001 had15/16 X/Z errors in the saved progress snapshot. Parent/resource sources and phase gates remain unchanged. See the [check summary](../../quick/261117-guy-check-priortilt-ten-cpu-progress-and-new/SUMMARY.md).

## Further parallel completions — quick261117-kva

The refreshed full-audited snapshot is28/39 points (346,440,636 decoded basis
shots/1120 observable errors):PriorTilt9/13,Relay10/13,Beam9/13. New PriorTilt
BB70/.0008 andGB102/.001 give1.694e-7 and3.847e-7 LER/cycle versus source
1.566e-7 and3.637e-7. All28 paper ordinates remain inside local pointwise95%
intervals, and all24 earlier complete CSV rows are unchanged. PriorTilt has the
lowest estimate in all nine completed three-method strata, without a blanket
statistical-superiority claim. Independent source/count/CI/work and resource
checks pass:13,488 sealed stages and16,951 inherited markers across five parallel
points;110,493,696 computed shots=109,962,648 retained+531,048 speculative. Figure
inspected. Eleven ten-CPU point jobs remain active, including final audit of
BB70 PriorTilt/.0005 after100M shots/basis with8/18 errors; that unaudited point
is excluded. Parent/resource identities and63 frozen files unchanged. No new
simulations or production changes; campaign remains PARTIAL. See the
[check summary](../../quick/261117-kva-check-current-priortilt-fig1-results-and/SUMMARY.md).

## All PriorTilt points audited — quick261118-ogi

Checked status:38/39 fully worker-audited points (1,661,754,800 decoded
memory-basis shots/1,447 observable errors):PriorTilt13/13,Relay13/13,Beam12/13.
All39 have completed sampling; only GB102 Beam/p=.0005 awaits its full audit
on10 CPUs. Collector61971020 remains pending. All38 paper ordinates fall within
local pointwise95% intervals; ratios0.771–1.401. PriorTilt has the lowest estimate
in all12 complete three-method strata, with overlapping uncertainty and no
matched-latency claim. New rare PriorTilt values include BB144/.0012.917e-8,
BB70/.0005 2.889e-8,GB102/.0005 1.222e-8 andGB102/.0008 1.291e-7 LER/cycle.
All28 previous full CSV rows are unchanged.

This is a separately labelled checked status CSV/table from matching final
full-worker audit receipts, manifest/policy/frozen checks, independent aggregate
source/count/stopping/interval/work checks and sampled on-disk bindings. It is
not a completed fresh full raw-ledger rehash. Complete rehash attempts were
deliberately stopped as duplicate work for a status query; logs retained.
The main canonical publication stays at28 until the scheduled final collector
refreshes it. All15 parallel receipt totals reconcile:1,190,545,664 computed
shots=1,189,379,980 retained+1,165,684 speculative; all45,747 inherited digests
are preserved in full-audit receipts. Fresh sampled checks cover90 inherited,
90 canonical NPZ/noise and87 stage NPZ/noise bindings. All63 frozen files and
parent/resource identities unchanged; no new simulations or production edits.
Verdict remainsPARTIAL until the last audit completes. See the
[check summary](../../quick/261118-ogi-check-completed-priortilt-fig1-results-a/SUMMARY.md),
[all PriorTilt rates](../../quick/261118-ogi-check-completed-priortilt-fig1-results-a/PRIORTILT-TABLE.md)
and [status CSV](../../quick/261118-ogi-check-completed-priortilt-fig1-results-a/comparison-snapshot.csv).

## Separate XYZ Table4 extension — quick261118-p8c

The user additionally requested XYZ reproduction with50 processors per point.
A separate immutable study now runs the published BB144/p=.003 Table4 comparison
with full joint detector models:PriorTilt60+6000x6 and RelayBP-5 80+600x60,
five converged candidates and first minimum original-prior LLR score. Both
RUNNING array62102101 tasks0/1 allocate50 CPUs/96GiB each; collector62102102
is dependency-pending. All100 production decoder processes initialized with
matching source-model identities. New relay-list policy reuses the unchanged
canonical sweep; no frozen XZ controller or original plan changed.

95 regression cases pass.50-CPU qualification62100693 passes24 matched native
Relay cases and128 actual full-budget XYZ pilot events, full original-DEM audits,
all-shot serial candidate/work/trace replay and unchanged resume receipts.
Initial62100295 stopped before simulation on node-local reference availability;
identical pinned native builds are now staged in a shared licensed archive.
Sparse author H/A/priors match exactly for the1728-check,67824/67752-fault
joint models. Paper source LERs are1.039392e-5 and1.095698e-5; no local XYZ
agreement claim yet.20-error/100M per-basis stopping and audited-only publication
apply. All63 original frozen files are unchanged. The original XZ campaign is
now39/39 worker-audited; its independent collector61971020 continues the large
publication refresh. This extension does not close the parent scientific gates.

See [XYZ campaign](../../../data/reproductions/priortilt-2611-13373-xyz/README.md),
[launch/qualification summary](../../quick/261118-p8c-qualify-and-launch-paper-xyz-priortilt-a/SUMMARY.md)
and [launch verification](../../quick/261118-p8c-qualify-and-launch-paper-xyz-priortilt-a/launch-verification.json).
Future XYZ refreshes use that study's report.py; the XZ publisher is unchanged.
