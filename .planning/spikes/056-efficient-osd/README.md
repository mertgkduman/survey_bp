---
spike: '056'
idea: efficient-canonical-bp-osd
name: efficient-osd
type: comparison
validates: Given pinned public OSD source and independent exact GF2 oracles, when OSD-0 and CS-10 run, then every candidate is valid, scored reproducibly and traceable at practical cost.
verdict: PENDING
related: ['055', '057']
tags: [osd, correctness, performance, provenance]
---

# Spike056: observable, efficient OSD

## What This Validates

Compare the public standalone C++ OSD algorithm, an independent dense GF2 oracle and a source-derived optimized implementation. Authorize production sampling only after deeper correctness, source correspondence and warmed performance qualification. This implements the user's explicit request to optimize public OSD code for this repository; the earlier failed Phase7 source/API receipt stays immutable.

## Research

Pinned public reference: quantumgizmos/ldpc commit d3429964cd4ffe1abfc041c6ec8b8425cb174f40, src_cpp/osd.hpp, sort.hpp and gf2sparse_linalg.hpp (MIT). Public osd.hpp enumerates all non-pivot single flips and pairs within the requested depth, solves each candidate separately and scores against declared channel probabilities. Its sorting routine orders supplied signed log-odds ascending, not absolute magnitude; this must be tested and explicitly recorded instead of inheriting an incompatible historical assumption. The Roffe paper ranks error probabilities descending, an equivalent signed-log-odds ordering.

| Approach | Benefits | Costs/constraints |
| --- | --- | --- |
| Public native standalone C++ | Independent executable source reference | Python exposure lacks candidate provenance; per-candidate solve/allocation |
| Dense GF2 Python oracle | Transparent complete candidate set, easy independent validity checks | Qualification only; slower |
| Source-derived Numba/packed GF2 | Reuse elimination and affine solution directions, observable candidates/work | Requires independent algebra/source/tie/overflow qualification |

## How to Run

Qualification scripts and commands will be recorded after implementation. No package replacement in the primary environment is permitted.

## Investigation Trail

1. Consulted Phase7 failed receipt: correct tiny syndromes did not suffice because its public API omitted full candidate enumeration. Preserving that receipt and qualification test.
2. Inspected public native OSD and sort source at an immutable revision. Found signed reliability ordering and source scoring conventions that require explicit tests.
3. Plan independent exact tiny-matrix checks, rank-deficient/zero/tied syndromes, source differential tests on actual toric terminal BP states, complete candidate evidence, allocation/count checks and warm same-input timing.

## Results

First qualification passes404 complete native/oracle candidate-set comparisons, including128 actual toric BP terminal-state/method cases. Thirty regression cases pass including the unchanged failed Phase7 receipt contract. Warm alternating single-core timings show CS10 about2.2–2.4x faster than native, but OSD0 is slower (0.53–0.62x native throughput on longer codes). This is not yet a production-efficiency pass. Preserve qualification-before.json and the baseline source revision before optimizing original-syndrome checks and OSD0 reduction work.
