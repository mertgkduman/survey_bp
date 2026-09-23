---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: planned
nyquist_compliant: true
wave_0_complete: false
created: "2026-09-22"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| **Quick run command** | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <target-test-file>` |
| **Full suite command** | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~23 seconds for the existing suite |

---

## Sampling Rate

- **After every task commit:** Run the targeted test file for the changed contract or subsystem.
- **After every plan wave:** Run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`.
- **Before `$gsd-verify-work`:** The full suite, documented tutorial, and ledger reconciliation must be green.
- **Max feedback latency:** 30 seconds for task-level checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-T1 | 01 | 1 | ENG-01 | T-02-01, T-02-03 | Independent evaluation occurs after candidate selection; replay/concurrency produce one terminal | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py` | ❌ Plan 01 | ⬜ pending |
| 02-02-T1 | 02 | 2 | ENG-02 | T-02-05, T-02-06 | Invalid policy compositions and arbitrary runtime imports are rejected | unit/adversarial | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py` | ❌ Plan 02 | ⬜ pending |
| 02-04-T1 | 04 | 3 | ENG-03 | T-02-13, T-02-14 | Scoped budgets cannot overrun or partially commit work | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py` | ❌ Plan 04 | ⬜ pending |
| 02-03-T1 | 03 | 2 | ENG-04 | T-02-09, T-02-10 | Nonfinite values fail explicitly and numerical conventions are deterministic | analytic/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py` | ❌ Plan 03 | ⬜ pending |
| 02-01-T2 | 01 | 1 | ENG-05 | T-02-01 | Policies cannot inspect hidden truth and selection precedes evaluation | adversarial/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_truth_boundary.py` | ❌ Plan 01 | ⬜ pending |
| 02-02-T2 | 02 | 2 | ENG-06 | T-02-06 | Implemented policies declare source, procedure, and deterministic invariants | schema/unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_policy_evidence.py` | ❌ Plan 02 | ⬜ pending |
| 02-03-T2 | 03 | 2 | SCH-01 | T-02-12 | Edge ordering cannot alter a flooding update | unit/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_flooding.py` | ❌ Plan 03 | ⬜ pending |
| 02-05-T2 | 05 | 3 | LED-02 | T-02-18, T-02-19 | Trace filtering and truncation never change decoded output | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py` | ❌ Plan 05 | ⬜ pending |
| 02-04-T2 | 04 | 3 | LED-03 | T-02-15, T-02-16 | Leaf work deltas reconcile exactly to ancestor and root summaries | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_work_accounting.py` | ❌ Plan 04 | ⬜ pending |
| 02-06-T2 | 06 | 4 | LED-04 | T-02-21, T-02-23 | Unobservable native counters remain missing with an explicit reason | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py` | ✅ extend in Plan 06 | ⬜ pending |
| 02-09-T1 | 09 | 6 | DOC-01 | T-02-33, T-02-34 | Documented tutorial uses the same validated execution boundary and evidence labels | docs smoke/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial` | ❌ Plan 09 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Test Creation Requirements

- [ ] Plan 01 creates `tests/test_canonical_cli.py` and `tests/canonical/test_truth_boundary.py` with the leading tracer.
- [ ] Plan 02 creates `tests/canonical/test_contracts.py` and `tests/canonical/test_policy_evidence.py`.
- [ ] Plan 03 creates `tests/canonical/conftest.py`, `tests/canonical/test_numerics.py`, and `tests/canonical/test_flooding.py`.
- [ ] Plan 04 creates `tests/canonical/test_budgets.py` and `tests/canonical/test_work_accounting.py`.
- [ ] Plan 05 creates `tests/canonical/test_tracing.py` and `tests/fixtures/canonical-semantic-events.json`.
- [ ] Plan 07 creates `tests/canonical/test_profiling.py`.
- [ ] Plans 08–09 expand the public CLI and executable tutorial tests.

Framework install: none; reuse the approved pytest environment.

---

## Manual-Only Verifications

All phase behaviors have automated verification. Documentation readability remains subject to human review but does not replace the executable tutorial test.

---

## Validation Sign-Off

- [x] Every finalized plan task has an `<automated>` verify command
- [x] Sampling continuity: no 3 consecutive tasks without automated verification
- [x] Every missing test reference has a creating plan before its first verification use
- [ ] No watch-mode flags
- [ ] Task-level feedback latency remains under 30 seconds
- [x] `nyquist_compliant: true` set in frontmatter after validation

**Approval:** pending
