---
phase: "08"
slug: "reproducible-campaigns-and-statistical-assessment"
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| LED-05 | 08-01 T1; 08-05 T1-T2; 08-06 T1-T2; 08-11 T1; 08-14 T2 — durable validation, exact merge, replay, resume, and reconstruction | `tests/test_campaign_shards.py` | Pass |
| SIM-01 | 08-04 T1-T2; 08-09 T1-T2; 08-14 T2 — arm/worker invariance and persisted-sample fallback | `tests/test_campaign_execution.py` | Pass |
| SIM-02 | 08-09 T1; 08-10 T1-T2; 08-12 T2; 08-14 T2 — one plan across local/Slurm with resource, timing, and work facts | `tests/test_campaign_execution.py` | Pass |
| SIM-03 | 08-02 T1-T2; 08-06 T1-T2; 08-10 T2; 08-12 T1 — exact resume and identity/rule/dependency drift rejection | `tests/test_campaign_shards.py` | Pass |
| STAT-01 | 08-02 T1-T2; 08-03 T1-T2; 08-07 T1; 08-11 T1 — prespecified targets, effects, methods, families, stopping, and decisions | `tests/test_campaign_contracts.py` | Pass |
| STAT-02 | 08-01 T1; 08-07 T1; 08-11 T2 — integer counts and exact rare-event boundary intervals | `tests/test_campaign_statistics.py` | Pass |
| STAT-03 | 08-02 T2; 08-06 T2; 08-07 T2; 08-09 T2 — fixed/finite looks, alpha, overshoot, and partial evidence | `tests/test_campaign_statistics.py` | Pass |
| STAT-04 | 08-03 T1-T2; 08-07 T1; 08-11 T1 — source and digitization bytes, calibration, precision, and missing sample n | `tests/test_campaign_targets.py` | Pass |
| STAT-05 | 08-02 T2; 08-08 T1-T2; 08-11 T2 — paired cells, intervals, multiplicity, denominators, and acceptance | `tests/test_campaign_statistics.py` | Pass |
| Operational gate | 08-13 T1-T2; 08-14 T1-T2 — representative decoder/replay throughput, storage, scheduler cost, and authorization | `tests/test_campaign_profile_gate.py` | Pass; production gate denies without site ceilings |

## Wave 0 Requirements

- [x] Create the six test files above, using tiny deterministic terminal fixtures for shard corruption and reconstruction cases.
- [x] Include adversarial fixed and adaptive stopping fixtures before implementing assessment decisions.
- [x] Preserve existing canonical ledger, sampler, CLI, and profiling tests in the phase run.

## Sampling Rate

- After each task: run its focused test module and its relevant existing regression module.
- After each wave: run the phase command above.
- Before phase verification: run the full suite and a bounded local/HPC-equivalent campaign with retained replay and profiling receipts.
- No three consecutive tasks may lack an automated verification command.

## Manual-Only Verifications

Site allocation ceilings and production campaign budgets require later user/site input. The Phase 8 implementation is verified with bounded synthetic and representative local runs; it does not authorize a large publication campaign without the measured operational gate.

## Validation Sign-Off

- [x] Every planned task has an automated command or a named Wave 0 prerequisite.
- [x] Phase tests cover all nine mapped requirements.
- [x] Phase suite: 95 passed; full suite: 1125 passed, 1 skipped.
- [x] The bounded campaign and operational gate receipts replay from retained evidence.
- [x] Set `nyquist_compliant: true` after the execution audit.

**Approval:** automated evidence complete; production campaign authorization remains denied until measured site ceilings are supplied.

## Validation Audit 2026-10-11

| Metric | Count |
|--------|-------|
| Requirements with automated coverage | 9 |
| Coverage gaps found | 0 |
| Gaps resolved | 0 |
| Escalated | 0 |

The requirement map above was checked against the Phase 8 test modules and all fourteen plan summaries. The targeted campaign suite passed 95 tests, the full suite passed 1,125 tests with one skip, and the retained operational gate verified its receipts. Site ceilings remain a separate production authorization condition.
