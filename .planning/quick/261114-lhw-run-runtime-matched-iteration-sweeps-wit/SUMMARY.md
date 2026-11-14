---
id: 261114-lhw
status: complete
campaign_status: running
implementation_commits: [ab91af9, 8e903bc]
---

# Joint controls and runtime-matched iteration histories launched

Implemented a separately versioned study that delegates all arithmetic to the unchanged canonical binary and joint-Pauli min-sum sweep helpers. Both constant scaling and multiplier times the original1-2^-t schedule are explicit; offset is applied in natural-LLR units before scaling. Old-message damping, scaling and offset all reach live canonical operands.144 exact candidate/belief/stopping/work comparisons pass across four toric codes, two families, two rates and combined controls. A dynamic-module Numba cache reload issue found in the prototype was fixed by registering the study engine module; a fresh-process cache regression passes. No canonical source or previous campaign was edited.

Frozen study has218 point workers:109 original code/rate strata times BP(X-only) and Q-BP(depolarizing1.5p_X). Each measures its contemporaneous same-CPU warmed BP+OSD0 reference, screens80 coarse damping/scale/offset combinations, refines promising settings, then rechecks five finalists and the previous damping baseline on4096 independent finalist-training shots.256-shot coarse training,4096-shot finalist training and final20-failure/1e8-shot confirmation use separate seeds. All candidate/cap histories remain retained; training is never pooled with confirmation. Select by LER within the runtime budget, then executed iterations. No finite grid or low-count result is called a global optimum.

Caps start at n, double and refine integer runtime brackets. Q-BP's n-cap can already cost1.2–6.6x the reference in the pilot, so those starting points remain recorded as over-budget and lower caps are tested too. Both the previous damping settings and joint selected controls receive fresh cap progressions, including the matched cap, original n-cap, intermediate caps and upper context. Calibration tolerance is10%; actual confirmation ratios are recorded without assuming equality. Early-convergence saturation, lower-cap overhead and operational search-guard cases remain visible.

Real full-search qualification on one Q-BP stratum tested102 control combinations and963 control/cap measurements, then10 shortened confirmation caps totaling699 shots. Exact resume, complete independent ledgers, endpoint replay, report generation and normalized catalog pass. The selected calibration cap23 was1.029x reference time; its shortened fresh-confirmation ratio was1.088x. These are qualification-only data and are never registered or pooled with production.

Passed65 unique regression cases, plus a collector-resource dispatch recheck;12 Chromium groups cover exact constant/ramped alpha and beta labels, table/CSV time-reference ratio, saved settings, blocked substitution in the builder, singleton filtering, stale choices, empty views, custom inputs and archivedv1. Injecting the real qualification extension into a catalog does not qualify its singleton curves or merge incompatible controls. Public view remains112 curves/1246 points/12 codes/0 circuits at launch.

Reports retain every point/control/cap independently of public curve eligibility. Confirmed rows include LER, stopping-aware95% intervals, mean sweeps, directed edge updates, warmed time, reference time and actual time ratio. Tuning rows remain separate. Only full-ledger/manifest/endpoint-audited confirmation reaches the extension, grouped by exact concrete control/cap; the existing multi-error-rate eligibility rule remains central. Public labels and exports now expose scale, offset and time/reference ratios.

Source commitab91af9 preserves the original unlaunched plan. Resource review increased only collector memory from2GiB to16GiB; its scientific design is byte-identical. That initial plan and exact source version are retained, while8e903bc seals the production source/plan. Workers remain one CPU/2GiB with private job-local JIT caches; the collector is one CPU/16GiB. All fit the existing site resource envelope. No production samples used the initial plan.

Launched Slurm array61824235 with complete independent collector61824236. Scheduler status and live calibration progress are in launch.json; point workers began tuning successfully. Main study results are prospective and not yet claimed complete. Final audit/report/catalog refresh follows successful array completion. Existing OSD and MacKay jobs are left running. Source, plans and dispatch are pushed; Phase11 gates/counters remain unchanged.

First production publication: six point workers and45 fresh control/cap measurements independently audited,36,041 shots/900 logical failures. The report also preserves5,496 separate coarse/finalist training measurements. All189 historical raw series remain unchanged. Active view112→117 curves and1246→1258 points,12 codes/0 circuits unchanged; additional singleton cap results remain in the study table and raw extension. Seven postpublication browser groups pass on the real data. Many more workers have already completed or continue running; this is an audited snapshot, not campaign completion.
