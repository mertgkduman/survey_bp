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
| MOD-02 | BPGD selection, fixation, BP continuation, declared zero/tie/final rules, cap ledger | `tests/canonical/test_guided_decimation.py` | Plan 05-01 tracer, expand 05-04 |
| MOD-03 | impulse trigger, fresh attempts, forced-one and separately labeled structural lift, stable minimum | `tests/canonical/test_impulse.py` | Create in Plan 05-05 |
| INT-01 | freeze eligibility, lifetime, release, retry, cap | `tests/canonical/test_perturbative_interventions.py` | Create in Plan 05-06 |
| INT-02 | oscillation rank, syndrome transform, certificate lift, original check | `tests/canonical/test_perturbative_interventions.py` | Create in Plan 05-06 |
| INT-03 | sign target, posterior mutation, unchanged message trajectory until declared boundary | `tests/canonical/test_perturbative_interventions.py` | Create in Plan 05-06 |
| INT-04 | root/branch reset, residual loop, finite caps, stable ties, explicit random-stream status | `tests/canonical/test_restart_execution.py` | Create in Plan 05-07 |
| Cross-code fixtures | Deterministic BB-144 and HGP algebra, lift, source qualification, and compatible policy transitions without code-wide sampling | `tests/canonical/test_phase5_code_fixtures.py` | Create in Plan 05-12 |
| Public evidence | V5 manifest preflight, run, verifier, matched physical sample, source qualification | `tests/test_phase5_public_execution.py` | Create in Plan 05-08 |
| Inspection | Shot-first notebook and synchronized HTML plot visibility without evidence mutation | `tests/test_phase5_notebook.py` | Create in Plan 05-11 |

## Test Creation and Ordering Requirements

- [ ] Plan 05-01 creates the production BPGD tracer test. Each later controller/public/notebook plan creates its own named test path before implementation in the same TDD task; no command may reference a path that its task or a dependency does not create.
- [ ] Include algebraic shortening and lifting equivalence, all-fixed contradiction, invalid lift, and working-valid/original-invalid examples; keep `tools/validate_intervention_design.py --check` as an independent oracle.
- [ ] Include a microfixture per source variant with declared ambiguous rules and source/adaptation status.
- [ ] Exercise denied, failed, contradictory, invalid, cap-hit, and successful attempts; verify leaf work aggregates exactly once and denial does not mutate state.
- [ ] Add notebook/export smoke fixtures without running a B1 evaluation campaign.
- [ ] Plan 05-12 creates executable deterministic BB-144 and HGP fixtures. Each code exercises exact artifact identity, fixed-coordinate algebra, syndrome-certificate lift/original rejection, and every compatible Phase 5 controller with fixed observations and finite single-path caps; unavailable/incompatible source presets are asserted as explicit status rather than sampled.

## Deterministic Cross-Code Commands

- BB-144 algebra and compatible policy fixtures: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase5_code_fixtures.py -k 'bb144 and (algebra or bpgd or impulse or freezing or syndrome_flip or sign_flip or restart)' -x`
- HGP algebra and compatible policy fixtures: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase5_code_fixtures.py -k 'hgp and (algebra or bpgd or impulse or freezing or syndrome_flip or sign_flip or restart)' -x`
- These commands are deterministic fixture checks. They do not launch code-wide comparison pilots or establish performance, source-curve, or ranking claims.

## Manual-Only Checks

| Behavior | Why manual | Procedure |
|---|---|---|
| Source identity and unresolved choices | Papers and code may omit zero, tie, and final-round rules | Review source pins and qualification record before freezing presets; retain unresolved items visibly. |
| Plotly package identity | Research package-legitimacy check returned `SUS` | Verify the official package/release source and pin an accepted version before installation or HTML implementation. |

## Sign-Off

- [ ] Every task has a runnable automated target or depends on Wave 0 creation.
- [ ] No three consecutive tasks lack an automated verification command.
- [ ] Full suite, independent algebra oracle, public replay, and notebook export checks pass.
- [ ] Source ambiguities, unavailable references, and `not_assessed` pilot status remain explicit.
- [ ] Set `nyquist_compliant: true` and `status: validated` only after tests and evidence checks are complete.

**Approval:** pending.
