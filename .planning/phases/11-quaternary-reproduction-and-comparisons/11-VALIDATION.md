---
phase: "11"
slug: "quaternary-reproduction-and-comparisons"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-14"
---

# Phase 11 — Validation Strategy

> Feedback and evidence contract for quaternary reproduction and matched comparisons. Plan task IDs and exact commands are assigned when the Phase 11 plans are written.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary tests/test_campaign_statistics.py tests/test_campaign_execution.py -x` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure on the execution node before setting the feedback latency ceiling. |

## Sampling Rate

- After every task commit: run the narrow new or changed test file and its closest existing analog.
- After every plan wave: run the quick quaternary and campaign suite.
- Before `$gsd-verify-work`: run the full suite and audit replay and source-target receipts.
- Max feedback latency: measure in Wave 0; split narrow tests if the task loop exceeds 30 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| Assign in plans | TBD | TBD | QEV-01 | TBD | Reject incomplete or mutated source targets | unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_targets.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-01 | TBD | Preserve fidelity, discrepancy, stopping, and denominator evidence | integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-01 | TBD | Reproduce deterministic MBP4 Figures 8–9 mechanism | regression | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_mbp4_target.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-02 | TBD | One Pauli sample feeds both arms while binary inputs expose only exact marginals | integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-02 | TBD | Retain partial nonconvergence, three frozen rows, and all-shot denominator | unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-02 | TBD | Cross-point paired effects and simultaneous exact bounds match hand counts | unit | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -x` | ❌ W0 | ⬜ pending |
| Assign in plans | TBD | TBD | QEV-01, QEV-02 | TBD | Typed work includes every round and path; production dispatch remains gated | integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py tests/test_phase11_quaternary_campaign.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

## Wave 0 Requirements

- [ ] `tests/test_phase11_source_targets.py` — exact target qualification, missing metadata, and tamper cases.
- [ ] `tests/test_phase11_quaternary_campaign.py` — Pauli campaign sample identity, merge, replay, fidelity, and typed work.
- [ ] `tests/test_phase11_joint_separate.py` — exact marginal boundary, partial nonconvergence, and GB46/BB72 pairing.
- [ ] `tests/test_phase11_correlation_statistics.py` — frozen contrasts and simultaneous exact intervals.
- [ ] `tests/test_phase11_resource_gate.py` — production denial until resource and accounting qualification.
- [ ] `tests/canonical/quaternary/test_phase11_mbp4_target.py` — deterministic source mechanism.
- [ ] Native injected-input verification is conditional on separately qualified rights and modified source scope.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Paper figure digitization and source settings | QEV-01 | The paper's plotted coordinates and some metadata need source interpretation. | Record extraction method, reviewer, coordinates, settings, uncertainty, and tolerance before assessment; retain unresolved items as blocked metadata. |
| Native aSCED source modification approval | QEV-01 | Existing bounded approval forbids algorithm or channel source changes. | Review the proposed minimal diff and rights scope; only then qualify an instrumented native identity and matched injected-error route. |
| Publication-scale resource authorization | QEV-01, QEV-02 | Site ceilings and scheduler accounting are not yet measured. | Review measured profile, site limits, accounting, frozen manifest, and explicit authorization before dispatch. |

## Validation Sign-Off

- [ ] All plan tasks have automated verification or a documented Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 covers every new test path before implementation acceptance.
- [ ] No watch mode flags.
- [ ] Feedback latency is measured and bounded.
- [ ] Set `nyquist_compliant: true` only after the plan map and tests are validated.

**Approval:** pending
