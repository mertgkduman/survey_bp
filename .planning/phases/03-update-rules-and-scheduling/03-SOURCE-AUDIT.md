# Phase 03 Source, Probe, and Artifact Coverage Audit

Planning audit only. Implementation and validation remain pending execution.

## Multi-Source Coverage

| Source | ID | Required outcome | Plans | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Researcher varies requested update/schedule policies without changing the canonical engine or losing semantic/cost visibility | 01–17 | COVERED | Tracer-first engine, public expansions, pilots/reporting, then the external cluster gate. |
| REQ | UPD-01 | Min-sum equation and small-graph behavior | 01, 02, 13, 08, 15 | COVERED | Complete public tracer, schema, compatibility, pilot, reporting. |
| REQ | UPD-02 | Normalized min-sum parameters and small-graph behavior | 02, 13, 08, 15 | COVERED | Scalar/check/edge assignments through public pilots. |
| REQ | UPD-03 | Offset min-sum offset/sign behavior | 11, 13, 08, 15 | COVERED | Boundary oracle, refresh, public replay, reporting. |
| REQ | SCH-02 | Layer membership/order/freshness | 03, 05, 06, 12, 13, 08, 15 | COVERED | Direct API, accounting/reconstruction, public admission, pilot. |
| REQ | SCH-03 | Serial unit/order/ties | 03, 05, 12, 13, 08, 15 | COVERED | Distinct CN/VN policies and public evidence. |
| REQ | SCH-04 | Residual definition/invalidation/selection/work | 04, 05, 12, 13, 08, 15 | COVERED | Stateful pinned conventional sRBP through reporting. |
| REQ | SCH-05 | Replayable random order independent of samples | 03, 05, 11, 12, 13, 08, 15 | COVERED | Purpose-separated streams, realized orders, matched pilots. |
| REQ | SCH-06 | Source-defined cluster sequence and learned parameters | 14, 09, 10, 16, 17 | COVERED | Qualifier, authentic checkpoint, tracer, traversal, retained result. |
| CONTEXT | D-01 | Scalar/iteration/check/edge assignments | 02, 11 | COVERED | Strict tagged shapes. |
| CONTEXT | D-02 | Explicit and seeded generated assignments | 11 | COVERED | Generator and resolved values persist. |
| CONTEXT | D-03 | Configuration/attempt/iteration refresh | 03, 11 | COVERED | Source-iteration boundary supplied by schedule. |
| CONTEXT | D-04 | Independent parameter/order/physical RNG | 03, 11, 08 | COVERED | Matched-sample metamorphic tests. |
| CONTEXT | D-05 | Exploratory ranges with labels | 02, 11, 08 | COVERED | Conventional/exploratory evidence separated. |
| CONTEXT | D-06 | Distinct CN/VN serial schedules | 03, 13 | COVERED | Separate local-unit semantics and public admission. |
| CONTEXT | D-07 | Explicit/source/automatic layers | 03, 06, 13 | COVERED | Membership, multiplicity, order, provenance. |
| CONTEXT | D-08 | Three random order refresh scopes | 03, 13 | COVERED | Exact realized permutation replay. |
| CONTEXT | D-09 | Convergence after each local unit | 01, 03–06, 10, 12, 16 | COVERED | Reserved with mutation work before state change. |
| CONTEXT | D-10 | Checks, hard budgets, partial progress | 01, 03–05, 10, 12, 16, 17 | COVERED | Versioned work/progress evidence. |
| CONTEXT | D-11 | Select source residual and cluster baselines | 04, 10, 14, 16, 17 | COVERED | Huang–Ueng conventional sRBP and Moradi RL-S. |
| CONTEXT | D-12 | Only pinned residual baseline | 04, 13 | COVERED | Deterministic full scan; no score/tie variants. |
| CONTEXT | D-13 | Pinned learned cluster artifacts only | 09, 10, 14, 16, 17 | COVERED | No training/synthetic/random substitute. |
| CONTEXT | D-14 | Setup/decode costs; training unknown | 04, 05, 10, 14, 16, 17 | COVERED | Separate fields and explicit missingness. |
| CONTEXT | D-15 | Focused comparisons | 08, 13 | COVERED | No full Cartesian product. |
| CONTEXT | D-16 | C2V cap and qualified iteration views | 01, 05, 08, 12, 15, 16 | COVERED | Full work retained in both views. |
| CONTEXT | D-17 | BB-144, B1, requested HGP | 07, 08 | COVERED | Exact/reused/generated identities separated. |
| CONTEXT | D-18 | Tables, plots, runnable notebook, traces | 12, 15 | COVERED | Bounded traces plus pinned analysis extra and venv kernel. |
| CONTEXT | D-19 | Pilot/adaptation/no-ranking claims | 08–10, 14–17 | COVERED | Assessment labels and prohibitions. |
| RESEARCH | — | Promote one local-step protocol; preserve flooding ABI | 01, 05, 06, 13 | COVERED | Assumption-delta decision recorded in Plan 01. |
| RESEARCH | — | Stateful sRBP reset/invalidation oracle and MS/SPA regression | 04 | COVERED | Stateless global oracle explicitly rejected. |
| RESEARCH | — | Deterministic lowest-EdgeTable residual tie | 04 | COVERED | Full scan retains first maximum. |
| RESEARCH | — | Strict cluster artifact acquisition gate | 14, 09, 10, 16, 17 | COVERED | SCH-06 cannot seal early. |
| RESEARCH | — | Exact B1 expansion/logicals | 07 | COVERED | Polynomial/source/order/hash checks. |
| RESEARCH | — | Generated 9x12 Gallager HGP with actual rank/dimension | 07 | COVERED | PCG64 seed 20260923; r=7; k=29. |
| RESEARCH | — | Analysis dependencies and kernel execution | 15 | COVERED | Exact audited pins including ipykernel. |
| RESEARCH | — | ASVS L1, block high threats | 01–17 | COVERED | Every plan has a threat model; no high threat accepted. |

Deferred ensemble execution, BPGD interventions, cluster training, exploratory residual variants, individual-message serial scheduling, and statistical reproduction campaigns are excluded by CONTEXT and are not gaps.

## Spec-Less Edge Coverage

Probe input: `/tmp/survey-bp-phase03-edge-coverage.json`. No SPEC supplied edge coverage. No item is silently dropped.

| # | Requirement | Category | Resolution | Authored acceptance location |
|---:|---|---|---|---|
| 1 | UPD-01 | boundary | resolved / explicit | Plan 01: degree-one, zero, repeated minima, sign, saturation and adjacent-float cases. |
| 2 | UPD-01 | precision | resolved / explicit | Plan 01: float64, inherited sign/tie, post-magnitude saturation. |
| 3 | UPD-02 | boundary | resolved / explicit | Plan 02: alpha zero/one/adjacent/>1/negative/nonfinite. |
| 4 | UPD-02 | precision | resolved / explicit | Plan 02: float64 multiplication then saturation; equivalent arrays. |
| 5 | UPD-03 | boundary | resolved / explicit | Plan 11: beta zero/equal/adjacent/negative/nonfinite. |
| 6 | UPD-03 | precision | resolved / explicit | Plan 11: float64 subtraction, zero floor, sign/tie, saturation. |
| 7 | SCH-02 | empty | resolved / explicit | Plan 03: null, zero/empty layers, unknown/missing membership and valid singleton. |
| 8 | SCH-02 | encoding | resolved / explicit | Plan 03: exact integer graph identities/tuples; text normalization is inapplicable. |
| 9 | SCH-03 | idempotency | resolved / explicit | Plan 03: retry vs next unit, unique leaf commit, unchanged cursor on denial. |
| 10 | SCH-03 | concurrency | resolved / explicit | Plan 03: attempt-local state and duplicate same-shot identity rejection. |
| 11 | SCH-04 | unclassified | unresolved / flagged assumption | Plans 04/06 retain explicit assumption and require cache/selection/work evidence. |
| 12 | SCH-05 | unclassified | unresolved / flagged assumption | Plans 12/13 retain explicit assumption and require realized-order/sample evidence. |
| 13 | SCH-06 | unclassified | unresolved / flagged assumption | Plans 14/10/16/17 retain explicit assumption and external artifact gate. |

Equality check: **13 probe items = 10 authored explicit checks + 3 flagged assumptions**.

## Spec-Less Prohibition Recall

The two-stage recall/precision pass dropped routine engineering and canon security items. Canon security is covered by the plan threat models. Seven bespoke scientific-integrity/transparency prohibitions survive and are authored descriptor-less as required by the no-SPEC protocol:

1. Hidden physical truth must not enter update/schedule policies — Plan 01.
2. Exploratory parameter settings must not be labeled source-faithful — Plan 02.
3. Generic layers/random groups must not be labeled published cluster algorithms — Plan 03.
4. Residual variants/stateless recomputation must not be labeled the pinned source baseline — Plan 04.
5. Synthetic/retrained/random cluster artifacts must not establish Moradi support — Plan 14.
6. Generated HGP adaptation must not be labeled an author instance or given an unsourced distance — Plan 07.
7. Bounded pilots must not imply statistical reproduction or ranking — Plan 08.

Equality check: **7 kept prohibitions = 7 descriptor-less flagged-unverified `must_haves.prohibitions` items**.

## Capability Contribution Decisions

- API coverage detector after authoring: `detected=false`; no external API/SDK/service integration, so no API `COVERAGE.md` is required.
- Assumption-delta detector: `detected=true`. Plan 01 records `promote`: the canonical schedule/local-step protocol is primary; flooding is an explicit versioned variant.
- Schema-push detector: no supported ORM schema paths; no database push applies.
- Package legitimacy: Plan 15 uses exact RESEARCH-audited PyPI pins for matplotlib, nbformat, nbclient, and ipykernel. Generic telemetry limitations are recorded in RESEARCH; no invented approval checkpoint is added.

## Complete Artifact and Symbol Inventory

| Plan | Artifact / symbol |
|---|---|
| 01 | `CheckUpdateRule`, `MinSumUpdate`, `UpdateRuleEvidence`, `LocalStepProposal`, `ScheduleProgress`, `CanonicalLocalStepExecutor`, `CanonicalExperimentV3` tracer grammar |
| 02 | `NormalizedMinSumUpdate`, scalar/check/edge `ParameterAssignment`, initial `schema-canonical-v3.json`, update-rule docs |
| 03 | `LayeredSchedule`, `CheckNodeSerialSchedule`, `VariableNodeSerialSchedule`, `RandomizedTraversalPlan` |
| 04 | `SyndromeResidualSchedule`, `ResidualCache`, `ResidualSelection`, source-lifecycle oracle |
| 05 | extended `WorkVector`, dual budget views, partial-progress terminal grammar, base reconstruction |
| 06 | public layered-SPA tracer through preflight/run/verify-run |
| 07 | `build_b1_ghp`, `derive_css_logicals`, `build_gallager_constituent`, `build_hgp`; B1 and Gallager-HGP artifacts/provenance |
| 08 | three pilot manifests, matched ledgers/results, `run_phase3_pilots.py` |
| 09 | authoritative cluster source record, Q-table, partition, qualification report |
| 10 | one-step qualified `ClusterRlsSchedule`/`ClusterRlsProgress` public tracer |
| 11 | `OffsetMinSumUpdate`, `ParameterGeneratorSpec`, `ParameterRefreshPlan`, purpose-separated replay evidence |
| 12 | complete terminal verifier and bounded local-convergence/schedule traces |
| 13 | full noncluster public compatibility matrix, schema, documentation, round-trip/rejection coverage |
| 14 | `ClusterArtifactSpec`, `ClusterArtifactQualification`, `load_cluster_artifact`, `qualify-cluster-artifact` CLI |
| 15 | `execute_phase3_notebook.py`, source/executed notebook, CSV and PNG reports |
| 16 | complete qualified cluster traversal, cost, progress, rollback, and reconstruction |
| 17 | qualified cluster manifest/ledger/result and final verify-run |

## Final Gate

Plans 01–08 and 11–15 complete every independent engine, policy, pilot, notebook, reporting, and qualifier deliverable before the external checkpoint. Plan 09 blocks only after Plan 15 is complete. Phase 03 and SCH-06 complete only after Plan 09 qualifies the authentic artifact, Plan 10 proves one source step, Plan 16 proves traversal/work/reconstruction, and Plan 17 retains and verifies the bounded public result.
