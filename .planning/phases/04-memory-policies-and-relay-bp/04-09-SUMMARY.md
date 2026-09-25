---
phase: 04-memory-policies-and-relay-bp
plan: "09"
subsystem: artifact-qualification
tags: [b1, css, artifact-identity, relay-bp, manifests, tdd]
requires:
  - phase: 03-update-rules-and-scheduling
    provides: frozen B1 v3 artifact and Phase 3 executable manifest
  - phase: 04-memory-policies-and-relay-bp
    provides: V4 memory manifest admission and Relay policy semantics
provides:
  - source-reconstructed B1 identity resolution with one measured stale-record disposition
  - reconciled B1 inventory and a V4 Phase 4 Relay-memory manifest bound to frozen v3
  - read-only BB-144 and HGP artifact identity qualification
affects: [04-10, 04-11, 04-12, 04-13, 04-14, 04-15, phase4-pilots]
tech-stack:
  added: []
  patterns: [source-reconstruction-before-admission, historical-evidence-preservation, resolved-identity-manifest-binding]
key-files:
  created:
    - scripts/qualify_phase4_artifacts.py
    - data/evidence/phase4-b1-identity-resolution.json
    - data/manifests/phase4-memory-relay-b1.json
  modified:
    - data/evidence/code-inventory.json
    - tests/canonical/test_phase4_evidence.py
key-decisions:
  - "B1 is inventory_stale: source reconstruction reproduces frozen v3 bytes and all artifact, matrix, ordered-logical, metadata, and Phase 3 manifest identities."
  - "Phase 4 binds B1 to v3 because only the inventory semantic digest was stale; no v4 artifact or historical rewrite is warranted."
  - "The Phase 4 B1 V4 manifest uses a compatible canonical-adaptation Relay affine-prior binding with alpha 0.875."
patterns-established:
  - "A post-repair qualifier retains the measured historical disposition alongside current matching records, rather than treating a successful repair as unresolved."
requirements-completed: [MOD-01]
actuals:
  tokens: 10358
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 7b95efe2c776fbe2ce0b31c11b8909499f5ada48
coverage:
  - id: D1
    description: Source reconstruction measures B1 raw, semantic, matrix, and ordered-logical identities, classifies the stale record, and read-only qualifies BB-144 and HGP.
    requirement: MOD-01
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/canonical/test_phase4_evidence.py -k 'b1 and (identity or digest or reconciliation or gate)'"
        status: pass
    human_judgment: false
  - id: D2
    description: Inventory-only B1 repair preserves Phase 3 evidence and binds a resolved Phase 4 V4 manifest to v3 through public preflight.
    requirement: MOD-01
    verification:
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/canonical/test_phase4_evidence.py -k 'b1 and (versioned_repair or historical_preserved or resolved_gate or regeneration)'"
        status: pass
      - kind: integration
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/phase4-memory-relay-b1.json"
        status: pass
    human_judgment: false
metrics:
  duration: "14m"
  completed: 2026-09-25
  status: complete
---

# Phase 04 Plan 09: B1 Identity Resolution Summary

**Source reconstruction proves B1 v3 is the executable identity; the only stale record was the inventory semantic digest.**

## Performance

- **Duration:** 14m
- **Started:** 2026-09-25T03:10:00Z
- **Completed:** 2026-09-25T03:24:03Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Reconstructed B1 from the pinned Panteleev--Kalachev v3 construction and reproduced the frozen v3 NPZ byte-for-byte, including raw, semantic, matrix, and ordered-logical identities.
- Classified exactly one disposition, `inventory_stale`, and retained the pre-repair conflicting semantic digest in the resolution evidence.
- Repaired the inventory only, preserved the v3 NPZ, v3 sidecar, and Phase 3 B1 manifest unchanged, and bound a preflighted Phase 4 V4 manifest to v3.
- Verified BB-144 and generated HGP identities read-only; HGP remains explicitly `author_instance: false`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/canonical/test_phase4_evidence.py -k 'b1 and (identity or digest or reconciliation or gate)'` — 3 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase3_codes.py tests/canonical/test_phase4_evidence.py -k 'b1 and (versioned_repair or historical_preserved or resolved_gate or regeneration)'` — 2 passed.
- `OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/phase4-memory-relay-b1.json` — passed; V4 memory compatibility admitted `relay-affine-prior-b1-v1`.
- Historical-preservation diff over the plan range reported no changes to `b1-panteleev-kalachev-v3.npz`, its v3 sidecar, or `phase3-pilot-b1.json`.

## Task Commits

1. **Task 1: Reconstruct B1 from the pinned source and classify the stale record**
   - `ba81b84` `test(04-09): add failing B1 identity qualification tests`
   - `839b8f4` `feat(04-09): qualify B1 identity from source reconstruction`
2. **Task 2: Apply the measured B1 repair without rewriting historical evidence**
   - `613a0fc` `test(04-09): add failing B1 inventory repair gate`
   - `31306fb` `feat(04-09): bind Phase 4 B1 to reconciled v3 identity`

## Decisions Made

- B1 resolves to the existing v3 artifact: the builder, frozen bytes, metadata, and Phase 3 manifest all agree on `3b3fb669...48eb38a6` raw and `ea120002...e20430548` semantic identity.
- The inventory entry now carries the measured semantic identity and an explicit link to the resolution record; its former `ea120ce6...17be3048` digest remains recorded as pre-repair evidence.
- No v4 B1 NPZ or metadata was created because a versioned artifact repair would falsely imply that the frozen evidence was stale.

## TDD Gate Compliance

- Task 1 RED: `.gsd/tdd-evidence/04-09-task-1-red.json` validated as `RED_EVIDENCE_OK`; GREEN commit `839b8f4` passed the focused qualification tests.
- Task 2 RED: `.gsd/tdd-evidence/04-09-task-2-red.json` validated as `RED_EVIDENCE_OK`; GREEN commit `31306fb` passed the resolved-manifest and preservation tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical qualification continuity] Preserved the stale-record disposition after the inventory repair.**
- **Found during:** Task 2 preflight verification.
- **Issue:** A fresh qualification after correcting the inventory would see no currently stale record and would fail closed as `unresolved`, losing the measured disposition needed by dependent plans.
- **Fix:** The qualifier now validates current agreement and retains the prior conflicting inventory digest from the immutable resolution record before reporting `inventory_stale`.
- **Files modified:** `scripts/qualify_phase4_artifacts.py`, `data/evidence/phase4-b1-identity-resolution.json`, `tests/canonical/test_phase4_evidence.py`.
- **Verification:** Both focused test commands and the public V4 preflight passed.
- **Committed in:** `31306fb`.

**Total deviations:** 1 auto-fixed (Rule 2).

## Issues Encountered

The public B1 preflight is materially slower than the focused unit checks because it verifies all 882-qubit matrix and ordered-logical identities. It completed successfully.

## Known Stubs

None.

## Next Phase Readiness

B1-dependent Phase 4 pilots may use only `data/manifests/phase4-memory-relay-b1.json` or the reconciled v3 inventory identity. The generated HGP remains a qualified generated-family adaptation and cannot be presented as a paper-exact instance.

## Self-Check: PASSED

---
*Phase: 04-memory-policies-and-relay-bp*
*Completed: 2026-09-25*
