---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "12"
subsystem: canonical-css-public-evidence
tags: [canonical-bp, profiling, trace-admission, native-isolation, provenance, css-syndrome]
requires:
  - phase: 02-10
    provides: executable public baseline with scoped work accounting
  - phase: 02-11
    provides: owner-authenticated structural evidence and current-attempt lineage
provides:
  - exception-safe profiling and identity-bound replay eligibility
  - typed public runtime/resource evidence with fail-closed trace admission
  - canonical execution independent of the optional native adapter
  - regenerated verified checked canonical ledger and result
affects: [phase-02-verification, canonical-results, profiling-and-tracing]
tech-stack:
  added: []
  patterns: [profiler-owned-global-cleanup, typed-observational-profile, lazy-native-adapter, cli-generated-checked-evidence]
key-files:
  created: []
  modified: [src/bp_registry/canonical/profiling.py, src/bp_registry/canonical/execution.py, src/bp_registry/manifests.py, src/bp_registry/runner.py, docs/canonical-engine.md, tests/canonical/test_profiling.py, tests/canonical/test_policy_evidence.py, tests/test_canonical_cli.py, data/results/canonical-three-qubit-development/events.jsonl, data/results/canonical-three-qubit-development/result.json]
key-decisions:
  - "Canonical profiles are typed observation facts and cannot affect decoding, stopping, selection, or evaluation."
  - "Public trace configurations remain rejected unless the engine can emit their promised bounded evidence."
  - "Checked canonical artifacts are produced directly by the public CLI so result ledger paths remain truthful."
patterns-established:
  - "Canonical dependency checks discover only project-owned runtime requirements; the native adapter loads inside native execution."
  - "Replay population claims require cohort and sample identity equality before semantic agreement is considered."
requirements-completed: [ENG-01, ENG-04, LED-02, LED-03, LED-04, DOC-01]
coverage:
  - id: D1
    description: Profiler cleanup and replay eligibility preserve global instrumentation ownership and identity-bound population claims.
    requirement: LED-02
    verification:
      - kind: unit
        ref: tests/canonical/test_profiling.py
        status: pass
    human_judgment: false
  - id: D2
    description: Public profile plans emit typed evidence, unsupported traces stop before a ledger, and canonical execution avoids the native adapter.
    requirement: LED-03
    verification:
      - kind: integration
        ref: tests/test_canonical_cli.py::test_public_profile_plan_emits_typed_attempt_evidence
        status: pass
      - kind: integration
        ref: tests/test_canonical_cli.py::test_enabled_public_trace_plan_is_rejected_before_ledger
        status: pass
      - kind: integration
        ref: tests/test_canonical_cli.py::test_canonical_preflight_and_run_do_not_import_ldpc
        status: pass
    human_judgment: false
  - id: D3
    description: Tutorial convention and checked ledger/result evidence are regenerated through the public canonical CLI.
    requirement: DOC-01
    verification:
      - kind: unit
        ref: tests/canonical/test_policy_evidence.py::test_canonical_tutorial_has_required_contract_anchors
        status: pass
      - kind: e2e
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development
        status: pass
    human_judgment: false
metrics:
  duration: 11 min
  completed: 2026-09-23
status: complete
plan_head_before: 6bf6aaf1440d06da487ae71b3c4364883079a4d4
commits: 6
actuals:
  tokens: 18811
  tasks: 3
  commits: 6
---

# Phase 02 Plan 12: Canonical Closure Evidence Summary

**Exception-safe profiling, fail-closed public tracing, native-adapter isolation, and freshly verified CSS canonical evidence.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-23T22:23:45Z
- **Completed:** 2026-09-23T22:34:27Z
- **Tasks:** 3/3
- **Files modified:** 10

## Accomplishments

1. Restored profiler-owned `tracemalloc` on successful and exceptional actions without disturbing caller-owned tracing, and bound replay cohorts to their selected sample identity.
2. Materialized public profile controls as typed runtime and terminal evidence, rejected non-off public trace plans before sampling, and delayed native adapter loading until an explicit native run.
3. Corrected the tutorial to `s_Z = H_Z e_X (mod 2)` and regenerated both checked evidence artifacts directly through the public canonical CLI.

## Task Commits

1. **Task 1: Make profiling cleanup and replay eligibility exception-safe**
   - `efce647` test RED
   - `a9538c8` feat GREEN
2. **Task 2: Honor the public profile plan, fail closed on unsupported tracing, and isolate native imports**
   - `5c9de4f` test RED
   - `53ee636` feat GREEN
3. **Task 3: Correct the tutorial and publish freshly verified closure evidence**
   - `10b4eaa` test RED
   - `59db997` docs GREEN

## Files Created/Modified

- `src/bp_registry/canonical/profiling.py` — cleans profiler-owned allocation tracing on every action exit and validates replay sample identity.
- `src/bp_registry/canonical/execution.py` — wraps admitted canonical attempts in typed local profiling.
- `src/bp_registry/manifests.py` and `src/bp_registry/runner.py` — reject unsupported public tracing and isolate native adapter imports.
- `docs/canonical-engine.md` — states the executable Z-check syndrome convention and current profile-evidence semantics.
- `data/results/canonical-three-qubit-development/events.jsonl` and `result.json` — fresh CLI-generated structural ledger and derived checked result.

## Decisions Made

- Profiling observations are recorded as typed evidence but cannot influence decoder semantics.
- A public trace plan is accepted only when the public engine can honor it; the current engine admits `off` only.
- Regenerated checked evidence preserves the actual deterministic outcomes: shot 0 is `logical_failure` and shot 1 is `exact`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Aligned stale fixed tutorial outcomes with the current manifest-derived samples.**

- **Found during:** Task 3 full-suite verification
- **Issue:** The old tutorial assertion expected two exact outcomes after the manifest migration changed deterministic sample identities.
- **Fix:** Reconstructed checked evidence from the current manifest and documented/asserted its actual `logical_failure`, `exact` terminal sequence.
- **Files modified:** `docs/canonical-engine.md`, `tests/test_canonical_cli.py`, `data/results/canonical-three-qubit-development/events.jsonl`, `data/results/canonical-three-qubit-development/result.json`
- **Committed in:** `59db997`

**Total deviations:** 1 auto-fixed regression.

## Known Stubs

None.

## Verification

- Focused profiling suite: `10 passed`.
- Public profile, trace-admission, native-isolation, and native reference suite: `12 passed`.
- Clean temporary public canonical run and `verify-run`: 2 terminal rows with current manifest identity, `bp_calls: 1`, lineage, ownership, typed profile, and `not_assessed` evidence.
- Checked-directory public canonical regeneration and `verify-run`: passed; `result.json` names `data/results/canonical-three-qubit-development/events.jsonl`.
- Complete suite: `145 passed`.

## TDD Gate Compliance

- Task 1 RED and GREEN commits: `efce647` → `a9538c8`.
- Task 2 RED and GREEN commits: `5c9de4f` → `53ee636`.
- Task 3 RED and GREEN commits: `10b4eaa` → `59db997`.

## Self-Check: PASSED

All ten plan artifacts exist and all six task commits are present in Git history.
