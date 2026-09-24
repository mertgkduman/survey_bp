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
terminal results for this deterministic fixture are `completed`; their
independently evaluated outcomes are `logical_failure` for shot 0 and `exact`
for shot 1. `verify-run` recomputes the result from the hash-linked
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
| terminal `profile` and `runtime` profile evidence | typed per-attempt CPU runtime/resource facts, adapter overhead, and explicit unavailable backend-device facts |
| `original_lineage_id`, `working_lineage_id`, `candidate_lineage_id` | immutable ancestry from problem through frozen candidate |
| `trace_plan` | public tracing is admitted only as `off` until a canonical trace hook can emit bounded sidecars honestly |

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

For X-error recovery in the binary CSS component, the observed Z-check syndrome
convention is `s_Z = H_Z e_X (mod 2)`, with bit vectors ordered by the immutable
CSS artifact. The canonical sampler therefore forms the decoder-visible
syndrome from `H_Z` and the hidden X-error vector `e_X`; it does not substitute
`H_X` for this recovery component. A
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

## Version 3 update rules and layered SPA

`CanonicalExperimentV2` remains the historical binary-SPA/flooding contract:
its schema, selector, numerical profile, and persisted meanings do not change.
`CanonicalExperimentV3` uses the named `cpu-float64-min-sum-v1` profile for
`min_sum`, `normalized_min_sum`, and `offset_min_sum`; those update rules are
intentionally flooding-only. The non-flooding public compositions are all
`binary_spa` under the historical `cpu-float64-spa-v1` profile. Layered manifests
declare conflict-free check `partitions` plus `provenance`; graph-colored partitions
add their deterministic construction rule. Public terminal evidence retains realized
membership/order, local progress, the full work vector, two non-convertible budget
views, and explicitly qualified schedule runtime facts. Its generated public schema is
`data/manifests/schema-canonical-v3.json`; regenerate it only from
`CanonicalExperimentV3.model_json_schema()` when the strict model changes.

### Focused noncluster schedule matrix

This is a focused compatibility matrix, not a claim that update and schedule
policies are universally interchangeable. Every listed local schedule runs through
`CanonicalLocalStepExecutor`, reserves its complete local mutation and one
convergence check before committing, and is replayed by `verify-run` from the
preflighted manifest rather than trusted merely because a ledger event was rehashed.

| Schedule kind | Admitted update | Atomic local unit | Required manifest evidence |
| --- | --- | --- | --- |
| `layered` | `binary_spa` | `one_layer` | explicit/source partitions and provenance; graph coloring also gives its construction rule |
| `check_node_serial` (check-node serial) | `binary_spa` | `one_check_all_c2v_then_affected_v2c` | canonical check order; later checks observe refreshed affected V2C state |
| `variable_node_serial` (variable-node serial) | `binary_spa` | `one_variable_belief_then_incident_v2c` | canonical variable order; the current incident C2V state is gathered before fanout refresh |
| `residual` | `binary_spa` | `one_residual_selected_c2v_commit` | the pinned conventional Huang--Ueng sRBP cache, canonical-edge tie rule, and explicit setup/decode work |
| `randomized` | `binary_spa` | one local unit of its declared layered base | `base_schedule`, `refresh_scope`, and a SHA-256 `root_identity`, plus the base partition evidence |

Randomized traversal uses only its purpose-separated `schedule_order` PCG64
stream. Its configuration, attempt, or sweep refresh boundary and every realized
order are terminal evidence; this stream never changes the matched physical sample.
The current public randomized factory deliberately admits only a layered base. A
randomized serial base, a non-SPA local schedule, min-sum plus a local schedule, a
missing source artifact for learned clustering, or any undeclared partition/refresh
combination is a **compatibility rejection before sampling**: it creates neither a
physical sample nor partial shot evidence.

### Clustered RL-S external artifact checkpoint

`clustered RL-S` is not an admitted canonical schedule.  In particular, a generic
layer, random partition, synthetic Q-table, fixture, retrained policy, or successful
qualification record is not Moradi support and cannot complete `SCH-06`.  The exact
author Q-table and ordered partition remain an external blocking dependency; their
training/production cost is recorded as `unknown`, never zero.

When authoritative bytes are supplied, create a strict JSON specification containing
exactly `q_table_path`, `partition_path`, the two SHA-256 fields, source `id`/`uri`/
`revision`/`record_sha256`, `graph_sha256`, `channel`, `kernel`, `state_encoding`,
`action_encoding`, `tie_breaking`, `q_shape`, and `check_count`.  The paths are
relative to an independently supplied confined root.  Then run:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli qualify-cluster-artifact \
  cluster-artifact-spec.json --approved-root author-release-directory
```

The command accepts only bounded `.npy` float64 Q-table bytes and bounded strict JSON
partition bytes; it rejects pickle/object arrays, traversal/symlink escapes, oversized
or malformed payloads, nonfinite values, raw-hash mismatches, wrong Q shape, incomplete
or repeated partition membership, and source/graph/channel/kernel/state/action/tie
metadata mismatches.  It emits a sorted schema-version-1 report with `qualified`,
`status` (`qualified`, `unavailable`, or `incompatible`), the pinned source and raw
hash facts, all check results, and the persistent labels
`not_established_by_qualification` for source support and reproduction.  An unavailable
or incompatible artifact writes its report but exits 2; a qualified artifact exits 0.
Qualification does not execute a schedule, establish a source claim, reproduce a paper,
or complete `SCH-06`.

For every local terminal, `source_iteration` gives the named local-unit count,
`completed_traversals` and `local_cursor` retain partial traversal state, and the
schedule evidence exposes fresh/stale visibility, selected order, residual cache
semantics, or randomized replay facts as appropriate. These quantities are not
converted to flooding sweeps or a universal cost.

Phase 3 pilot terminals also retain `setup_runtime` and `decode_runtime` as
separate nanosecond measurements. Setup covers canonical graph, kernel, and
schedule initialization; decode is the profiled attempt wall time after
subtracting initialization inside that profile. Local schedule construction
before the attempt is included in setup. Public preflight, artifact loading,
and ledger I/O are outside these two scopes, so their sum is not an end-to-end
CLI runtime. If an attempt ends before a scope is measured, its value is
explicitly unavailable rather than zero.

For an outgoing check-to-variable edge, min-sum uses

\[
m_{c\to v}=(-1)^{s_c}\prod_{u\in N(c)\setminus v}\operatorname{sign}(q_{u\to c})
\min_{u\in N(c)\setminus v}|q_{u\to c}|.
\]

Normalized min-sum applies its declared normalization before the inherited
finite saturation:

\[
m^{\mathrm{NMS}}_{c\to v}=\alpha\,m_{c\to v}.
\]

Offset min-sum uses the same signed extrinsic minimum, but subtracts its
explicit nonnegative beta in `float64`, floors the magnitude at zero, and only
then applies the named finite saturation:

\[
m^{\mathrm{OMS}}_{c\to v}=\operatorname{sat}\left(
(-1)^{s_c}\prod\operatorname{sign}(q_{u\to c})
\max(0,\min|q_{u\to c}|-\beta)\right).
\]

The update policy's `parameter_assignment` accepts exactly one tagged shape:
`{"shape":"scalar","value":alpha}`, a `source_iteration` `values` vector,
or graph-bound `check` / canonical `edge` `values` with a matching
`graph_sha256`. There is no implicit vector broadcasting. Each resolved value
is a finite `float64` alpha with `alpha >= 0`; `0 < alpha <= 1` is labelled
`conventional`, while larger finite alpha is explicitly `exploratory`, never a
source-faithful preset. Resolved values and this provenance are retained in
terminal `policy_effects` and independently reconstructed by `verify-run`.

For either NMS or OMS, a V3 update may instead carry a closed
`parameter_generator` plus `parameter_refresh` declaration. The only current
generator is `numpy.PCG64` with a finite nonnegative uniform interval and a
graph-bound scalar, check, or canonical-edge output. Its purpose is always
`parameter_assignment`, separate from both `schedule_order` and physical
sampling. Evidence retains the generator/version, distribution bounds,
provenance, graph hash, derived seed identity, refresh scope, source-iteration
boundary, and every resolved assignment. Refresh scopes are exactly
`configuration`, `attempt`, and `source_iteration`: the latter is the
schedule's recorded iteration boundary, never a layer/node/residual local-unit
counter. The draw is admitted atomically before RNG advancement; an admission
denial leaves both assignment state and RNG state unchanged.

Public V3 execution currently admits generated NMS/OMS assignments only with
`configuration` refresh under flooding. Preflight rejects generated `attempt`
or `source_iteration` refresh and generated assignments under local schedules;
those scope contracts remain available for isolated semantics tests. The
configuration draw is replayed from the compact manifest and immutable graph
by both the kernel and `verify-run`.

`source_defined` generation requires a source anchor. Arbitrary generated
ranges are `exploratory`; no generated exploratory declaration can be relabeled
as a source-faithful setting.

To run the scalar NMS development variant in a disposable directory, derive a
strict V3 manifest from the checked fixture, then use the same public commands:

```bash
OUT="$(mktemp -d "${TMPDIR:-/tmp}/canonical-nms.XXXXXX")"
OMP_NUM_THREADS=1 .venv/bin/python -c 'import json, pathlib; p=pathlib.Path("data/manifests/canonical-three-qubit-development.json"); m=json.loads(p.read_text()); m.update({"schema_version":3,"run_id":"canonical-nms-development","numerical_profile":"cpu-float64-min-sum-v1"}); m["policies"]["update"].update({"kind":"normalized_min_sum","binding_id":"update-nms-v1","parameter_assignment":{"shape":"scalar","value":0.75}}); pathlib.Path("'"$OUT"'/nms.json").write_text(json.dumps(m))'
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight "$OUT/nms.json"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli canonical "$OUT/nms.json" --output "$OUT/result"
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run "$OUT/result"
```

The final command must report `final_row_count: 2`. Changing a declared or
resolved assignment, policy effect, candidate, progress, work, or profile
cannot be made valid by rehashing ledger records: the independent verifier
reconstructs the manifest-bound terminal claims.

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
sweep. Per-attempt runtime/resource evidence is emitted as a typed local
profile: wall and process CPU time, peak host memory, adapter overhead, and
explicitly unavailable backend-device timing/memory for this CPU fixture.
Disabled profiling emits typed `not_collected` missingness rather than zeroes;
the profile values are observational and never affect decoding, stopping, or
candidate selection.

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
