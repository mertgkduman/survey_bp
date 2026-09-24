---
phase: 04-memory-policies-and-relay-bp
plan: "04"
subsystem: canonical-manifests
tags: [python, pydantic, canonical-engine, memory-policy, schema, cli, tdd]
requires:
  - phase: 04-03
    provides: ordered memory bindings, closed compatibility admission, and replayable memory lifecycle contracts
provides:
  - strict CanonicalExperimentV4 public memory-composition manifest
  - V4 public preflight, canonical execution, and verification dispatch
  - generated V4 schema and executable lifecycle documentation
affects: [04-05, canonical-manifests, memory-policy, relay-bp, public-replay]
tech-stack:
  added: []
  patterns: [versioned public manifest extension, pre-artifact compatibility rejection, canonical-v4-to-v3 compact execution projection]
key-files:
  created: [data/manifests/schema-canonical-v4.json]
  modified:
    - src/bp_registry/manifests.py
    - src/bp_registry/cli.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/compatibility.py
    - src/bp_registry/runner.py
    - docs/canonical-engine.md
    - tests/test_manifest.py
    - tests/test_canonical_cli.py
key-decisions:
  - "CanonicalExperimentV4 extends the complete V3 public evidence contract and stores ordered memory bindings separately from the fixed seven policy roles."
  - "V4 validation rejects incompatible memory operands before artifact loading; the preflight report persists accepted binding order and compatibility evidence."
  - "The compact kernel preserves its existing V3 execution grammar while public V4 identity remains bound to the full memory manifest."
patterns-established:
  - "Public version changes retain historical manifest routing and use explicit version projection only at the compact engine boundary."
requirements-completed: [MEM-01, MEM-02, MEM-03, MEM-04, MEM-05]
coverage:
  - id: D1
    description: Strict public V4 manifests admit compatible repeated ordered bindings and reject unsupported target/boundary operands before loading artifacts.
    requirement: MEM-01
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py tests/test_canonical_cli.py -k 'canonical_v4 or memory_composition or historical_v2 or historical_v3'"
        status: pass
    human_judgment: false
  - id: D2
    description: V4 manifests use public CLI preflight, canonical execution, and verify-run while preserving V2/V3 execution semantics.
    requirement: MEM-05
    verification:
      - kind: integration
        ref: "tests/test_canonical_cli.py::test_canonical_v4_memory_composition_preflights_runs_and_verifies_publicly"
        status: pass
    human_judgment: false
  - id: D3
    description: Generated V4 schema and canonical-engine guide define binding identity, lifecycle, aliases, labels, rejection behavior, and public commands.
    requirement: MEM-04
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py -k 'schema_v4 or documented or round_trip'"
        status: pass
    human_judgment: false
metrics:
  duration: "11m"
  completed: "2026-09-24"
status: complete
actuals:
  tokens: 64027
  tasks: 2
  commits: 3
plan_head_before: 201d035bf5db5e5d2a60b7916f79fe9528ac00e1
commits: 3
---

# Phase 04 Plan 04: Public V4 Memory Manifest Summary

CanonicalExperimentV4 makes strict ordered memory compositions available through public preflight, canonical execution, replay verification, generated schema, and executable documentation.

## Accomplishments

- Added a strict V4 contract that preserves the complete V3 experiment/evidence shape and adds ordered, owner-separated `MemoryCompositionSpec` bindings.
- Routed V4 through public CLI and canonical runner paths; accepted bindings and compatibility evidence appear in the public preflight report while the compact engine retains its established V3 grammar.
- Rejected invalid memory target/boundary combinations before artifact loading or sampling, with a stable compatibility reason.
- Generated the JSON schema and documented lifecycle fields, binding order, source labels, EWA/Relay equivalence, repeated bindings, and public commands.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py tests/test_canonical_cli.py -k 'canonical_v4 or memory_composition or historical_v2 or historical_v3'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py -k 'schema_v4 or documented or round_trip'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/test_manifest.py` — 45 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py` — all 67 tests passed when run in ordered groups of nine to fit the execution environment's 30-second command window.

## Task Commits

1. **Task 1: Preflight and execute CanonicalExperimentV4 memory compositions**
   - `1657978` `test(04-04): add failing V4 public memory contracts`
   - `70b2dd8` `feat(04-04): admit public V4 memory compositions`
2. **Task 2: Export and document the V4 memory contract**
   - `5994f25` `docs(04-04): publish V4 memory manifest contract`

## Decisions Made

- V4 adds memory bindings without changing the fixed seven-role policy object, allowing repeated policy kinds while retaining binding-private history ownership.
- V4 public identity includes the complete memory composition. The compact execution input uses schema version 3 only because the existing kernel contract has not changed.
- `binary_spa` is a valid compatibility update-rule identifier alongside the preexisting symbolic names; JSON memory-boundary labels are explicitly converted to their strict enums.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking integration] Extended the runner's V4 dispatch and compact projection.**
- **Found during:** Task 1 public CLI execution.
- **Issue:** The plan's public V4 manifest can inherit the V3 evidence runner, but its schema version would otherwise reach the compact V4 structural contract, which has a different preexisting shape.
- **Fix:** Added explicit V4 public routing and projected only the compact kernel input to the existing V3 execution grammar; V4's full digest remains public evidence.
- **Files modified:** `src/bp_registry/runner.py`
- **Commit:** `70b2dd8`

**2. [Rule 1 - Bug] Accepted strict JSON boundary labels and the existing `binary_spa` update identifier.**
- **Found during:** Task 1 focused V4 validation.
- **Issue:** The existing strict enum fields rejected declared JSON strings, and compatibility validation omitted the project's baseline `binary_spa` identifier.
- **Fix:** Added explicit JSON-to-enum validators and registered `binary_spa` as a supported memory compatibility operand.
- **Files modified:** `src/bp_registry/canonical/contracts.py`, `src/bp_registry/canonical/compatibility.py`
- **Commit:** `70b2dd8`

## Known Stubs

None.

## Self-Check: PASSED

Confirmed every declared production, schema, documentation, and test artifact exists. Confirmed task commits `1657978`, `70b2dd8`, and `5994f25` are present in git history.
