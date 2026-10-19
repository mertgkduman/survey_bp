---
id: 261019-0po
slug: benchmark-canonical-python-bp-kernels-ag
type: quick
status: complete
---

# Bounded BP kernel efficiency study

Goal: measure whether the policy-composable canonical engines can support efficient decoding while preserving their inspectable semantics.

1. Pin local source/build identities and choose matched CSS and GB46 workloads. Record graph, syndrome/sample, priors, update/schedule, stopping, thread count, CPU, and timing scope. Reject cross-family speed rankings.
2. Run bounded repeated timings for canonical binary SPA/min-sum, `ldpc` C++/Cython, Relay-BP Rust plain min-sum, canonical quaternary BP4, and aSCED C++ BP4. Check output consistency, convergence, iterations, and work before any speed interpretation.
3. Retain raw results, benchmark driver, and a concise report with uncertainty and bottlenecks. Recommend concrete optimization experiments where evidence supports them.

No production campaign, source-reproduction claim, or native aSCED matched-input promotion follows from these development timings.
