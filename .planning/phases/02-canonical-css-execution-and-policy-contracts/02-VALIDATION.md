---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: draft
nyquist_compliant: false
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
| TBD | TBD | TBD | ENG-01 | — | Independent evaluation occurs after candidate selection | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ENG-02 | — | Invalid policy compositions and hidden-state access are rejected | unit/adversarial | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ENG-03 | — | Scoped budgets cannot overrun or partially commit work | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ENG-04 | — | Nonfinite values fail explicitly and numerical conventions are deterministic | analytic/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ENG-05 | — | Policies cannot inspect hidden truth | adversarial/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_truth_boundary.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ENG-06 | — | Implemented policies declare source, procedure, and deterministic invariants | schema/unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_policy_evidence.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | SCH-01 | — | Edge ordering cannot alter a flooding update | unit/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_flooding.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | LED-02 | — | Trace filtering and truncation never change decoded output | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | LED-03 | — | Leaf work deltas reconcile exactly to ancestor and root summaries | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_work_accounting.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | LED-04 | — | Unobservable native counters remain missing with an explicit reason | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py` | ✅ extend | ⬜ pending |
| TBD | TBD | TBD | DOC-01 | — | Documented tutorial uses the same validated execution boundary | docs smoke/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/canonical/conftest.py` — tiny graph/CSS fixtures, analytic message helpers, and manifest builders
- [ ] `tests/canonical/test_contracts.py` — ENG-02 and ENG-06 contract tests
- [ ] `tests/canonical/test_policy_evidence.py` — ENG-06 source/procedure/invariant checks
- [ ] `tests/canonical/test_numerics.py` — ENG-04 numerical oracles and failure cases
- [ ] `tests/canonical/test_flooding.py` — SCH-01 flooding schedule and ordering checks
- [ ] `tests/canonical/test_budgets.py` — ENG-03 scoped-budget tests
- [ ] `tests/canonical/test_work_accounting.py` — LED-03 work reconciliation tests
- [ ] `tests/canonical/test_truth_boundary.py` — ENG-05 hidden-truth adversarial tests
- [ ] `tests/canonical/test_tracing.py` — LED-02 trace and truncation tests
- [ ] `tests/test_canonical_cli.py` — ENG-01 and DOC-01 vertical-slice tests
- [ ] `tests/fixtures/` — canonical manifest and golden semantic events/traces

Framework install: none; reuse the approved pytest environment.

---

## Manual-Only Verifications

All phase behaviors have automated verification. Documentation readability remains subject to human review but does not replace the executable tutorial test.

---

## Validation Sign-Off

- [ ] Every finalized plan task has an `<automated>` verify command or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification
- [ ] Wave 0 covers all missing test references
- [ ] No watch-mode flags
- [ ] Task-level feedback latency remains under 30 seconds
- [ ] `nyquist_compliant: true` set in frontmatter after validation

**Approval:** pending
