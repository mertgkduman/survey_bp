---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "12"
subsystem: evaluation
tags: [schedule, paired, b1, bounded]
status: complete
dependency_graph:
  requires: [09-11, 09-19]
  provides: [bounded schedule control assessment]
  affects: [09-15]
key_files:
  created: [data/studies/phase9-update-schedule-control-v1.json, tests/test_phase9_update_schedule_control.py]
actuals:
  tasks: 2
---

# Phase 09 Plan 12: Schedule Control

## Delivered

- Verified the frozen B1 p=0.10 flooding/serial manifest pair differs in scientific configuration only by schedule. Run ID and deterministic decoder stream labels differ; artifact, channel, budgets, and other policies match.
- Executed all three prospectively frozen matched samples through public local ordered work. A serial work-budget terminal initially exposed a missing campaign taxonomy mapping. Its unsealed ledger is retained with zero credit; the adapter now classifies that exact null-outcome budget stop as nonconvergence, and the missing unit was executed again under the same frozen plan.
- Public merge, assessment, and verify passed for six sealed arms. The paired all-shot table has 3 joint failures, zero discordant pairs, risk difference 0, and interval [-0.7679, 0.7679]. Neither arm accepted a candidate under these tight caps, so conditional failure rates are unavailable with a reason. Typed receipts preserve actual work, iterations, runtime, process-scope RSS, evidence, and storage. This bounded result supports no superiority claim.

## Verification

- `tests/test_phase9_update_schedule_control.py`: 2 passed.
- Public plan/run-local/merge/resume/assess/verify passed, including an inside-pair partial and independent report replay.

## Self-Check: PASSED

The frozen positive N was completed, with an inconclusive small-sample mechanism result and no source-curve claim.
