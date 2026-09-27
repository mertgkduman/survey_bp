# Phase 4 shared-memory evaluation preparation

Status: **prepared contract only; no amendment is published and no production
qualification exists.**

`scripts/phase4_shared_evaluation.py` supplies the bounded, pure preparation
contract for a later shared-settings CSS evaluation.  It does not change
`data/manifests/phase4-pilot-caps.json`, the active calibration plan, any
sample namespace, retained evidence, or campaign output.  It cannot invoke a
decoder, scheduler, or native reference.

## Supported preparation API

`run_phase4_evaluation.build_shared_evaluation_supplement(...)` returns a
versioned `phase4-shared-memory-evaluation-supplement` object.  The caller
must supply a positive finite per-code count and a separate positive finite
supplemental wall ceiling.  The object is deliberately marked
`prepared_not_published_no_sampling` and `no_production_side_effects: true`.
It binds exact cap and selected-settings bytes/digests, deterministic shared
calibration selection, each code's error rate/work/boundary, and the two
allowed arms:

- `shared_source_procedure`: the source-procedure min-sum kernel;
- `shared_canonical_procedure`: the canonical-default SPA kernel.

Both arms use the same selected candidate and its digest-bound memory tuning,
the same per-code evaluation sample namespace, and the same finite work,
count, and timing boundary.  That namespace remains distinct from the
calibration, native, and benchmark namespaces.  The legacy V4 three-arm plan
remains byte-compatible and is not made a 14-arm factorial prerequisite.

`run_phase4_evaluation.build_shared_manifest(...)` materializes a declared
shared cell for manifest validation only.  It rejects a changed cap or
selection byte identity, changed source setting, unrecognized arm, candidate
or namespace drift, inconsistent paired tuning, category overcommit, duplicate
cells, and ineligible/inconclusive selections.  It labels the manifest as
unpublished and unauthorized for sampling.

## Required continuation gate

Before either legacy selection freezing or a supplemental contract is derived,
the runner calls `verify_phase4_calibration.audit_terminal`.  That audit
requires complete frozen-surface/configuration/shot coverage, terminal result
and amendment/cap bindings, per-attempt receipts/sample identities/work
limits, reconstructed aggregates, and retained category accounting.  Its
scope is explicitly surface integrity; canonical-ledger replay remains a
separate verification requirement.

A future implementation would need an explicit reviewed publication decision
that reserves a supplemental allocation and adds a new production executor.
Neither is included here.  The active calibration is currently not an audited
terminal production result, so this preparation has no authorization to
generate fresh samples or support a performance, source-faithfulness, timing,
native-agreement, reproduction, or ranking claim.
