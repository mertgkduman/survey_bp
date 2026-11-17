---
spike: '062'
idea: workbench-feedback-forecast
name: paper-comparison-forecast
type: standard
validates: Given earlier user-directed HTML revisions and the live workbench, when inspected, then likely feedback is tied to observed behavior and explicit confidence.
verdict: PARTIAL
related: ['055', '060', '061', '063']
tags: [html, workbench, feedback, forecast]
---

# Paper comparisons, metrics and work

## What this validates

Concrete UI observations and historical intent can ground a feedback forecast.
They cannot establish what the user will prefer without later user feedback.
The user selected **all three checks, feedback forecast only**. No mock-up,
production edit, catalog rebuild, simulation or deployment is in scope.

## Research

Read earlier user-directed GSD records and HTML revisions; inspected the current
source/catalog and real browser. Followed the existing static HTML/JS and
Playwright patterns. No new dependency or external-service API was needed.

| Approach | Benefit | Limitation | Disposition |
|---|---|---|---|
| History/source only | Preserves precise prior requirements | Can miss visible UX behavior | Used as primary context |
| Live browser plus pinned earlier UI | Checks actual defaults, layout and controls | Earlier UI uses current catalog; preference remains inferred | Used for verification |
| Proposed new HTML | Can test a design choice | User declined mock-up | Not built |

## How to run

From repository root, serve the existing workbench on127.0.0.1:8883, then run
`.venv/bin/python .planning/spikes/061-results-discovery-forecast/probe.py`.
This navigates current/historical HTML and saves inspection evidence only.
It does not execute experiments or write product files.

## Findings

- **High** — Opening a paper should take me straight to useful comparisons, not an empty graph. MacKay Fig.15 has zero paper curves and24 additional; LP Example4 has zero paper curves and25 additional. Both default to zero visible rows. Relay/Beam/BP-SF controlled CSS views likewise have zero paper reproductions.
- **High** — There is too much interface before I can see the result. With the same catalog the custom chart moves from top640px before the paper update to811px now. Current paper chart begins at1260px in a1050px viewport. Yao page is12812px high; Roffe offers340 curve controls.
- **Very high** — Compare decoders at the paper budget or the same measured cost, and make the tradeoff visible. Your corrections about88200 iterations, runtime matching to OSD0, damping/scale/offset tuning and work units. Current metrics exist, but are a single per-card dropdown; new OSD benchmark is not catalogued.
- **High** — Which parameters and success metric produced each plotted point? Repeated user questions about X/Z block failure, paper budget, mean iterations/edge updates, tuned settings and circuit observable success. Current main table lacks explicit per-point tuning columns and source references are deliberately excluded.

## Investigation trail

1. Separated explicit older user requests from new hypotheses; do not treat
   already-delivered axis/filter/group controls as missing features.
2. User selected forecast only at the alignment gate; no UI prototype built.
3. Captured current catalog bytes for the live and historical views. Historical
   HTML comparison uses pre-781055fb index/app/style plus current shared helpers,
   not the entire historical data/environment.
4. Corrected a historical-route test-harness lambda binding error; retained failed
   probe logs and reran. It is not evidence of product loading performance.
5. Live observations completed without page errors; inspected screenshots.
6. Verified production source/catalog bytes unchanged from the initial snapshot.

## Results

**PARTIAL** — current behavior is verified; the predicted preferences are not
user-validated. Full ranked forecast, constraints and confidence are in
[FORECAST.md](../061-results-discovery-forecast/FORECAST.md). Shared observations
and source hashes are in the061 directory. This is a research handoff only.
