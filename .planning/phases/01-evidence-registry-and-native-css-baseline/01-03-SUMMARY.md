---
phase: 01-evidence-registry-and-native-css-baseline
plan: 03
subsystem: native-css-tracer
tags: [pydantic, ldpc, css, ledger]
requires:
  - {phase: 01-01, provides: collectable contract tests and environment probe}
  - {phase: 01-02, provides: approved exact package identities}
provides:
  - Strict version 1 project fixture manifest
  - Native BP-only CSS tracer with independent outcome classification
  - Source-linked JSONL begin and terminal shot evidence
affects: [01-04, 01-05, 01-06, 01-07, 01-09]
actuals: {tokens: 5000, tasks: 2, commits: 4}
tech-stack:
  added: [pydantic 2.13.5, bposd 2.1]
  patterns: [strict preflight, hidden-truth decoder boundary, native reference adapter]
key-files:
  created: [src/bp_registry/manifests.py, src/bp_registry/css.py, src/bp_registry/reference.py, src/bp_registry/ledger.py, src/bp_registry/runner.py, docs/phase1-pilot.md]
  modified: [pyproject.toml, docs/environment-pins.md, tests/test_reference_smoke.py]
key-decisions:
  - "The three-qubit fixture is project-owned and carries pilot_adaptation/not_assessed status."
  - "The isolated environment inherits already observed global packages and installs only the two approved distributions plus resolver dependencies."
patterns-established:
  - "Native decoding receives only checks, syndrome, prior and settings; evaluation receives hidden truth."
requirements-completed: [MAP-02, REG-01, REG-03, CSS-01, CSS-03, CSS-04, LED-01]
coverage:
  - id: D1
    description: One project fixture shot passes strict preflight, native BP, evaluator and ledger
    requirement: CSS-03
    verification:
      - {kind: integration, ref: "tests/test_reference_smoke.py", status: pass}
    human_judgment: false
  - id: D2
    description: Reproducible local command and observed dependency identities are recorded
    requirement: REG-03
    verification:
      - {kind: e2e, ref: "python -m bp_registry.runner data/manifests/project-three-qubit-fixture.json", status: pass}
    human_judgment: false
duration: 18min
completed: 2026-09-22
status: complete
---

# Phase 1 Plan 03 Summary

**A strict fixture manifest now drives native BP decoding, independent CSS evaluation, and an identified JSONL shot record.**

## Accomplishments

- Added a Pydantic version 1 fixture contract that rejects unknown and missing fields, invalid rates and incompatible settings before sampling.
- Added project-owned three-qubit CSS algebra, deterministic X sampling, a native `ldpc.BpDecoder` adapter, an independent outcome classifier, and a persisted begin/terminal ledger.
- Added a runnable `python -m bp_registry.runner` fixture command and recorded the actual isolated environment, import locations and full observed `pip freeze`.

## Task Commits

1. **Red fixture test:** `b48aeda`
2. **Production tracer:** `c69c7dd`
3. **Command, package and documentation:** `fe6eb06`
4. **Ignore editable install metadata:** `3c7ec54`

## Decisions Made

- Source URI and revision are labeled methodological context for a project-owned fixture, never a publication-code reproduction.
- Native edge-update counts are null with an explicit missingness reason.

## Deviations from Plan

- Added `.gitignore` and a fixture manifest file to make the local command runnable without staging environment artifacts.

## Issues Encountered

- `BpDecoder` reports zero iterations for the zero-syndrome deterministic fixture. A separate nonzero-syndrome test verifies positive iteration and convergence.

## Self-Check: PASSED

- The end-to-end test failed red before implementation and now reports `2 passed`.
- The documented command completed and printed `outcome=exact` with native convergence.
- The output ledger contains begin followed by terminal with manifest/source/sample/candidate/outcome fields.

## Next Phase Readiness

- Plans 04 and 06 can expand CSS semantics and source evidence independently.
