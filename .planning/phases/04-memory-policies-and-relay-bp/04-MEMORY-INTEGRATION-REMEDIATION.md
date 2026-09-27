---
phase: 04-memory-policies-and-relay-bp
status: independent-memory-slice-verified-isolated
date: 2026-09-27
source_validation_commit: 62fe977
workflow: gsd-execute-phase
corrects: [04-03, 04-04]
affects: [04-13]
base_commit: 101a01b
branch: gsd/phase4-memory-integration-20260926
---

# Ordinary memory execution correction

The execution matrix below records the validated `62fe977` checkpoint.
Commit `3a3bb8c` subsequently implements disordered affine-prior assignments
at complete source-iteration traversals on the same three deterministic local
schedules. See [local disordered continuation](04-LOCAL-DISORDERED-AFFINE-CONTINUATION.md)
for its focused verification and remaining lifetime/schedule limits. Statements
below that reject disordered local affine execution describe the earlier
checkpoint; the live main campaign remains on its frozen source.

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
  reduction additions separately from directional BP work. PD-prime's field
  plus per-variable C2V history, and momentum's posterior plus velocity, each
  count as two owned variable vectors per committed update.
- Failed count-budget/iteration runs preserve the last committed diagnostic
  candidate and origin, with null for no committed proposal. It remains
  unselected; truth-aware classification belongs in the outer evaluator.
- Semantic verification reconstructs memory evidence, diagnostics, and the
  committed prefix preceding a numerical failure. Rehashed semantic
  alterations are rejected.
- PD-prime uses an O(n) per-variable C2V sum, reduced in canonical edge order,
  as the sufficient statistic for its delta equation.
- Min-sum, scalar NMS, and V3 per-iteration NMS/OMS dispatch/replay are
  covered. OMS now receives its beta assignment at every declared source
  iteration (rather than silently retaining beta index zero), and both NMS/OMS
  source-iteration vectors must cover the entire declared attempt before an
  artifact is loaded or a sample is drawn.
- Public ordinary disordered affine-prior bindings now declare a bounded
  per-variable Uniform interval and 64-hex root seed identity. Each admitted
  flooding source iteration derives its own decoder-local NumPy PCG64 draw;
  assignment state, evidence, and coefficient vector commit with the sweep and
  replay independently of hidden physical truth.
- Opt-in public V4 flooding-memory tracing now materializes the existing
  semantic-sidecar contract within the public output directory. Every
  committed retained sweep can expose decoder-visible beliefs, complete
  committed history arrays plus digests, PCG64 draw identity/evidence, and a
  terminal candidate origin. A single terminal `trace_link` precedes work
  evidence and carries the existing content-addressed sidecar link, caps, and
  truncation facts; no committed state produces an explicit unavailable reason.
  The trace observer never supplies the PCG64 context: public configuration
  and decoder identities are supplied unconditionally for each shot and replay.
- A bounded local-memory execution slice now runs through the existing Phase 3
  local executors. At an admitted local unit, PDBP, PD-prime, and momentum
  consume the complete fresh decoder-visible belief vector before candidate
  construction; V2C damping consumes the subsequently formed affected fresh
  V2C buffer. PD-prime receives that unit's complete C2V vector directly and
  reduces it in canonical edge order to its matched per-variable old/fresh
  sufficient statistic. It never reconstructs C2V from a clipped belief.
  All bindings retain separate histories and commit only after the unit's
  reserve, compute, and convergence check; denied or abandoned units discard
  proposals.
- Uniform affine prior memory now has a separate local source-iteration
  boundary: it stages the declared ordered affine prior before a deterministic
  local traversal, holds that exact prior across the traversal's units, and
  commits each owner history from the final decoder-visible posterior only
  after the traversal completes. An early convergence, denial, or numerical
  failure discards the uncommitted affine proposal while retaining already
  committed local-unit work honestly. Disordered local affine refresh remains
  rejected: its assignment lifecycle needs a distinct source-iteration
  reservation/evidence controller.

## Executable memory matrix

| Schedule family | Admitted local operands | Commit boundary | Explicit rejection |
| --- | --- | --- | --- |
| Flooding | affine prior, PDBP, PD-prime, posterior momentum, V2C damping at `source_iteration` | complete double-buffered sweep | local-update bindings and unsupported lifecycle declarations |
| Layered, check-node serial, variable-node serial | uniform affine prior at a complete `source_iteration` traversal, then PDBP, PD-prime (first field binding only), posterior momentum, and V2C damping at `local_update`; repeated supported bindings retain distinct histories | admitted local unit plus complete source traversal for affine history | disordered local affine, PD-prime after another field binding, wrong target/boundary, V2C-before-field order |
| Residual, randomized, group-shuffled | none in this slice | n/a | no full common belief-plus-affected-V2C operand/commit proof is wired for the memory binding controller |

All local bindings currently require `state_lifetime: attempt`,
`refresh_boundary: attempt_start`, and `retain_history: false`. These
constraints preserve the existing one-attempt scheduler lifecycle without
claiming a leg/search/member history controller that is not yet implemented.

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
4. Focused post-correction trace/disordered/NMS gate:
   `python -m pytest -q tests/canonical/test_memory_execution.py tests/canonical/test_memory_trace.py`:
   **35 passed** (5.17 s). This includes public V5 preflight/run/semantic
   replay of a disordered affine-prior arm, transactional PCG64 replay, capped
   trace sidecars, and per-iteration NMS execution.
5. Local-memory preflight/run/replay and rollback gate:
   `python -m pytest -q tests/canonical/test_memory_execution.py tests/canonical/test_local_memory_execution.py tests/test_manifest.py -k 'memory or canonical_v4'`:
   **41 passed, 33 deselected** (5.47 s). This includes the public layered
   PDBP-plus-damping V4 path, semantic replay, and a denied local-unit rollback.
6. Public trace and source-iteration repair gate:
   `python -m pytest -q tests/canonical/test_memory_execution.py tests/canonical/test_memory_trace.py -k 'semantic_replay or v3_source or memory_evidence_counts or public_v4_trace'`:
   **9 passed, 34 deselected** (3.48 s). It covers traced-versus-untraced
   disordered assignment equality, distinct public shot identities, linked
   history/draw/candidate facts, explicit sidecar truncation, V3 NMS/OMS
   source-iteration replay, pre-artifact short-vector rejection, and
   independent two-history operation-count validation.
7. Expanded local exact-operand/trace gate:
   `python -m pytest -q tests/canonical/test_local_memory_execution.py tests/canonical/test_memory_execution.py tests/canonical/test_memory_trace.py -k 'local or memory or trace'`:
   **53 passed** (15.39 s). It covers PD-prime's exact local C2V statistic,
   repeated momentum histories, all three admitted local schedule families,
   denied/numerical-failure rollback, public preflight/run/replay, local trace
   ON/OFF semantic equality, linked candidate/history sidecars, and cap
   truncation.
8. The local controller applies the active numerical profile before returning
   or storing a policy proposal. Saturated PD-prime histories and traces now
   equal the exact clipped belief consumed by the next unit. Public trace
   verification independently replays bounded ordinary-memory observations;
   hash-valid empty, altered-belief/history, or altered-candidate sidecars are
   rejected, while V3 local numerical terminals reconstruct their empty local
   schedule prefix.
9. The ordinary local replay reconstructs the declared SPA/min-sum update
   kernel and parameter assignment rather than assuming SPA. Numerical-failure
   traces replay their committed V5 prefix before accepting a sidecar; V3 local
   failures derive their retained local-unit count from the typed schedule
   terminal. Trace sidecar finalization failures emit typed unavailable
   evidence after decoder work, so observation never changes terminal decoder
   state.

These are implementation fixtures, not statistical performance evidence.
No calibration, evaluation, factorial or publication sample budget was used.

Final resumption regression, after `3743d35` and `2a00572`:
`OMP_NUM_THREADS=1 PYTHONPATH=src /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q`
passed **478 tests, with one existing skip**, in **299.52 seconds**. The bounded
reviewer recheck in `cdd82b4` confirms all four correction-slice findings resolved.
This does not replace the remaining complete-phase scientific and quality gates.

Subsequent independent continuation validation on `62fe977` passed **532 tests,
with one existing skip**, in **547.39 seconds**. The local prior keyword is now
passed only to an actual memory controller's schedule, preserving the legacy
Hsu public and retained-pilot round trips. Public admission tests explicitly
cover supported local min-sum and rejection of a non-Relay leg lifecycle.
See `04-IMPLEMENTATION-CONTINUATION-REVIEW.md` for the bounded trace/replay and
cache corrections. Unsupported entries below remain gaps; this is not phase
completion or performance evidence.

## Remaining Phase 4 work

- Local execution remains intentionally limited to the matrix above. Retained
  histories and lifetimes beyond one ordinary attempt remain unimplemented and
  reject explicitly. A non-Relay `leg` declaration now rejects before artifact
  loading rather than implying generic multi-leg execution. Mathematical
  compatibility declarations alone do not prove execution.
- Public trace support covers the admitted ordinary flooding and local V4
  boundaries only. Local sidecars observe only committed local histories and
  terminal decoder-visible candidates; they do not change controller state or
  randomness. Relay unavailable-link handling and any multi-leg/lifetime
  controller remain separate work and are not silently represented as complete
  traces in public preflight.
- The outcome-independent factorial execution supplement preserves the frozen
  damping-before-affine and momentum-before-affine arrays while recording the
  executable prior -> fields -> V2C order. It binds arm coefficients and the
  existing public trace contract. Its implementation tests do not authorize
  production sampling; terminal calibration and fresh evaluation are required.
- Calibration must terminate and settings freeze before fresh evaluation.
  Existing evaluation-runner code is prepared; its scientific gates remain.
- Do not mark Plan 04-13 or Phase 4 complete from this correction. Phase 5 and
  later regimes remain in scope after Phase 4's outstanding gates.

The main checkout's live Relay simulations are unaffected by this isolated
correction. Earlier memory-only V4 ledgers remain historical plain-BP evidence;
the new compact identity prevents their reuse as executed-memory evidence.
Earlier V3 source-iteration OMS/NMS evidence and memory-operation totals that
used the prior affected paths require requalification; this correction does not
rewrite durable historical ledgers.
