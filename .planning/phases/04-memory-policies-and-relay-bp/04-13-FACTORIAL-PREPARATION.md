# Phase 4 focused factorial preparation status

Status: **prepared; production sampling blocked**

`scripts/run_phase4_factorial.py` expands the frozen focused design into 882
identified cells: 14 arms × three fixed noise regions × three CSS codes × seven
matched shots. Its default preparation command does not invoke the canonical
CLI, native adapter, scheduler, or any decoder kernel. The explicit production
executor remains gated and uses the public canonical commands only after the
fresh evaluation predecessor verifies. Each cohort at one code/rate/shot has
one derived physical-sample identity shared by all 14 arms; decoder randomness
remains arm-specific.

The companion [execution supplement](../../../data/evidence/phase4-factorial-execution-supplement-v1.json)
is a versioned, digest-checked, outcome-independent binding of the frozen design
and active-V4 caps. It preserves the original design arrays and records the
necessary executable order: affine prior, field transformations including
posterior momentum, then V2C damping. In particular, it does not silently rewrite the frozen
`v2c-damping-plus-ewa` or `momentum-plus-ewa` declaration arrays; both the frozen
array and effective order are retained per cell.

The runner refuses production sampling until a retained fresh evaluation:

- has `status: completed` for BB-144, B1, and generated HGP;
- binds the exact design/cap/supplement digests; and
- completes its separately frozen three-arm baseline/source/canonical cohort.

For a genuine predecessor, its nonempty canonical evaluation-plan and
selected-settings digests must also match the retained three-arm evaluation
plan whenever `selected-settings.json` is present. This verifies calibration
provenance without asking evaluation to admit the distinct 14-arm factorial.

This gate is deliberately not met because calibration/evaluation evidence is
outstanding. The frozen active-V4 evaluation cap legitimately admits only
`baseline`, `selected_source_procedure`, and `selected_canonical_procedure`.
The distinct frozen factorial category admits all 14 focused arms after that
predecessor completes; no cap or frozen design was changed.

The public ordinary disordered-prior form is now the declared fresh uniform
per-source-iteration PCG64 assignment on `[0, 1]`, bound to an arm-specific
decoder seed. Its frozen design label is retained as an alias for executable
`affine_prior`. The runner now declares its public V4 `trace_plan` using the
existing confined sidecar contract. It selects only the deterministic
`visible_bp_failures` shot 0 from every arm before outcomes, stores every
observed ledger link and truncation fact, and retains unavailable Relay/native
trace evidence as missingness. The coordinated public V4 ON/OFF, disordered
assignment, and cap-truncation checks have passed. This confirms only the
execution contract; calibration/evaluation evidence still blocks scientific
sampling.

The fourteen selected arm traces per code are within the frozen per-code
`trace_caps.max_shots` limit of 32. Record and byte caps are aggregate per
code, so the runner assigns each selected manifest an equal floor share and
checks the retained inventory total. The separate frozen `fixture_shots_per_code`
allocation remains seven and is not consumed by these existing factorial shot-0
executions. Each production cell has one 900-second-or-less deadline shared by
preflight, observation, canonical execution, and verification; each command
receives only the remaining time. Actual wall duration is retained while RSS
remains explicit missingness when unavailable.

Development fixtures can exercise the runner only if they state both
`development_fixture: true` and `assessment: not_assessed`. Fixture results stay
`development_fixture_not_assessed`; they cannot authorize sampling or support a
performance claim.

For an enabled flooding-memory shot, the public engine uses
`MemoryFloodingSchedule(..., trace_sink=..., trace_context=...)`, call
`observe_candidate(origin, candidate)` after committed work, then call
`trace_result()` and retain its sidecar as a `trace_link` ledger event. The
sidecar is bounded by the frozen per-code byte, record, and shot caps and records
only decoder-visible beliefs, history digests/shapes, assignment evidence,
candidate origin, transitions, and raw work. No hidden physical truth is traced.

The planned result contract retains the five mutually exclusive proposal outcome
cells (`valid_correct`, `valid_wrong_logical`, `invalid_correct`,
`invalid_wrong_logical`, `no_proposal`), candidate origins, terminal-derived
raw per-leg/total work, runtime/resource tails, and explicit resource missingness.
Command failure and incomplete execution remain separate `execution_status`
facts and do not masquerade as `no_proposal`. It does not form a heterogeneous scalar cost. Any eventual evidence remains a
CSS pilot adaptation and `not_assessed`, with no circuit-reproduction or
universal-ranking claim.
