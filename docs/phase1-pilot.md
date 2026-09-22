# Phase 1 CSS tracer

Run the project-owned three-qubit CSS smoke fixture from the repository root:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.runner \
  data/manifests/project-three-qubit-fixture.json \
  --shot-id 0 --ledger /tmp/bp-three-qubit-events.jsonl
```

The fixture has `Hx=[[1,1,0]]`, `Hz=[[0,0,1]]`, and an X-only physical
error rate of zero for a deterministic native API smoke run. The manifest's
BPGD paper URI, v2 revision, and Figure 2 anchor establish methodological
context; **this project-owned code is not a code or curve from that paper**.
Its relation is `pilot_adaptation` and its expected-output status is
`not_assessed`. It is neither source-faithful reproduction nor the selected
publication-code pilot of Plan 09.

The JSONL file contains a `begin` event before sampling and one `terminal`
event for the identified `(run_id, shot_id)` pair. Each terminal event includes
the manifest SHA-256, source revision/anchor, Z-check syndrome, hidden X error
for independent evaluation, native candidate, `converge`/`iter` fields, and
one of the original-code outcome classes. Native edge-update counts are null
with an explicit missingness reason because `ldpc.BpDecoder` does not expose
them. The decoder receives only the check matrix, syndrome, prior, and BP
settings; hidden truth is used only by the evaluator and ledger.

`ldpc` is an external native SDK integration. The real adapter call is tested
by `tests/test_reference_smoke.py` and probed directly in
`docs/environment-pins.md`. Unsupported settings and malformed native
outputs raise explicit errors. A future selected-code pilot must pass its own
artifact, manifest, and source gates before any publication claim.
