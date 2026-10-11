# Bounded campaign evidence

Phase 8 campaigns separate frozen scientific work from observations about how
that work was delivered. They produce reproducible development evidence. They
do not establish a source reproduction, a decoder ranking, or an authorization
to start a publication campaign.

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
bp-registry-campaign assess --merge <merge-root>/campaign-merge.json
```

All receipt publication is immutable. Re-running a sealed shard into its
existing destination is an error. Merge accepts exactly one frozen identity and
unique unit keys. Resume reconstructs the exact missing set from preserved
receipts; it never guesses work from a scheduler array index.

The same frozen unit may be delivered through the bounded Slurm route. It
emits literal `sbatch` argv and accepts only a precomputed array index. The
synthetic harness is the normal Phase 8 equivalence check. A real array is
attempted only after `site-capability` reports actual safe defaults. The Phase
8 operational receipt records unavailable capability facts rather than filling
them with guessed values.

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
