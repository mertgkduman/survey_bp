---
spike: '063'
idea: workbench-feedback-forecast
name: workbench-controls-forecast
type: standard
validates: Given earlier user-directed HTML revisions and the live workbench, when inspected, then likely feedback is tied to observed behavior and explicit confidence.
verdict: PARTIAL
related: ['056', '057', '061', '062']
tags: [html, workbench, feedback, forecast]
---

# Controls, defaults and experiment builder

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

- **Very high** — Changing to min-sum should not silently change precision or stopping behavior. Live selection changes float64→int8, strict_pauli→min_llr and shortcut false→true. Source is the build-rule handler in app.js.
- **High goal; medium implementation scope** — If I can compare a decoder, I want a clear way to reproduce or request that exact configuration. Builder has565 presets but only BP/Q-BP and optional Q-BPGD visual families. Selecting a BP+OSD preset blocks the general package builder and directs to study commands.
- **Medium** — Remember the paper, figure and curves I selected, and let me share that comparison. Opening Roffe leaves URL at#results; reload returns to Custom plots. Only uploaded results currently persist.
- **Medium** — Too many similar options and reused colors make the comparisons harder to follow. Roffe has8 paper plus332 additional curve controls; color palette repeats every six curves. Recommendations still says paper selectors moved to v1 although current v2 has seven paper options.

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
