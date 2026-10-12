---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "10"
subsystem: campaigns
tags: [yao, b1, inverse-binomial, cap-censor, canonical-adaptation]
status: complete
dependency_graph:
  requires: [09-09, 09-16, 09-17, 09-20]
  provides: [bounded Yao B1 adaptation assessment]
  affects: [09-15]
key_files:
  modified: [src/bp_registry/campaigns/execution.py, src/bp_registry/manifests.py, src/bp_registry/runner.py, tests/test_phase9_yao_b1_tracer.py, docs/campaigns.md]
  created: [data/studies/phase9-yao-b1-t001-p010-v4-assessment.json]
actuals:
  tasks: 2
---

# Phase 09 Plan 10: Bounded Yao B1 Adaptation

## Delivered

- Froze T=1, B1 p=0.10, the authored target 0.855932, 100 failures, 95% exact inverse-binomial stopping, factor 1.5, global shot order, one local worker, and measured resource caps. The final executable study is `data/studies/phase9-yao-b1-t001-p010-v4.json`; superseded identities remain retained with their diagnostic evidence.
- The v1 local run ended with a sealed zero-credit partial. V2 and v3 stopped before terminal due event-size guards. The first v4 run emitted a complete canonical `wall_clock_deadline` ledger but the campaign adapter could not classify it; its ledger hash and zero-credit status are retained in `first-attempt-diagnostic.json`. Added a 4 MiB guided event ceiling in the v4 manifest and mapped this exact canonical terminal to the frozen timeout category.
- A fresh v4 run under the unchanged scientific plan sealed two timeout terminals. The first exhausted campaign cap was wall, after 2,104,202,730,786 ns of observed boundaries. The cap receipt, merge, assessment, and independent public verify all agree on two completed shots, 2 frozen all-shot timeout failures, 3,591 events, 9,470,745 work units, and 12,596,648 evidence bytes.
- The assessment is `inconclusive_cap_censored`: no `T_100`, inverse-binomial interval, rate, or target verdict was computed. Timeout classification is explicit and is not reported as an observed source-style logical error rate. Source implementation/settings and the exact author B1 artifact remain unverified; the result is a `canonical_adaptation` only.

## Verification

- Public merge/assess/verify succeeded for `data/results/phase9-yao-b1-t001-p010-v4/retry-run` and its final report.
- Focused tracer and terminal tests check frozen source/profile digests, diagnostic zero credit, exact cap reason, no inference at censoring, and public replay.

## Deviations

The measured event record exceeded the earlier serializer ceiling; executable variants v2-v4 were frozen separately. Unsealed diagnostic attempts were not promoted into the denominator. The campaign ended at the prospective wall cap before 100 failures, as permitted by the plan.

## Self-Check: PASSED

The two tasks ended in the plan's allowed verified cap-censored state, without a source-faithful or decoder-ranking claim.
