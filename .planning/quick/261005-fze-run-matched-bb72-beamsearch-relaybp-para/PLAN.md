---
quick_id: 261005-fze
status: in_progress
date: 2026-10-05
---

# Matched BB72 BeamSearch and RelayBP campaign

1. Freeze an independent BB72 CSS campaign before sampling: p=0.05 and p=0.08, separate 128-shot parameter-selection cohorts and 512/1280-shot evaluation cohorts, matched physical samples across three extra-leg iteration profiles and both damping settings. The study uses the already qualified controlled CSS adaptations and the shared 8,640 additional C2V update cap.
2. Add a resumable, source-sealed shard runner. Retain one shot ledger per rate/cohort/profile, initial and additional work separately, deterministic replay, all outcomes in the denominator, and measured serial runtime.
3. Select each method's extra-leg profile by selection-cohort failure count, then C2V work, then profile ID, before opening evaluation results. Freeze selection hashes and rule. Run all evaluation profiles to preserve the parameter view.
4. Produce an evaluation report with selected Beam-vs-Relay paired comparisons, exact failure intervals, work/runtime, a shared-work view, and source-adaptation limits. Do not claim original circuit-paper reproduction or use selection shots in evaluation estimates.
5. Run focused tests and a small prelaunch replay, submit bounded HPC shards, verify and publish only terminal evidence. Keep Phase 6 planning status separate from this ad-hoc campaign.
