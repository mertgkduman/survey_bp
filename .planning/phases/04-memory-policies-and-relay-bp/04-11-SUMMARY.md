---
phase: 04-memory-policies-and-relay-bp
plan: "11"
subsystem: finite Phase 4 Relay pilot evidence and allocation
tags: [relay, benchmark, slurm, caps, provenance]
requires: [04-10]
provides: [representative-work-evidence, frozen-pilot-caps]
affects: [04-12, 04-13]
tech-stack: [Python, SLURM, public CLI, exact Relay-v0.2.2]
key-files:
  created: [data/evidence/phase4-pilot-design-amendment-v3.json, data/results/phase4-memory-relay/benchmark-v3-b1-p07-bounded-three-leg.json]
  modified: [scripts/run_phase4_pilots.py, data/manifests/phase4-pilot-caps.json, tests/canonical/test_phase4_evidence.py]
decisions:
  - "Use one OMP_NUM_THREADS=1 worker because the job cgroup had no safe memory headroom for a two-worker proof."
  - "Use BB/B1 p=.07 and HGP p=.03 only through the retained amendment and B1 three-leg-equivalent cap."
metrics:
  duration: "ongoing SLURM evidence campaign"
  completed: 2026-09-25
status: complete
actuals:
  tokens: 399675
  tasks: 2
  commits: 17
plan_head_before: ec51e883cde3a80115fe003f148948e393de2b1d
---

# Phase 04 Plan 11: Representative Relay Benchmark and Caps Summary

Retained 32-shot representative Relay evidence and a numeric, one-worker Phase 4 cap contract before calibration.

## Completed Tasks

1. Recorded SLURM 55938300 entitlement and retained public canonical/native benchmark cohorts for BB-144, B1, and HGP.
2. Froze rate-specific work, runtime, configuration, shot, trace, factorial, native, and evaluation caps with separate namespaces.

## Evidence and Decisions

- The representative p=.03 cohort ran all baseline, 31-leg Relay, and exact-author native arms. HGP exercised later legs through all 31 declared legs; BB and B1 did not.
- Retained p=.05 and p=.07 baseline scans selected BB p=.07 and HGP p=.03. B1 p=.07 has four unbounded public-boundary timeouts, retained as incomplete rate-scan evidence.
- A fresh matched B1 p=.07 bounded cohort kept the same physical sample stream and converted prior timeout IDs 0, 7, 19, and 20 into retained `budget_exhausted` ledger terminals. It completed 32/32 with public-command p95 121.235 seconds, max 134.764 seconds, and four budget terminals.
- The cap amendment explicitly distinguishes the original design's rate grid and source/canonical Relay controls from the 31-leg controlled CSS calibration adaptation.
- Remaining wall at freeze was 2,202,370 seconds. After a 220,237-second margin, category ceilings are 693,746 calibration, 891,959 evaluation, 198,213 native, and 198,213 fixture/trace seconds.
- Calibration fixes 54 BB, 20 B1, and 14 HGP coarse candidates at 32 shots per preset; one fixed refinement candidate per code/preset; fresh evaluation is 448 matched shots per listed arm; factorial is 14 arms × three original rates × seven shots per code.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'frozen_v3_caps or bounded_probe or representative_v3_manifest or rate_amendment or benchmark_timeout'` — 5 passed.
- Independently recomputed cap and design digests, verified all cited benchmark digests, B1 bounded work qualification, namespace separation, and numeric category arithmetic.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Replaced the provisional one-iteration v2 cap basis with representative 80/60 evidence.
2. [Rule 2 - Critical evidence retention] Added durable canonical/native started journals, public command timing, and timeout/incomplete retention.
3. [Rule 2 - Scientific correctness] Added the matched B1 p=.07 bounded three-leg-equivalent cohort after the unbounded p=.07 scan had four timeouts.

## Known Limitations

- The B1 unbounded p=.07 rate scan remains incomplete; only its separately labeled bounded adaptation is eligible for calibration.
- Canonical per-shot RSS was not measured. Native RSS is a cumulative child-process high-water mark, not a per-shot measurement.
- The adapted calibration and factorial counts are precision limited; Wilson intervals and capped/inconclusive outcomes remain required.

## Self-Check: PASSED

- Representative reports, portable ledgers, amendment, cap manifest, and focused tests exist and are committed.
