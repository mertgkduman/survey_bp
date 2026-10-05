---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "08"
subsystem: literature-policy-command
tags: [mbbp-ld, toml, study, provenance]
status: complete
dependency_graph:
  requires: [06-04, 06-07]
  provides: [rabeti-runnable-adaptation, public-mbbp-policy-route]
  affects: [css-literature-b1-gate]
key_files:
  created: [literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml]
  modified: [src/bp_registry/literature.py, src/bp_registry/study.py, tests/test_literature_policy.py]
decisions:
  - The source transcription remains non-runnable; the two-member one-hot duplicate-row pilot is explicitly a canonical adaptation.
  - Basis row indices resolve only after the pinned artifact bytes and semantics validate, then enter the executable and cache identities.
  - A no-member-converged source zero return is a typed failure and never an evaluator candidate.
---

# Phase 06 Plan 08: MBBP-LD Policy-File Route

## Completed Work

- Qualified the Rabeti–Mahdavifar source controls against its source specification: normalized min-sum factor 0.875, serial checks, 100 iterations, independent augmented members, and frequency divided by weight plus one.
- Added a closed paper-root TOML with two explicit one-hot duplicate-row members. It records the unresolved maximal-subtree partition, syndrome notation, tie rule, author implementation, and ordered experiment artifact.
- Compiled source-row indices to full one-hot transforms only after artifact validation. The resulting decoder runs through the same `ensure_study` and installed `bp-registry STUDY --decoder FILE` interface as the first two papers.
- Verified a selected original-valid candidate and a separately forced all-members-fail terminal. The latter retains the source zero sentinel without selection or evaluation.

## Verification

- `tests/test_literature_policy.py`, `tests/test_phase6_public_execution.py`, and `tests/test_study_entrypoint.py`: 33 passed together.
- The installed command computes then returns verified `reused` status for the bounded MBBP policy.
- `git diff --check` passed.

## Deviations from Plan

- Added source qualification and public MBBP cases to `tests/test_literature_policy.py`, the shared parser and command test module, rather than duplicate them in `tests/test_study_entrypoint.py`.
- Updated the paper reproduction note and registry README because both had stated that no MBBP route existed.

## Scientific Limit

The two-member policy is a mechanism and workflow pilot, not the paper's maximal-subtree experiment or Figure 5 reproduction. Statistical assessment remains in the later CSS campaign phases.
