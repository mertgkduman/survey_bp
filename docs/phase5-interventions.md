# Phase 5: guided and perturbative BP interventions

Phase 5 exposes one CSS code-capacity BP baseline and six separate, source-qualified intervention controllers through saved public manifests. The design is one baseline and six single-intervention arms. The primary sampled mechanism pilot uses the exact tracked B1 artifact at `p=0.07`. BB-144 and generated HGP are deterministic algebra and policy fixtures; they are not sampled comparison cohorts in this phase.

The B1 pilot is `pilot_adaptation` and `not_assessed`. Its finite 4-shot calibration and 16-shot evaluation are for mechanism inspection. No result here establishes published-curve agreement, source-faithful reproduction, decoder superiority, or an error-rate ranking.

The sealed `phase5-b1-p005-damping-pilot.json` and its
`b1-p005-damping-pilot` result directory predate the correction that makes V2C
damping retain the previous committed damped output. They are retained only as
invalidated historical evidence and must not be resumed or republished. The
sealed v1 builder remains unchanged, and its implementation-digest comparison
rejects the corrected source tree.

A corrected campaign must use a new v2 design and output namespace, including
`phase5-b1-p005-damping-pilot-v2.json`, `b1-p005-damping-pilot-v2`, v2 run IDs,
and new physical-sample and decoder identities. Its sealed equation must read
`v2c=(1-gamma)*previous_committed_damped+gamma*current_fresh`, with channel-prior
reset at every fresh attempt. This prevents public execution from discovering
or appending to any v1 ledger while preserving the old bytes for audit.

The current pilot uses the corrected work-receipt v2 execution. The earlier v1 pilot is retained in Git history at `5bdc3d9` as superseded development evidence: review found target/order and contradiction computations that preceded their work reservations. V2 keeps the original numerical caps and source variants while using new physical sample seeds, namespaces, and run identities; its four-shot calibration and cap freeze precede its evaluation. The older outcomes were not used to alter the ceilings.

## Public execution path

The stage design in `data/manifests/phase5-b1-calibration.json` has seven embedded complete `CanonicalExperimentV5` manifests. The stage runner saves each arm's individual manifest under its result directory before calling the public canonical path. Each V5 manifest projects to compact `CanonicalManifestV6`; its structural ledger uses version 5. Earlier public and compact schemas retain their historical meanings.

After the stage manifests exist, inspect an individual arm with:

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli preflight data/results/phase5-interventions/b1-mechanism-pilot/impulse/manifest.json
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli canonical data/results/phase5-interventions/b1-mechanism-pilot/impulse/manifest.json --output data/results/phase5-interventions/b1-mechanism-pilot/impulse
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-canonical-shot data/results/phase5-interventions/b1-mechanism-pilot/impulse/manifest.json data/results/phase5-interventions/b1-mechanism-pilot/impulse --shot 0
OMP_NUM_THREADS=1 .venv/bin/python -m bp_registry.cli verify-run data/results/phase5-interventions/b1-mechanism-pilot/impulse
```

For the matched pilot, first capture the effective scheduler entitlement, calibrate four purpose-separated physical samples, freeze the prespecified caps, and self-audit the seal. Evaluation refuses to run without that seal.

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase5_pilot.py --preflight-entitlement --calibrate --freeze-caps --self-audit
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase5_pilot.py --evaluate --require-cap-freeze docs/evidence/phase5-b1-cap-freeze.json --require-entitlement docs/evidence/phase5-compute-entitlement.json
OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase5_pilot.py --verify
```

The entitlement is in `docs/evidence/phase5-compute-entitlement.json`; the objective cap and manifest digest binding is in `docs/evidence/phase5-b1-cap-freeze.json`. Calibration and evaluation use different physical sample namespaces. Within a stage, each of the seven arms uses the same physical sample seed and identity for each shot. The baseline has no intervention; no arm combines two interventions. The fixed ceilings include 80 baseline sweeps, 16 BPGD rounds of at most 10 sweeps, 8 impulse attempts, 8 freezing retries, top-8 weight-one syndrome tests, a 16-action sign envelope within 80 sweeps, and Restart Belief `eta=8`, `t_cap=8`, and at most 10 sweeps per residual solve. Per-shot runtime and typed work caps are declared in each saved manifest.

## Decoder and evidence boundary

Controllers receive only the immutable original CSS problem, public syndrome, declared controls, and bounded work tree. Hidden physical X/Z truth is held by the runner until a selected original-space candidate is frozen. A candidate is eligible only after the original equation `H_Z x = s` holds; the independent evaluator then assigns one of five cells: `exact`, `stabilizer_equivalent`, `logical_failure`, `invalid_syndrome`, or `outcome_unavailable`. Undefined metrics remain unavailable rather than zero.

Each version-five structural shot binds manifest, artifact, sample, source variant, qualification, state/attempt rows, transform and lift facts, original checks, selection, evaluation, and terminal status. Typed work is the sum of unique committed leaf vectors. Denied, contradictory, invalid, cap-hit, unsuccessful, and no-proposal paths remain visible. `verify-canonical-shot` independently replays the controller and checks event order, candidate origin, original validation, outcome, and leaf work; rehashing a changed ledger claim does not make it valid.

The declared 300-second per-shot operational limit is checked at atomic-work boundaries. A deadline retains completed leaves, records the observed elapsed time and boundary in a `runtime` event, and emits a normal terminal row. One in-flight atomic operation may finish after the nominal threshold; its overshoot is recorded. Deadline shots do not enter truth-aware evaluation.

## Source qualifications and limits

The primary source-decision record is `docs/evidence/phase5-source-decisions.json`. Its per-arm anchors, revisions, native availability, unresolved details, and canonical identity control the claims below.

| Arm | Canonical qualification | Specific limit |
| --- | --- | --- |
| Guided decimation (BPGD) | `algorithm_interpretation` | Algorithm 1 v2 uses a finite prior magnitude of 25, an explicit positive-prior exact-zero rule, and returns after the last fixation. The source's exact-zero sign and possible extra final BP round remain unresolved; native identity is unverified. |
| Impulse | `controlled_css_adaptation` | The public arm uses exact fixed-one structural shortening and certified restoration. The paper's unchanged-graph negative-infinite-LLR trajectory is a separate semantic operator; its numerical equivalence to shortening and author-code identity are unverified. |
| Freezing | `controlled_css_adaptation` | A binary temporary-zero freeze and bounded seeded neighbor choice adapt a source quaternary identity-probability procedure. Native availability and source sampling equivalence are unverified. |
| Syndrome flip | `controlled_css_adaptation` | Oscillation counting follows the source all-zero initial hard decision. Canonical test order and seeded selection replace source unseeded/parallel arrival semantics. Only lifted candidates satisfying the original syndrome can be selected. |
| Sign flip | `bsfbp_sign_only_controlled_adaptation` | The public controller isolates a posterior sign action in normalized min-sum BP. It does not claim the source's compound branch-assisted pruning or native-code agreement. |
| Restart Belief | `mechanism_only_adaptation` | B1's distance bound 18–24 proves only `t>=8`. The B1 preset accepts a root-valid candidate only at weight at most 8 and branches from heavier roots. The paper's defect shortcut is unavailable because exact `t` and `xi` are undeclared. Fresh residual resets preserve only inserted-error state, so this remains a conservative mechanism adaptation rather than an exact-distance source run. |

Native comparisons marked `unverified` or `repository_revision_verified_in_phase_research` are not inferred to agree with canonical trajectories. Calibration may establish trigger availability and cost but cannot tune ceilings using logical outcomes. Evaluation cannot alter source qualification, tie rules, arm membership, or the frozen caps.

## Deterministic non-B1 fixtures

The tracked BB-144 and generated-HGP artifacts have fixed, nonzero syndromes and an independent GF(2) shortening/lift/original-check oracle. Compatible controllers have deterministic target and unique-leaf assertions. Restart Belief is explicit `unavailable` on these codes without an exact distance, and the B1-specific preset is incompatible.

```bash
OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/test_phase5_code_fixtures.py
OMP_NUM_THREADS=1 .venv/bin/python tools/validate_intervention_design.py --check
```

## Notebook and offline HTML

Plotly is pinned to the human-approved `plotly==7.1.0`, upstream `plotly/plotly.py` tag `v7.1.0` at commit `243bfd0fa5c0a5c29a185e4034a1ab5b111695a5`. It is confined to read-only charts and HTML export; it has no decoder, selection, evidence, or assessment role.

```bash
OMP_NUM_THREADS=1 .venv/bin/python scripts/execute_phase5_notebook.py --evidence data/results/phase5-interventions/b1-mechanism-pilot --output data/results/phase5-notebook/phase5-interventions.ipynb
OMP_NUM_THREADS=1 .venv/bin/python scripts/preview_phase5_notebook.py --executed data/results/phase5-notebook/phase5-interventions.ipynb --html data/results/phase5-notebook/phase5-interventions.html --check
OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_phase5_notebook.py
```

The notebook begins with a matched physical shot, highlights baseline plus one selected arm, and provides expandable rows for every attempt, including failure and no-proposal states. Baseline BP sweeps remain expandable but count as zero intervention attempts. One grouped Plotly legend toggles each arm across outcome, intervention-attempt-count, and typed-work panels. The standalone HTML embeds Plotly JavaScript and data for offline inspection; it supplies summary tables and confined links back to the complete ledger and executed notebook. Visibility controls change presentation only.
