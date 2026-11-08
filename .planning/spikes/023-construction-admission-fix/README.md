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
15 regression cases failed before the fix. All 174 construction/profile/compiled BP4 tests passed after it. Constructors now enforce semantic admission, canonical CSR consistency and immutable buffer ownership, including dataclass replacement. Conflicting flooding/kernel profiles are rejected. Validation occurs once at graph construction; decoding arithmetic is unchanged.

## How to Run
`.venv/bin/python -m pytest tests/canonical/test_boundary_fixes.py tests/canonical/test_kernel_contract_admission.py tests/canonical/quaternary/test_compiled_bp4.py -q`

## Investigation Trail
The factory-only guard was insufficient. Shared dataclass post-init admission closes direct construction and replacement. BP4 cross-index validation uses a stable index sort rather than scanning all edges once per variable. Raw caller buffers are copied into immutable bytes-backed arrays so caller mutation cannot alter a compiled graph.
