# Likely feedback on the research workbench

My strongest inference: you want recently completed research to appear in the workbench, organized into useful paper/figure comparisons, with plots visible early and the settings/cost behind each result clear.

These are predictions, not an implementation plan approved by the user. The user explicitly chose **feedback forecast only**. No mock-up, production HTML/catalog edit, simulation or deployment was made.

## Ranked forecast

| Priority | Likely feedback | Likely requested change | Confidence |
|---|---|---|---|
| 1 | Why are PriorTilt and the latest efficiency results still missing from Available experiment results? | Publish reviewed recent studies through the shared catalog; show audited progress/freshness. PriorTilt gets named Fig.1 views. OSD v2 gets an efficiency/benchmark view with its own scope. | Very high |
| 2 | Opening a paper should take me straight to useful comparisons, not an empty graph. | Keep separate named figures, paper-configuration curves selected and one group switch for our comparisons. Give adaptation-only views an obvious Show comparisons action and state their qualification before plotting. | High |
| 3 | There is too much interface before I can see the result. | Show the chart earlier; use compact figure navigation and a concise curve shortlist, retaining all requested parameter values in accessible expanded labels/details. Put large tables and detailed evidence behind deliberate expansion. | High |
| 4 | Compare decoders at the paper budget or the same measured cost, and make the tradeoff visible. | Make paper-budget, extended-budget and runtime-matched results distinct; keep iterations and directed updates adjacent. Expose whole BP-OSD time, BP/OSD split, hardware/cohort/evidence mode, and regression cases. Consider LER-versus-cost and linked views at a fixed p. | Very high |
| 5 | Changing to min-sum should not silently change precision or stopping behavior. | Make update rule, message resolution, hard decision and zero-syndrome shortcut explicit independent settings; preserve them when changing one control or explain a required compatibility change. | Very high |
| 6 | Which parameters and success metric produced each plotted point? | Make noise/physical-versus-component p, metric definition and per-point selected T,damping,scale,offset/gamma leg settings easy to inspect. Distinguish original paper reference, paper-configuration local runs and new comparisons. | High |
| 7 | If I can compare a decoder, I want a clear way to reproduce or request that exact configuration. | Connect supported full-stack methods to faithful reproduce/extend/request actions; distinguish runnable portable specs from study-specific command recipes before the user selects one. Expose qualified new controls only through supported execution routes. | High goal; medium implementation scope |
| 8 | Remember the paper, figure and curves I selected, and let me share that comparison. | Persist or deep-link valid selections, metric and visibility; reconcile them against available evidence when the catalog changes. | Medium |
| 9 | Too many similar options and reused colors make the comparisons harder to follow. | Group/filter curve choices by method, code, budget and tuning role; use consistent curve encodings across figures and expose full labels on demand. Update stale help text. | Medium |

## Evidence and limits

### 1. discovery

No priortilt/2611.13373/weighted-streaming-osd-v2 records in current catalog; 453 active curves, 13 codes, zero active circuits. New data exists in reproduction/benchmark reports.

Plot only fully audited compatible multi-rate local curves. Progress is separate; do not turn pending results into measurements or benchmark timings into LER points.

### 2. comparisons

MacKay Fig.15 has zero paper curves and24 additional; LP Example4 has zero paper curves and25 additional. Both default to zero visible rows. Relay/Beam/BP-SF controlled CSS views likewise have zero paper reproductions.

Do not relabel an inferred budget or controlled adaptation as an exact source reproduction, or fabricate an LP paper LER figure.

### 3. comparisons

With the same catalog the custom chart moves from top640px before the paper update to811px now. Current paper chart begins at1260px in a1050px viewport. Yao page is12812px high; Roffe offers340 curve controls.

Preserve separate plots, exact configurations, group controls and exportable full tables. Cosmetic simplification must not erase scientific context.

### 4. comparisons

Your corrections about88200 iterations, runtime matching to OSD0, damping/scale/offset tuning and work units. Current metrics exist, but are a single per-card dropdown; new OSD benchmark is not catalogued.

Never substitute standalone OSD speed for whole BP-OSD latency, mix one-/ten-CPU timing cohorts, or pool incompatible iteration/counter versions.

### 5. controls

Live selection changes float64→int8, strict_pauli→min_llr and shortcut false→true. Source is the build-rule handler in app.js.

This is a confirmed behavior; its undesirability is inferred from your modularity/fair-comparison requirements. No controls were changed in this spike.

### 6. comparisons

Repeated user questions about X/Z block failure, paper budget, mean iterations/edge updates, tuned settings and circuit observable success. Current main table lacks explicit per-point tuning columns and source references are deliberately excluded.

Adding a paper-reference overlay is a medium-confidence design hypothesis because earlier v2 deliberately shows only local measurements. References must stay separately labeled and must not enter local selectors/denominators.

### 7. controls

Builder has565 presets but only BP/Q-BP and optional Q-BPGD visual families. Selecting a BP+OSD preset blocks the general package builder and directs to study commands.

The block currently correctly prevents substitution by plain BP. Some new families need backend/manifest qualification, not just a new dropdown option.

### 8. controls

Opening Roffe leaves URL at#results; reload returns to Custom plots. Only uploaded results currently persist.

Discard stale/hidden inputs and keep custom matrix/Stim functionality, as previously requested.

### 9. controls

Roffe has8 paper plus332 additional curve controls; color palette repeats every six curves. Recommendations still says paper selectors moved to v1 although current v2 has seven paper options.

Do not remove scientifically distinct cohorts merely because labels look alike; preserve exact evidence identity and all requested parameter values.

## Changes already delivered that should stay

- Distinct measured error-rate eligibility after validity, retirement and projection; valid zero-failure bounds count. No fictional point made from repeated cohorts at one rate.
- Hidden codes/circuits with no displayed results and no public three-qubit CSS fixture; custom matrix/Stim inputs remain.
- Add-curve picker excludes displayed curves; group/individual toggles and independent custom plots remain.
- Superscript powers, decade labels/minor grid, automatic visible-curve range, mean iterations and directed updates already exist; do not frame them as missing features.
- Preserve original evidence and archived v1. Do not recreate its five-selector workflow merely to add paper navigation.
- Preserve measured-only local-result semantics. Original-paper overlays require an explicitly separate reference layer; the proposed overlay is less certain than the need for clearer comparison.

## What was actually inspected

- User-directed v2 revision300cb12b; semantics update dc39055e; later axis/work updates; paper-figure update781055fb and current worktree.
- Live current UI and pre-paper-update index/app/style with the **same captured current catalog**; this is not a recreation of the historical data snapshot.
- Current catalog:453 active curves,3229 points,13 codes,0 active circuits and seven paper options; these figures are a worktree snapshot with pre-existing collector changes.
- Browser checks cover discoverability, source/local classification, default groups, adaptation-only empty views, curve picking, geometry, metrics, reload state and builder behavior.
- Final browser run has no page errors. Earlier historical-route attempts failed because the probe lambda accidentally accepted Playwright’s request argument into a default closure parameter. That harness error was corrected and is not product evidence.

Evidence: [browser observations](browser-observations.json), [source snapshot](source-context.json), [verification](verification.json).
Historical task records: [v2](../../quick/261104-n37-retire-research-html-v1-and-build-simple/261104-n37-PLAN.md), [semantics](../../quick/261106-nd0-refine-workbench-result-semantics-and-co/261106-nd0-PLAN.md), [paper figures](../../quick/261116-ote-check-lp1054-results-and-add-paper-figur/PLAN.md).

## Verdict

PARTIAL: interface behaviors and gaps were verified, while future user feedback remains an inference. The forecast can guide a later discussion; it does not authorize changes.
