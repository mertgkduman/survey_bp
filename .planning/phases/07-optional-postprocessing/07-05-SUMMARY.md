---
phase: 07-optional-postprocessing
plan: "05"
subsystem: ordered Tanner forest CSS adaptation
tags: [otf, css, postprocessing, tdd, tanner-forest]
requires:
  - phase: 07-01
    provides: frozen failed-BP handoff and one-method postprocessing boundary
  - phase: 07-04
    provides: method-owned postprocessing work-leaf pattern
provides:
  - Deterministic original-H_Z ordered Tanner forest construction
  - Same-kernel forest rerun, total zero lift, and immutable original validation
  - Explicit source-faithful circuit blocker beside the runnable CSS adaptation
affects: [07-optional-postprocessing, phase-08-campaigns]
tech-stack:
  added: []
  patterns: [stable posterior probability ordering, cycle-safe union-find certificate, method-owned OTF work leaves]
key-files:
  created:
    - src/bp_registry/canonical/postprocessing/otf.py
    - tests/canonical/test_postprocessing_otf.py
  modified:
    - src/bp_registry/canonical/postprocessing/work.py
key-decisions:
  - "Pin arXiv:2409.01440 and BPOTF da6caa4509dadb8620d8cac38108b4816897b18b while keeping faithful detector/circuit transfer non-runnable until Phases 12-13."
  - "Order finite log(P(0)/P(1)) posterior error probabilities descending with stable original-column ties, then admit only union-find cycle-safe Tanner columns."
  - "Retain an original-valid zero-lifted candidate when the declared forest cap remains part of the method termination evidence."
requirements-completed: [POST-04]
actuals:
  tokens: 7139
  tasks: 2
  commits: 5
plan_head_before: 5401b11d1622163d8dd9fdab01054d0346a68ee7
commits: 5
metrics:
  duration: 35min
  completed: 2026-10-06
status: complete
---

# Phase 07 Plan 05: Ordered Tanner Forest Summary

The Phase 7 OTF path is now a deterministic binary-CSS adaptation: it builds an acyclic original-H_Z forest from failed-BP posterior odds, reruns the declared canonical BP kernel, zero-lifts omitted columns, and validates the immutable original syndrome.

## Accomplishments

- Added `OrderedTannerForestSpec`, `ForestConstruction`, `OtfResult`, and `OtfPostprocessor` with the pinned paper/code identities and explicit `canonical_css_adaptation` status.
- Converted finite natural-log odds into error probabilities, broke exact ties by original column identity, and retained considered, accepted, cycle-rejected, and cap-denied columns.
- Independently replayed acyclicity and ordered maximality for complete forests, with typed handling of nonfinite reliability, duplicate identities, disconnected columns, and resource caps.
- Recorded OTF-specific sort, union-find probe, accepted-column, forest-BP, lift, and original-check work leaves.
- Tested same-kernel rerun, zero extension, invalid/nonconverged forest output, cap retention, source circuit exclusion, and compatibility with the generic one-shot postprocessing controller.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_otf.py -x` — 13 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_handoff.py -x` — 4 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` — 861 passed, 1 skipped, 6 pre-existing multiprocessing fork warnings in 12m 26s.
- `.venv/bin/python -m py_compile src/bp_registry/canonical/postprocessing/otf.py src/bp_registry/canonical/postprocessing/work.py` — passed.

## TDD Gate Compliance

| Task | RED evidence | GREEN commit | Result |
| --- | --- | --- | --- |
| 1 | `.gsd/tdd-evidence/07-05-task-1-red.json` (`RED_EVIDENCE_OK`) | `d37968d` | Passed |
| 2 | `.gsd/tdd-evidence/07-05-task-2-red.json` (`RED_EVIDENCE_OK`) | `18c7a49` | Passed |

## Task Commits

1. `8b2e7de` — `test(07-05): add failing OTF forest contract`
2. `d37968d` — `feat(07-05): build ordered Tanner forests`
3. `4e378d3` — `test(07-05): add failing OTF rerun contract`
4. `18c7a49` — `feat(07-05): rerun and lift OTF forests`
5. `be75c8f` — `test(07-05): cover OTF controller binding`

## Deviations from Plan

### Scoped dependency deviation

Plan 07-03 halted with the approved standalone OSD source deliberately non-runnable. Plan 07-05 was executed under the orchestrator's explicit independent-OTF scope because no OSD worker, adapter, API, or qualification receipt is needed by the ordered-Tanner-forest CSS adaptation. The failed Plan 07-03 receipt remains unchanged; POST-01 stays blocked.

## Known Source Boundary

The source-faithful BPOTF circuit/detector procedure remains non-runnable in Phase 7. `source_faithful_status()` retains the detector sparsification and LLR-path blockers, while the executable path is explicitly labeled `canonical_css_adaptation` and accepts only an immutable binary-CSS original H_Z problem.

## Self-Check: PASSED

`otf.py`, `work.py`, and the OTF test module exist; all five task commits are present in Git history.
