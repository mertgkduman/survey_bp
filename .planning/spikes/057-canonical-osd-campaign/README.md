---
spike: '057'
idea: efficient-canonical-bp-osd
name: canonical-osd-campaign
type: standard
validates: Given qualified OSD-0/CS-10, when the canonical BP controller emits its terminal state, then optional fallback runs without hidden truth or second BP and produces paper-budget auditable results.
verdict: VALIDATED
related: ['056']
tags: [osd, canonical, campaign, roffe]
---

# Spike057: canonical BP handoff and controlled Roffe OSD campaign

## What This Validates

Use the existing canonical min-sum sweep unchanged, preserve its terminal signed posterior, invoke independently qualified OSD only after original-syndrome nonconvergence, then evaluate through the independent CSS outcome checker. Freeze both source-compatible undamped BP+OSD-0 and BP+OSD-CS10 over the original109 rate/code strata (218 points), max sweepsT=n, float64 and20 logical failures or1e8 shots. Every measurement retains raw per-shot ledgers and separate BP/OSD work.

## Investigation Trail

Initial design uses the original undamped BP so postprocessing is the only changed setting. Existing damped BP/Q-BP and paper CS60 results remain comparison context. Production dispatch depends on Spike056 qualification; no old plan/runtime or historical result is edited.

The first controller retained the public Python sweep wrapper. The128-shot smoke passed all ledgers/replays but exposed substantial per-iteration wrapper overhead. Its frozen `roffe-2005-07016-osd` plan remains an unlaunched baseline. A separate `roffe-2005-07016-osd-fast` campaign compiles only traversal/allocation/stopping around the unchanged canonical sweep and original-syndrome check. It preserves the original initialization prior separately from the canonical v2 update prior; recomputing them as one expression would change float64 beliefs.

## Results

All436 full-budget terminal states over109 original code/rate strata match candidates, bitwise float64 terminal beliefs, stopping and work.192 complete events match every non-timing field, including complete OSD candidate-set hashes. Both converged and nonconverged paths are represented. The separate fast smoke audited128 shots,72 OSD calls, exact resume, full-ledger and endpoint replay, normalized publication and comparison reporting. Qualification shots are unregistered and never pooled with production.

Alternating warmed complete-event timings improve approximately5–48x over the scalar controller in the sampled cases. At p=.01 they are94–335 microseconds/shot including sampling, decoding, independent evaluation and hashes, excluding JIT and ledger I/O. These are small-sample forecasts without exclusive-core guarantees; stage times in reported results exclude sampling/evaluation. Native OSD-only comparisons remain in Spike056.

The frozen production design has218 points (109 strata times OSD-0/CS-10), T=n, original alpha schedule/min-sum/X-only grid, one CPU/2GiB per point,20 logical failures or1e8 shots, and an after-success full audit. It preserves earlier evidence, native implementations, canonical kernels and phase gates. A free-space checkpoint guard avoids filesystem exhaustion without changing scientific stopping. Candidate methods and execution backend participate in curve identity; singleton filtering and empty/stale-choice handling remain central. Tables/CSV show BP work beside separate OSD costs.

Validation of implementation and launch is distinct from completion of the prospective statistical campaign. Production measurements and source comparisons are updated in `data/reproductions/roffe-2005-07016-osd-fast/RESULTS.md` only after full retained-ledger audit. No CS60 reproduction or decoder superiority is inferred from qualification.

## Production launch

Committed implementation `a4497da` and launched Slurm array61804747 with complete-audit collector61804748 on2026-11-14. Each task owns one frozen code/rate/method point and one CPU; pending tasks retain the same plan. Initial launch has200 running workers and18 pending. `launch.json` contains exact scheduler commands and dependency. Production completion and partial comparisons are tracked separately in the study report.

First publication:173/218 points audited,153,881 shots and3,460 logical failures;88 OSD0 and85 CS10 points. Public view104→112 curves and1073→1246 points;12 codes/0 circuits unchanged. All181 historical raw series remain structurally identical. Seven real-data browser groups pass after publication, in addition to the five OSD-specific groups. The complete source-rate table shows pending values honestly.

One initial worker (index83) encountered NFS stale-file-handle error116 while loading the shared Numba cache during warmup, before sampling. Retry61805013 used a job-private cache and completed0:0 with the same frozen plan. Collector61804748 was replaced by61805014, dependent on termination of the full initial array and success of the retry, and still requiring all218 audited terminal points. Exact commands/reason are in `recovery-dispatch.json`. No simulation source or numerical settings changed.
