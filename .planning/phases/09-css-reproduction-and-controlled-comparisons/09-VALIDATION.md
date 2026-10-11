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
| 09-03-01 | 3 | EVAL-01, EVAL-02 | Missing Bhatnagar author data remains unavailable and cannot become a curve | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'bhatnagar and unavailable' -x` | created in task | pending |
| 09-03-02 | 3 | EVAL-01, EVAL-02 | All 14 variants have monotone, tamper-evident qualification states | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_source_qualification.py -k 'inventory or fourteen or monotone or faithful or tamper' -x` | created in task | pending |
| 09-04-01 | 1 | EVAL-02 | Ordered target-th-failure stopping separates inferential prefix, terminal tail, censoring, and interruption | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'stopping or ordered_stop or terminal_tail or denominator or outcome or partial' -x` | existing, expanded in task | green |
| 09-04-02 | 1 | EVAL-02 | Inverse-binomial inference and target tolerance cannot cross sampling designs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_contracts.py -k 'failure_count or inverse_binomial or censor or multiplicative or historical' -x` | existing, expanded in task | green |
| 09-05-01 | 2 | EVAL-02 | Exact inverse-binomial bounds use T_r and remain invariant to authorized terminal tail | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'inverse_binomial or ordered_stop or authorized_tail or coverage or boundary' -x` | existing, expanded in task | green |
| 09-05-02 | 2 | EVAL-02 | Target agreement keeps source precision and prespecified tolerance separate | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_statistics.py -k 'multiplicative or containment or discrepant or inconclusive or target' -x` | existing, expanded in task | green |
| 09-06-01 | 3 | EVAL-02 | Target-reached/censored lifecycle reconstructs canonical order, exact T_r, tail, interruption, and resume | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_failure_count.py -k 'tracer or ordered_stop or terminal_batch_tail or censor or resume or interruption' -x` | created in task | pending |
| 09-06-02 | 3 | EVAL-02 | Public CLI reports and replays ordered prefix/tail receipts with complete costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_failure_count.py -k 'cli or report or replay or ordered_prefix or authorized_tail or tamper or resource' -x` | created in task | pending |
| 09-07-01 | 1 | CAN-02 | Vote executes only over admitted declared members; invalid/empty outcomes stay visible | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py -k 'vote or electorate or exclusion or invalid or empty or list_regression' -x` | existing, expanded in task | green |
| 09-07-02 | 1 | CAN-02 | Ballots and lineage are deterministic and original validation remains independent | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py tests/canonical/test_mbbp.py -k 'vote or tie or order or original_valid or lineage' -x` | existing, expanded in task | green |
| 09-08-01 | 4 | CAN-02 | Public vote ledger runs, verifies, rejects tamper, independently replays, and carries the declared tie bit through both canonical paths | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_canonical_cli.py -k 'vote and (run or verify or tamper or replay)' -x` | existing, expanded in task | pending |
| 09-08-02 | 4 | EVAL-01, CAN-02 | Tracked vote policy compiles and replays with explicit adaptation status | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_css_literature_gate.py -k 'vote or policy_file or replay or cache or adaptation' -x` | existing, expanded in task | pending |
| 09-09-01 | 4 | EVAL-02, EVAL-03 | Small public policy path reaches a verified sealed merge under bounded caps | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_profile_gate.py -k 'tracer or policy or ledger or seal or merge' -x` | created in task | pending |
| 09-09-02 | 4 | EVAL-02, EVAL-03 | Independent replay emits receipt-linked measurements and leaves production denied | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_profile_gate.py -k 'measured or replay or unavailable or denied or receipt' -x` | created in task | pending |
| 09-10-01 | 5 | EVAL-01, EVAL-02 | Bounded Yao B1 launches only after the measured gate and retains its first whole batch | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_yao_b1_tracer.py -k 'profile_gate or preflight or first_batch or replay or label' -x` | created in task | pending |
| 09-10-02 | 5 | EVAL-01, EVAL-02 | Resume closes at exact T_100 with tail excluded or an honest cap-censored terminal | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_yao_b1_tracer.py -k 'resume or target_reached or target_ordinal or authorized_tail or censor or final_report or interruption' -x` | created in task | pending |
| 09-11-01 | 5 | EVAL-03 | Paired sizing uses disjoint calibration and reports powered and bounded boundaries | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_sizing.py -k 'paired or power or disjoint or blocked or boundary' -x` | created in task | pending |
| 09-11-02 | 5 | EVAL-03 | Relay, Beam, and MBBP use separate profiles and positive bounded N while Slurm stays denied | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_sizing.py -k 'resource or representative_profile or relay or beam or mbbp or positive_n or slurm or missing' -x` | created in task | pending |
| 09-12-01 | 6 | EVAL-03 | Schedule control changes one factor and requires frozen positive-N matched execution | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_update_schedule_control.py -k 'one_factor or positive_n or matched_evidence or paired_execution or phase_incomplete or label' -x` | created in task | pending |
| 09-12-02 | 6 | EVAL-03 | Schedule replay keeps completion gate, paired/all-shot denominators, and realized costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_update_schedule_control.py -k 'assessment or cost or replay or all_shot or conditional' -x` | created in task | pending |
| 09-13-01 | 6 | EVAL-03 | Relay uses its own profile, positive N, shared initial BP, and separate convergence/iterations | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_beam_relay_control.py -k 'relay or relay_profile or positive_n or shared_initial or convergence or iterations or extra_work or phase_incomplete' -x` | created in task | pending |
| 09-13-02 | 6 | EVAL-03 | Beam uses its own profile, positive N, typed status fields, replay, and multiplicity | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_beam_relay_control.py -k 'beam or beam_profile or positive_n or shared_initial or convergence or iterations or holm or incomplete or replay' -x` | created in task | pending |
| 09-14-01 | 6 | EVAL-03, CAN-02 | MBBP uses its own profile/positive N; members expose convergence/iterations and decisions preserve dispositions | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_vote_list_control.py -k 'mbbp_profile or positive_n or shared_members or convergence or iterations or vote or list or disposition or original_validation or phase_incomplete' -x` | created in task | pending |
| 09-14-02 | 6 | EVAL-03, CAN-02 | Replay preserves typed fields, completion, denominators, labels, and common/decision costs | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_vote_list_control.py -k 'cost or replay or convergence or iterations or completion or label or assessment or denominator' -x` | created in task | pending |
| 09-15-01 | 7 | EVAL-01, EVAL-02, EVAL-03, CAN-02 | Index reconstructs ordered-stop, profile, positive-N, typed status, and phase-completion evidence | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_css_evidence_index.py -k 'coverage or fourteen or ordered_stop or tail or positive_n or convergence or iterations or phase_status or reconstruct or tamper or cost' -x` | created in task | pending |
| 09-15-02 | 7 | EVAL-01, EVAL-02, EVAL-03, CAN-02 | Guide preserves completion blockers, typed fields, external unknowns, denied Slurm, and no-overclaim labels | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase9_css_evidence_index.py -k 'guide or paper_records or ordered_stop or completion_blocker or convergence or iterations or external_unknown or no_overclaim or slurm_denied' -x` | created in task | pending |

*Status values: pending, green, red, flaky. “Created in task” means the task uses TDD and must make the selected test fail before implementation.*

## Completed Wave Gates

| Wave | Completed plans | Full-suite result | Elapsed | Peak RSS | Status |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 09-01, 09-04, 09-07 | 1,170 passed, 1 skipped | 828.10 s | unavailable (not measured) | green |
| 2 | 09-02, 09-05 | 1,184 passed, 1 skipped | 873.65 s | 383,736 KiB | green |

The observed peak is for the pytest child process, measured with `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`; it is a local test-suite measurement, not an HPC job allocation or production campaign ceiling.

## Wave 0 Requirements

No separate Wave 0 is required. Every new fixture/test file is owned by the same TDD task that consumes it, and all inherited test files already exist. Before implementation, each task must demonstrate that its newly selected behavior is red rather than accepting a zero-test selection. Required fixtures include target failure at the first/middle/last terminal-batch ordinal with tail invariance; distinct Relay, Beam, and MBBP profile origins; zero/short matched-family phase-incompletion; and separate convergence/iteration values with reasoned N/A/unavailable states.

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
- [ ] Inverse-binomial replay uses exact `T_r`; authorized terminal tail is excluded from inference and included in actual cost.
- [ ] Relay, Beam, and MBBP projections each trace to their own representative pre-outcome profile receipt; cross-family/Yao substitution fails.
- [ ] Update/schedule, memory/intervention, and search/selection each contain the frozen positive N complete matched evaluative samples; otherwise `phase_status=incomplete` is verified.
- [ ] Convergence and iterations remain separate through Relay/Beam/MBBP leaves, reports, and evidence index, with typed N/A/unavailable reasons.
- [ ] External blockers remain typed `unavailable`, `unverified`, or `blocked` until qualifying evidence exists.
- [ ] `nyquist_compliant: true` and `wave_0_complete: true` are set only after execution evidence supports them.

**Approval:** pending plan execution and independent verification
