---
phase: "05"
slug: "guided-and-perturbative-bp-interventions"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-30"
---

# Phase 05 — Validation Strategy

This is a test plan for intervention semantics and evidence integrity. A small B1 pilot remains `pilot_adaptation` and `not_assessed`; fixture success cannot establish a published-curve reproduction or decoder ranking.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <target> -x` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Feedback latency | Measure at Wave 0; keep each targeted run below two minutes |

## Sampling Rate

- After each task: run its targeted test file with `-x` and record the result.
- After each wave: run the full suite and the independent shortening/lifting oracle when transformations changed.
- Before phase verification: run the full suite, public preflight/run/verify on a deterministic fixture, replay the event ledger, execute the notebook, and inspect its standalone HTML export.
- Calibration and B1 pilot outcome sampling occur only after a frozen finite manifest, disjoint calibration/evaluation identities, and measured work caps.

## Per-Requirement Verification Map

| Requirement | Behavior | Automated target | Wave 0 |
|---|---|---|---|
| MOD-02 | BPGD selection, fixation, BP continuation, declared zero/tie/final rules, cap ledger | `tests/canonical/test_guided_decimation.py` | Create |
| MOD-03 | impulse trigger, fresh attempts, forced-one and separately labeled structural lift, stable minimum | `tests/canonical/test_impulse.py` | Create |
| INT-01 | freeze eligibility, lifetime, release, retry, cap | `tests/canonical/test_perturbative_interventions.py` | Create |
| INT-02 | oscillation rank, syndrome transform, certificate lift, original check | `tests/canonical/test_perturbative_interventions.py` | Create |
| INT-03 | sign target, posterior mutation, unchanged message trajectory until declared boundary | `tests/canonical/test_perturbative_interventions.py` | Create |
| INT-04 | root/branch reset, residual loop, finite caps, stable ties, explicit random-stream status | `tests/canonical/test_restart_execution.py` | Create |
| Public evidence | V5 manifest preflight, run, verifier, matched physical sample, source qualification | `tests/test_phase5_public_execution.py` | Create |
| Inspection | Shot-first notebook and synchronized HTML plot visibility without evidence mutation | `tests/test_phase5_notebook.py` | Create |

## Wave 0 Requirements

- [ ] Create the six named test files above and shared deterministic fixtures before controllers.
- [ ] Include algebraic shortening and lifting equivalence, all-fixed contradiction, invalid lift, and working-valid/original-invalid examples; keep `tools/validate_intervention_design.py --check` as an independent oracle.
- [ ] Include a microfixture per source variant with declared ambiguous rules and source/adaptation status.
- [ ] Exercise denied, failed, contradictory, invalid, cap-hit, and successful attempts; verify leaf work aggregates exactly once and denial does not mutate state.
- [ ] Add notebook/export smoke fixtures without running a B1 evaluation campaign.

## Manual-Only Checks

| Behavior | Why manual | Procedure |
|---|---|---|
| Source identity and unresolved choices | Papers and code may omit zero, tie, and final-round rules | Review source pins and qualification record before freezing presets; retain unresolved items visibly. |
| B1 pilot cap approval | Compute entitlement and representative cost are environment-specific | Record scheduler entitlement, four disjoint calibration shots, measured per-arm work, finite caps, and manifest digest before evaluation. |
| Plotly package identity | Research package-legitimacy check returned `SUS` | Verify the official package/release source and pin an accepted version before installation or HTML implementation. |

## Sign-Off

- [ ] Every task has a runnable automated target or depends on Wave 0 creation.
- [ ] No three consecutive tasks lack an automated verification command.
- [ ] Full suite, independent algebra oracle, public replay, and notebook export checks pass.
- [ ] Source ambiguities, unavailable references, and `not_assessed` pilot status remain explicit.
- [ ] Set `nyquist_compliant: true` and `status: validated` only after tests and evidence checks are complete.

**Approval:** pending.
