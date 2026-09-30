---
phase: "04"
slug: "memory-policies-and-relay-bp"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-24"
updated: "2026-09-30"
---

# Phase 04 — Validation

The automated contracts cover the six Phase 4 requirements and the stopped-campaign evidence boundary. The full repository suite passed on 2026-09-30: **568 passed, 1 skipped**. A later narrow path-confinement correction passed 20 affected notebook tests. These checks establish executable semantics and evidence integrity; they do not establish a Relay performance effect or published-curve reproduction.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` |
| Full suite | `PYTHONPATH=src OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Retained audit | `OMP_NUM_THREADS=1 PYTHONPATH=src .venv/bin/python scripts/verify_phase4_calibration.py --root . --ledgers` (5,824/5,824 terminal shots verified in Plan 04-12) |

## Per-Requirement Verification Map

| Requirement | Executable check and retained evidence | Status |
|---|---|---|
| MEM-01 | `tests/canonical/test_memory_policies.py` checks damping equation, endpoints and boundary; `test_memory_execution.py` and `test_local_memory_execution.py` check public execution and reset/rollback. | Covered |
| MEM-02 | `test_memory_policies.py` distinguishes PDBP field mixing from PD′BP edge-delta mixing; `test_local_memory_execution.py` checks operands, saturation and order. | Covered |
| MEM-03 | `test_memory_policies.py` checks zero momentum initialization, original C2V subtraction and reset; local and public execution tests check history ownership and replay. | Covered |
| MEM-04 | `test_memory_policies.py` checks affine prior memory and EWAInit/Relay reparameterization; `test_memory_composition.py`, `test_memory_execution.py` and local tests check lifetime and ordered bindings. | Covered |
| MEM-05 | `test_memory_composition.py` checks decoder-local seeded draws, refresh and rollback; `test_memory_execution.py` and local tests check public replay, trace neutrality and assignment evidence. | Covered |
| MOD-01 | `tests/canonical/test_relay.py` checks leg transfer, stopping, scoring and work; `test_relay_differential.py` checks exact-author identity, translation and observer equivalence; `test_phase4_evidence.py` checks artifact identities, stage reuse and ledger reconstruction. | Covered |
| MOD-01 evidence boundary | `test_phase4_notebook.py`, `test_phase4_notebook_campaign.py` and `test_phase4_notebook_presentation.py` check cancelled-stage labeling, receipt integrity and unavailable outcome denominators. The executed read-only notebook is `data/results/phase4-notebook/retained-cancelled-phase4.ipynb`. | Covered |

## Wave 0 and Invariants

The five named Wave 0 targets exist: `tests/canonical/test_memory_policies.py`, `test_memory_composition.py`, `test_relay.py`, `test_relay_differential.py`, and `test_phase4_evidence.py`. Later tests added ordinary and local schedule execution, trace and notebook boundaries. The full suite covers typed version routing, independent history, budget rollback, decoder-visible selection, finite posterior transfer, leaf-work reconstruction, identity gates and hash-linked artifact reuse.

The retained calibration passed an independent ledger audit of 182 configurations and 5,824 terminal shots. B1 selection is inconclusive under its frozen cap. The cancelled evaluation prefix has 159 completed and one interrupted **receipt**, with no qualified performance denominator. Fresh evaluation, native-pair and factorial results are absent. No statistical comparison is inferred from this prefix.

## Manual Evidence Review

The exact-author v0.2.2 tag/commit/tree and divergent installed fork were reviewed in Plan 04-07; the isolated build, comment-only observer and bounded equivalence fixture are recorded in Plan 04-08. Plan 04-11 recorded scheduler entitlement and finite caps before calibration. These are provenance and resource checks, not substitutes for automated policy tests.

## Sign-Off

- [x] Every Phase 4 requirement has executable checks.
- [x] All five Wave 0 test targets exist.
- [x] Full suite and bounded native differential fixtures passed.
- [x] Incomplete production evidence remains explicitly unqualified.

**Approval:** validated 2026-09-30 under the revised Phase 4 scope.
