---
phase: 03-update-rules-and-scheduling
plan: "12"
subsystem: canonical-verification-and-tracing
tags: [schedule-replay, ledger, tamper-evidence, bounded-traces, provenance]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: V3 schedule terminals with qualified progress, complete work vectors, and separate runtime observations
provides:
  - independent V3 deterministic schedule-terminal comparison that resists rehashed semantic tampering
  - bounded local-convergence and schedule-state trace records with explicit selection and missingness
  - preserved V2 flooding grammar and timing-excluded replay equality
affects: [public-schedule-admission, pilot-comparisons, ledger-verification, trace-analysis]
plan_head_before: 85d2d976174f417cf75a156a4b4784f012501e87
commits: 4
actuals:
  tokens: 8985
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - rehashed structural evidence is compared with independently derived deterministic facts instead of treated as self-authenticating
    - trace sidecars retain only quota-bound decoder-visible schedule facts and make selection/missingness explicit
key-files:
  created:
    - .planning/phases/03-update-rules-and-scheduling/03-12-task-1-red-evidence.json
    - .planning/phases/03-update-rules-and-scheduling/03-12-task-2-red-evidence.json
  modified:
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/canonical/tracing.py
    - src/bp_registry/ledger.py
    - tests/test_ledger.py
    - tests/canonical/test_tracing.py
key-decisions:
  - "Replay equality compares V3 deterministic progress/work/candidate/policy/RNG facts, while typed setup/decode measurements remain observational."
  - "Local schedule traces retain only bounded integer progress/order state; physical truth is rejected before a sidecar can be written."
requirements-completed: [SCH-02, SCH-03, SCH-04, SCH-05]
coverage:
  - id: D1
    description: "V3 local-schedule terminal evidence is independently reconstructed and rejects rehashed progress, candidate, policy, or RNG tampering."
    requirement: SCH-04
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_ledger.py tests/test_canonical_cli.py -k 'progress or work or reconstruct or tamper or historical'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Selected local convergence and schedule state are written as bounded, hash-linked, truth-separated trace sidecars."
    requirement: SCH-02
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/test_ledger.py -k 'local or schedule or quota or truth or truncat'"
        status: pass
    human_judgment: false
duration: 8m
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 12: Deterministic Schedule Verification and Bounded Trace Summary

**V3 schedule terminals now resist rehashed semantic tampering through independent deterministic comparison, while selected local convergence and schedule state remain bounded, hash-linked observational evidence.**

## Performance

- **Duration:** 8m
- **Started:** 2026-09-24T10:28:47Z
- **Completed:** 2026-09-24T10:36:10Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Added a V3 schedule-terminal verifier that reconstructs typed progress/work evidence and compares candidate, policy, and purpose-separated RNG facts from independent inputs rather than trusting a recomputed event ID.
- Preserved timing/resource measurements as typed ledger observations outside deterministic equality, and left historical V2 flooding grammar untouched.
- Added local-convergence and schedule-state trace APIs with explicit selection basis, missingness, quota truncation, bounded cursor/order state, confined hash-linked sidecars, and hidden-physical-truth rejection.

## Task Commits

1. **Task 1 RED: failing schedule replay-verifier contract** — `9f9125f` (`test`)
2. **Task 1 GREEN: deterministic V3 schedule-terminal reconstruction** — `d00d155` (`feat`)
3. **Task 2 RED: failing bounded local-trace contract** — `2572675` (`test`)
4. **Task 2 GREEN: bounded local-convergence and schedule-state traces** — `b43815f` (`feat`)

## Files Created/Modified

- `src/bp_registry/canonical/verification.py` — projects typed V3 terminal evidence into deterministic equality fields and verifies it against independently derived facts.
- `src/bp_registry/ledger.py` — enforces the V3 schedule-terminal deterministic field grammar before durable ingestion.
- `src/bp_registry/canonical/tracing.py` — records constrained local schedule observations with selection provenance and truth separation.
- `tests/test_ledger.py` and `tests/canonical/test_tracing.py` — rehashed-tamper, measurement-independence, bounded-trace, truncation, and truth-boundary regressions.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_ledger.py tests/test_canonical_cli.py -k 'progress or work or reconstruct or tamper or historical'` — 12 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/test_ledger.py -k 'local or schedule or quota or truth or truncat'` — 5 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/test_ledger.py tests/test_canonical_cli.py` — 74 passed.

## TDD Gate Compliance

- **Task 1 RED:** `03-12-task-1-red-evidence.json` validates `test_version_three_schedule_verifier_reconstructs_deterministic_claims_after_rehashing` as `RED_EVIDENCE_OK`; `d00d155` makes it pass.
- **Task 2 RED:** `03-12-task-2-red-evidence.json` validates `test_selected_local_schedule_traces_are_bounded_truth_separated_and_explicit` as `RED_EVIDENCE_OK`; `b43815f` makes it pass.

## Decisions Made

- Deterministic replay never treats a terminal hash as proof of semantic correctness; a caller supplies independently reconstructed terminal and deterministic facts for comparison.
- Trace sidecars exclude physical truth and restrict schedule observations to bounded decoder-visible integer progress/order values. Their quota and selection basis are durable evidence.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Public schedule-admission work can bind its re-executed schedule semantics to the V3 verifier and emit D-18 local evidence without changing deterministic replay semantics or historical flooding records.

## Self-Check: PASSED

- Confirmed all five implementation/test artifacts and this summary exist.
- Confirmed task commits `9f9125f`, `d00d155`, `2572675`, and `b43815f` are reachable.
- No stubs, skipped tests, unrun verification, or new network/auth/file-access trust boundary was introduced.

---

*Phase: 03-update-rules-and-scheduling*
*Completed: 2026-09-24*
