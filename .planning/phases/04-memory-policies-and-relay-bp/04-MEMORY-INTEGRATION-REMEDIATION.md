---
phase: 04-memory-policies-and-relay-bp
status: flooding-correction-verified-isolated
date: 2026-09-26
workflow: gsd-execute-phase
corrects: [04-03, 04-04]
affects: [04-13]
base_commit: 101a01b
branch: gsd/phase4-memory-integration-20260926
---

# Ordinary memory execution correction

## Finding and authorized work

During the user's requested coding continuation, Plan 04-13's factorial runner
could not safely use ordinary-memory arms. Public V4 preflight validated the
memory declarations, but `_canonical_kernel_manifest` projected memory-only
inputs to V3 and discarded `memory`. The executable V5 contract already
existed, while the structural executor did not dispatch it. Thus previous
memory-only V4 runs executed plain BP. The prior 04-03/04-04 completion
summaries overstated execution coverage; retain those summaries as history.

This is prerequisite corrective work within the approved Phase 4 execution.
The live Relay calibration invokes CLI processes from the main checkout.
Work therefore stays in the isolated checkout
`/hpc/group/pfisterlab/mg551/storage/survey_bp_memory_integration_20260926`;
do not merge kernel changes into that live source tree mid-campaign.

## Implemented and verified

- Public memory-only V4 now carries its full memory composition into compact
  V5. Relay V4 and historical V2/V3 projections are preserved.
- One flooding attempt/leg executes affine prior, V2C damping, PDBP, PD-prime,
  and posterior momentum using the existing equation primitives. Repeated
  bindings have separate histories. Operand order is prior, fields, then V2C.
- Histories commit only after a whole admitted sweep and successful
  convergence check. Denial, compute/check failure, and reset reject or roll
  back private state; reset invalidates stale proposals.
- Momentum requires explicit alpha and gamma, replacing the earlier unused
  beta declaration. Source coefficient endpoint constraints now match the
  primitives. No old beta value is assigned an invented mapping.
- Terminal evidence records resolved primitives/fidelity, private-history
  digests, committed iterations, memory element updates and PD-prime C2V
  reduction additions separately from directional BP work.
- Failed count-budget/iteration runs preserve the last committed diagnostic
  candidate and origin, with null for no committed proposal. It remains
  unselected; truth-aware classification belongs in the outer evaluator.
- Semantic verification reconstructs memory evidence, diagnostics, and the
  committed prefix preceding a numerical failure. Rehashed semantic
  alterations are rejected.
- PD-prime uses an O(n) per-variable C2V sum, reduced in canonical edge order,
  as the sufficient statistic for its delta equation.
- Min-sum, scalar NMS, and per-iteration OMS dispatch/replay are covered. OMS
  assignments must cover the declared attempt limit; unsupported per-iteration
  NMS rejects before artifact loading rather than failing during execution.

## Verification

Commands run with `PYTHONPATH=src`, `OMP_NUM_THREADS=1`, and the main checkout's
approved `.venv/bin/python`, from the isolated checkout.

1. Initial regression reproducer: 7 failures, including public V4 projecting
   to V3 instead of V5; numerical executor module absent.
2. `python -m pytest tests/canonical tests/test_manifest.py tests/test_canonical_cli.py -q`:
   **356 passed, 1 skipped** (273.84 s) on the integration revision. The skip
   is the existing B1 notebook/digest evidence placeholder in
   `test_phase4_evidence.py`, not a memory execution test.
3. Final targeted gate after assignment/admission/reset checks:
   `python -m pytest tests/canonical/test_memory_execution.py tests/test_manifest.py -q`:
   **67 passed** (7.37 s), including 30 ordinary-memory execution tests.
4. Generated public V4 schema remains identical to the checked schema; model
   validator corrections do not change its JSON shape. `git diff --check`
   passes.

These are implementation fixtures, not statistical performance evidence.
No calibration, evaluation, factorial or publication sample budget was used.

## Remaining Phase 4 work

- Local-schedule memory execution, retained histories, lifetimes beyond this
  single attempt/leg, per-iteration NMS, and public ordinary disordered prior
  assignments remain unimplemented and now reject explicitly where applicable.
  Mathematical compatibility declarations alone do not prove execution.
- The frozen factorial design lists damping-before-affine and
  momentum-before-affine interaction binding arrays. Those orders violate the
  implemented operand dependencies. Resolve their execution semantics in a
  versioned, outcome-independent supplement/amendment before factorial
  sampling; preserve the frozen design/caps and document the discrepancy.
- Ordinary arm coefficient settings and diagnostic trace hooks still need
  implementation before Plan 04-13 Task 2 can run.
- Calibration must terminate and settings freeze before fresh evaluation.
  Existing evaluation-runner code is prepared; its scientific gates remain.
- Do not mark Plan 04-13 or Phase 4 complete from this correction. Phase 5 and
  later regimes remain in scope after Phase 4's outstanding gates.

The main checkout's live Relay simulations are unaffected by this isolated
correction. Earlier memory-only V4 ledgers remain historical plain-BP evidence;
the new compact identity prevents their reuse as executed-memory evidence.
