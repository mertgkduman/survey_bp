# Bounded campaign evidence

Phase 8 campaigns separate frozen scientific work from observations about how
that work was delivered. They produce reproducible development evidence. They
do not establish a source reproduction, a decoder ranking, or an authorization
to start a publication campaign.

## Paired BB-144 canonical gate

`data/studies/phase8-paired-canonical-gate-v1.json` is the retained real
two-arm definition. It binds the `phase8-paired-bb144-fast.json` baseline and
the `phase8-paired-bb144-slow.json` relay policy to the same selected BB-144
artifact, CSS code-capacity channel, `p=0.05`, sampler seed `317`, physical
sample namespace, and sample IDs `0` and `1`. The fast and slow arms retain
different decoder-seed identities. One evaluator-owned physical error artifact
is sampled once for each point/sample and replayed through both policies.

The canonical event ledger fields and sampler-derived identity do not change
for the campaign. A separate campaign attempt receipt binds each immutable
canonical ledger, materialized sample, and realized-error hash before merge.
The four resulting units are bounded development evidence: the all-domain
`development_fixture-not_assessed-all-domain` target is explicitly
`development_fixture` / `not_assessed`, so it supplies no paper-reproduction
or decoder-superiority verdict.

The historical `phase8-bb144-fast.json` / `phase8-bb144-slow.json` pair is
synthetic transport and recovery evidence only. Its one-shot inputs use
different rates (`0.05` and `0.03`) and are never described as matched decoder evidence.

Preflight validates the exact manifest bytes, shared code/channel/sampler
material, resource caps, and frozen work expansion without creating an output
directory, physical sample, canonical event ledger, or result receipt:

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign preflight \
  --campaign data/studies/phase8-paired-canonical-gate-v1.json \
  --campaign-root . \
  --output-root data/results/phase8-paired-canonical-gate-v1
```

After that no-write check, freeze the immutable work artifact before sampling:

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign plan \
  --campaign data/studies/phase8-paired-canonical-gate-v1.json \
  --campaign-root . \
  --output-root data/results/phase8-paired-canonical-gate-v1
```

The paired command writes
`data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json`.
It reconstructs exactly two samples by two arms; it does not authorize a
larger shard, sample, evidence, storage, or decoder-work allocation.

Run the retained local route, verify its typed paired-run receipt, merge it,
derive only any exact resume set, and publish the bounded assessment:

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign run-local \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --campaign-root . --output-root <local-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify \
  --receipt <local-root>/paired-run.json \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign merge \
  --receipt <local-root>/paired-run.json \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --campaign-root . --output-root <merge-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign resume \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --merge <merge-root>/campaign-paired-merge.json --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign assess \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --merge <merge-root>/campaign-paired-merge.json --campaign-root . \
  --output-root <assessment-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify \
  --report <assessment-root>/assessment.json \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --merge <merge-root>/campaign-paired-merge.json --campaign-root .
```

The selected Slurm route is a transport route for frozen shards. First record
measured site capability and retain bounded allocation and scheduler-observation
receipts; then emit the literal array command and run only its selected shard:

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign site-capability \
  --scontrol <scontrol-observation.json> --sacct <sacct-observation.txt>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign emit-slurm \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --campaign-root . --allocation <bounded-allocation.json> \
  --site-allowlists <measured-site-allowlists.json>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign run-shard \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --campaign-root . --output-root <slurm-root> --array-task-id <frozen-index> \
  --allocation <bounded-allocation.json> \
  --scheduler-observation <scheduler-observation.json>
```

No real scheduler submission is authorized without measured site ceilings for
wall time, CPU, memory, storage, replay, and scheduler cost. Unavailable
observations remain explicit unavailable facts. After both routes have retained
their independently verified merge and report chains, compare only their
route-neutral scientific evidence:

The retained `phase8-paired-canonical-gate-v1/slurm-route` evidence ran frozen
array indexes `0` and `1` directly through `run-shard`; no `sbatch` job was
submitted. Its `direct-observation-*.json` files are harness inputs. The
`allocated_cpus: 1` field is a declared request, and the zero elapsed and
overhead fields are placeholders, not scheduler measurements. Slurm accounting
is explicitly unavailable. Actual child-process wall and peak RSS measurements
and cumulative peak child RSS upper bounds are in
`shard-*-resource-measurement.json`. These measurements size only this
bounded development run; the production profiling gate remains denied until
site ceilings and accounting are measured.

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify-routes \
  --plan data/results/phase8-paired-canonical-gate-v1/campaign-work-plan.json \
  --local-merge <local-merge>/campaign-paired-merge.json \
  --local-report <local-assessment>/assessment.json \
  --slurm-merge <slurm-merge>/campaign-paired-merge.json \
  --slurm-report <slurm-assessment>/assessment.json \
  --campaign-root . --output <route-equivalence.json>
```

## Frozen inputs and identity

`data/studies/phase8-operational-gate-v1.json` is the retained Phase 8 gate.
It is labelled `development_fixture` and `not_assessed`. Its primary one-unit
campaign binds the fast BB-144 manifest, source/environment locks, exact
interval rule, all-terminal outcome matrix, and fixed-shot assessment. Its
`operational_gate` metadata separately binds the two eligible canonical
manifests, their SHA-256 values, a shared physical-sample namespace, and the
preselected IDs `0` and `1`.

The shared physical sample identity never incorporates a policy or worker
label. Decoder seed identities are arm scoped. This allows matched physical
errors while keeping decoder randomness separate. `preflight` checks each
manifest and every stated SHA-256 before it creates an output directory:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.campaigns.cli preflight \
  --campaign data/studies/phase8-operational-gate-v1.json \
  --campaign-root . \
  --output-root data/results/phase8-operational-gate-v1
```

The phase gate is deliberately small: at most two preselected samples across
the fast and slow paths, one CPU per task, one concurrent task, a five-minute
candidate wall ceiling only when the site has supplied safe defaults, and
bounded evidence/storage caps. Those candidate allocation values are not site
facts. Absent site ceilings remain unavailable and deny production dispatch.

## Lifecycle and immutable receipts

For the primary tracer, plan before any execution, run a frozen unit, verify
its shard, merge it, reconstruct the all-shot result, and resume only from the
preserved merge receipt:

```bash
bp-registry-campaign plan --campaign data/studies/phase8-operational-gate-v1.json --campaign-root . --output-root <plan-root>
bp-registry-campaign run-local --plan <plan-root>/campaign-plan.json --campaign-root . --output-root <local-root>
bp-registry-campaign verify --receipt <local-root>/shard-*/receipt.json --campaign-root .
bp-registry-campaign merge --receipt <local-root>/shard-*/receipt.json --campaign-root . --output-root <merge-root>
bp-registry-campaign resume --plan <plan-root>/campaign-plan.json --merge <merge-root>/campaign-merge.json --campaign-root .
bp-registry-campaign assess --merge <merge-root>/campaign-merge.json --campaign-root .
```

All receipt publication is immutable. Re-running a sealed shard into its
existing destination is an error. Merge accepts exactly one frozen identity and
unique unit keys, and records a canonical content SHA-256. Both resume and
assessment re-verify every listed shard and require the merge JSON bytes and
content hash to equal their canonical reconstruction. Resume
reconstructs the exact missing set from preserved receipts; it never guesses
work from a scheduler array index. The one-unit tracer reducer rejects an
assessment declaring more than one fixed shot rather than reporting a partial
receipt as complete.

The same frozen unit may be delivered through the bounded Slurm route. It
emits literal `sbatch` argv and accepts only a precomputed array index. The
synthetic harness is the normal Phase 8 equivalence check. A real array is
attempted only after `site-capability` reports actual safe defaults. The Phase
8 operational receipt records unavailable capability facts rather than filling
them with guessed values. A positive accounting capability requires a bounded
`sacct --parsable2` observation with `JobIDRaw|State|Elapsed|AllocCPUS` header
and at least one well-formed row; blank or malformed text remains explicitly
unavailable. Profile-gate measurements and limits must be finite numeric JSON
values, never booleans or non-finite literals.

## Stopping, outcomes, and reports

Fixed-shot evidence uses exact Clopper-Pearson intervals and an explicit
all-shot outcome map. `exact` and `stabilizer_equivalent` are successes;
wrong logical actions and invalid/no-proposal/nonconvergence/timeout outcomes
are all-shot failures; infrastructure interruption is incomplete. Conditional
denominators retain excluded outcomes explicitly.

The bounded synthetic matched-arm fixture exercises the paired family and the
finite-look route. Its deterministic fault is injected after a complete look
has been assessed and before the atomic stop receipt is published. Resume must
reconstruct and publish that receipt before it subtracts any unit from the next
look. This local finite-look controller seals a separate per-look merge receipt
from its unit receipts before assessing the stop. The retained proof records
the authorized undispatched tail, zero next-look submission, and byte-identical
pre-crash unit and local merge evidence. The legacy single-unit CLI merge uses
a different receipt format; it does not consume this local merge receipt.

Reports reconstruct claims from terminal receipts and their hashes. Target
references retain a source byte digest, its uncertainty and precision, and an
explicit source denominator status. A zero failure count is a measured count
with an exact interval, not evidence that a failure rate is zero.

## Profiling and authorization

Representative profiling records decoder and replay throughput, ledger and
sidecar bytes, scheduler overhead, and memory availability. Each profile pair
must be pre-outcome, semantically equal on the scientific facts, and linked to
verified shard, merge, and replay receipts. The authorization receipt applies a
frozen rational safety factor to measured costs and binds every supporting
digest.

An authorization is `deny` whenever a required observation or any site ceiling
is unavailable or exceeded. This is the expected Phase 8 result until a site
provides explicit wall-time, CPU, memory, storage, replay, and scheduler cost
ceilings. A denial keeps the bounded gate evidence; it does not prevent normal
development tests or synthetic scheduler equivalence checks.
