---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "15"
subsystem: evidence
tags: [source-inventory, controlled-evidence, researcher-guide, replay]
status: complete
dependency_graph:
  requires: [09-03, 09-10, 09-12, 09-13, 09-14, 09-16, 09-17, 09-18, 09-19, 09-20]
  provides: [complete Phase 9 evidence index and bounded researcher guide]
  affects: [phase verification, publication planning]
key_files:
  created: [src/bp_registry/campaigns/evidence_index.py, data/results/phase9-css-evidence-index-v1.json, docs/css-evaluation.md, tests/test_phase9_css_evidence_index.py]
  modified: [literature_policies/qualification-phase9-v1.json]
actuals:
  tasks: 2
---

# Phase 09 Plan 15: Evidence Index and Researcher Guide

## Delivered

- Rebuilt the monotone 14-variant source inventory. Yao T=1 gains a separate digest-bound `canonical_assessment` field for its cap-censored local adaptation; the source-faithful and native identity gates remain unverified.
- The deterministic CSS evidence index binds all source receipts, the B1 cap-censored assessment, three frozen controlled families and their own measured profiles, typed convergence/iteration/work/resource coverage, paired and Holm results, and explicit coverage for Plans 09-01 through 09-20. It rejects missing or changed receipts and can invoke public no-decoder verification before publication.
- The researcher guide links exact public commands and retained artifacts, distinguishes all-shot and conditional denominators, explains source gaps and small-sample limitations, and records denied publication Slurm authorization. The three paper records link to the index without upgrading source fidelity.

## Verification

- Source inventory compiler output and the checked-in file agree byte for byte.
- A fresh index rebuild byte-matches the checked-in index. Public B1, schedule, Relay/Beam, and MBBP report verification passed separately. Focused index tests check fourteen variants, twenty plan rows, positive frozen matched N, typed missingness, receipt binding, and no-overclaim statuses.

## Self-Check: PASSED

The evidence inventory is complete and the phase closure gate is tied to the three exact positive matched control sets. B1 remains explicitly inconclusive at its frozen cap.
