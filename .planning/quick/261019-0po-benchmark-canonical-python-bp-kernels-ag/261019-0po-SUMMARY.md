---
id: 261019-0po
type: quick
status: complete
date: 2026-10-19
implementation_commit: 91f0559
---

# Bounded BP kernel efficiency study

Benchmarked BB72 binary SPA/min-sum against `ldpc` and Relay-BP Rust, and GB46 four-state BP4 against the pinned aSCED C++ implementation. Retained seeded workloads, three repeated batch timings, candidates, iteration/success evidence, source/build identities, and a profiler sample in [REPORT.md](./REPORT.md), [results.json](./results.json), and [profile.txt](./profile.txt).

The canonical Python kernels currently have order-of-thousands throughput gaps on these small code-capacity workloads. SPA candidates and iterations agreed with `ldpc` on 24/24 BB72 cases; early-stop BP4 candidates agreed with the C++ driver on 8/8 GB46 cases. Binary min-sum and fixed-eight-sweep BP4 retain explicit output divergences. Recommended a compiled, graph-indexed hot loop under the same canonical policy contract, preceded by recurrence-level differential checks for the divergent paths.

Verification: both Python drivers compiled; the native C++ driver built and ran from the pinned aSCED static library; benchmark output invariants were asserted; `git diff --check` passed. No production campaign was dispatched.
