---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "04"
subsystem: literature-impulse-policy
tags: [literature, impulse, toml, forced-zero, source-qualification]
requires:
  - phase: "06-01"
    provides: strict literature TOML parser and shared study command
  - phase: "06-03"
    provides: distinct forced-zero/one impulse realizations and V2C clip
provides:
  - Closed typed mappings for the three requested Bhatnagar impulse variants
  - Runnable first-convergence-0 TOML with artifact-resolved attempt cap
  - Verified common-command computation and reuse on a bounded CSS fixture
affects: [06-09, css-literature-gate, bhatnagar-2026-impulse-decoding]
key-files:
  created: [literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.toml]
  modified: [src/bp_registry/literature.py, tests/test_literature_policy.py, literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/PAPER.md]
key-decisions:
  - "The source's stateless per-coordinate behavior maps to fresh impulse-controller sessions and an identity public state-memory role, as required by the current Phase 5 manifest contract."
  - "Algorithm 1's declared index order governs this CSS policy; the source's later reliability order belongs to its separate circuit-oriented Algorithm 2."
  - "Flooding and a finite magnitude-25 forced LLR are explicit canonical interpretations; published Figure 5 reproduction remains unassessed."
requirements-completed: [INT-05, CAN-01]
completed: 2026-10-05
status: complete
---

# Phase 06 Plan 04: Impulse Literature Policy Summary

All three requested [Bhatnagar et al.](https://arxiv.org/html/2606.18240v1) names now have exact typed translations: `Minimum_Weight/1`, `First_Convergence/0`, and `First_Convergence/1`. Their source records remain non-runnable and retain the source experiment identity gap. The first-convergence force-zero variant has a separate runnable TOML policy at the paper root.

The runnable policy declares 100 sweeps for baseline and each fresh coordinate, V2C clip 25, original-syndrome validation, and symbolic ascending coordinate order and one-attempt-per-coordinate cap resolved after artifact validation. Its paper notes distinguish the unspecified message schedule and finite realization of an infinite forced prior. The common command computes and then verifies/reuses a bounded three-qubit fixture. That fixture frequently succeeds at baseline, so the direct impulse kernel tests supply the forced-attempt and replay evidence; the fixture is not a paper curve assessment.

## Verification

- RED: missing Bhatnagar compiler caused collection failure before implementation.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'bhatnagar or minimum_weight or first_convergence or forced_zero or forced_one or v2c_clip' -x` — passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py tests/canonical/test_impulse.py -x` — 38 passed.
- Installed `bp-registry` subprocess test computes and reports a verified force-zero specification.

## Limitations

The runnable file is a canonical adaptation. It does not establish author-code identity, exact infinity semantics, or Figure 5 statistical agreement. The other two variants have typed compiler dispositions; they still need runnable files and bounded command runs in Plan 09.

## Self-Check: PASSED

The three source names map without aliases; tampered suffix and executable force values fail closed. Public compute/reuse and inherited impulse replay tests pass.
