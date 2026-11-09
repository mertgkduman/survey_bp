---
quick_id: 261108-qcu
status: complete
baseline: 872f7e1
---

# Expand compatible policy support across execution regimes

User request: expand support for all policies across kernels; unsuitable GPU
policies may be left out. Execute through GSD inline; no automatic subagents.
Preserve frozen legacy defaults, numerical identities, results and publication
gates. New public policy surfaces must have explicit versions and admission.

"All policies" refers to implemented repository policies, not mapped-only future
algorithms or unavailable trained artifacts. User scope decision: use only
existing/source-defined counterparts. Do not invent cross-family Pauli memory
or intervention adaptations. Binary CPU/circuit parity reuses existing equations.

1. Inventory every implemented update/schedule/memory/intervention/controller and
   its required operands. Extend the canonical binary session/controller seams
   with owned per-variable priors, including shortening and syndrome transforms,
   while preserving the scalar-channel path exactly.
2. Build a versioned shared binary policy runner for code-capacity and circuit
   fault graphs. Reuse existing canonical schedules, ordered memory, Relay,
   guided/impulse/freezing/syndrome-flip/sign-flip/restarting and ensemble policies.
   Include graph/iteration assignments and randomized/group/residual scheduling.
   Inventory clarification: clustered learning has only an artifact gate, not an
   implemented executor; exclude it under the user's existing-counterpart scope.
   Reject
   unsupported combinations before execution with an operand-specific reason.
3. Expose the shared runner through an opt-in Stim/Sinter interface with complete
   model/configuration/input/output/work/lineage evidence, original detector
   validation, affine observable projection, safe packed I/O and replay. Keep the
   existing circuit-policy-v1 interface unchanged.
4. Preserve the already implemented source-defined Pauli counterparts under the
   user's chosen scope; do not invent generic cross-family adaptations. Keep
   named MBP4/Q-BPGD/aSCED mathematics distinct.
   Publish one executable capability inventory describing implemented paths,
   mathematical incompatibilities and deliberately excluded GPU combinations.
5. Qualify independent equations, matched CPU/circuit outputs, policy sensitivity,
   state reset/continuation, hidden-truth exclusion, complete work accounting,
   invalid admission, replay and legacy regressions. Keep compiled ordinary CPU
   paths available; do not silently advertise scalar policies as compiled/GPU.
   Preserve the hardware-qualified GPU subset unless a concrete compatible
   extension warrants separate hardware qualification.

Completion requires concrete implementations and tests for the identified
compatible gaps, documented genuine exclusions, source-hashed evidence, a final
regression run appropriate to the breadth of changes, atomic commits and STATE
updates. This is not permission to relabel adapters as source-faithful paper
reproductions or rerun existing simulation campaigns.

## Execution checkpoint

- Prior/controller foundation committed as 7f888a1.
- Shared CPU/Sinter runner, six schedules, five memory policies, nine controllers,
  generated/indexed coefficients, existing precision formats and capability
  inventory implemented. New binary-to-Pauli adaptations and GPU extensions excluded.
- Final affected suite: 387 passed, including 125 new qualification cases.
- Frozen-baseline comparison: 82 complete legacy receipts byte-identical to 872f7e1.
- Real Sinter worker: 24 shots across serial/impulse/precision; every ledger replayed.
- Bounded warm timing: 55.7x scalar/compiled ratio, exact outputs; all receipts retained.
- Broad suite: 2462 passed, 20 skipped with required OMP_NUM_THREADS=1. An initial invocation
  omitted that variable, caused manifest admission failures, and was interrupted;
  its log is retained. Shared execution committed as c512723; see SUMMARY.md and
  qualification.json for final scope, source hashes and overlapping verification counts.
