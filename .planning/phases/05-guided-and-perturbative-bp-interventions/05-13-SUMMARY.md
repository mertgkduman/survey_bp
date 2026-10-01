---
phase: 05-guided-and-perturbative-bp-interventions
plan: "13"
status: complete
subsystem: phase5-offline-report
tags: [html, plotly, evidence-guide, source-limits]
requires: [05-11]
provides:
  - self-contained synchronized interactive HTML report
  - public Phase 5 commands and qualified evidence guide
affects: [phase5-verification]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-10-01
---

# Phase 5 Plan 13: Offline report and public guide

The exporter checks the executed notebook and its evidence identity before producing a self-contained HTML file with embedded Plotly JavaScript. Arm legend groups synchronize the outcome, intervention-count, and typed-work panels. The report preserves hover and summary identities, qualifications, `pilot_adaptation` and `not_assessed` labels, and project-relative evidence references. Untrusted source text is escaped before insertion into HTML. Full attempt rows remain in the executed notebook.

The public guide documents preflight, bounded execution, retained-result verification, deterministic BB-144/HGP fixtures, notebook execution, and HTML validation. It keeps the original-problem truth boundary, five outcome cells, leaf accounting, B1 entitlement and cap freeze, source interpretation limits, and absent native comparisons explicit. The HTML `--check` and focused notebook tests passed. No performance ranking or curve agreement is asserted.

The executed notebook and standalone HTML were regenerated from the corrected v2 aggregate, with the approved `plotly==7.1.0` pin. The HTML check and all 12 notebook tests passed on that evidence.
