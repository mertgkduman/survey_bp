---
spike: 032
idea: canonical-kernel-audit
name: bp4-failure-fix
type: standard
validates: "Given an admitted configuration, when executed, then all BP4 scopes fail consistently on nonfinite state"
verdict: VALIDATED
related: [027, 028, 029, 030]
tags: [fixes, freeze]
---

# bp4-failure-fix

## Research
Reuses the source-scoped semantics and counterexamples in spikes 027–030. Pure validation and control-flow corrections require no new dependency or upstream equation.

## Investigation Trail
Baseline 729157f; historical evidence is retained unchanged.


## Changes and results
Finite-state guards cover BP4 beliefs, proposals, committed V2C and marginal inputs independently of rounding scope. Finite inputs whose shifted log weights underflow remain valid. A compiled per-shot exception/status wrapper reports failed indices after restoring the caller thread mask; no partial batch or ledger is published. The wrapper lives outside `prange` to preserve parallel execution.

The pre-fix counterexamples produced **7 failed, 1 passed** (`red.log`; tests were subsequently moved from `test_freeze_fixes.py` to `test_bp4_failure_contract.py`). The focused suite now has **169 passed** with no warnings (`green.log`). It exercises all three scopes, sweep/single/batch paths, mixed successful/failed batches, ledger preservation, thread restoration, and ordinary stable-SPA behavior. CPU throughput and broader integration are qualified in spike 033.

An initial inline try/except made Numba serialize the batch loop. Moving exception handling into a non-inlined compiled shot helper removed that compiler warning. Numba's [documented exception restrictions](https://numba.readthedocs.io/en/stable/reference/pysupported.html#exception-handling) require catching `Exception` without carrying the exception instance; batch errors therefore report generic execution failure and exact failed shot indices, not an invented numerical cause.
