---
phase: "03"
slug: "update-rules-and-scheduling"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-09-23"
finalized: "2026-09-24"
---

# Phase 03 — Validation Strategy

Planning contract only. Every status below is **pending**; no implementation check is represented as passed.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 in the current `.venv` |
| Python | 3.12.2 on the planning node |
| Config | `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["src"]` |
| Required prefix | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Notebook | `OMP_NUM_THREADS=1 MPLBACKEND=Agg .venv/bin/python scripts/execute_phase3_notebook.py --input notebooks/phase3-pilot-analysis.ipynb --output data/results/phase3-pilots/phase3-pilot-analysis.executed.ipynb` |
| Feedback target | Targeted task commands under 60 seconds; measure during execution and keep bounded pilot/notebook commands separate if longer |

## Sampling Rate

- After each task: run its targeted command; nonzero exit or zero collected tests fails the task.
- After each wave: run the full suite and retain failure evidence before repair.
- Before phase verification: full suite, public manifest/run/verify flows, algebraic artifact checks, bounded pilots, notebook execution, and qualified cluster run.
- Plan 03-09 is a blocking-human source-artifact checkpoint. A missing artifact is a block, never an approvable test result.

## Per-Task Verification Map

| Wave | Task | Requirements | Primary target / test type | Automated command summary | Creation dependency | Threats | Status |
|---:|---|---|---|---|---|---|---|
| 1 | 01-1 | UPD-01 | complete public MS tracer + oracle | update rules + canonical CLI, min-sum/historical selectors | creates `test_update_rules.py` | T-03-01–05 | pending |
| 1 | 07-1 | all noncluster pilot support | B1 algebra/identity | `test_phase3_codes.py -k b1` | creates test and artifact in task | T-03-27–30 | pending |
| 1 | 07-2 | all noncluster pilot support | HGP algebra/identity | `test_phase3_codes.py -k 'gallager or hgp'` | same owning plan | T-03-27–30 | pending |
| 1 | 07-3 | all noncluster pilot support | three-code inventory | phase3 codes + source artifact tests | artifacts from 07-1/2 | T-03-27–30 | pending |
| 2 | 02-1 | UPD-02 | NMS oracle/public | update/manifest/CLI alpha selectors | 01 public tracer | T-03-06,08,09 | pending |
| 2 | 02-2 | UPD-01–02 | generated schema/docs/tamper | manifest + CLI min-sum/NMS selectors | schema generated in task | T-03-06,08,09 | pending |
| 2 | 03-1 | SCH-02 | layered direct-API tracer | schedule semantics layer selector | creates `test_schedule_semantics.py` | T-03-10–13 | pending |
| 2 | 03-2 | SCH-03 | CN/VN serial semantics | serial/retry/isolation selectors | same owning plan | T-03-10–13 | pending |
| 2 | 03-3 | SCH-05 | RNG replay/metamorphic | random/refresh/sample selectors | same owning plan | T-03-10–13 | pending |
| 2 | 04-1 | SCH-04 | sRBP direct-API tracer | residual tracer/selection/tie selectors | creates `test_residual_schedule.py` | T-03-14–17 | pending |
| 2 | 04-2 | SCH-04 | lifecycle/property/rollback | full residual test module | same owning plan | T-03-14–17 | pending |
| 3 | 11-1 | UPD-03 | OMS public tracer | offset/beta/iteration-assignment selectors | Plans 02–04 iteration contracts | T-03-06–09 | pending |
| 3 | 11-2 | UPD-03, SCH-05 | generation/refresh/sample invariance | update/contracts/manifest/sampling | generator/refresh owned here | T-03-06–09 | pending |
| 4 | 05-1 | SCH-02–05 | atomic local/check transaction | budgets + schedule local/partial/rollback selectors | Plans 03/04/11 tests exist | T-03-18,19,21 | pending |
| 4 | 05-2 | SCH-02–05 | dual budgets/versioned evidence | budgets/work/schedule/residual/ledger modules | WorkVector and grammar owned here | T-03-18,19,21 | pending |
| 5 | 06-1 | SCH-02 | public layered tracer | contracts/manifest/CLI layered/v3/historical | Plan 05 engine/evidence | T-03-25–26 | pending |
| 5 | 12-1 | SCH-02–05 | deterministic reconstruction | ledger + CLI progress/work/tamper selectors | Plan 05 grammar exists | T-03-19 | pending |
| 5 | 12-2 | SCH-02–05 | bounded local traces | tracing + ledger quota/truth selectors | Plan 05 terminals exist | T-03-20–21 | pending |
| 6 | 13-1 | all noncluster | full public compatibility | contracts/manifest/CLI/ledger selectors | public layered tracer | T-03-25–26 | pending |
| 6 | 13-2 | all noncluster | complete schema/docs | manifest/CLI schema/documented selectors | all noncluster models admitted | T-03-26 | pending |
| 7 | 14-1 | SCH-06 | loader/security/unavailable | cluster/manifest artifact selectors | creates `test_cluster_schedule.py` | T-03-22–25 | pending |
| 7 | 14-2 | SCH-06 | deterministic qualifier CLI | cluster/CLI qualify/report selectors | loader exists | T-03-22–25 | pending |
| 8 | 08-1 | all noncluster | BB-144 matched pilot | phase3 pilot BB/matched selectors | public policies + artifacts | T-03-31,34 | pending |
| 8 | 08-2 | all noncluster | B1/HGP focused pilots | phase3 pilot B1/HGP/undefined selectors | 08 runner/test exist | T-03-31,34 | pending |
| 9 | 15-1 | all noncluster | notebook/dependency/kernel | phase3 pilot notebook/dependency selectors | retained Plan 08 evidence | T-03-32–SC | pending |
| 9 | 15-2 | all noncluster | tables/plots/labels | phase3 pilot report/label selectors | notebook executor exists | T-03-32–34 | pending |
| 10 | 09-1 | SCH-06 | authoritative qualification | qualifier CLI + qualified-author test | all independent outputs complete; user supplies authoritative files/link | T-03-35–37 | blocked pending artifact |
| 11 | 10-1 | SCH-06 | one-step cluster public tracer | cluster + CLI qualified greedy/tracer selectors | qualification `qualified=true` | T-03-38–41 | pending checkpoint |
| 12 | 16-1 | SCH-06 | exact complete traversal | cluster traversal/remaining/rollback selectors | Plan 10 tracer | T-03-39–41 | pending checkpoint |
| 12 | 16-2 | SCH-06 | work/progress/tamper reconstruction | cluster + manifest selectors | traversal passes | T-03-39–41 | pending checkpoint |
| 13 | 17-1 | SCH-06 | retained qualified pilot | manifest/CLI cluster verify/tamper + verify-run | Plan 16 passes | T-03-38,40 | pending checkpoint |

## Requirement and Edge Coverage

| Requirement | Required evidence |
|---|---|
| UPD-01 | MS sign/minimum/degree-one/repeated minima/saturation/adjacent-float/nonfinite oracle plus public tracer |
| UPD-02 | NMS scalar/indexed/generated assignments, alpha domain/precision, refresh and replay |
| UPD-03 | OMS zero floor/sign, beta exact/adjacent boundaries, invalid rejection and replay |
| SCH-02 | partition empty/boundary validation, membership/order/multiplicity, fresh later layers, local checks |
| SCH-03 | CN/VN distinction, deterministic order, retry/idempotency semantics, shot isolation, local checks |
| SCH-04 | source-lifecycle oracle, MS-predict/SPA-commit reset regression, full-scan tie/work, rollback |
| SCH-05 | three order refresh scopes, exact realized replay, unchanged physical samples and rollback |
| SCH-06 | strict author artifact qualification, exact greedy local unit/traversal, missing fail-closed, public verify-run |

The 13-item spec-less edge audit and 7 descriptor-less prohibitions are count-reconciled in `03-SOURCE-AUDIT.md`.

## Required Validation Layers

1. Independent small-graph mathematical oracles for MS/NMS/OMS and source-lifecycle residual behavior.
2. Direct production-API schedule fixtures before public manifest expansion.
3. Full public preflight/run/serialization/result/verify-run coverage after admission.
4. Reserve-before-mutation, exact work leaves, partial traversal, dual budgets, and setup/decode separation.
5. Purpose-separated RNG replay and matched physical-sample invariance.
6. Independent CSS algebra, ordering, logical provenance, and exact identity for BB-144/B1/HGP.
7. Strict imported-artifact security/compatibility and no-substitute cluster behavior.
8. Evidence-linked tables/plots/executed notebook under the pinned project-venv kernel.

## Wave 0 and Creation Contract

Existing pytest infrastructure is available. No empty scaffold task is required. New targets are created by their owning implementation tasks before invocation:

- Plan 01 Task 1: `tests/canonical/test_update_rules.py`
- Plan 03 Task 1: `tests/canonical/test_schedule_semantics.py`
- Plan 04 Task 1: `tests/canonical/test_residual_schedule.py`
- Plan 14 Task 1: `tests/canonical/test_cluster_schedule.py`
- Plan 07 Task 1: `tests/test_phase3_codes.py`
- Plan 08 Task 1: `tests/test_phase3_pilots.py`

## Manual and External Gates

- The only preplanned human action is Plan 03-09: supply authoritative Moradi Q-table/partition material or an authoritative release link after Plan 03-14 installs the qualifier. The executor performs all retrieval, preservation, hashing, qualification, and tests after the user supplies access.
- No external contacts or outbound messages are authorized.
- Human judgment at phase end reviews scientific labels and confirms pilots/notebook make no reproduction/ranking claim; it cannot override failed automated qualification.

## Validation Sign-Off

- [x] Every task has an automated command and observable `fails_when` condition.
- [x] Every new test path has an owning creation task.
- [x] Every UPD-01–03 and SCH-02–06 requirement maps to automated evidence.
- [x] No watch-mode command is used.
- [x] Source-dependent completion gates are explicit.
- [x] High security threats have mitigating tasks and no high threat is accepted.
- [ ] Task feedback latency measured during execution.
- [ ] Implementation tests executed.
- [ ] Authoritative cluster artifact qualified.
- [ ] Phase verification and human scientific-label review complete.

Approval: independent plan check passed 2026-09-24; all execution results pending.
