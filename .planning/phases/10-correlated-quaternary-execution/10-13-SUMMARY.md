---
phase: 10-correlated-quaternary-execution
plan: "13"
subsystem: native-aSCED-qualification
tags: [asced, native-reference, source-provenance, pypi, cmake, pybind11]
requires:
  - phase: 10-01
    provides: quaternary execution evidence conventions
provides:
  - Exact kit-cel/quantum_asced source identity and algorithm digest audit
  - Pending-human isolated native dependency and CMake proposal
  - Tamper-tested refusal of unapproved native execution
affects: [phase-10-plan-14, native-aSCED-reference]
tech-stack:
  added: []
  patterns: [read-only-remote-source-audit, digest-bound-build-proposal, pending-human-execution-gate]
key-files:
  created:
    - scripts/qualify_phase10_native_asced.py
    - data/native/phase10-asced-source-spec.json
    - tests/canonical/quaternary/test_asced_evidence.py
  modified: []
key-decisions:
  - "Only kit-cel/quantum_asced commit 816772071486615dfc7d71d1e15df597edc58a26 qualifies as the native reference."
  - "All native package, pybind11-overlay, and CMake inputs remain pending human review and build-run refuses to execute."
requirements-completed: [QBP-04]
plan_head_before: 0a29540352ed87eccbc003d8b508a71554cac0db
commits: 5
actuals:
  tokens: 6353
  tasks: 2
  commits: 5
coverage:
  - id: D1
    description: Exact native source identity, algorithm file hashes, and known divergence record.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_asced_evidence.py
        status: pass
      - kind: integration
        ref: scripts/qualify_phase10_native_asced.py audit-source
        status: pass
    human_judgment: false
  - id: D2
    description: Digest-bound five-package, pybind11 overlay, CMake, and out-of-tree driver proposal remains inert.
    requirement: QBP-04
    verification:
      - kind: unit
        ref: tests/canonical/quaternary/test_asced_evidence.py
        status: pass
      - kind: integration
        ref: scripts/qualify_phase10_native_asced.py verify-proposal
        status: pass
    human_judgment: false
metrics:
  duration: 7m
  completed: 2026-10-06
status: complete
---

# Phase 10 Plan 13: Native aSCED Qualification Summary

Read-only qualification of the exact aSCED author source with a digest-bound, pending-human isolated build proposal.

## Accomplishments

- Added a read-only audit command that verifies the exact `kit-cel/quantum_asced` commit through GitHub's commit API and SHA-256 hashes each selected build, binding, channel, BP4, aSCED, and selection source input.
- Recorded the missing pybind11 gitlink, README demo-path mismatch, unresolved license fact, native `I/X/Z/Y` translation, paper/native selection difference, equal-proportion channel restriction, and unavailable native shot/path instrumentation.
- Froze all five official PyPI artifacts, the pybind11 v3.1.0 overlay, and Kitware CMake 4.2.0 by version, URL, and SHA-256. The proposal forbids primary-environment access, algorithm modifications, and ambient CMake discovery.
- Kept the proposal `pending_human`; the `build-run` subcommand returns a refusal and never performs install, build, import, or native execution.

## Task Commits

1. **Task 1: Audit the exact native source and preserve discrepancies**
   - `1aaa4db` `test(10-13): add failing native aSCED evidence contract`
   - `c71bf29` `feat(10-13): audit pinned native aSCED source`
2. **Task 2: Generate a digest-bound isolated build proposal**
   - `7ff748f` `test(10-13): add failing isolated build proposal contract`
   - `d612dd3` `feat(10-13): freeze inert native aSCED build proposal`
   - `4c8af2a` `fix(10-13): resolve pinned aSCED commit by API`

## Verification

- `scripts/qualify_phase10_native_asced.py audit-source` — passed; exact commit and all twelve audited source hashes matched.
- `scripts/qualify_phase10_native_asced.py verify-proposal` — passed; verified `pending_human` status without network installs or native execution.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -x` — passed (6 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py tests/canonical/quaternary/test_algebra.py -x` — passed (44 tests).
- `docs/environment-freeze.txt` SHA-256 was unchanged and its git diff was empty.

## TDD Gate Compliance

- Task 1 RED evidence passed: `test_source_identity_records_exact_commit_and_audited_discrepancies` failed intentionally before the source audit existed.
- Task 2 RED evidence passed: `test_proposal_binds_all_unapproved_packages_overlay_and_cmake_identity` failed intentionally before the proposal existed.
- Both GREEN suites passed after implementation.

## Decisions Made

- Treat absence of a located license file solely as an unresolved fact. It cannot establish a license conclusion or grant execution authority.
- Treat official registry metadata as a proposal input only. No package is installed or otherwise made executable by this plan.
- Use the immutable GitHub commit API endpoint for an exact commit check. A `git ls-remote` ref-pattern query does not reliably prove reachability of an arbitrary immutable object.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Replaced an unreliable exact-commit `git ls-remote` query with the pinned GitHub commit API identity.**
   - **Found during:** Overall source audit after Task 2.
   - **Issue:** A full object ID passed as an `ls-remote` ref pattern did not reliably return the immutable commit.
   - **Fix:** Queried the exact official commit API URL and compared its returned `sha` to the required full commit before fetching and hashing source files.
   - **Files modified:** `scripts/qualify_phase10_native_asced.py`, `tests/canonical/quaternary/test_asced_evidence.py`
   - **Verification:** Read-only remote audit and all evidence tests passed.
   - **Committed in:** `4c8af2a`

## Known Stubs

None.

## Next Phase Readiness

Plan 10-14 has one concrete review object containing the exact source, all package and tool bytes, overlay/driver limits, unresolved license fact, and a hard no-build gate. Human approval remains required before any isolated build or native execution.

## Self-Check: PASSED

- Confirmed all three delivered files exist.
- Confirmed commits `1aaa4db`, `c71bf29`, `7ff748f`, `d612dd3`, and `4c8af2a` exist.
