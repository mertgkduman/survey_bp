---
phase: "07"
slug: "optional-postprocessing"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-05"
---

# Phase 07 — Validation Strategy

> Validate fallback semantics on deterministic CSS fixtures before the bounded B1 demonstration. Source-faithful claims require their own source and API gates.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 in the existing `.venv` |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_handoff.py tests/canonical/test_postprocessing_lsd.py` after Wave 0 creates those files |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure in Wave 0; do not assume an HPC-node runtime |

## Sampling Rate

- After each implementation task, run the task's focused test file and the nearest handoff or ledger regression test.
- After each plan wave, run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`.
- Before `$gsd-verify-work`, require the full suite, deterministic source/compatibility fixtures, ledger verification, bounded B1 receipt, and executed notebook.
- Record actual targeted and full-suite runtimes in the execution summaries; adjust sampling only from measured latency.

## Per-Task Verification Map

| Requirement | Behavior | Threat Ref | Test Type | Automated Command | File Exists | Status |
|-------------|----------|------------|-----------|-------------------|-------------|--------|
| POST-01 | Pinned standalone OSD build/import gate, declared reliability and method/order, original-space candidate, work | T-07-01, T-07-03 | contract/differential | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_osd.py` | ❌ Wave 0 | ⬜ pending |
| POST-02 | Released standalone LSD handoff, methods/order, tie fixture, candidate and work | T-07-01 | contract/differential | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_lsd.py` | ❌ Wave 0 | ⬜ pending |
| POST-03 | SI inactivation, rerun/solve/lift for qualified adaptation; source-faithful blocker remains non-runnable | T-07-01, T-07-02 | algebra/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_si.py` | ❌ Wave 0 | ⬜ pending |
| POST-04 | OTF stable forest, acyclicity, rerun/lift for labeled CSS adaptation | T-07-01, T-07-02 | algebra/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_otf.py` | ❌ Wave 0 | ⬜ pending |
| POST-05 | Whole-composition trigger, BP-only/final separation, native composite identity and opaque missingness | T-07-01, T-07-04 | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase7_public_execution.py tests/test_phase7_notebook.py` | ❌ Wave 0 | ⬜ pending |

*Plan/task IDs are assigned when PLAN.md files are created. The requirement map is the Wave 0 seed.*

## Required Semantic Fixtures

- BP success, a failed branch followed by BP success, and whole-composition nonconvergence prove zero, zero, and exactly one fallback call respectively.
- Permuting failed-attempt completion order and changing hidden truth cannot change the selected handoff.
- Missing, nonfinite, wrong-length, wrong-sign, or nontranslatable reliability records a skip reason and retains the BP terminal result.
- Every candidate is reconstructed and checked against the immutable original problem. A complete valid candidate survives a later cap; incomplete or invalid candidates remain ineligible.
- Native BP-OSD/BP-LSD references retain their own BP execution identity and unavailable internal counters with explicit reasons.
- Strict TOML rejects multiple methods, incomplete component provenance, unresolved runnable source claims, and implicit overrides.
- Ledger tamper/replay covers fallback trigger, origin, candidate lineage, BP-only and final outputs, work, caps, and native missingness.
- The B1 demonstration retains every prespecified identified shot. Separate deterministic fixtures force trigger and no-trigger views.

## Wave 0 Requirements

- [ ] `tests/canonical/test_postprocessing_handoff.py` — trigger, ranking, reliability, reconstruction, and compatibility fixtures.
- [ ] `tests/canonical/test_postprocessing_osd.py` — isolated official branch import/build receipt and tiny-matrix differential fixtures.
- [ ] `tests/canonical/test_postprocessing_lsd.py` — released standalone interface and work fixtures.
- [ ] `tests/canonical/test_postprocessing_si.py` and `tests/canonical/test_postprocessing_otf.py` — source-qualified algebra and adaptation fixtures.
- [ ] `tests/test_phase7_public_execution.py` and `tests/test_phase7_notebook.py` — manifest, ledger, CLI, B1, and notebook evidence.
- [ ] Versioned fallback ledger/work fixture and tamper case; an isolated OSD environment receipt if its source build is admitted.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notebook readability and source/adaptation labels | POST-05 | Human visual review supplements automated notebook execution | Open the generated bounded B1 notebook and confirm each shot displays BP-only and final outcomes, fallback origin/status, work, lineage, and native missingness. |

## Validation Sign-Off

- [ ] All tasks have an `<automated>` verification command or explicit Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 creates all named test targets before later tasks use them.
- [ ] No watch-mode command is used.
- [ ] Actual feedback latency is measured and recorded.
- [ ] `nyquist_compliant: true` is set only after validation audit.

**Approval:** pending
