---
spike: 024
idea: canonical-kernel-audit
name: local-damping-fix
type: standard
validates: "Given audited counterexamples, when corrected, then local schedule updates honor their active numerical profile"
verdict: VALIDATED
related: [019, 020, 021, 022]
tags: [fixes, contracts, numerics]
---

# Local damping

## Research
Reuses the independent oracles and pinned primary-source investigation in spikes 019–022. No new dependencies.

## Investigation Trail
Started from boundary audit at 02d165e; historical evidence is retained unchanged.

## Results
Independent degree-two recurrences cover damping 0, 0.1 and 0.6 in check-serial, variable-serial and layered execution through the budgeted public local-step seam. Nine failures before the change; all 69 focused schedule/boundary regressions pass afterward. Unselected edges remain untouched except for the selected profile's declared entry clipping. Damping precedes optional V2C memory transforms, as in flooding. V1 has no damping parameter and retains undamped updates.

## How to Run
`.venv/bin/python -m pytest tests/canonical/test_boundary_fixes.py tests/canonical/test_schedule_semantics.py tests/canonical/test_residual_schedule.py tests/canonical/test_cluster_schedule.py -q`

## Investigation Trail
Layered execution shared both omissions, so it received the same fix. Red evidence was rerun synchronously against the committed pre-fix schedule module after an initial asynchronous run raced with the edit; the retained red.log is the confirmed pre-fix run. An initial green command named nonexistent test files; the retained green.log uses the actual suite paths.
