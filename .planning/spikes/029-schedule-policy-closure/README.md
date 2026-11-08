---
spike: 029
idea: canonical-kernel-audit
name: schedule-policy-closure
type: standard
validates: "Given the corrected kernel, when boundaries are exercised, then all advertised numerical controls remain active or are explicitly rejected across schedules"
verdict: PARTIAL
related: [023, 024, 025, 026]
tags: [freeze-audit, boundaries]
---

# Schedule policy closure

## Research
Reuse the independent equations, pinned upstream identities and qualified contracts in spikes 019–026. Numerical and implementation agreement are tested separately.

## Investigation Trail
Baseline 12cf2b1, production be7286e. No production changes.

## Results
Four controls pass: active damping in flooding/check-serial/variable-serial/layered execution, v1 residual budget-denial isolation, strict rejection of stable policy by the frozen research manifest contract, and rejection of unqualified stable-policy BPGD/Q-BPGD calls.

C02: residual scheduling accepts a v3 profile with damping 0.6 but produces exactly the undamped V2C update. This is another admitted profile/schedule mismatch. The conventional source procedure can remain undamped; its constructor should reject incompatible damping unless a distinct, independently qualified damped extension is selected. Blindly inserting damping would change the source schedule, so admission comes first.

## Investigation Trail
Expanded the schedule inventory beyond the three local schedules fixed in spike 024. The residual implementation maintains source-specific cache/reset order correctly in the tested v1 budget case, but its numerical profile admission is broader than its implemented update. Guided-decimation entry points explicitly reject the new policy; this is a correct exclusion, not a bug.

## Run
`OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/029-schedule-policy-closure/probe.py`
