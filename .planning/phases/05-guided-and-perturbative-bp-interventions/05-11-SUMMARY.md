---
phase: 05-guided-and-perturbative-bp-interventions
plan: "11"
status: complete
subsystem: phase5-evidence-analysis
tags: [plotly, notebook, matched-shots, read-only-evidence]
requires: [05-09, 05-12, 05-14]
provides:
  - digest-checked immutable shot, arm, and attempt tables
  - synchronized outcome, intervention-count, and work panels
  - executed shot-first notebook with complete attempt drilldown
affects: [05-13]
requirements-completed: [MOD-02, MOD-03, INT-01, INT-02, INT-03, INT-04]
completed: 2026-10-01
---

# Phase 5 Plan 11: Verified evidence analysis and notebook

The analysis layer reads the corrected v2 B1 pilot through public result and ledger verification and builds immutable records for all 16 matched samples and seven arms. It retains 112 shot rows and 1,083 attempt rows, including failed, denied, invalid, unavailable, and no-proposal paths. Baseline flooding sweeps remain visible in the drilldown but are excluded from the intervention-attempt count. The loader binds run IDs to the sealed design, allowing the fresh v2 identities while rejecting a manifest that differs from that design.

The Plotly 7.1.0 pin was explicitly approved. One subplot figure groups each arm across the five-outcome, attempt-count, and typed-work panels. Baseline and one selected arm start visible; the remaining arms start `legendonly`. Legend changes affect presentation only.

The executed notebook starts from a matched shot and exposes arm qualifications, candidate origins, selected recovery and original check, outcome, attempts, and leaf work. Evidence references are relative to the project, and execution did not sample new decoder shots. All 12 notebook tests passed against the corrected evidence; the executed artifact contains no cell errors. The result retains `pilot_adaptation` and `not_assessed` and makes no ranking or reproduction claim.
