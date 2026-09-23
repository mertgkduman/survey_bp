---
phase: 02-canonical-css-execution-and-policy-contracts
plan: "09"
subsystem: canonical-css-researcher-documentation
tags: [css, canonical-bp, cli, profiling, tracing, provenance, research-methods]
requires:
  - phase: 02
    provides: canonical execution, evidence, profiling, tracing, and manifest contracts from plans 02-01 through 02-08
provides:
  - executable no-dependency canonical CLI tutorial and contract reference
  - D-20 profiling and tracing evidence strategy
  - D-26 provisional novelty and depth register
affects: [phase-03, canonical-experiments, profiling, tracing, publication-methods]
tech-stack:
  added: []
  patterns: [documentation-as-executable-contract, public-profile-resolution, version-aware-ledger-query, evidence-maturity-register]
key-files:
  created:
    - docs/canonical-engine.md
    - docs/profiling-and-tracing-strategy.md
    - docs/research-novelty-and-depth-register.md
  modified:
    - src/bp_registry/cli.py
    - src/bp_registry/runner.py
    - tests/test_canonical_cli.py
    - tests/canonical/test_policy_evidence.py
key-decisions:
  - "Public preflight reports both the persisted cpu-float64-spa-v1 manifest label and the resolved binary-spa-flooding-f64-v1 engine convention profile."
  - "The public reconcile command reads canonical v2 structural terminal evidence as a validated query while retaining legacy v1 reconciliation behavior."
  - "Profiling and selective tracing remain provisional, evidence-linked diagnostic methods rather than population, reproduction, or novelty claims."
patterns-established:
  - "Researcher documentation executes the public command path in a disposable output directory and contract-tests printed evidence fields."
  - "Documentation registers preserve explicit cohort eligibility, missingness, truncation, retention, and claim-maturity boundaries."
requirements-completed: [DOC-01]
coverage:
  - id: D1
    description: Executable canonical-engine tutorial and public CLI evidence contract
    requirement: DOC-01
    verification:
      - kind: integration
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial tests/canonical/test_policy_evidence.py
        status: pass
    human_judgment: true
    rationale: Automated checks prove commands and anchors; mathematical exposition and lifecycle readability still require researcher review.
  - id: D2
    description: D-20 profiling/tracing strategy and D-26 provisional novelty register
    requirement: DOC-01
    verification:
      - kind: unit
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_policy_evidence.py tests/canonical/test_profiling.py
        status: pass
    human_judgment: true
    rationale: Tests enforce evidence limitations and implementation identifiers, but precedent adequacy requires continuing literature review.
metrics:
  duration: 16 min
  completed: 2026-09-23
  tasks_completed: 2
  files_changed: 7
status: complete
plan_head_before: 4d38dcde7abf7ec38a07b4c23c8af4e737beef46
commits: 4
actuals:
  tokens: 7911
  tasks: 2
  commits: 4
---

# Phase 02 Plan 09: Canonical CSS Researcher Guidance Summary

**An executable canonical CSS tutorial now exposes checked policy, numerical, lifecycle, work, lineage, and evidence contracts alongside bounded profiling/tracing and provisional-novelty guidance.**

## Performance

- **Duration:** 16 min
- **Completed:** 2026-09-23T09:45:22Z
- **Tasks:** 2/2
- **Files changed:** 7

## Accomplishments

1. Published a no-dependency-fetch tutorial that preflights, runs, reconciles, inspects, and verifies the checked canonical development fixture from the approved environment.
2. Documented deterministic SPA/flooding conventions, explicit seven-role policy composition, capability/lifecycle boundaries, scoped work, lineage, and independent outcome evaluation.
3. Published the D-20 cohort, quota, tracing, missingness, replay, plotting, and retention strategy plus the D-26 evidence/precedent/claim-maturity register.
4. Added executable documentation contracts and public CLI fields for resolved numerical profiles and canonical structural-ledger reconciliation.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial tests/canonical/test_policy_evidence.py tests/canonical/test_profiling.py` → `11 passed`.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` → `126 passed`.
- Both task RED evidence records passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.

## Task Commits

1. **Task 1: Write and execute the canonical engine tutorial/reference**
   - `e38ab89` test: add canonical tutorial contracts
   - `c58c01d` feat: publish executable canonical engine guide
2. **Task 2: Publish profiling/tracing strategy and provisional novelty register**
   - `d173941` test: add strategy and novelty contracts
   - `8754a19` docs: publish profiling and novelty registers

## Decisions Made

- Preflight exposes the persisted manifest label and fully materialized numerical conventions separately, making the historical public/profile naming distinction inspectable rather than silently conflated.
- Canonical v2 reconciliation is a read-only validated terminal-row query; legacy v1 ledgers retain their repair-capable reconciliation path.
- D-20/D-26 examples are development and diagnostic evidence only. They cannot become population estimates, assessed reproduction, or novelty claims without prespecified campaign evidence and a corpus recheck.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Completed the public canonical reconcile and profile-inspection path.**

- **Found during:** Task 1 tutorial execution.
- **Issue:** The planned public `reconcile` sequence rejected canonical v2 structural events, and preflight did not expose the resolved numerical conventions needed to map printed fields to the documented engine profile.
- **Fix:** Added a validated canonical terminal-row query to the public reconcile command and exposed persisted plus resolved numerical profile evidence and policy bindings from canonical preflight.
- **Files modified:** `src/bp_registry/cli.py`, `src/bp_registry/runner.py`, `tests/test_canonical_cli.py`, `docs/canonical-engine.md`.
- **Verification:** Focused tutorial test, policy-evidence tests, and the full 126-test suite pass.
- **Committed in:** `c58c01d`.

**Total deviations:** 1 auto-fixed (Rule 2).

## Known Stubs

None.

## Threat Review

- Documentation uses checked relative project paths and a disposable output directory; it does not print environment secrets or private absolute paths.
- The tutorial and register preserve `canonical_implemented`, `development_fixture`, and `not_assessed` limitations. Contract tests prevent promotion to reproduction, population, or established-novelty language.
- Trace digests are described only as bounded content identity/integrity for replay, not as authenticity or performance evidence.

## TDD Gate Compliance

- Task 1 RED (`e38ab89`) preceded GREEN (`c58c01d`); `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- Task 2 RED (`d173941`) preceded GREEN (`8754a19`); `check tdd-red-evidence` returned `RED_EVIDENCE_OK`.

## Next Phase Readiness

Phase 3 can use the checked tutorial and evidence-maturity boundaries when extending canonical policy families without relabelling development diagnostics as controlled or source-faithful results.

## Self-Check: PASSED

All seven planned documentation/source/test artifacts, the summary artifact, and task commits `e38ab89`, `c58c01d`, `d173941`, and `8754a19` exist.
