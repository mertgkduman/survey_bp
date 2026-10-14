---
phase: 11-quaternary-reproduction-and-comparisons
plan: "13"
subsystem: quaternary controlled policy comparisons
tags: [mbp4, asced, eligibility, matched-sample, bounded-evidence]
requires:
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "06"
    provides: preserved-unavailable native aSCED qualification
  - phase: 11-quaternary-reproduction-and-comparisons
    plan: "10"
    provides: default-deny bounded controlled lifecycle
provides:
  - One-change MBP4 recurrence comparison contract with deterministic replay
  - Exact lower-Y, independence, higher-Y policy anchor enforcement
  - Complete method eligibility matrix with separate canonical and native aSCED states
affects: [phase-11-controlled-comparisons, quaternary-method-evidence]
tech-stack:
  added: []
  patterns: [one-change-policy-contract, immutable-anchor-order, independent-canonical-native-eligibility]
key-files:
  created:
    - data/studies/phase11-policy-comparisons.json
    - data/manifests/phase11-complete-methods.json
    - scripts/run_phase11_policy_comparisons.py
    - tests/test_phase11_policy_comparisons.py
  modified:
    - data/results/phase11-policy-comparisons/verification.json
key-decisions:
  - "MBP4 comparisons change only the qualified fixed-alpha recurrence while schedule, initialization, construction, stopping, postprocessing, channel, and sample identity remain equal."
  - "Every policy row uses exactly lower_y, independence, and higher_y in frozen order; ordinary and overcomplete aSCED construction rows remain distinct."
  - "Canonical aSCED controlled eligibility is independent of Plan 11-06's declined native matched-input route; native matching stays unavailable with no fidelity promotion."
actuals:
  tokens: 6706
  tasks: 3
  commits: 6
commits: 6
plan_head_before: 50006ea3ef0d00839cec011f44418c28205cd477
duration: 11m
completed: 2026-10-14
status: complete
---

# Phase 11 Plan 13: Policy Comparisons Summary

**Bounded policy evidence now isolates the MBP4 recurrence on shared Pauli input, structurally locks each policy row to the three frozen channel anchors, and preserves complete method eligibility without conflating canonical aSCED with unavailable native matching.**

## Accomplishments

- Added a public bounded MBP4 comparison runner that materializes one independence sample before both arms execute, records both terminals, typed work, and same-condition timing, and replays deterministic fields.
- Rejected unsupported MBP4 alpha values and any additional configuration difference before output publication.
- Expanded the policy design to the exact frozen lower-Y, independence, and higher-Y anchors, and retained separate ordinary and overcomplete canonical aSCED construction lanes.
- Added a receipt-derived matrix for ordinary BP4, Q-BPGD, MBP4, and canonical aSCED. Q-BPGD remains visibly ineligible because its source qualification gaps are unresolved; aSCED remains canonical-adaptation evidence and its native match lane remains unavailable.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'tracer or mbp4 or one_change or independence or unsupported or replay' -x` — passed (3 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase11_policy_comparisons.py run --output-root /tmp/phase11-policy-tracer` — passed; replayed one sealed MBP4 record.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'three_anchor or lower_y or higher_y or asced or overcomplete or ineligible or multi_change' -x` — passed (2 tests).
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase11_policy_comparisons.py -k 'complete_methods or eligibility or matched or gb46 or bb72 or work or runtime or excluded' -x` — passed (1 test).

## TDD Gate Compliance

- Task 1 RED: `test_tracer_mbp4_one_change_contract_and_replay` failed because the policy runner did not exist; committed in `4ed54c8` before `7ba7472` implemented it.
- Task 2 RED: `test_three_anchor_policy_rows_keep_asced_lanes_separate_and_native_unavailable` failed because the tracer covered only independence; committed in `cbe612d` before `3858926` expanded the contract.
- Task 3 RED: `test_complete_methods_keeps_canonical_asced_eligible_without_native_matching` failed because no complete-method loader existed; committed in `08b6792` before `cd5b10f` supplied the receipt-derived matrix.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Corrected the controlled MBP4 integration boundary during Task 1.
   - The original-problem lineage needed the canonical `original-` prefix, scalar BP4 required an explicit iteration cap, and evaluator replay required its immutable tracer problem type.
   - The runner now uses each required public invariant before it writes a sealed record.
   - Commit: `7ba7472`.

## Known Stubs

None. The unavailable native aSCED lane is an intentional, digest-bound `preserve_unavailable` terminal and is retained explicitly in the method matrix.

## Self-Check: PASSED

- Confirmed all five key implementation, evidence, and regression files exist.
- Confirmed task commits `4ed54c8`, `7ba7472`, `cbe612d`, `3858926`, `08b6792`, and `cd5b10f` exist in Git history.
- Focused tracer, anchor, and complete-method verification selections passed with nonzero collection.
