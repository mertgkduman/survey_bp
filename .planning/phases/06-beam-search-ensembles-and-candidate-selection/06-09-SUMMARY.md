---
phase: 06-beam-search-ensembles-and-candidate-selection
plan: "09"
subsystem: css-literature-gate
tags: [b1, bpgd, impulse, mbbp-ld, provenance, portable-cache]
status: complete
dependency_graph:
  requires: [06-02, 06-04, 06-08]
  provides: [three-paper-css-policy-gate, fourteen-source-dispositions, portable-study-evidence]
  affects: [phase-7-literature-intake, phase-8-campaign-design, phase-9-css-reproduction]
key_files:
  created: [data/studies/css-literature-b1-gate-v1.json, scripts/run_css_literature_gate.py, tests/test_css_literature_gate.py, literature_policies/qualification-v1.json, docs/css-literature-gate.md, data/results/css-literature-gate-v1/evidence-index.json]
  modified: [src/bp_registry/study.py, src/bp_registry/manifests.py, src/bp_registry/cli.py, .planning/ROADMAP.md]
decisions:
  - One schema 8 researcher study compiles to strict V5 intervention or V7 ensemble manifests with an explicit numerical profile for each registered update family.
  - The B1 gate uses two matched p=0.000001 shots solely for execution, provenance, and compute/reuse validation; all outcomes remain not assessed.
  - Repository-relative artifact roots, result paths, and request-source paths make the retained gate cache portable across editable checkouts.
  - Full source-curve and controlled performance claims wait for independently prespecified campaigns in Phases 8–9.
---

# Phase 06 Plan 09: Small CSS Literature Gate

## Completed Work

- Frozen one B1 candidate artifact, deterministic matched physical sample identity, p=0.000001, two terminal shots per policy, 100-iteration caps, typed work limits, and `pilot_adaptation`/`not_assessed` evidence.
- Qualified all 14 selected source records: ten Yao BPGD, three Bhatnagar impulse, and one Rabeti–Mahdavifar MBBP-LD. Each has a source revision, source-byte identity, parser disposition, blockers, and runnable counterpart when supported. No source record is labeled source-faithful.
- Computed one policy per paper through the same public study API and installed `bp-registry STUDY --decoder FILE` shape: Yao BPGD T=100 R=2, Bhatnagar First_Convergence/0, and a two-member Rabeti MBBP-LD adaptation. Retained manifests, terminal ledgers, results, computation receipts, request receipts, hashes, and a stable evidence index.
- Added portable paths to the study-generated cache and verified installed-command reuse after moving completed outputs from scratch storage into the repository result package. The CLI smoke receipt fixes the cache key, ledger/result hashes, and two-shot denominator.
- Kept the earlier p=0.005 exploratory run labeled separately. It includes two completed historical entries and an interrupted MBBP entry, all outside the frozen gate index.
- Documented the three commands, paper-source gaps, candidate B1 artifact limitation, and the existing fair BB72 BeamSearch/RelayBP evidence. The Phase 5 visual review remains human-pending.

## Verification

- Focused historical CLI, study, literature, and Phase 6 public-execution tests: 105 passed.
- All tests outside the new gate module: 810 passed, 1 skipped.
- Gate design and documentation checks: 3 passed before packaging.
- The installed CLI smoke test returned `reused` for all three paper policies with unchanged cache identities and denominators.
- Packaged gate verifier: `verified`, 3 paper families, 14 source records, and two terminal shots per policy after the package was moved into the repository.
- Full gate-module test includes replay after relocation and a result-mutation rejection.
- `git diff --check` passed.

## Scientific and Operational Limits

Two near-zero-noise shots cannot measure decoder performance or reproduce a published curve. The ordered paper-specific B1 artifacts, author-code revisions, full settings, figure targets, and statistical tolerances remain unresolved. The Rabeti pilot uses declared duplicate-row members because the paper's maximal-subtree partition is not yet reconstructed. The p=0.005 interruption is retained as historical exploratory evidence, not as part of this gate.

Serial Python execution and repeated B1 algebra/replay checks made even this small gate several minutes long. Phase 8 must profile nontrivial-sample throughput, ledger size, and HPC shard costs before authorizing a larger campaign. Phase 7 may continue source policy intake and bounded pilots alongside postprocessing implementation; publication-level assessment remains in Phases 8–9.
