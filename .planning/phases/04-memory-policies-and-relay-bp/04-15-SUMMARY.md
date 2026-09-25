---
phase: 04-memory-policies-and-relay-bp
plan: "15"
subsystem: phase4-pilot-evidence
tags: [memory-policy, relay-bp, pilot-design, provenance, tdd]
requires: [04-05, 04-09]
provides: [phase4-pilot-design, three-code-v4-pilot-manifests]
affects: [phase4-pilot-execution, relay-comparisons, sample-provenance]
tech_stack:
  added: []
  patterns: [canonical-json-digest-binding, immutable-presampling-design, matched-physical-sample-namespaces]
key_files:
  created:
    - data/evidence/phase4-pilot-design.json
    - data/manifests/phase4-memory-relay-bb144.json
    - data/manifests/phase4-memory-relay-hgp.json
  modified:
    - data/manifests/phase4-memory-relay-b1.json
    - tests/canonical/test_phase4_evidence.py
decisions:
  - "The Phase 4 design freezes the common baseline, all selected memory-family arms, three source-grounded interactions, Relay ablations, and easy/visible-failure/harder noise regions before sampling."
  - "Each code receives a distinct physical sample namespace shared by every arm at that code and rate; source-procedure, canonical-procedure, and controlled-matched settings remain distinct."
  - "B1 binds the frozen v3 artifact plus the canonical digest of its resolved Plan 04-09 identity record; generated HGP remains an explicit non-paper-exact pilot fixture."
metrics:
  duration: "approximately 22 minutes"
  completed: 2026-09-24
status: complete
plan_head_before: 6a644c7275c16eedb653f3e7ef6faba9a58be2a6
commits: 2
actuals:
  tokens: 5388
  tasks: 1
  commits: 2
---

# Phase 04 Plan 15: Three-Code Pilot Design Summary

Frozen Phase 4 CSS pilot inputs now bind BB-144, resolved B1, and generated HGP to exact artifacts, matched samples, focused factorial arms, and immutable source or controlled Relay configurations.

## Delivered

- Added a versioned pre-sampling design with baseline, each selected memory family, three research-selected interactions, and Relay component ablations.
- Declared a three-region noise grid and per-code namespaces that require the same physical samples for all arms at one code/rate point.
- Added strict V4 BB-144 and HGP manifests and upgraded B1 provenance with the frozen design digest, resolved B1 identity-record digest, and a matched physical-sample identity.
- Preserved distinct qualifications: BB-144 is an exact pinned artifact, B1 is source-reconstructed with inventory-only reconciliation, and HGP is generated and explicitly not paper-exact.
- Added tests that fail if the design, manifest identities, B1 gate, matched samples, Relay configuration labels, or HGP qualification drift.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py -k 'artifact_gate or pilot_design or noise_grid or matched_samples or factorial'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase4_evidence.py` — 9 passed, 1 skipped (the pre-existing notebook placeholder).
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight` passed for BB-144, B1, and HGP Phase 4 manifests.

## TDD Gate Compliance

- RED: `test_phase4_pilot_design_prespecifies_focused_factorial_and_noise_grid` failed intentionally because the pilot-design artifact did not exist; `.gsd/tdd-evidence/04-15-task-1-red.json` verified `RED_EVIDENCE_OK`; commit `7411068`.
- GREEN: the focused evidence checks and public preflights pass with commit `6a04452`.
- REFACTOR: not needed.

## Decisions Made

- The initial frozen design cannot inspect calibration outcomes. Any later grid amendment needs a retained baseline scan before calibration, a versioned reason, and preservation of prior design evidence.
- The V4 public schema keeps the detailed design in evidence data; manifests bind it with its canonical JSON SHA-256 and persist only schema-admitted provenance and sample identity fields.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All declared design, manifest, and test files exist; both TDD commits are present in git history.
