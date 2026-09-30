---
phase: 05-guided-and-perturbative-bp-interventions
plan: "08"
status: complete
subsystem: public-intervention-execution
tags: [public-manifest, cli, replay, ledger-v5]
requires: [05-04, 05-05, 05-06, 05-07]
provides:
  - strict public CanonicalExperimentV5 and compact CanonicalManifestV6 intervention projection
  - baseline and six source-qualified controller dispatches through saved public manifests
  - version-five structural ledger, deterministic controller replay, and independent evaluation checks
affects: [05-10, 05-14, 05-11, 05-13]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-09-30
---

# Phase 5 Plan 08: Public intervention execution

The complete V5 public manifest preflights one identity baseline or one source-qualified intervention and projects to compact V6 without changing historical schemas. The public runner routes each selected arm to its controller, validates an original-space recovery before truth-aware evaluation, and writes version-five structural events.

## Evidence

- Version-five events bind manifest, artifact, sample, execution identity, source variant, qualification, controller rows, transform/lift/original checks, selection, evaluation, and unique leaf work.
- The shot verifier reruns the selected controller with a fresh budget tree and compares event order and every semantic payload; recomputed event hashes do not make altered claims pass.
- Small-fixture public paths cover baseline, guided decimation, impulse, freezing, syndrome flip, and sign flip. A pinned B1 run covers Restart Belief.

## Verification

- Public execution, manifest, and CLI modules: 135 passed.
- Rehashed qualification, missing attempt, duplicate leaf, and altered candidate tests: 4 passed.
- B1 public restart and replay: 1 passed.
- A full two-shot V5 run and `verify-run` completed successfully.

## Commits

- `799a8fd` — strict V5/V6 preflight contract.
- `5bc56bc` — public controller dispatch and independent structural replay.

## Known limit

The runtime ceiling is checked after bounded controller execution. Attempt, action, iteration, and typed work caps are checked before their respective mutations. Phase 5 public traces are rejected at preflight because their observation grammar has not been implemented for V5.
