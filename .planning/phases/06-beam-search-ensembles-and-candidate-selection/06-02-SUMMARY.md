---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "02"
subsystem: literature-policy-interface
tags: [toml, bpgd, yao, guided-decimation, artifact-identity, cache]
requires:
  - phase: "06-01"
    provides: strict runnable literature-policy parsing and common study command
provides:
  - Typed translation of every requested Yao BP/BPGD Figure 3 and Figure 6 record
  - Artifact-resolved Algorithm 1 `R = n` control in the executable manifest and cache identity
  - Runnable bounded BPGD T=1 canonical adaptation through the installed command
affects: [06-09, css-literature-gate, literature-policies]
actuals:
  tokens: 7598
  tasks: 2
  commits: 2
plan_head_before: f0e36f9c71204d53dfa3025718ea2d802d85e58e
tech-stack:
  added: []
  patterns: [source-control compiler, artifact-resolved policy controls, source-qualified BPGD composition]
key-files:
  created: [literature_policies/yao-2024-guided-decimation/bpgd-t001.toml]
  modified: [src/bp_registry/literature.py, src/bp_registry/study.py, src/bp_registry/manifests.py, src/bp_registry/canonical/contracts.py]
key-decisions:
  - "Yao's symbolic R=n is resolved only after raw and semantic validation of the selected artifact, and the integer is persisted in numerical identity."
  - "Guided decimation may declare stateless policy memory because its controller owns the continuing session; legacy identity bindings and all other Phase 5 intervention rules remain accepted as before."
requirements-completed: [INT-05, CAN-01]
coverage:
  - id: D1
    description: All ten requested Yao source records have stable T/R translation, source-gap disclosure, and non-source-faithful qualification.
    requirement: INT-05
    verification:
      - kind: unit
        ref: tests/test_literature_policy.py#test_yao_source_table_preserves_t_r_and_source_identity_gaps
        status: pass
    human_judgment: false
  - id: D2
    description: The BPGD T=1 policy resolves R from a validated artifact before running and reuses verified bounded CSS evidence through the installed command.
    requirement: CAN-01
    verification:
      - kind: e2e
        ref: tests/test_literature_policy.py#test_bpgd_t001_runnable_policy_uses_installed_common_command
        status: pass
      - kind: integration
        ref: tests/test_literature_policy.py#test_bpgd_t001_runnable_policy_resolves_after_artifact_and_reuses
        status: pass
    human_judgment: false
duration: 16min
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 02: Yao BPGD Policy Summary

**Yao's BP/BPGD Figure 3 and Figure 6 controls now translate into closed canonical policies, with a runnable T=1 BPGD adaptation that resolves Algorithm 1's R=n from the validated study artifact.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-05T21:04:33Z
- **Completed:** 2026-10-05T21:20:31Z
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

- Added a typed, ordered ten-record Yao translation table covering the BP comparator, T=1/10/70/100, and T=100 with explicit R=2/5/10/50/882.  T maps only to sweeps per round; R maps only to the round limit.
- Preserved the declared finite prior magnitude 25, ascending original-coordinate reliability ties, positive-prior zero rule, and return-after-last-fixation rule.  Author implementation and ordered B1 paper-artifact identity remain unresolved, so no record is source-faithful.
- Added `bpgd-t001.toml`, a canonical-adaptation/not-assessed policy.  Its `round_limit = "code_block_length"` is replaced only after raw and semantic artifact validation, making the resolved integer part of the persisted manifest and cache identity.
- Verified a bounded three-qubit run and reuse, the installed `bp-registry` command, and B1 length resolution to 882 without launching a B1 simulation.

## Task Commits

1. **Task 1: Translate and qualify every requested BP and BPGD control** — `f10a69a` (`feat`)
2. **Task 2: Publish one bounded BPGD policy for the gate** — `071aace` (`feat`)

## Files Created/Modified

- `src/bp_registry/literature.py` — Yao table compiler plus closed symbolic-control resolution and resolved execution identity.
- `src/bp_registry/study.py` — validates the selected artifact before converting `R=n` to an integer.
- `src/bp_registry/manifests.py` and `src/bp_registry/canonical/contracts.py` — admit `stateless` only for guided decimation while retaining historical identity bindings and all other intervention restrictions.
- `literature_policies/yao-2024-guided-decimation/bpgd-t001.toml` — runnable source-linked T=1 policy with inert equations, qualification, and unresolved provenance.
- `tests/test_literature_policy.py`, `tests/test_study_entrypoint.py`, and `tests/test_phase5_public_execution.py` — source mapping, artifact identity, preflight, command, and compatibility checks.

## Decisions Made

- Resolve a symbolic policy value only from the selected artifact after its declared raw and semantic digests validate; no cache or public manifest contains an unresolved `R=n` token.
- Interpret `stateless` as absence of a separate composition-level memory policy.  It does not reset guided decimation's controller-owned BP session between its rounds.

## Deviations from Plan

### Approved plan correction

- **Found during:** Task 1 and Task 2.
- **Issue:** The original file list could not satisfy its stated `R=n` rule: the study compiler projected a TOML file before it had validated the artifact length.  The existing Phase 5 compatibility rule also rejected the source-declared `stateless` BPGD role.
- **Fix:** Extended the plan's ownership to the study compiler, complete and compact Phase 5 compatibility checks, and focused regression tests.  Resolution now occurs after artifact validation and before cache identity.  Only guided decimation accepts `stateless`; historical guided identity records and all non-guided interventions retain their previous constraints.
- **Verification:** Focused source/control tests, public preflight regression, installed command smoke test, and B1 artifact-length validation passed.

**Impact on plan:** The correction implements the prespecified source controls without broadening the public intervention contract.

## Known Stubs

None.

## Next Phase Readiness

The bounded Yao policy can enter the common B1 literature gate once that study's finite budgets are frozen.  It remains a canonical adaptation until ordered paper artifact and full experiment settings are reconciled.

## Self-Check: PASSED

- Confirmed the runnable policy and all modified source/test files exist.
- Confirmed task commits `f10a69a` and `071aace` exist in repository history.
