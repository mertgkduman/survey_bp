---
spike: 023
idea: canonical-kernel-audit
name: construction-admission-fix
type: standard
validates: "Given audited counterexamples, when corrected, then accepted construction paths enforce one contract"
verdict: VALIDATED
related: [019, 020, 021, 022]
tags: [fixes, contracts, numerics]
---

# Construction admission

## Research
Reuses the independent oracles and pinned primary-source investigation in spikes 019–022. No new dependencies.

## Investigation Trail
Started from boundary audit at 02d165e; historical evidence is retained unchanged.

## Results
15 regression cases failed before the fix. All 175 construction/profile/compiled BP4 tests passed after it. Constructors now enforce semantic admission, canonical CSR consistency and immutable buffer ownership, including dataclass replacement. Conflicting flooding/kernel profiles are rejected. Validation occurs once at graph construction; decoding arithmetic is unchanged.

## How to Run
`.venv/bin/python -m pytest tests/canonical/test_boundary_fixes.py tests/canonical/test_kernel_contract_admission.py tests/canonical/quaternary/test_compiled_bp4.py -q`

## Investigation Trail
The factory-only guard was insufficient. Shared dataclass post-init admission closes direct construction and replacement. BP4 cross-index validation uses a stable index sort rather than scanning all edges once per variable. Raw caller buffers are copied into immutable bytes-backed arrays so caller mutation cannot alter a compiled graph.

## Integration follow-up
The broader suite exposed ten Relay-path failures because its prior-vector adapter delegated all numerical methods but omitted a `profile` property. The adapter now exposes its underlying kernel profile, so it obeys the same consistency check; no bypass was introduced. All 19 focused Relay, calibration-ledger and adapter tests pass. The first broad run and subsequent clean-cache qualification are retained under spike 026.
