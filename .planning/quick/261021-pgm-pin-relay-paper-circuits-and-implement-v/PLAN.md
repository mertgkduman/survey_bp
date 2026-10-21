---
status: in_progress
type: quick
date: 2026-10-21
---

# Pinned paper circuits and CPU circuit BP integration

## Goal

Import exact Relay-BP v0.2.2 and BeamSearch circuit fixtures, compile independent-fault Stim detector models into the existing binary parity BP semantics, expose a Sinter decoder, and measure representative CPU performance. Record GPU availability and an evidence-based backend decision. Connect current paper source policies and evidence in a cross-regime index.

## Tasks

1. Preserve the Relay and BeamSearch upstream `.stim` fixtures in separate compressed archives with upstream commit, license, per-file hashes, and directly usable representative circuits.
2. Implement typed DEM conversion and Sinter integration. Retain detector and observable maps, heterogeneous priors, deterministic faults, and explicit model limitations.
3. Reuse the canonical binary numerical primitives and graph ordering in an opt-in compiled CPU path. Verify against the reference policy sweep and injected faults.
4. Run bounded Stim/Sinter and pinned author-release Relay Rust comparisons on the same detector shots, report throughput and semantics separately, and document the GPU environment and feasibility.
5. Add non-runnable source paper policies for the selected quaternary and circuit methods, retain the CSS runnable/source separation, and link policies, targets, manifests, and assessments in an index.

This is an integration and profiling slice. Publication-level source reproduction remains governed by Phase 12–13 requirements.
