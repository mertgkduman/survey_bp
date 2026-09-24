---
phase: 04-memory-policies-and-relay-bp
plan: "02"
subsystem: canonical-memory-policies
tags: [python, numpy, bp, damping, pdbp, pdprime, momentum, ewa, relay]
requires:
  - phase: 04-01
    provides: typed affine prior-memory primitive and Phase 4 relay policy foundation
provides:
  - target-specific V2C damping, PDBP field mixing, and PD-prime C2V delta mixing
  - Chen posterior momentum with explicit state and original-C2V subtraction
  - source-named EWAInit and Relay aliases over one affine prior primitive
  - auditable source equations, fidelity labels, and code-drift register
affects: [04-03, 04-04, 04-05, memory-composition, relay]
actuals:
  tokens: 8152
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 52a1a57e1efd799a80e117578f0bb5109e955779
tech-stack:
  added: []
  patterns:
    - pure target proposal plus binding-owned history commit
    - source-named aliases over a single mathematically identical primitive
key-files:
  created:
    - docs/memory-policy-sources.md
  modified:
    - src/bp_registry/canonical/memory.py
    - tests/canonical/test_memory_policies.py
key-decisions:
  - "Keep PDBP field mixing and PD-prime edge-delta mixing as separate state machines because their operands and history differ."
  - "Represent uniform EWAInit and Relay affine memory as source-named aliases of one primitive under gamma = 1 - alpha."
patterns-established:
  - "Every memory policy declares its target, boundary, owned history, reset, and fidelity label."
requirements-completed: [MEM-01, MEM-02, MEM-03, MEM-04]
coverage:
  - id: D1
    description: Target-specific V2C damping and Pretti field/delta mixing with endpoint, boundary, and divergence fixtures.
    requirement: MEM-01
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_memory_policies.py -k 'damping or pdbp or pdprime or target or boundary'"
        status: pass
    human_judgment: false
  - id: D2
    description: Chen momentum and shared EWAInit/Relay affine prior policies with reset and reparameterization fixtures.
    requirement: MEM-03
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_memory_policies.py -k 'momentum or affine or ewa or reparameterization or reset'"
        status: pass
    human_judgment: false
  - id: D3
    description: Source and drift audit for all selected memory mechanisms.
    requirement: MEM-04
    verification:
      - kind: unit
        ref: "OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_update_rules.py tests/canonical/test_memory_policies.py"
        status: pass
    human_judgment: false
duration: 6min
completed: 2026-09-24
status: complete
---

# Phase 04 Plan 02: Memory Equations and Affine Source Policies Summary

**Four source-linked memory mechanisms with explicit target histories, plus EWAInit and Relay aliases that share an affine prior primitive.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-24T23:17:30Z
- **Completed:** 2026-09-24T23:23:44Z
- **Tasks:** 2/2
- **Files modified:** 3
- **Verification:** 41 passed in 0.54s

## Accomplishments

- Added pure, boundary-checked V2C damping, PDBP field mixing, and PD-prime edge-aligned C2V-delta policies with separate committed histories.
- Added Chen posterior momentum with `g0=0`, `Q0=prior`, explicit reset, and a V2C method that subtracts the original current C2V contribution.
- Added EWAInit and Relay source aliases over `AffinePriorMemory`, and documented their exact reparameterization, source qualifications, original-code availability, and Relay paper/code drift.

## Task Commits

1. **Task 1: Distinguish damping, PDBP, and PD-prime mixing**
   - `1947c39` `test(04-02): add failing targeted memory-rule contract`
   - `55a5ca3` `feat(04-02): implement target-specific damping and mixing`
2. **Task 2: Implement posterior momentum and shared EWA/Relay affine primitive**
   - `d8b1c30` `test(04-02): add failing momentum and affine contracts`
   - `f38f1a4` `feat(04-02): add momentum and affine source policies`

## Files Created/Modified

- `src/bp_registry/canonical/memory.py` — source-qualified state machines, pure proposals, commits, resets, and affine aliases.
- `tests/canonical/test_memory_policies.py` — source equations, endpoint, boundary, divergence, reset, and reparameterization fixtures.
- `docs/memory-policy-sources.md` — source equation register, scientific fidelity labels, selected/rejected variants, and drift audit.

## Decisions Made

- PDBP and PD-prime remain distinct policies because one mixes complete fields while the other advances a field with edge-aligned C2V deltas.
- EWAInit and uniform Relay memory are preserved as source aliases of one affine primitive under `gamma = 1 - alpha`; their different lifetime and source labels remain explicit.
- Classical, GF(4), and circuit-source equations are retained as scalar CSS adaptations rather than represented as source-faithful quantum performance methods.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The TDD evidence checker consumes TAP summaries while the project test command uses pytest. Each RED phase therefore ran the selected pytest command and recorded the same failing test through a direct TAP-compatible invocation before GREEN; both RED records passed `tdd-red-evidence` validation.

## TDD Gate Compliance

Both tasks have a validated RED commit before their corresponding GREEN commit. No refactor commit was needed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The policy implementations now expose declared targets, advance boundaries, reset lifetimes, and source fidelity required for ordered composition and relay integration. Disordered Relay gamma assignments and engine-level composition admission remain owned by subsequent Phase 4 plans.

## Self-Check: PASSED

- Confirmed the three declared production/documentation/test files and this summary exist.
- Confirmed all four RED/GREEN task commits exist in repository history.

---
*Phase: 04-memory-policies-and-relay-bp*
*Completed: 2026-09-24*
