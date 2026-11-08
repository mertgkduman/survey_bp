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


## Integration results
- Fresh-cache broad regressions: **1,412 passed, one existing skip**, including 44 new cases across C03/C01/C02 (`regression.log`, `regression.xml`).
- Independent qualification: **18/18 groups pass** (`qualify.py`, `results.json`). Pinned native correspondence and exact inference remain passing; prior audit directories are never rewritten.
- Matched CPU replay: **6,144 baseline/current ledger rows**; candidates, iterations, convergence and work agree exactly.
- Alternating warmed processes, 15 repetitions: one-worker throughput is **+0.28% binary, −0.22% BP4** against `729157f`; all worker settings remain within 1%. Numba diagnostics confirm parallel shot loops. This allocation is one physical core with two sibling threads, so no multicore scaling claim is made.
- An initial sequential run showed a roughly 17% slowdown in both the candidate and unchanged binary control. Retained in `preliminary-sequential/`; final interleaved measurements do not establish a material regression. No unnecessary arithmetic optimization was introduced in response to host drift.

## Reproduce and scope
Run `qualify.py`, the broad pytest command in the consolidated report, `compare_cpu.py`, then `paired_cpu.py`, then `verify.py` with `.venv/bin/python`. Use fresh Numba caches for changed shared helpers and run timings after tests. The comparison scripts extract baseline source into owned temporary directories; the working tree remains on its current revision. `paired_cpu.py` uses the same source/input identities and retained ledgers from `compare_cpu.py`.

See [the consolidated fix report](../CANONICAL-KERNEL-FREEZE-FIXES.md) for commands, performance tables, public-contract limits and source scopes. Phase position, publication gates, public defaults and historical evidence are preserved. `verification.json` records the final source/evidence checks.
