---
spike: '056'
idea: efficient-canonical-bp-osd
name: efficient-osd
type: comparison
validates: Given pinned public OSD source and independent exact GF2 oracles, when OSD-0 and CS-10 run, then every candidate is valid, scored reproducibly and traceable at practical cost.
verdict: VALIDATED
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

Run `PYTHONPATH=src .venv/bin/python .planning/spikes/056-efficient-osd/probe.py` with the clean pinned native checkout at `.git/osd-upstream`. It builds the thin reference adapter with g++ and writes the qualification receipt. Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_uniform_osd.py tests/canonical/test_postprocessing_osd.py` for independent algebra and historical-admission checks. No package replacement in the primary environment was needed. Do not overwrite a receipt pinned by a dispatched plan; use a separate qualification directory for later changes.

## Investigation Trail

1. Consulted Phase7 failed receipt: correct tiny syndromes did not suffice because its public API omitted full candidate enumeration. Preserving that receipt and qualification test.
2. Inspected public native OSD and sort source at an immutable revision. Found signed reliability ordering and source scoring conventions that require explicit tests.
3. Plan independent exact tiny-matrix checks, rank-deficient/zero/tied syndromes, source differential tests on actual toric terminal BP states, complete candidate evidence, allocation/count checks and warm same-input timing.

## Results

Passed404 complete native/oracle candidate-set comparisons, including128 actual toric BP terminal-state/method cases. Thirty regression cases pass including the unchanged failed Phase7 receipt contract. Exact search coverage, scoring/ties, signed reliabilities, redundant/inconsistent syndromes, zero inputs, packed-word boundaries, immutability and original-syndrome validation pass.

The first implementation was correct but OSD0 was slower. Preserved baseline source commit9865447 and qualification-before.json; removed a dense per-call int64 validation allocation and unnecessary OSD0 above-diagonal reduction. The final warmed, alternating, single-core benchmark puts CS10 at2.1–3.4x native throughput, with the optimized call also producing full candidates, digest and counters. OSD0 is33–55 microseconds/call: slower than native's final-only interface on the two smaller matrices and comparable/faster on the larger ones. No universal OSD0 speedup is claimed. Its additional provenance/validation overhead is retained, and end-to-end pilot timings must assess its contribution alongside canonical BP.

The native timing wrapper was corrected to exclude redundant Python tie-control sorting for already order-equivalent unique inputs. Only qualification.json's final timings support the final comparison; the earlier snapshot remains historical. Constructor/JIT costs are excluded, CPU affinity is recorded, and measurements do not imply end-to-end speedups.

Qualified scope is uniform-channel OSD0/CS with no hidden truth. Source sorting is signed log(P0/P1), stable original-ID ties are explicit, and strict first-minimum scoring is uniform-channel minimum Hamming weight. OSD0 uses a partial pivot prefix sufficient to span the syndrome; its reported pivots/unprocessed columns are not a claim of full matrix rank. Complete candidate vectors and weights are available through the API, with per-shot candidate-set digests and deterministic replay planned for production. The historical failed Phase7 admission remains unchanged. Nonuniform channels and generic Phase7 worker admission are outside this new version's qualification.
