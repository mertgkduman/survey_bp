---
status: in_progress
quick_id: 261003-s2b
date: 2026-10-03
---

# Prespecify and prepare the BB72 CSS BP comparison

## Goal

Deliver a frozen, executable BB72 CSS code-capacity study design with matched physical samples, disjoint parameter-selection and evaluation cohorts, explicit compatibility and source qualifications, and separate paper-settings and shared-work views. Publication-level superiority and paper-reproduction claims remain gated by the stated assessment rules.

## Tasks

1. Freeze a machine-readable design and human-readable methods note before any BB72 study outcomes are examined. Specify code/noise, eligible update and damping compositions, sample identities, selection and evaluation sizes, shared work caps, outcome definitions, statistical rules, and source-settings qualifications.
2. Build a deterministic manifest generator and campaign executor that preflights every arm, verifies each public run, rejects changed design/implementation identities and incomplete or mismatched paired samples, and separates selection from evaluation. Add focused tests for leakage, compatibility, and seal integrity.
3. Run bounded BB72 evidence through the public engine, produce both study views from verified ledgers, check the stated gates, and report limits without treating adaptation as source-curve reproduction. Commit code and planning artifacts atomically.

## Must haves

- The frozen design precedes evaluation and is digest-bound to all generated manifests.
- Every arm at one rate/cohort receives identical physical sample identities; selection and evaluation share none.
- Controlled rows have the same CSS artifact, channel, schedule, stopping, and declared edge-work cap; each varying parameter is explicit.
- Source-settings rows distinguish faithful original experiments from BB72 transplants and never claim reproduction for the latter.
- No missing or cap-hit terminal is removed from the primary denominator.
