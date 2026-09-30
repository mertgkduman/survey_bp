---
phase: 05-guided-and-perturbative-bp-interventions
plan: "09"
status: complete
subsystem: analysis-dependency-gate
tags: [plotly, package-identity, human-approval]
requires: [05-02]
provides:
  - approved exact plotly==7.1.0 analysis dependency pin for notebook charts and HTML export only
affects: [05-11, 05-13]
completed: 2026-09-30
---

# Phase 5 Plan 09: Plotly package gate

The human approved the exact `plotly==7.1.0` pin solely for read-only notebook charts and HTML export after reviewing the PyPI project, upstream `plotly/plotly.py` repository, and immutable `v7.1.0` tag commit `243bfd0fa5c0a5c29a185e4034a1ab5b111695a5`.

Read-only checks confirmed PyPI lists version 7.1.0, the upstream tag resolves to that exact commit, and Plotly is absent from `.venv` before Plan 05-11. This checkpoint installed no package and edited no dependency file. Plotly has no decoder, selection, evidence, or assessment role.
