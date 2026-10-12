# Bounded campaign evidence

## Phase 9 local failure-count campaigns

A failure-count document has one top-level `failure_count_work_spec` containing
the prospective `campaign_work_spec` and `policy`. It freezes one arm, one
target, ordered sample IDs, a target failure count, a whole-batch size, the
inverse-binomial procedure, independently derived executable limits, and
finite shot, work, event, evidence, storage, and wall caps. The policy's
`campaign_plan_sha256` is the acyclic binding returned by
`failure_count_plan_binding(CampaignWorkSpecV1.model_validate(campaign_work_spec))`;
set that value in both policy copies before `plan`. The plan contains no
observed failure count, stopping ordinal, interval, or verdict.

The local commands run one next bounded batch at a time. `run-local` returns
the preserved `receipt_path`; pass that path to `merge`. Use a fresh merge
output directory for each progress snapshot because merge receipts are
immutable. `resume` reports the exact next missing ordinal. Repeat the run,
merge, and resume steps until the state is `target_reached` or `cap_censored`.

```bash
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign preflight \
  --campaign <failure-count-document.json> --campaign-root . --output-root <run-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign plan \
  --campaign <failure-count-document.json> --campaign-root . --output-root <plan-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign run-local \
  --plan <plan-root>/failure-count-plan.json --campaign-root . --output-root <run-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign merge \
  --receipt <receipt_path-returned-by-run-local> \
  --plan <plan-root>/failure-count-plan.json --campaign-root . --output-root <merge-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign resume \
  --plan <plan-root>/failure-count-plan.json \
  --merge <merge-root>/failure-count-merge.json --campaign-root .
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign assess \
  --plan <plan-root>/failure-count-plan.json \
  --merge <merge-root>/failure-count-merge.json --campaign-root . \
  --output-root <assessment-root>
OMP_NUM_THREADS=1 .venv/bin/bp-registry-campaign verify \
  --report <assessment-root>/failure-count-assessment.json \
  --plan <plan-root>/failure-count-plan.json \
  --merge <merge-root>/failure-count-merge.json --campaign-root .
```

The verified target receipt identifies `T_r`, the exact ordinal of the
target-th logical failure. Inference uses only the ordered prefix through
`T_r`; later shots completed in that terminal batch are authorized tail and
remain in total work, runtime, and resource costs. A cap-censored receipt has
no inverse-binomial interval or source-agreement verdict. A partial attempt
has zero completed-shot and failure credit; its consumed resources and pending
ordinal remain visible. Publication Slurm dispatch for this route remains
denied until site ceilings are measured.

## Phase 9 ordered controlled campaigns

An ordered document has one top-level `ordered_campaign_work_spec` with a
validated `campaign_work_spec` and `execution_order`. Its `arm_order` lists
every arm exactly once. `plan` freezes coordinate, sample-group, and unit
ordinals in that order; changing the declaration changes the plan digest.
This route accepts fixed-shot or finite-look work and runs locally only.

```bash
bp-registry-campaign plan --campaign <ordered-document.json> --campaign-root . --output-root <plan-root>
bp-registry-campaign run-local --plan <plan-root>/campaign-ordered-plan.json --campaign-root . --output-root <run-root> --max-units 1
bp-registry-campaign merge --plan <plan-root>/campaign-ordered-plan.json --receipt <run-root>/ordered-run-00000001-00000001.json --campaign-root . --output-root <partial-merge-root>
bp-registry-campaign resume --plan <plan-root>/campaign-ordered-plan.json --merge <partial-merge-root>/campaign-ordered-merge.json --campaign-root .
```

Repeat `run-local` in the same run root to execute the exact remaining unit
prefix; pass all returned ordered run receipts to a fresh `merge` directory.
Partial merge and `verify --receipt ... --merge ...` report the exact missing
units and groups, including a group with one completed arm. `assess` requires
every frozen group to be complete. Then use `verify --report ... --merge ...`
to replay the terminal report. The route carries a publication Slurm denial.

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

The two `local-failed-*-mapping` directories retain incomplete implementation
diagnostics from before the campaign terminal mappings were repaired. Each
contains a `diagnostic.json` with `scientific_denominator_contribution: false`;
neither enters the verified merge or assessment.

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

## Phase 9 measured controlled design

`data/studies/phase9-controlled-design-v2.json` freezes three separate matched
CSS comparisons before any evaluative sample: B1 SPA flooding versus SPA
check-node serial at p=0.10, BB72 initial BP versus Relay and initial BP versus Beam in one Holm family
at p=0.08, and B1 MBBP list selection versus coordinate vote at p=0.000001.
The bounded local denominators are respectively 3, 16, and 2 complete pairs.
They are exploratory. Exact paired McNemar sizing with a 0.05 relevant
all-shot risk difference, one contrast for schedule and MBBP and two
prespecified baseline contrasts for Relay/Beam, and an explicit worst-case
discordance assumption q=1 requires 3,143 pairs for the one-contrast families
and 3,820 for the two-contrast family to reach 80% power.
The q=1 input is a conservative planning assumption; the one-shot calibration
runs cannot estimate discordance.

Each mechanism has a separate immutable profile receipt under
`data/results/phase9-control-profiles-v1/`. Beam and Relay retain distinct
inner runtime and work, while their full matched process wall, CPU, memory,
and storage serve as conservative shared-process bounds. MBBP work comes from
the two verified member-work ledgers; the two decision arms share one member
set per evaluative sample. The schedule profiles are fresh runs from the
tracked Phase 3 manifests: the older Phase 3 run ledgers did not pass the
current manifest digest verifier, so those old results are not used as verified
cost receipts. Schedule calibration used p=0.03 and is projected to p=0.10
with a twofold cost factor and a small local cap.

Every family has a public `OrderedCampaignWorkSpecV1` plan under
`data/results/phase9-controlled-design-v1/` or its version-two successor,
with a complete declared arm sequence and sample-major group ordinals.
The public `plan`, `run-local`, `merge`, `resume`, `assess`, and `verify`
commands execute the frozen schedule pair, the shared-initial BP/Relay/Beam
family, and the shared-member MBBP list/vote family. A partial merge retains
completed arms, reports the exact missing set, and cannot be assessed.
`run-local` returns `run_envelope_paths` for every sealed segment to pass as
`--receipt` inputs to `merge`. If execution stops after a unit seals but before
its envelope is published, the next `run-local` call verifies that prefix and
publishes the missing envelope without repeating the unit. Recoverable
dispatch errors retain numbered interruption receipts without exception text.
Relay and Beam consume one sealed initial BP state per sample; list and vote
consume one sealed MBBP member set. Shared work is charged once in the typed
cost projection. Complete matched groups alone enter paired inference and the
declared Holm family. No calibration sample may enter the evaluative
denominator. Site wall, core, memory, storage, and accounting ceilings remain
unavailable, and publication Slurm authorization is denied.

## Phase 9 Yao B1 bounded adaptation

`data/studies/phase9-yao-b1-t001-p010-v4.json` is the current frozen local
campaign for the project B1 artifact, Yao Figure 3 `bpgd-t001` at p=0.10.
It targets 100 logical failures under a 95% exact inverse-binomial rule and a
separately frozen factor 1.5 comparison to the published rate. The profile
gate and source target are digest-bound. The execution uses one local worker,
an 1,800 second campaign wall cap, and an explicit 4 MiB ceiling for each
guided-decimation event. Publication Slurm authorization remains denied.

The v1 run reached its 600 second wall cap without a completed shot and
retains a sealed zero-credit partial. The v2 and v3 attempts encountered
guarded event-size limits before a terminal shot; their unsealed ledgers are
diagnostic evidence with no shot or failure credit. The first v4 attempt
completed a canonical `wall_clock_deadline` terminal, but the campaign adapter
rejected that outcome before sealing its shot receipt. Its full ledger is
retained as diagnostic evidence, without campaign credit. The adapter now
maps that exact canonical terminal to the frozen `timeout` class, and a fresh
run under the unchanged v4 scientific plan records a new execution observation.
The later versions have new study and manifest identities only where their
executable bounds changed. These failed attempts cannot enter inverse-binomial
inference. The credited v4 run sealed two timeout terminals and reached the
1,800 second campaign wall cap before the target of 100 failures. Its report is
`inconclusive_cap_censored`: no inverse-binomial rate, interval, or paper-target
verdict is computed. The two terminal attempts retained 3,591 events,
9,470,745 decoder work units, 12,596,648 evidence bytes, and 2,104,202,730,786
nanoseconds of measured wall boundaries. The frozen all-shot matrix counts
both timeout terminals as decoder failures; this is not an observed
paper-style logical error rate. Every result remains a `canonical_adaptation`:
the original source settings and exact paper artifact have not been established.
