---
phase: "09"
slug: "css-reproduction-and-controlled-comparisons"
status: verified
threats_open: 0
threats_total: 88
asvs_level: 1
created: "2026-10-12"
---

# Phase 9 security verification

The 20 plan-time STRIDE registers contain 88 unique threats: 49 high, 19 medium, and 20 low accepted dependency risks. This audit checks the planned mitigations against the code, focused tests, retained receipts, and public replay. The accepted risks concern existing dependencies only; this phase installed no packages. No source-authenticity or HPC site-ceiling fact is inferred from content hashes or local runs.

## Trust boundaries

| Boundary | Control |
|---|---|
| Source artifact to qualification | Exact source snapshots, ordered identity, native availability, and monotone labels; missing author facts stay blocked. |
| Frozen campaign to execution | Strict manifests and bounded prospective plans, independent executable-limit derivation, one local worker, and guarded serializer. |
| Decoder evidence to assessment | Immutable attempts, shared-input lineage, exact ordered/pair coverage, original-problem validation, and no-decoder report replay. |
| Local evidence to publication | Typed resource missingness and explicit `publication_slurm_authorization: deny`. |

## Threat register

`campaigns/` source paths below are relative to `src/bp_registry/`; test filenames are relative to `tests/`. Each row retains the planned mitigation. `closed` means the named implementation/test or retained receipt supports the mitigation; `accepted` means the plan-time low dependency risk was accepted because no installation occurs.

| Threat | Category | Component | Severity | Disposition | Planned mitigation | Evidence | Status |
|---|---|---|---|---|---|---|---|
| T-09-01A | Tampering | source qualification | high | mitigate | Bind exact revisions, byte snapshots, ordered identities, blockers, and canonical receipt digests. | `campaigns/targets.py`; `test_campaign_targets.py` | closed |
| T-09-01B | Spoofing | native implementation identity | high | mitigate | Require repository/revision/environment/settings receipts or a typed unverified state. | `campaigns/targets.py`; `test_campaign_targets.py` | closed |
| T-09-01C | Denial of Service | receipt payloads | medium | mitigate | Bound strings, collections, snapshots, and paths before allocation or parsing. | `campaigns/targets.py`; `test_campaign_targets.py` | closed |
| T-09-01SC | Tampering | dependencies | low | accept | No install occurs; this plan uses the pinned project stack only. | `campaigns/targets.py`; `test_campaign_targets.py` | accepted |
| T-09-02A | Tampering | authored target transcription | high | mitigate | Store literal decimals, source snapshot digest, exact locator, rounding interval, and exact-vector tests. | source target receipts; `test_phase9_source_receipts.py` | closed |
| T-09-02B | Spoofing | B1 experiment identity | high | mitigate | Bind ordered-artifact gaps and reject common-name equivalence. | source target receipts; `test_phase9_source_receipts.py` | closed |
| T-09-02C | Repudiation | stopping evidence | medium | mitigate | Keep point-level source anchors and unresolved states instead of cross-figure inheritance. | source target receipts; `test_phase9_source_receipts.py` | closed |
| T-09-02SC | Tampering | dependencies | low | accept | No package installation occurs. | source target receipts; `test_phase9_source_receipts.py` | accepted |
| T-09-03A | Tampering | qualification compiler | high | mitigate | Recompute input digests, sort deterministically, reject duplicates, and compare checked-in bytes. | `literature.py`; `test_phase9_source_qualification.py` | closed |
| T-09-03B | Spoofing | source-faithful flag | high | mitigate | Require all D-02 predicates and receipt digests before true. | `literature.py`; `test_phase9_source_qualification.py` | closed |
| T-09-03C | Repudiation | unavailable author artifacts | medium | mitigate | Record access scope/date/reason and permit later qualification without erasing history. | `literature.py`; `test_phase9_source_qualification.py` | closed |
| T-09-03SC | Tampering | dependencies | low | accept | No install occurs. | `literature.py`; `test_phase9_source_qualification.py` | accepted |
| T-09-04A | Tampering | stopping discriminator | high | mitigate | Closed unions and cross-field validation reject sampling-design substitution. | `campaigns/contracts.py`; `test_campaign_contracts.py` | closed |
| T-09-04B | Denial of Service | failure target and caps | medium | mitigate | Bound all integer/resource fields before planning or allocation. | `campaigns/contracts.py`; `test_campaign_contracts.py` | closed |
| T-09-04C | Repudiation | stopping/tail state | high | mitigate | Bind global order, exact target-th failure ordinal, inferential prefix, authorized tail, cap reason, and authorization receipts. | `campaigns/contracts.py`; `test_campaign_contracts.py` | closed |
| T-09-04SC | Tampering | dependencies | low | accept | No install occurs. | `campaigns/contracts.py`; `test_campaign_contracts.py` | accepted |
| T-09-05A | Tampering | sampling-design mapping | high | mitigate | Persist global order, exact `T_r`, prefix/tail split, and test enumerated tails plus tail invariance against SciPy. | `campaigns/statistics.py`; `test_campaign_statistics.py` | closed |
| T-09-05B | Tampering | target verdict | high | mitigate | Bind every input digest and retain source interval, tolerance, computed interval, and algebra separately. | `campaigns/statistics.py`; `test_campaign_statistics.py` | closed |
| T-09-05C | Denial of Service | root inversion | medium | mitigate | Bound counts/probabilities and use finite deterministic root brackets. | `campaigns/statistics.py`; `test_campaign_statistics.py` | closed |
| T-09-05SC | Tampering | dependencies | low | accept | SciPy is already pinned; no install occurs. | `campaigns/statistics.py`; `test_campaign_statistics.py` | accepted |
| T-09-06A | Tampering | stop/censor receipt | high | mitigate | Verify sealed shards, canonical merge bytes, exact unit coverage, and atomic receipt publication. | `campaigns/execution.py`, `cli.py`; `test_campaign_failure_count.py` | closed |
| T-09-06B | Repudiation | ordered stop/tail | high | mitigate | Retain canonical ordinal lineage, exact `T_r`, prefix/tail digests, partial counts, and stop reason. | `campaigns/execution.py`, `cli.py`; `test_campaign_failure_count.py` | closed |
| T-09-06C | Denial of Service | dispatcher | medium | mitigate | Enforce frozen shot/work/event/evidence/storage caps before each whole batch. | `campaigns/execution.py`, `cli.py`; `test_campaign_failure_count.py` | closed |
| T-09-06SC | Tampering | dependencies | low | accept | No package installation occurs. | `campaigns/execution.py`, `cli.py`; `test_campaign_failure_count.py` | accepted |
| T-09-07A | Tampering | electorate construction | high | mitigate | Reconcile every declared member to one admitted ballot or typed exclusion and reject duplicates. | `canonical/candidate_selection.py`, `phase6.py`, `mbbp.py`; `test_voting.py`, `test_mbbp.py` | closed |
| T-09-07B | Information Disclosure | voting policy | high | mitigate | Pass only decoder-visible candidates; test invariance when hidden truth changes. | `canonical/candidate_selection.py`, `phase6.py`, `mbbp.py`; `test_voting.py`, `test_mbbp.py` | closed |
| T-09-07C | Tampering | aggregate validity | high | mitigate | Recompute the original syndrome independently and retain invalid aggregates without repair. | `canonical/candidate_selection.py`, `phase6.py`, `mbbp.py`; `test_voting.py`, `test_mbbp.py` | closed |
| T-09-07D | Denial of Service | ballot payload | medium | mitigate | Bound member count and correction length through the manifest and immutable original problem. | `canonical/candidate_selection.py`, `phase6.py`, `mbbp.py`; `test_voting.py`, `test_mbbp.py` | closed |
| T-09-07SC | Tampering | dependencies | low | accept | No package installation occurs. | `canonical/candidate_selection.py`, `phase6.py`, `mbbp.py`; `test_voting.py`, `test_mbbp.py` | accepted |
| T-09-08A | Tampering | policy-file vote fields | high | mitigate | Closed parser, raw/compiled digests, strict preflight, and unknown-key rejection. | public vote manifest/ledger; `test_canonical_cli.py`, `test_literature_policy.py` | closed |
| T-09-08B | Tampering | vote ledger replay | high | mitigate | Recompute semantic events, lineage, work, aggregate, and original validity from immutable inputs. | public vote manifest/ledger; `test_canonical_cli.py`, `test_literature_policy.py` | closed |
| T-09-08C | Spoofing | source status | high | mitigate | Carry qualification receipt/blockers and enforce canonical-adaptation/not-assessed labels. | public vote manifest/ledger; `test_canonical_cli.py`, `test_literature_policy.py` | closed |
| T-09-08SC | Tampering | dependencies | low | accept | No package installation occurs. | public vote manifest/ledger; `test_canonical_cli.py`, `test_literature_policy.py` | accepted |
| T-09-09A | Tampering | profile receipt | high | mitigate | Bind verified run/merge/replay hashes and producer-qualified measurements. | profile receipts; `test_phase9_profile_gate.py` | closed |
| T-09-09B | Spoofing | site capability | high | mitigate | Preserve unavailable site/scheduler facts and deny publication authorization. | profile receipts; `test_phase9_profile_gate.py` | closed |
| T-09-09C | Denial of Service | profile run | medium | mitigate | One worker, preselected small samples, and strict work/evidence/storage caps. | profile receipts; `test_phase9_profile_gate.py` | closed |
| T-09-09SC | Tampering | dependencies | low | accept | Existing pinned dependencies only. | profile receipts; `test_phase9_profile_gate.py` | accepted |
| T-09-10A | Spoofing | source-faithful identity | high | mitigate | Bind explicit blockers and enforce adaptation-only evidence-state transitions. | B1 plan, cap, assessment receipts; `test_phase9_yao_b1_tracer.py` | closed |
| T-09-10B | Tampering | target/stopping/caps | high | mitigate | Hash shot order, exact `T_100`, prefix/tail receipts, and reject launch/replay drift. | B1 plan, cap, assessment receipts; `test_phase9_yao_b1_tracer.py` | closed |
| T-09-10C | Denial of Service | B1 campaign | medium | mitigate | One worker, whole bounded batches, measured cost projection, and hard work/evidence/storage caps. | B1 plan, cap, assessment receipts; `test_phase9_yao_b1_tracer.py` | closed |
| T-09-10D | Repudiation | censored attempts | medium | mitigate | Retain every attempt, interruption, overshoot, stop/censor, and resource receipt. | B1 plan, cap, assessment receipts; `test_phase9_yao_b1_tracer.py` | closed |
| T-09-10SC | Tampering | dependencies | low | accept | No install occurs. | B1 plan, cap, assessment receipts; `test_phase9_yao_b1_tracer.py` | accepted |
| T-09-11A | Tampering | sample-size design | high | mitigate | Bind all assumptions/receipts and verify minimal N against enumerated small cases. | `campaigns/sizing.py`; `test_campaign_sizing.py` | closed |
| T-09-11B | Information Disclosure | calibration outcomes | medium | mitigate | Enforce namespace disjointness so calibration samples cannot enter evaluation. | `campaigns/sizing.py`; `test_campaign_sizing.py` | closed |
| T-09-11C | Spoofing | publication authorization | high | mitigate | Enforce the Phase 9 result as denied and require measured site receipts in a later separately authorized phase. | `campaigns/sizing.py`; `test_campaign_sizing.py` | closed |
| T-09-11D | Denial of Service | resource projection | medium | mitigate | Bound N and use checked integer/rational arithmetic. | `campaigns/sizing.py`; `test_campaign_sizing.py` | closed |
| T-09-11E | Spoofing | mechanism cost receipt | high | mitigate | Require per-mechanism profile digests and reject Yao or cross-family substitution. | `campaigns/sizing.py`; `test_campaign_sizing.py` | closed |
| T-09-11SC | Tampering | dependencies | low | accept | Existing SciPy only; no installation. | `campaigns/sizing.py`; `test_campaign_sizing.py` | accepted |
| T-09-12A | Tampering | one-factor manifest pair | high | mitigate | Canonically diff every scientific field and allow only schedule. | schedule plan/report; `test_phase9_update_schedule_control.py` | closed |
| T-09-12B | Tampering | pair identity | high | mitigate | Join complete identities and reject duplicate/partial pairs from paired inference. | schedule plan/report; `test_phase9_update_schedule_control.py` | closed |
| T-09-12C | Repudiation | work/runtime attribution | medium | mitigate | Retain configured caps and realized per-arm work/resource receipts separately. | schedule plan/report; `test_phase9_update_schedule_control.py` | closed |
| T-09-12SC | Tampering | dependencies | low | accept | No package installation occurs. | schedule plan/report; `test_phase9_update_schedule_control.py` | accepted |
| T-09-13A | Tampering | shared initial state | high | mitigate | Bind sample, seed, terminal, candidate, state, and work digests across all arms. | shared BP plan/report; `test_phase9_relay_beam_control.py` | closed |
| T-09-13B | Tampering | work/convergence attribution | high | mitigate | Separate initial, Relay, and Beam work plus typed convergence and iteration fields; reconstruct totals from leaves. | shared BP plan/report; `test_phase9_relay_beam_control.py` | closed |
| T-09-13C | Repudiation | family membership | medium | mitigate | Freeze exactly two primary claims before evaluation and preserve unavailable members. | shared BP plan/report; `test_phase9_relay_beam_control.py` | closed |
| T-09-13SC | Tampering | dependencies | low | accept | No installation occurs. | shared BP plan/report; `test_phase9_relay_beam_control.py` | accepted |
| T-09-14A | Tampering | shared member set | high | mitigate | Content-bind every member terminal and require identical receipt hashes across decisions. | shared member plan/report; `test_phase9_mbbp_list_vote_control.py` | closed |
| T-09-14B | Tampering | invalid vote disposition | high | mitigate | Retain invalid/empty/tie/exclusion evidence and forbid list substitution. | shared member plan/report; `test_phase9_mbbp_list_vote_control.py` | closed |
| T-09-14C | Repudiation | cost/status attribution | medium | mitigate | Separate common/decision work, convergence, iterations, and typed N/A/unavailable leaves; reconstruct totals. | shared member plan/report; `test_phase9_mbbp_list_vote_control.py` | closed |
| T-09-14SC | Tampering | dependencies | low | accept | No installation occurs. | shared member plan/report; `test_phase9_mbbp_list_vote_control.py` | accepted |
| T-09-15A | Tampering | evidence index | high | mitigate | Revalidate every input hash and deterministic reconstruction; fail closed on missing items. | `campaigns/evidence_index.py`; `test_phase9_css_evidence_index.py` | closed |
| T-09-15B | Spoofing | evidence status | high | mitigate | Central closed state transitions and tests forbid unsupported promotion. | `campaigns/evidence_index.py`; `test_phase9_css_evidence_index.py` | closed |
| T-09-15C | Repudiation | documentation claims | medium | mitigate | Require every quantitative/status statement to link an index receipt. | `campaigns/evidence_index.py`; `test_phase9_css_evidence_index.py` | closed |
| T-09-15D | Spoofing | phase completion | high | mitigate | Require per-family profile and frozen positive-N complete matched evidence before EVAL-03/phase completion. | `campaigns/evidence_index.py`; `test_phase9_css_evidence_index.py` | closed |
| T-09-15SC | Tampering | dependencies | low | accept | No installation occurs. | `campaigns/evidence_index.py`; `test_phase9_css_evidence_index.py` | accepted |
| T-09-16A | Tampering | prospective policy | high | mitigate | Reject every observed field and bind all policy/cap authorization facts in canonical bytes. | prospective/terminal schemas; `test_campaign_failure_count.py` | closed |
| T-09-16B | Repudiation | terminal receipt | high | mitigate | Bind policy, plan, cap, order, prefix/tail, realized resource, and terminal-reason digests. | prospective/terminal schemas; `test_campaign_failure_count.py` | closed |
| T-09-16C | Denial of Service | cap vector | medium | mitigate | Require finite bounded values for each dispatch-relevant resource dimension. | prospective/terminal schemas; `test_campaign_failure_count.py` | closed |
| T-09-16SC | Tampering | dependencies | low | accept | No package installation occurs. | prospective/terminal schemas; `test_campaign_failure_count.py` | accepted |
| T-09-17A | Tampering | executable-limit receipt | high | mitigate | Independently derive every dimension and require exact digest/value equality before dispatch. | cap and partial receipts; `test_campaign_execution.py`, `test_campaign_failure_count.py` | closed |
| T-09-17B | Denial of Service | bounded dispatch | high | mitigate | Checked projection against every remaining cap and deterministic cap precedence before creating artifacts. | cap and partial receipts; `test_campaign_execution.py`, `test_campaign_failure_count.py` | closed |
| T-09-17C | Repudiation | interrupted attempt | high | mitigate | Atomic immutable partial receipt with exact counters, denied operation, parent lineage, and artifact hashes. | cap and partial receipts; `test_campaign_execution.py`, `test_campaign_failure_count.py` | closed |
| T-09-17D | Tampering | resume selection | high | mitigate | Require one contiguous completed prefix and exactly one digest-linked pending ordinal. | cap and partial receipts; `test_campaign_execution.py`, `test_campaign_failure_count.py` | closed |
| T-09-17SC | Tampering | dependencies | low | accept | No package installation occurs. | cap and partial receipts; `test_campaign_execution.py`, `test_campaign_failure_count.py` | accepted |
| T-09-18A | Tampering | arm/order declaration | high | mitigate | Validate exact arm-set equality and bind rule, arm sequence, groups, ordinals, and keys in a new digest domain. | ordered plan/merge; `test_campaign_execution.py` | closed |
| T-09-18B | Repudiation | merge/resume order | high | mitigate | Reconstruct membership from plan bytes and reject reordered, missing, duplicate, or split groups. | ordered plan/merge; `test_campaign_execution.py` | closed |
| T-09-18C | Spoofing | scheduler authorization | medium | mitigate | Preserve local/direct scope and denied publication Slurm status. | ordered plan/merge; `test_campaign_execution.py` | closed |
| T-09-18SC | Tampering | dependencies | low | accept | No package installation occurs. | ordered plan/merge; `test_campaign_execution.py` | accepted |
| T-09-19A | Tampering | shared input lineage | high | mitigate | Content-bind initial/member receipts and require exact digest equality in every consumer. | `campaigns/controlled*.py`; `test_campaign_execution.py`, `test_campaign_statistics.py` | closed |
| T-09-19B | Repudiation | typed component evidence | high | mitigate | Seal status, iteration, work, runtime, resource, interruption, and provenance leaves at their producer. | `campaigns/controlled*.py`; `test_campaign_execution.py`, `test_campaign_statistics.py` | closed |
| T-09-19C | Tampering | family membership | high | mitigate | Freeze declared arms/comparisons before execution and admit only complete matched groups. | `campaigns/controlled*.py`; `test_campaign_execution.py`, `test_campaign_statistics.py` | closed |
| T-09-19D | Denial of Service | partial lifecycle | medium | mitigate | Retain exact missing sets and immutable interruptions so resume performs only missing work. | `campaigns/controlled*.py`; `test_campaign_execution.py`, `test_campaign_statistics.py` | closed |
| T-09-19SC | Tampering | dependencies | low | accept | No package installation occurs. | `campaigns/controlled*.py`; `test_campaign_execution.py`, `test_campaign_statistics.py` | accepted |
| T-09-20A | Tampering | executable profile | high | mitigate | Closed route registry, digest-bound derivation inputs, exact declaration equality, fail-closed unknown routes. | `runner.py`, guarded serializer; `test_campaign_execution.py`, `test_canonical_cli.py` | closed |
| T-09-20B | Denial of Service | ledger/artifact bytes | high | mitigate | Exact pre-mutation reservations with checked counters and inaccessible control reserve. | `runner.py`, guarded serializer; `test_campaign_execution.py`, `test_canonical_cli.py` | closed |
| T-09-20C | Repudiation | wall interruption | high | mitigate | Named boundary plus before/deadline/after/overshoot facts in a typed snapshot. | `runner.py`, guarded serializer; `test_campaign_execution.py`, `test_canonical_cli.py` | closed |
| T-09-20D | Tampering | V7 voting | high | mitigate | Preserve absent-guard bytes and forbid vote projection from an interrupted incomplete electorate. | `runner.py`, guarded serializer; `test_campaign_execution.py`, `test_canonical_cli.py` | closed |
| T-09-20SC | Tampering | dependencies | low | accept | No package installation occurs. | `runner.py`, guarded serializer; `test_campaign_execution.py`, `test_canonical_cli.py` | accepted |

## Focused audit findings

- The high shared-input lineage and family-membership threats are backed by one shared initial BP or member-set receipt per sample, frozen arm order, exact missing-set merge, and independent report replay. Interrupted first-arm retry now reuses a sealed shared receipt and records each recoverable dispatch exception without exposing the exception message (`8fa9dd9`, `e660bcd`).
- The Yao study remains a labeled canonical adaptation. Its two timeout terminals and cap-censored assessment have no inferred paper rate, target verdict, or source-faithful promotion.
- The retained controls use disjoint calibration/evaluation namespaces, source-specific profiles, shared samples, and typed costs. Small paired N never becomes a superiority claim.
- No publication Slurm dispatch occurred or is authorized. Site limits and accounting remain unavailable.

## Accepted risks log

| Risk | Threats | Rationale | Basis |
|---|---|---|---|
| Existing dependency integrity | All twenty `T-09-xxSC` entries | Plans use the existing pinned environment; no package installation occurred. | Plan-time accepted dispositions and Phase 9 source diff |

## Audit trail

| Date | Threats | Mitigated closed | Accepted closed | Open |
|---|---:|---:|---:|---:|
| 2026-10-12 | 88 | 68 | 20 | 0 |

`threats_open: 0` covers the planned ASVS L1 threat register. This is a code/evidence integrity gate, not author source authentication or production scheduler authorization.
