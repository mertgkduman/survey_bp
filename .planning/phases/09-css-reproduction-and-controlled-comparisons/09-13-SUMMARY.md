---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "13"
subsystem: evaluation
tags: [relay, beam, shared-initial, holm]
status: complete
dependency_graph:
  requires: [09-11, 09-19]
  provides: [bounded Relay and Beam baseline contrasts]
  affects: [09-15]
key_files:
  created: [data/studies/phase9-relay-beam-control-v2.json, tests/test_phase9_relay_beam_control.py]
actuals:
  tasks: 2
---

# Phase 09 Plan 13: Relay and Beam Control

## Delivered

- Ran all 16 frozen B1 matched physical samples through one initial BP, Relay continuation, and Beam continuation per sample. Exactly 16 shared initial receipts feed 48 terminal arms. Common BP, continuation, and independent validation costs are separated.
- A first run exposed one no-candidate initial BP terminal incorrectly charged one original validation check. Its evidence remains under `phase9-controlled-evaluation-v1` and its study is marked diagnostic. The corrected producer records zero actual original checks for no-candidate terminals; the full frozen design was executed into version-two result evidence and independently verified.
- Both prespecified baseline contrasts have 8 joint successes, 8 joint failures, zero discordant pairs, risk difference 0, and simultaneous interval [-0.2396, 0.2396]. The one Holm family is not rejected. This bounded adaptation makes no decoder-ranking claim.

## Verification

- `tests/test_phase9_relay_beam_control.py`: 2 passed.
- Version-two public merge, assess, and verify passed with 16 complete groups and exact shared-input lineage.

## Self-Check: PASSED

Both frozen contrasts have complete matched evidence and corrected actual costs.
