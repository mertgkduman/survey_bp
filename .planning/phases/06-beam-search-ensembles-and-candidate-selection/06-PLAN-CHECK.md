# Phase 6 Plan Check

## VERIFICATION PASSED

**Phase:** 06 — Beam Search, Ensembles, and Candidate Selection
**Plans verified:** 9
**Status:** All checks passed

The plans will deliver the current Phase 6 goal: preserve and verify the completed controlled CSS BeamSearch/RelayBP work, add auditable ensemble/list/voting semantics, and execute the first three-paper CSS literature-policy gate through one researcher-facing command without claiming paper reproduction.

## Coverage Summary

| Requirement | Plans | Status |
|---|---|---|
| MOD-04 — controlled CSS BeamSearch adaptation, damping, branch/prune/budget/selection and work evidence | 06-05, 06-09 | Covered |
| INT-05 — explicit branch/member identity, state mode, limits and unique aggregated work | 06-01–09 | Covered |
| CAN-01 — complete candidate origins, eligibility, scores and deterministic ties | 06-02–09 | Covered |
| CAN-02 — declared voting object/electorate with independent original-problem validation | 06-05–09 | Covered |

| Roadmap success criterion | Coverage | Status |
|---|---|---|
| SC1 — fair controlled BeamSearch/RelayBP semantics and evidence | 06-05 Task 3 plus 06-09 documentation/evidence gate | Covered |
| SC2 — generic branching/ensemble state, resources and work | 06-05 through 06-07 | Covered |
| SC3 — list selection and voting semantics | 06-05 and 06-07 | Covered |
| SC4 — replayable accepted/rejected/pruned/denied paths | Existing fair-tree regression in 06-05 plus public ensemble replay in 06-07 | Covered |
| SC5 — three-paper policy files, typed dispositions and bounded common-command execution | 06-01–04 and 06-06–09 | Covered |

The revised ROADMAP and REQUIREMENTS correctly assign Phase 6 the controlled CSS BeamSearch adaptation. The original circuit procedure and pinned executable reference are explicitly owned by CIR-04/CEV-01 in Phases 12–13, matching the locked replan rather than restoring the superseded native/AutDEC work.

## Plan Summary

| Plan | Tasks | Files | Wave | Dependencies | Status |
|---|---:|---:|---:|---|---|
| 06-01 | 2 | 5 | 1 | none | Valid |
| 06-02 | 2 | 3 | 2 | 06-01 | Valid |
| 06-03 | 2 | 5 | 2 | 06-01 | Valid |
| 06-04 | 2 | 5 | 3 | 06-01, 06-03 | Valid |
| 06-05 | 3 | 4 | 2 | 06-01 | Valid |
| 06-06 | 2 | 3 | 3 | 06-05 | Valid |
| 06-07 | 2 | 6 | 4 | 06-01, 06-03, 06-05, 06-06 | Valid |
| 06-08 | 2 | 5 | 5 | 06-01, 06-04, 06-07 | Valid |
| 06-09 | 3 | 7 | 6 | 06-02, 06-04, 06-08 | Valid |

The dependency graph is acyclic, every dependency names an existing earlier-wave plan, and same-wave plans have disjoint file ownership. Transitive dependencies correctly order the parser, intervention kernels, selection seam, MBBP controller, public schema/replay, literature compiler and final B1 gate.

All plans contain complete frontmatter and every task has files, a specific action, automated verification, a stated failing direction, acceptance criteria and a done condition. The structure checker reports all nine plans valid with no warnings. Each plan has two or three tasks and three to seven declared files. Calibrated estimates range from 18,000 to 30,000 tokens against a 100,000-token smart-zone budget; all are below budget, with low calibration confidence because the estimator has no completed-phase samples.

## Scientific and Interface Checks

- The Yao family accounts for all ten requested records. `T` remains sweeps per decimation round, `R` remains the round limit, symbolic code-length limits resolve before execution identity, and zero-bias/final-round interpretations remain explicit.
- The Bhatnagar family implements force-to-zero as distinct behavior, preserves force-to-one and historical routes, scopes clipping to fresh V2C messages at magnitude 25, uses fresh attempts, and keeps schedule/infinite-prior interpretations visible.
- MBBP-LD declares exact augmented-basis transformations and syndromes, independent normalized-min-sum serial members, frequency divided by weight-plus-one selection, stable ties and unique work. Its no-member-converged source return is a typed failure sentinel: the zero vector is retained as procedure evidence, cannot enter selection, cannot receive a successful original check and cannot reach the evaluator. Kernel, public replay and compiler tests cover this terminal.
- Plans 06-01 and 06-09 preserve the exact `bp-registry STUDY --decoder FILE` workflow. The final gate runner computes the three selected policies, then its `cli-smoke` helper invokes the installed command for each, parses JSON, requires `status == "reused"`, and rejects changed output identity, hashes, denominators or shot counts before final verification.
- Execution identity, normalized provenance identity and raw-document identity are separated. Metadata-only differences can reuse verified computation while append-only request receipts retain source attribution; semantic conflicts and tampering fail closed.
- The B1 gate pins local raw/semantic artifact identity, samples, denominator and complete caps, retains every terminal, and packages ledgers, lineage, unique work, original checks and computation/request receipts. It keeps all three families at `pilot_adaptation`/`not_assessed` while exact paper artifacts, author code and source settings remain unresolved.
- The completed BB72 BeamSearch/RelayBP package is reused without relaunch. Regression coverage fixes the shared initial min-sum BP, damping 1.0/0.5, masked branches, disordered-memory Relay legs and gamma interval, shared extra-work ceiling, typed work/runtime, pruned/denied paths, matched samples and source/adaptation labels.
- The outstanding Phase 5 human notebook/HTML review remains visible and is not marked passed.

## Validation and Compliance

- `06-VALIDATION.md` exists and maps every task to an automated command, failure condition and test owner. New tests are created by the first task that needs them; `wave_0_complete` correctly remains false until execution records the RED direction.
- Sampling continuity is complete: every implementation task has an automated check, and the final gate runs production, installed-CLI reuse assertions, final evidence verification, focused regressions and the full suite.
- The supplied prompt contained no deterministic failing-direction or verify-path probe payload. Per the checker contract, those two probe-only dimensions are silent. Static review found no suppressed errors, watch modes, comparison-fed defaults or vacuous `echo` checks.
- The plans honor `06-CONTEXT.md` and `06-LITERATURE-GATE.md`: no native/AutDEC plan is reintroduced, full curves remain in Phases 8–9, and controlled adaptations are not relabeled as source reproductions.
- The refreshed research has no unresolved open question for current Phase 6 and assigns native BeamSearch work to Phases 12–13. Plan tasks follow the responsibility map: BP updates stay in the canonical session/kernel, ensemble lifecycle stays in controllers, selection/voting stays truth-free until independent original validation, and work remains in unique budget leaves.
- Applicable `06-PATTERNS.md` analogs are followed for candidate records, strict versioned manifests, structural execution/replay, deterministic lineage and atomic work. New literature and MBBP surfaces cite the refreshed research and existing canonical seams.
- AGENTS.md constraints are preserved: one compatible canonical CSS engine, immutable original problems, truth-free decoder decisions, explicit ledgers and provenance, source/adaptation distinction, and CSS-first sequencing.

No BLOCKER, WARNING or INFO findings remain. The plan set is ready for `$gsd-execute-phase 06`.
