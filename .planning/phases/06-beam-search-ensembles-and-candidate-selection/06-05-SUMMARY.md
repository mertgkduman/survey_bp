---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "05"
subsystem: candidate-selection
tags: [candidate-list, provenance, voting, original-syndrome-validation, fair-beam-relay]
requires:
  - phase: "06-01"
    provides: strict policy routing and source-qualified controlled-campaign context
provides:
  - Complete deterministic candidate-list records with duplicate provenance and registered score rules
  - Closed coordinate-majority voting with explicit electorate, tie rule, and original-syndrome validation
  - Read-only verification and reuse lock for the sealed fair BeamSearch/RelayBP campaign
affects: [06-06, 06-07, mbbp-ld, phase6-public-execution]
actuals:
  tokens: 8400
  tasks: 3
  commits: 2
plan_head_before: 0f59468c6c270ae313a12a25bd5a728ac712df6c
tech-stack:
  added: []
  patterns: [complete-origin-set, stable-lineage-ties, post-aggregation-original-validation, sealed-evidence-reuse]
key-files:
  created:
    - src/bp_registry/canonical/candidate_selection.py
    - tests/canonical/test_candidate_selection.py
    - tests/canonical/test_voting.py
    - tests/test_phase6_existing_evidence.py
  modified: []
key-decisions:
  - "List scoring is restricted to decoder-visible original-coordinate candidates; original-syndrome validity is independently recorded and gates eligibility."
  - "Duplicate payloads are grouped for frequency scoring only when their source is eligible and their candidate independently satisfies the original syndrome; every other origin remains in the frozen evidence with frequency zero."
  - "Coordinate majority retains an invalid synthesized correction with its voter record and never replaces it with a hidden-truth or undeclared fallback."
  - "The completed fair BeamSearch/RelayBP package is verified through hashes and reused; its campaign runner is patched to fail if verification tries to launch it."
requirements-completed: [MOD-04, INT-05, CAN-01, CAN-02]
duration: implementation handoff
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 05: Candidate Selection and Voting Summary

**Canonical candidate lists now retain all origins and select deterministically, while coordinate-majority votes expose their electorate and reject synthesized corrections that fail the immutable original syndrome.**

## Accomplishments

- Added immutable candidate-origin and frozen-list records.  Every origin retains lineage, local ordinal, digest or explicit absence, source eligibility, independent original-validity result, score, frequency, and reason.  Declared origin sets must be complete and duplicate-free.
- Added registered `stable_first`, `minimum_original_weight`, and `frequency_over_weight_plus_one` policies.  Frequency groups include only source-eligible, original-valid candidates, so rejected, pruned, denied, invalid, and candidate-less rows cannot inflate an admitted candidate's score.  Ties use `(local_ordinal, lineage_id)` and all evidence is canonical JSON, independent of worker arrival order.
- Added closed coordinate-majority voting over named correction bits.  It requires one eligible binary ballot from every declared member, names its tie bit, persists candidate, validation, and selection lineage nodes, and leaves invalid aggregate results ineligible.
- Added a sealed-evidence regression suite for the completed BB72 controlled adaptation.  It validates the matched 20-iteration initial BP, damping 1.0 and 0.5, Beam/Relay source profiles, relay interval `[-0.24, 0.66]`, separate work fields, disjoint cohorts, retained pruned and denied units, source labels, and reuse without relaunching a campaign.

## TDD Evidence

- RED, Task 1: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_candidate_selection.py::test_candidate_selection_module_exports_policy_seam -x` failed intentionally with `AssertionError: assert None is not None` because the production module was absent.
- GREEN, Task 1: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_candidate_selection.py -k 'eligibility or origin or duplicate or score or tie or worker or nonfinite' -x` — 6 passed, 1 deselected, including a rejected duplicate that would otherwise change a frequency-based winner.
- RED, Task 2: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py::test_vote_evidence_names_correction_bit_object -x` failed intentionally with `KeyError: 'object'` before the vote evidence named its correction-bit object.
- GREEN, Task 2: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py -k 'electorate or ballot or majority or tie or invalid or original or worker' -x` — 3 passed, 1 deselected.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_existing_evidence.py tests/canonical/test_fair_legs.py tests/test_study_entrypoint.py -k 'phase6 or fair or matched or beam or relay or published or reused' -x` — 17 passed, 5 deselected.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_candidate_selection.py tests/canonical/test_voting.py tests/test_phase6_existing_evidence.py tests/canonical/test_fair_legs.py tests/test_study_entrypoint.py -x` — 33 passed after review.
- `git diff --check` over all four owned implementation/test files — passed.

## Task Commits

1. **Tasks 1–2: deterministic list selection and valid coordinate voting** — `36aaf9e` (`feat`).
2. **Task 3: read-only published BeamSearch/RelayBP regression** — `317cbb0` (`test`).

## Deviations from Plan

The protected-main executor handed off reviewed changes. The coordinating agent made the two task-scoped commits and will update shared planning state.

## Known Stubs

None.

## Next Phase Readiness

MBBP-LD and later candidate-producing controllers can call `freeze_candidate_list` after retaining every declared origin.  Ensemble voting can call `CoordinateMajorityVote` with a declared parent node, complete electorate, and typed ballots.  The fair BeamSearch/RelayBP campaign remains sealed evidence rather than a compute dependency.

## Self-Check: PASSED

- Confirmed all four implementation and test files exist.
- Confirmed all 33 focused tests pass after review.
- Confirmed the sealed package is verified through `ensure_study` while any attempted subprocess campaign launch raises an assertion.
- Confirmed task commits `36aaf9e` and `317cbb0` exist and the post-review regression suite passes 33 tests.
