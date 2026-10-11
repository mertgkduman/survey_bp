---
phase: "08"
slug: "reproducible-campaigns-and-statistical-assessment"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-11"
---

# Phase 8 — Validation Strategy

This is the pre-execution test contract. The planner assigns task IDs and waves; each plan must name a focused automated verification command and update the task map below.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config | `pyproject.toml` |
| Quick run | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py tests/test_campaign_statistics.py` |
| Phase run | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_*.py tests/test_ledger.py tests/test_sampling.py tests/test_canonical_cli.py tests/canonical/test_profiling.py` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Feedback target | Focused tests within 60 seconds; phase run after each wave; full suite at the phase gate |

## Per-Requirement Verification Map

| Requirement | Planned verification | Test file | Current status |
|-------------|----------------------|-----------|----------------|
| LED-05 | Valid, incomplete, duplicate, conflicting, and corrupt shards; replay from retained evidence | `tests/test_campaign_shards.py` | Wave 0 |
| SIM-01 | Same physical sample identities across arm order and worker count; persisted-sample fallback | `tests/test_campaign_execution.py` | Wave 0 |
| SIM-02 | Local and synthetic Slurm runs consume the same plan and retain resource, timing, and work facts | `tests/test_campaign_execution.py` | Wave 0 |
| SIM-03 | Resume is exact missing-unit subtraction; source, environment, and rule drift are rejected | `tests/test_campaign_shards.py` | Wave 0 |
| STAT-01 | Manifest freezes targets, effects, methods, families, stopping, and decision rules | `tests/test_campaign_contracts.py` | Wave 0 |
| STAT-02 | Integer counts and exact rare-event intervals, including positive zero-failure upper bound | `tests/test_campaign_statistics.py` | Wave 0 |
| STAT-03 | Fixed and finite-look stopping, alpha allocation, overshoot, and partial-run evidence | `tests/test_campaign_statistics.py` | Wave 0 |
| STAT-04 | Source/table/figure and digitization bytes, calibration, precision, and missing sample n | `tests/test_campaign_targets.py` | Wave 0 |
| STAT-05 | Exact paired cells, difference intervals, multiplicity, denominator and acceptance rules | `tests/test_campaign_statistics.py` | Wave 0 |
| Operational gate | Representative decoder/replay throughput, ledger bytes, and shard-cost bound | `tests/test_campaign_profile_gate.py` | Wave 0 |

## Wave 0 Requirements

- [ ] Create the six test files above, using tiny deterministic terminal fixtures for shard corruption and reconstruction cases.
- [ ] Include adversarial fixed and adaptive stopping fixtures before implementing assessment decisions.
- [ ] Preserve existing canonical ledger, sampler, CLI, and profiling tests in the phase run.

## Sampling Rate

- After each task: run its focused test module and its relevant existing regression module.
- After each wave: run the phase command above.
- Before phase verification: run the full suite and a bounded local/HPC-equivalent campaign with retained replay and profiling receipts.
- No three consecutive tasks may lack an automated verification command.

## Manual-Only Verifications

Site allocation ceilings and production campaign budgets require later user/site input. The Phase 8 implementation is verified with bounded synthetic and representative local runs; it does not authorize a large publication campaign without the measured operational gate.

## Validation Sign-Off

- [ ] Every planned task has an automated command or a named Wave 0 prerequisite.
- [ ] Phase tests cover all nine mapped requirements.
- [ ] Phase and full suites pass.
- [ ] The bounded campaign and operational gate receipts replay from retained evidence.
- [ ] Set `nyquist_compliant: true` only after the execution audit.

**Approval:** pending execution
