---
phase: 04-memory-policies-and-relay-bp
workflow: gsd-execute-phase
status: isolated-implementation-verified
date: 2026-09-27
commits: [cc0f0b4, 6747e90]
scope: terminal-calibration-surface-integrity
---

# Terminal calibration surface audit

The live calibration remains on the frozen main source. This correction is
independent preparation in the existing memory-integration checkout; it does
not select parameters, publish caps, launch samples, or close Plan 04-12.

The previous downstream provenance gate checked the result digest and its
cap/plan identity. A self-consistent digest alone cannot demonstrate that
every planned configuration and shot was retained. The new read-only
`scripts/verify_phase4_calibration.py` reconstructs that additional contract.
It requires a terminal result, binds exact cap bytes and the frozen plan and
amendment, checks exact configuration/code/preset and shot coverage, rejects
duplicates, checks work caps and matched sample identities, and reconstructs
the recorded eligibility, Wilson intervals, work means, termination counts,
terminal status and category wall charge. Explicit capped and inconclusive
attempts remain in the full planned population.

Run after calibration reaches a terminal state, with the qualified project
interpreter and the appropriately integrated source:

```bash
OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python scripts/verify_phase4_calibration.py
```

The verdict is explicitly `surface_integrity_only`. Verification receipts and
digest links are checked for presence and consistency, but this helper does
not independently replay their underlying ledgers. The plan's separate public
canonical verification of every retained terminal remains required. The
helper neither manufactures an eligible winner nor changes the historical
calibration denominator rule. Its result is `not_assessed`, not evidence of
statistical reproduction or a universal decoder ranking.

Verification: 16 new tests passed in 0.23 seconds, including exact byte
provenance, missing configurations/shots, duplicates, rehashed aggregate
alterations, contradictory verification receipts, mismatched samples, work
cap violations, wall charge drift and explicit capped/inconclusive rows.
An actual read-only call against main's live result rejected it at the terminal
gate before inspecting the tuning surface. Existing main Phase 4 evidence and
evaluation tests passed 40 tests with one unchanged pre-existing skip in
81.88 seconds. This record is scoped implementation evidence, not a Phase 4
completion or scientific verdict.
