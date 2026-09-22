---
phase: "1"
slug: "evidence-registry-and-native-css-baseline"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-22"
---

# Phase 1 — Validation Strategy

> Execution feedback contract. This phase qualifies a local pilot and its evidence path; it does not assess a published curve.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | `pytest 9.0.3` locally; capture exact environment at execution |
| Config file | `pyproject.toml` to create in Wave 0 |
| Quick run | `python -m pytest -q tests/test_css_small.py tests/test_manifest.py tests/test_reference_smoke.py` after Wave 0 |
| Full suite | `python -m pytest -q` |
| Feedback target | Local quick suite under 60 seconds; measure during execution |

## Sampling Rate

- After each task commit, run the tests for that task and the quick suite once its files exist.
- After each wave, run the full suite.
- Before verification, run the full suite and the documented 32-shot pilot; inspect manifest, artifact, event, and outcome links.
- A package installation or HPC node change requires an environment identity check before interpreting the run.

## Per-Requirement Verification Map

| Requirement | Automated evidence | Planned test file | Exists |
|---|---|---|---|
| MAP-01–03 | Protocol required fields, dedup/revision/screening history reload, taxonomy and unresolved claims | `tests/test_evidence.py` | No — Wave 0 |
| REG-01–02 | Strict schema and preflight reject missing settings, extra fields, bad rates, missing files, changed hashes before decoder invocation | `tests/test_manifest.py` | No — Wave 0 |
| REG-03–04 | Pinned native BP syndrome smoke; pilot lineage cannot become statistically assessed merely by execution | `tests/test_reference_smoke.py` | No — Wave 0 |
| CSS-01–02 | GF(2) checks/logicals, pairing, dimensions, ordered semantic hashes, row/bit mutation rejection | `tests/test_css_small.py` | No — Wave 0 |
| CSS-03 | Fixed-seed X-only and separate X/Z syndrome conventions; decoder receives no hidden truth | `tests/test_sampling.py` | No — Wave 0 |
| CSS-04 | Exact, stabilizer-equivalent, logical-failure, invalid-syndrome outcomes checked against independent row-space and logical-action methods | `tests/test_css_small.py` | No — Wave 0 |
| LED-01 | Success, nonconvergence, exception, and interrupted begin reconcile to one terminal shot row each | `tests/test_ledger.py` | No — Wave 0 |

## Wave 0 Requirements

- [ ] Create `pyproject.toml`, the package skeleton, small CSS fixtures, and the seven listed test files before referencing runnable verify commands.
- [ ] Pin and record the environment actually used; verify the native adapter API against the installed version.
- [ ] Use an isolated install only after the package legitimacy checkpoint recorded in RESEARCH.md.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Procedure |
|---|---|---|---|
| Source extraction fidelity | MAP-01–03 | Published figures and variant descriptions require editorial review | Compare seed records with pinned paper revisions and page/figure anchors; record ambiguity. |
| Native artifact identity | CSS-01–02, REG-03 | Source code may generate logical rows dynamically | Compare frozen rows and parameters with pinned upstream commit, then run independent algebraic checks. |
| Pilot evidence label | REG-04 | A pilot must not imply reproduction | Inspect command output, manifest, registry status, and report for `pilot_adaptation` and `not_assessed`. |

## Validation Sign-Off

- [ ] Every task has an automated check or a declared Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Full suite and pilot evidence review pass.
- [ ] Set `nyquist_compliant: true` only after validation audit.

**Approval:** pending execution and audit
