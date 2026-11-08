---
spike: 041
idea: canonical-kernel-audit
name: committed-posterior-fix
type: standard
validates: "Close D02 with retained regressions"
verdict: VALIDATED
related: [034, 035, 036, 037]
tags: [fixes, completeness]
---

# D02 correction

Baseline 6f68961. Historical evidence is retained unchanged. Fixes execute D03 → D04 → D01 → D02 → D05.

The serial unit now transports the exact post-transform belief array alongside its candidate and C2V state. Successful results own an immutable posterior snapshot. No posterior is reconstructed using a different prior; this also removes one redundant full belief assembly per local unit. Denied units publish no posterior and invoke no transformations.

Red: 10 failed / 2 passed. Green: 91 passed in 7.27s, including ordinary, nonuniform-prior, field-only, combined, no-op and denied cases, indexed context and public memory replay. Numerical decisions, damping and work accounting are unchanged.
