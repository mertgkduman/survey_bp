# Phase 4 notebook campaign adapter status

Status: **read-only adapters prepared; campaign evidence remains unqualified**

`scripts/phase4_notebook_campaign.py` exposes
`build_campaign_snapshots(root, development_fixture=False)` for the notebook.
It reads the retained Phase 4 baseline, benchmark, calibration, selected-settings,
evaluation, factorial, native, and trace paths without invoking a decoder,
subprocess, or scheduler. Each artifact remains separately indexed with its
producer path and byte digest, producer status, sample facts, normalized table
rows, and an `execution_qualified` decision.

Qualification is deliberately stricter than an artifact's terminal label. The
adapter calls the producer's stage-specific readers: calibration uses its
frozen caps byte SHA, calibration-plan/input, terminal result digest, and
evaluation-namespace guard; selection and post-selection stages additionally
use the producer's deterministic selected-settings and three-arm evaluation
plan checks. Evaluation and factorial records remain unavailable until their
durable terminal ledgers are independently replayed; this read-only adapter
does not invoke a simulation or a subprocess verifier. Missing, running,
interrupted, malformed, or identity-mismatched records remain explicit
unavailable or inconclusive snapshots. The adapter never changes a sample
namespace or copies a terminal flag into its own proof.

The reader imports producer validators from the analysis worktree, while its
`campaign_root` supplies only retained data and ledgers. Completed V4 Relay
shots are reconstructed through their persisted manifest, public context, and
ledger rather than by rerunning a decoder. Future factorial terminals retain
their manifest and ledger paths plus manifest byte digest so this reconstruction
can bind each outcome to its originating execution. Calibration tables retain
the configuration identity as well as preset, preventing distinct tuned
configurations from being conflated in a plotted arm label.

The current historical author-agreement diagnostic is included only as
`historical_provenance_only`; it is never a substitute for fresh selected
evaluation or factorial evidence. Development fixtures are always returned as
`development_fixture_not_assessed` and cannot support a performance claim.

The frozen calibration and fresh evaluation results are still outstanding, so
the real campaign inventory presently contains no execution-qualified stages.
Benchmark and author-agreement metadata can still be displayed with their
historical diagnostic scope. This does not prevent notebook construction or
bounded fixture rendering.

For the notebook-support layer, retain existing exact-cache confinement and add
only an adapter-facing identity mapping for campaign snapshots. The mapping must
preserve the adapter's producer-byte bindings and status; it must not turn an
adapter's unavailable state into a reusable terminal snapshot.
