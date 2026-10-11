---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "01"
subsystem: campaign-evidence
tags: [python, pydantic, provenance, css, source-qualification]
requires:
  - phase: 08-reproducible-campaigns-and-statistical-assessment
    provides: immutable campaign target and content-addressed receipt conventions
provides:
  - strict source-experiment identities with ordered CSS and logical evidence
  - native-reference assessments with typed unavailable measurements
  - digest-bound source-faithful eligibility receipts
affects: [campaigns, literature_policies, CSS reproduction, publication reporting]
tech-stack:
  added: []
  patterns: [strict immutable Pydantic receipts, content-addressed evidence, explicit missingness]
key-files:
  created: []
  modified:
    - src/bp_registry/campaigns/targets.py
    - tests/test_campaign_targets.py
key-decisions:
  - "Source-faithful eligibility requires complete D-02 identity evidence and a successful native assessment."
  - "Unavailable native work, runtime, and counters carry reasons and cannot serialize as zero."
patterns-established:
  - "Later evidence supersedes a qualification only through a new receipt linked to the earlier digest."
requirements-completed: [EVAL-01, EVAL-02]
actuals:
  tokens: 6319
  tasks: 2
  commits: 4
plan_head_before: 1b667f89b670167272c024391c6a0b8b7717650f
coverage:
  - id: D1
    description: Strict ordered source-experiment identity and confined evidence snapshots.
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: tests/test_campaign_targets.py#test_source_experiment_identity_binds_ordered_identity_and_rejects_incomplete_faithful_tuple
        status: pass
    human_judgment: false
  - id: D2
    description: Typed native availability and source-faithful eligibility gate.
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: tests/test_campaign_targets.py#test_qualification_receipt_rejects_discrepant_or_incomplete_native_evidence_and_preserves_prior_receipt
        status: pass
    human_judgment: false
duration: 2m
completed: 2026-10-11
status: complete
---

# Phase 09 Plan 01: Source Qualification Receipts Summary

**Digest-bound CSS source identities and native-reference assessments prevent incomplete or unavailable evidence from becoming source-faithful execution.**

## Performance

- **Duration:** 2m
- **Started:** 2026-10-11T19:12:38Z
- **Completed:** 2026-10-11T19:14:36Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added strict source-experiment identities for the full D-02 tuple, including ordered code/logical artifacts, paper locator, source denominator, stopping evidence, author implementation evidence, executable policy digest, and blockers.
- Added confined, non-symlink source reads with a size limit checked before content is read, and content-bound snapshot digests.
- Added native assessment states for unverified, non-executable, executed, and discrepant references; unavailable metrics require a reason and have no numeric value.
- Added qualification receipts that bind target, source identity, native evidence, blockers, eligibility, and an optional earlier receipt digest.

## Task Commits

1. **Task 1: Bind one selected target to its complete source-experiment identity**
   - `cdf306c` `test(09-01): add failing source identity tests`
   - `fb42b28` `feat(09-01): bind strict source experiment identities`
2. **Task 2: Add native assessment states and the source-faithful eligibility gate**
   - `26124e0` `test(09-01): add failing native qualification tests`
   - `7201f3b` `feat(09-01): gate source-faithful native qualification`

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -x` — 12 passed.
- Task 1 focused command — 8 passed, 4 deselected.
- Task 2 focused command — 4 passed, 8 deselected.
- Both TDD RED evidence records passed `gsd-tools check tdd-red-evidence` before implementation.

## Decisions Made

- Faithful eligibility is an exact derived predicate: complete source identity, an `executed` native receipt, and no qualification blockers are all required.
- A later verified author artifact creates a distinct qualification receipt and can retain the earlier receipt digest; it never rewrites unavailable history.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Later campaign and publication plans can reference the new receipt digests without treating the current literature inventory or canonical adaptations as source-faithful evidence.

## Self-Check: PASSED

- Found `src/bp_registry/campaigns/targets.py` and `tests/test_campaign_targets.py`.
- Found all four task commits in the repository history.
