---
phase: "03"
slug: "update-rules-and-scheduling"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-23"
---

# Phase 03 — Validation Strategy

Planning contract only: implementation checks have not been run. The planner must finalize the per-task map against the completed research and executable plans.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3, observed in the current `.venv` |
| Python | 3.12.2, observed on the current node |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_numerics.py tests/canonical/test_flooding.py` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure during execution; no new Phase 3 runtime measurement yet |

## Sampling Rate

- After each task, run its targeted automated check; nonzero exit or zero collected tests is a failure.
- After each wave, run the full suite and retain failures before repair.
- Before phase verification, run the full suite, the public manifest/run/verify flows, bounded matched pilots, and notebook execution.
- Target task feedback latency is under 60 seconds. Keep bounded pilot and notebook checks separately scheduled if they exceed that target.

## Required Validation Layers

1. Independent hand-calculated and small-graph oracles for MS/NMS/OMS, including sign, zero, repeated minima, degree-one behavior, clipping, and parameter domain boundaries.
2. Step-by-step fresh/stale message visibility fixtures for each local schedule unit; convergence at every selected local boundary; flooding regression at the historical complete-sweep boundary.
3. Budget reservation before mutation, exact leaf-work accounting, and partial traversal evidence; separate scheduler/residual/priority/check work and setup/decoding runtime.
4. Replay tests for parameter and schedule refresh scopes, graph assignment identity, independent RNG streams, and unchanged matched physical-error samples.
5. Source procedure and imported-artifact qualification. Cluster fixtures do not establish support if required learned artifacts are absent.
6. Independent CSS algebra, matrix ordering, ordered logical basis provenance, and identity checks for BB-144, B1, and the requested HGP family.
7. Public preflight rejection of unsupported combinations and malformed imports; ledger verification rejects rehashed inconsistent semantic claims while respecting nondeterministic measurement fields.
8. Evidence-linked tables, plots, and an executable notebook with explicit pilot/adaptation assessment, retained denominator rules, and bounded representative traces.

## Per-Task Verification Map

The planner will replace this paragraph with the final task IDs, waves, requirements, threat references, secure behaviors, test types, automated commands, creation dependencies, and pending execution statuses. Every UPD-01–03 and SCH-02–06 requirement must be represented.

## Wave 0 Requirements

Existing pytest infrastructure is available. New test modules must be created in their owning implementation tasks before verification commands invoke them; the final map must identify every planned file and dependency. Do not add empty test stubs solely to satisfy a path probe.

## Manual-Only Verifications

Source-artifact acquisition and the scientific labeling of unavailable artifacts require documented provenance review. If an external cluster parameter artifact remains unavailable, retain the explicit checkpoint and do not claim SCH-06 or phase execution complete. No new source contact or outbound message is authorized by this plan.

## Validation Sign-Off

- [ ] Every task has an automated verification or an explicit prerequisite.
- [ ] No three consecutive implementation tasks lack automated feedback.
- [ ] Every new verification target has an owning creation task.
- [ ] No watch-mode command is used.
- [ ] Task feedback latency has been measured.
- [ ] Source-dependent acceptance gates are explicit.
- [ ] `nyquist_compliant: true` is justified by the finalized validation contract.

Approval: pending plan verification; execution results remain pending.
