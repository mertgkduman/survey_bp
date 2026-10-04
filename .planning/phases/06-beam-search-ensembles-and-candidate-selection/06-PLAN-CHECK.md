# Phase 6 Plan Check

## VERIFICATION PASSED

**Phase:** Beam Search, Ensembles, and Candidate Selection  
**Plans verified:** 06-01 through 06-10  
**Tasks verified:** 20  
**Status:** All checks passed; 0 blockers, 0 warnings, 0 info

## Goal-backward verdict

The revised plans will deliver the Phase 6 goal and all four mapped requirements. A researcher can execute source-qualified BeamSearch variants and generic ensemble/list/vote compositions, inspect every candidate and discarded path, distinguish aggregate work from observed runtime and DAG span, replay a complete small search tree, and compare the canonical adaptations with a genuinely attempted pinned native reference.

The six blockers from the first check are closed: both source-qualified BeamSearch profiles use min-sum; the official-C++ profile preserves the pinned index-zero sentinel, stale-index reuse, strict comparisons, and queue ties; AutDEC uses the direct `U_A H = H A` coordinate convention without an inverse map; native missingness requires a captured isolated build attempt; `06-VALIDATION.md` supplies the Nyquist contract; and all research questions are explicitly resolved.

## Requirement coverage

| Requirement | Covering plans | Goal evidence | Status |
|---|---|---|---|
| MOD-04 | 02, 03, 05, 07-10 | Masked min-sum kernel seam, separate paper/pinned-C++ profiles, bounded public execution, replay, and approved pinned native attempt | Covered |
| INT-05 | 02-08, 10 | Explicit parent/member identity, state mode, topology, caps, exact-once leaf work, runtime/span separation | Covered |
| CAN-01 | 03-08, 10 | Complete frozen lists with origin, eligibility, finite score/direction, stable ties, and retained discarded paths | Covered |
| CAN-02 | 03-04, 06-08, 10 | Declared vote object/electorate/ballots/ties, synthesized lineage, and independent original-problem validation | Covered |

## Phase success criteria

| Success criterion | Plans | Planned proof | Status |
|---|---|---|---|
| Canonical BeamSearch exposes masked BP, branching, width, ranking/pruning, budgets, selection, fixtures, and pinned reference | 02, 05, 07-10 | Hand-audited min-sum trees, exact pinned-C++ divergence fixtures, public manifest, replay, native qualification | Covered |
| Generic branch/ensemble composition declares identity, state, limits, and work without hiding or double-counting paths | 02-03, 05-08, 10 | Stable lineage DAG, immutable snapshots, unique leaves, denied-work rollback, topology-independent ordering | Covered |
| List selection and voting retain origins and independently validate final output | 03-08, 10 | Complete candidate/electorate records, deterministic ties, invalid coordinate-majority fixture | Covered |
| A small tree can be replayed with accepted, rejected, pruned, duplicate, late, and budget-exhausted paths accounted for | 03, 07-08, 10 | Full event reconstruction, semantic tamper rejection, exact work and terminal audit | Covered |

## Source and scientific contract checks

| Contract | Evidence in revised plans | Status |
|---|---|---|
| BeamSearch paper kernel | `paper_v2_min_sum_plus_declared_ties` binds `binary-min-sum-masked-flooding-f64-v1`; SPA is `canonical_css_spa_adaptation` | Pass |
| Pinned C++ behavior | `official_cpp_084a475_observed_min_sum` tests root `min_idx=0`, no-eligible reuse, strict branch ties, and equal-score later `store_idx` preference | Pass |
| AutDEC coordinates | Plan 06 tests `U_A H = H A`, `(H A)c = U_A s`, and direct `Hc=s`; it forbids an inverse map under this source contract | Pass |
| Source separation | Paper, pinned implementation, cleaned adaptation, SPA adaptation, circuit-level publication, and raw-matrix CSS use have distinct machine-readable statuses | Pass |
| Native execution | Exact commit `084a475b05fb64308103317a1ce5a0c4b0be58aa`; approved hash lock; isolated offline install; documented `setup.py build_ext --inplace`; typed unavailable only after a captured failed attempt | Pass |

The source-sensitive findings agree with the primary BeamSearch paper, pinned BeamSearch repository, AutDEC paper, and pinned AutDEC implementation cited in `06-RESEARCH.md` and `06-SOURCE-AUDIT.md`.

## Native dependency approval sequence

Plan 06-09 now performs the required order inside the native-only Wave 7 work:

1. Prepare a wheel-only proposal without installing or importing proposed distributions.
2. Run mutation tests and a stdlib-only validator over the exact source/setup digests, all 14 direct requirements, closed transitive graph, pinned lock, target ABI/platform, wheel metadata/set, and recomputed SHA-256 values.
3. Pause for human approval of the concrete identities, graph, wheels, hashes, target, and build boundary.
4. Require `status: approved` before any isolated install or native build.

The approval checkpoint's automated command accepts pending or approved status while validating every immutable proposal property, so it remains valid after the human decision. Task 3 requires approved status. This gate no longer blocks canonical Plans 02-08; it starts only after Plan 07 and joins Plan 10. The `&amp;&amp;` sequences in plan XML are decoded by the GSD executor to shell `&&` before execution.

## Nyquist and command checks

- `06-VALIDATION.md` contains exactly 20 task rows for 20 planned tasks.
- Every task has an automated command and a stated failing direction; checkpoints additionally carry the required human judgment.
- New test/script paths have same-task test-first creation owners before downstream use.
- Native proposal validation now fails for incomplete graphs/locks, source or target drift, missing/extraneous wheels, metadata mismatch, or recomputed hash mismatch.
- The Phase 5 visual UAT remains the only Wave 1 human gate; the native package approval is the only late Wave 7 gate.
- Historical compact contracts V2-V7 and work/event grammars 2-4 receive explicit golden compatibility checks before the new versions are admitted.

## Plan and dependency summary

| Plan | Tasks | Paths | Wave | Depends on | Status |
|---|---:|---:|---:|---|---|
| 06-01 | 1 | 1 | 1 | — | Valid; Phase 5 visual UAT gate |
| 06-02 | 2 | 4 | 2 | 01 | Valid; BB72 source-seal precondition before edits |
| 06-03 | 2 | 5 | 3 | 02 | Valid |
| 06-04 | 2 | 3 | 4 | 03 | Valid |
| 06-05 | 2 | 4 | 5 | 04 | Valid |
| 06-06 | 2 | 4 | 5 | 04 | Valid |
| 06-07 | 2 | 5 | 6 | 05, 06 | Valid |
| 06-08 | 2 | 5 | 7 | 07 | Valid |
| 06-09 | 3 | 8 | 7 | 07 | Valid; proposal/approval/build sequence is internal |
| 06-10 | 2 | 5 | 8 | 05, 06, 08, 09 | Valid |

The graph is acyclic and wave assignments match dependencies. Same-wave pairs 05/06 and 08/09 have no write overlap, prerequisite coupling, or incompatible shared transformation. Plan 09 was reduced to eight owned paths, within the normal scope target. Every calibrated estimate is below half of the configured 100,000-token budget; confidence remains low because the project has no calibration samples.

## Remaining dimensions

- **Task completeness:** `verify.plan-structure` reports all ten plans valid with no errors or warnings; every task has its required fields.
- **Key links and data contracts:** kernel, controller, lineage/work, list/vote, manifest/execution, replay, and native evidence links are implemented by named tasks with compatible versioned contracts.
- **Truth boundary:** branch ranking, selection, and voting receive decoder-visible facts only; original validation precedes hidden-truth evaluation.
- **Architectural tiers:** numerical updates remain in the canonical kernel; lifecycle in controllers; policy selection/voting in canonical policy code; independent validation at the evaluator/replay boundary; native execution stays isolated.
- **Pattern compliance:** plans use the Phase 5 kernel/session, lineage, relay, manifest, execution, and replay analogs mapped in `06-PATTERNS.md`; novel source logic follows the resolved research contracts.
- **AGENTS.md compliance:** the plans preserve one canonical engine per compatible family, CSS-first scope, immutable original problems, typed provenance, explicit source/adaptation status, no canonical native dependency, the active BB72 source seal, and the configured GSD workflow.
- **Context/review compliance:** no Phase 6 `CONTEXT.md` or `REVIEWS.md` exists; no Phase 7 postprocessing or performance campaign is pulled into this phase.
- **Research resolution:** `06-RESEARCH.md` has `## Open Questions (RESOLVED)` and inline resolutions for every entry.

Plans verified. Phase 6 is ready for `$gsd-execute-phase 06`.
