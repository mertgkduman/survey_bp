---
phase: 03-update-rules-and-scheduling
plan: "17"
subsystem: hsu-group-pilot
tags: [hsu-ndgsbp, css-code-capacity, retained-ledger, SCH-06]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: Plan 03-16 full group traversal and replay
provides:
  - strict source-labeled BB-144 two-shot Hsu group manifest
  - retained independently verified public ledger and result
  - bounded SCH-06 execution evidence without a curve-reproduction claim
affects: [SCH-06, phase-03-verification]
key-files:
  created:
    - data/manifests/phase3-hsu-group-pilot.json
    - data/results/phase3-hsu-group-pilot/events.jsonl
    - data/results/phase3-hsu-group-pilot/result.json
  modified:
    - tests/test_canonical_cli.py
requirements-completed: [SCH-06]
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 17: Retained Hsu CSS Pilot

A strict V3 manifest runs two BB-144 binary CSS shots using Hsu's size-two, overlap-one groups and a declared schedule root. The retained ledger records source identity, both realized group traversals where reached, source-qualified local progress, work, and separate setup/decode runtime. The result remains `pilot_adaptation` / `not_assessed`. It does not claim classical AWGN curve reproduction or Moradi RL-S execution.

Both shots terminate and independently verify: one converged with an exact recovery after 70 group units, while one reached the 72-unit limit. The two-shot result preserves both outcomes in its denominator. SCH-06's executable source-defined schedule and construction/order evidence are delivered; the unavailable Moradi artifact record remains separate.

## Verification

- Public `preflight`, `canonical`, and `verify-run` succeeded on `data/manifests/phase3-hsu-group-pilot.json` and the retained result.
- `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py tests/test_canonical_cli.py -k 'hsu or group_shuffled'` — 9 passed.
- `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 300 passed.

## Commit

- `8bb7ef7` — retained source-labeled pilot manifest, ledger, result, and regression test.

## Deviations

- The bounded retained pilot uses two shots rather than a single shot, preserving a converged and an iteration-limit terminal.
- Tests and retained artifact were committed together; no separate TDD red-step evidence is claimed.
