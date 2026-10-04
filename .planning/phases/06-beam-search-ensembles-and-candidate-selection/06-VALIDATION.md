---
phase: "06"
slug: "beam-search-ensembles-and-candidate-selection"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-10-04"
---

# Phase 06 — Validation Strategy

This is the executable validation contract for MOD-04, INT-05, CAN-01, and CAN-02. It validates source-qualified masked min-sum BeamSearch, the pinned C++ sentinel/reuse behavior, the AutDEC `U_A H = H A` coordinate convention, generic list/vote policies, typed work, public replay, and the mandatory isolated native build attempt. Deterministic fixtures are `development_fixture`/`not_assessed`; they do not establish a paper-curve reproduction or decoder ranking.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 plus deterministic validation scripts |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q <target> -x` |
| Full suite | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Existing full-suite baseline | 716 passed, 1 skipped in approximately 392 seconds before Phase 6 implementation |
| Targeted feedback latency | Under 120 seconds per ordinary task; native dependency/build and the full suite are explicit long-running gates |

## Sampling Rate

- After every task: run the exact task command in the matrix and retain its exit status.
- After Waves 2 through 5: run the focused Phase 6 modules created so far and the existing Phase 5 session/budget compatibility targets touched by that wave.
- After Wave 6: run all canonical Phase 6 modules plus public preflight/run/verify.
- After Wave 7: rerun those targets, structural replay, and the approved native qualification/build/smoke validator.
- After Wave 8: run `scripts/validate_phase6_design.py --check`, every focused Phase 6 target, and `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q`.
- Before `$gsd-verify-work 06`: rerun the full suite, public structural replay, native build/smoke receipt validation, and the source-status/claim-limit tests.
- Do not launch a performance campaign as part of this phase gate.

## Per-Task Nyquist Matrix

| Task ID | Plan | Wave | Requirement | Threat | Automated command | Expected failing direction | Test ownership | Latency |
|---|---:|---:|---|---|---|---|---|---|
| 06-01-01 | 01 | 1 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-01/02 | `OMP_NUM_THREADS=1 .venv/bin/python scripts/preview_phase5_notebook.py --executed data/results/phase5-notebook/phase5-interventions.ipynb --html data/results/phase5-notebook/phase5-interventions.html --check` | Fails for missing, stale, hash-inconsistent, or structurally incomplete retained export; human readability still requires the checkpoint. | Existing Phase 5 script/artifacts | <30s plus human review |
| 06-02-01 | 02 | 2 | MOD-04, INT-05 | T-06-03/04/05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_beam_search.py -k 'tracer or masked_child or min_sum_profile or spa_adaptation or original_validation' -x` | RED before implementation; fails if a source profile uses SPA, profile identities alias, masks update excluded edges, or original validity is skipped. | Task creates `tests/canonical/test_beam_search.py` before production code | <60s |
| 06-02-02 | 02 | 2 | MOD-04, INT-05 | T-06-03/05 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_beam_search.py -k 'state_transfer or warm_start or cumulative or denial or immutable' -x` | Fails for partial/incompatible snapshots, denied-work mutation, incorrect accumulator iteration count, or root-state mutation. | Test file created by 06-02-01; task adds named cases first | <60s |
| 06-03-01 | 03 | 3 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-06/07/08 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase6_replay_budget.py -k 'tracer or version5 or unique_leaf or span' -x` | RED before implementation; fails if version-5 fields are incomplete, leaves double-count, runtime enters structural equality, or span is not DAG-derived. | Task creates `tests/canonical/test_phase6_replay_budget.py` first | <60s |
| 06-03-02 | 03 | 3 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-06/07/08 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase6_replay_budget.py tests/canonical/test_budgets.py -k 'historical or discarded or denial or conflict or identity or cycle' -x` | Fails if discarded origins disappear, conflicting leaves overwrite, cycles pass, denial mutates, or versions 2-4/V2-V7 change grammar. | Existing/new files owned by 06-03-01/02 | <90s |
| 06-04-01 | 04 | 4 | CAN-01, INT-05 | T-06-09/10/11 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_candidate_selection.py -k 'tracer or eligibility or tie or discarded or worker' -x` | RED before implementation; fails if ineligible origins win, ties depend on arrival order, or rejected/pruned/duplicate/late/denied origins vanish. | Task creates `tests/canonical/test_candidate_selection.py` first | <45s |
| 06-04-02 | 04 | 4 | CAN-02 | T-06-09/10/11 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_voting.py -k 'plurality or majority or invalid or tie or original' -x` | RED before implementation; fails for undeclared electorate/ballots, nondeterministic ties, missing synthesized lineage, hidden repair, or accepted invalid majority. | Task creates `tests/canonical/test_voting.py` first | <45s |
| 06-05-01 | 05 | 5 | MOD-04, INT-05, CAN-01 | T-06-12/13/14 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_beam_search.py -k 'paper_v2_min_sum or paper_preset or ranking or collective or quota' -x` | Fails if `paper_v2_min_sum_plus_declared_ties` uses SPA, omits declared tie completions, computes the wrong rank, exceeds caps, or selects the wrong fixture result. | Test file from 06-02; task adds paper-profile cases first | <90s |
| 06-05-02 | 05 | 5 | MOD-04, INT-05, CAN-01 | T-06-12/13/14 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_beam_search.py -k 'official_cpp_observed or min_idx_zero or no_eligible_reuse or strict_branch_tie or equal_score_store_idx or source_separation' -x` | Fails if root index-zero filtering is cleaned, stale min_idx is reset, strict branch ties change, equal queue scores do not favor later store indices, or an adapted profile claims the pin. | Test file from 06-02; task adds pinned edge cases first | <90s |
| 06-06-01 | 06 | 5 | INT-05, CAN-01 | T-06-15/16/17 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_ensembles.py -k 'tracer or uah_equals_ha or transformed_syndrome or original_coordinate or original_validation' -x` | RED before implementation; fails if `U_A H != H A`, `(H A)c != U_A s`, an inverse map is applied, or direct `Hc=s` is not checked. | Task creates `tests/canonical/test_ensembles.py` and nontrivial fixture first | <60s |
| 06-06-02 | 06 | 5 | INT-05, CAN-01, CAN-02 | T-06-15/16/17 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_ensembles.py -k 'minimum_weight or fallback or topology or worker or work' -x` | Fails if fallback is silently admitted, weight ties change by completion order, members share state, or serial/concurrent work differs structurally. | Test file from 06-06-01; task adds selection/topology cases first | <90s |
| 06-07-01 | 07 | 6 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-18/19/20/21 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py -k 'tracer or v7 or source_min_sum or spa_adaptation or preflight or public_execution or truth_boundary' -x` | RED before implementation; fails if source profiles accept SPA, adaptations alias source IDs, caps are incomplete, or truth enters before frozen original-valid selection. | Task creates `tests/test_phase6_public_execution.py` first | <90s |
| 06-07-02 | 07 | 6 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-18/19/20/21 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py tests/test_manifest.py -k 'phase6 or ensemble or vote or unsupported or malformed or historical' -x` | Fails if malformed permutations/IDs/caps/paths pass, incompatible votes execute, invalid majority reaches evaluator, or historical manifests drift. | Public test file from 06-07-01 plus existing manifest tests | <120s |
| 06-09-01 | 09 | 7 | MOD-04 | T-06-SC | `bash -lc "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_native_reference.py -k 'dependency_proposal' -x && OMP_NUM_THREADS=1 .venv/bin/python scripts/stage_phase6_beamsearch_reference.py --validate-proposal --source-url https://github.com/ionq-publications/BeamSearchDecoder.git --expected-commit 084a475b05fb64308103317a1ce5a0c4b0be58aa --approval docs/evidence/phase6-native-dependency-approval.json --lock docs/evidence/phase6-native-requirements-lock.txt --wheelhouse data/results/phase6-native-wheelhouse --require-status pending_human_approval"` | RED until validator mode/tests exist; rejects wrong source/digests/status/target, incomplete or cyclic dependency closure, missing/extraneous/duplicate lock entries or wheels, incompatible wheel identity/tags, and any recorded or recomputed SHA-256 mismatch. | Task creates mutation tests and stdlib-only validator mode before preparing and checking the concrete proposal | Resolver/download latency plus <60s validation |
| 06-09-02 | 09 | 7 | MOD-04 | T-06-SC | `OMP_NUM_THREADS=1 .venv/bin/python scripts/stage_phase6_beamsearch_reference.py --validate-proposal --source-url https://github.com/ionq-publications/BeamSearchDecoder.git --expected-commit 084a475b05fb64308103317a1ce5a0c4b0be58aa --approval docs/evidence/phase6-native-dependency-approval.json --lock docs/evidence/phase6-native-requirements-lock.txt --wheelhouse data/results/phase6-native-wheelhouse --allow-status pending_human_approval --allow-status approved` | Fails if any concrete source, graph, lock, target-tag, wheel-set, or recomputed-hash property drifts; the allowed status set keeps the check valid both immediately before review and after approval. | Validator mode and concrete review artifacts created by 06-09-01 | <60s plus human review |
| 06-09-03 | 09 | 7 | MOD-04 | T-06-25/26/27/SC | `bash -lc "OMP_NUM_THREADS=1 .venv/bin/python scripts/stage_phase6_beamsearch_reference.py --validate-proposal --source-url https://github.com/ionq-publications/BeamSearchDecoder.git --expected-commit 084a475b05fb64308103317a1ce5a0c4b0be58aa --approval docs/evidence/phase6-native-dependency-approval.json --lock docs/evidence/phase6-native-requirements-lock.txt --wheelhouse data/results/phase6-native-wheelhouse --require-status approved && OMP_NUM_THREADS=1 .venv/bin/python scripts/stage_phase6_beamsearch_reference.py --stage-root data/results/phase6-native-stage --qualification docs/evidence/phase6-beamsearch-native-qualification.json --build && OMP_NUM_THREADS=1 .venv/bin/python scripts/stage_phase6_beamsearch_reference.py --stage-root data/results/phase6-native-stage --qualification docs/evidence/phase6-beamsearch-native-qualification.json --smoke && OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_native_reference.py -k 'build_attempt or smoke or adapter or original_validation or partial or instrumentation' -x"` | RED until the native script/tests exist; fails unless the complete proposal is approved, the isolated build is invoked, a built stage is smoked, every vector passes Hc=s, statuses remain distinct, and missingness has a demonstrated failed-build receipt. | Task completes staging script, native tests, adapter, manifest, and qualification schema before invocation | Explicit long gate: allow up to 20 min |
| 06-08-01 | 08 | 7 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-22/23/24 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase6_replay_budget.py tests/test_phase6_public_execution.py -k 'complete_tree or replay or reconstruct or measurement' -x` | Fails if replay trusts summaries, omits a path/event/leaf, compares elapsed timing deterministically, or skips independent original validation. | Test files created by 06-03 and 06-07; task adds replay cases first | <120s |
| 06-08-02 | 08 | 7 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-22/23/24 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase6_replay_budget.py tests/test_phase6_public_execution.py -k 'tamper or rehash or worker or duplicate or missing or historical' -x` | Fails if any rehashed semantic mutation passes, topology changes deterministic evidence, or missing/duplicate/reordered/unknown events are accepted. | Test files from dependencies; task adds mutations first | <120s |
| 06-10-01 | 10 | 8 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-28/29/30 | `bash -lc "OMP_NUM_THREADS=1 .venv/bin/python scripts/validate_phase6_design.py --check && OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py -k 'integrated_fixture or source_status or complete_tree' -x"` | RED until validator/manifest exist; fails for digest/status mismatch, missing terminal class, incorrect leaf total, invalid candidate/vote, failed public replay, or performance-claim promotion. | Task creates validator and manifest; public test file exists from 06-07 | <120s |
| 06-10-02 | 10 | 8 | MOD-04, INT-05, CAN-01, CAN-02 | T-06-28/29/30 | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase6_public_execution.py -k 'documentation or source_status or claim_limit' -x` | Fails if source profiles, pins, native availability, AutDEC convention, generic voting, CSS adaptation, or not_assessed limits are missing or over-promoted. | Public test file from 06-07; task adds documentation/status assertions | <60s |

## Wave 0 and Test-Creation Ownership

No plan uses `<automated>MISSING</automated>`. Existing infrastructure covers pytest and the Phase 5 export check. New test files are created test-first inside the earliest task that owns them:

| Test or validator | Creation owner | First production behavior it gates | Downstream consumers |
|---|---|---|---|
| `tests/canonical/test_beam_search.py` | 06-02-01 | kernel-generic masked min-sum tracer and separate SPA identity | 06-02-02, 06-05-01, 06-05-02 |
| `tests/canonical/test_phase6_replay_budget.py` | 06-03-01 | version-5 identity/work/span tracer | 06-03-02, 06-08-01, 06-08-02 |
| `tests/canonical/test_candidate_selection.py` | 06-04-01 | complete list selection | none |
| `tests/canonical/test_voting.py` | 06-04-02 | plurality and invalid majority | none |
| `tests/canonical/test_ensembles.py` | 06-06-01 | AutDEC algebra/direct coordinates | 06-06-02 |
| `tests/test_phase6_public_execution.py` | 06-07-01 | V7 preflight and public tracer | 06-07-02, 06-08-01/02, 06-10-01/02 |
| `scripts/stage_phase6_beamsearch_reference.py` + `tests/test_phase6_native_reference.py` proposal mode | 06-09-01 | complete source/graph/lock/target/wheel/hash proposal validation | 06-09-02/03 |
| `tests/test_phase6_native_reference.py` build/adapter cases | 06-09-03 | pin/build/receipt qualification and adapter validation | phase gate |
| `scripts/stage_phase6_beamsearch_reference.py` build/smoke modes | 06-09-03 | mandatory isolated build and smoke attempt | phase gate |
| `scripts/validate_phase6_design.py` | 06-10-01 | independent integrated evidence audit | phase gate |

`wave_0_complete` remains false until the task-owned RED tests have been created and their failing direction captured during execution. The plan graph guarantees every downstream command depends on the task that creates its path.

## Deterministic Scientific Fixtures

- Source-kernel fixture: fails if either source-qualified BeamSearch profile uses SPA instead of min-sum; separately confirms `canonical_css_spa_adaptation` has different identity and may diverge.
- Pinned C++ fixtures: root variable zero has degree at most two; later scan has no eligible unmasked variable; strict equal branch scores retain current `min_idx`; full equal-score queue favors later `store_idx` values.
- AutDEC fixture: nontrivial `A`/`U_A` verifies `U_A H = H A`, `(H A)c = U_A s`, and direct `Hc=s` without inverse mapping.
- Complete-tree fixture: accepted, rejected, pruned, duplicate, late, and budget-denied origins with hand-calculated unique work and critical-path span.
- Voting fixture: exact plurality tie plus a coordinate-majority vector that violates the original syndrome and remains invalid.
- Native fixture: exact pinned checkout and mandatory documented isolated build/smoke attempt; typed missingness requires a retained failed command receipt.

## Manual-Only Verification

| Behavior | Requirement | Why manual | Procedure |
|---|---|---|---|
| Phase 5 notebook/offline HTML readability | Phase dependency | Automated checks cannot judge visual readability and interaction clarity | Execute Plan 06-01 checkpoint and record explicit pass or issues through `$gsd-verify-work 05`. |
| Exact SUS native dependency lock | MOD-04 | Registry metadata was insufficient to establish legitimacy for all 14 packages | During Plan 06-09, review the concrete resolution, authoritative package/source identities, wheel hashes, target tags, and requirements/setup.py digests; approve or reject before native installation. |

All Phase 6 algorithmic, algebraic, manifest, ledger, replay, native-attempt, and claim-limit behaviors have automated failing directions.

## Validation Sign-Off

- [x] Every task has a runnable `<automated>` command.
- [x] Every new command path has an earlier or same-task test-first creation owner.
- [x] Every automated command states a concrete failing direction.
- [x] Sampling continuity is 20/20 tasks with automated verification; no three-task gap exists.
- [x] No watch-mode flag or blocking sleep appears.
- [x] Source min-sum, pinned C++ sentinel/reuse/queue behavior, AutDEC direct coordinates, and native build-attempt gates are explicit.
- [ ] Task-owned RED tests and validators have been created during execution.
- [ ] Full suite, independent design audit, public replay, and native attempt receipt are green.
- [ ] Set `wave_0_complete: true`, `status: validated`, and record approval after execution evidence exists.

**Approval:** pending execution.
