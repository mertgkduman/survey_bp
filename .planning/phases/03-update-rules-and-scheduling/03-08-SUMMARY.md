---
phase: 03-update-rules-and-scheduling
plan: "08"
subsystem: matched-policy-pilots
tags: [css, bp, schedules, min-sum, provenance, work-accounting, runtime]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: promoted update rules, local schedules, code artifacts, and cluster-artifact qualifier
provides:
  - bounded matched BB-144, exact B1, and generated HGP public pilot manifests and ledgers
  - 19 independently verified policy terminals with physical-sample, graph, logical, and policy identities
  - replayable configuration-scoped generated parameter assignment under flooding
  - explicit C2V-cap and qualified-iteration budget views, full work, and scoped setup/decode timing
affects: [03-15, UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05]
plan_head_before: 349058e
actuals:
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - public preflight/canonical/verify-run commands generate and independently replay every retained pilot
    - generated assignments use a graph-bound configuration seed separated from physical sampling and schedule order
    - observational timing remains scoped evidence, separate from deterministic work and outcome checks
key-files:
  created:
    - scripts/run_phase3_pilots.py
    - data/manifests/phase3-pilot-bb144.json
    - data/manifests/phase3-pilot-b1.json
    - data/manifests/phase3-pilot-hgp-gallager.json
    - data/results/phase3-pilots/result.json
    - tests/test_phase3_pilots.py
  modified:
    - src/bp_registry/cli.py
    - src/bp_registry/manifests.py
    - src/bp_registry/runner.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/updates.py
    - src/bp_registry/canonical/verification.py
    - docs/canonical-engine.md
key-decisions:
  - "Pilot evidence is always pilot_adaptation/not_assessed; one-shot results do not rank policies or reproduce published curves."
  - "Configuration-scoped generated NMS/OMS assignment is executable under flooding; attempt/source-iteration generation is rejected at public preflight until integrated."
  - "Setup and decode timings are observational nanosecond measurements with explicit scopes; public preflight, artifact loading, and ledger I/O are excluded."
requirements-completed: [UPD-01, UPD-02, UPD-03, SCH-02, SCH-03, SCH-04, SCH-05]
duration: 2h
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 08: Matched Policy Pilot Summary

**Nineteen bounded policy runs across BB-144, exact B1, and generated (3,4)-regular HGP now have durable public manifests, ledgers, results, and independent verification.**

## Accomplishments

- Ran four flooding update variants on BB-144, seven B1 schedule/parameter variants, and eight HGP schedule/parameter variants. All use matched physical sample identities within code and shot, independent policy/order streams, one prespecified shot, and one qualified iteration. Undefined randomized scheduling is rejected before sampling.
- Retained exact artifact and logical-matrix hashes, code/policy/composition identities, terminal outcomes and missingness, schedule-qualified iterations, full atomic work, profile evidence, and both declared C2V-cap and iteration-limit views. Setup and decode timing is measured in the same terminal ledger; the scopes and excluded preflight/I/O time are documented.
- Wired configuration-scoped generated parameter assignments into public execution and independent replay. The HGP seeded NMS run records its generator/version, graph hash, derived seed identity, resolved assignment, and exploratory provenance. Unsupported refresh scopes fail at preflight.
- Added an aggregate `verify-run` path that re-verifies each run, matches the combined ledger and terminal rows exactly to the per-run evidence, checks graph/logical/policy/sample identities, and enforces pilot/adaptation/not_assessed claims.

## Verification

- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — **277 passed**.
- `PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/phase3-pilots` — **19 verified terminals**, matched samples true.
- `tests/test_phase3_pilots.py` — both focused tests passed; `tests/canonical/test_schedule_semantics.py tests/canonical/test_work_accounting.py` — 17 passed.
- Task 2 RED evidence passed `gsd-tools check tdd-red-evidence`; `git diff --check` passed.

## Task Commits

1. `255b503` — Task 1 failing BB-144 public pilot test.
2. `3546ed8` — Task 1 BB-144 runner and verified evidence.
3. `7169817` — Task 2 failing B1/HGP matrix test and RED evidence.
4. `31ce871` — Task 2 B1/HGP schedule pilots, generated assignment execution, and strict aggregate verification.
5. `4a69037` — same-ledger setup/decode timing and regenerated verified evidence.

## Deviations and Limits

- The task 2 executor exhausted its context after generating the first durable run. The orchestrator completed the atomic commits, fixed the generated-assignment execution gap, added scoped timing, and reran the gates.
- The first generated HGP attempt failed before a terminal because the kernel did not yet consume generated assignments. Its incomplete ledger is retained at `03-08-seeded-integration-failure.jsonl`; the corrected run independently verifies.
- The pilots are one-shot diagnostic adaptations. `outcome=null` where stopping produced no candidate is retained as missingness, never inferred as success or failure. The two budget views describe the same retained work and do not claim equal total cost. Preflight, artifact loading, and ledger I/O are outside setup/decode timing.

## Next Phase Readiness

Plan 03-15 can read the retained aggregate without recomputing decoder outcomes and must preserve the pilot/adaptation/not_assessed labels and timing scopes. Plan 03-09 still requires authoritative Moradi clustered RL-S Q-table and ordered partition bytes before SCH-06 can proceed.

## Self-Check: PASSED

- Required manifests, 19 per-run directories, combined ledger/result, tests, and documentation are present.
- The four task commits plus timing correction are reachable; the worktree is clean after this summary commit.

---
*Phase: 03-update-rules-and-scheduling*
*Plan: 08*
*Completed: 2026-09-24*
