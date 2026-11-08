---
spike: 031
idea: canonical-kernel-audit
name: prior-state-fix
type: standard
validates: "Given an admitted configuration, when executed, then normalized stored priors are finite before shortcuts"
verdict: VALIDATED
related: [027, 028, 029, 030]
tags: [fixes, freeze]
---

# prior-state-fix

## Research
Reuses the source-scoped semantics and counterexamples in spikes 027–030. Pure validation and control-flow corrections require no new dependency or upstream equation.

## Investigation Trail
Baseline 729157f; historical evidence is retained unchanged.

## Results
21 pre-fix failures, seven passing controls. After correction, 226 prior/admission/boundary tests pass. BoundBinaryFlooding now requires a compiled graph and normalizes a finite real scalar into float64 at construction. Floating immutable buffers are checked after dtype conversion, before ownership or execution. Invalid bool/string/complex/container priors are rejected; finite float32/longdouble inputs, subnormals and large finite float64 values remain supported.

## Run
`.venv/bin/python -m pytest tests/canonical/test_freeze_fixes.py tests/canonical/test_boundary_fixes.py tests/canonical/test_kernel_contract_admission.py -q`

## Performance and contract
Validation occurs once at binding/construction, outside decode loops. Post-cast checks replace overflow warnings with an explicit ValueError rather than silently storing infinity. No frozen numerical equations or profile identities changed.
