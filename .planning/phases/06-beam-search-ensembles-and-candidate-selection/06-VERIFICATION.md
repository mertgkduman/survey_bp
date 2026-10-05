---
phase: 06-beam-search-ensembles-and-candidate-selection
verified: 2026-10-05T23:20:53Z
status: passed
score: 5/5 roadmap success criteria verified
requirements: [MOD-04, INT-05, CAN-01]
carried_forward: [CAN-02]
human_verification: []
---

# Phase 6 Goal Verification

**Goal:** A researcher can execute branching and ensemble searches and inspect candidate generation, pruning, selection, and work. The approved three-paper CSS gate also demonstrates one policy-file command with honest source status.

| Roadmap criterion | Verdict | Evidence |
| --- | --- | --- |
| Controlled BeamSearch/RelayBP CSS adaptation with a common initial BP run, damping, bounded branches/legs, selection, and work evidence | Verified | `data/studies/fair-beam-relay-css-v2.json`, sealed results, `docs/fair-beam-relay-css-v2.md`, and `tests/test_phase6_existing_evidence.py` check matched initial state, both damping levels, pruned/denied units, distinct work, and verified reuse. The original circuit experiment remains in Phases 12–13. |
| Explicit member/branch identity, state inheritance, limits, and unique work | Verified | Canonical ensemble and candidate-lineage contracts, public MBBP-LD execution, terminal ledger replay, and Phase 6 public-execution tests. |
| Complete-origin list scoring and precise coordinate-majority primitive | Verified for Phase 6 scope | `canonical/candidate_selection.py` and its tests check eligibility, deterministic ties, complete electorate, invalid aggregate rejection, and original-syndrome validation. The importable vote primitive works; a public TOML vote is rejected until Phase 9 implements execution and replay. CAN-02 therefore remains pending there. |
| Replayable small search tree with accepted, rejected, pruned, and budget-denied paths | Verified | Sealed BB72 ledger regression and public V7 MBBP tests check terminal/control-flow lineage and work; structural replay rejects changed results. |
| Three source-grounded CSS paper families through one policy-file command, 14 dispositions, and bounded B1 evidence | Verified | `literature_policies/qualification-v1.json` has 10 Yao, 3 Bhatnagar, and 1 Rabeti record; five have runnable canonical adaptations and nine remain source-spec only. Three selected policies compute and reuse with `data/studies/css-literature-b1-gate-v1.json`; `data/results/css-literature-gate-v1/` retains manifests, ledgers, receipts, hashes, a CLI reuse receipt, and verified two-shot denominators. All are `pilot_adaptation` and `not_assessed`. |

**Verification commands:** The installed CLI smoke returned `reused` for all three selected policies. The package verifier returned `verified` with three paper families, 14 source records, and two terminal shots per policy. `tests/test_css_literature_gate.py` passed 5 tests, including relocated-package replay and mutation rejection. The remaining suite passed 810 tests with 1 skip; focused historical command tests passed 105. `git diff --check` passed.

**Scientific boundary:** The B1 candidate is algebraically checked but not matched to the papers' ordered artifacts. The two near-zero-noise shots are a workflow smoke test; they do not estimate decoder performance or reproduce source curves. Phases 8–9 own statistical campaign controls and CSS source assessment. Phase 5's existing human visual review remains open and is not represented as a Phase 6 failure.

**Phase plan decision:** Preserve Phase 7 postprocessing, Phase 8 campaign controls, and Phase 9 CSS assessment in order. Literature policy intake, artifact collection, and bounded pilots may proceed alongside Phase 7. Public policy-file voting (CAN-02) moves to Phase 9, where it can be assessed on matched CSS samples after its ledger execution and replay are implemented. Phase 8 must measure decode/replay throughput and ledger size before launching larger campaigns.
