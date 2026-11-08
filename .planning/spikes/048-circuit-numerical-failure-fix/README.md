---
spike: 48
idea: canonical-kernel-audit
name: circuit-numerical-failure-fix
type: standard
validates: "Close E01 with failing-then-passing regression and unchanged valid behavior."
verdict: VALIDATED
related: [043, 045, 046]
tags: [circuit, fixes, contracts]
---

# E01: circuit numerical failure

Implemented in approved order E03 → E01 → E02 through GSD quick task
261108-oq5-fix-circuit-contract-findings-e03-e01-e0. Commit: **02d890a**.

Compiled NMS checks its scaled magnitude before clipping and raises the canonical NumericalFailure at normalized_min_sum_output. Scalar/compiled/auto agree; large finite coefficients and unexecuted updates remain admitted.

## Reproduction and verification

- Before: five overflow failures with twelve passing finite/stopping controls; [red receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e01-red.log).
- After: 78 passing circuit checks; [green receipt](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/e01-green.log).
- Final: 257 regression tests and all 12 requalification groups pass.
- [Source-hashed qualification](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/results.json).
- [Full summary and repeatable commands](../../quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/SUMMARY.md).

The original 043–046 failure receipts are unchanged. Final independent factor,
native and capability-matrix receipts match their ordinary-domain baselines.
No numerical profile or publication gate was changed.

