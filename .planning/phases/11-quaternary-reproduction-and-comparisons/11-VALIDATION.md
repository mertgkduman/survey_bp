---
phase: "11"
slug: "quaternary-reproduction-and-comparisons"
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| Measured Phase 11 suite | 76 passed in 259 seconds on 2026-10-14. |

## Sampling Rate

- After every task commit: run the narrow new or changed test file and its closest existing analog.
- After every plan wave: run the quick quaternary and campaign suite.
- Before `$gsd-verify-work`: run the full suite and audit replay and source-target receipts.
- Max feedback latency: measure in Wave 0; split narrow tests if the task loop exceeds 30 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|----------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | QEV-01 | T-11-01A, T-11-01B, T-11-01C, T-11-01D | Carry one frozen aSCED Figure 2 member to a terminal assessment | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_targets.py -k 'asced and (tracer or ordinary or preflight or bounded or assess or blocked or tamper)' -x` | ✅ | ✅ green |
| 11-01-02 | 01 | 1 | QEV-01 | T-11-01A, T-11-01B, T-11-01C, T-11-01D | Freeze separate ordinary and overcomplete GB46 curve targets | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_targets.py -k 'asced and (overcomplete or digitization or tolerance or stopping or discrepancy or mutation)' -x` | ✅ | ✅ green |
| 11-02-01 | 02 | 2 | QEV-01 | T-11-02A, T-11-02B, T-11-02C, T-11-02D | Reconstruct and preflight the A5 source artifact | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_qbpgd_source.py -k 'a5 and (tracer or artifact or polynomial or rank or commutation or provenance or tamper)' -x` | ✅ | ✅ green |
| 11-02-02 | 02 | 2 | QEV-01 | T-11-02A, T-11-02B, T-11-02C, T-11-02D | Freeze Figure 7 settings and a bounded Q-BPGD qualification path | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_qbpgd_source.py -k 'figure7 or settings or decimation or work or adaptation or replay or blocked or discrepancy' -x` | ✅ | ✅ green |
| 11-03-01 | 03 | 3 | QEV-01 | T-11-03A, T-11-03B, T-11-03C, T-11-03D | Replay the alpha=1 oscillation from target receipt to assessment | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_mbp4_target.py -k 'tracer or alpha_one or oscillation or independent or replay or digest' -x` | ✅ | ✅ green |
| 11-03-02 | 03 | 3 | QEV-01 | T-11-03A, T-11-03B, T-11-03C, T-11-03D | Verify alpha=1.5 convergence and preserve curve metadata gaps | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_mbp4_target.py -k 'alpha_one_point_five or convergence or original_problem or work or figure6 or blocked or claim_scope' -x` | ✅ | ✅ green |
| 11-04-01 | 04 | 2 | QEV-01 | T-11-04A, T-11-04B, T-11-04C, T-11-04D | Prove current native matched-input unavailability | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'tracer or current_unavailable or pinned or aggregate_only or no_execution or tamper' -x` | ✅ | ✅ green |
| 11-04-02 | 04 | 2 | QEV-01 | T-11-04A, T-11-04B, T-11-04C, T-11-04D | Generate an unapplied minimal injected-error diff and review package | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'proposal or diff_scope or translation or vector_digest or unchanged_downstream or authorization_required' -x` | ✅ | ✅ green |
| 11-05-01 | 05 | 3 | QEV-01 | T-11-05A, T-11-05B, T-11-05C | Qualify native aSCED source modification and rights scope | checkpoint | `OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase11_native_asced.py verify-proposal --proposal data/native/phase11-asced-injected-input-proposal.json --patch data/native/phase11-asced-injected-input-diff.patch` | ✅ | ✅ green |
| 11-06-01 | 06 | 4 | QEV-01 | T-11-06A, T-11-06B, T-11-06C, T-11-06D | Materialize the decision as a fail-closed qualification terminal | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'decision or declined or authorized or digest_drift or isolated or no_partial' -x` | ✅ | ✅ green |
| 11-06-02 | 06 | 4 | QEV-01 | T-11-06A, T-11-06B, T-11-06C, T-11-06D | Qualify bounded injected-error execution when authorized | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_native_asced.py -k 'injected or identity or translation or bounded or splitter or discrepancy or unavailable or receipt_tamper' -x` | ✅ | ✅ green |
| 11-07-01 | 07 | 1 | QEV-02 | T-11-07A, T-11-07B, T-11-07C, T-11-07D | Execute one GB46 Pauli sample through joint and separate inference | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -k 'tracer or identical_sample or marginals or hidden_truth' -x` | ✅ | ✅ green |
| 11-07-02 | 07 | 1 | QEV-02 | T-11-07A, T-11-07B, T-11-07C, T-11-07D | Preserve partial nonconvergence, work, replay, and tamper evidence | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py -k 'nonconver or all_shot or component or replay or tamper or duplicate or partial' -x` | ✅ | ✅ green |
| 11-08-01 | 08 | 2 | QEV-02 | T-11-08A, T-11-08B, T-11-08C, T-11-08D | Assess a hand-checkable three-point fixed-marginal sweep | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -k 'tracer or rational or fixed_marginal or hand_count or contrast or simultaneous' -x` | ✅ | ✅ green |
| 11-08-02 | 08 | 2 | QEV-02 | T-11-08A, T-11-08B, T-11-08C, T-11-08D | Calibrate paired-discordance precision before campaign admission | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_correlation_statistics.py -k 'sizing or precision or ceiling or zero or extreme or duplicate or partial or deterministic' -x` | ✅ | ✅ green |
| 11-09-01 | 09 | 3 | QEV-02 | T-11-09A, T-11-09B, T-11-09C, T-11-09D | Run and replay one public GB46 independence pair | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py -k 'tracer or installed_cli or one_pair or replay or tamper or output_root' -x` | ✅ | ✅ green |
| 11-09-02 | 09 | 3 | QEV-02 | T-11-09A, T-11-09B, T-11-09C, T-11-09D | Execute disjoint bounded GB46 calibration shards at all three points | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py -k 'gb46 and (three_point or shard or resume or merge or overlap or duplicate or empty or lane)' -x` | ✅ | ✅ green |
| 11-10-01 | 10 | 4 | QEV-01, QEV-02 | T-11-10A, T-11-10B, T-11-10C, T-11-10D | Run one BB72 independence pair through the qualified public lifecycle | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_joint_separate.py tests/test_phase11_quaternary_campaign.py -k 'bb72 and (tracer or independence or provenance or distance or replay)' -x` | ✅ | ✅ green |
| 11-10-02 | 10 | 4 | QEV-01, QEV-02 | T-11-10A, T-11-10B, T-11-10C, T-11-10D | Calibrate BB72 at all three points with typed work and runtime | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_quaternary_campaign.py tests/test_phase11_resource_gate.py -k 'bb72 and (three_point or work or runtime or resource or limit or merge)' -x` | ✅ | ✅ green |
| 11-10-03 | 10 | 4 | QEV-01, QEV-02 | T-11-10A, T-11-10B, T-11-10C, T-11-10D | Assemble a default-deny two-code production authorization package | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py -k 'proposal or deny or ceiling or accounting or stale or source or precision or digest' -x` | ✅ | ✅ green |
| 11-11-01 | 11 | 5 | QEV-01, QEV-02 | T-11-11A, T-11-11B, T-11-11C | Decide exact Phase 11 publication dispatch authorization | checkpoint | `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase11_controlled.py verify-authorization --package data/results/phase11-production-authorization.json` | ✅ | ✅ green |
| 11-11-02 | 11 | 5 | QEV-01, QEV-02 | T-11-11A, T-11-11B, T-11-11C | Materialize the reviewed decision as the sealed authorization receipt | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_resource_gate.py -k 'record_authorization or materialize or exact_digest or allow_subset or preserve_deny or stale or ineligible or atomic' -x` | ✅ | ✅ green |
| 11-12-01 | 12 | 6 | QEV-01 | T-11-12A, T-11-12B, T-11-12C, T-11-12D | Close the aSCED Figure 2 source lane through separate assessments | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_assessments.py -k 'asced and (ordinary or overcomplete or authorized or denied or unavailable or discrepancy or fidelity)' -x` | ✅ | ✅ green |
| 11-12-02 | 12 | 6 | QEV-01 | T-11-12A, T-11-12B, T-11-12C, T-11-12D | Qualify Q-BPGD Figure 7 A5 as a gap-visible canonical adaptation | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_source_assessments.py -k 'qbpgd and (a5 or setting or gap or adaptation or stopping or denied or discrepancy)' -x` | ✅ | ✅ green |
| 11-12-03 | 12 | 6 | QEV-01 | T-11-12A, T-11-12B, T-11-12C, T-11-12D | Finalize the MBP4 Figures 8–9 deterministic mechanism assessment | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_mbp4_target.py tests/test_phase11_source_assessments.py -k 'mbp4 and (figure8 or figure9 or deterministic or replay or mechanism or nonclaim or unavailable)' -x` | ✅ | ✅ green |
| 11-13-01 | 13 | 5 | QEV-01, QEV-02 | T-11-13A, T-11-13B, T-11-13C, T-11-13D | Compare the source-qualified MBP4 alpha recurrence on one matched anchor | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'tracer or mbp4 or one_change or independence or unsupported or replay' -x` | ✅ | ✅ green |
| 11-13-02 | 13 | 5 | QEV-01, QEV-02 | T-11-13A, T-11-13B, T-11-13C, T-11-13D | Expand each qualified policy comparison to exactly three channel anchors | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'three_anchor or lower_y or higher_y or asced or overcomplete or ineligible or multi_change' -x` | ✅ | ✅ green |
| 11-13-03 | 13 | 5 | QEV-01, QEV-02 | T-11-13A, T-11-13B, T-11-13C, T-11-13D | Complete matched-sample evidence for all qualified quaternary methods | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'complete_methods or eligibility or matched or gb46 or bb72 or work or runtime or excluded' -x` | ✅ | ✅ green |
| 11-14-01 | 14 | 7 | QEV-01, QEV-02 | T-11-14A, T-11-14B, T-11-14C, T-11-14D | Produce the terminal GB46 joint-versus-separate assessment | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py -k 'tracer or gb46 or primary or cross_point or simultaneous or bounded or inconclusive' -x` | ✅ | ✅ green |
| 11-14-02 | 14 | 7 | QEV-01, QEV-02 | T-11-14A, T-11-14B, T-11-14C, T-11-14D | Add BB72 assessment with identical estimands and retained caveats | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py -k 'bb72 or provenance or distance or identical_estimand or no_pooling or exclusion' -x` | ✅ | ✅ green |
| 11-14-03 | 14 | 7 | QEV-01, QEV-02 | T-11-14A, T-11-14B, T-11-14C, T-11-14D | Reconcile source, primary, and policy evidence into a verified public index | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_final_assessment.py tests/canonical/quaternary/test_public_execution.py -k 'phase11 or assessment_index or source_lane or controlled_lane or policy_lane or installed_cli or tamper or claim' -x` | ✅ | ✅ green |
| 11-15-01 | 15 | 6 | QEV-02 | T-11-15A, T-11-15B, T-11-15C, T-11-15D, T-11-15E | Consume the exact GB46 authorization through one terminal controlled path | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'gb46 and (tracer or allow or deny or ineligible or blocked_precision or stale or accounting or budget or interruption)' -x` | ✅ | ✅ green |
| 11-15-02 | 15 | 6 | QEV-02 | T-11-15A, T-11-15B, T-11-15C, T-11-15D, T-11-15E | Execute or explicitly close the exact BB72 controlled manifest | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'bb72 and (allow or close or provenance or precision or budget or complete_pair or interruption or cross_code)' -x` | ✅ | ✅ green |
| 11-15-03 | 15 | 6 | QEV-02 | T-11-15A, T-11-15B, T-11-15C, T-11-15D, T-11-15E | Verify two-code receipt completeness and publication-evidence boundaries | unit/integration | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_controlled_evaluation.py -k 'verify_all or terminal_coverage or receipt_digest or attempted_work or complete_pair or exceeded_budget or calibration_scope or tamper' -x` | ✅ | ✅ green |

*Status: ✅ green for implemented automated checks. The two blocking-human decisions were recorded separately in Plans 11-05 and 11-11. Threat references point to each plan's register.*

## Wave 0 Requirements

- [x] `tests/test_phase11_source_targets.py` — exact target qualification, missing metadata, and tamper cases.
- [x] `tests/test_phase11_qbpgd_source.py` — A5 artifact, Figure 7 settings, fidelity, and source gaps.
- [x] `tests/test_phase11_quaternary_campaign.py` — Pauli campaign sample identity, merge, replay, fidelity, and typed work.
- [x] `tests/test_phase11_joint_separate.py` — exact marginal boundary, partial nonconvergence, and GB46/BB72 pairing.
- [x] `tests/test_phase11_correlation_statistics.py` — frozen contrasts and simultaneous exact intervals.
- [x] `tests/test_phase11_resource_gate.py` — production denial until resource and accounting qualification.
- [x] `tests/canonical/quaternary/test_phase11_mbp4_target.py` — deterministic source mechanism.
- [x] `tests/canonical/quaternary/test_phase11_native_asced.py` — pinned native limitation, proposal, decision, and conditional injected-error qualification.
- [x] `tests/test_phase11_source_assessments.py` — aSCED, Q-BPGD, and MBP4 separate source-lane terminals.
- [x] `tests/test_phase11_policy_comparisons.py` — one-change, three-anchor, and complete-method eligibility.
- [x] `tests/test_phase11_final_assessment.py` — two-code primary contrast and evidence index.
- [x] `tests/test_phase11_controlled_evaluation.py` — exact controlled authorization consumption, code-specific execution or closure, and complete-pair receipt verification.
- [x] Native injected-input verification remains conditional; the user selected `preserve_unavailable` and no derivative was executed.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Paper figure digitization and source settings | QEV-01 | The paper's plotted coordinates and some metadata need source interpretation. | Record extraction method, reviewer, coordinates, settings, uncertainty, and tolerance before assessment; retain unresolved items as blocked metadata. |
| Native aSCED source modification approval | QEV-01 | Existing bounded approval forbids algorithm or channel source changes. | Review the proposed minimal diff and rights scope; only then qualify an instrumented native identity and matched injected-error route. |
| Publication-scale resource authorization | QEV-01, QEV-02 | Site ceilings and scheduler accounting are not yet measured. | Review measured profile, site limits, accounting, frozen manifest, and explicit authorization before dispatch. |

## Validation Sign-Off

- [x] All plan tasks have automated verification or a documented human checkpoint.
- [x] No three consecutive tasks lack automated verification.
- [x] Wave 0 test paths were created and exercised.
- [x] No watch mode flags.
- [x] Phase 11 feedback latency measured: 76 tests in 259 seconds.
- [x] Plan map and implemented tests validated.

**Approval:** automated validation complete; manual source digitization and publication dispatch remain unavailable under the recorded decisions.

## Validation Audit 2026-10-14

| Metric | Count |
|--------|-------|
| Planned task checks | 34 |
| Implemented Phase 11 test files | 12 |
| Consolidated Phase 11 tests passed | 76 |
| Missing automated test paths | 0 |

The two checkpoint verifiers passed before the user selected `preserve_unavailable` and `preserve_deny`. This audit confirms coverage of the implemented and denied paths; it does not claim source-curve agreement or controlled effect estimation from zero publication pairs.
