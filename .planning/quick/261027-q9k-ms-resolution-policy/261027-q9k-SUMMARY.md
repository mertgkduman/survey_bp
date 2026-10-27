---
status: complete
quick_id: 261027-q9k
date: 2026-10-27
---

# Corrected BP4 MS and composable resolution

`CompiledBp4Graph.from_code(..., rule="min_sum")` and
`CompiledBp4Graph.from_css(..., rule="min_sum")` select the corrected MS
recurrence by default. The three identity-referenced Pauli V2C LLRs remain
unbounded float64; the full commute-minus-anticommute log-sum-exp projection
is formed before Q8 scalar rounding. Check outputs are Q8, scale 16; the
default damping is zero and the legacy minimum-LLR hard decision is explicit.
The historical experimental Q8 implementation and prior evidence are intact.

The shared `ResolutionPolicy` and `BpFloodingPolicy` specify float16/32/64 or
signed fixed 8/16/32, message scope, coefficient mode, check rule, damping,
MS scale and offset, and tie/shortcut behavior. `coefficients="same"` rounds
`d`, `1-d`, `alpha`, and `beta` to the selected format at binding. `as_spec`,
`from_spec`, `as_evidence`, and SHA-256 semantic identity support explicit
data-only replay. Both compiled binary and BP4 flooding graphs execute the
policy; public historical manifests do not silently adopt it.

Verified the new BP4 `from_css` default against the prior `both_changes`
diagnostic on 200 paired B1 shots and 200 paired double-Gross shots: candidate,
iteration, convergence, and independent outcome matched for every shot.
Binary OMS with the new policy matched the earlier experimental kernel on
those same shots, in both CSS components. The 400 per-shot records, outcome
counts, policy identities, and verified ledger SHA-256 are in
`from_dr_pfister_presentetations/results/ms_resolution_policy_qualification/`;
the reproducible runner is `qualify_resolution_policy.py`. Focused regression
tests: 28 passed. Float16 rounding was
also compared against NumPy conversion on 50,000 finite random values with
zero mismatches. No full source-curve campaign was rerun in this quick task;
the prior nine-point exploratory campaign remains the curve evidence.

The new policy is a numerical-resolution contract in the compiled development
backend. Quantized values still travel in float64 arrays, and intermediates
are float64. Publication dispatch requires a new manifest and event-ledger
binding for this policy. The independent double-Gross p=.06 source-point
discrepancy described in the earlier diagnostic remains unresolved.
