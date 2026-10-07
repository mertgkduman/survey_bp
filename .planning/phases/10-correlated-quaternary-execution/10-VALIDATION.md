---
phase: "10"
slug: "correlated-quaternary-execution"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-06"
---

# Phase 10 — Validation Strategy

> Execution feedback contract. Plan and task IDs will be filled after plan generation; this draft records the independent evidence required by `10-RESEARCH.md`.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Existing targeted baseline | 24 tests in 1.76 s on 2026-10-06, per `10-RESEARCH.md` |

## Sampling Rate

- **After every task commit:** Run the file-specific test named in that task, plus the closest existing boundary test.
- **After every plan wave:** Run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary tests/test_sampling.py tests/test_css_small.py tests/test_phase6_public_execution.py`.
- **Before `$gsd-verify-work`:** Run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` and retain the result.
- **Max feedback latency:** Keep the per-task command under 30 seconds where fixtures permit; split slow native build checks into an explicit bounded integration gate.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | QBP-01 | — | N/A | algebra, vector and exact oracle | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py tests/canonical/quaternary/test_vector_oracle.py tests/canonical/quaternary/test_kernel.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | QBP-02 | — | Reject malformed channel tables and silent smoothing | unit, property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_sampling.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | QBP-03 | — | Independent original-problem evaluation | exhaustive | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_evaluator.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | QBP-04 | — | Closed policy preflight and decoder truth boundary | unit, integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py tests/canonical/quaternary/test_public_execution.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-08 | — | Reject AMBP4 and unsupported recurrences | differential | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_mbp4.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-10–D-11 | — | Preserve immutable original syndrome; reject non-CSS aSCED | exhaustive, fixture | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_splitters.py tests/canonical/quaternary/test_asced_ensemble.py tests/canonical/quaternary/test_asced_overcomplete.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-12–D-13 | — | Pin native identity and preserve qualified missingness | integration, evidence | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Replace TBD identifiers after plans are final.*

## Wave 0 Requirements

- [ ] Create the `tests/canonical/quaternary/` package and files listed in the verification map, plus `test_schedules.py` and `conftest.py`.
- [ ] Establish hand algebra and exact-enumeration Pauli oracles independent of the production kernel.
- [ ] Pin source fixtures for the five-qubit `IIIYI` case and aSCED `H/H0/M` artifacts before implementation tests rely on them.
- [ ] Include manifest/ledger replay and tamper tests in `test_public_execution.py`; ensure each command selects at least one test once its file exists.
- [ ] Use the installed pytest environment; no framework installation is required.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Native aSCED source/build license and interface qualification | D-12 | Upstream repository packaging and native build may require human source interpretation | Inspect pinned checkout, build receipt, license evidence, and documented source divergences before labeling native output qualified. |

## Validation Sign-Off

- [ ] Every task has a runnable `<automated>` command or a Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 resolves all test-file references.
- [ ] No watch-mode flags are used.
- [ ] Per-task feedback is under the stated budget or an explicit exception is recorded.
- [ ] Set `nyquist_compliant: true` only after validation against the final plans and executed evidence.

**Approval:** pending
