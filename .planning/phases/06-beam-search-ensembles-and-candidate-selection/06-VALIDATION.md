---
phase: "06"
slug: "beam-search-ensembles-and-candidate-selection"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-10-05"
---

# Phase 06 — Validation Strategy

This contract validates only the remaining Phase 6 gaps. The tracked fair BeamSearch/RelayBP implementation and published BB72 package are regression-checked and reused; the campaign is not rerun. The new evidence is a bounded, `not_assessed` B1 gate for Yao BPGD, Bhatnagar impulse, and Rabeti–Mahdavifar MBBP-LD. Full published-curve assessment remains in Phases 8–9.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9 with deterministic validation scripts |
| Config | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <target> -x` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Scientific fixtures | Small binary hand oracles plus a fixed small-shot B1 gate |
| Existing evidence | `data/results/fair-beam-relay-css-v2/` is verification/reuse input only |

## Sampling Rate

- After every task, run its exact focused target and require selected tests to be collected.
- After Waves 2 and 3, run parser, guided-decimation, impulse, selection/voting, and existing fair-evidence regressions.
- After Waves 4 and 5, run MBBP unit/public replay plus historical manifest tests.
- In Wave 6, freeze the B1 gate, compute one policy per paper, invoke each again for verified reuse, and retain every terminal.
- Before phase verification, run the gate verifier, focused Phase 6 suite, existing sealed-package reuse test, and full pytest suite.
- No Phase 8/9 curve grid or completed BB72 campaign is launched by validation.

## Per-Task Nyquist Matrix

| Task | Wave | Requirement | Automated command | Expected failing direction | Ownership |
|---|---:|---|---|---|---|
| 06-01-01 | 1 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'tracer or strict_parser or schema5 or schema6 or bp_t100 or non_runnable_before_artifact' -x` | Fails if metadata executes, an unknown kind/control passes, a source spec reaches artifact I/O, or schemas 5/6 cannot use the common command. | Creates `tests/test_literature_policy.py`; extends existing study test. |
| 06-01-02 | 1 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'execution_identity or provenance_identity or raw_document or shared_compute or request_receipt or tamper' -x` | Fails if prose changes computation identity, executable changes reuse, the second provenance overwrites the first, or tampered evidence is reused. | Test paths exist from 06-01-01. |
| 06-02-01 | 2 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/canonical/test_guided_decimation.py -k 'yao or bpgd or round_limit or sweeps_per_round or zero or final_round' -x` | Fails for a missing variant, swapped T/R, wrong symbolic code length, zero-rule drift, or an extra final sweep. | Existing/new tests. |
| 06-02-02 | 2 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py -k 'bpgd_t001 and (runnable or source_agreement or qualification)' -x` | Fails if runnable/source controls differ or unresolved identities are promoted. | Existing new test file. |
| 06-03-01 | 2 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_impulse.py -k 'forced_zero or forced_one or forced_value or first_convergence or minimum_weight or historical' -x` | Fails if zero aliases one, the value is absent from evidence/identity, selection order changes, or legacy routes drift. | Extends existing impulse test. |
| 06-03-02 | 2 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_impulse.py -k 'v2c_clip or clip_boundary or finite or fresh or replay or original' -x` | Fails if clipping is global, absent from identity, nonfinite, state leaks between attempts, or original validation is skipped. | Existing impulse test. |
| 06-04-01 | 3 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'bhatnagar or minimum_weight or first_convergence or forced_zero or forced_one or v2c_clip' -x` | Fails for a semantic alias, wrong selector, missing clip, hidden schedule default, or missing variant. | Test files from 06-01. |
| 06-04-02 | 3 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'first_convergence_0 and (runnable or public or reuse or original)' -x` | Fails if the promoted policy does not run/reuse or ledger evidence does not show forced zero and original validation. | Test files from 06-01. |
| 06-05-01 | 2 | CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_candidate_selection.py -k 'eligibility or origin or duplicate or score or tie or worker or nonfinite' -x` | Fails if any losing origin disappears, nonfinite scores pass, duplicate frequency erases provenance, or worker order changes selection. | Creates candidate-selection test. |
| 06-05-02 | 2 | CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py -k 'electorate or ballot or majority or tie or invalid or original or worker' -x` | Fails for undeclared/incomplete ballots, nondeterministic ties, hidden repair, or acceptance of an invalid majority. | Creates voting test. |
| 06-05-03 | 2 | MOD-04, INT-05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_existing_evidence.py tests/canonical/test_fair_legs.py tests/test_study_entrypoint.py -k 'phase6 or fair or matched or beam or relay or published or reused' -x` | Fails if matched initial BP, damping, legs/branches, work, source labels, package hashes, or reuse semantics drift; launch calls are forbidden. | Creates existing-evidence regression. |
| 06-06-01 | 3 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py -k 'basis or augmented or syndrome or oracle or immutable or malformed' -x` | Fails if a redundant row/syndrome lacks a valid GF(2) transform, original input mutates, or malformed bases reach BP. | Creates MBBP test with independent oracle. |
| 06-06-02 | 3 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_mbbp.py tests/canonical/test_candidate_selection.py -k 'member or independent or normalized or serial or frequency or weight or no_member_converged or zero_return or worker or work or replay' -x` | Fails if members share state, use the wrong kernel/schedule, miscount duplicates, admit the source zero-return failure as a candidate, change by worker order, or double-count work. | MBBP and selection tests, including an independent all-members-fail nonzero-syndrome fixture. |
| 06-07-01 | 4 | INT-05, CAN-01, CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py tests/test_manifest.py -k 'phase6 and (schema or preflight or mbbp or ensemble or vote or historical or unsupported)' -x` | Fails if caps/compatibility are incomplete, unsupported state/kernel/voting passes, or historical manifests drift. | Creates public Phase 6 test. |
| 06-07-02 | 4 | INT-05, CAN-01, CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py -k 'public_execution or no_member_converged or zero_return or replay or original or truth_boundary or tamper or duplicate or missing or work or runtime' -x` | Fails if replay trusts summaries, misses an origin/leaf, permits semantic tampering, admits/evaluates the no-member zero sentinel, evaluates truth before valid selection, or compares timing as deterministic science. | Public test from 06-07-01 plus an independent all-members-fail public fixture. |
| 06-08-01 | 5 | INT-05, CAN-01 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'rabeti or mbbp or augmented_basis or frequency or no_member_converged or zero_return or source_gap' -x` | Fails if source controls map incorrectly, missing basis identity defaults silently, the zero-return failure becomes selectable, or unresolved settings disappear. | Test files from 06-01. |
| 06-08-02 | 5 | INT-05, CAN-01, CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_literature_policy.py tests/test_study_entrypoint.py -k 'mbbp_ld and (runnable or public or no_member_converged or zero_return or reuse or receipt or original)' -x` | Fails if MBBP cannot compute/reuse through the common command, the no-member failure produces a selected/evaluated zero correction, or receipts/member/original evidence are incomplete. | Test files from 06-01; covers both selected-candidate and no-member outcomes. |
| 06-09-01 | 6 | MOD-04, INT-05, CAN-01, CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_css_literature_gate.py -k 'design or artifact or denominator or caps or dispositions or source_status' -x` | Fails for unpinned B1 identity, open work/denominator, any missing source record, or a source-faithful claim with unresolved blockers. | Creates gate test and runner. |
| 06-09-02 | 6 | MOD-04, INT-05, CAN-01, CAN-02 | Ordered commands: gate runner `run`; gate runner `cli-smoke --bp-registry .venv/bin/bp-registry`; gate runner final `verify`; focused compute/reuse/tamper pytest target | The smoke helper invokes all three exact installed CLI commands, parses JSON, requires `status == "reused"`, and fails for changed output identity, ledger/result hash, denominator, or shot count. Final verification also fails for absent/incomplete/tampered runs, receipt/replay mismatch, invalid original candidate, or compute/reuse inconsistency. | Runner from 06-09-01 owns the assertion logic; selected files are Yao `bpgd-t001.toml`, Bhatnagar `first-convergence-0.toml`, and Rabeti–Mahdavifar `mbbp-ld.toml`. Exact user commands remain in documentation. |
| 06-09-03 | 6 | MOD-04, INT-05, CAN-01, CAN-02 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_css_literature_gate.py tests/test_phase6_existing_evidence.py -k 'documentation or claim_limit or phase5_review or fair_evidence or all_variants' -x` | Fails if docs hide a source gap, omit a variant/result, promote bounded evidence, lose Phase 5 review status, or imply the BB72 campaign was rerun. | Gate/existing tests. |

## Wave 0 and Test Creation

No command references a test path without a creation owner. The first task that adds behavior creates or extends its test before implementation. `wave_0_complete` remains false until execution records the intended RED direction for the new paths.

| Test path | Creation owner | First behavior gated |
|---|---|---|
| `tests/test_literature_policy.py` | 06-01-01 | strict parser/projections and typed dispositions |
| `tests/canonical/test_candidate_selection.py` | 06-05-01 | complete candidate list and stable selection |
| `tests/canonical/test_voting.py` | 06-05-02 | declared electorate/ballots and invalid-majority rejection |
| `tests/test_phase6_existing_evidence.py` | 06-05-03 | read-only fair BeamSearch/RelayBP package regression |
| `tests/canonical/test_mbbp.py` | 06-06-01 | basis algebra, members, list, and work |
| `tests/test_phase6_public_execution.py` | 06-07-01 | strict public ensemble contract and replay |
| `tests/test_css_literature_gate.py` | 06-09-01 | frozen B1 gate, dispositions, evidence, and claims |

## Multi-Source Coverage Audit

### GOAL — ROADMAP Phase 6

| Source item | Coverage | Plans |
|---|---|---|
| SC1 canonical BeamSearch branch/mask/rank/prune/budget/selection evidence | COVERED by tracked implementation plus read-only regression; no superseded native plan restored | 06-05, 06-09 |
| SC2 generic members, inherited/independent state, limits, unique work | COVERED by tracked fair legs and new MBBP independent-member public evidence | 06-05, 06-06, 06-07 |
| SC3 candidate origins, eligibility, scores/ties, precise voting and original validation | COVERED | 06-05, 06-07 |
| SC4 replay accepted/rejected/pruned/denied/budget paths | COVERED by existing fair replay plus complete new ensemble replay | 06-05, 06-07, 06-09 |
| SC5 three-paper policy files, one bounded variant each, all dispositions, provenance/original checks | COVERED | 06-01–04, 06-06–09 |

### REQ — REQUIREMENTS.md

| Requirement | Coverage | Plans |
|---|---|---|
| MOD-04 source-linked BeamSearch controls and evidence | COVERED by existing implementation/evidence regression; new native/AutDEC work excluded by binding replan | 06-05, 06-09 |
| INT-05 parent/member identity, state mode, resource limits, aggregated work | COVERED | 06-01–09 |
| CAN-01 declared candidate eligibility/scoring/ties with rejected origins | COVERED | 06-02–09 |
| CAN-02 declared voting object/electorate and independent final validity | COVERED | 06-05, 06-07, 06-09 |

### RESEARCH — Binding 2026-10-05 Findings

| Research item | Coverage | Plans |
|---|---|---|
| Strict executable/provenance/raw projections and metadata-safe reuse | COVERED | 06-01 |
| V5/V6 BPGD and impulse study dispatch | COVERED | 06-01–04 |
| Force-to-zero is a real behavior and V2C clip is scoped | COVERED | 06-03–04 |
| MBBP augmented bases, independent members, list frequency/weight score | COVERED | 06-05–08 |
| MBBP no-member-converges return-zero failure semantics | COVERED by typed terminal, separate sentinel, no candidate/evaluator admission, complete work/ledger/replay, and independent nonzero-syndrome fixture | 06-06–08 |
| B1 local identity verified; paper artifact identity unresolved | COVERED | 06-09 |
| Full curves deferred to campaign/assessment phases | EXCLUDED as explicitly scoped to Phases 8–9 | 06-09 documentation |

### CONTEXT — Locked Decisions and Literature Gate

| Context decision | Coverage | Plans |
|---|---|---|
| Common matched initial min-sum BP for Beam/Relay | COVERED by existing-evidence regression | 06-05 |
| Relay extra unit/state reset/disordered interval semantics | COVERED by existing-evidence regression | 06-05 |
| Beam decimated branch/mask/warm-start/pruning semantics | COVERED by existing-evidence regression | 06-05 |
| Damping gamma 0.5 and off control 1.0 | COVERED by existing-evidence regression | 06-05 |
| Same extra C2V ceiling, separate typed work/runtime | COVERED by existing-evidence regression | 06-05 |
| Separate selection/evaluation samples and no fixture ranking | COVERED by sealed package regression and claim tests | 06-05, 06-09 |
| Parser/manifest extension and V5/V6 BPGD/impulse route | COVERED | 06-01–04 |
| MBBP subtree/member/list semantics | COVERED | 06-05–08 |
| One command, one bounded variant per paper, all typed dispositions | COVERED | 06-09 |
| Source artifact matching remains explicit and conditional | COVERED | 06-02, 06-04, 06-08, 06-09 |
| Phase 5 human review remains visible | COVERED | 06-05, 06-09 |
| Superseded AutDEC/native BeamSearch and BB72 rerun | EXCLUDED by binding context and parent instruction | Regression tests fail if reintroduced or launched |

No GOAL, REQ, binding RESEARCH, or locked CONTEXT item is missing from the plan set.

## Scientific Qualification Gates

- Yao: Algorithm 1 versus equation zero-boundary interpretation stays explicit; local B1 ordered artifact and author implementation remain unverified.
- Bhatnagar: force suffix changes real behavior; flooding and finite infinity realization remain declared interpretations; V2C clip placement is independently checked.
- Rabeti–Mahdavifar: local partition/permutation and tie completion are explicit canonical choices; source-faithful status remains blocked.
- Rabeti–Mahdavifar no-convergence: the paper-declared zero return is a recorded failure sentinel under `no_member_converged_zero_return`; it is never a selected correction, never receives a successful original-check claim, and never reaches truth-aware evaluation. Independent kernel and public fixtures force all members to fail on a nonzero syndrome and verify complete member/work replay.
- B1: raw/semantic local identities are pinned, but equality to each paper's experimental ordered matrices/logicals is unresolved.
- Every B1 run is `pilot_adaptation`/`not_assessed`; a small fixed denominator cannot rank decoders or reproduce a curve.

## Manual-Only Verification

| Behavior | Why manual | Procedure |
|---|---|---|
| Phase 5 notebook/HTML visual review | Automated checks cannot judge visual clarity; Phase 5 verification left this human-pending | Keep the status visible and complete the existing Phase 5 UAT separately. It does not block authorized Phase 6 coding. |
| Future source-faithful promotion | Requires exact paper artifacts/settings or author confirmation not present in the repository | Review new primary evidence, update the paper reproduction record, and rerun qualification before changing the closed source status. |

## Sign-Off

- [x] Every task has a runnable automated command and a stated failure direction.
- [x] Every new test path has a same-task creation owner.
- [x] All roadmap requirements and success criteria have coverage.
- [x] Existing fair BeamSearch/RelayBP evidence is reused and regression-checked.
- [x] No package install or native reference build is planned.
- [ ] Task-owned RED tests have been created and observed during execution.
- [ ] Three bounded B1 paper-family runs compute, verify, and reuse.
- [ ] All fourteen typed dispositions and retained receipts pass validation.
- [ ] Focused and full test suites pass.
- [ ] Set `wave_0_complete: true`, `status: validated`, and record execution evidence.

**Approval:** pending execution.
