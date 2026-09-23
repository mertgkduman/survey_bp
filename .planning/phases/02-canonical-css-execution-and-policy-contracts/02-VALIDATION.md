---
phase: "02"
slug: "canonical-css-execution-and-policy-contracts"
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| 02-01-T1 | 01 | 1 | ENG-01 | T-02-01, T-02-03 | Independent evaluation occurs after candidate selection; replay/concurrency produce one terminal | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py` | ✅ | ✅ green |
| 02-01-T2 | 01 | 1 | ENG-05 | T-02-01 | Hostile policies cannot reach hidden truth; lineage ties and empty selection are deterministic | adversarial/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_truth_boundary.py tests/test_canonical_cli.py` | ✅ | ✅ green |
| 02-02-T1 | 02 | 2 | ENG-02 | T-02-05, T-02-08 | Invalid policy compositions, arbitrary runtime imports, and v1 semantic drift are rejected | unit/adversarial | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/test_manifest.py` | ✅ | ✅ green |
| 02-02-T2 | 02 | 2 | ENG-06 | T-02-06, T-02-07 | Lifecycle decisions are ownership-checked and each policy has ordered source/procedure evidence | schema/unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_contracts.py tests/canonical/test_policy_evidence.py` | ✅ | ✅ green |
| 02-03-T1 | 03 | 2 | ENG-04 | T-02-09, T-02-10, T-02-11 | Nonfinite values fail explicitly and materialized numerical conventions are deterministic | analytic/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py` | ✅ | ✅ green |
| 02-03-T2 | 03 | 2 | SCH-01 | T-02-12 | Edge ordering cannot alter the double-buffered flooding update or proposed work | unit/golden | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py tests/canonical/test_flooding.py` | ✅ | ✅ green |
| 02-05-T1 | 05 | 3 | ENG-05 | T-02-17, T-02-20 | Immutable lineage and candidate retention preserve ancestry without truth-feedback mutation | unit/adversarial | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/canonical/test_truth_boundary.py` | ✅ | ✅ green |
| 02-05-T2 | 05 | 3 | LED-02 | T-02-18, T-02-19 | Trace filtering, path confinement, and truncation never change decoded output | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_tracing.py tests/test_ledger.py` | ✅ | ✅ green |
| 02-04-T1 | 04 | 4 | ENG-03 | T-02-13, T-02-14 | Count budgets cannot overrun/partially commit; wall deadlines stop at declared boundaries with overshoot evidence | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py` | ✅ | ✅ green |
| 02-04-T2 | 04 | 4 | LED-03 | T-02-15, T-02-16 | Every typed work category reduces from unique leaves while zero and missingness remain distinct | unit/property | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_budgets.py tests/canonical/test_work_accounting.py` | ✅ | ✅ green |
| 02-06-T1 | 06 | 5 | LED-04 | T-02-21 | Native observed and unavailable metric variants reject fabricated zero and malformed values | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py` | ✅ | ✅ green |
| 02-06-T2 | 06 | 5 | LED-04 | T-02-22, T-02-23 | Unobservable native counters preserve null, reason, scope, and availability denominators | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_reference_smoke.py tests/test_ledger.py` | ✅ | ✅ green |
| 02-07-T1 | 07 | 5 | LED-03 | T-02-25, T-02-28 | Profilers expose only allowlisted typed metrics and explicit unavailability | unit/security | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_profiling.py` | ✅ | ✅ green |
| 02-07-T2 | 07 | 5 | LED-03 | Representative/tail cohorts stay distinct and profiled replays require semantic agreement | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_profiling.py tests/canonical/test_tracing.py` | ✅ | ✅ green |
| 02-08-T1 | 08 | 6 | ENG-02, ENG-04 | T-02-29, T-02-32 | Canonical preflight rejects changed, malformed, oversized, or unverified input before execution | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_manifest.py tests/test_canonical_cli.py` | ✅ | ✅ green |
| 02-08-T2 | 08 | 6 | ENG-01, ENG-03, ENG-05, LED-02, LED-03, LED-04 | T-02-30, T-02-31 | Public execution preserves the truth boundary, durable ownership, typed failures, and verified links | integration/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py tests/test_reference_smoke.py tests/test_ledger.py` | ✅ | ✅ green |
| 02-08-T3 | 08 | 6 | ENG-01, LED-02, LED-03 | T-02-31 | Checked result reconstructs from immutable terminal evidence and remains idempotent | artifact/CLI | `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development` | ✅ | ✅ green |
| 02-09-T1 | 09 | 7 | DOC-01 | T-02-33, T-02-34 | Tutorial runtime commands use the validated boundary; install text is checked without package mutation | docs smoke/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py::test_documented_tutorial tests/canonical/test_policy_evidence.py` | ✅ | ✅ green |
| 02-09-T2 | 09 | 7 | DOC-01 | T-02-33, T-02-35 | Strategy/register fields match implementation and preserve provisional, non-population labels | docs contract/unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_policy_evidence.py tests/canonical/test_profiling.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Test Creation Requirements

- [x] Plan 01 created `tests/test_canonical_cli.py` and `tests/canonical/test_truth_boundary.py` with the leading tracer.
- [x] Plan 02 created `tests/canonical/test_contracts.py` and `tests/canonical/test_policy_evidence.py`.
- [x] Plan 03 created `tests/canonical/conftest.py`, `tests/canonical/test_numerics.py`, and `tests/canonical/test_flooding.py`.
- [x] Plan 04 created `tests/canonical/test_budgets.py` and `tests/canonical/test_work_accounting.py`.
- [x] Plan 05 created `tests/canonical/test_tracing.py` and `tests/fixtures/canonical-semantic-events.json`.
- [x] Plan 07 created `tests/canonical/test_profiling.py`.
- [x] Plans 08–09 expanded the public CLI and executable tutorial tests.

Framework install: none; reuse the approved pytest environment.

---

## Manual-Only Verifications

All phase behaviors have automated verification. Documentation readability remains subject to human review but does not replace the executable tutorial test.

---

## Validation Sign-Off

- [x] Every finalized plan task has an `<automated>` verify command
- [x] Sampling continuity: no 3 consecutive tasks without automated verification
- [x] Every missing test reference has a creating plan before its first verification use
- [x] No watch-mode flags
- [x] Task-level targeted checks remain under 30 seconds; the full suite completed in 45.93 seconds.
- [x] `nyquist_compliant: true` set in frontmatter after validation

**Approval:** validated on 2026-09-23 — 126 tests passed and the checked canonical result verified.

## Validation Audit 2026-09-23

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
