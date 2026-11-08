---
spike: 49
idea: canonical-kernel-audit
name: circuit-control-admission-fix
type: standard
validates: "Close E02 with failing-then-passing regression and unchanged valid behavior."
verdict: VALIDATED
related: [043, 045, 046]
tags: [circuit, fixes, contracts]
---

# E02: circuit controller admission

Implemented in approved order E03 → E01 → E02 through GSD quick task
261108-oq5-fix-circuit-contract-findings-e03-e01-e0. Commit: **5855049**.

Non-default solution_limit/relay_alpha outside Relay and bias outside guided/beam are rejected. Shared defaults preserve policy identity. Active guided/beam bias and Relay solution limits remain effective.

## Reproduction and verification

- Before: eight inactive-control failures with seven passing active/default controls; [red receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e02-red.log).
- After: 93 passing circuit checks; [green receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e02-green.log).
- Final: 257 regression tests and all 12 requalification groups pass.
- [Source-hashed qualification](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/results.json).
- [Full summary and repeatable commands](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/SUMMARY.md).

The original 043–046 failure receipts are unchanged. Final independent factor,
native and capability-matrix receipts match their ordinary-domain baselines.
No numerical profile or publication gate was changed.

