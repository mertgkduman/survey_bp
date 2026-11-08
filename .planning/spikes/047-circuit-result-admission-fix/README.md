---
spike: 47
idea: canonical-kernel-audit
name: circuit-result-admission-fix
type: standard
validates: "Close E03 with failing-then-passing regression and unchanged valid behavior."
verdict: VALIDATED
related: [043, 045, 046]
tags: [circuit, fixes, contracts]
---

# E03: circuit result admission

Implemented in approved order E03 → E01 → E02 through GSD quick task
261108-oq5-fix-circuit-contract-findings-e03-e01-e0. Commit: **d6e8756**.

Binary matrix ranks and values, boolean convergence and nonnegative int64-representable iteration counts are validated before lossless conversion. The owned execution arrays are then bound to the ledger. Valid normalization, replay, zero-shot shapes and immutability are retained.

## Reproduction and verification

- Before: 26 failures and one passing valid-input control; [red receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e03-red.log).
- After: 97 passing result/circuit/evidence checks; [green receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e03-green.log).
- Final: 257 regression tests and all 12 requalification groups pass.
- [Source-hashed qualification](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/results.json).
- [Full summary and repeatable commands](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/SUMMARY.md).

The original 043–046 failure receipts are unchanged. Final independent factor,
native and capability-matrix receipts match their ordinary-domain baselines.
No numerical profile or publication gate was changed.

