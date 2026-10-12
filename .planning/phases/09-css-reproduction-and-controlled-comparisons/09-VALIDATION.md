---
phase: "09"
slug: "css-reproduction-and-controlled-comparisons"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-11"
updated: "2026-10-11"
---

# Phase 9 — Validation Strategy

## Test Infrastructure

| Property | Value |
| --- | --- |
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` |
| Focused command form | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <file> -k '<selection>' -x` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Runtime policy | Measure focused and full-suite elapsed time on first execution; no unmeasured ceiling is assumed. |

## Sampling Rate

- **After every task commit:** Run every `<automated>` command in that task and retain exit status and selected-test count.
- **After every plan wave:** Run the full suite and record elapsed time, peak memory, and exit status.
- **Before `$gsd-verify-work`:** Run the full suite and independently reconstruct retained source, tracer, voting, paired-control, and production-authorization receipts.
- **Feedback bound:** Set from measured focused/full runs. Missing timing evidence remains `unavailable` rather than becoming a guessed limit.

## Per-Task Verification Map

| Task ID | Wave | Requirement | Secure behavior | Automated command | Test source | Status |
| --- | ---: | --- | --- | --- | --- | --- |
| 09-01-01 | 1 | EVAL-01 | Ordered source identity and evidence paths fail closed | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -k 'source or table or denominator or tamper or path' -x` | existing, expanded in task | green |
| 09-01-02 | 1 | EVAL-01 | Typed native gaps and faithful-eligibility predicates remain complete and monotone | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_targets.py -k 'qualification or native or unavailable or ordered_identity' -x` | existing, expanded in task | green |
| 09-02-01 | 2 | EVAL-01, EVAL-02 | First Yao target is authored and pinned without invented experiment identity | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_receipts.py -k 'yao and tracer' -x` | created in task | green |
| 09-02-02 | 2 | EVAL-01, EVAL-02 | Authored-coordinate inventories retain locator, stopping, and identity gaps | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_receipts.py -k 'authored_coordinates or locator or stopping or identity_gap' -x` | created in task | green |
| 09-03-01 | 3 | EVAL-01, EVAL-02 | Missing Bhatnagar author data remains unavailable and cannot become a curve | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'bhatnagar and unavailable' -x` | created in task | green |
| 09-03-02 | 3 | EVAL-01, EVAL-02 | All 14 variants have monotone, tamper-evident qualification states | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'inventory or fourteen or monotone or faithful or tamper' -x` | created in task | green |
| 09-04-01 | 1 | EVAL-02 | Ordered target-th-failure stopping separates inferential prefix, terminal tail, censoring, and interruption | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'stopping or ordered_stop or terminal_tail or denominator or outcome or partial' -x` | existing, expanded in task | green |
| 09-04-02 | 1 | EVAL-02 | Inverse-binomial inference and target tolerance cannot cross sampling designs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'failure_count or inverse_binomial or censor or multiplicative or historical' -x` | existing, expanded in task | green |
| 09-05-01 | 2 | EVAL-02 | Exact inverse-binomial bounds use T_r and remain invariant to authorized terminal tail | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'inverse_binomial or ordered_stop or authorized_tail or coverage or boundary' -x` | existing, expanded in task | green |
| 09-05-02 | 2 | EVAL-02 | Target agreement keeps source precision and prespecified tolerance separate | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'multiplicative or containment or discrepant or inconclusive or target' -x` | existing, expanded in task | green |
| 09-16-01 | 3 | EVAL-02 | Prospective policy contains no terminal facts; executable-limit receipts prove hard maxima, reserve interruption evidence, and define boundary-observed wall timeout | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'prospective_failure_count or executable_limit or understated_bound or receipt_reserve or boundary_timeout or wall_overshoot or terminal_receipt or pre_run or observed_fact or historical or failure_count_stopping or failure_count_assessment' -x` | existing, expanded in task | green |
| 09-16-02 | 3 | EVAL-02 | Inverse-binomial inference joins a verified target-reached terminal receipt to its prospective policy and rejects every mismatch/censored state | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'prospective_failure_count or terminal_receipt or inverse_binomial or policy_mismatch or censored' -x` | existing, expanded in task | green |
| 09-20-01 | 5 | EVAL-02 | Independent registered-route maxima and exact declaration verifier reject stale or understated work/event/byte limits | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_resource_guard.py tests/canonical/test_resource_profiles.py -k 'executable_maxima or registered_route or event_inventory or serializer_bound or artifact_layout or declaration_verifier or stale or understated or local_schedule_profile or relay_profile or beam_route or v7_profile' -x` | created in task | green |
| 09-20-02 | 5 | EVAL-02 | Strict and explicit interruptible-unit authorizations use exact pre-write reservations; one control receipt survives byte exhaustion | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_ledger.py tests/canonical/test_resource_guard.py -k 'guarded_append or guarded_artifact or exact_fit or one_byte_over or stop_before_append or stop_before_write or duplicate_event or reservation_release or control_receipt_reserve or interruptible_unit or single_use_control' -x` | created in task | green |
| 09-20-03 | 5 | EVAL-02 | Engine boundaries record positive wall overshoot and typed interruption without later work; absent-guard legacy/V7 bytes remain stable | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_resource_guard.py tests/canonical/test_resource_boundaries.py -k 'wall_boundary or inside_iteration_crossing or positive_overshoot or no_future_work or typed_interruption or guided or phase5 or mbbp or v7_list_compatibility or v7_vote_compatibility or legacy_compatibility' -x` | created in task | green |
| 09-17-01 | 6 | EVAL-02 | Strict full-batch admission verifies maxima and all caps; a separate frozen interruptible-unit mode admits only one next ordinal | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'canonical_bounded_batch or executable_maxima or executable_limit or stale_derivation or understated_bound or predispatch_cap or cap_precedence or interruptible_unit or strict_full_batch or guarded_v7_compatibility or legacy_complete_plan_compatibility' -x` | existing, expanded in task | green |
| 09-17-02 | 6 | EVAL-02 | Explicit interruptible-unit byte or wall stops seal zero-credit partial attempts; fresh-attempt resume preserves the pending ordinal | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_failure_count.py -k 'interruptible_unit or mid_unit_cap or evidence_stop_before_append or storage_stop_before_write or wall_boundary_overshoot or no_work_after_timeout or partial_attempt or exact_pending_resume or fresh_attempt_identity or no_duplicate_scientific_work or cap_censor_after_partial or tracer_ordered_stop' -x` | existing, expanded in task | green |
| 09-06-01 | 7 | EVAL-02 | Target-reached/censored lifecycle reconstructs canonical order, exact T_r, tail, interruption, and resume | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_failure_count.py -k 'tracer or ordered_stop or terminal_batch_tail or censor or resume or interruption' -x` | created in task | green |
| 09-06-02 | 7 | EVAL-02 | Public lifecycle retains hard-cap interruptions and boundary-observed wall overshoot receipts while preserving prospective policy, terminal evidence, and complete costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_failure_count.py -k 'public_failure_count_plan or public_failure_count_run_local or public_failure_count_merge or public_failure_count_resume or public_failure_count_assess or public_failure_count_verify or public_mid_unit_cap or public_wall_overshoot or tracer_ordered_stop' -x` | created in task | pending |
| 09-18-01 | 8 | EVAL-03 | Additive ordered work specs bind complete sample-major groups and declared arm ordinals without changing historical bytes | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'ordered_work_spec or declared_arm_order or group_ordinal or arm_order or topology_invariant' -x` | existing, expanded in task | pending |
| 09-18-02 | 8 | EVAL-03 | Public ordered partial merge/verify retains completed arms, emits the exact missing set, and terminal assess/verify requires every frozen group | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'installed_ordered_campaign or ordered_partial_merge or ordered_inside_group_partial or ordered_missing_set or ordered_assess or declared_arm_order or worker_order or ordered_resume or ordered_tamper or mixed_route' -x` | existing, expanded in task | pending |
| 09-07-01 | 1 | CAN-02 | Vote executes only over admitted declared members; invalid/empty outcomes stay visible | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py -k 'vote or electorate or exclusion or invalid or empty or list_regression' -x` | existing, expanded in task | green |
| 09-07-02 | 1 | CAN-02 | Ballots and lineage are deterministic and original validation remains independent | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py tests/canonical/test_mbbp.py -k 'vote or tie or order or original_valid or lineage' -x` | existing, expanded in task | green |
| 09-08-01 | 4 | CAN-02 | Public vote ledger runs, verifies, rejects tamper, independently replays, and carries the declared tie bit through both canonical paths | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py -k 'vote and (run or verify or tamper or replay)' -x` | existing, expanded in task | green |
| 09-08-02 | 4 | EVAL-01, CAN-02 | Tracked vote policy compiles and replays with explicit adaptation status | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_css_literature_gate.py -k 'vote or policy_file or replay or cache or adaptation' -x` | existing, expanded in task | green |
| 09-09-01 | 8 | EVAL-02, EVAL-03 | Small public policy path reaches a verified sealed merge under bounded caps | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_profile_gate.py -k 'tracer or policy or ledger or seal or merge' -x` | created in task | pending |
| 09-09-02 | 8 | EVAL-02, EVAL-03 | Independent replay emits receipt-linked measurements and leaves production denied | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_profile_gate.py -k 'measured or replay or unavailable or denied or receipt' -x` | created in task | pending |
| 09-10-01 | 9 | EVAL-01, EVAL-02 | Bounded Yao B1 launches only after the measured gate and retains its first whole batch | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_yao_b1_tracer.py -k 'profile_gate or preflight or first_batch or replay or label' -x` | created in task | pending |
| 09-10-02 | 9 | EVAL-01, EVAL-02 | Resume closes at exact T_100 with tail excluded or an honest cap-censored terminal | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_yao_b1_tracer.py -k 'resume or target_reached or target_ordinal or authorized_tail or censor or final_report or interruption' -x` | created in task | pending |
| 09-11-01 | 9 | EVAL-03 | Paired sizing uses disjoint calibration and reports powered and bounded boundaries | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_sizing.py -k 'paired or power or disjoint or blocked or boundary' -x` | created in task | pending |
| 09-11-02 | 9 | EVAL-03 | Relay, Beam, and MBBP use separate profiles and positive bounded N while Slurm stays denied | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_sizing.py -k 'resource or representative_profile or relay or beam or mbbp or positive_n or slurm or missing' -x` | created in task | pending |
| 09-19-01 | 10 | EVAL-03, CAN-02 | Public controlled lifecycle retains typed leaves, one shared initial receipt, completed arms inside partial groups, exact missing sets, terminal assessment, and byte replay | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py -k 'controlled_component or shared_initial_receipt or controlled_partial or controlled_inside_group_partial or controlled_resume or controlled_assess or controlled_byte_replay or paired_canonical_replays' -x` | existing, expanded in task | pending |
| 09-19-02 | 10 | EVAL-03, CAN-02 | Frozen three-arm Holm plus public six-verb ordinary-two-arm and shared-MBBP lifecycles preserve one member set, exact resume, costs, and replay | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_execution.py tests/test_campaign_statistics.py -k 'three_arm_family or shared_initial_receipt or shared_mbbp_member_set or member_no_rerun or public_two_arm_plan or public_two_arm_run_local or public_two_arm_merge or public_two_arm_resume or public_two_arm_assess or public_two_arm_verify or public_shared_mbbp_plan or public_shared_mbbp_run_local or public_shared_mbbp_merge or public_shared_mbbp_resume or public_shared_mbbp_assess or public_shared_mbbp_verify or common_incremental_cost or controlled_replay_drift or holm or paired_canonical_replays' -x` | existing, expanded in task | pending |
| 09-12-01 | 11 | EVAL-03 | Schedule control changes one factor and uses public two-arm plan/run-local/merge/resume for frozen positive-N typed evidence | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_update_schedule_control.py -k 'one_factor or positive_n or matched_evidence or paired_execution or typed_evidence or public_two_arm_plan or public_two_arm_run_local or public_two_arm_merge or public_two_arm_resume or phase_incomplete or label' -x` | created in task | pending |
| 09-12-02 | 11 | EVAL-03 | Public two-arm assess/verify invokes no decoder and byte-reconstructs completion, denominators, typed actuals, and costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_update_schedule_control.py -k 'assessment or cost or replay or public_two_arm_assess or public_two_arm_verify or no_decoder or byte_replay or exact_missing_set or all_shot or conditional' -x` | created in task | pending |
| 09-13-01 | 11 | EVAL-03 | Frozen three-arm family uses one shared initial BP receipt plus distinct typed Relay leaves and costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_beam_relay_control.py -k 'relay or relay_profile or positive_n or three_arm_family or shared_initial_receipt or public_lifecycle or convergence or iterations or extra_work or phase_incomplete' -x` | created in task | pending |
| 09-13-02 | 11 | EVAL-03 | Beam consumes the same initial receipt; exact replay reconstructs both baseline contrasts and one Holm family | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_beam_relay_control.py -k 'beam or beam_profile or positive_n or shared_initial_receipt or convergence or iterations or holm or no_decoder or byte_replay or incomplete or replay' -x` | created in task | pending |
| 09-14-01 | 11 | EVAL-03, CAN-02 | Public shared-MBBP plan/run-local/merge/resume produces one typed member receipt for list and vote without rerun | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_vote_list_control.py -k 'mbbp_profile or positive_n or shared_members or shared_member_receipt or member_no_rerun or public_shared_mbbp_plan or public_shared_mbbp_run_local or public_shared_mbbp_merge or public_shared_mbbp_resume or convergence or iterations or vote or list or disposition or original_validation or phase_incomplete' -x` | created in task | pending |
| 09-14-02 | 11 | EVAL-03, CAN-02 | Public shared-MBBP assess/verify replays without decoder and preserves typed leaves, completion, denominators, labels, and costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_vote_list_control.py -k 'cost or replay or public_shared_mbbp_assess or public_shared_mbbp_verify or no_decoder or byte_replay or shared_member_receipt or convergence or iterations or completion or label or assessment or denominator' -x` | created in task | pending |
| 09-15-01 | 12 | EVAL-01, EVAL-02, EVAL-03, CAN-02 | Index audits Plans 09-01..09-20 and reconstructs policy/terminal, verified limits, cap receipts, ordered lifecycle, typed shared-input controls, and phase completion | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_css_evidence_index.py -k 'coverage or gap_plan or plan_16 or plan_17 or plan_18 or plan_19 or plan_20 or fourteen or ordered_stop or executable_limit or dynamic_cap or shared_input or tail or positive_n or convergence or iterations or phase_status or reconstruct or tamper or cost' -x` | created in task | pending |
| 09-15-02 | 12 | EVAL-01, EVAL-02, EVAL-03, CAN-02 | Guide preserves completion blockers, typed fields, external unknowns, denied Slurm, and no-overclaim labels | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_css_evidence_index.py -k 'guide or paper_records or ordered_stop or completion_blocker or convergence or iterations or external_unknown or no_overclaim or slurm_denied' -x` | created in task | pending |

*Status values: pending, green, red, flaky. “Created in task” means the task uses TDD and must make the selected test fail before implementation.*

Plan 09-20 exact task selectors passed with nonzero selections: Task 1 selected 7 tests in 40.11 s; Task 2 selected 2 in 0.88 s; Task 3 selected 4 in 0.84 s. The combined guard/profile/boundary/Relay/V7/ledger/CLI regression selected 164 tests and passed in 112.88 s. A later focused regression confirmed the repeated-layer and bounded syndrome-flip fixes (2 passed in 1.48 s).

## Completed Wave Gates

| Wave | Completed plans | Full-suite result | Elapsed | Peak RSS | Status |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 09-01, 09-04, 09-07 | 1,170 passed, 1 skipped | 828.10 s | unavailable (not measured) | green |
| 2 | 09-02, 09-05 | 1,184 passed, 1 skipped | 873.65 s | 383,736 KiB | green |
| 3 | 09-03, 09-16 | 1,197 passed, 1 skipped | 841.28 s | 377,768 KiB | green |
| 4 | 09-08 | 1,201 passed, 1 skipped | 829.74 s | 375,952 KiB | green |
| 5 | 09-20 | 1,234 passed, 1 skipped | 899.98 s | 386,436 KiB | green |
| 6 | 09-17 | 1,247 passed, 1 skipped | 883.70 s | 388,664 KiB | green |

The observed peak is for the pytest child process, measured with `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`; it is a local test-suite measurement, not an HPC job allocation or production campaign ceiling.

## Wave 0 Requirements

No separate Wave 0 is required. Every new fixture/test file is owned by the same TDD task that consumes it, and all inherited test files already exist. Before implementation, each task must demonstrate that its newly selected behavior is red rather than accepting a zero-test selection. Required fixtures include target failure at the first/middle/last terminal-batch ordinal with tail invariance; an understated executable bound; a wall deadline crossed inside one indivisible iteration with explicit overshoot and no subsequent work; hard pre-append evidence and pre-write storage exhaustion with reserved partial receipts; an ordered run stopping inside a matched group followed by exact no-duplicate resume and terminal assess; one shared initial BP receipt for the frozen three-arm Holm family; one shared MBBP member receipt for list/vote; exact no-decoder byte replay; distinct Relay, Beam, and MBBP profile origins; zero/short matched-family phase-incompletion; and separate convergence/iteration values with reasoned N/A/unavailable states.

## Manual and External Verification

| Behavior | Requirement | Status and reason | Instructions |
| --- | --- | --- | --- |
| Source-authored numeric target or digitization audit | EVAL-01, EVAL-02 | Manual source inspection; unavailable artifacts remain blocked | Compare literal points, locator, source digest, rounding/digitization interval, and extraction receipt before freezing an assessment. Never infer absent coordinates. |
| Native executable/source receipt qualification | EVAL-01 | External artifacts may remain unavailable or unverified | Record request/provenance facts and exact blocker. Qualify later only from a digest-bound executable/source receipt; do not silently substitute the canonical adaptation. |
| Journal-grade reproduction tolerance | EVAL-02 | External scientific/venue criterion remains unknown | Apply factor 1.5 only to the frozen bounded Yao tracer and label it accordingly. Do not promote it to a manuscript-scale or source-faithful curve criterion. |
| Publication-scale site authorization | EVAL-03 | Denied pending measured resource and site-policy receipts | Inspect measured wall time, cores, memory, storage, allocation/accounting policy, and profiling-gate receipt. This draft authorizes no publication Slurm submission. |

## Validation Sign-Off

- [ ] Every task's exact automated command selects at least one test and passes.
- [ ] Every inherited automated command named in a plan also passes.
- [ ] Full suite passes after every wave.
- [ ] Focused and full-suite latency are measured.
- [ ] Receipt reconstruction independently detects tamper and missing inputs.
- [ ] Prospective failure-count plans contain no terminal state, T_r, realized count/resource, prefix/tail digest, or computed interval; those facts appear only in verified post-run receipts.
- [ ] Work/event/evidence/storage bounds are independently derived from executable manifest/policy/ledger/serializer/artifact maxima, including a mandatory partial/interruption-receipt reserve; understated or stale bounds fail before plan freeze.
- [ ] Before every whole failure-count batch, hard resource bounds and nominal wall/local-worker authorizations are checked; evidence/storage stop before append/write, while wall timeout is observed at boundaries with explicit within-iteration overshoot and no later dispatch.
- [ ] New single-arm and multi-arm plans bind their ordinal rule and declared arm order before execution; controlled comparisons reconstruct complete sample-major matched groups.
- [ ] Ordered partial merge/verify exposes the exact resumable missing set, while public assess and terminal verify require every frozen group.
- [ ] Inverse-binomial replay uses exact `T_r`; authorized terminal tail is excluded from inference and included in actual cost.
- [ ] Relay, Beam, and MBBP projections each trace to their own representative pre-outcome profile receipt; cross-family/Yao substitution fails.
- [ ] Update/schedule, memory/intervention, and search/selection each contain the frozen positive N complete matched evaluative samples; otherwise `phase_status=incomplete` is verified.
- [ ] Convergence and iterations remain separate through Relay/Beam/MBBP leaves, reports, and evidence index, with typed N/A/unavailable reasons.
- [ ] Initial/Relay/Beam share one initial receipt per sample in a frozen three-arm/two-contrast Holm family; MBBP list/vote share one member-set receipt with no decoder rerun.
- [ ] Ordinary two-arm schedule controls and shared-MBBP controls each pass public plan/run-local/merge/resume/assess/verify, including partial inside-group retention and exact no-duplicate resume.
- [ ] The closeout audit explicitly covers Plans 09-01 through 09-20 and fails phase completion if a required gap-plan summary or receipt is missing.
- [ ] External blockers remain typed `unavailable`, `unverified`, or `blocked` until qualifying evidence exists.
- [ ] `nyquist_compliant: true` and `wave_0_complete: true` are set only after execution evidence supports them.

**Approval:** pending plan execution and independent verification
