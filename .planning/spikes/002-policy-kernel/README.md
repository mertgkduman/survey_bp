---
spike: 002
idea: pfister-slide-bp-reproduction
name: policy-kernel
type: standard
validates: "Given the existing fast decoders, when both code fixtures and slide knobs are applied, then numerical behavior is executable and qualified"
verdict: PARTIAL
related: [001-slide-evidence, 003-paired-reproduction]
tags: [decoder, q8, codes]
---

# Spike 002: Policy kernel

## What This Validates

The project's fast graph structures can run the presentation's four named policy variants on B1 and double-Gross with deterministic paired errors.

## Research

The project already has `CompiledBp4Graph` and `CompiledBinaryFlooding`, but their plain fast backends use float64 and do not implement the presentation's Q8 and damping policies. An experimental Numba wrapper in `from_dr_pfister_presentetations/policy_kernel.py` adds these knobs while leaving the canonical engine unchanged. The slide does not specify rounding boundaries, damping target, exact binary channel mapping, or schedule, so the wrapper marks those as assumptions.

## How to Run

`PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python from_dr_pfister_presentetations/verify_spike.py`

## What to Expect

The command prints `presentation spike checks passed` after checking code parameters, commutation, stabilizer/logical classification, exact fast-graph equality on double-Gross, source table size, and pilot ledger hashes.

## Investigation Trail

1. The validated double-Gross code has `n=288`, `k=12`; B1 has `n=882`, `k=24`.
2. Direct `PauliCode` construction for B1 was killed by its dense pairwise commutation validation. The spike uses the already validated CSS matrices to build the same indexed BP4 graph in bounded memory. Equality with the standard graph was verified on double-Gross.
3. The local Q8 kernel rounds to nearest even after scalar check and outgoing variable messages, uses variable-to-check damping, and stops on syndrome match. These decisions are explicit adaptations.
4. Independent GF(2) row-space checks confirm the residual logical classifier for both codes.

## Results

**PARTIAL.** The code identities, graph indexing, policy values, and local semantics are executable and checked. Source-fidelity qualification is open because the slide does not provide the missing numerical and scheduling details. The existing float64 BP4 prototype also differs from the slide rates, so Q8 rounding alone cannot explain the gap.
