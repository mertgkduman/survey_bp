---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: 11
current_phase_name: Quaternary Reproduction and Comparisons
current_plan: 17
status: executing
stopped_at: Advanced BP kernel tuning running. Confirmation jobs and collector 62150056 depend on training.
last_updated: "2026-11-19T20:24:05.587Z"
last_activity: 2026-11-19
last_activity_desc: Launched 11 advanced decoder anchor pairs at 20 CPUs per point. XZ PriorTilt, RelayBP-1 and BeamSearch on BB144/.003 and BB70, GB102/.001, plus XYZ PriorTilt and RelayBP-5 on BB144/.003. Original 18060/18080 XZ and 36060/36080 XYZ caps and Beam340 per-path cap and width32 verified. Screen difficult syndromes using neutral BP40, then nine damping settings, scale/offset refinement, held-out selection and unfiltered confirmation. Passed 72 neutral equivalence checks, non-neutral trace audits, range guard, end-to-end pilot and 95 regressions. Screen 62150027/28/30/31, tuning arrays 62150032/36/48/52, collector 62150056. Verified running screens and tuning tasks. Original XYZ/XZ and ordinary follow-up runs preserved.
state_head: d105c23f8c6f14c0e31e964716e187ea46b3258a
progress:
  total_phases: 15
  completed_phases: 9
  total_plans: 179
  completed_plans: 163
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-12)

**Core value:** Make BP decoder differences explicit, reproducible, and fairly comparable through canonical policy execution and published evidence.
**Current focus:** Phase 11 — Quaternary Reproduction and Comparisons

## Current Position

Phase: 11 (Quaternary Reproduction and Comparisons) — EXECUTING
Plan: 17 of 25
Total Phases: 15
Current Plan: 17
Total Plans in Phase: 25
Status: Executing Phase 11
Last activity: 2026-11-19 — quick 261119-ibq launches advanced decoder kernel tuning
Last Activity Description: Launched 11 advanced decoder anchor pairs at 20 CPUs per point. XZ PriorTilt, RelayBP-1 and BeamSearch on BB144/.003 and BB70, GB102/.001, plus XYZ PriorTilt and RelayBP-5 on BB144/.003. Original 18060/18080 XZ and 36060/36080 XYZ caps and Beam340 per-path cap and width32 verified. Screen difficult syndromes using neutral BP40, then nine damping settings, scale/offset refinement, held-out selection and unfiltered confirmation. Passed 72 neutral equivalence checks, non-neutral trace audits, range guard, end-to-end pilot and 95 regressions. Screen 62150027/28/30/31, tuning arrays 62150032/36/48/52, collector 62150056. Verified running screens and tuning tasks. Original XYZ/XZ and ordinary follow-up runs preserved.

Previous source-scoring audit:
Last activity: 2026-11-17 — quick261117-h97 audits author syndrome versus observable success
Last Activity Description: Current public Rust/Python/adapter/simulation-helper blobs match pinned8eefd37d694b5942fe60ec6d5c82ce97f3d2a450. PriorTilt checks H ehat=s after each sweep for early stopping; on exhaustion returns last vector with convergefalse. Python always projects A ehat, and Sinter receives only predicted observable bits without convergence gating/discard, so released workflow scores observable mismatch alone. Actual unmodified author native+single+packed adapter proof passes on reachable two-sweep toy: s110, H ehat000, A ehat=A e=1, convergencefalse. Literal joint failure adds nonconverged/observable-correct events. Existing canonical BB144/.002 Z-memory has one such shot (20 observable errors versus21 joint failures on1,192,846 recorded shots); this is our data, not historical author statistics. Published author CSVs lack joint flags. Native binary matches frozen qualification; all assertions pass. Our reproduction already uses released observable-only scoring with joint counters retained. No campaign, metric, stop, frozen/source/kernel/model/public/v1/phase-gate/counter changes or simulation reruns; other collector outputs remain unstaged. Ten-CPU continuations remain active; use parallel_report.py for future refreshes.

Previous result check:
Last activity: 2026-11-17 — quick261117-guy checks ten-CPU PriorTilt progress
Last Activity Description: Resource-aware report now24/39 full-audited points (112,123,660 decoded basis shots/960 errors):PriorTilt7/13,Relay8/13,Beam9/13. New GB102 Beam/p=.001 is6.145e-7 LER/cycle versus source5.8e-7, within local95% interval; all24 source ordinates remain inside pointwise intervals and all23 earlier rows unchanged. No new PriorTilt point complete; saved GB102 PriorTilt/.001 progress is15/16 X/Z errors at9,486,336 shots each; BB70/.0008 is11 X errors and Z stopped20.15 ten-CPU workers61971019 continue without reported errors; collector61971020 pending. First completed parallel point's142 sealed stages and1,642 inherited markers rehashed; computed1,163,264 shots=1,056,051 retained+107,213 speculative, additive work/cohort totals reconcile and extra outcomes excluded from LER. Parent/resource identities valid, source/count/CI/work checks pass, final figure inspected. Production code unchanged; no repeated software tests or simulations; other collectors' dirty outputs remain unstaged. Frozen/kernel/source/v1/model/public/phase gates/counters preserved; spike060 remains PARTIAL. Use parallel_report.py for future refreshes.

Prior resource migration:
Last activity: 2026-11-17 — quick261117-fdl moves remaining Fig1 points to ten CPUs each
Last Activity Description: User explicitly superseded one-CPU allocation. Array61971019 resumes all16 unfinished points on10 CPUs/24GiB each (160 point CPUs); all16 observed RUNNING with AllocCPUS10 and real resumed points sealing batches from ten distinct worker PIDs. New collector61971020 pending; only after replacement submission,16 old active tasks61946754 and collector61946755 intentionally cancelled. Original23 completed audits/CSV preserved and all63 frozen parent files unchanged. New separately pinned resource amendment (da570e399be73f21d768d015c124b02fb5ee82796bda498effa284e8ddeb6a22) adds ordered concurrent sealed batches, exact global-shot stopping prefixes, separate speculative-work archive, inherited marker-hash snapshots and ten-process fresh full audits. Qualification61970828 completes0:0 on10 CPUs:480 full-budget pilot events across PriorTilt/Relay/Beam match frozen sequential candidates/predictions/stats/traces bitwise; inherited prefixes/audits/resume pass.51 targeted regressions pass. Concurrent timing cohorts are explicit; saved input bytes authoritative under existing Stim producer protocol. Use parallel_report.py for future report refreshes. No canonical/scientific plan/source/v1/model/public/phase-gate/counter changes; other collectors' pre-existing outputs remain unstaged. Campaign remains running; spike060 PARTIAL.

Previous PriorTilt result check:
Last activity: 2026-11-17 — quick 261117-exr checks new PriorTilt results
Last Activity Description: Published23/39 full-audited points (97,616,345 decoded memory-basis shots/920 observable errors):7 PriorTilt and8 each Relay/Beam. New PriorTilt BB144/p=.002 is2.723e-6 versus source2.467e-6 LER/cycle; BB70/p=.001 is3.958e-7 versus4.678e-7. Both and all23 source ordinates lie within local pointwise95% intervals, ratios0.771–1.253. PriorTilt has the lowest estimate at all seven complete three-method strata. Independent source/count/CI/work/receipt checks pass; all19 previous rows and63 frozen identities unchanged; final figure inspected. Sixteen one-CPU workers61946754 continue without reported failures; collector61946755 pending. Unfinished counts remain progress only. Production code unchanged, regressions not repeated for a data-only update. Sixteen pre-existing dirty files from other collectors/public catalog remained outside staging. No simulation/source/kernel/v1/model/phase-gate/counter changes; spike060 stays PARTIAL.

Previous PriorTilt check:
Last activity: 2026-11-17 — quick 261117-077 checks PriorTilt Fig1 progress
Last Activity Description: Published19/39 full-audited points (24,299,037 decoded basis shots/760 observable errors):5 PriorTilt,7 Relay and7 Beam. All19 paper ordinates are within local pointwise95% intervals; all15 previous point records and63 frozen identities remain unchanged. Four new comparison points are Relay/Beam at BB144/.002 and BB70/.001; no new PriorTilt point has finished. Saved PriorTilt progress is BB144/.002 at778240/770048 X/Z shots and10/13 errors; BB70/.001 at5029888/5021696 shots and10/12 errors, retaining20-error/100M per-basis stops without provisional rates.20 one-CPU workers61946754 continue without reported failures; collector61946755 pending. Independent source/count/CI/work/receipt reconciliation passes; plot inspected. No production code or simulation changes, regressions not repeated for data-only update; source/raw/kernel/public/v1/model/phase gates/counters preserved. Spike060 remains PARTIAL.

Previous PriorTilt check:
Last activity: 2026-11-16 — quick 261116-ta4 checks PriorTilt Fig1 progress
Last Activity Description: Published 15/39 full-audited pairs (2,838,888 decoded basis shots/600 observable errors), including 5/13 PriorTilt points and all three methods at five complete strata. All 15 source ordinates lie inside local pointwise 95% intervals, ratios 0.771–1.253. Late BB144 PriorTilt/p=.003 gives5.574e-5 versus source5.741e-5. PriorTilt has the lowest estimate at all five strata; BB70/p=.002 is about1.89x below Relay and2.84x below Beam at paper settings.24 single-CPU workers61946754 continue; collector61946755 pending. Independent source/count/CI/work reconciliation passes and all14 earlier point records/frozen63-file identities are unchanged. Both14-point and final15-point assessments are preserved; final figure inspected. No simulations, canonical/frozen/source/public/v1/model/phase gates/counters changed. Spike060 remains PARTIAL.

Prior PriorTilt snapshot and OSD explanation:
Last activity: 2026-11-16 — quick261116-rf9 checks PriorTilt Fig1 and OSD-CS speedup
Last Activity Description: Published7/39 full-audited PriorTilt memory pairs (345,963 decoded basis shots/280 observable errors); all seven paper ordinates fall inside local pointwise95% intervals, ratios.958–1.253. At BB144/p=.005 PriorTilt/Relay/Beam estimates .005509/.009532/.010883 preserve the source ordering with overlapping intervals.32 single-CPU workers61946754 continue; collector61946755 pending. Frozen63-file identity and source/count/CI/work/receipt hashes independently reconcile;13 affected regressions pass and figure inspected. Warm standalone uniform-channel CS10 benchmark implementation hash still matches;2.32–3.53x versus pinned native -O3 -march=native comes from reused affine flip responses, packed XOR and popcount, excluding BP/JIT and broader speed claims. No simulation or native benchmark reruns; no old raw/frozen/source/kernel/public/v1/model/gate/counter changes. Spike060 remains PARTIAL pending full campaign.

Prior PriorTilt launch:
Last activity: 2026-11-16 — spikes058–060 launch exact PriorTilt Fig1 circuit reproduction
Last Activity Description: Reviewed project goals and2611.13373v1; pinned exact26 X/Z memory circuits,78 source basis rows,39 source figure points and full-precision three-phase schedules. New transient-prior and source-specific Beam/Relay controllers use unchanged canonical float64 min-sum sweep; independent math, native144 controller cases,144 ordinary-BP numeric probes and624 full-budget pilot events pass, alongside348 regressions. Canonical/native reduction-order drift remains explicit (strict-state failure preserved); no source LER agreement claimed. Frozen39-point array61946754 has one CPU/3GiB per point, X/Z sequentially, independent policy RNG and shared sealed Stim samples,20 observable errors or100M shots per basis. All39 observed RUNNING; fresh-process original-DEM full audits use same CPU allocation; dependent collector61946755 queued. Initial source-only report0/39 local points inspected; no provisional bounds published. Work retains all-path sweeps/directed updates, typed random/bias operands and instrumented latency separately. Existing raw data, prior frozen kernels/campaigns, public catalog/v1, model config and phase gates/counters unchanged. Spikes058/059 VALIDATED within stated scope;060 PARTIAL while production continues.

Prior paper-figure and result activity:
Last activity: 2026-11-16 — quick 261116-ote checks results and adds paper figure views
Last Activity Description: Clickable paper titles open named figures with default-on paper reproductions and default-off additional comparisons, group/mixed-state controls, scoped exports and unchanged central multi-rate eligibility. Source-backed metadata preserves Yao figure conflicts, Roffe CS60 versus local CS10/OSD0, MacKay inferred budget/metric limits and LP Example 4 without a fabricated LER figure. New imports and stale selections reconcile; 88 relevant tests and 14 Chromium groups pass after scoped fixes. Gamma 6/12 strata audited (24 fresh policies, 6525 shots/480 failures, 1322 training settings); p=.06 source/tuned gamma LER .02522/.01784 versus BP140 .04301/.01921, overlapping intervals. At p=.06 both select gamma0=0. Additional p=.08/.10 results are mixed, with overlapping intervals in all six comparisons. Original LP 70/72 audited (11,236,743 shots/1400 failures); new p=.02 Beam32 and QBP+CS10 LERs 7.35e-6/8.12e-6 overlap. Outstanding workers/audits continue unchanged. Public counts 448/3207/13/0 with five multi-rate gamma-study curves, all 1543 prior raw point multisets preserved. No frozen/raw/kernel/v1/model/phase-gate/counter changes.

Prior gamma launch:
Last activity: 2026-11-16 — quick261116-nf0 launches Relay gamma80/60 tuning
Last Activity Description: User confirmed exactly80 uniform-gamma +one60 disordered-gamma leg, max140/component. New frozen lp1054-relay-gamma80-60 retains parent code/rates and unchanged canonical/search kernels. Source and parent training-selected numerical backgrounds,11 gamma0 values×18 intervals+zero control=199 coarse policies/point; independent finalist/refinement/fresh seeds and separate memory RNG. Fresh selected/phase ablations/reset-zero/matchedBP140 stop20 failures or100M, exact-control duplicates deduped. Typed gamma work and external-hash-free controller timing explicit;1024-shot atomic chunks and deadline requeue. Array61942447 has12 single-CPU/3GiB workers with fresh-process audits in same allocations; collector61942448 queued.64 scientific tests,56 catalog tests,11 Chromium groups and96 pilot shots pass; frozen/source/parent pins remain valid. Initial workers tuning; no fresh gamma measurements yet. Public443/3194/13/0 unchanged and1543 old raw-series point multisets preserved. No old frozen/raw/canonical/v1/model/config or phase gate/counter changes.

Prior lifted-product result check:
Last Activity Description: LP1054 campaign68/72 simulations complete;68 full audits published(6,054,571 fresh decoder shots/1,360 failures,1,892 separate training settings). Four p=.02 simulations(Q-BP+CS10,tunedQBP,beam32/128) continue; both late tunedBP/Relay128 p=.02 full audits completed and are included. Existing one-CPU allocations/stopping and collector61930188 retained; eight satisfied audit dependencies released with verified source0:0 and hashes. Independent1,960-summary/manifest/count/interval/work/selection/source reconciliation passes. At p=.06/.08, joint CS10 LER3.17e-4/6.68e-4 is5.38x/16.33x lower than tunedQBP; .04 intervals overlap. Current binary search does not match joint OSD at middle rates;128 permits4x directed-edge work. Scientific3-panel PNG/PDF inspected. Public443 curves/3194 points/13 codes/0 circuits; all1538 historical point multisets preserved.55 catalog tests and11 Chromium groups pass. Original paper has no1054 source LER grid/cap; borrowed32/.625, schedule difference and provenance-instrumented timing remain explicit. No new simulations, frozen/raw/kernel/v1/model/config/phase-gate/counter edits; campaign remains running. Late p=.02 tuned BP LER1.20e-5(113x below baseline) and Relay1281.49e-5 have intervals overlapping joint OSD0(1.85e-5); no rare-point superiority claim.

Prior original lifted-product launch:
Last Activity Description: User-selected original Panteleev–Kalachev2012.04068v2 Example4 reconstructed as LP1054/k140/ranks457+457, independently checked against polynomial coefficient expansion. No source LER/grid/cap exists for1054; controlled depolarizing .02/.04/.06/.08/.10/.12 and NMS32/.625 borrowed from cited1904.02703 are explicit adaptations with flooding/layered schedule difference. Twelve families/variants per rate, including ordinary/correlated BP+OSD0/CS10, BP/QBP numerical tuning and Relay/beam32/128. One CPU per point, disjoint coarse/finalist/fresh seeds,20 failures or100M fresh shots. Frozen array61930050, point audits61930127 and collector61930188 continue. Snapshot50/72 workers:273,537 shots/1,000 failures,1,140 separate training settings,12 displayed compatible curves/44 displayed points. Public440 curves/3178 points/13 codes/0 circuits; all1520 prior series point arrays unchanged.20 new/61 unique scientific tests,55 catalog tests and16 browser groups pass, including new LP input/stale exports and final13-code public flow; old NFS cleanup-only flake passes retry. Provenance-instrumented timing scope documented. Prior beam frontier now218/218/642 settings/271.66M shots in separate9dba3da. No canonical/prior frozen/raw/v1/model/config/phase-gate/counter changes; campaign remains running. Implementation53fabae.

Prior beam/RelayBP check(earlier snapshot, superseded by automatic full collector):
Last Activity Description: Original218-worker/full-audit campaign complete(616 settings/11,477,871 shots). Broader snapshot215/218 passes unchanged full-ledger/reference/endpoint/proposal/source audits via61875143(8 CPUs/16GiB,8m50s):639 fresh settings/27,243,865 shots/12,780 failures,2,063 separate training measurements. Independently reconcile1,255 old/new summaries/manifests/hashes/counts/stopping/CI/work/ratio/selection. At X-only p=.02,1x-role beam LER4.65e-5/2.70e-5/3.47e-6 on lengths162/242/338 uses.490/.366/.216 times same-CPU OSD0. Length162 intervals overlap;242/338 estimates remain3.0x/2.5x higher than OSD0. Beam242 improves14.8x versus first search; Relay remains less accurate at these examples. Actual1x budget fits93/106 beam,92/109 Relay;30 over-budget rows flagged. Three beam rare points(242/.01,450/.01,450/.02) remain active; no provisional rate/bound published. Full tables/role comparisons/PNG/PDF saved. Public427 curves/3132 points/12 codes/0 circuits; all800 historical raw series retain point subsets.53 regressions/12 Chromium groups pass, including empty/stale/custom/v1 flows. No simulations or frozen/raw/kernel/config/gate/counter changes; automatic final collector61870315 still awaits remaining workers.

Prior beam/RelayBP launch: 2026-11-15 — quick261115-sxj tunes beam search and RelayBP against OSD latency
Last Activity Description: Canonical-sweep beam/RelayBP traversal passes128 exact real-code scalar-oracle cases,80 unique regressions and12 final Chromium groups. First array61869371 completed218/2180:0; full audit61869372 runs. Completed-worker snapshot deeply audits114 workers/277 fresh settings/3,297,851 shots/5,540 failures plus23,839 training measurements. At length242/p=.02 beam LER4.01e-4 and Relay2.68e-4 use.145/.166 times same-CPU OSD0 time, improving earlier BP .161 but above OSD0 8.87e-6. Initial coarse zero-failure ties underused budgets; separately frozen training-only frontier (array61870314, audit61870315) retains budget-spanning/multiple-solution arms and uses new finalist/confirmation seeds1562/1563. Adaptive timing documented; no parent confirmation outcomes enter its selector. Source-dependent215 task releases verified sacct/completion hashes after Slurm cache expiry, without changing science or collector dependencies. Central normalized catalogs now registered; complete search state guards evidence identity. Public324 curves/2667 points/12 codes/0 circuits; all547 historical raw series unchanged.277 raw measurements remain in full report/CSV, singleton concrete policies excluded centrally. Full settings, pointwise intervals, all-path mean sweeps/edge updates and measured latency quantiles preserved. PNG/PDF inspected. Both studies/audits continue; no old frozen/raw/canonical/v1/config/model or Phase11 gate/counter changes.

Prior completed runtime-budget activity: 2026-11-14 — quick261114-pna checks completed runtime-budget and related results
Last Activity Description: All218 runtime workers and collector61824236 complete0:0. Independently reconciled1464 fresh rows/249,888 shots/29,280 failures plus218 frozen selections;163,668 tuning rows remain separate. Only1/107 extended-cap BP strata improves LER; joint-control median LER and mean-iteration ratios remain1.00 across the grid. Offset zero selected217/218; alpha magnitude1 selected217/218. Actual selected timing145/218 within10%,36 over1.1 and37 below.9, so strict runtime claims use qualified subsets. At p_X=.02, same-channel BP remains orders of magnitude above OSD0. Full434MiB verification and70MiB tuning CSV retained locally and committed losslessly as gzip with byte hashes/roundtrip checks; no raw data or source edits. Refreshed public308 curves/2627 points/12 codes/0 circuits; old227 raw-series point subsets preserved.52 regressions and7 real-data browser groups pass. MacKay T100 confirmation now40/40(112,619,245 shots/791 failures); rare274 QBP point100M/11 failures ends at1.1e-7. OSD212 fully audited points retained; four length450 points run, two completed338/p=.01 points await final OSD audit. Checked findings/figure/selected-point CSV linked from study RESULTS.md. No new simulations, canonical/frozen/v1 changes or phase gate/counter changes.

Prior runtime-budget launch activity: 2026-11-14 — quick261114-lhw prepares joint-control tuning and runtime-matched iteration studies
Last Activity Description: Separately versioned traversal calls unchanged canonical binary/Pauli sweep helpers;144 exact candidate/belief/stopping checks pass across damping/scaling/offset. Joint search has80 coarse controls plus local refinement, then4096-shot finalist training and fresh20-failure/1e8-shot confirmation. Preserve each candidate/cap and earlier damping progression; match mean warmed same-CPU BP+OSD0 time within10%, with explicit saturation/over-budget status. Original109 code/rate grids retained for both families; BP X-only and Q-BP depolarizing1.5p remain distinct. Pilot finds Q-BP at T=n can already exceed reference1.2–6.6x, so lower caps are retained alongside n-cap controls. Real full search tested102 controls/963 control-caps,10 shortened confirmation caps/699 shots, exact resume/full audit; these qualification samples are not pooled.65 regression cases and12 Chromium groups pass, including exact scale/offset labels and time/reference CSV column. Frozen218-worker campaign launched as61824235 with complete collector61824236; workers have begun calibration/tuning, with first45 fresh control/cap measurements now independently audited(36,041 shots/900 failures), six completed point workers and5,496 retained training measurements. Active117 curves/1258 points/12 codes/0 circuits; all189 prior raw series unchanged and seven real-data browser groups pass. Remaining points continue; this is a partial snapshot. One CPU/2GiB per worker, one CPU/16GiB collector. Initial unlaunched2GiB-collector plan/source preserved; scientific design unchanged. Public112 curves/1246 points/12 codes/0 circuits before launch, with singleton/incompatible-policy filtering unchanged. No canonical, prior frozen simulation, v1 or phase-gate/counter changes.

Prior OSD check activity: 2026-11-14 — quick261114-i9b checks current OSD results and explains source-matched performance
Last Activity Description:212/218 terminal points contain318,346,784 decoder shots/4,207 logical failures. Frozen manifests, summary arithmetic/stopping/exact95% CI/work and424 endpoint replays pass. Six rare points remain running: both methods on338/p=.01 and450/p=.01/.02; four zero-failure progress counts are50–77M shots and are not final estimates. At p=.02 the three completed codes have similar OSD0/CS10 LERs with overlapping intervals; damped BP is orders of magnitude worse. Same-CS10 native -O3 -march=native rebuild preserves64 selected outputs and yields2.32–3.53x warmed ratios; packed affine reuse/popcount explain the changed implementation, without a paperCS60 or generic speed claim. Full318M-row refresh runs as61820674; final complete collector61820676 is serialized behind it and the original array. Replaced61805014; prior retry61805013 already completed0:0. Fresh summary/endpoint snapshot and all109 comparison rows are saved separately; workbench retains fully audited173-point OSD snapshot112 curves/1246 points/12 codes/0 circuits pending full refresh, byte-identical to02f802a. No raw/frozen/canonical/native/v1/phase-gate changes. Evidence commit2c8b6fe.

Prior OSD implementation activity: 2026-11-14 — spikes056–057 qualify efficient canonical BP + OSD-0 / CS-10 and prepare production dispatch
Last Activity Description: Public OSD source pinned at d3429964cd4ffe1abfc041c6ec8b8425cb174f40;404 complete native/independent-oracle candidate sets pass. Packed source-derived CS10 achieves2.1–3.4x native final-only throughput; OSD0 costs33–55us with full provenance. The unchanged canonical sweep is called from a separate compiled traversal, with436 bitwise terminal-state and192 complete-event comparisons across109 source strata.128 qualification shots/72 OSD calls pass resume, full-ledger, endpoint and publication checks. Frozen campaign roffe-2005-07016-osd-fast has218 points, X-only/min-sum/alpha schedule/T=n,20 logical failures or1e8 shots, one CPU per point, separate BP/OSD work and timing. Superseded frozen scalar controller remains unlaunched.100 unique tests and12 Chromium workflow groups pass; prelaunch catalog104 curves/1073 points/12 codes/0 circuits, historical points unchanged. No canonical kernel, frozen prior campaign, v1, generic Phase7 admission or Phase11 gate/counter changes. Implementation a4497da is pushed; array61804747 is running. First173/218 points pass full-ledger/endpoint audit:153,881 shots/3,460 logical failures,88 OSD0/85 CS10. Public112 curves/1246 points/12 codes/0 circuits; all181 historical raw series unchanged. Seven real-data browser groups pass. One NFS cache failure before sampling recovered unchanged as61805013; replacement complete collector61805014 depends on initial-array termination and retry success and still enforces all218 terminal points. Report/CSV include paperCS60 and earlier BP/dampedBP/QBP alongside new methods; pending points stay unavailable.

Prior source comparison activity: 2026-11-13 — quick261113-vj0 tabulates Roffe paper BP-OSD against confirmed BP-family results
Last Activity Description: Added all108 main-panel Figure3 BP+OSD-CS lambda60 source ordinates and109 ordinary-BP source-rate rows alongside436 local confirmed measurements. Tables preserve the missing length450/p=.01 value, undefined author samples/work, source error-bar semantics and separate noise channels. At X-only p=.02, source BP-OSD LER is about2,200–1.2M times below damped binary BP estimates, with additional elimination/search work. Complete Markdown/CSV, source hashes and PNG/PDF are in roffe-2005-07016-osd-comparison; linked from damping RESULTS.md. Passed22 source/join/damping/unchanged-plan tests; public catalog remains byte-identical104 curves/1073 points/12 codes/0 circuits. No simulations, canonical/frozen/source or measured-data changes. Phase11 gates/counters unchanged; MacKay rare point continues separately.

Prior Roffe damping activity: All1526 tuning points and436 fresh confirmation points pass the original full audit; independent re-reading reconciles all436 raw ledgers and the completed receipt. Confirmation retained47,473 shots/8,720 failures. Selected BP d=.5 and Q-BP d=.3 on all four codes, preserving paper grids/min-sum/T=n. At matched X rate.02, Q-BP depolarizing p=.03 LER estimates improve15–21x versus its own undamped controls; ordinary BP improvements are smaller. Equal-rate mean LER decreases3.4–16.3% for BP and20.8–35.1% for Q-BP; mean iterations decrease2.9–10.8% and19.4–31.9%. These are descriptive20-failure results with different channels across families. Final collector61794901 failed only after audit/normalization at duplicate Roffe paper metadata; exact-equality paper merging now repairs future rebuilds and rejects conflicts. Public104 curves/1073 points/12 codes/0 circuits; all165 prior raw series/points unchanged. Saved full CSV/report/assessment/four-panel figure. Passed62 tests and16 Chromium groups. No frozen/kernel/runtime/publisher/v1 changes or new simulations. Separate MacKay rare point remains running, last observed33.79M shots/3 failures. Phase11 gates and counters unchanged.

Prior Roffe assessment: Roffe collector61785160 completed0:0 and fully audited/published218 points (9,816 decoder shots/4,360 failures). Quick261113-p1r independently checks source coordinates, counts, work, stopping intervals and receipt hashes: all109 ordinary-BP paper values lie inside pointwise95% intervals; maximum point-estimate deviation22.3%. Four-panel overlay and complete tables are in the Roffe study. Agreement is scoped to current20-failure precision and X-only ordinary BP, with no simultaneous curve/native numerical identity or BP-OSD claim.109 Q-BP/depolarizing points remain separate. Source archive re-extraction and frozen40-pin plan pass. Passed54 catalog checks and12 browser groups; public88 curves/637 points/12 codes/0 circuits. All157 prior raw series/points unchanged, no canonical/frozen/v1 edits. Roffe is complete; MacKay's separate rare point remains running. Phase11 gates unchanged.

Completed campaign: See the [paper-rate task summary](./quick/261112-k9m-run-mackay-bp-campaign-at-the-five-publi/261112-k9m-SUMMARY.md). Source-plot coordinates and the exact five rates are pinned. The retained historical curves used 20 block failures or 100 million shots per rate and the 88,200 total-sweep ceiling; the new inferred-budget campaign is recorded above. Classical errors are recorded separately from quantum failures. No full-curve agreement is claimed.

Completed historical MacKay campaign: Array 61698133 and collector 61698134 completed with exit 0:0. All 42 points, 2,366 shots and 840 block failures are audited. These controlled wide-grid results remain preserved; the subsequent paper-grid correction retires them from public v2 views.

Completed campaign: The frozen BPGD/Q-BP design and the verified result snapshot are recorded in the [quick task summary](./quick/261110-sic-complete-b1-and-c2-bpgd-and-matched-q-bp/261110-sic-SUMMARY.md). Slurm arrays 61550993–61550995 and final collector 61550996 are complete.

Prior work metric activity: Quick task 261111-f0q added adjacent mean iterations and mean directed edge updates per shot to results tables and CSV exports, with both quantities selectable for plots. Historical component means, exact graph sizes, imported component counters, and sample-weighted pooling preserve the work definitions. Passed 124 research tests and 18 Chromium workflow checks. Implementation `324b53a`.

Prior plot activity: Quick task 261110-oou adds superscript labels for powers of ten and lighter logarithmic gridlines. Visible curves and confidence intervals determine the plot limits. Chromium verified matching axes after hiding curves or selecting a decoder directly. Implementation `8d35f04`.

Prior literature activity: Spikes 054-055 screened citation prominence and independently verified primary-paper BP baseline evidence. Saved twelve direct standalone-BP comparisons, two code benchmarks, two related hybrids and one specialized min-sum hardware study. OpenAlex counts are a dated single-record snapshot, with duplicate/edition caveats; global top-N completeness is not established. See `.planning/spikes/055-bp-baseline-source-check/PAPERS.md`. No simulation, kernel, UI or phase-status change.

Prior builder activity: Quick task 261110-lsd adds Request experiment results beside package download. Validation enables it; edits and invalid state clear it. The action prepares an exact downloadable portable specification and a SHA-256-bound GitHub issue draft for the user to review and submit. Verified with 12 browser workflow groups; no issue submissions or simulations. Implementation: `7b8e702`.

Prior picker activity: Quick task 261109-mzx filters each add-curve picker by visible curve identity before prefix matching. Hidden curves restore without duplicate entries; compare-all has an explicit empty state. Verified with 16 browser workflow groups and JS syntax/diff checks. Implementation: `1e6b825`.

Prior interface activity: Quick task 261109-mcf centrally filters active v2 curves to at least two distinct measured error rates and derives public input/saved choices from that view. Counts: 105→63 curves, 361→319 points, 7→6 codes, 3→0 registered circuits. Verified with 118 research tests, 14 browser workflow groups and real retained-result imports. Empty/default/import selection handling passes; raw catalog, evidence and v1 bytes are preserved. Implementation: `7eeddf7`.

Prior kernel activity: Quick task 261109-hhq rejects invalid changing-prior PD-prime compositions and gives new shared Sinter execution observation-v2 identity with exact shared-v1 replay. Final production regression: 1,712 passed, 20 skipped; final shared decoder tests: 161 passed (overlapping suites). Real Sinter worker: 24 verified v2 shots; earlier shared-v1: 15 ledgers / 58 shots replayed; 82 legacy receipts byte-identical. Scanned and hashed 3,839 tracked data/experiment files without finding an affected campaign; all remain unchanged. Prior mathematics, upstream and GPU evidence is carried by source/evidence hashes. HTML can consume the qualified inventory; scientific publication gates remain unchanged. See spikes/CANONICAL-KERNEL-SHARED-POLICY-FIXES.md.

Progress: 8 of 14 phases complete ([██████░░░░] 60%); 159 of 176 plans complete. Phase 11 has 17 of 25 plans complete; plan 17 is the first open number but depends on source reviews 18 and 19, while plan 20's blocked-target review is complete.

## Performance Metrics

- Total plans completed: 159
- Average duration: N/A
- Total execution time: 0 hours
- Recent trend: Phase 11 completed 15 original and 2 gap-closure plans. Its source-curve, controlled-effect, and policy-replay evidence remains incomplete; publication dispatch remains denied.

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 02 P01 | 18m | 2 tasks | 9 files |
| Phase 02 P02 | 17m | 2 tasks | 6 files |
| Phase 02 P03 | 7m | 2 tasks | 6 files |
| Phase 02 P05 | 13m | 2 tasks | 5 files |
| Phase 02 P04 | 7 min | 2 tasks | 4 files |
| Phase 02 P06 | 8 min | 2 tasks | 7 files |
| Phase 02 P07 | 10 min | 2 tasks | 3 files |
| Phase 02 P08 | 8 min | 3 tasks | 10 files |
| Phase 02 P09 | 16 min | 2 tasks | 7 files |
| Phase 04 P01 | 31m | 2 tasks | 10 files |
| Phase 04 P02 | 6m | 2 tasks | 3 files |
| Phase 04 P03 | 18m | 2 tasks | 4 files |
| Phase 04 P04 | 11m | 2 tasks | 9 files |
| Phase 04 P05 | 14m | 2 tasks | 4 files |
| Phase 04 P07 | 67s | 1 tasks | 1 files |
| Phase 04-memory-policies-and-relay-bp P06 | 417 seconds | 2 tasks | 6 files |
| Phase 04 P08 | 25m | 2 tasks | 5 files |
| Phase 04 P09 | 14m | 2 tasks | 5 files |
| Phase 04 P15 | 22m | 1 tasks | 5 files |
| Phase 04 P10 | 58m | 2 tasks | 8 files |
| Phase 04 P11 | 0 | 2 tasks | 73 files |
| Phase 04 P12 | 4d | 2 tasks | 2 files |
| Phase 04 P13 | 2026-09-30 | 2 tasks | 4 files |
| Phase 05 P01 | 15min | 1 tasks | 5 files |
| Phase 05 P02 | 8min | 2 tasks | 6 files |
| Phase 05 P03 | 8min | 2 tasks | 7 files |
| Phase 05 P04 | 12min | 2 tasks | 2 files |
| Phase 05 P05 | 10min | 2 tasks | 2 files |
| Phase 05 P06 | 18min | 3 tasks | 3 files |
| Phase 05 P07 | 12min | 2 tasks | 2 files |
| Phase 06 P01 | 14m | 2 tasks | 5 files |
| Phase 10-correlated-quaternary-execution P01 | 482 seconds | 1 tasks | 7 files |
| Phase 10-correlated-quaternary-execution P02 | 10m | 2 tasks | 4 files |
| Phase 10-correlated-quaternary-execution P13 | 7m | 2 tasks | 3 files |
| Phase 10 P03 | 4m | 1 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P04 | 8m 14s | 2 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P05 | 8m 10s | 2 tasks | 4 files |
| Phase 10 P06 | 10m 14s | 2 tasks | 2 files |
| Phase 10-correlated-quaternary-execution P07 | 33m | 2 tasks | 5 files |
| Phase 10 P08 | 7m | 2 tasks | 6 files |
| Phase 10-correlated-quaternary-execution P09 | 7m | 2 tasks | 6 files |
| Phase 10 P10 | 12m | 2 tasks | 4 files |
| Phase 10 P11 | 11m | 1 tasks | 4 files |
| Phase 10 P12 | 10m | 2 tasks | 7 files |
| Phase 10 P15 | 22m | 2 tasks | 5 files |
| Phase 10 P16 | 3h 23m bounded run plus verification | 2 tasks | 8 files |
| Phase 11 P01 | 3m 27s | 2 tasks | 6 files |
| Phase 11-quaternary-reproduction-and-comparisons P07 | 322s | 2 tasks | 3 files |
| Phase 11 P02 | 12m | 2 tasks | 8 files |
| Phase 11-quaternary-reproduction-and-comparisons P04 | 17m | 2 tasks | 4 files |
| Phase 11 P08 | 8m 38s | 2 tasks | 4 files |
| Phase 11 P03 | 11m | 2 tasks | 5 files |
| Phase 11 P09 | 34m | 2 tasks | 5 files |
| Phase 11 P10 | 31m | 3 tasks | 8 files |
| Phase 11-quaternary-reproduction-and-comparisons P05 | 4m | 1 tasks | 1 files |
| Phase 11 P11 | 1028s | 2 tasks | 4 files |
| Phase 11 P06 | 7m | 2 tasks | 3 files |
| Phase 11 P13 | 11m | 3 tasks | 5 files |
| Phase 11-quaternary-reproduction-and-comparisons P12 | 11m | 3 tasks | 5 files |
| Phase 11 P15 | 666s | 3 tasks | 6 files |
| Phase 11 P14 | 1h | 3 tasks | 6 files |
| Phase 11 P16 | 30m | 2 tasks | 3 files |
| Phase 11 P20 | Not recorded | Review decision | Not recorded |

Phase 02 P10–P16 gap-closure metrics are recorded in their individual summaries.

## Accumulated Context

### Decisions

- Shared-policy audit 050–053 required no core mathematical redesign. F01 and F02 are closed in quick task 261109-hhq. Freeze the qualified interface with observation-v2 for new shared Sinter execution and explicit historical v1 replay. Repeated identical observations share randomness under the same policy/model; independent replicas require distinct seeds. Keep source-defined counterparts, explicit backend exclusions, old receipts and scientific result qualifications.

Full decisions are in PROJECT.md; workflow choices are in config.json.

- Policy expansion uses only existing/source-defined counterparts, per explicit user choice. `binary-policy-v1` shares compatible binary execution across CPU and circuit fault graphs. Preserve separate named Pauli equations and the qualified GPU subset; expose genuine operand/source/implementation exclusions in the capability inventory.

- Post-extension audit 043–046 supports ordinary BP mathematics and practical policy breadth without a kernel redesign. Its three bounded circuit contract findings were closed E03 → E01 → E02 in quick task 261108-oq5 / spikes 047–049. Use versioned extensions for future policies instead of reopening an unbounded audit. Preserve source-scoped reproduction claims and explicit backend subsets.

- First journal milestone includes CSS code-capacity → correlated quaternary code-capacity → circuit level; none is deferred beyond the paper.
- Canonical engines are defined per compatible kernel family. BP modifications are primary; OSD/LSD is optional additional processing for nonconvergence.
- Reproduction requires declared statistical agreement, not bitwise identity; source semantics and outcome correctness require separate checks.
- Preserve faithful source configurations and controlled shared-sample/work-budget comparisons as separate evaluation views.
- [Phase 08]: Paired canonical CSS campaigns freeze one physical sample for both arms, verify local and direct selected-shard deliveries independently, and report exact denominator uncertainty and merge provenance.
- [Phase 08]: The two-sample BB-144 run is development evidence only; site ceilings and scheduler accounting are unavailable, so production authorization remains denied.
- [Phase 09]: The 14-variant CSS inventory and capped Yao B1 run preserve unavailable source/native facts; EVAL-01/02 remain pending, and timeout terminals never become a paper-rate estimate.
- [Phase 09]: Three prospectively frozen matched controls completed at N=3, 16, and 2 with separate profiles, typed shared-work costs, and no decoder-superiority claim.
- [Phase 09]: Public controlled retry reuses sealed initial/member receipts and recovers orphaned sealed units into merge envelopes; publication Slurm stays denied without site limits.
- Autonomous execution, fine phases, parallel independent agents, Git-tracked planning, full instructions, research/checking/verification enabled; saved Codex model/effort overrides retained.
- Phase 1 selected a source-pinned Bravyi BB-144 artifact and kept its 32-shot native BP pilot labeled `pilot_adaptation` and `not_assessed`.
- Phase 1 preserves ordered CSS matrix/logical identity, strict manifest preflight, and a durable shot ledger with independent outcome evaluation.
- [Phase 02]: Canonical manifests require seven explicit policy roles, including named identity roles.
- [Phase 02]: Canonical selection freezes immutable decoder-visible candidates before independent truth-aware evaluation.
- [Phase 02]: Persisted canonical compositions require seven explicit closed-registry policy bindings.
- [Phase 02]: The engine owns lifecycle traversal and binding-private state; policies return typed decisions only.
- [Phase 02]: Each resolved policy binding carries a procedure basis and deterministic ordered invariants.
- [Phase 02]: Phase 02: binary-spa-flooding-f64-v1 fixes CPU float64 natural-log odds, symmetric K=25 saturation, and deterministic zero/tie rules.
- [Phase 02]: Phase 02: flooding reads one complete old v2c snapshot, then commits a complete new v2c buffer after c2v and belief phases.
- [Phase 02]: Canonical lineage IDs derive from typed logical parents and canonical content, never timing or append order.
- [Phase 02]: Canonical structural evidence uses a separate v2 grammar; optional semantic sidecars are confined, hash-linked, and observational.
- [Phase 02]: Phase 02: count budgets reserve complete typed sweep work before mutation, while wall-clock limits remain distinct declared-boundary controls.
- [Phase 02]: Phase 02: canonical work is committed only as unique leaf vectors and ancestor totals are derived by typed scope ancestry.
- [Phase 02]: Phase 02: iteration, runtime, and resource measurements retain schedule, unit, precision, method, scope, and explicit missingness.
- [Phase 02]: Native SDK iterations remain qualified observations and are never equated with canonical flooding work.
- [Phase 02]: Opaque native internals serialize as unavailable metric facts with reasons and availability-only summaries.
- [Phase 02]: Local standard-library profiling is default-on but retains explicit missingness and separately measured adapter overhead.
- [Phase 02]: Only pre-outcome representative paired cohorts with inclusion probability and semantic agreement can support profiling population estimates.
- [Phase 02]: Replay semantics compare candidate, termination, work, lineage, and trace digest while excluding measurement timing.
- [Phase 02]: Phase 02: public canonical experiments use a strict persisted CanonicalExperimentV2 while compact kernel contracts remain direct-test APIs.
- [Phase 02]: Phase 02: canonical results reconstruct from hash-linked v2 terminal evidence and retain canonical_implemented/development_fixture/not_assessed labels.
- [Phase 02]: Phase 02: canonical CPU runtime is measured per attempt and unavailable device timing is explicit missingness.
- [Phase 02]: Phase 02: public preflight reports persisted and resolved numerical profiles separately; canonical reconcile queries v2 terminals without changing legacy v1 repair semantics.
- [Phase 02]: Phase 02: profiling and selective tracing remain provisional diagnostic evidence pending campaign preregistration and corpus recheck.
- [Phase 02]: Public execution rejects non-baseline policies and unbounded profiling plans before sampling; full manifest, artifact, sample, and shot identity bind replay.
- [Phase 02]: Public verification reconstructs deterministic terminal, budget, work, candidate, lineage, and outcome claims; transient numerical errors retain explicit nonreproduction status.
- [Phase 02]: Public low-overhead profile evidence has producer-backed metric and unavailable-RSS grammars; nondeterministic measurements are same-ledger observations, not replay-equality facts.
- [Phase 04]: Phase 04: V4 manifests alone persist contiguous ordered affine-prior bindings, preserving V2/V3 semantics.
- [Phase 04]: Phase 04: Relay legs transfer only a finite digest-bound posterior LLR and reset all leg-local execution state.
- [Phase 04]: Phase 04: PDBP field mixing and PD-prime delta mixing remain separate source-linked state machines.
- [Phase 04]: Phase 04: Uniform EWAInit and Relay affine memory share one primitive under gamma = 1 - alpha.
- [Phase 04]: Memory bindings persist contiguous explicit order with disjoint history ownership.
- [Phase 04]: Memory refreshes use decoder-local replay identities and one-owner commits.
- [Phase 04]: CanonicalExperimentV4 extends the full V3 public evidence contract with ordered memory bindings while preserving historical V2/V3 meanings.
- [Phase 04]: Public V4 preflight rejects incompatible memory operands before artifact loading and records resolved binding order and compatibility evidence.
- [Phase 04]: Phase 04: Relay source and canonical presets are immutable named CSS adaptations; modified controls receive a controlled-adaptation identity.
- [Phase 04]: Phase 04: Relay candidate selection uses decoder-visible syndrome/prior weights and stable earlier-leg ties.
- [Phase 04]: Use only trmue/relay tag v0.2.2 at immutable commit 14cb31a18f9b9d7d099791b793e35b8a2951f8f3 as the original Relay reference.
- [Phase 04]: Keep the PyPI relay-bp package and editable mg551-duke/relay fork outside the approved original-reference identity.
- [Phase 04]: Phase 04 Plan 06: V4 Relay evidence reconstructs only from unique typed leaves and preserves V2/V3 semantics.
- [Phase 04]: Phase 04 Plan 08: exact Relay v0.2.2 adapter uses only decoder-visible inputs and never imports the installed fork.
- [Phase 04]: Phase 04 Plan 08: comment-only Relay observer preserves a behavior-neutral boundary; gamma, edge work, and resource facts remain unavailable.
- [Phase 04]: Phase 04 Plan 09: B1 resolves to the frozen v3 artifact; only the inventory semantic digest was stale.
- [Phase 04]: Phase 04 Plan 09: Phase 4 B1 manifests bind v3 and preserve all Phase 3 B1 evidence byte-for-byte.
- [Phase 04]: Phase 04 Plan 15: freeze focused factorial arms, three-region noise grids, and matched sample namespaces before sampling.
- [Phase 04]: Phase 04 Plan 15: bind B1 to the Plan 04-09 resolution digest and keep generated HGP explicitly non-paper-exact.
- [Phase 04]: Phase 04 Plan 10: exact-author native Relay runs only from a stage-local verified v0.2.2 checkout; canonical and native arms share public observations but retain separate identities.
- [Phase 04]: Phase 4 caps use one worker and rate-specific representative Relay evidence; B1 p=.07 is bounded to a measured three-leg-equivalent work vector.
- [Phase 04]: Phase 04 Plan 12: terminal Relay-ledger verification releases BB-144/HGP selections while B1 remains inconclusive under the frozen cap.
- [Phase 04]: Phase 04 Plan 12: async calibration manifest reconciled from terminal evidence without campaign relaunch or result rewrites.
- [Phase 6]: Phase 06: executable policy identity excludes source prose while immutable request receipts retain provenance and raw TOML identity.
- [Phase 6]: The three-paper B1 gate verified the common policy-file command and portable cache for one Yao, Bhatnagar, and Rabeti adaptation; two p=0.000001 shots per policy are not a performance or source-curve assessment.
- [Phase 6]: Coordinate-majority voting is an importable, independently checked kernel primitive; CAN-02 public TOML execution and replay are assigned to Phase 9.
- [Phase 6]: Phase 5 human visual review remains open while Phase 7 planning proceeds, as directed by the user. Continue CSS paper intake and bounded pilots alongside Phase 7; Phase 8 owns campaign statistics and throughput profiling.
- [Phase 10]: Phase 10 Plan 01: Persist Pauli values as I=0, X=1, Y=2, Z=3 and sample each qubit from one categorical joint channel.
- [Phase 10]: Phase 10 Plan 01: Separate decoder smoothing from physical channel probabilities and expose unavailable logical action without a declared non-CSS basis.
- [Phase 10]: Phase 10: Persisted Pauli labels use I=0, X=1, Y=2, Z=3 with fixed symplectic pairs and owned read-only arrays.
- [Phase 10]: Phase 10: CSS compilation persists X rows then Z rows, giving [s_X,s_Z]=[H_x z,H_z x], with roles, row indices, logical availability, and source identity in semantic bytes.
- [Phase 10]: Phase 10: Derived quaternary working graphs require explicit transform and lift witnesses; identity edges cannot change graph or syndrome.
- [Phase 10]: Native aSCED source is fixed to kit-cel/quantum_asced commit 816772071486615dfc7d71d1e15df597edc58a26; the exact digest was approved, and the bounded isolated build and native run succeeded.
- [Phase 10]: Phase 10 Plan 03: evaluator-local symplectic and GF(2) routines are the authority for four-outcome Pauli classification.
- [Phase 10]: Phase 10 Plan 03: logical residual actions use immutable (x, z) coordinates, while absent bases yield explicit unavailable reasons.
- [Phase 10]: Phase 10 Plan 04: physical I/X/Y/Z rows remain unchanged after strict validation, while decoder smoothing is separately identified.
- [Phase 10]: Phase 10 Plan 04: inverse-CDF ties use decimal persisted-value thresholds with stable I<X<Y<Z ownership.
- [Phase 10]: Phase 10: quaternary-bp4-f64-v1 freezes float64 identity-referenced LLRs with symmetric +/-25 saturation and requires vector/exact oracle qualification before public evidence.
- [Phase 10]: Phase 10: canonical scalar BP4 retains I/X/Y/Z node beliefs and uses scalar commutation messages only on edges.
- [Phase 10]: Phase 10 Plan 06: Flooding retains a whole old V2C snapshot while serial makes each declared variable update visible to later variables.
- [Phase 10]: Phase 10 Plan 06: Normalization and offset are closed finite-positive transforms applied only to scalar C2V messages.
- [Phase 10]: Phase 10 Plan 07: component source fidelity is persisted separately from run fidelity; continued-message Q-BPGD runs are canonical adaptations.
- [Phase 10]: Phase 10 Plan 07: quaternary_experiment_v2 is additive; V1 tracer parsing and replay semantics remain stable.
- [Phase 10]: Q-BPGD records source-backed setup components separately from the D-14 continued-message canonical-adaptation run.
- [Phase 10]: Q-BPGD preserves raw literal fixation weights and records common-sum normalized decoder priors for replay.
- [Phase 10]: Phase 10 Plan 09: fixed-alpha MBP4 scales only posterior anticommuting sums; destination-edge inhibition remains unscaled.
- [Phase 10]: Phase 10 Plan 09: non-source-defined MBP4 transform combinations remain canonical_adaptation despite source-backed components.
- [Phase 10]: GB46 H is a pinned source input; deterministic T and H_ext are project-generated canonical_adaptation evidence.
- [Phase 10]: The extended aSCED factor graph retains immutable-original transform/lift lineage without claiming its noncommuting splitter rows are a stabilizer code.
- [Phase 10]: Phase 10 Plan 11: canonical GB46 M retains identity rows and appends deterministic X/Z pair images under a 1000-pair cap.
- [Phase 10]: Phase 10 Plan 11: typed [s_X,g_X,s_Z,g_Z] assembly and comparison-only source maps prevent block or source-map substitution.
- [Phase 10]: Phase 10 Plan 11: canonical overcomplete construction accepts only a reverified QualifiedAscedBatch, closing standalone receipt spoofing.
- [Phase 10]: aSCED executes every declared CSS virtual path in LSB order and selects only original-syndrome-valid minimum-weight candidates with stable batch/path ties.
- [Phase 10]: Canonical aSCED runs bind verified constructed splitter and overcomplete receipts and remain canonical_adaptation even when paper components are source-backed.
- [Phase 10]: Phase 10 Plan 15: isolated native aSCED aggregate evidence remains distinct from canonical execution and retains unavailable native instrumentation.
- [Phase 10]: Retained the 256-shot GB46 p=0.05 seed-10 all-path ledger as canonical_adaptation mechanism evidence; native 160/10 remains aggregate-only with unavailable matched-shot identity.
- [Phase 10]: Full 256-shot decoder replay exited 0 and byte-matched all retained events; the bounded mechanism evidence remains `not_assessed` for curve reproduction or ranking.
- [Phase 11]: Figure 2 GB46 aSCED targets remain blocked_metadata until reviewed digitization and native execution evidence exist.
- [Phase 11]: Ordinary and overcomplete aSCED source members remain separately receipted; canonical adaptation fidelity is not promoted by target agreement.
- [Phase 11]: D-05 binary callbacks receive only component priors, syndromes, and arm-neutral identities.
- [Phase 11]: D-08 maps retained separate-arm nonconvergence to all-shot failure without dropping paired evidence.
- [Phase 11]: A5 reconstructs from the published l=90 polynomial pair while its distance interval remains source reported.
- [Phase 11]: Figure 7 source settings remain frozen; the one-sweep canonical-adaptation probe cannot assess the Figure 7 curve.
- [Phase 11]: A5 reconstructs from the published l=90 polynomial pair while its distance interval remains source reported.
- [Phase 11]: Figure 7 source settings remain frozen; the one-sweep canonical-adaptation probe cannot assess the Figure 7 curve.
- [Phase 11]: Phase 11: pinned native aSCED aggregate evidence is not matched-shot evidence; a proposed injected-input derivative stays unapplied until rights and semantic review approve a separate identity.
- [Phase 11]: D-12 reports D_y first across three fixed-marginal channel rows with simultaneous six-arm exact bounds.
- [Phase 11]: Phase 11 paired precision is frozen from a pilot identity, two-contrast alpha family, fixed stopping rule, and 5,000-pair cap.
- [Phase 11]: Phase 11 Plan 03: Treat the MBP4 Figures 8-9 five-qubit alpha contrast as finite deterministic mechanism evidence; Figure 6 remains blocked without statistical metadata.
- [Phase 11]: Pinned the GB46 source check bytes and kept all controlled calibration receipts in the canonical-adaptation lane with publication authorization deny.
- [Phase 11]: Used one sealed Pauli sample for the scalar four-state joint arm and canonical binary SPA marginal arms, with independent evaluation after both arms finish.
- [Phase 11]: BB72 calibration retains source-reported distance 6 and project-derived logical qualifications; neither becomes a platform verification claim.
- [Phase 11]: Joint BP4 and separate binary arms report native named work beside callback-wall runtime without cross-unit conversion.
- [Phase 11]: The Phase 11 package is immutable deny-only: missing site capacity, accounting, quota/cost, source eligibility, or persisted profiles prevents a dispatch token.
- [Phase 11]: User selected preserve_unavailable for the verified Phase 11 aSCED derivative patch dd8a31965372ba8aa736134d71c66183c1d044b5ae6910dee48068e04cec2229; native matched-input evidence remains unavailable and canonical work continues.
- [Phase 11]: Preserved deny for all four Phase 11 publication campaigns after verified missing site ceilings, account/partition, quota/cost, persisted runtime profiles, and source-route eligibility.
- [Phase 11]: Sealed the human-reviewed denial against package semantic SHA-256 4f53f8ce6af2961831830105dde34b4050632751960c9e8c475e9cc7ac16334a with no dispatch token.
- [Phase 11]: Plan 11-05 preserve_unavailable now has a digest-bound declined_unavailable terminal with no derivative source operation, build, run, matched row, or source-fidelity claim.
- [Phase 11]: Phase 11 Plan 13: D-13 policy comparisons change only the qualified MBP4 recurrence and retain shared sample identity.
- [Phase 11]: Phase 11 Plan 13: D-13 policy comparisons change only the qualified MBP4 recurrence and retain shared sample identity.
- [Phase 11]: Phase 11 Plan 13: Canonical aSCED eligibility remains separate from unavailable matched-native aSCED evidence.
- [Phase 11]: Phase 11 Plan 13: Canonical aSCED eligibility remains separate from unavailable matched-native aSCED evidence.
- [Phase 11]: aSCED canonical-adaptation and unavailable matched-native states remain separately assessed for each Figure 2 member.
- [Phase 11]: Phase 11 source lanes retain sealed deny-only zero-dispatch terminals; MBP4 five-qubit evidence remains mechanism-only.
- [Phase 11]: Phase 11 Plan 15: sealed preserve-deny authority yields independent GB46 and BB72 zero-dispatch receipts; calibration remains forecast provenance only.
- [Phase 11]: Phase 11 Plan 15: Plan 11-14 may assess only receipt-declared complete pairs; both controlled closures currently expose zero.
- [Phase 11]: Phase 11 final assessment retains GB46 and BB72 as zero-pair inconclusive receipt closures with no controlled effect claim.
- [Phase 11]: Source, primary controlled, and policy evidence remain separate digest-bound lanes in the Phase 11 public index.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- F01/F02 are closed and qualified; no open correction from audit 050–053 blocks HTML integration over the documented supported subset. See spikes/CANONICAL-KERNEL-SHARED-POLICY-FIXES.md. Existing scientific/publication gates remain separate.

- Prior circuit/CUDA audit findings E03/E01/E02 remain closed with 257 regression passes and 12/12 audit groups. Shared-policy F01/F02 are now closed as well. Scientific publication gates below remain separate; see spikes/CANONICAL-KERNEL-CIRCUIT-CUDA-FIXES.md and CANONICAL-KERNEL-SHARED-POLICY-FIXES.md.

- [Phase 11] Eight gap plans remain open: 11-18 aSCED Figure 2 review and user-deferred 11-19 Q-BPGD Figure 7 review gate 11-17 policy replay and 11-21 resource qualification; 11-22 authorization, 11-23/24 campaigns, and 11-25 final verification depend on those outcomes. Completed 11-20 retains the MBP4 Figure 6 mechanism-only, zero-shot target. The current preserve-deny decision remains in force; no controlled effect or source-curve reproduction is established.
- [Phase 09] Exact author experiment artifacts, source settings, and executable native assessments are still unverified; EVAL-01/02 remain pending. The Yao B1 adaptation is cap censored. Site resource ceilings and scheduler accounting remain unavailable, so publication dispatch is denied.

- Current: Phase 4 passed goal verification (4/4 revised criteria; 6/6 requirements), validation and ASVS L1 security. The user stopped the oversized comprehensive experiment; its terminal manifest disables resume. B1 selection remains inconclusive, and the 159 completed plus one interrupted B1 records are receipts without a qualified performance denominator. Fresh evaluation, native-pair and factorial results remain absent. Phase 5 has 14 implemented and technically verified plans; human notebook/HTML review remains open. See the [cancellation record](phases/04-memory-policies-and-relay-bp/04-13-CANCELLATION-20260930.md) and `04-VERIFICATION.md`. Entries below are historical checkpoints, not live progress.

- New-chat progress audit: calibration running with 3,716/5,824 retained attempts (63.8%) at 2026-09-27T17:20:42.542Z. See `.planning/HANDOFF.json` for the measured snapshot and async resume context. Phase 1/2 verification reports are now flagged stale by GSD and need refreshing; Phase 3 remains passed. No completed plans were rerun or removed.
- Phase 4 calibration remains `running` (PID 2702938); Plans 04-12/13/14 remain incomplete. Independent local PD-prime/momentum/affine execution, semantic failure-prefix traces, exact-byte terminal readers, immutable shot contexts and notebook views are verified in isolated source `62fe977`: 532 tests passed, one existing skip. Both notebooks execute all 14 cells without errors. The completed benchmark summary retains a real incomplete B1 p=.07 arm, so its rows remain explicitly unqualified. Fresh production evidence, retained histories/additional lifetimes, other local schedules, disordered local affine and Relay traces remain. Keep source changes separate from the live campaign. See [implementation continuation](phases/04-memory-policies-and-relay-bp/04-IMPLEMENTATION-CONTINUATION-20260927.md) and [coding handoff](phases/04-memory-policies-and-relay-bp/04-CODING-RESUME-HANDOFF.md).
- Phase 3 passed goal verification with 17/17 plans and all eight requirements complete. The Hsu source-defined group schedule has a retained, independently verified two-shot CSS pilot. The Moradi artifact remains unavailable and is not conflated with the Hsu policy.

Phase 2 is complete (16/16 plans; 5/5 goal criteria; clean review; 46/46 security threats closed). Remaining research concerns for later phases:

- Original BPGD/impulse code identities remain unverified; exact SI/OTF variants and generic mixing/memory/voting definitions need source specifications.
- Statistical targets and compute budgets for publication campaigns remain to be prespecified.
- Phase 11's prespecified comparisons still require eligible reviewed targets, measured site resources, authorized complete-pair campaigns, and deep policy replay. Phase 10 mechanism evidence and the native aggregate do not establish source-curve agreement or matched-shot performance.
- The observed development environment is node-specific; recheck package and backend identity before interpreting runs elsewhere.
- Circuit fault correlations and observable semantics require dedicated qualification; a CSS adaptation does not reproduce a circuit paper.
- Phase 07 POST-01 / Plan 07-03: approved standalone OSD commit builds in isolation but does not expose complete higher-order candidate solutions and scores; qualification receipt is failed/non-runnable. The user paused postprocessing, so no OSD source patch or reduced evidence contract is being pursued now.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 261117-htb | Compare PriorTilt and Relay Rust provenance | 2026-11-17 | fdc677b3 | Verified no direct Relay dependency; historical derivation remains unproven | [261117-htb](./quick/261117-htb-compare-priortilt-and-relaybp-rust-imple/) |
| 261117-h97 | Audit PriorTilt syndrome and observable scoring | 2026-11-17 | b5012500 | Verified public source and native/Sinter counterexample; campaign unchanged | [261117-h97](./quick/261117-h97-audit-priortilt-source-syndrome-consiste/) |
| 261117-guy | Check ten-CPU progress and first parallel result | 2026-11-17 | 967f3b99 | Verified24/39; PriorTilt7/13;15 ten-CPU jobs continue | [261117-guy](./quick/261117-guy-check-priortilt-ten-cpu-progress-and-new/) |
| 261117-fdl | Resume remaining Fig1 points on ten CPUs each | 2026-11-17 | c653c495 | Qualified;16 running ten-CPU continuations;23 completed points preserved | [261117-fdl](./quick/261117-fdl-resume-remaining-priortilt-fig1-points-w/) |
| 261117-exr | Check new PriorTilt results and paper agreement | 2026-11-17 | 70d91402 | Verified23/39; PriorTilt7/13;16 one-CPU workers continue | [261117-exr](./quick/261117-exr-check-new-priortilt-fig1-results-and-sou/) |
| 261117-077 | Check PriorTilt progress and newly completed comparison points | 2026-11-17 | be547ae3 | Verified19/39; PriorTilt5/13;20 one-CPU workers continue | [261117-077](./quick/261117-077-check-priortilt-fig1-progress-and-newly-/) |
| 261116-ta4 | Check PriorTilt Fig1 completed points and paper agreement | 2026-11-16 | 97d6423d | Verified 15/39 audited pairs; 24 one-CPU workers continue | [261116-ta4](./quick/261116-ta4-check-priortilt-completed-fig1-points-an/) |
| 261116-rf9 | Check PriorTilt Fig1 and explain matched OSD-CS speedup | 2026-11-16 | 0e8ec024 | Verified7/39 audited pairs;32 one-CPU workers continue | [261116-rf9](./quick/261116-rf9-check-priortilt-fig1-results-and-explain/) |
| 261116-ote | Check LP results and add paper figure views with grouped curve controls | 2026-11-16 | 781055fb | Verified; gamma 6/12 and original LP 70/72 audited, campaigns running | [261116-ote](./quick/261116-ote-check-lp1054-results-and-add-paper-figur/) |
| 261116-nf0 | Tune RelayBP uniform80/disordered60 gamma with matched controls | 2026-11-16 | 177417b7 | 12 single-CPU workers tuning; fresh results pending | [261116-nf0](./quick/261116-nf0-tune-relaybp-uniform-gamma80-and-disorde/) |
| 261116-mkh | Check original lifted-product results and decoder comparisons | 2026-11-16 | a75222da |68 audited points published; four rare simulations continue | [261116-mkh](./quick/261116-mkh-check-original-lifted-product-campaign-r/) |
| 261116-jzy | Launch original lifted-product full decoder stack | 2026-11-16 | 53fabae |72 single-CPU workers;50 audited points published; campaign running | [261116-jzy](./quick/261116-jzy-reproduce-lifted-product-paper-codes-wit/) |
| 261116-0k6 | Check broader beam/RelayBP results and latency tradeoffs | 2026-11-16 | 77aba5a | Verified215/218 workers;639 fresh settings published | [261116-0k6](./quick/261116-0k6-check-tuned-beam-and-relaybp-frontier-re/) |
| 261115-sxj | Tune beam search and RelayBP for LER versus OSD0 latency | 2026-11-15 | 1154bbf | Qualified;114-worker snapshot published; broader frontier running | [261115-sxj](./quick/261115-sxj-tune-canonical-beam-search-and-relaybp-a/) |
| 261114-pna | Check completed runtime-budget results and archive full evidence | 2026-11-14 | 7fcae85 | Complete;1464 rows/218 workers, timing caveats explicit | [261114-pna](./quick/261114-pna-audit-completed-runtime-budget-joint-con/) |
| 261114-lhw | Joint damping/scaling/offset and runtime-matched iteration histories | 2026-11-14 | 8e903bc | Implementation/launch complete;218-worker array61824235 running | [261114-lhw](./quick/261114-lhw-run-runtime-matched-iteration-sweeps-wit/) |
| 261114-i9b | Explain optimized OSD search and check212 terminal points/424 endpoints | 2026-11-14 | 2c8b6fe | Check complete; full interior audit61820674 continues | [261114-i9b](./quick/261114-i9b-audit-current-osd0-cs10-results-and-expl/) |
| 261113-vj0 | Tabulate all current Roffe BP-OSD source points beside confirmed BP/Q-BP | 2026-11-13 | 04002e0 | Complete;108 paper points/109 grid rows, no new simulations | [261113-vj0](./quick/261113-vj0-extract-all-roffe-figure3-bp-osd-points-/) |
| 261113-v31 | Audit and publish completed Roffe damping comparison; fix shared paper registration | 2026-11-13 | c595969 | Complete;436 confirmation points audited/published | [261113-v31](./quick/261113-v31-audit-completed-roffe-damping-results-re/) |
| 261113-q96 | Launch paper-budget Roffe damped BP/Q-BP tuning and fresh confirmation | 2026-11-13 | 4c8471f | Complete;1526 tuning/436 confirmation points, follow-up v31 | [261113-q96](./quick/261113-q96-tune-and-independently-confirm-damped-ro/) |
| 261113-p1r | Assess completed Roffe curves and verify publication | 2026-11-13 | efc3e6a | Complete;109/109 source points consistent pointwise | [261113-p1r](./quick/261113-p1r-assess-completed-roffe-figure-3-results-/) |
| 261113-oan | Launch Roffe with one CPU for each of218 points | 2026-11-13 | b121812 | Complete218-point audit/publication; see p1r assessment | [261113-oan](./quick/261113-oan-launch-all-218-roffe-points-concurrently/) |
| 261113-mmo | Isolate undamped Q-BP under matched noise; verify length74 source ordinates | 2026-11-13 | bd08a80 | Complete controls; five paper ordinates unavailable, summary extracted | [261113-mmo](./quick/261113-mmo-add-independent-undamped-q-bp-and-matche/) |
| 261113-hk2 | Infer short MacKay cap, retain long curves, replace oversized damping | 2026-11-13 | 1b040da | T100 baseline published; confirmation 39/40, continuation via mmo controls | [261113-hk2-replace-oversized-mackay-damping-ceiling](./quick/261113-hk2-replace-oversized-mackay-damping-ceiling/) |
| 261113-ggu | Tune MacKay BP/Q-BP damping; then reproduce early BP-OSD paper regular BP | 2026-11-13 | ad689b0 | Setup verified; Superseded: oversized damping canceled; continuation moved to hk2 | [261113-ggu-tune-mackay-bp-and-q-bp-damping-and-repr](./quick/261113-ggu-tune-mackay-bp-and-q-bp-damping-and-repr/) |
| 261112-k9m | Run MacKay at the five published error rates | 2026-11-12 | fdbb98b | Complete; 30/30 audited points; lower-rate source discrepancy retained | [261112-k9m-run-mackay-bp-campaign-at-the-five-publi](./quick/261112-k9m-run-mackay-bp-campaign-at-the-five-publi/) |
| 261112-i4d | Construct and run foundational MacKay unicycle BP campaign | 2026-11-12 | 8e234a4, fdbb98b | Complete: 42/42 audited points; old grid preserved as historical evidence | [261112-i4d-construct-mackay-2004-unicycle-codes-and](./quick/261112-i4d-construct-mackay-2004-unicycle-codes-and/) |
| 261110-sic | Complete B1/C2 BPGD and matched-marginal Q-BP sweeps | 2026-11-11 | 25c6c1f, a84413f | Verified 77/77 points and 40,459,752 shots, with 40 final tests and 18 browser checks | [261110-sic-complete-b1-and-c2-bpgd-and-matched-q-bp](./quick/261110-sic-complete-b1-and-c2-bpgd-and-matched-q-bp/) |
| 261111-f0q | Display mean iterations and directed edge updates together | 2026-11-11 | 324b53a | Verified with 124 research tests and 18 browser workflow checks | [261111-f0q-display-mean-iterations-and-directed-edg](./quick/261111-f0q-display-mean-iterations-and-directed-edg/) |
| 261110-oou | Format log axis powers and rescale plots to visible curves | 2026-11-10 | 8d35f04 | Verified with 17 browser workflow checks and five plot-coordinate tests | [261110-oou-format-log-axis-powers-and-rescale-plots](./quick/261110-oou-format-log-axis-powers-and-rescale-plots/) |
| 261110-lsd | Add validated Request experiment results action and GitHub request draft | 2026-11-10 | 7b8e702 | Verified: 12 browser groups; exact specs/hash, invalidation, long inputs, mobile | [261110-lsd-add-a-validated-request-experiment-resul](./quick/261110-lsd-add-a-validated-request-experiment-resul/) |
| 261109-mzx | Exclude already displayed curves from each plot add picker | 2026-11-09 | 1e6b825 | Verified: 16 browser groups; keyboard/mouse restoration, empty and independent plot states | [261109-mzx-exclude-already-displayed-curves-from-ea](./quick/261109-mzx-exclude-already-displayed-curves-from-ea/) |
| 261109-mcf | Filter active research curves to multiple measured rates and hide inputs without results | 2026-11-09 | 7eeddf7 | Verified: 118 tests; 14 browser groups; retained imports; 105→63 curves, 361→319 points | [261109-mcf-filter-active-research-curves-to-multipl](./quick/261109-mcf-filter-active-research-curves-to-multipl/) |
| 261109-hhq | Fix shared-policy findings F01 → F02 and qualify result preservation | 2026-11-09 | fd5c3d0, 78f1c1c | Verified: 1712 kernel / 161 final shared passes; 24 Sinter v2 shots; 82 identical legacy receipts; 58 shared-v1 shots replayed | [261109-hhq-fix-f01-memory-admission-then-f02-sinter](./quick/261109-hhq-fix-f01-memory-admission-then-f02-sinter/) |
| 261108-qcu | Expand compatible policies across CPU and Stim/Sinter kernels | 2026-11-08 | 7f888a1, c512723 | Verified: 2462 broad / 387 affected passes; 24 Sinter shots; 82 identical legacy receipts | [261108-qcu-expand-existing-compatible-policies-acro](./quick/261108-qcu-expand-existing-compatible-policies-acro/) |
| 261108-oq5 | Fix circuit findings E03 → E01 → E02 in order | 2026-11-08 | d6e8756, 02d890a, 5855049 | Verified: 257 tests; 12/12 audit groups; unchanged ordinary ledgers | [261108-oq5-fix-circuit-contract-findings-e03-e01-e0](./quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/) |
| 261108-meg | Implement compatible circuit policies and binary/Pauli CUDA execution | 2026-11-08 | 90ecfbc, dc43249 | Verified: 2285 regression passes; 34 circuit and 20 H200 checks; 4096 exact GPU/CPU shots | [261108-meg-implement-compatible-circuit-policies-an](./quick/261108-meg-implement-compatible-circuit-policies-an/) |
| 261102-okz | Consolidate research branches onto main and preserve recovery/evidence | 2026-11-02 | 22f881f | 1,514 passed, 1 skipped; main only; archived 28 original refs and retained three evidence worktrees | [261102-okz-consolidate-research-branches-into-main-](./quick/261102-okz-consolidate-research-branches-into-main-/) |
| 261102-jnd | Add B1/C2 depolarizing plain BP/QBP and four-code comparison at T=100 | 2026-11-02 | b204164 | Verified 381,309 fresh paired samples; all 14 points and 28 arm estimates ≥100 failures | [261102-jnd-extend-plain-binary-bp-and-qbp-compariso](./quick/261102-jnd-extend-plain-binary-bp-and-qbp-compariso/) |
| 261102-i0p | Add plain BP A5/B2 and plain QBP B1/C2 at T=100 | 2026-11-02 | a95a898 | Verified all 28 code/rate cells; 1,583,664 paired samples, all main arms ≥100 failures | [261102-i0p-add-missing-plain-bp-a5-b2-and-plain-qbp](./quick/261102-i0p-add-missing-plain-bp-a5-b2-and-plain-qbp/) |
| 261029-vdb | Reproduce Yao non-OSD figures and tables with bounded source-linked runs | 2026-10-30 | 50d6371, 7eef1c5 | Verified development evidence; rare-event and imported BP-SI points remain unresolved | [261029-vdb-reproduce-remaining-non-bp-osd-yao-2312-](./quick/261029-vdb-reproduce-remaining-non-bp-osd-yao-2312-/) |
| 261029-j3n | Apply tuned BP4 profiles inside A5/B2 Q-BPGD on paired errors | 2026-10-29 | — | Verified 20,000-shot main comparison; lower mean work, accuracy unresolved | [261029-j3n-apply-tuned-bp4-profiles-to-a5-and-b2-q-](./quick/261029-j3n-apply-tuned-bp4-profiles-to-a5-and-b2-q-/) |
| 261029-i1m | Compare tuned and untuned BP4 at equal T=100 and matched mean work on A5/B2 | 2026-10-29 | — | Verified 1,160,000-shot paired controls; B2 equal-work difference unresolved | [261029-i1m-run-paired-equal-cap-t100-bp4-baseline-v](./quick/261029-i1m-run-paired-equal-cap-t100-bp4-baseline-v/) |
| 261028-kvb | Tune canonical BP4 on Yao A5/B2 at physical p=0.06 | 2026-10-28 | — | Verified 257-task paired search; selected finite-neighborhood policies | [261028-kvb-tune-vanilla-bp4-at-p-0-06-on-yao-a5-and](./quick/261028-kvb-tune-vanilla-bp4-at-p-0-06-on-yao-a5-and/) |
| 261027-qsa | Reproduce Yao et al. vanilla Q-BP on A5/B2 with paired binary/BP4 v1/v2 | 2026-10-27 | — | Verified 1,216,144-shot campaign; A5 v2 near source, B2 v2 modestly lower | [261027-qsa-yao-vanilla-bp-reproduction](./quick/261027-qsa-yao-vanilla-bp-reproduction/) |
| 261027-q9k | Promote corrected BP4 min-sum and add shared resolution policies | 2026-10-27 | — | Verified compiled development policy; historical manifests unchanged | [261027-q9k-ms-resolution-policy](./quick/261027-q9k-ms-resolution-policy/) |
| 261027-p6o | Recheck nine vanilla BP4 MS curve points with jointly corrected diagnostic numerics | 2026-10-27 | — | Verified exploratory match; double-Gross p=.06 holdout differs from source point | [261027-p6o-ms-both-changes-curve](./quick/261027-p6o-ms-both-changes-curve/) |
| 261027-mnotation | Replace v1/v2 comparison with BP message notation | 2026-10-27 | — | Verified | [261027-mnotation-v1-v2](./quick/261027-mnotation-v1-v2/) |
| 261027-math | Replace v1/v2 comparison with typeset vector equations | 2026-10-27 | — | Superseded by 261027-mnotation | [261027-math-v1-v2-comparison](./quick/261027-math-v1-v2-comparison/) |
| 261027-l1l | Promote plain SPA/BP4 float64 v2 defaults and publish version comparison | 2026-10-27 | — | Verified | [261027-l1l-v2-default-canonical](./quick/261027-l1l-v2-default-canonical/) |
| 261026-ns3 | Run BP4 min-sum at presentation vanilla and tuned knobs on matched B1 and double-Gross errors | 2026-10-26 | c6c50cf | Verified exploratory adaptation | [261026-ns3-run-presentation-vanilla-and-tuned-setti](./quick/261026-ns3-run-presentation-vanilla-and-tuned-setti/) |
| 261025-s21 | Test two-thirds shift of presentation depolarizing p against paired BP4 and binary pilots | 2026-10-25 | 89d5984 | Verified diagnostic; shift does not reconcile pilots | [261025-s21-test-two-thirds-presentation-p-axis-hypo](./quick/261025-s21-test-two-thirds-presentation-p-axis-hypo/) |
| 261024-pyb | Reconcile Phase 11 plan completion and planning state | 2026-10-24 | 3868253 | Verified bookkeeping; scientific gaps open | [261024-pyb-reconcile-phase-11-plan-completion-and-p](./quick/261024-pyb-reconcile-phase-11-plan-completion-and-p/) |
| 261021-pgm | Pin Relay and BeamSearch circuits, add Sinter CPU BP adapter and paper index | 2026-10-21 | 93757e2 | Verified development integration | [261021-pgm-pin-relay-paper-circuits-and-implement-v](./quick/261021-pgm-pin-relay-paper-circuits-and-implement-v/) |
| 261021-om6 | Optimize shared binary BP numerical and schedule path with exact policy traces | 2026-10-21 | f54ee9d | Verified development optimization | [261021-om6-optimize-shared-binary-bp-numerical-and-](./quick/261021-om6-optimize-shared-binary-bp-numerical-and-/) |
| 261021-njt | Optimize policy-composable quaternary BP4 flooding and MBP4 incidence | 2026-10-21 | bf6048a | Verified development optimization | [261021-njt-optimize-policy-composable-quaternary-bp](./quick/261021-njt-optimize-policy-composable-quaternary-bp/) |
| 261019-4l9 | Reuse compiled BP decode buffers and skip unused BP4 marginals | 2026-10-19 | 3c16239 | Verified development prototype | [261019-4l9-reuse-compiled-bp-decode-buffers-and-ski](./quick/261019-4l9-reuse-compiled-bp-decode-buffers-and-ski/) |
| 261019-18p | Profile and accelerate canonical binary and BP4 kernels | 2026-10-19 | d65e338 | Verified development prototype | [261019-18p-profile-canonical-binary-spa-and-quatern](./quick/261019-18p-profile-canonical-binary-spa-and-quatern/) |
| 261019-0po | Benchmark canonical BP kernels against Relay Rust, aSCED C++, and ldpc | 2026-10-19 | 91f0559 | Verified development benchmark | [261019-0po-benchmark-canonical-python-bp-kernels-ag](./quick/261019-0po-benchmark-canonical-python-bp-kernels-ag/) |
| 261012-kia | Defer Phase 5 human review and route to Phase 11 planning | 2026-10-12 | — | Verified | [261012-kia-defer-phase-5-human-review-and-route-to-](./quick/261012-kia-defer-phase-5-human-review-and-route-to-/) |
| 261005-le8 | Capture first three-paper CSS literature gate and source specs | 2026-10-05 | a6526e8 | Verified and published | [261005-le8-capture-three-paper-css-literature-gate-](./quick/261005-le8-capture-three-paper-css-literature-gate-/) |
| 261005-kkp | Place decoder TOML in paper folder and reproduction details below it | 2026-10-05 | 1ad21ba | Verified | [261005-kkp-place-decoder-toml-beside-paper-folder-a](./quick/261005-kkp-place-decoder-toml-beside-paper-folder-a/) |
| 261005-kcm | Scaffold literature policy registry and source status contract | 2026-10-05 | 660bdd8 | Verified | [261005-kcm-scaffold-literature-policy-registry-and-](./quick/261005-kcm-scaffold-literature-policy-registry-and-/) |
| 261005-jlz | Add importable policy-file study command with verified cache reuse | 2026-10-05 | 1f8b1c3 | Verified | [261005-jlz-add-importable-policy-file-study-command](./quick/261005-jlz-add-importable-policy-file-study-command/) |
| 261005-fze | Run matched BB72 BeamSearch/RelayBP parameter and evaluation campaign | 2026-10-05 | 3db441e | Verified and published | [261005-fze-run-matched-bb72-beamsearch-relaybp-para](./quick/261005-fze-run-matched-bb72-beamsearch-relaybp-para/) |
| 261005-2b9 | Merge fair damped BeamSearch/RelayBP after BB72 BP-SF v2 publication | 2026-10-05 | b84071e | Verified and published | [261005-2b9-merge-verified-fair-damped-beamsearch-re](./quick/261005-2b9-merge-verified-fair-damped-beamsearch-re/) |
| 261004-krc | Implement fair initial BP with damped BeamSearch branches and RelayBP memory legs | 2026-10-04 | 4955bff | Verified development implementation | [261004-krc-implement-fair-initial-bp-plus-damped-re](./quick/261004-krc-implement-fair-initial-bp-plus-damped-re/) |
| 261003-s2b | Prespecify, run, and publish the BB72 CSS BP comparison | 2026-10-04 | a23899c | Verified | [261003-s2b-prespecify-and-prepare-bb72-css-bp-decod](./quick/261003-s2b-prespecify-and-prepare-bb72-css-bp-decod/) |
| 261002-mjc | Parallelize Phase 5 v2 arm verification before publication | 2026-10-02 | b26d0c2 | Verified | [261002-mjc-parallelize-phase-5-v2-arm-verification-](./quick/261002-mjc-parallelize-phase-5-v2-arm-verification-/) |
| 261002-ldj | Pin and validate Bravyi BB72 CSS fixture | 2026-10-02 | 60679e4 | Verified | [261002-ldj-pin-and-validate-bravyi-bb72-css-fixture](./quick/261002-ldj-pin-and-validate-bravyi-bb72-css-fixture/) |
| 260922-21z | Document Phase 1 ldpc SDK coverage and unblock UAT | 2026-09-22 | 4581389 | — | [260922-21z-document-phase-1-ldpc-sdk-coverage-and-u](./quick/260922-21z-document-phase-1-ldpc-sdk-coverage-and-u/) |
| 260923-nbn | Repair Phase 2 GSD verification metadata | 2026-09-23 | 15a9e8a | — | [260923-nbn-repair-phase-2-gsd-verification-metadata](./quick/260923-nbn-repair-phase-2-gsd-verification-metadata/) |
| 260923-ui8 | Create a reproducible PDF documentation snapshot through completed Phase 2 from existing Markdown; preserve existing Markdown and do not advance Phase 3 | 2026-09-23 | 30df961 | — | [260923-ui8-create-a-reproducible-pdf-documentation-](./quick/260923-ui8-create-a-reproducible-pdf-documentation-/) |
| 260924-max | Record prospective quaternary memory-policy novelty in Markdown and reproducible PDF | 2026-09-24 | 2a83502 | — | [260924-max-record-prospective-quaternary-memory-pol](./quick/260924-max-record-prospective-quaternary-memory-pol/) |
| 260926-ps2 | Review Phase 4 gates, design Phase 5 interventions and document development since the last PDFs | 2026-09-26 | b684cab | Verified | [260926-ps2-review-pending-phase-4-gates-design-phas](./quick/260926-ps2-review-pending-phase-4-gates-design-phas/) |
| 260927-p0f | Add project README and push main plus isolated Phase 4 branch to GitHub | 2026-09-27 | 5a6377a | Verified | [260927-p0f-add-a-project-readme-and-push-to-git-git](./quick/260927-p0f-add-a-project-readme-and-push-to-git-git/) |
| 260929-qaa | Publish a verified 29 September development update in Markdown and PDF to GitHub | 2026-09-29 | 640b9c1 | Verified | [260929-qaa-publish-a-verified-29-september-developm](./quick/260929-qaa-publish-a-verified-29-september-developm/) |
| 260930-0vq | Stop Phase 4 comprehensive experiment and right-size plans | 2026-09-30 | db99a51 | Verified | [260930-0vq-stop-phase-4-comprehensive-experiment-an](./quick/260930-0vq-stop-phase-4-comprehensive-experiment-an/) |
| 260930-nuv | Create a source-backed study-design glossary in Markdown and color-coded PDF, then commit and push to GitHub | 2026-09-30 | 6ddf013 | Verified | [260930-nuv-create-a-source-backed-study-design-glos](./quick/260930-nuv-create-a-source-backed-study-design-glos/) |
| 261002-in6 | Add explicit Phase 6 candidate-list selection foundation | 2026-10-02 | 77bf533 | Verified | [261002-in6-implement-phase-6-candidate-list-selecti](./quick/261002-in6-implement-phase-6-candidate-list-selecti/) |

| 261103-lyt | Build research catalog, HTML workbench, and portable experiment packages | 2026-11-03 | See quick summary | Verified (83 checks + browser workflows) | [261103-lyt-build-reusable-research-catalog-html-int](./quick/261103-lyt-build-reusable-research-catalog-html-int/) |

| 261104-n37 | Archive research interface v1 and deliver focused v2 MVP | 2026-11-04 | See quick summary | Verified (106 tests + browser) | [261104-n37-retire-research-html-v1-and-build-simple](./quick/261104-n37-retire-research-html-v1-and-build-simple/) |

| 261105-q2s | Improve v2 parameter labels and interactive curve selection; hide retired clipping | 2026-11-05 | See quick summary | Verified (111 tests + browser) | [261105-q2s-improve-v2-decoder-labels-and-legends-se](./quick/261105-q2s-improve-v2-decoder-labels-and-legends-se/) |

| 261106-nd0 | Refine workbench curves, composable policies, circuit sweeps and per-point budgets | 2026-11-06 | dc39055 | Verified (144 tests + 22 browser checks) | [261106-nd0-refine-workbench-result-semantics-and-co](./quick/261106-nd0-refine-workbench-result-semantics-and-co/) |
| 261117-kva | Verify 28 PriorTilt Fig1 points and explain small-matrix OSD runtime regressions | 2026-11-17 | 355b9e97 | — | [261117-kva-check-current-priortilt-fig1-results-and](./quick/261117-kva-check-current-priortilt-fig1-results-and/) |
| 261118-ogi | Check 38 audited Fig1 results; all 13 PriorTilt points complete | 2026-11-18 | 30275791 | — | [261118-ogi-check-completed-priortilt-fig1-results-a](./quick/261118-ogi-check-completed-priortilt-fig1-results-a/) |
| 261118-p8c | Qualify and launch paper XYZ comparison with 50 CPUs per point | 2026-11-19 | 1d816528 | — | [261118-p8c-qualify-and-launch-paper-xyz-priortilt-a](./quick/261118-p8c-qualify-and-launch-paper-xyz-priortilt-a/) |
| 261118-s8d | Check XYZ progress and final 39-point XZ publication | 2026-11-19 | 9d141231 | — | [261118-s8d-check-live-xyz-priortilt-and-relaybp5-pr](./quick/261118-s8d-check-live-xyz-priortilt-and-relaybp5-pr/) |
| 261118-ui1 | Expand decoder policies and research workbench | 2026-11-19 | a297e53d | Verified workbench and portable routes covered here. aSCED and Unicycle use registered studies. | [261118-ui1](./quick/261118-ui1-update-canonical-policy-support-and-rese/) |
| 261119-1m4 | Run ordinary and tuned BP on the full PriorTilt circuit grid with 20 CPUs per point | 2026-11-19 | a6fc2cf4 | — | [261119-1m4-run-ordinary-and-tuned-min-sum-bp-on-pri](./quick/261119-1m4-run-ordinary-and-tuned-min-sum-bp-on-pri/) |
| 261119-h7b | Check 25 audited BP follow-up results and XYZ progress | 2026-11-19 | d73405dd | — | [261119-h7b-check-audited-priortilt-bp-follow-up-res](./quick/261119-h7b-check-audited-priortilt-bp-follow-up-res/) |
| 261119-i4j | Show source captions and compare papers | 2026-11-19 | 33d71574 | 38 tests and eight browser checks passed | [261119-i4j-use-source-captions-and-compare-paper-re](./quick/261119-i4j-use-source-captions-and-compare-paper-re/) |
| 261119-ibq | Launch damping-first advanced circuit BP tuning on 11 anchors | 2026-11-19 | 71eb5309 | — | [261119-ibq-tune-priortilt-relaybp-and-beamsearch-bp](./quick/261119-ibq-tune-priortilt-relaybp-and-beamsearch-bp/) |
| 261119-jgk | Constrain Construction U table cells and show full hover text | 2026-11-19 | 843cbf10 | Verified at desktop, comparison, and mobile widths | [261119-jgk-constrain-construction-u-table-cells-and](./quick/261119-jgk-constrain-construction-u-table-cells-and/) |
| 261119-ksp | Display recorded PriorTilt work and timing by memory basis | 2026-11-19 | 02dfe835 | Verified 39 rows, guest panels, and CSV export | [261119-ksp-display-recorded-priortilt-work-and-timi](./quick/261119-ksp-display-recorded-priortilt-work-and-timi/) |
| 261119-kxq | Plot 307 paper-reported points as matching stars on reproduced figures | 2026-11-19 | d105c23f | — | [261119-kxq-plot-paper-reported-points-as-matching-s](./quick/261119-kxq-plot-paper-reported-points-as-matching-s/) |

### Roadmap Evolution

- Phase 10 reordered: User selected quaternary BP next: Phase 10 now depends on verified Phase 6 CSS foundation; Phase 8 can proceed independently of paused Phase 7, Phase 11 requires both Phase 8 statistical controls and Phase 10 engine, and optional fallback comparisons remain conditional on qualification.
- Phase 11.1 inserted after Phase 11: User-scoped autonomous weighted streaming OSD qualification; unrelated phase gates preserved (URGENT)

## Deferred Items

No requested decoding regime or named policy family is deferred beyond the first journal milestone. The user deferred Phase 5's pending human notebook/HTML review while moving to Phase 11; Phase 5 is not marked complete. Phase 7 remains paused. The cancelled comprehensive Phase 4 CSS evaluation/factorial is deferred from Phase 4; Phase 8 supplied bounded campaign infrastructure and Phase 9 completed exploratory CSS controls. Source-faithful CSS publication assessments remain pending exact author evidence. Relay circuit-curve assessment remains in Phase 13.

## Session Continuity

Latest check: quick261116-0k6. Original search fully audited218/218. Broader search215/218 deeply audited;639 fresh configurations/27.24M shots published, with independent arithmetic/selection checks. Three beam points remain running and collector61870315 waits for them. See FINDINGS.md, comparisons.csv and scientific figure. Strict comparisons use actual mean-time eligibility; no equivalence/threshold claim follows from20-failure precision. Public427 curves/3132 points/12 codes/0 circuits; historical subsets and singleton eligibility preserved. Do not change frozen plans or resubmit simulations. Phase gates/counters unchanged.

Prior comparison: quick 261114-pna, evidence `7fcae85`. Runtime-budget tuning is complete: 218/218 workers and collector 61824236 completed; all 1,464 fresh confirmation rows are independently reconciled. Extra iterations improve observed binary BP LER in only 1/107 extended-cap strata. Joint-control median LER and mean-iteration ratios remain 1.00; pointwise gains and uncertainty remain in the report. Actual selected timing is within 10% at 145/218 points; 36 over-budget points are flagged. See the quick task FINDINGS.md, per-cap figure, selected-point CSV and full study RESULTS.md. Public workbench now has 308 curves/2,627 points/12 codes/0 circuits. Full evidence and training CSV are losslessly archived with raw-byte hashes; unchanged local raw files remain available. MacKay T100 confirmation is complete 40/40. OSD audit 61820674 completed; 212 audited OSD points are published, two completed length338/p=.01 endpoints await final audit, and four length450 points continue. Complete collector 61820676 remains dependent on the original array. No simulations were rerun or submitted, and phase gates/counters remain unchanged.

Prior result: quick261113-v31, implementationc595969. Roffe damping is complete and published: all1526 tuning/436 independent confirmation points audited. Public104 curves/1073 points at that snapshot. See data/reproductions/roffe-2005-07016-damping/RESULTS.md and completion-status.json. Original failed publication history is retained; equal paper metadata now merges safely. The separate MacKay rare-event point subsequently completed, as recorded above.

Historical launch: quick261113-q96, implementation4c8471f. Arrays61789908/61794900 and selection controller61789909 completed; final collector61794901 failed at catalog refresh after its full audit. Follow-up v31 repairs publication; do not resubmit simulations or change frozen files.

Prior campaign: quick 261113-hk2, implementation `1b040da`. Old 88200 damping is canceled. Curve alignment favors inferred T=100, with 50 also plausible; no historical cap is asserted. Fresh baseline and training are audited; confirmation had 39/40 terminal points at that snapshot and is now complete 40/40. The old 30-point long-budget MacKay results and displayed curves stay intact. See the hk2 summary for frozen plans, retrospective caveats, tests and accepted commands.

Latest literature research: spikes 054 (PARTIAL: bounded citation screening, not an exhaustive global ranking) and 055 (VALIDATED: explicit baseline evidence in the screened sources). Twelve direct BP baseline papers are listed with min-sum/SPA families and evidence locations; foundational code benchmarks and BP+OSD/BP+SSF hybrids are separate. JSON/CSV and an offline consistency verifier accompany the report. This source list does not certify reproduction settings or authorize simulations. Scientific phase progress is unchanged.

Latest builder action: quick task 261110-lsd, implementation `7b8e702`. Request experiment results enables after validation, prepares a complete portable JSON and prefilled GitHub issue, and invalidates on configuration changes. User review/attachment/submission remains on GitHub; no backend job was launched. Twelve browser workflow groups passed.

Latest picker fix: quick task 261109-mzx, implementation `1e6b825`. Add a decoder / curve lists only curves not currently displayed on that plot. Hidden curves can be restored without duplication; all-displayed empty state and independent plot state pass Chromium checks (16 workflow groups total).

Latest interface work: quick task 261109-mcf, implementation `7eeddf7`. Active v2 uses a single multi-rate projection for all results and public input choices: 63 curves / 319 points / 6 codes / 0 registered circuits. Empty/default/import states and stale selections are verified. Full retained catalog and archived v1 are unchanged. See the quick summary, verification and explicit removal audit. Scientific phase progress and gates remain unchanged.

Latest kernel work: completed F01 → F02 corrections and qualification in quick task 261109-hhq, implementation 78f1c1c. See spikes/CANONICAL-KERNEL-SHARED-POLICY-FIXES.md and quick/261109-hhq-fix-f01-memory-admission-then-f02-sinter/qualification.json. Kernel regression: 1,712 passed / 20 skipped; final shared suite: 161 passed. Exact legacy/shared-v1 replay and real Sinter v2 worker execution pass. All 3,839 tracked result/data files are preserved, with no affected campaign found. Pauli/GPU source and prior qualification remain unchanged; prior evidence is not relabelled as fresh execution.

**Resume file:** None

Last session: 2026-11-10T22:51:46+00:00
Stopped at: Advanced BP kernel tuning running. Confirmation jobs and collector 62150056 depend on training.
Next step: Requested builder request action and display/catalog cleanup are complete; resume the existing Phase 11 scientific work when directed. Preserve identity versions and qualification labels. Phase 11 scientific gaps and Phase 5 human review remain open; Phase 7 stays paused.

Design continuation: `.planning/phases/05-guided-and-perturbative-bp-interventions/05-DESIGN-TASKS.md`.
Latest execution report: `.planning/phases/04-memory-policies-and-relay-bp/04-EXECUTION-CONTINUATION-20260927-RESUMED.md`.
Latest isolated terminal ledger audit: `gsd/phase4-memory-integration-20260926` at `263501e`, `.planning/phases/04-memory-policies-and-relay-bp/04-CALIBRATION-LEDGER-AUDIT-PREPARATION.md` in that branch.
The September 26 development PDF remains a historical snapshot. The September 29 update records the terminal calibration. Phase 4 is complete under the revised scope; Phase 5 implementation passed technical verification and awaits the human notebook/HTML review. The comprehensive production campaign was cancelled by the user and is no longer a Phase 4 gate.
