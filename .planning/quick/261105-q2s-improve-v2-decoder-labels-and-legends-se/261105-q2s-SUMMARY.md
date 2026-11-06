---
status: complete
date: 2026-11-05
scientific_phase_status_changed: false
---
# V2 parameter names and curve interaction

Implemented display-only decoder labels shared by Results, Show curves, tables,
run details and Start from a saved specification. Names identify the algorithm,
check rule and recorded `variable = value` parameters rather than evidence labels.
Noise channels, binary marginal q versus joint p₀, fresh-weight γ versus old-weight
d, check caps versus V2C caps, and independent retained record identities remain
explicit. Equal settings receive N/set suffixes; a set does not imply independent
samples. A per-plot Parameter key explains the notation. Frozen IDs/specs remain
unchanged.

Added an accessible per-plot prefix combobox. Focus lists all available code
curves, typed prefixes filter case-insensitively, arrow keys/Enter select and add,
and Escape dismisses. Additional curves preserve the plot's existing selection.
Colors and axes remain stable while hiding/restoring selected curves. Plot paths
and points can be clicked to hide a curve; Show curves restores it. Hover or
focus a curve name previews its path at faint opacity without adding table or
export rows. Plot states remain independent.

Tables, Run details and reproduction, CSV and run-settings exports now all use
the same visible-curve set. An all-hidden plot explains how to preview/restore;
its data exports are disabled.

The display classifier hides 12 retired curves from v2: 4 canonical globally
clipped binary/BP4 float64-v1 arms, and 8 experimental Q8 BP4 state-clipping arms.
The resulting 101 measured curves retain corrected scalar-Q8 min-sum, binary
OMS quantization, paper-specific V2C caps and compatible study/circuit profiles.
Historical evidence and archived v1 are preserved byte for byte.

The metadata audit also corrected two inherited non-OSD QBP configuration
bindings: their actual source is the frozen vanilla BP4-v2 arm inherited by
assess.py, not the non-OSD Q-BPGD point runner. No numerical results changed.

## Verification

111 targeted Python/Node checks passed in 42.97 seconds. Actual Chromium passed
seven curve-interaction groups: parameterized labels, retirement filtering,
prefix/arrow selection, line toggling, hidden-curve preview, visible-only details
and exports, per-plot independence, saved names, mobile layout and no-match/Escape.
The existing ten-group v2 download/run/upload/circuit/archive regression also
passed using tiny fixtures. No scientific campaign was launched.

Read-only scientific metadata review confirmed the scope of clipping retirement,
the inherited QBP binding, and the q/p₀ and γ conventions. Rebuilding the catalog
matches the checked-in snapshot. V1 archive checksums are unchanged, and no
retained scientific data or decoder kernel changed. Browser checks were Chromium
only; no screen-reader audit was performed.

See `261105-q2s-VERIFICATION.json`. Full screenshots and exports remain local
under `.git/research-curve-browser-delivery/` and `.git/research-curve-regression/`.
Documentation is in `docs/research-interface.md`; preview remains
`http://127.0.0.1:8765/web/research/`.
