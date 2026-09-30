---
phase: 04-memory-policies-and-relay-bp
plan: "14"
subsystem: Phase 4 notebook and public evidence guide
tags: [relay-bp, notebook, provenance, cancellation, bounded-evidence]
requires:
  - phase: 04-13
    provides: terminal cancellation and hash-linked retained evidence inventory
provides:
  - Executed read-only Phase 4 notebook over retained evidence with explicit cancelled-stage labels
  - Verified B1 receipt-count display without a performance denominator or effect estimate
  - Public guide for bounded fixture and read-only retained-evidence execution
affects: [phase-4-verification, phase-5, phase-8, phase-9]
actuals:
  tokens: 4100
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [verified cancellation metadata before display, separate receipt counts from outcome denominators]
key-files:
  created:
    - data/results/phase4-notebook/retained-cancelled-phase4.ipynb
  modified:
    - notebooks/phase4-memory-relay-analysis.ipynb
    - scripts/phase4_notebook_campaign.py
    - docs/phase4-memory-relay.md
    - tests/canonical/test_phase4_notebook.py
    - tests/canonical/test_phase4_notebook_campaign.py
    - tests/canonical/test_phase4_notebook_presentation.py
key-decisions:
  - "Treat the stopped evaluation prefix as receipt counts only; its performance denominator remains unavailable."
  - "The current notebook has no producer invocation for cancelled stages; read-only analysis may verify retained artifacts."
requirements-completed: [MEM-01, MEM-02, MEM-03, MEM-04, MEM-05, MOD-01]
metrics:
  duration: 16 min
  completed: 2026-09-30
status: complete
coverage:
  - id: C1
    description: Read-only notebook visibly labels all cancelled production stages and the interrupted B1 prefix without estimating a failure rate.
    requirement: MOD-01
    verification:
      - kind: integration
        ref: "data/results/phase4-notebook/retained-cancelled-phase4.ipynb (28 executed cells; cancelled labels in evaluation/factorial/native/traces)"
        status: pass
      - kind: unit
        ref: "tests/canonical/test_phase4_notebook_campaign.py and test_phase4_notebook_presentation.py"
        status: pass
    human_judgment: false
  - id: C2
    description: Public guide and notebook state the source, mechanism and bounded evidence limits while keeping fixture and production identities separate.
    requirement: MEM-01
    verification:
      - kind: integration
        ref: "tests/canonical/test_phase4_notebook.py"
        status: pass
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q (568 passed, 1 skipped)"
        status: pass
    human_judgment: false
---

# Phase 4 Plan 14: Availability-aware notebook and guide

The Phase 4 notebook now identifies the completed calibration, frozen BB-144/HGP settings, inconclusive B1 selection, independent auxiliary author diagnostics, and the cancelled production stages. The reader cross-checks the terminal cancellation manifest, evidence inventory, B1 receipt bytes, SHA-256 and status counts before showing 159 completed and one interrupted receipt. It leaves the performance denominator unavailable and draws no figure or comparison from the interrupted prefix. Fresh evaluation, native pairs, factorial and planned factorial-linked traces display `cancelled_before_completion`.

The public guide gives separate bounded fixture and read-only retained-evidence commands. The executed retained notebook has 28 completed cells and no production sampling. No code path in the notebook invokes the cancelled producer.

Verification: 60 focused tests passed with one skipped; full repository suite 568 passed with one skipped. The retained notebook output was inspected for all four cancelled-stage labels, receipt counts, and lack of a performance denominator. No comprehensive simulation was restarted.

Phase 4 plans are complete. Phase goal verification remains the next gate before Phase 5.
