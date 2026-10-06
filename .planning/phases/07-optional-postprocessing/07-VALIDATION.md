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
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase7_public_execution.py tests/canonical/test_postprocessing_handoff.py` after Wave 0 creates those files |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure in Wave 0; do not assume an HPC-node runtime |

## Sampling Rate

- After each implementation task, run the task's focused test file and the nearest handoff or ledger regression test.
- After each plan wave, run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`.
- Before `$gsd-verify-work`, require the full suite, deterministic source/compatibility fixtures, ledger verification, bounded B1 receipt, and executed notebook.
- Record actual targeted and full-suite runtimes in the execution summaries; adjust sampling only from measured latency.

## Per-Task Verification Map

| Requirement | Plan / task | Behavior | Threat Ref | Test Type | Automated Command | File Exists | Status |
|-------------|-------------|----------|------------|-----------|-------------------|-------------|--------|
| POST-01 | 07-02 T1; 07-03 T1–T2; 07-07 T1; 07-12 T1–T2; 07-13 T1–T2; 07-14 T1 | Pinned standalone OSD build/import gate, declared reliability and method/order, original-space candidate, replay, public execution, and work | T-07-01, T-07-03 | contract/differential/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_osd.py tests/test_phase7_public_execution.py tests/test_phase7_literature_osd_lsd.py` | ❌ Wave 0 | ⬜ pending |
| POST-02 | 07-01 T1; 07-11 T1–T2; 07-07 T1–T2; 07-12 T1–T2; 07-13 T1–T2; 07-14 T1 | Released standalone LSD, base/MBBP whole-composition handoff, stable ties, public replay, and policy-file route | T-07-01, T-07-02 | contract/differential/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_handoff.py tests/canonical/test_mbbp.py tests/test_phase7_public_execution.py` | ❌ Wave 0 | ⬜ pending |
| POST-03 | 07-04 T1–T2; 07-07 T1; 07-12 T1–T2; 07-15 T1 | SI inactivation, rerun/solve/lift for qualified adaptation; source-faithful blockers remain non-runnable | T-07-01, T-07-02 | algebra/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_si.py tests/test_phase7_literature_si_otf.py` | ❌ Wave 0 | ⬜ pending |
| POST-04 | 07-05 T1–T2; 07-07 T1; 07-12 T1–T2; 07-15 T1 | OTF stable forest, acyclicity, rerun/lift for labeled CSS adaptation; faithful circuit source status remains non-runnable | T-07-01, T-07-02 | algebra/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_otf.py tests/test_phase7_literature_si_otf.py` | ❌ Wave 0 | ⬜ pending |
| POST-05 | 07-01 T1; 07-06 T1–T2; 07-11 T1–T2; 07-07 T1–T2; 07-12 T1–T2; 07-13 T1–T2; 07-09 T1–T2; 07-10 T1–T2 | Whole-composition trigger, fail-closed unsupported pairs, BP-only/final separation, native identity/missingness, matched shots, and notebook | T-07-01, T-07-04, T-07-05 | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_postprocessing_handoff.py tests/test_phase7_public_execution.py tests/test_phase7_notebook.py` | ❌ Wave 0 | ⬜ pending |

## Required Semantic Fixtures

- BP success, a failed branch followed by BP success, and whole-composition nonconvergence prove zero, zero, and exactly one fallback call respectively.
- Permuting failed-attempt completion order and changing hidden truth cannot change the selected handoff.
- Every failed MBBP member retains terminal posterior reliability and reaches the frozen ranking set; any later original-valid member suppresses fallback for the whole ensemble.
- Relay, fair Beam/Relay, intervention, restart, and unknown composition/postprocessing pairs fail public preflight before artifact loading until a complete snapshot adapter exists.
- Missing, nonfinite, wrong-length, wrong-sign, or nontranslatable reliability records a skip reason and retains the BP terminal result.
- Every candidate is reconstructed and checked against the immutable original problem. A complete valid candidate survives a later cap; incomplete or invalid candidates remain ineligible.
- Native BP-OSD/BP-LSD references retain their own BP execution identity and unavailable internal counters with explicit reasons.
- Strict TOML rejects multiple methods, incomplete component provenance, unresolved runnable source claims, and implicit overrides.
- Ledger tamper/replay covers fallback trigger, origin, candidate lineage, BP-only and final outputs, work, caps, and native missingness.
- The B1 demonstration retains every prespecified identified shot. Separate deterministic fixtures force trigger and no-trigger views.

## Wave 0 Requirements

- [ ] `tests/canonical/test_postprocessing_handoff.py` — trigger, ranking, reliability, reconstruction, and compatibility fixtures.
- [ ] `tests/canonical/test_postprocessing_osd.py` — isolated official branch import/build receipt and tiny-matrix differential fixtures.
- [ ] `tests/test_phase7_public_execution.py` — released standalone LSD contract fixtures plus the installed-CLI tracer.
- [ ] `tests/canonical/test_postprocessing_si.py` and `tests/canonical/test_postprocessing_otf.py` — source-qualified algebra and adaptation fixtures.
- [ ] `tests/test_phase7_public_execution.py` and `tests/test_phase7_notebook.py` — manifest, ledger, CLI, B1, and notebook evidence.
- [ ] `tests/test_phase7_literature_osd_lsd.py` and `tests/test_phase7_literature_si_otf.py` — split policy publication, source-status, identity, and common-command coverage.
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
