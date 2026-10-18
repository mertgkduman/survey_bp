---
phase: 11-quaternary-reproduction-and-comparisons
plan: "20"
subsystem: MBP4 Figure 6 source review
status: complete
requirements-completed: []
key-decisions:
  - "The chat reviewer selected preserve_mechanism_only for candidate bc4678ef8da5d02d3c57c6f6392fc7b8334a6048980fdfe9486791e06fc17184 by directing us to record policy and move on."
  - "Figure 6 remains a blocked, zero-shot statistical target because coordinates, denominators, stopping, uncertainty, tolerance, and other source facts remain unresolved."
---

# Phase 11 Plan 20: MBP4 Figure 6 Review

The 11-point `alpha=1.5` Figure 6 candidate passed structural and digest verification. The reviewer retained the existing mechanism-only policy. The materialized [Figure 6 target](../../../data/source-targets/phase11-mbp4-curve.json) binds the reviewed candidate digest, retains every field blocker, and admits zero shots. Its receipt digest is `0b83a8e0fbadfae37888c1555469971b4402e9196ff850ce172f22258d292763`.

The [Figures 8–9 assessment](../../../data/results/phase11-mbp4-figures8-9/assessment.json) remained byte unchanged. The immutable [candidate](../../../data/source-targets/phase11-mbp4-curve-review.json) also remains unchanged so its original digest is still verifiable.

Verification: `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_phase11_mbp4_target.py -x` passed 10 tests. `verify-candidate` passed. No production dispatch occurred.

Deviation: materialization stores the explicit decision in the separate Figure 6 target, leaving the pending candidate immutable; this preserves its pre-review digest and makes the target the reviewed terminal.
