---
phase: 01-evidence-registry-and-native-css-baseline
plan: 09
subsystem: native-css-pilot-evidence
tags: [css, ldpc, product-sum, jsonl, provenance, pilot-adaptation]
requires:
  - plan: 01-05
    provides: durable final-row shot ledger and reconciliation
  - plan: 01-06
    provides: mapped source experiment and separate pilot identity
  - plan: 01-07
    provides: strict manifests and immutable preflight
  - plan: 01-08
    provides: verified BB-144 matrices and logical basis
provides:
  - selected-artifact-only CLI preflight and 32-shot native BP pilot command
  - checked-in final-row ledger and result reconstructed from the ledger
  - bidirectionally linked reference-executable pilot record with mapped-only paper maturity
affects: [phase-1-uat, css-code-capacity, evidence-registry, later-statistical-assessment]
tech-stack:
  added: []
  patterns: [selected-artifact CLI binding, final-row-derived result reconstruction, idempotent fixed-shot pilot execution]
key-files:
  created: [src/bp_registry/cli.py, data/manifests/selected-css-pilot_adaptation-not_assessed.json, data/results/pilot_adaptation-not_assessed/events.jsonl, data/results/pilot_adaptation-not_assessed/result.json]
  modified: [src/bp_registry/runner.py, data/evidence/seed-records.json, docs/phase1-pilot.md, tests/test_reference_smoke.py, tests/test_evidence.py, .gitignore]
key-decisions:
  - "Bind the public Phase 1 pilot only to Plan 08's verified BB-144 provenance, not a BB family label."
  - "Run a fixed 32-shot X-only product-sum BP smoke budget at one OpenMP thread and report it solely as pilot_adaptation/not_assessed."
  - "Promote the distinct native pilot to reference_executable while keeping its linked source paper experiment mapped_only."
requirements-completed: [MAP-02, MAP-03, REG-01, REG-02, REG-03, REG-04, CSS-03, CSS-04, LED-01]
coverage:
  - id: D1
    description: Selected frozen CSS artifact preflights before native BP and reports transparent evidence maturity.
    requirement: REG-03
    verification:
      - kind: integration
        ref: tests/test_reference_smoke.py#test_selected_pilot_preflight_is_bound_and_transparent
        status: pass
      - kind: integration
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/selected-css-pilot_adaptation-not_assessed.json
        status: pass
    human_judgment: false
  - id: D2
    description: The checked-in 32-shot pilot ledger, result, and registry link retain terminal outcomes without paper-maturity promotion.
    requirement: LED-01
    verification:
      - kind: integration
        ref: tests/test_evidence.py#test_completed_selected_pilot_preserves_final_rows_and_paper_maturity
        status: pass
      - kind: integration
        ref: OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/pilot_adaptation-not_assessed
        status: pass
    human_judgment: false
actuals:
  tokens: 38356
  tasks: 2
  commits: 4
plan_head_before: c61e65ef2efb540b4c04e9881e84faa6b3eb6a48
metrics:
  duration: 13min
  completed: 2026-09-22
  tasks_completed: 2
  files_changed: 10
status: complete
---

# Phase 1 Plan 09: Pinned Native CSS Pilot Summary

**A selected-artifact-only native `ldpc` BP command now produces a 32-shot BB-144 pilot ledger and result with final-row counts, source links, and explicit `pilot_adaptation`/`not_assessed` status.**

## Performance

- **Duration:** 13min
- **Started:** 2026-09-22T02:52:59Z
- **Completed:** 2026-09-22T03:05:39Z
- **Tasks:** 2/2
- **Files modified:** 10
- **Pilot resource context:** `OMP_NUM_THREADS=1` on `dcc-core-ferc-u-ac39-4-1`; native 32-shot execution elapsed 4.22 seconds.

## Accomplishments

- Added `bp_registry.cli` commands for evidence validation, selected-pilot preflight, execution, reconciliation, and run verification. Its pilot path rejects another artifact, source revision, environment, or native decoder contract before a native call.
- Added a complete selected BB-144 manifest with actual source, artifact, matrix/logical, package, decoder, seed, budget, and assessment fields. The documented command runs only product-sum, parallel BP with X-only `p=0.01` noise and 32 fixed shots.
- Executed and checked in 64 durable JSONL events: one begin and one terminal record for each shot ID 0–31. Final rows report 32 exact outcomes, zero nonconverged rows, zero interrupted rows, zero logical failures, and zero postselected rows for this local smoke budget.
- Reconstructed `result.json` only from final ledger rows, then reran the command without adding events. `verify-run` checks the manifest/artifact links, labels, exact shot set, and derived totals.
- Linked `gross-bb144-pilot` to `bhatnagar-impulse:Figure 6` in both directions. The pilot is `reference_executable`, `pilot_adaptation`, and `not_assessed`; the paper experiment remains `mapped_only` and `not_assessed`.

## Task Commits

1. **Task 1 RED: selected pilot preflight contract** — `ef388de` (`test`)
2. **Task 1 GREEN: selected CSS pilot command** — `96c50cf` (`feat`)
3. **Task 2 RED: completed pilot evidence contract** — `fad7165` (`test`)
4. **Task 2 GREEN: checked-in local pilot evidence** — `4d1bb90` (`feat`)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — **58 passed**.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/pilot_adaptation-not_assessed` — **passed**.
- A repeat `pilot` invocation retained **64 events and 32 terminal rows**; terminal IDs remain exactly `0..31`, and all result totals match the final ledger rows.
- `validate-evidence` passed and the registry retains the source-paper/pilot maturity distinction.

## Decisions Made

- The command validates against the actual Plan 08 provenance record so a matching code family name cannot substitute a different matrix/logical artifact.
- The 32-shot run is intentionally a local smoke pilot. Its successful exact outcomes do not establish source-faithful behavior, a curve pass, or statistical agreement.
- Native edge-update internals remain null with an explicit missingness reason in every final row because `ldpc.BpDecoder` does not expose them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected result-label verification semantics.**

- **Found during:** Task 2 verification.
- **Issue:** `verify-run` mistakenly required both labels to appear in each individual result field, rejecting a valid result where `relation` and `assessment_status` each carry their own label.
- **Fix:** Require both labels in the title and the exact corresponding value in each structured field.
- **Files modified:** `src/bp_registry/cli.py`
- **Verification:** completed-pilot test and `verify-run` both pass.
- **Committed in:** `4d1bb90`

**2. [Rule 2 - Missing critical functionality] Ignore generated local ledger lock files.**

- **Found during:** Task 2 pilot execution.
- **Issue:** Per-shot owner and journal locks are required runtime artifacts but would otherwise remain as untracked files beside checked-in evidence.
- **Fix:** Added a narrow result-directory lock ignore pattern while retaining the event ledger and result artifact in version control.
- **Files modified:** `.gitignore`
- **Verification:** `git status --short` shows no generated pilot lock files.
- **Committed in:** `4d1bb90`

**Total deviations:** 2 auto-fixed. Both preserve the required verification and artifact contracts.

## Known Stubs

None. `native_edge_updates: null` is an explicit SDK instrumentation limitation recorded with a per-row reason, not a rendering or data-flow stub.

## Next Phase Readiness

Later source-faithful and statistical work can use the manifest, stable sample identities, final-row ledger, and separate pilot registry record without promoting the mapped source experiment. The fixed pilot is evidence of executable reference plumbing only.

## TDD Gate Compliance

- **Task 1 RED:** `test_selected_pilot_preflight_is_bound_and_transparent` failed intentionally because the selected manifest did not yet exist; `ef388de` precedes the feature commit.
- **Task 1 GREEN:** the selected manifest, runner binding, CLI preflight, and native tiny-case smoke coverage pass.
- **Task 2 RED:** `test_completed_selected_pilot_preserves_final_rows_and_paper_maturity` failed intentionally because no checked-in pilot result existed; `fad7165` precedes the evidence commit.
- **Task 2 GREEN:** the 32-shot ledger/result, status transition, rerun idempotency, and full suite pass.

## Self-Check: PASSED

- All selected manifest, CLI, event-ledger, result, guide, and test files exist.
- Task commits `ef388de`, `96c50cf`, `fad7165`, and `4d1bb90` are present in git history.
- The full 58-test suite and the end-to-end `verify-run` command pass.
