---
spike: 033
idea: canonical-kernel-audit
name: residual-admission-fix
type: standard
validates: "Given an admitted configuration, when executed, then conventional residual scheduling rejects incompatible damping"
verdict: VALIDATED
related: [027, 028, 029, 030]
tags: [fixes, freeze]
---

# residual-admission-fix

## Research
Reuses the source-scoped semantics and counterexamples in spikes 027–030. Pure validation and control-flow corrections require no new dependency or upstream equation.

## Investigation Trail
Baseline 729157f; historical evidence is retained unchanged.


## Changes and focused verification
The conventional Huang–Ueng residual constructor now rejects nonzero V2C damping before state/cache creation. Legacy v1 and explicitly undamped v2/v3 remain admitted. Existing lifecycle fixtures now request undamped v3 explicitly; their independent equations and expected results are unchanged. No damped residual algorithm is invented.

Before the guard: **5 failed, 3 passed** (`red.log`). After the guard: **18 passed** across admission and lifecycle/budget tests (`green.log`). Broader integration and CPU measurements are recorded below after qualification.
