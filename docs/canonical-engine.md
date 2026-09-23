# Canonical CSS engine: a checked development tutorial and contract reference

This guide runs the project-owned binary CSS sum-product implementation.  It is
not an adapter to a native decoder, a source-faithful reproduction, or a
statistical result.  The checked fixture is explicitly labelled
`canonical_implemented`, `development_fixture`, and `not_assessed`.

## Scope and approved environment

Use the approved `.venv` described in [environment-pins.md](environment-pins.md).
It is a node-specific development environment, not a portable release lock.
The commands below assume the repository root and a checked working tree.  They
do not fetch packages, alter the checked result, or expose hidden error truth to
the decoder.

If an approved environment needs its local project import registered, the only
permitted editable-install command is:

```bash
.venv/bin/python -m pip install --no-deps -e .
```

`--no-deps` is intentional: it prohibits dependency fetching.  Do not run
`pip install`, upgrade a package, or recreate `.venv` as part of reproducing
this tutorial.  During Phase 2 validation, the approved environment already
imports the checked project source without running that command.

## Run, inspect, reconcile, and verify the checked experiment

The public manifest is
`data/manifests/canonical-three-qubit-development.json`.  First, preflight it:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/manifests/canonical-three-qubit-development.json
```

Preflight validates the schema, environment declaration, artifact and matrix
identities, closed policy bindings, profile, and budgets before a sample,
ledger, or kernel operation.  Its JSON includes `run_id`,
`numerical_profile`, the resolved `policy_identity`, `shot_budget`, and the
development-evidence labels.

Run an isolated, disposable copy so the checked result is never modified:

```bash
OUT="$(mktemp -d "${TMPDIR:-/tmp}/canonical-three-qubit-development.XXXXXX")"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli canonical data/manifests/canonical-three-qubit-development.json --output "$OUT"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli reconcile "$OUT/events.jsonl"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run "$OUT"
```

The `canonical` report and `verify-run` report both return
`final_row_count: 2`.  The reconciliation query reports two final rows.  The
terminal results for this deterministic fixture are `completed` and `exact`
for shots 0 and 1.  `verify-run` recomputes the result from the hash-linked
structural ledger, checks the manifest identity and independent evaluation,
and rejects mismatched or relabelled evidence.

Inspect the persisted, checked result without executing a shot:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m json.tool data/results/canonical-three-qubit-development/result.json
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/canonical-three-qubit-development
```

Expected result fields map to contracts as follows:

| Result or event field | Contract it identifies |
| --- | --- |
| `run_id`, `manifest_sha256`, `ledger_sha256` | declared experiment and hash-linked durable evidence |
| `policy_identity` | resolved, ordered seven-role composition |
| `relation`, `fixture`, `assessment_status`, `statistical_claim` | evidence maturity: canonical implementation, development fixture, not assessed |
| terminal `outcome`, `logical_action_agrees`, `termination` | evaluation after selection and the terminal reason |
| `qualified_iterations`, `work_vector` | schedule-qualified flooding work, not a universal cost scalar |
| `runtime` / `missingness` events | per-attempt CPU timing and explicitly unavailable backend device time |
| `original_lineage_id`, `working_lineage_id`, `candidate_lineage_id` | immutable ancestry from problem through frozen candidate |
| trace semantic digest, when a trace sidecar is enabled | timing-independent observational semantic identity, not a performance measurement |

The checked fixture has trace level `off`; consequently it records no trace
sidecar digest.  That absence is declared by the manifest rather than inferred
from an empty trace file.

## Mathematical and numerical conventions

The persisted public manifest profile is `cpu-float64-spa-v1`; preflight
materializes its resolved engine profile as `binary-spa-flooding-f64-v1` in
`resolved_numerical_profile`.  That engine profile is materialized by
`src/bp_registry/canonical/numerics.py` and
`src/bp_registry/canonical/schedules.py`.  It uses deterministic CPU NumPy
`float64` and natural-log likelihood ratios,

\[
L = \log(P(0) / P(1)).
\]

For the binary CSS component being decoded, the observed syndrome convention is
`s = Hx (mod 2)`, with bit vectors ordered by the immutable CSS artifact.  A
hard-decision tie is resolved deterministically by the profile's canonical
index/order rule; no physical-error truth or unrecorded random draw chooses a
tie.

The check update uses the stable LLR-domain SPA (box-plus) procedure: combine
incoming messages through the sign/parity and stable magnitude operation, then
apply the observed syndrome sign.  Variable-to-check values are the channel
LLR plus the other incoming check messages.  The profile clips finite
calculation boundaries symmetrically at `K = 25`.  A non-finite message is a
recorded `NumericalFailure` terminal condition, not a silently propagated
value.  Degree-one checks, zero messages, normalization, initialization, and
ties have deterministic tested handling in the numerical profile; an
alternative precision, clipping limit, or randomized tie rule must be a new
named profile or declared policy, never an implicit substitution.

## Graph order and flooding buffers

Sparse input enumeration is normalized to a canonical **check-major,
variable-minor** edge table.  One flooding sweep reads the complete **old v2c
snapshot** (the old v2c snapshot), computes all check-to-variable messages,
forms beliefs, and only then commits the complete **fresh v2c buffer** (the
fresh v2c buffer).  It never interleaves fresh
and stale variable-to-check values.  The atomic work unit is therefore a
complete double-buffered sweep, not an individual array assignment.

The source anchors are `CanonicalEdgeTable` and `FloodingSchedule.sweep` in
`src/bp_registry/canonical/schedules.py`, `BinarySpaKernel` in
`src/bp_registry/canonical/kernel.py`, and the finite boundaries in
`src/bp_registry/canonical/numerics.py`.  These are project procedure anchors;
they do not claim that a paper's implementation used identical numerical
choices.

## Seven explicit policy roles and lifecycle

Every persisted `CanonicalExperimentV2` names every role, including explicit
identity policies when inactive:

| Role | Checked fixture binding | Responsibility |
| --- | --- | --- |
| `update` | `binary_spa` | finite binary SPA message procedure |
| `schedule` | `flooding` | edge/message ordering within an attempt |
| `state_memory` | `stateless` | declared policy-local memory behavior |
| `intervention` | `identity` | declared no-op search/intervention behavior |
| `stopping` | `syndrome_or_budget` | syndrome/budget termination decision |
| `selection` | `stable_first` | deterministic candidate choice |
| `postprocessing` | `identity` | declared no-op postprocessing behavior |

The engine, rather than a policy callback, traverses the named hooks at **shot,
search, member, leg, branch, attempt, iteration, and message** scope.  A
policy receives a capability-scoped decoder-visible view, owns only declared
private state, and returns typed decisions or mutations that the engine
validates.  It cannot obtain hidden sampled truth, evaluator state, ledger
ownership, or arbitrary kernel internals.  Binding evidence records a procedure
basis and ordered invariants alongside the closed registry entry.

Compatibility is enforced twice.  **Static composition validation** rejects
unknown kinds, omitted roles, unsupported declarations, and incompatible
binding metadata before sampling.  A **live-state invariant** check protects
runtime boundaries.  A source semantic that cannot be expressed through these
declared hooks needs a versioned lifecycle extension or a documented composite
controller, rather than an undocumented global callback order.

## Budgets, work, runtime, lineage, and evaluation

Count budgets are hierarchical hard caps at attempt, member/leg, search, and
shot scopes.  The engine must **reserve** the full proposed work before a
state-changing sweep and commits it only after the fresh buffer is finite.
Wall-clock limits are separate boundary checks, not retroactive work counts.
`WorkVector` records leaf work once (including c2v/v2c updates, belief
assemblies, candidate checks, and other typed units); ancestor totals are
derived through lineage instead of double-counted.

`iterations` is intentionally retained as a familiar headline but is a
**schedule-qualified iteration**: here, a flooding complete-double-buffered
sweep.  Per-attempt runtime has method, scope, unit, and precision.  The CPU
fixture emits `time.perf_counter_ns` timing and a `missingness` fact for
`backend_device_time`, because zero would falsely imply an observed device
measurement.

Lineage IDs are derived from typed logical parents and canonical content, not
event arrival, wall time, or process identity.  Candidate retention is a
storage choice after identity, while selection uses declared stable order.  The
selected payload becomes a **frozen decoder-visible candidate** before the
independent evaluator receives the hidden sampled truth.  The evaluator then
judges the original CSS problem and appends an evaluation annotation; it cannot
change selection.  This separation is why an exact development outcome is not
evidence of source-faithful or statistical reproduction.

## Compatibility examples

- The checked composition is compatible because it names all seven closed
  bindings and uses the CPU `float64` flooding profile.
- Replacing `flooding` with a residual scheduler is not a harmless label
  change: it needs a registered schedule procedure, its own qualified
  iteration semantics, and compatible lifecycle/work evidence.
- A random tie rule must declare replayable decoder-local randomness independent
  of physical-error sampling; it cannot reuse the deterministic profile name.
- A relay leg may transfer only a typed, named payload and has sequential
  attribution.  It cannot inherit arbitrary predecessor private state.

## Evidence boundary

This two-shot result is a bounded development smoke fixture.  It supplies an
executable contract check, not a publication curve, a population estimate, or
a claim of established methodological novelty.  Keep source-faithful
reproduction and controlled comparisons as separately declared experiment
relations with their own manifests, prespecified denominators, tolerances, and
evidence.
