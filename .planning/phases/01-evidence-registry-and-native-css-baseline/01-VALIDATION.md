---
phase: "1"
slug: "evidence-registry-and-native-css-baseline"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-22"
---

# Phase 1 — Validation Strategy

> Execution feedback contract. This phase qualifies a local pilot and its evidence path; it does not assess a published curve.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | `pytest 9.0.3` locally; capture exact environment at execution |
| Config file | `pyproject.toml` |
| Quick run | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_css_small.py tests/test_manifest.py tests/test_reference_smoke.py` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Observed full run | 66 passed in 24.22 seconds on 2026-09-22 |

## Sampling Rate

- After each task commit, run the tests for that task and the quick suite once its files exist.
- After each wave, run the full suite.
- Before verification, run the full suite and the documented 32-shot pilot; inspect manifest, artifact, event, and outcome links.
- A package installation or HPC node change requires an environment identity check before interpreting the run.

## Per-Requirement Verification Map

| Requirement | Automated evidence | Planned test file | Exists |
|---|---|---|---|
| MAP-01–03 | Protocol, event history, anchored source inventory, taxonomy, and maturity-safe queries | `tests/test_evidence.py`, `tests/test_source_artifact.py` | Yes — passing |
| REG-01–02 | Strict schema, immutable preflight, identity and path mutation rejection | `tests/test_manifest.py` | Yes — passing |
| REG-03–04 | Native BP smoke, public CLI subprocess, pilot labels and maturity constraints | `tests/test_reference_smoke.py`, `tests/test_phase1_cli.py`, `tests/test_evidence.py` | Yes — passing |
| CSS-01–02 | GF(2) checks/logicals, pairing, ordered hashes, frozen source artifact | `tests/test_css_small.py`, `tests/test_source_artifact.py` | Yes — passing |
| CSS-03 | Identified deterministic sampling, X/Z orientation and decoder-visible boundary | `tests/test_sampling.py`, `tests/test_reference_smoke.py` | Yes — passing |
| CSS-04 | Four independent evaluator outcomes and pilot ledger outcome reconstruction | `tests/test_css_small.py`, `tests/test_phase1_cli.py` | Yes — passing |
| LED-01 | Durable final records, interruption repair, idempotency and 32-shot reconciliation | `tests/test_ledger.py`, `tests/test_phase1_cli.py` | Yes — passing |

## Wave 0 Requirements

- [x] Create `pyproject.toml`, the package skeleton, and contract tests before implementation.
- [x] Record the observed environment and verify the installed native adapter API.
- [x] Install new packages in the isolated environment only after the Plan 02 human checkpoint.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Procedure |
|---|---|---|---|
| Source extraction fidelity | MAP-01–03 | Published figures and variant descriptions require editorial review | Compare seed records with pinned paper revisions and page/figure anchors; record ambiguity. |
| Native artifact identity | CSS-01–02, REG-03 | Source code may generate logical rows dynamically | Compare frozen rows and parameters with pinned upstream commit, then run independent algebraic checks. |
| Pilot evidence label | REG-04 | A pilot must not imply reproduction | Inspect command output, manifest, registry status, and report for `pilot_adaptation` and `not_assessed`. |

## Validation Sign-Off

- [x] Every task has an automated check or a declared Wave 0 dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] Full suite and pilot `verify-run` pass.
- [x] Nyquist audit completed; manual source judgments remain listed above.

**Approval:** automated coverage validated 2026-09-22; source-fidelity judgments remain manual.

## Validation Audit 2026-09-22

| Metric | Count |
|---|---:|
| Phase requirements with automated coverage | 12 |
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

The audit added `tests/test_phase1_cli.py` to exercise documented preflight and
run verification in fresh subprocesses. The resulting full suite passed 66 tests.
