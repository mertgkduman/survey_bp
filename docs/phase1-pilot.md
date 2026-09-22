# Phase 1 selected CSS pilot

The selected command runs the Plan 08 verified Gross/BB-144 artifact through
one native `ldpc.BpDecoder` configuration: X-only code-capacity noise at
`p=0.01`, product-sum updates, parallel schedule, maximum 30 iterations, and
one OpenMP thread. It fixes 32 identified shots through a manifest-derived
seed policy.

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight \
  data/manifests/selected-css-pilot_adaptation-not_assessed.json
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli pilot \
  data/manifests/selected-css-pilot_adaptation-not_assessed.json \
  --output data/results/pilot_adaptation-not_assessed
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run \
  data/results/pilot_adaptation-not_assessed
```

The manifest binds the source revision, source-file SHA-256, frozen matrix and
logical hashes, package versions, decoder settings, and finite budget before a
native call. Flags cannot replace those scientific fields. The command rejects
another BB artifact, source revision, environment, or decoder API contract.

## Project-owned three-qubit tracer fixture

The original Phase 1 local tracer command is retained as a one-shot smoke
fixture with a complete current manifest. It verifies the project-owned
three-qubit CSS artifact, current environment, and native BP boundary before
writing a begin and terminal event:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.runner \
  data/manifests/project-three-qubit-fixture.json \
  --ledger /tmp/project-three-qubit-fixture-events.jsonl
```

The fixture is a `pilot_adaptation` with `not_assessed` output. Its linked
paper gives only bit-flip methodological context; the code, logical basis,
and one-shot budget are project-owned test data. It is neither a paper result
nor a source-faithful reproduction.

Every displayed surface calls this a **pilot_adaptation** and
**not_assessed**. The ledger and result preserve successful, nonconverged,
invalid-syndrome, interrupted, and unavailable-outcome rows. `result.json`
rebuilds denominators only from final ledger rows; rerunning fills only missing
shot IDs and never double-counts final rows.

This is a local execution smoke pilot. It is not source-faithful reproduction,
does not use the source impulse method, does not use OSD, and makes no curve
pass or statistical-reproduction claim. The linked paper experiment remains
`mapped_only` until later source-faithful qualification and assessment.
