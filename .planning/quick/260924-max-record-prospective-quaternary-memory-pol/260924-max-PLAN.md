---
phase: quick
plan: 260924-max
status: ready
description: Record prospective quaternary memory-policy novelty in Markdown and reproducible PDF
files_modified:
  - docs/research-novelty-and-depth-register.md
  - docs/research-novelty-and-depth-register.pdf
  - tools/build_novelty_pdf.py
---

# Quick task: Cross-kernel memory research question

## Goal

Record the user's proposed comparison of memory-policy effects under separate binary CSS and joint quaternary Pauli BP as a provisional research question, and provide a current PDF rendering of the living Markdown novelty register. Preserve the fixed Phase 1–2 documentation PDF snapshot.

## Tasks

1. Add a narrowly worded entry and research/evidence plan to the living novelty register. Distinguish Relay-BP's circuit-level XYZ binary error-mode representation from a genuine four-state Pauli BP kernel. Tie implementation to Phases 10–11 and circuit comparisons to Phase 13.
2. Add a deterministic, source-hashed PDF renderer for the living novelty register and generate its PDF. Check byte-for-byte regeneration and the current Markdown source digest.

## Verification

- Fresh PDF regeneration matches the checked-in PDF byte for byte.
- The source digest embedded in the PDF matches `docs/research-novelty-and-depth-register.md`.
- The historical `docs/policy-bp-documentation-through-phase-2.pdf` remains unchanged.
