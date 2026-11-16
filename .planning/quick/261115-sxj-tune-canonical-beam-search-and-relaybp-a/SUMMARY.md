---
id: 261115-sxj
status: complete
data_commit: 1154bbf
initial_campaign_workers: complete
initial_full_audit: running
frontier_campaign: running
phase_gates_changed: false
---

# Tuned beam/RelayBP studies launched and first results published

Implemented a separately versioned search traversal calling the unchanged canonical float64 min-sum sweep. Original-syndrome stopping, masked warm-start beam branches, stable reliability pruning, posterior-only Relay transfer, per-iteration disordered affine-prior memory, multiple-solution weight selection and all-path work are explicit. No hidden truth enters decoding. The four original Roffe toric codes and all 109 X-only source-rate strata allow a same-channel OSD-0 comparison. Paper circuit-noise performance and Pauli Q-BP remain separate.

Independent scalar equations/controller agree exactly on128 real-code cases, including360 beam expansions,411 relay legs and83 prunes. Qualification pilots retain complete event ledgers and are not confirmation evidence. Twenty controller/pipeline tests, seven frontier orchestration tests and53 catalog/projection/display regressions pass (80 unique cases). Twelve final Chromium groups pass on the expanded catalog and search fixtures. The tests verify exact seeded replay, resume, original algebra, work, locks, full-ledger/endpoint/reference checks, source hashes, distinct cohorts, dependency/idempotence and tamper rejection. A NFS test-directory cleanup retry, expired local HTTP server and expected historical-count exclusion updates were resolved; scientific values were not modified.

The first frozen study (implementation57eebaa; plan bd0b6527cbfe152957867896ce48855344b9ea7637317de52b1a07ab473a8ce0) ran218 one-CPU workers as61869371. All218 now completed0:0; final full audit61869372 is running. Its original512-shot coarse/65,536-shot-or100-failure finalist search tunes numerical controls, topology, solution count and Relay memory, then freezes before20-failure/100M-shot confirmation. Actual mean time relative to contemporaneous warmed same-CPU OSD-0 and1%-bin p50/p95/p99 are explicit.

The completed-worker snapshot independently audits114 workers,277 fresh settings,3,297,851 shots/5,540 failures and23,839 separate training measurements. Every training/confirmation ledger, source/selection/manifest/reference and deterministic endpoint passes. Compressed receipts/training tables and all per-point results are retained. An initial live collection encountered a new-reference enumeration race and published nothing; the recorded snapshot helper admits only sealed completed workers and uses the unchanged frozen audit helpers. Automatic full collection remains safe after array completion.

At length242/X-only p=.02, beam LER4.0115e-4 (95%[2.4505e-4,5.9507e-4]) and Relay2.6817e-4 ([1.6381e-4,3.9782e-4]) use.145/.166 times their same-CPU OSD-0 reference. They are much below the previous selected BP .16129 but still above audited OSD-0 8.8676e-6. The estimates are descriptive20-failure results; cross-host raw runtimes and fine statistical rankings are not implied. Full settings and pointwise intervals remain in the report/CSV. The PNG/PDF scatter figure does not connect incompatible controls and marks pending results.

Many zero-failure coarse ties selected only fast finalists, leaving substantial runtime budget unused. Preserved that study and separately froze the broader training-only proposal study (implementation7610e01). It retains fast winners plus budget-spanning and one/four-solution arms, uses new finalist/confirmation seeds2026111562/1563, and explicitly documents design after first-study observations. Its selector never reads parent confirmation outcomes. Array61870314 follows parent workers; collector61870315 also requires the complete parent audit61869372. Slurm lost old completed individual tasks from its live cache, leaving aftercorr unfulfilled;215 pending dependencies were released only after successful sacct0:0 and exact source completion/selection verification. Resource-only receipts are retained; numerical controls, raw files and audit dependencies were unchanged. Remaining corresponding dependencies resolved, and no eligible pending workers remained at recheck.

Registered both normalized catalog files centrally; the future frontier file is empty until audited output. Search configuration is part of conservative implementation identity, so unlike searches cannot supply each other's qualifying error rates. Active catalog grows308→324 curves and2627→2667 points, with12 codes/0 circuits unchanged. All547 historical raw series preserve every point.277 raw search measurements form253 concrete-policy series; singleton policies stay out of public choices and remain in the dedicated report. Search labels and saved settings include the actual controls, and the builder refuses silent substitution of ordinary BP. Empty/stale inputs, custom matrices/Stim and archivedv1 pass. No old frozen source, raw result, canonical kernel, GSD model/config, phase gate or plan counter changed.

Campaigns/audits continue automatically. The quick task completes implementation, qualification, launch and partial reporting; it does not mark the stronger study or Phase11 scientifically complete.
