# Phase 5: Guided and Perturbative BP Interventions - Discussion Log

> **Audit trail only.** Downstream research and planning use `05-CONTEXT.md`; this log records the alternatives considered.

**Date:** 2026-09-30
**Phase:** 05-Guided and Perturbative BP Interventions
**Areas discussed:** Pilot scope, Researcher workflow

---

## Area Selection

The user selected pilot scope and researcher workflow. Source fidelity and flip-source selection were offered, but the user did not select them for discussion. The existing project and design source-qualification rules still apply.

## Pilot Scope

| Question | Alternatives offered | Selected |
| --- | --- | --- |
| Codes for matched physical-sample pilots | Small pilots on BB-144, B1, and HGP; one primary code with deterministic fixtures for others; broader three-code pilots | One primary code |
| Primary code | BB-144, with verified artifact and Phase 4 evidence; B1, closer to a BPGD source example but Phase 4 low-noise selection inconclusive; constructed HGP, not paper-exact | B1 |
| Intervention comparisons | Each of six interventions separately against baseline; BPGD and impulse on B1 with fixtures for others; separate arms plus selected combinations | Each intervention separately |
| Primary pilot purpose | Mechanism and evidence inspection; preliminary failure-rate estimates; runtime comparison | Mechanisms and evidence |

**User's choices:** The user answered `2`, `B1`, `1`, and `1`, then chose to move on. The B1 pilot should use small matched samples, inspectable attempt traces, original-problem outcomes, and work; it should not rank decoders. Intervention-pair arms and three-code pilot coverage were not selected.

## Researcher Workflow

| Question | Alternatives offered | Selected |
| --- | --- | --- |
| Pilot entry point | Manifest and CLI with compact notebook; notebook-first execution; manifest and CLI only | Manifest and CLI with compact notebook |
| Notebook opening view | Shot-by-shot path; arm summary; event timeline | Shot-by-shot path |
| Visibility of failed, contradictory, invalid, or denied attempts | Visible attempt rows with expandable detail; grouped counts; separate exceptions panel | Visible attempt rows |
| Matched-sample comparison | Baseline beside one selected arm; all seven arms together; one arm at a time | Baseline beside one selected arm |
| Plot delivery | Notebook and shareable HTML; notebook only; HTML only | Notebook and shareable HTML |
| First plot set | Outcomes and work; outcomes only; outcomes, work, and timing | Outcomes and work |
| Initially visible plotted arms | Baseline plus selected arm; all seven arms; baseline only | Baseline plus selected arm |
| Plot visibility controls | Synchronized across plots; separate per plot; optional sync | Synchronized across plots |
| HTML detail | Plots and provenance; plots only; full shot drilldown | Plots and provenance |

**User's addition:** “Can we also produce plots with interactive choice for what is shown and what is not, like click based on/off on the legend”. This was incorporated as interactive legend toggles without changing saved evidence. After four initial workflow questions and four plot follow-ups, the user chose to move on.

**User's choices:** `1` for the entry point, opening view, attempt visibility, and paired comparison; then `1` for notebook plus HTML, outcomes and work, initial baseline plus one arm, synchronized toggles, and HTML plots with provenance.

## Agent Discretion

- Exact finite pilot counts, B1 noise point(s), and plot implementation remain for measured planning under the Phase 5 design and project evidence rules.
- Source selection and resolution of BPGD, impulse, syndrome-flip, and sign-flip ambiguities remain research tasks because the user did not choose a source preference.

## Deferred Ideas

- A broader three-code or intervention-pair pilot and decoder ranking were considered but not selected for Phase 5.
