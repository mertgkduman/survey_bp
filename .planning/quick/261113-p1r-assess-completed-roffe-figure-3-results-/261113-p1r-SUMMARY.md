---
status: complete
analysis_commit: efc3e6a
campaign_status: audited_published
source_assessment: pointwise_consistent_at_current_precision
---

# Completed Roffe Figure3 comparison

Collector61785160 completed0:0: all218 points,9,816 retained decoder shots /
4,360 logical block failures pass full ledger/count/work/hash and endpoint
replay audit. This includes109 ordinary binary BP and109 additional joint
Q-BP points, all with20 failures and the frozen source-specific T=n budget.

All109 digitized ordinary-BP paper values lie inside our independently
recomputed pointwise95% stopping-aware intervals:25/25 for distance9 and28/28
for distances11/13/15. Point-estimate ratios range .8111–1.2227 of source,
maximum relative difference22.3%. At p=.01, paper versus canonical LER:
[[162,2,9]] .04434 versus .03597; [[242,2,11]] .06553 versus .06920;
[[338,2,13]] .09035 versus .09434; [[450,2,15]] .11819 versus .13333.
The low-noise increase in ordinary-BP failure with code distance matches the
source's qualitative observation.

This is pointwise consistency at20-failure precision. High-p saturation and
cross-code shared samples preclude treating109 coverage events as independent.
No simultaneous acceptance criterion was prespecified; author counts and exact
row/numerical conventions are unavailable. It remains a canonical adaptation,
not a claim of recovered source numerical identity or BP-OSD reproduction.
Q-BP uses depolarizing noise and is kept outside the direct X-only source test.

Re-extracted the pinned original source archive and matched all109 coordinates
byte-for-byte with source_points.json. Independently reconciled terminal counts,
exact negative-binomial intervals, directed work and source targets. Saved a
218-row results-table.csv, assessment.json with source/receipt hashes, RESULTS.md
and a4-panel PNG/PDF overlay. The figure was visually inspected: all source
curves, measured points and uncertainty are visible with consistent log axes.
No new decoding/simulations or frozen scientific edits were needed.

Published view:80→88 curves,419→637 points,8→12 codes,0 registered circuits.
All157 existing raw series/points remain structurally identical; eight curves
and the four previously hidden toric inputs become visible. Passed54 catalog/
extension/projection/display checks, seven measured-public browser groups and
five source-specific browser groups with no page errors or browser simulations.
The source-specific browser fixture now removes real Roffe series from its
synthetic base so it remains valid after publication. Matrix loading, min-sum
alpha schedule, saved-choice refusal to silently change policy, CSV/settings,
empty/import/custom inputs, stale state and archived v1 are verified.

Scientific plan retains40 pins and SHA256
`eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3`.
No canonical/quaternary, source/plan/runner, shared-runtime or v1 file changed.
The separate MacKay rare point remains outside this completed Roffe campaign.
Phase11 publication gates and milestone status are unchanged.
