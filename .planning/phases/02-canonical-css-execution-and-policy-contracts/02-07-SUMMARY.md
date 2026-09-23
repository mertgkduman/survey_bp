---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "07"
subsystem: canonical-css-profiling-and-replay
tags: [css, profiling, replay, cohorts, semantic-tracing, provenance]
requires:
  - phase: 02-04
    provides: qualified runtime and resource measurement facts
  - phase: 02-05
    provides: bounded canonical trace sidecars and immutable lineage
provides:
  - typed local standard-library profiling with explicit availability
  - prespecified representative and diagnostic cohort evidence
  - clean/profile replay links with timing-independent semantic agreement
affects: [controlled-comparisons, profiling-docs, statistical-evidence, tracing]
tech-stack:
  added: []
  patterns: [typed-missingness, allowlisted-context, paired-replay, cohort-disclosure, semantic-digest]
key-files:
  created:
    - src/bp_registry/canonical/profiling.py
    - tests/canonical/test_profiling.py
  modified:
    - src/bp_registry/canonical/tracing.py
key-decisions:
  - "Local standard-library profiling is default-on but distinguishes process-local observed facts, unavailable adapters, and separately measured adapter overhead."
  - "Only pre-outcome representative paired cohorts with an inclusion probability and semantic agreement are eligible for profiling population estimates."
  - "Replay comparison binds clean/profile, manifest, sample, decoder-randomness, and order identities while comparing semantic fields independently of timing."
requirements-completed: [LED-03]
coverage:
  - id: D1
    description: "Default-on local timing, CPU, RSS, allocation, allowlisted-context, disabled, unavailable, and strict-required profiling behavior."
    requirement: LED-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_profiling.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Prespecified representative and diagnostic cohort claims, paired replay provenance, semantic agreement, divergence retention, and timing-independent trace digest."
    requirement: LED-03
    verification:
      - kind: unit
        ref: "tests/canonical/test_profiling.py tests/canonical/test_tracing.py"
        status: pass
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q"
        status: pass
    human_judgment: false
metrics:
  duration: 10 min
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 3
status: complete
plan_head_before: 34f548f269079ab199c706f7e520c0e6deec8a7e
commits: 4
actuals:
  tokens: 8190
  tasks: 2
  commits: 4
---

# Phase 02 Plan 07: Scientifically Interpretable Profiling and Replay Summary

Canonical CSS profiling now records process-local standard-library measurements with explicit missingness and links prespecified clean/profile cohorts through timing-independent semantic replay checks.

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-23T09:06:20Z
- **Completed:** 2026-09-23T09:16:20Z
- **Tasks:** 2
- **Files changed:** 3

## Accomplishments

1. Added default-on, opt-out local profiling for wall time, process CPU time, platform-qualified `RUSAGE_SELF` RSS, concurrency, and optional representative Python allocation peaks. Every unavailable adapter is a typed missing fact, strict plans fail closed, adapter overhead is isolated, and only valid numeric thread-count settings from an explicit allowlist are retained.
2. Added clean, representative, and diagnostic cohort records; representative pair records retain strata and inclusion probability before outcomes, while diagnostic tail records are permanently ineligible for population estimates.
3. Added immutable clean/profile replay links with manifest, sample, decoder-randomness, ordering, cohort, overhead, and retention evidence. Semantic comparison checks candidate, termination, work, lineage, and trace digest while excluding measurement fields; divergences are retained as diagnostics rather than measuring the clean execution.

## Verification

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_profiling.py tests/canonical/test_tracing.py` → `14 passed`.

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` → `120 passed`.

## Task Commits

1. **Task 1: Measure local runtime/resources with typed availability and overhead**
   - `31ebaa0` test: failing local profiling contracts
   - `636c5d9` feat: typed local profiler
2. **Task 2: Prespecify clean, representative, and diagnostic replay cohorts**
   - `74090e6` test: failing replay cohort contracts
   - `b9890e7` feat: representative replay evidence

## Decisions Made

- Process-local wall/CPU/RSS facts are qualified by method, scope, unit, precision, and raw RSS context; child-process RSS and ambiguous platform normalization remain unavailable rather than guessed.
- The full clean population owns outcome/runtime estimates; detailed profiling can support population claims only through a prespecified representative paired cohort with inclusion probability and semantic agreement.
- Timing and resource facts remain durable observations but never participate in replay semantic identity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Restrict retained thread environment values to valid counts**

- **Found during:** Task 2 threat-model review.
- **Issue:** An allowlisted thread variable could still contain an arbitrary non-path string, allowing accidental retention of an unrelated value.
- **Fix:** Retain only positive decimal thread-count values from the four named concurrency variables; omit all other values.
- **Files modified:** `src/bp_registry/canonical/profiling.py`, `tests/canonical/test_profiling.py`.
- **Verification:** Focused profiling/tracing tests and the full 120-test suite pass.
- **Commit:** `b9890e7`.

**Total deviations:** 1 auto-fixed (Rule 2).

## Known Stubs

None.

## Threat Review

- Profiler environment capture is restricted to validated numeric values from an explicit concurrency allowlist; no arbitrary environment value, secret, hostname, or path is serialized.
- Cohort records make representative inclusion probability and diagnostic selection reason durable, preventing tail replays from being summarized as population estimates.
- Replay links require distinct run IDs and retain mismatches as diagnostic evidence; trace semantic digests exclude measurement-only fields without changing trace control flow.

## TDD Gate Compliance

- Task 1 RED (`31ebaa0`) preceded GREEN (`636c5d9`); `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- Task 2 RED (`74090e6`) preceded GREEN (`b9890e7`); `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.

## Next Phase Readiness

Plan 08 can persist canonical execution evidence using the same qualified profile facts and can label detailed traces/replays without conflating diagnostic depth with population performance.

## Self-Check: PASSED

All three planned source/test artifacts and task commits `31ebaa0`, `636c5d9`, `74090e6`, and `b9890e7` exist. The focused profiling/tracing suite passes with 14 tests.
