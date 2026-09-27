# Phase 4 focused factorial preparation status

Status: **prepared; production sampling blocked**

`scripts/run_phase4_factorial.py` expands the frozen focused design into 882
identified cells: 14 arms × three fixed noise regions × three CSS codes × seven
matched shots. It does not invoke the canonical CLI, native adapter, scheduler,
or any decoder kernel. Each cohort at one code/rate/shot has one derived
physical-sample identity shared by all 14 arms; decoder randomness remains
arm-specific.

The companion [execution supplement](../../../data/evidence/phase4-factorial-execution-supplement-v1.json)
is a versioned, digest-checked, outcome-independent binding of the frozen design
and active-V4 caps. It preserves the original design arrays and records the
necessary executable order: affine prior, field transformations, V2C damping,
then posterior momentum. In particular, it does not silently rewrite the frozen
`v2c-damping-plus-ewa` or `momentum-plus-ewa` declaration arrays; both the frozen
array and effective order are retained per cell.

The runner refuses production sampling until a retained fresh evaluation:

- has `status: completed` for BB-144, B1, and generated HGP;
- binds the exact design/cap/supplement digests; and
- explicitly admits every one of the 14 factorial arms.

This gate is deliberately not met. The frozen active-V4 evaluation cap admits
only `baseline`, `selected_source_procedure`, and
`selected_canonical_procedure`; it does not admit the remaining 11 focused
ordinary-memory/Relay arms. Calibration/evaluation evidence also remains
outstanding. No cap or frozen design was changed to conceal this gap.

One additional execution gap remains explicit: the planned ordinary
`disordered-affine-prior` arm has a fixed coefficient/assignment declaration,
but public ordinary disordered-prior execution is still rejected by the current
engine. The preparatory plan retains its seven shots per code/rate, marks it
`execution_ready: false`, and refuses production execution until that declared
assignment is implemented and verified.

Development fixtures can exercise the runner only if they state both
`development_fixture: true` and `assessment: not_assessed`. Fixture results stay
`development_fixture_not_assessed`; they cannot authorize sampling or support a
performance claim.

When the coordinated trace implementation lands, ordinary-memory callers use
`MemoryFloodingSchedule(..., trace_sink=..., trace_context=...)`, call
`observe_candidate(origin, candidate)` after committed work, then call
`trace_result()` and retain its sidecar as a `trace_link` ledger event. The
sidecar is bounded by the frozen per-code byte, record, and shot caps and records
only decoder-visible beliefs, history digests/shapes, assignment evidence,
candidate origin, transitions, and raw work. No hidden physical truth is traced.

The planned result contract retains all five mutually exclusive proposal outcome
cells (`proposed_selected`, `proposed_unselected`, `no_proposal`,
`terminal_failure`, `terminal_incomplete`), candidate origins, terminal-derived
raw per-leg/total work, runtime/resource tails, and explicit resource missingness.
It does not form a heterogeneous scalar cost. Any eventual evidence remains a
CSS pilot adaptation and `not_assessed`, with no circuit-reproduction or
universal-ranking claim.
