---
phase: 03-update-rules-and-scheduling
plan: "10"
subsystem: group-shuffled-public-tracer
tags: [hsu-ndgsbp, overlapping-check-groups, public-replay]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: Plan 03-09 source-pinned group construction
provides:
  - canonical overlapping-group local step with atomic work reservation
  - strict V3 Hsu schedule admission and replayable public evidence
  - independent ledger reconstruction from manifest, seed, and attempt identity
affects: [03-16, 03-17, SCH-06]
key-files:
  modified:
    - src/bp_registry/canonical/group_shuffled.py
    - src/bp_registry/canonical/contracts.py
    - src/bp_registry/canonical/execution.py
    - src/bp_registry/canonical/verification.py
    - src/bp_registry/manifests.py
    - data/manifests/schema-canonical-v3.json
requirements-completed: []
completed: 2026-09-24
status: complete
---

# Phase 03 Plan 10: Public Hsu Group Step

The canonical binary SPA path now executes a size-two, overlap-one Hsu group as one atomic local unit. Both check updates read a frozen V2C entry view; afterward, affected V2C messages refresh from the committed C2V state. Checks may share variables. The declared schedule seed and attempt identity generate a replayable check order, separately metered from physical sampling. Post-group convergence is explicitly recorded as the CSS adaptation.

V3 preflight requires the Hsu source ID and a schedule root identity, rejects incompatible controls and graphs with fewer than two checks, and exports the added schema field. The public verifier regenerates the order and candidate from the manifest, then compares terminal work and schedule evidence.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_group_shuffled.py tests/test_canonical_cli.py tests/test_manifest.py -k 'hsu or group_shuffled or canonical_v3_schema'` — 12 passed.
- A one-shot BB-144 public `run_canonical` and `verify_run` round trip passed in the test suite.
- A separate B1 one-group public preflight, run, and verify round trip passed.

## Commit

- `de29842` — public group execution, V3 admission, schema, replay, and tests.

## Deviations

- The V3 JSON schema was regenerated because the public schedule contract gained `source_id`.
- Tests and implementation were committed together; no separate TDD red-step evidence is claimed.
