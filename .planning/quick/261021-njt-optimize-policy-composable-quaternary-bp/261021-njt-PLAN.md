---
id: 261021-njt
slug: optimize-policy-composable-quaternary-bp
type: quick
status: complete
---

# Optimize policy-bearing quaternary BP paths

Goal: improve the shared BP4 policy execution paths without changing equation order, numerical profile, update freshness, work accounting, or replayable results.

1. Capture same-host baseline sweep timings and full numerical/evidence digests for transformed BP4 flooding and fixed-alpha MBP4 flooding and variable-serial paths on a pinned GB46 workload.
2. Reuse immutable graph incidence across policy paths. Quantize each old V2C edge once per complete flooding snapshot while retaining excluded-neighbor reduction order and every transform/MBP4 recurrence. Serial paths must continue to read current V2C after each variable commit.
3. Compare before/after buffers and evidence, run focused quaternary policy and replay tests, measure final speed, and record limits. Leave the reference backend and campaign authorization semantics intact.
