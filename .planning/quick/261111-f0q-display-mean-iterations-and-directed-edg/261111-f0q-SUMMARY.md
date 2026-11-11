---
quick_id: 261111-f0q
status: complete
date: 2026-11-11
implementation_commit: 324b53a
verification: passed
---

# Iteration and directed edge work

Results tables and CSV downloads have adjacent mean iterations per shot and
mean directed edge updates per shot columns. Both quantities are available
as plot metrics. The work columns wrap their labels within a narrow plot card,
and linear work axes have room for their ticks and labels.

Iteration averages sum executed sweeps across decoder components and
decimation rounds and include successful and failed shots. The historical
cross-code per-component means are converted to component totals. Directed
work uses the retained counter where available and otherwise follows the
existing two-directions-per-edge-per-sweep convention with the exact CSS or
circuit graph size. Unequal binary X/Z graphs use their separate retained
iteration counters. Incomplete work counters display Unavailable, and other
retained work measures remain available.

The original catalog observations and original work fields compare equal
after removing the three additive display fields. Raw evidence and running
campaign inputs were preserved. This update executes no research simulations.

Verification passed 124 research tests and 18 Chromium workflow checks.
The focused import check also compares browser and CLI derivations for
unequal X/Z graph sizes. Browser checks cover both plot metrics, adjacent
columns, CSV parity, incomplete counters, curve visibility, empty results,
stale selections, custom input validation, and mobile layout. The final work
chart and table were visually inspected.

The final B1/C2 collector in quick task 261110-sic used the same catalog
adapters. All 77 verified campaign points include both work metrics.
