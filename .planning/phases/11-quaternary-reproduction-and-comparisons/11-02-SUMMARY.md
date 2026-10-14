---
phase: 11-quaternary-reproduction-and-comparisons
plan: "02"
subsystem: source-evidence
tags: [qbpgd, a5, figure-7, provenance, canonical-adaptation]
requires:
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "01"
    provides: digest-bound source-target and blocked-assessment contract
provides:
  - Deterministic A5 [[180,10,15<=d<=18]] CSS artifact with source-bound provenance
  - Frozen Figure 7 Q-BPGD target and manifest with explicit fidelity blockers
  - Replayable bounded canonical-adaptation qualification probe with typed work evidence
affects: [phase-11-source-studies, quaternary-reproduction]
tech-stack:
  added: []
  patterns: [polynomial-reconstructed artifact, source-setting versus qualification-probe separation, typed Q-BPGD terminal evaluation]
key-files:
  created:
    - data/artifacts/quaternary-a5.json
    - data/artifacts/quaternary-a5.provenance.json
    - data/source-targets/phase11-qbpgd-figure7-a5.json
    - data/manifests/phase11-qbpgd-figure7-a5.json
    - tests/test_phase11_qbpgd_source.py
  modified:
    - src/bp_registry/quaternary/problems.py
    - src/bp_registry/quaternary/qbpgd.py
    - scripts/run_phase11_source_studies.py
key-decisions:
  - "A5 reconstructs from the published l=90 polynomial pair, while its distance interval remains source reported and unproved locally."
  - "Figure 7 remains frozen at Q-BPGD T=10, ordinary Q-BP T=100, epsilon=1e-10, up to n rounds, and 100 error cases."
  - "The one-sweep, p=0.03 qualification probe is distinct canonical-adaptation evidence, not a Figure 7 performance point or source-faithful assessment."
actuals:
  tokens: 25283
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 2bc3fec6304562d1786fe32637b9242faea48c09
duration: 12m
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 02: Q-BPGD Figure 7 A5 Source Target Summary

**A deterministic A5 source artifact and Figure 7 Q-BPGD target now preserve published settings, provenance, typed decimation work, and every unresolved fidelity fact.**

## Performance

- **Duration:** 12m
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

- Reconstructed the A5 generalized-bicycle CSS code from its published polynomial pair and persisted ordered matrices, derived logicals, raw and semantic digests, ranks, and commutation checks.
- Kept the reported `15<=d<=18` interval separate from independently checked algebraic facts.
- Added the digest-bound Figure 7 source target and manifest with the paper's Q-BPGD, ordinary Q-BP, stopping, artifact, source-component, and interpretation identities.
- Added a bounded one-sweep canonical-adaptation probe that records Q-BPGD decimation, ranking, fixation, terminal evaluation, and replay evidence without creating a curve or fidelity verdict.

## Task Commits

1. **Task 1: Reconstruct and preflight the A5 source artifact** — `3159d59` (feat)
2. **Task 2: Freeze Figure 7 settings and a bounded Q-BPGD qualification path** — `aa84ba6` (feat)

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_qbpgd_source.py -k 'a5 and (tracer or artifact or polynomial or rank or commutation or provenance or tamper)' -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_qbpgd_source.py -k 'figure7 or settings or decimation or work or adaptation or replay or blocked or discrepancy' -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_qbpgd_source.py -x` — passed (4 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_targets.py -x` — passed (5 tests).

## Decisions Made

- Full source settings remain immutable in the target. The qualification probe declares `canonical_iterations_per_round=1`, `round_limit=1`, and `p=0.03` as a separate bounded route because a full T=10 execution plus replay exceeded the initial 25-second safety probe.
- The qualification receipt remains `inconclusive`, `canonical_adaptation`, and `not_assessed`; unresolved message lifecycle, ties, normalization, coordinates, and author implementation identity remain blockers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Avoided array-valued dataclass equality during replay verification**
- **Found during:** Task 2 qualification regression.
- **Issue:** Comparing replayed `QbpgdResult` instances invoked ambiguous NumPy array truth evaluation.
- **Fix:** Relied on `reconstruct_qbpgd`, which already performs the full transition, fidelity, and work-evidence comparison.
- **Files modified:** `scripts/run_phase11_source_studies.py`.

**2. [Rule 2 - Critical functionality] Recorded terminal candidate evaluation as typed Q-BPGD work**
- **Found during:** Task 2 implementation.
- **Issue:** The existing decimation controller retained sweep, ranking, fixation, and original-syndrome work but omitted terminal candidate evaluation.
- **Fix:** Added a reserved `candidate_checks=1` terminal-evaluation leaf to the controller.
- **Files modified:** `src/bp_registry/quaternary/qbpgd.py`.

**3. [Rule 2 - Critical functionality] Made the qualification probe explicitly bounded and distinct from source assessment**
- **Found during:** Task 2 bounded execution verification.
- **Issue:** Full Figure 7 T=10 execution plus replay exceeded the bounded local safety probe.
- **Fix:** Preserved source settings in the target and added a separately labeled one-sweep canonical-adaptation qualification path with finite BP, event, storage, and wall-time caps.
- **Files modified:** `scripts/run_phase11_source_studies.py`, `data/source-targets/phase11-qbpgd-figure7-a5.json`, `data/manifests/phase11-qbpgd-figure7-a5.json`.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed all eight task files exist.
- Confirmed task commits `3159d59` and `aa84ba6` exist in Git history.
