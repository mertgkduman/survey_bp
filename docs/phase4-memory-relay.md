# Phase 4 memory policies and Relay-BP

Phase 4 is in progress. Its canonical memory correction, factorial preparation
and notebook analysis live in the isolated memory-integration checkout while
the main checkout runs its frozen Relay calibration. Do not interpret fixture
outputs or notebook infrastructure as measured decoder performance.

## Equations, state and source identity

[Memory policy sources](memory-policy-sources.md) records the damping, PDBP,
PD-prime, posterior-momentum and affine-prior equations, coefficients, targets,
private histories, resets, original-C2V subtraction and source qualifications.
Repeated bindings own separate histories. Prior operands precede field updates,
which precede V2C updates; a versioned factorial supplement records the
discrepancy between this dependency order and the original frozen binding arrays.
Histories and diagnostic candidates commit only with admitted complete work.

Uniform EWAInit and Relay affine memory are the same primitive under
`gamma = 1 - alpha`. Seeded disordered assignments are explicit controller
adaptations, with draw identities and refresh boundaries. Mathematical
compatibility declarations do not establish that every schedule or lifetime has
an implemented numerical execution path. Consult the memory-integration
remediation record for current execution coverage and outstanding gaps.

The isolated executor runs all five memory kinds at flooding boundaries.
Layered, check-node serial and variable-node serial execution also admit PDBP,
PD-prime, posterior momentum and V2C damping at atomic local boundaries, with
separate histories for repeated compatible bindings. PD-prime uses the actual
complete C2V operand; clipping cannot be undone by subtracting beliefs. Local
uniform and disordered affine-prior bindings stage once per source traversal, hold that prior
through local units, and advance posterior history only after a complete
traversal. An incomplete traversal keeps its committed local work and discards
uncommitted affine history and assignment evidence. Disordered assignments use
decoder-local PCG64 streams bound to the shot and source iteration; tracing
does not change the draws. Other local schedules and retained histories across
additional lifetimes remain explicit gaps. PD-prime must precede other field bindings.
These three deterministic local schedules support sum-product and the declared
min-sum, normalized min-sum and offset min-sum profiles. Replay uses the same
profile and source-iteration parameter assignment as execution.

The original executable reference is **trmue/relay v0.2.2**, immutable commit
`14cb31a18f9b9d7d099791b793e35b8a2951f8f3`. Its source record, qualification and
observer patch are in `data/evidence/relay-v0.2.2-source.json` and
`native/relay-v0.2.2-observer.patch`. The installed local editable fork and PyPI
package do not inherit this identity. Preserve paper parameters, Rust defaults,
Python defaults and README examples separately. The observer boundary is
behavior-neutral; unavailable native gamma/work/resource facts remain explicit.

Relay transfers only a digest-bound finite posterior LLR and resets leg-local
state. Candidate selection uses decoder-visible syndrome/prior weights and
stable earlier-leg ties. Independent outcome evaluation uses the immutable
original problem after selection. Neither policies nor the author adapter
receive hidden physical truth.

## Bounded experimental workflow

The frozen design and cap manifest are `data/evidence/phase4-pilot-design.json`
and `data/manifests/phase4-pilot-caps.json`. Preserve these bytes and all
superseded evidence. BB-144, reconciled B1 and generated HGP retain ordered
artifact hashes; generated HGP is explicitly non-paper-exact. B1 uses the
documented bounded three-leg work envelope. All campaigns retain finite
configuration/shot/work/runtime limits and disjoint stage sample namespaces.

1. Reconcile the running calibration using its existing async manifest. Never
   relaunch a live PID or change its source/caps. Retain every coarse/refinement
   attempt, Wilson uncertainty, work, failure and capped/inconclusive terminal.
2. From verified terminal calibration, freeze deterministic per-preset and
   shared candidate settings. Apply the prespecified interval/work/lexicographic
   tie rules; an insufficient-precision candidate remains inconclusive.
   In the isolated continuation, `scripts/verify_phase4_calibration.py` checks
   the complete planned configuration/shot population, deterministic physical
   sample identities, work caps and reconstructed aggregates/accounting before
   either legacy selection freezing or shared-view preparation. Its
   `surface_integrity_only` result supplements the separate public verification
   of every retained canonical terminal; it does not replay ledgers itself.
3. Use `scripts/run_phase4_evaluation.py --prepare`, then its `--run` and
   `--run-native` modes for fresh, matched observations under frozen caps. The
   current V4 evaluation cap admits baseline plus two selected-preset arms.
   Fresh shared-settings evaluation requires a versioned presampling cap
   amendment; a retained shared candidate is not an evaluated arm.
   The isolated `build_shared_evaluation_supplement(...)` API prepares a
   separately identified finite contract for source/canonical kernels using
   the same shared memory setting and matched evaluation namespace.
   `build_shared_manifest(...)` permits manifest validation only. Neither API
   publishes an amendment, reserves scheduler entitlement, or starts samples;
   its explicit supplemental wall ceiling is preparation, not funded compute.
4. Run the focused factorial only after its required predecessor evidence and
   versioned execution supplement are verified. Preserve all 14 arms, three
   regions and three codes; use the frozen per-code shot/work limits.
5. Read producer-qualified notebook views from verified originating executions
   and retain linked per-shot/trace evidence. The campaign readers reconstruct
   planned populations, outcome classifications, work and matched cohorts;
   missing, running or incompatible evidence keeps its original status. The
   production calibration, fresh evaluation and factorial views fill when their
   terminal evidence becomes available.

The auxiliary lower-noise and exact-author agreement campaigns have separate
designs, sample identities and outputs. Their terminal results do not substitute
for fresh evaluation of calibration-selected settings.

## Outcomes, work and tracing

Retain five diagnostic proposal cells: valid syndrome/correct logical action,
valid syndrome/wrong logical action, invalid syndrome/correct logical projection,
invalid syndrome/wrong logical projection, and no proposal. Invalid-syndrome
logical projection is diagnostic only. No recovery counts as an all-shot
failure; an interrupted command is separately incomplete evidence. Conditional
selected-valid denominators and paired matched denominators are explicit.

Keep canonical C2V/V2C work, memory element operations, reduction additions,
controller/transfer work, per-leg totals, setup/tuning costs, elapsed runtime and
resource facts in their original units. Retain upper tails and measurement
missingness. A heterogeneous scalar cost or a native-iteration-to-C2V conversion
has no automatic justification. Representative traces preserve beliefs,
histories, assignment draws, leg transitions, candidates and public ledger links,
with record/byte limits, truncation and native unavailability.

Public trace links cover ordinary flooding-memory and the supported local-memory
V4 execution. Relay traces remain unavailable in this preparation. Decoder
assignment identities are supplied independently of the trace observer, so
enabling tracing preserves the sampled coefficients and decoder semantics.
Memory sidecars are checked against independent numerical replay, including
committed beliefs, private histories and candidate records. Capped sidecars keep
their verified prefix and explicit truncation instead of claiming a full trace.
Numerical-failure sidecars must match the independently reconstructed committed
prefix. A sidecar finalization or storage failure records an unavailable trace
reason while preserving decoder work and terminal evidence.

## Notebook execution and reuse

`notebooks/phase4-memory-relay-analysis.ipynb` has all 13 research sections.
Tables and failure figures retain exact denominators and 95% Wilson intervals.
Retained-campaign validation can take several minutes. The confined executor
allows ten minutes per cell for that analysis and two minutes in fixture mode.
Development fixtures exercise these views with explicit synthetic labels;
production figures require verified originating execution. The executor pins the observed
NumPy/Matplotlib/nbformat/nbclient/ipykernel versions, requires the project venv,
clears notebook outputs, confines source/output paths and removes volatile cell
timings. In an existing GSD worktree it uses the primary checkout's venv.

From the primary checkout:

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/execute_phase4_notebook.py --fixture
```

From the isolated memory-integration checkout, use the primary checkout's
absolute `.venv/bin/python` path. Fixture execution consumes no campaign shots
and labels every stage `development_fixture` / `not_assessed`. Omit `--fixture`
to inspect campaign evidence and qualified snapshot availability. This mode
never starts simulation. `--campaign-root` can read another checkout of the same
Git repository; outputs stay in the integration checkout. Each executed notebook
saves its figures alongside its output, avoiding writes to the campaign inputs.

For a portable local HTML preview of a saved executed notebook:

```bash
.venv/bin/python scripts/preview_phase4_notebook.py \
  --input data/results/phase4-notebook/executed.ipynb \
  --output data/results/phase4-notebook/preview.html
```

The preview embeds its saved tables and PNG figures and preserves status and
assessment labels. It does not rerun notebook cells or campaigns.

The equations section checks all five primitives with deterministic vectors.
Work/runtime and cross-code sections keep each originating population and
measurement boundary separate. The native section displays historical author
agreement as an auxiliary diagnostic, alongside the status of fresh native
pairs. Tables show bounded previews with retained row counts; large values are
explicitly shortened and remain available in their linked source artifacts.

`scripts/phase4_notebook_support.py` matches manifest, executable source/policy,
ordered code, environment, sample, stage, caps and selection facts. It checks
current referenced bytes and sample namespaces. Snapshot/index digests bind
records; originating execution qualification is a separate producer obligation.
Mismatched/nonterminal evidence is preserved; new identity paths use exclusive
creation. Explicit producer callbacks require verified predecessor evidence
before invocation. Arbitrary notebook Python is trusted project code, not a
filesystem sandbox.

## Scientific limits and completion gates

All Phase 4 experiments are finite **CSS pilot adaptations**, with publication
assessment **not_assessed**. They do not reproduce Relay circuit curves, establish
a universal ranking or demonstrate quaternary behavior. Native agreement and
statistical performance checks supplement independent algebra and policy checks.
Quaternary decoding, circuit implementation, generic search and publication
campaign assessment stay with their owning later phases.

Plans 04-12, 04-13 and 04-14 cannot close until their production evidence and
verification gates pass. The executed fixture notebook verifies its plumbing;
its existence does not satisfy the complete Phase 4 notebook evidence contract.
