---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "06"
subsystem: mbbp-ld
tags: [mbbp-ld, augmented-basis, gf2, normalized-min-sum, check-node-serial, list-selection]
requires:
  - phase: "06-05"
    provides: complete original-valid candidate origins and frequency-weighted selection
provides:
  - Explicit GF(2) augmented-basis descriptors with derived augmented syndromes
  - Independent normalized-min-sum serial-check MBBP member sessions and unique work leaves
  - Canonical-adaptation frequency-weighted list selection with typed no-convergence sentinel
affects: [06-07, 06-09, rabeti-2026-multiple-bases-bp-list-decoding]
actuals:
  tokens: 8100
  tasks: 2
  commits: 1
plan_head_before: 0f59468c6c270ae313a12a25bd5a728ac712df6c
tech-stack:
  added: []
  patterns: [explicit-gf2-augmentation, member-local-serial-state, declared-completion-order, typed-source-failure-sentinel]
key-files:
  created: [src/bp_registry/canonical/mbbp.py, tests/canonical/test_mbbp.py]
  modified: [src/bp_registry/canonical/__init__.py]
key-decisions:
  - "Every redundant check is an explicit binary transform of original checks, and its appended syndrome uses the same GF(2) transform."
  - "Each MBBP basis owns a fresh normalized-min-sum alpha=0.875 check-node-serial schedule, message buffer, C2V state, executor, and budget scope."
  - "Completion order may vary for execution but all terminals, work leaves, origins, and selection evidence are returned in declared stable order."
  - "The paper's zero return is represented only as a typed no-member-converged failure sentinel and is never admitted to the candidate list or evaluator."
requirements-completed: [INT-05, CAN-01, CAN-02]
duration: implementation handoff
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 06: MBBP-LD Core Summary

**The canonical MBBP-LD core now derives auditable augmented parity-check bases, runs fresh serial normalized-min-sum members, and selects an original-valid list candidate by frequency divided by Hamming weight plus one.**

## Accomplishments

- Added immutable `MbbpBasis` descriptors containing the member identity, declared partition and permutation identities, ordered redundant GF(2) transforms, and canonical-adaptation status.  `augment()` appends each derived redundant check and applies the identical transform to the immutable original syndrome.
- Added algebra checks for binary, nonzero, original-row-aligned transformations; augmented row/syndrome dimensions; duplicate member identities; and descriptor order.  Original check and syndrome arrays remain unchanged.
- Added `MbbpController`: every basis gets a new normalized-min-sum `alpha=0.875` kernel, check-node-serial schedule, V2C/C2V state, executor, and budget scope.  Work is collected from unique committed leaves and reduced without double counting.
- Connected each member's converged original-space correction to Phase 6 candidate selection.  Only converged, independently original-valid member origins increase duplicate frequency or can win the frequency-over-weight-plus-one score.
- Implemented `no_member_converged_zero_return`: the source zero vector is retained as a failure sentinel, while selected candidate and origin remain absent.  The sentinel is never passed to candidate admission or evaluation.

## TDD Evidence

- RED, Task 1: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py::test_mbbp_module_exports_augmented_basis_seam -x` failed intentionally because `bp_registry.canonical.mbbp` did not exist.
- GREEN, Task 1: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py -k 'basis or augmented or syndrome or oracle or immutable or malformed' -x` — 6 passed, 6 deselected.
- RED, Task 2: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py::test_mbbp_exports_independent_member_controller -x` failed intentionally because `MbbpController` was absent.
- GREEN, Task 2: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_candidate_selection.py -k 'member or independent or normalized or serial or frequency or weight or no_member_converged or zero_return or worker or work or replay' -x` — 13 passed, 6 deselected.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_candidate_selection.py -x` — 19 passed.
- `git diff --check` over `mbbp.py`, canonical exports, MBBP tests, and this summary — passed.

## Task Commits

The coordinating agent independently reran the focused tests and committed the core as `3032774` after reviewing the controller, algebra, and source qualification.

## Deviations from Plan

The controller adds the finite per-member C2V cap as the narrow budget-denial mechanism needed to retain denied terminals and their zero committed work leaves.

The source's $H_t$ is a submatrix of original checks, so a source-style member uses one-hot row transforms. The core accepts general explicit GF(2) transforms as a canonical extension; the runnable literature compiler must constrain its paper-labelled basis descriptors to duplicated original rows and keep the unresolved partition/permutation identity visible.

## Known Stubs

None.

## Next Phase Readiness

The Phase 6 public policy route can now bind a declared canonical MBBP adaptation to B1 after it supplies a reproducible partition/permutation and artifact identity.  It must retain the existing `canonical_adaptation` source label until those paper-experiment gaps are resolved.

## Self-Check: PASSED

- Confirmed all owned source, export, and test files exist.
- Confirmed 19 focused MBBP and candidate-selection tests pass.
- Confirmed no large simulation or campaign output was created or changed, and task commit `3032774` exists.
