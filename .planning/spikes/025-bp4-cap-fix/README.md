---
spike: 025
idea: canonical-kernel-audit
name: bp4-cap-fix
type: standard
validates: "Given audited counterexamples, when corrected, then compiled legacy BP4 honors the selected saturation"
verdict: VALIDATED
related: [019, 020, 021, 022]
tags: [fixes, contracts, numerics]
---

# BP4 active cap

## Research
Reuses the independent oracles and pinned primary-source investigation in spikes 019–022. No new dependencies.

## Investigation Trail
Started from boundary audit at 02d165e; historical evidence is retained unchanged.

## Results
Seven of fifteen cap/syndrome cases failed before the fix. After propagating the active profile saturation into both compiled sweep and decode calls, all 47 boundary and compiled-BP4 tests pass. Qualification compares C2V, V2C, beliefs, marginals, candidates, iteration counts and convergence over caps 0.1, 1, 5, 25 and 40. Default v1 cap 25 remains unchanged.

## How to Run
`.venv/bin/python -m pytest tests/canonical/test_boundary_fixes.py tests/canonical/quaternary/test_compiled_bp4.py -q`

## Investigation Trail
Both legacy entry points hardcoded the default constant. This was parameter propagation, not a changed equation or a reason to rename historical profiles.
