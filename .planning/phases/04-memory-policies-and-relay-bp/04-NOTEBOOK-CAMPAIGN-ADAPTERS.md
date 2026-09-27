# Phase 4 notebook campaign adapter status

Status: **read-only adapters prepared; campaign evidence remains unqualified**

`scripts/phase4_notebook_campaign.py` exposes
`build_campaign_snapshots(root, development_fixture=False)` for the notebook.
It reads the retained Phase 4 baseline, benchmark, calibration, selected-settings,
evaluation, factorial, native, and trace paths without invoking a decoder,
subprocess, or scheduler. Each artifact remains separately indexed with its
producer path and byte digest, producer status, sample facts, normalized table
rows, and an `execution_qualified` decision.

Qualification is deliberately stricter than an artifact's terminal label. A
terminal producer must have a verifying canonical result digest plus bound
source-policy, code/manifest, frozen-cap, sample, and, for post-selection
stages, selected-settings bytes. Missing, running, interrupted, malformed, or
identity-mismatched records remain explicit unavailable or inconclusive
snapshots. The adapter never changes a sample namespace or copies a terminal
flag into its own proof.

The current historical author-agreement diagnostic is included only as
`historical_provenance_only`; it is never a substitute for fresh selected
evaluation or factorial evidence. Development fixtures are always returned as
`development_fixture_not_assessed` and cannot support a performance claim.

The frozen calibration and fresh evaluation results are still outstanding, so
the real campaign inventory presently contains no execution-qualified stages.
This is expected and does not prevent notebook construction or bounded fixture
rendering.

For the notebook-support layer, retain existing exact-cache confinement and add
only an adapter-facing identity mapping for campaign snapshots. The mapping must
preserve the adapter's producer-byte bindings and status; it must not turn an
adapter's unavailable state into a reusable terminal snapshot.
