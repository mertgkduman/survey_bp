---
spike: 038
idea: canonical-kernel-audit
name: circuit-admission-fix
type: standard
validates: "Close D03 with retained regressions"
verdict: VALIDATED
related: [034, 035, 036, 037]
tags: [fixes, completeness]
---

# D03 correction

Baseline 6f68961. Historical evidence is retained unchanged. Fixes execute D03 → D04 → D01 → D02 → D05.

## Results
33 failing admission cases and 10 passing controls before the fix. After construction-time validation, all 50 circuit tests pass. Shared settings admission covers factory/direct/replacement paths; DEM shape/type/CSR/table/finite-state checks precede immutable buffer ownership. This also closes the DEM write-flag hole as a prerequisite for D04. Numerical equations and source DEM interpretation are unchanged.
