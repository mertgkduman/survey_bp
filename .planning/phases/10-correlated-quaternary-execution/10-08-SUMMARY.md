---
phase: 10-correlated-quaternary-execution
plan: "08"
subsystem: quaternary-qbpgd-execution
tags: [python, qbp, qbpgd, provenance, replay, four-state-decoding]
requires:
  - phase: 10-07
    provides: resolved quaternary composition and component-versus-run fidelity contracts
provides:
  - Persistent four-state Q-BPGD rounds with literal fixation, stable ties, exact work, and replay
  - Public canonical-adaptation Q-BPGD execution with source-component provenance retained separately
affects: [phase-10-mbp4, phase-10-asced, phase-11-quaternary-evaluation]
actuals:
  tokens: 8460
  tasks: 2
  commits: 4
plan_head_before: 39df9e98dbc59e1f8c398f3ee9320475756aee20
tech-stack:
  added: []
  patterns: [persistent session-owned message buffers, literal-prior evidence, component-versus-run fidelity, deterministic ledger replay]
key-files:
  created:
    - src/bp_registry/quaternary/qbpgd.py
    - tests/canonical/quaternary/test_bpgd.py
  modified:
    - src/bp_registry/quaternary/kernel.py
    - src/bp_registry/quaternary/execution.py
    - src/bp_registry/runner.py
    - tests/canonical/quaternary/test_public_execution.py
key-decisions:
  - "Continued QBP buffers are an explicit D-14 canonical interpretation, so every Q-BPGD run remains canonical_adaptation even with source-backed depolarizing setup components."
  - "Q-BPGD persists literal (1-epsilon, epsilon, epsilon, epsilon) fixation weights and a separately recorded common-sum normalized decoder prior."
requirements-completed: [QBP-04]
coverage:
  - id: D1
    description: Persistent Q-BPGD selects from four-state marginals, preserves literal fixation evidence, caps work, and rejects replay tampering.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_bpgd.py
        status: pass
    human_judgment: false
  - id: D2
    description: Public Q-BPGD runs retain source-backed component evidence alongside canonical-adaptation run identity and replayable ledgers.
    requirement: QBP-04
    verification:
      - kind: integration
        ref: tests/canonical/quaternary/test_public_execution.py#qbpgd
        status: pass
    human_judgment: false
duration: 7m
completed: 2026-10-07
status: complete
---

# Phase 10 Plan 08: Q-BPGD Execution Summary

Persistent four-state Q-BPGD with literal fixation evidence, deterministic replay, and public canonical-adaptation provenance.

## Accomplishments

- Added a Q-BPGD controller that continues its committed QBP edge buffers across D-14 decimation rounds, uses normalized I/X/Y/Z posterior reliability, and persists stable qubit and Pauli ties.
- Preserved the source's literal D-15 fixation vector and its separately normalized decoder prior, plus every original-syndrome check, work leaf, terminal state, and replay identity.
- Routed resolved public Q-BPGD bindings through the controller and wrote component fidelity, run fidelity, source identity, round evidence, outcomes, and deterministic replay into the event ledger.

## Task Commits

1. Task 1 RED — `0b49cf1` `test(10-08): add failing Q-BPGD controller contract`
2. Task 1 GREEN — `43a6d82` `feat(10-08): implement persistent Q-BPGD rounds`
3. Task 2 RED — `caeb9b2` `test(10-08): add failing public Q-BPGD evidence contract`
4. Task 2 GREEN — `b818a49` `feat(10-08): expose replayable public Q-BPGD runs`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py -k 'reliability or undecimated or fixation or raw or normalized or continuation or run_fidelity or component_identity or tie or early or round_cap or work or replay or truth_boundary' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py tests/canonical/quaternary/test_public_execution.py -k 'qbpgd and (source_component or run_fidelity or depolarizing_adaptation or general_prior_adaptation or installed_cli or ledger or outcome or replay or unverified or unsupported)' -x` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` — 119 passed.

## TDD Gate Compliance

- Task 1 RED evidence: `.gsd/tdd-evidence/10-08-task-1-red.json` verified as `RED_EVIDENCE_OK` before the controller implementation.
- Task 2 RED evidence: `.gsd/tdd-evidence/10-08-task-2-red.json` verified as `RED_EVIDENCE_OK` before public dispatch implementation.

## Decisions Made

- Source-backed Algorithm 3, fixation, and depolarizing setup component IDs remain separate from the complete D-14 continued-message trajectory, whose run fidelity is always `canonical_adaptation`.
- Public general-joint priors carry the resolver's additional `general_joint_prior` adaptation reason; the unresolved author-code identity remains `unverified`.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 3 - Blocking issue] Added QBP session continuation primitives.**
   - **Found during:** Task 1.
   - **Issue:** The existing session stopped at convergence and had no safe way to replace one decoder-visible prior while retaining committed edge buffers.
   - **Fix:** Added exact-block sweeping, stable session digesting, and validated single-prior replacement without resetting C2V/V2C buffers.
   - **Files modified:** `src/bp_registry/quaternary/kernel.py`.
   - **Verification:** Q-BPGD contracts and the full quaternary suite passed.

2. **[Rule 3 - Blocking issue] Routed the public manifest entry point to the resolved Q-BPGD controller.**
   - **Found during:** Task 2.
   - **Issue:** The existing public runner always dispatched the baseline tracer, so it could not emit Q-BPGD candidate, fidelity, or round evidence.
   - **Fix:** Added resolved-Q-BPGD dispatch and replayable result fields to `runner.py`.
   - **Files modified:** `src/bp_registry/runner.py`.
   - **Verification:** Public Q-BPGD integration tests and deterministic ledger replay passed.

## Known Stubs

None.

## Next Phase Readiness

MBP4 and aSCED can reuse the public resolved-composition boundary while retaining their own policy-specific recurrence and source qualification gates.

## Self-Check: PASSED

- Confirmed the Q-BPGD controller, direct contracts, and summary exist on disk.
- Confirmed all four TDD task commits exist in repository history.
