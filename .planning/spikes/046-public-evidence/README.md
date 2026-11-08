---
spike: 046
idea: canonical-kernel-audit
name: public-evidence
type: standard
validates: "New public execution results remain bound to valid execution-dtype values and replayable evidence."
verdict: PARTIAL
related: [037, 042, 043, 045]
tags: [evidence, readiness]
---

# Evidence and practical public use

Regrounded in MANIFEST.md and CONVENTIONS.md after 045. Preserve all previous
hardware qualification and publication gates. This audit adds no GPU timing and
does not initiate a literature reproduction campaign or release packaging.

## Approach

Test normal circuit export/replay, immutable outputs and exclusive publication.
Probe direct public result construction across execution-dtype conversion using
an internally content-bound ledger, then verify that independent decoder replay
still rejects invalid records. A content digest is not an authenticity signature;
the concern is constructor consistency, not resistance to a malicious author.

Revalidate current source hashes against the previous H200 receipt, validate its
stored ledgers and public GPU result bindings on CPU, and preserve separate
decode/JIT/export timing scopes. Run focused existing circuit and evidence tests;
reuse the full regression receipt because production source has not changed.

## Run

`OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/046-public-evidence/probe.py`

`OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/circuit tests/canonical/test_batch_evidence.py`

Detailed counterexamples and hashes are retained. Exit success of the diagnostic
probe is distinct from its invariant verdicts.

## Results and investigation trail

Normal circuit export/replay, exclusive publication, immutable result columns and
stale-evidence rejection pass. The focused regression suite passes 120 tests in
6.74 seconds, including the Sinter worker path.

**E03:** CircuitBatchResult compares incoming values with its ledger before
converting them to execution dtypes. Five directly constructed invalid results
are admitted: fault/prediction 256 becomes uint8 zero, convergence 2 becomes true,
iteration 1.5 becomes integer 1, and iteration -1 remains invalid. Four then
disagree with their bound ledgers. All five exported examples are rejected by
independent decoder replay. Generated decode results were not observed to take
this path; this is a public construction/import guard gap. Validate ranks,
binary values, boolean convergence and nonnegative integral work before binding
immutable normalized state. Do not change valid decoder outputs.

The prior hardware source hashes still match. All four 1,024-shot GPU ledgers
pass fresh content/result binding checks on CPU, including execution-dtype
rejection controls. Their H200 runs and CPU replay are carried evidence, not new
execution. The existing 2,285-pass full suite and 20-pass H200 qualification remain
separate receipts. Warm decode speedups exclude JSON export, which can dominate
these small millisecond GPU batches. No universal end-to-end speedup is inferred.

Two invariant groups pass; the public result admission group fails.
